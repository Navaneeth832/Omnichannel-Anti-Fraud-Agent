from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional
from uuid import uuid4

from .contradictions import detect_contradictions
from .mcp.elastic_adapter import fuzzy_match_domain, search_identity
from .mcp.mongo_adapter import get_institution_rules, lookup_blacklist, save_blacklist_entry
from .scoring import calculate_threat_score, risk_level_from_score
from .utils import (
    dedupe_preserve_order,
    extract_domains,
    extract_emails,
    extract_institution_candidates,
    extract_phone_numbers,
    infer_channels,
    normalize_text,
)

from .guardian_alert_service import send_fraud_alert


@dataclass
class BehavioralAnalysis:
    artificial_urgency: float
    social_coercion: float
    institutional_deviation: float


@dataclass
class DetectedEntities:
    institution: str = ""
    phone_number: str = ""
    website: str = ""
    payment_method: str = ""


@dataclass
class VerificationResults:
    mongodb_check: str = ""
    elastic_check: str = ""


@dataclass
class ThreatReport:
    case_id: str
    timestamp: str
    threat_score: float
    risk_level: str
    fraud_type: str
    behavioral_analysis: BehavioralAnalysis
    detected_entities: DetectedEntities
    verification_results: VerificationResults
    reasoning_summary: str
    recommended_action: str
    guardian_alert_required: bool
    blacklist_candidate: bool
    contradictions: List[dict] = field(default_factory=list)
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    blacklist_hits: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["behavioral_analysis"] = asdict(self.behavioral_analysis)
        payload["detected_entities"] = asdict(self.detected_entities)
        payload["verification_results"] = asdict(self.verification_results)
        return payload


def _score_artificial_urgency(text: str) -> float:
    content = normalize_text(text)
    score = 0.0
    signals = [
        ("immediately", 0.16),
        ("urgent", 0.16),
        ("within 10 minutes", 0.28),
        ("within 15 minutes", 0.22),
        ("freeze", 0.18),
        ("account will be frozen", 0.30),
        ("last warning", 0.18),
        ("do not disconnect", 0.18),
        ("transfer immediately", 0.20),
        ("click now", 0.18),
        ("now", 0.08),
    ]
    for token, weight in signals:
        if token in content:
            score += weight
    if any(char.isdigit() for char in content):
        if "minute" in content or "hour" in content:
            score += 0.15
    return min(score, 1.0)


def _score_social_coercion(text: str) -> float:
    content = normalize_text(text)
    score = 0.0
    signals = [
        ("arrest", 0.28),
        ("digital arrest", 0.55),
        ("legal action", 0.20),
        ("do not tell", 0.20),
        ("stay on the line", 0.22),
        ("under surveillance", 0.18),
        ("money laundering", 0.18),
        ("threat", 0.15),
        ("police", 0.12),
        ("cbi", 0.12),
    ]
    for token, weight in signals:
        if token in content:
            score += weight
    if any(token in content for token in ["family", "employer", "bank"]):
        score += 0.08
    return min(score, 1.0)


def _classify_fraud_type(institution: str, text: str, domain_risk: str, blacklist_hit: bool) -> str:
    content = normalize_text(text)
    institution_norm = normalize_text(institution)
    if "digital arrest" in content or "fake arrest" in content:
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


def _evidence_to_sentence(items: Iterable[str]) -> str:
    cleaned = [item for item in items if item]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "; ".join(cleaned)


def _primary_identity(entities: DetectedEntities) -> tuple[str, str]:
    if entities.phone_number:
        return entities.phone_number, "phone_number"
    if entities.website:
        return entities.website, "domain"
    if entities.institution:
        return entities.institution, "institution"
    if entities.payment_method:
        return entities.payment_method, "payment_method"
    return "", "unknown"


def _extract_institution(text: str) -> str:
    aliases = [
        "State Bank of India",
        "SBI",
        "CBI",
        "Central Bureau of Investigation",
        "Police",
        "Cyber Police",
    ]
    found = extract_institution_candidates(text, aliases)
    if found:
        return found[0]
    content = normalize_text(text)
    if "bank" in content:
        return "Bank"
    if "police" in content:
        return "Police"
    if "cbi" in content:
        return "CBI"
    return ""


def _payment_method_from_text(text: str) -> str:
    content = normalize_text(text)
    if any(token in content for token in ["upi", "gpay", "phonepe", "paytm"]):
        return "digital_wallet"
    if "cash" in content:
        return "cash"
    if "crypto" in content or "bitcoin" in content:
        return "crypto"
    return ""


def extract_entities(text: str) -> dict:
    phone_numbers = extract_phone_numbers(text)
    domains = extract_domains(text)
    emails = extract_emails(text)
    institution = _extract_institution(text)
    payment_method = _payment_method_from_text(text)
    return {
        "phone_numbers": phone_numbers,
        "domains": domains,
        "emails": emails,
        "institution": institution,
        "payment_method": payment_method,
        "observed_channels": infer_channels(text),
    }


def _merge_scores(
    artificial_urgency: float,
    social_coercion: float,
    institutional_deviation: float,
    contradiction_severity: Optional[str] = None,
    blacklist_hit: bool = False,
    domain_result: Optional[dict] = None,
) -> tuple[float, float, float]:
    deviation = institutional_deviation
    if contradiction_severity == "critical":
        deviation = max(deviation, 0.98)
    elif contradiction_severity == "high":
        deviation = max(deviation, 0.9)
    elif contradiction_severity == "medium":
        deviation = max(deviation, 0.75)
    elif contradiction_severity == "low":
        deviation = max(deviation, 0.55)

    if blacklist_hit:
        deviation = max(deviation, 1.0)
        social_coercion = max(social_coercion, 0.75)

    if domain_result:
        if domain_result.get("official_match"):
            deviation = min(deviation, 0.25)
        elif domain_result.get("typo_squatting_risk") in {"high", "critical"}:
            deviation = max(deviation, 0.9 if domain_result["typo_squatting_risk"] == "high" else 0.98)
        elif domain_result.get("typo_squatting_risk") == "medium":
            deviation = max(deviation, 0.7)

    return (
        min(max(artificial_urgency, 0.0), 1.0),
        min(max(social_coercion, 0.0), 1.0),
        min(max(deviation, 0.0), 1.0),
    )


def run_pipeline(text: str, case_id: Optional[str] = None) -> dict:
    case_id = case_id or f"CASE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    entities = extract_entities(text)
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

    elastic_result = {}
    if domains:
        elastic_result = fuzzy_match_domain(domains[0])
    elif institution:
        elastic_result = search_identity(institution)

    contradictions = detect_contradictions(
        message=text,
        institution=institution,
        observed_channels=observed_channels,
        rule_record=rule_record or None,
        domain=domains[0] if domains else None,
    )

    urgency = _score_artificial_urgency(text)
    coercion = _score_social_coercion(text)
    deviation = 0.12 if institution else 0.05
    if contradictions:
        primary = contradictions[0]
        severity = primary.get("severity", "low")
        if severity == "critical":
            deviation = 0.92
        elif severity == "high":
            deviation = 0.84
        elif severity == "medium":
            deviation = 0.68
        else:
            deviation = 0.48

        contradiction_type = primary.get("contradiction_type", "")
        if contradiction_type == "impossible_legal_procedure":
            urgency = max(urgency, 0.78)
            coercion = max(coercion, 0.92)
            deviation = max(deviation, 0.98)
        elif contradiction_type == "unauthorized_financial_instruction":
            urgency = max(urgency, 0.95)
            coercion = max(coercion, 0.55)
            deviation = max(deviation, 0.95)
        elif contradiction_type == "unofficial_communication_channel":
            urgency = max(urgency, 0.72)
            coercion = max(coercion, 0.45)
            deviation = max(deviation, 0.9)
        elif contradiction_type == "improper_messaging_platform":
            urgency = max(urgency, 0.68)
            coercion = max(coercion, 0.42)
            deviation = max(deviation, 0.88)

    if blacklist_hits:
        urgency = max(urgency, 0.7)
        coercion = max(coercion, 0.65)
        deviation = max(deviation, 0.95)

    if rule_record and not contradictions and institution:
        channels = {channel.lower() for channel in observed_channels}
        allowed = {channel.lower() for channel in rule_record.get("allowed_communication_channels", [])}
        prohibited = {channel.lower() for channel in rule_record.get("prohibited_channels", [])}
        if channels and channels.intersection(allowed):
            deviation = min(deviation, 0.2)
        if channels.intersection(prohibited):
            deviation = max(deviation, 0.88)

    if elastic_result:
        if elastic_result.get("official_match"):
            deviation = min(deviation, 0.25)
        elif elastic_result.get("typo_squatting_risk") in {"high", "critical"}:
            deviation = max(deviation, 0.9 if elastic_result["typo_squatting_risk"] == "high" else 0.98)

    urgency, coercion, deviation = _merge_scores(
        urgency,
        coercion,
        deviation,
        contradiction_severity=contradictions[0]["severity"] if contradictions else None,
        blacklist_hit=bool(blacklist_hits),
        domain_result=elastic_result,
    )

    threat_score = calculate_threat_score(urgency, coercion, deviation)
    risk_level = risk_level_from_score(threat_score)
    fraud_type = _classify_fraud_type(
        institution=institution,
        text=text,
        domain_risk=(elastic_result or {}).get("typo_squatting_risk", ""),
        blacklist_hit=bool(blacklist_hits),
    )

    confirmed_domain = domains[0] if domains else ""
    if elastic_result and elastic_result.get("matched_candidates"):
        confirmed_domain = elastic_result["matched_candidates"][0]["domain"] or confirmed_domain

    verification_sentences = []
    if rule_record:
        verification_sentences.append(
            f"MongoDB matched {rule_record.get('institution', institution or 'unknown institution')} and returned official channels {rule_record.get('allowed_communication_channels', [])}."
        )
        if contradictions:
            verification_sentences.append(contradictions[0]["explanation"])
        else:
            verification_sentences.append("No stored procedural deviation was found.")
    elif institution:
        verification_sentences.append("No institutional rule record was found in MongoDB.")
    else:
        verification_sentences.append("No institution was detected for MongoDB verification.")

    if elastic_result:
        verification_sentences.append(elastic_result.get("evidence_summary", ""))
    else:
        verification_sentences.append("No domain evidence was sent to Elasticsearch.")

    if blacklist_hits:
        verification_sentences.append(f"Blacklist hit for {len(blacklist_hits)} offender identifier(s).")

    reasoning_summary = _evidence_to_sentence(
        [
            f"Detected {institution}" if institution else "",
            f"Observed channels: {', '.join(observed_channels)}" if observed_channels else "",
            f"Urgency {urgency:.2f}, coercion {coercion:.2f}, deviation {deviation:.2f}",
            "Contradiction found" if contradictions else "No direct contradiction detected",
        ]
    )

    recommended_action = (
        "Treat as a confirmed scam, block the sender, and contact the institution only through official channels."
        if threat_score >= 0.8
        else "Use caution, verify the sender through official channels, and avoid clicking links or making payments."
    )

    report = ThreatReport(
        case_id=case_id,
        timestamp=timestamp,
        threat_score=threat_score,
        risk_level=risk_level,
        fraud_type=fraud_type,
        behavioral_analysis=BehavioralAnalysis(
            artificial_urgency=round(urgency, 4),
            social_coercion=round(coercion, 4),
            institutional_deviation=round(deviation, 4),
        ),
        detected_entities=DetectedEntities(
            institution=institution,
            phone_number=phone_numbers[0] if phone_numbers else "",
            website=confirmed_domain,
            payment_method=payment_method,
        ),
        verification_results=VerificationResults(
            mongodb_check=_evidence_to_sentence(
                [
                    verification_sentences[0] if len(verification_sentences) > 0 else "",
                    verification_sentences[1] if len(verification_sentences) > 1 else "",
                    verification_sentences[3] if len(verification_sentences) > 3 else "",
                ]
            ),
            elastic_check=elastic_result.get("recommended_interpretation", "No Elasticsearch evidence available.")
            if elastic_result
            else "No Elasticsearch evidence available.",
        ),
        reasoning_summary=reasoning_summary,
        recommended_action=recommended_action,
        guardian_alert_required=threat_score >= 0.8,
        blacklist_candidate=threat_score >= 0.8,
        contradictions=contradictions,
        extracted_entities={
            "phone_numbers": phone_numbers,
            "domains": domains,
            "emails": emails,
            "observed_channels": observed_channels,
        },
        blacklist_hits=blacklist_hits,
    )

    if report.blacklist_candidate:
        offender_identity, identity_type = _primary_identity(report.detected_entities)
        if offender_identity:
            save_blacklist_entry(
                {
                    "offender_identity": offender_identity,
                    "identity_type": identity_type,
                    "reported_carrier_platform": observed_channels[0] if observed_channels else "text",
                    "claimed_persona": institution or fraud_type,
                    "calculated_threat_score": threat_score,
                    "scam_type": fraud_type,
                    "timestamp_logged": timestamp,
                }
            )

    # New: Call Guardian Alert Service if required
    if report.guardian_alert_required:
        customer_phone = report.detected_entities.phone_number
        customer_email = emails[0] if emails else "" # Assuming first extracted email is customer email for now

        customer_contact = {}
        if customer_phone:
            customer_contact["phone"] = customer_phone
        if customer_email:
            customer_contact["email"] = customer_email

        alert_results = send_fraud_alert(
            threat_score=report.threat_score,
            case_id=report.case_id,
            summary=report.reasoning_summary,
            customer_contact=customer_contact
        )
        # Optionally, you might want to log or store alert_results
        # For now, I'll just print it for observability
        print(f"Guardian Alert Service Results for {report.case_id}: {alert_results}")

    return report.to_dict()


def analyze_text(text: str, case_id: Optional[str] = None) -> dict:
    return run_pipeline(text=text, case_id=case_id)
