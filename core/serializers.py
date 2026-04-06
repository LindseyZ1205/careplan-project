from __future__ import annotations

import json
from typing import Any, Dict

from django.http import HttpRequest

from .models import CarePlan
from .textgen import CarePlanInput


def parse_form_input(request: HttpRequest) -> CarePlanInput:
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


def parse_api_body(request: HttpRequest) -> CarePlanInput:
    if request.content_type and "application/json" in request.content_type:
        try:
            raw = json.loads(request.body.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            raw = {}
        body = raw if isinstance(raw, dict) else {}
    else:
        body = request.POST
    return CarePlanInput(
        patient_first_name=str(body.get("patient_first_name", "") or "").strip(),
        patient_last_name=str(body.get("patient_last_name", "") or "").strip(),
        patient_mrn=str(body.get("patient_mrn", "") or "").strip(),
        doctor_name=str(body.get("doctor_name", "") or "").strip(),
        doctor_npi=str(body.get("doctor_npi", "") or "").strip(),
        diagnosis=str(body.get("diagnosis", "") or "").strip(),
        medication_name=str(body.get("medication_name", "") or "").strip(),
        notes=str(body.get("notes", "") or "").strip(),
    )


def care_plan_to_dict(cp: CarePlan) -> Dict[str, Any]:
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


def care_plan_status_payload(cp: CarePlan) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "careplan_id": cp.pk,
        "status": cp.status,
        "content": None,
        "error": None,
    }
    if cp.status == CarePlan.Status.COMPLETED:
        payload["content"] = cp.careplan_text
    elif cp.status == CarePlan.Status.FAILED:
        payload["error"] = "Care plan generation failed after retries."
    return payload
