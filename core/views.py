from __future__ import annotations

from typing import Any, Dict

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import CarePlan
from .serializers import (
    care_plan_status_payload,
    care_plan_to_dict,
    parse_api_body,
    parse_form_input,
)
from .services import submit_care_plan_request


def careplan_form(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}

    if request.method == "POST":
        form_data = parse_form_input(request)
        care_plan = submit_care_plan_request(form_data)
        context["ack"] = {
            "message": "已收到",
            "careplan_id": care_plan.pk,
            "status": care_plan.status,
        }

    return render(request, "core/index.html", context)


@csrf_exempt
def generate_careplan_api(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        return JsonResponse({
            "message": (
                "POST to enqueue a care plan: patient_first_name, patient_last_name, "
                "patient_mrn (optional), doctor_name, doctor_npi (optional), "
                "diagnosis, medication_name, notes (optional). "
                "Returns 202 with careplan_id; Celery worker generates text. "
                "Poll GET /api/careplan/<id>/status/ for status + content when completed."
            ),
        })
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    form_data = parse_api_body(request)
    care_plan = submit_care_plan_request(form_data)
    return JsonResponse(
        {
            "message": "已收到",
            "careplan_id": care_plan.pk,
            "status": care_plan.status,
        },
        status=202,
    )


def get_careplan_api(request: HttpRequest, id: int) -> JsonResponse:
    care_plan = get_object_or_404(CarePlan.objects.select_related("order__patient", "order__doctor"), pk=id)
    return JsonResponse(care_plan_to_dict(care_plan))


def careplan_status_api(request: HttpRequest, id: int) -> JsonResponse:
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    care_plan = get_object_or_404(CarePlan.objects.only("pk", "status", "careplan_text"), pk=id)
    return JsonResponse(care_plan_status_payload(care_plan))
