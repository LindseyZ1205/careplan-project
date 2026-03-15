from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


_CAREPLANS: List[Dict[str, Any]] = []


@dataclass
class CarePlanInput:
    patient_first_name: str
    patient_last_name: str
    diagnosis: str
    medication_name: str
    notes: str = ""


def _generate_careplan_text(data: CarePlanInput) -> str:
    full_name = f"{data.patient_first_name} {data.patient_last_name}".strip()
    return (
        f"Care Plan for {full_name}\n"
        f"Diagnosis: {data.diagnosis}\n"
        f"Medication: {data.medication_name}\n\n"
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


def careplan_form(request: HttpRequest) -> HttpResponse:
    context: Dict[str, Any] = {}

    if request.method == "POST":
        form_data = CarePlanInput(
            patient_first_name=request.POST.get("patient_first_name", "").strip(),
            patient_last_name=request.POST.get("patient_last_name", "").strip(),
            diagnosis=request.POST.get("diagnosis", "").strip(),
            medication_name=request.POST.get("medication_name", "").strip(),
            notes=request.POST.get("notes", "").strip(),
        )
        generated_text = _generate_careplan_text(form_data)
        record = {**asdict(form_data), "careplan_text": generated_text}
        _CAREPLANS.append(record)
        context["careplan"] = record

    return render(request, "core/index.html", context)


@csrf_exempt
def generate_careplan_api(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    body: Dict[str, Any] = getattr(request, "POST", {})
    form_data = CarePlanInput(
        patient_first_name=body.get("patient_first_name", "").strip(),
        patient_last_name=body.get("patient_last_name", "").strip(),
        diagnosis=body.get("diagnosis", "").strip(),
        medication_name=body.get("medication_name", "").strip(),
        notes=body.get("notes", "").strip(),
    )
    generated_text = _generate_careplan_text(form_data)
    record = {**asdict(form_data), "careplan_text": generated_text}
    _CAREPLANS.append(record)

    return JsonResponse(record, status=201)

