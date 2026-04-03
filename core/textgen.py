from __future__ import annotations

from dataclasses import dataclass


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


def generate_careplan_template_text(data: CarePlanInput) -> str:
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
