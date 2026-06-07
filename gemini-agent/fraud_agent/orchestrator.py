from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional
from uuid import uuid4

from .config import get_settings, load_environment, validate_startup
from .contradictions import detect_contradictions
from .gemini_runtime import analyze_with_gemini
from .guardian_alert_service import send_fraud_alert
from .mcp.elastic_adapter import fuzzy_match_domain, search_identity
from .mcp.mongo_adapter import get_institution_rules, lookup_blacklist, save_blacklist_entry, save_case
from .observability import trace_stage
from .schemas import BehavioralAnalysis, DetectedEntities, ThreatReport, VerificationResults
from .scoring import calculate_threat_score, risk_level_from_score
from .utils import dedupe_preserve_order, extract_domains, extract_emails, extract_institution_candidates, extract_phone_numbers, infer_channels, normalize_text

load_environment()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _case_id() -> str:
    return f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"


def _evidence_to_sentence(items: Iterable[str]) -> str:
    return "; ".join(item for item in items if item)


def _extract_institution(text: str, gemini_payload: dict | None = None) -> str:
    if gemini_payload and gemini_payload.get("institution"):
        return str(gemini_payload["institution"])
    aliases = ["State Bank of India", "SBI", "Central Bureau of Investigation", "CBI", "Cyber Police", "Police"]
    found = extract_institution_candidates(text, aliases)
    if found:
        return found[0]
    content = normalize_text(text)
    if "bank" in content:
        return "Bank"
    if "police" in content:
        return "Police"
    return "CBI" if "cbi" in content else ""


def _payment_method_from_text(text: str) -> str:
    content = normalize_text(text)
    if any(token in content for token in ["upi", "gpay", "phonepe", "paytm"]):
        return "digital_wallet"
    if "cash" in content:
        return "cash"
    if "crypto" in content or "bitcoin" in content:
        return "crypto"
    if any(token in content for token in ["transfer", "payment", "safe account"]):
        return "bank_transfer"
    return ""


def extract_entities(text: str, gemini_payload: dict | None = None) -> dict:
    phones = dedupe_preserve_order([*(gemini_payload or {}).get("phone_numbers", [])] + extract_phone_numbers(text))
    domains = dedupe_preserve_order([*(gemini_payload or {}).get("domains", [])] + extract_domains(text))
    emails = dedupe_preserve_order([*(gemini_payload or {}).get("emails", [])] + extract_emails(text))
    return {
        "phone_numbers": phones,
        "domains": domains,
        "emails": emails,
        "institution": _extract_institution(text, gemini_payload),
        "payment_method": _payment_method_from_text(text),
        "observed_channels": infer_channels(text),
    }


def _classify_fraud_type(institution: str, text: str, domain_risk: str, blacklist_hit: bool, gemini_payload: dict) -> str:
    gemini_type = str(gemini_payload.get("fraud_type") or "")
    if gemini_type:
        return gemini_type
    content = normalize_text(text)
    institution_norm = normalize_text(institution)
    if "digital arrest" in content:
        return "digital_arrest_scam"
    if "sbi" in institution_norm or "bank" in institution_norm:
        return "banking_impersonation"
    if "cbi" in institution_norm or "police" in institution_norm:
        return "authority_impersonation"
    if blacklist_hit:
        return "repeat_offender_campaign"
    if domain_risk in {"high", "critical"}:
        return "phishing"
    return "impersonation_attempt"


def _primary_identity(entities: DetectedEntities) -> tuple[str, str]:
    if entities.phone_number:
        return entities.phone_number, "phone_number"
    if entities.website:
        return entities.website, "domain"
    if entities.institution:
        return entities.institution, "institution"
    return "", "unknown"


def _deviation_from_contradiction(contradictions: list[dict], institution: str) -> float:
    deviation = 0.12 if institution else 0.05
    if not contradictions:
        return deviation
    severity = contradictions[0].get("severity", "low")
    return {"critical": 0.98, "high": 0.9, "medium": 0.75, "low": 0.55}.get(severity, 0.55)


def run_pipeline(text: str, case_id: Optional[str] = None, evidence_metadata: Optional[dict] = None) -> dict:
    validate_startup()
    settings = get_settings()
    case_id = case_id or _case_id()
    timestamp = _now()
    with trace_stage(case_id, "ingestion"):
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("No analyzable text was provided.")
    with trace_stage(case_id, "gemini"):
        gemini_payload = analyze_with_gemini(clean_text)
    with trace_stage(case_id, "mongodb"):
        entities = extract_entities(clean_text, gemini_payload)
        phone_numbers = entities["phone_numbers"]
        domains = entities["domains"]
        emails = entities["emails"]
        institution = entities["institution"]
        payment_method = entities["payment_method"]
        observed_channels = entities["observed_channels"]
        blacklist_hits: List[dict] = []
        for identity in dedupe_preserve_order([*phone_numbers, *emails, *domains, institution]):
            hit = lookup_blacklist(identity)
            if hit:
                blacklist_hits.append(hit)
        rule_record = get_institution_rules(institution) if institution else {}
    with trace_stage(case_id, "elasticsearch"):
        elastic_result = fuzzy_match_domain(domains[0]) if domains else (search_identity(institution) if institution else {})
    with trace_stage(case_id, "contradictions"):
        contradictions = detect_contradictions(clean_text, institution, observed_channels, rule_record or None, domains[0] if domains else None)
    with trace_stage(case_id, "scoring"):
        urgency = max(float(gemini_payload.get("artificial_urgency", 0.0) or 0.0), 0.0)
        coercion = max(float(gemini_payload.get("social_coercion", 0.0) or 0.0), 0.0)
        deviation = _deviation_from_contradiction(contradictions, institution)
        if blacklist_hits:
            urgency, coercion, deviation = max(urgency, 0.7), max(coercion, 0.65), max(deviation, 0.95)
        if elastic_result.get("official_match"):
            deviation = min(deviation, 0.25)
        elif elastic_result.get("typo_squatting_risk") in {"high", "critical"}:
            deviation = max(deviation, 0.9 if elastic_result["typo_squatting_risk"] == "high" else 0.98)
        if contradictions:
            ctype = contradictions[0].get("contradiction_type", "")
            if ctype == "impossible_legal_procedure":
                urgency, coercion, deviation = max(urgency, 0.78), max(coercion, 0.92), max(deviation, 0.98)
            elif ctype == "unauthorized_financial_instruction":
                urgency, coercion, deviation = max(urgency, 0.95), max(coercion, 0.55), max(deviation, 0.95)
            elif ctype in {"unofficial_communication_channel", "improper_messaging_platform"}:
                urgency, coercion, deviation = max(urgency, 0.72), max(coercion, 0.45), max(deviation, 0.88)
        threat_score = calculate_threat_score(urgency, coercion, deviation)
        risk_level = risk_level_from_score(threat_score)
    fraud_type = _classify_fraud_type(institution, clean_text, elastic_result.get("typo_squatting_risk", ""), bool(blacklist_hits), gemini_payload)
    confirmed_domain = domains[0] if domains else ""
    if elastic_result.get("matched_candidates"):
        confirmed_domain = elastic_result["matched_candidates"][0].get("domain") or confirmed_domain
    reasoning_summary = _evidence_to_sentence([
        str(gemini_payload.get("structured_reasoning", "")),
        f"Detected institution: {institution}" if institution else "",
        f"Observed channels: {', '.join(observed_channels)}" if observed_channels else "",
        f"Urgency {urgency:.2f}, coercion {coercion:.2f}, deviation {deviation:.2f}",
        "Contradiction found" if contradictions else "No direct contradiction detected",
    ])
    report = ThreatReport(
        case_id=case_id,
        timestamp=timestamp,
        threat_score=threat_score,
        risk_level=risk_level,
        fraud_type=fraud_type,
        behavioral_analysis=BehavioralAnalysis(round(urgency, 4), round(coercion, 4), round(deviation, 4)),
        detected_entities=DetectedEntities(institution, phone_numbers[0] if phone_numbers else "", confirmed_domain, payment_method),
        verification_results=VerificationResults(
            mongodb_check=_evidence_to_sentence([f"MongoDB matched {rule_record.get('institution')}" if rule_record else ("No institution was detected for MongoDB verification." if not institution else "No institutional rule record was found in MongoDB."), f"Blacklist hit for {len(blacklist_hits)} offender identifier(s)." if blacklist_hits else ""]),
            elastic_check=elastic_result.get("recommended_interpretation") or elastic_result.get("evidence_summary") or "No Elasticsearch evidence available.",
        ),
        reasoning_summary=reasoning_summary,
        recommended_action="Treat as a confirmed scam, block the sender, and contact the institution only through official channels." if threat_score >= settings.fraud_alert_threshold else "Use caution, verify the sender through official channels, and avoid clicking links or making payments.",
        guardian_alert_required=threat_score >= settings.fraud_alert_threshold,
        blacklist_candidate=threat_score >= settings.fraud_alert_threshold,
        contradictions=contradictions,
        extracted_entities={"phone_numbers": phone_numbers, "domains": domains, "emails": emails, "observed_channels": observed_channels},
        blacklist_hits=blacklist_hits,
        gemini_reasoning=gemini_payload,
    )
    if report.blacklist_candidate:
        offender_identity, identity_type = _primary_identity(report.detected_entities)
        if offender_identity:
            save_blacklist_entry({"offender_identity": offender_identity, "identity_type": identity_type, "reported_carrier_platform": observed_channels[0] if observed_channels else "text", "claimed_persona": institution or fraud_type, "calculated_threat_score": threat_score, "scam_type": fraud_type, "timestamp_logged": timestamp})
    alert_status = "not_required"
    with trace_stage(case_id, "alerts"):
        if report.guardian_alert_required:
            alert_results = send_fraud_alert(report.threat_score, report.case_id, report.reasoning_summary)
            alert_status = alert_results.get("status", "unknown")
        report.alert_status = alert_status
    payload = report.to_dict()
    save_case(case_id, {"text": clean_text, **(evidence_metadata or {})}, payload, alert_status)
    return payload


def analyze_text(text: str, case_id: Optional[str] = None) -> dict:
    return run_pipeline(text=text, case_id=case_id, evidence_metadata={"channel": "text"})
