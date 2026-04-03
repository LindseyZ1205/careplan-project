from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.db import transaction

from .llm import generate_careplan_with_llm
from .models import CarePlan

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_care_plan_task(self, careplan_id: int) -> str | None:
    """
    Celery pulls tasks from the broker (Redis). This task loads the CarePlan,
    calls generate_careplan_with_llm (mock / template / openai per LLM_MODE),
    then saves to the database.
    """
    try:
        cp = CarePlan.objects.select_related("order__patient", "order__doctor").get(pk=careplan_id)
    except CarePlan.DoesNotExist:
        logger.warning("CarePlan id=%s not found", careplan_id)
        return None

    if cp.status == CarePlan.Status.COMPLETED and cp.careplan_text:
        return cp.careplan_text

    with transaction.atomic():
        locked = (
            CarePlan.objects.select_for_update()
            .select_related("order__patient", "order__doctor")
            .get(pk=careplan_id)
        )
        if locked.status == CarePlan.Status.COMPLETED and locked.careplan_text:
            return locked.careplan_text
        locked.status = CarePlan.Status.PROCESSING
        locked.save(update_fields=["status", "updated_at"])

    cp.refresh_from_db()
    logger.info(
        "generate_care_plan_task id=%s LLM_MODE=%s",
        careplan_id,
        getattr(settings, "LLM_MODE", "mock"),
    )
    try:
        text = generate_careplan_with_llm(cp)
    except Exception as exc:
        logger.exception("LLM failed careplan_id=%s retry=%s", careplan_id, self.request.retries)
        if self.request.retries >= self.max_retries:
            failed = CarePlan.objects.get(pk=careplan_id)
            failed.status = CarePlan.Status.FAILED
            failed.save(update_fields=["status", "updated_at"])
            raise
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown) from exc

    done = CarePlan.objects.get(pk=careplan_id)
    done.careplan_text = text
    done.status = CarePlan.Status.COMPLETED
    done.save(update_fields=["careplan_text", "status", "updated_at"])
    return text
