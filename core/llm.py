"""Care plan text generation: mock, template, or OpenAI — controlled by settings.LLM_MODE."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from django.conf import settings

from .models import CarePlan
from .textgen import CarePlanInput, generate_careplan_template_text

logger = logging.getLogger(__name__)

# Fixed body for development / tests (no external call). Override via MOCK_LLM_BODY_FILE if needed.
_MOCK_DEFAULT = """Problem List / Drug Therapy Problems (DTPs):
- [MOCK] Hypothetical DTP pending full chart review.

Goals (SMART format):
- [MOCK] Improve adherence and clinical stability within 90 days.

Pharmacist Interventions / Plan:
- [MOCK] Patient education on medication use and side-effect monitoring.

Monitoring Plan & Lab Schedule:
- [MOCK] Follow labs per protocol; reassess in 4 weeks.

Summary:
This paragraph is produced by mock_llm_generate_careplan() for dev/test only.
"""


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


def mock_llm_generate_careplan(cp: CarePlan) -> str:
    """
    Fake LLM: returns a fixed care plan string (optionally load body from MOCK_LLM_BODY_FILE).
    Use with LLM_MODE=mock so the Celery worker never hits the network.
    """
    body = _MOCK_DEFAULT
    path = os.environ.get("MOCK_LLM_BODY_FILE", "").strip()
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                body = f.read()
        except OSError as e:
            logger.warning("MOCK_LLM_BODY_FILE read failed (%s), using built-in mock body", e)
    data = _careplan_to_input(cp)
    full_name = f"{data.patient_first_name} {data.patient_last_name}".strip()
    return (
        "[MOCK LLM — LLM_MODE=mock, no real model call]\n\n"
        f"Care Plan (mock) for {full_name}\n"
        f"Diagnosis: {data.diagnosis} | Medication: {data.medication_name}\n\n"
        f"{body}\n"
        f"---\n(trace: careplan_id={cp.pk})\n"
    )


def _openai_chat(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_MODE=openai")
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
    """
    Dispatch by settings.LLM_MODE:
      - mock: mock_llm_generate_careplan (fixed / file body)
      - template: deterministic text from patient/order fields (no network)
      - openai: OpenAI Chat Completions
    """
    mode = getattr(settings, "LLM_MODE", "mock") or "mock"
    mode = str(mode).lower()

    if mode == "mock":
        return mock_llm_generate_careplan(cp)

    if mode == "template":
        return generate_careplan_template_text(_careplan_to_input(cp))

    if mode == "openai":
        data = _careplan_to_input(cp)
        base_context = (
            f"Patient: {data.patient_first_name} {data.patient_last_name}\n"
            f"MRN: {data.patient_mrn or 'n/a'}\n"
            f"Diagnosis: {data.diagnosis}\n"
            f"Medication: {data.medication_name}\n"
            f"Provider: {data.doctor_name} (NPI {data.doctor_npi or 'n/a'})\n"
            f"Notes: {data.notes or 'none'}\n"
        )
        try:
            return _openai_chat(
                "Write a concise care plan for this specialty pharmacy case:\n\n" + base_context
            )
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"OpenAI request failed: {e}") from e

    logger.warning("Unknown LLM_MODE=%r, falling back to mock", mode)
    return mock_llm_generate_careplan(cp)
