"""Call LLM for care plan text, or fall back to template when no API key."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .models import CarePlan
from .textgen import CarePlanInput, generate_careplan_template_text


def _careplan_to_input(cp: CarePlan) -> CarePlanInput:
    o = cp.order
    p = o.patient
    d = o.doctor
    return CarePlanInput(
        patient_first_name=p.first_name,
        patient_last_name=p.last_name,
        patient_mrn=p.mrn or "",
        doctor_name=d.name,
        doctor_npi=d.npi or "",
        diagnosis=o.diagnosis,
        medication_name=o.medication_name,
        notes=o.notes or "",
    )


def _openai_chat(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a clinical pharmacist assistant. "
                        "Output a structured care plan with sections: "
                        "Problem List/DTPs, Goals (SMART), Interventions, Monitoring."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"].strip()


def generate_careplan_with_llm(cp: CarePlan) -> str:
    data = _careplan_to_input(cp)
    base_context = (
        f"Patient: {data.patient_first_name} {data.patient_last_name}\n"
        f"MRN: {data.patient_mrn or 'n/a'}\n"
        f"Diagnosis: {data.diagnosis}\n"
        f"Medication: {data.medication_name}\n"
        f"Provider: {data.doctor_name} (NPI {data.doctor_npi or 'n/a'})\n"
        f"Notes: {data.notes or 'none'}\n"
    )
    if os.environ.get("OPENAI_API_KEY", "").strip():
        try:
            return _openai_chat(
                "Write a concise care plan for this specialty pharmacy case:\n\n" + base_context
            )
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"OpenAI request failed: {e}") from e
    return generate_careplan_template_text(data)
