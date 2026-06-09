from __future__ import annotations

import json
from typing import Any, Dict

from .config import get_settings
from .utils import extract_domains, extract_emails, extract_phone_numbers, normalize_text

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None


def deterministic_fallback_analysis(text: str) -> Dict[str, Any]:
    content = normalize_text(text)
    urgency_terms = ["immediately", "urgent", "within 10 minutes", "within 15 minutes", "now", "last warning", "freeze", "click now"]
    coercion_terms = ["arrest", "digital arrest", "police", "cbi", "do not tell", "stay on the line", "under surveillance", "legal action"]
    fraud_indicators = [term for term in urgency_terms + coercion_terms if term in content]
    institution = ""
    for label in ["State Bank of India", "SBI", "Central Bureau of Investigation", "CBI", "Cyber Police", "Police"]:
        if normalize_text(label) in content:
            institution = label
            break
    if "digital arrest" in content:
        fraud_type = "digital_arrest_scam"
    elif any(token in content for token in ["sbi", "bank", "account frozen", "statement"]):
        fraud_type = "banking_impersonation"
    elif any(token in content for token in ["cbi", "police", "arrest"]):
        fraud_type = "authority_impersonation"
    elif extract_domains(text):
        fraud_type = "phishing"
    else:
        fraud_type = "impersonation_attempt"
    urgency = min(1.0, sum(0.16 for term in urgency_terms if term in content) + (0.15 if "minute" in content else 0.0))
    coercion = min(1.0, sum(0.18 for term in coercion_terms if term in content) + (0.25 if "digital arrest" in content else 0.0))
    return {
        "source": "deterministic_fallback",
        "institution": institution,
        "phone_numbers": extract_phone_numbers(text),
        "domains": extract_domains(text),
        "emails": extract_emails(text),
        "fraud_indicators": fraud_indicators,
        "coercion_detected": coercion > 0,
        "urgency_detected": urgency > 0,
        "fraud_type": fraud_type,
        "artificial_urgency": round(urgency, 4),
        "social_coercion": round(coercion, 4),
        "structured_reasoning": "Deterministic lexical analysis extracted entities, urgency, coercion, and fraud indicators from the supplied evidence.",
    }


def _coerce_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def analyze_with_gemini(text: str) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key or genai is None:
        if settings.strict_production_mode:
            raise RuntimeError("Gemini is unavailable in STRICT_PRODUCTION_MODE. Configure GEMINI_API_KEY and install google-generativeai.")
        return deterministic_fallback_analysis(text)
    prompt = """
Return only compact JSON with keys: institution, phone_numbers, domains, emails,
fraud_indicators, coercion_detected, urgency_detected, fraud_type,
artificial_urgency, social_coercion, structured_reasoning.
Scores must be deterministic floats from 0 to 1 based only on the evidence.
Evidence:
""" + text
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt, generation_config={"temperature": 0, "response_mime_type": "application/json"})
        payload = _coerce_json(getattr(response, "text", "") or "{}")
        return payload
    except Exception as e:
        print(f"Gemini API Error: {e}")
        if settings.strict_production_mode:
            raise
        return deterministic_fallback_analysis(text)
