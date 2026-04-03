from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .models import CarePlan, Doctor, Order, Patient
from .queue import enqueue_careplan_id


@dataclass
class CarePlanInput:
    patient_first_name: str
    patient_last_name: str
    patient_mrn: str
    doctor_name: str
    doctor_npi: str
    diagnosis: str
    medication_name: str
    notes: str


def _generate_careplan_text(data: CarePlanInput) -> str:
    """Reserved for a future worker / LLM step (not called on HTTP request path)."""
    full_name = f"{data.patient_first_name} {data.patient_last_name}".strip()
    return (
        f"Care Plan for {full_name}\n"
        f"Diagnosis: {data.diagnosis}\n"
        f"Medication: {data.medication_name}\n"
        f"Referring provider: {data.doctor_name} (NPI: {data.doctor_npi or 'n/a'})\n\n"
        "Problem List / Drug Therapy Problems (DTPs):\n"
        "- Pending detailed assessment based on full patient record.\n\n"
        "Goals (SMART format):\n"
        "- Improve clinical outcomes related to the primary diagnosis.\n\n"
        "Pharmacist Interventions / Plan:\n"
        "- Educate patient on proper medication use and adherence.\n\n"
        "Monitoring Plan & Lab Schedule:\n"
        "- Monitor relevant labs and clinical markers per standard of care.\n\n"
        "---\nSummary:\n"
        f"This care plan covers {full_name} for {data.diagnosis} on {data.medication_name}. "
        "Key next steps: complete DTP assessment, set SMART goals with the patient, "
        "deliver interventions, and follow the monitoring schedule above.\n"
    )


def _care_plan_to_dict(cp: CarePlan) -> Dict[str, Any]:
    order = cp.order
    patient = order.patient
    doctor = order.doctor
    return {
        "id": cp.pk,
        "status": cp.status,
        "careplan_text": cp.careplan_text,
        "patient_first_name": patient.first_name,
        "patient_last_name": patient.last_name,
        "patient_mrn": patient.mrn,
        "doctor_name": doctor.name,
        "doctor_npi": doctor.npi,
        "diagnosis": order.diagnosis,
        "medication_name": order.medication_name,
        "notes": order.notes,
        "order_id": order.pk,
        "patient_id": patient.pk,
        "doctor_id": doctor.pk,
    }


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


def _submit_care_plan_request(data: CarePlanInput) -> CarePlan:
    with transaction.atomic():
        care_plan = _create_pending_care_plan(data)
        pk = care_plan.pk
        transaction.on_commit(lambda: enqueue_careplan_id(pk))
    return care_plan


def _parse_form_input(request: HttpRequest) -> CarePlanInput:
    return CarePlanInput(
        patient_first_name=request.POST.get("patient_first_name", "").strip(),
        patient_last_name=request.POST.get("patient_last_name", "").strip(),
        patient_mrn=request.POST.get("patient_mrn", "").strip(),
        doctor_name=request.POST.get("doctor_name", "").strip(),
        doctor_npi=request.POST.get("doctor_npi", "").strip(),
        diagnosis=request.POST.get("diagnosis", "").strip(),
        medication_name=request.POST.get("medication_name", "").strip(),
        notes=request.POST.get("notes", "").strip(),
    )


def _parse_api_body(request: HttpRequest) -> CarePlanInput:
    body = getattr(request, "POST", {})
    return CarePlanInput(
        patient_first_name=body.get("patient_first_name", "").strip(),
        patient_last_name=body.get("patient_last_name", "").strip(),
        patient_mrn=body.get("patient_mrn", "").strip(),
        doctor_name=body.get("doctor_name", "").strip(),
        doctor_npi=body.get("doctor_npi", "").strip(),
        diagnosis=body.get("diagnosis", "").strip(),
        medication_name=body.get("medication_name", "").strip(),
        notes=body.get("notes", "").strip(),
    )


def careplan_form(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}

    if request.method == "POST":
        form_data = _parse_form_input(request)
        care_plan = _submit_care_plan_request(form_data)
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
                "Returns immediately with careplan_id; generation is async (worker not included yet)."
            ),
        })
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    form_data = _parse_api_body(request)
    care_plan = _submit_care_plan_request(form_data)
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
    return JsonResponse(_care_plan_to_dict(care_plan))
