from __future__ import annotations

from django.conf import settings
from django.db import transaction

from .models import CarePlan, Doctor, Order, Patient
from .textgen import CarePlanInput


def _schedule_celery_task(careplan_id: int) -> None:
    from .tasks import generate_care_plan_task

    generate_care_plan_task.delay(careplan_id)


def _create_pending_care_plan(data: CarePlanInput) -> CarePlan:
    patient = Patient.objects.create(
        first_name=data.patient_first_name,
        last_name=data.patient_last_name,
        mrn=data.patient_mrn,
    )
    doctor = Doctor.objects.create(
        name=data.doctor_name,
        npi=data.doctor_npi,
    )
    order = Order.objects.create(
        patient=patient,
        doctor=doctor,
        medication_name=data.medication_name,
        diagnosis=data.diagnosis,
        notes=data.notes,
    )
    return CarePlan.objects.create(
        order=order,
        status=CarePlan.Status.PENDING,
        careplan_text="",
    )


def submit_care_plan_request(data: CarePlanInput) -> CarePlan:
    with transaction.atomic():
        care_plan = _create_pending_care_plan(data)
        pk = care_plan.pk
        if settings.CELERY_BROKER_URL or settings.CELERY_TASK_ALWAYS_EAGER:
            transaction.on_commit(lambda: _schedule_celery_task(pk))
    return care_plan
