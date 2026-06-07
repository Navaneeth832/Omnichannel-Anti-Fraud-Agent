from __future__ import annotations

from typing import Iterable, Optional

from .utils import normalize_text


def _contains_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def detect_contradiction(
    message: str,
    institution: Optional[str] = None,
    observed_channels: Optional[Iterable[str]] = None,
    rule_record: Optional[dict] = None,
    domain: Optional[str] = None,
) -> dict:
    content = normalize_text(message)
    channels = {normalize_text(channel) for channel in (observed_channels or []) if channel}
    institution_normalized = normalize_text(institution or "")
    allowed_channels = {
        normalize_text(channel)
        for channel in (rule_record or {}).get("allowed_communication_channels", [])
        if channel
    }
    prohibited_channels = {
        normalize_text(channel)
        for channel in (rule_record or {}).get("prohibited_channels", [])
        if channel
    }

    if domain:
        domain_norm = normalize_text(domain)
        if _contains_any(content, ["secure", "verify", "payment", "kyc", "freeze", "arrest"]):
            if any(token in domain_norm for token in ["secure", "verify", "alert", "kyc", "support", "helpdesk"]):
                return {
                    "contradiction_type": "typosquatting_domain",
                    "severity": "high",
                    "explanation": f"The domain '{domain}' mimics institutional branding while supporting a deceptive request.",
                }

    if institution_normalized in {"cbi", "central bureau of investigation", "police", "cyber police"}:
        if _contains_any(content, ["digital arrest", "video arrest", "safe account", "stay on the line"]):
            return {
                "contradiction_type": "impossible_legal_procedure",
                "severity": "critical",
                "explanation": "The message describes a fake arrest workflow that is not a valid legal process.",
            }

    if institution_normalized in {"sbi", "state bank of india", "bank"}:
        if _contains_any(content, ["immediate payment", "transfer immediately", "safe account", "urgent payment"]):
            return {
                "contradiction_type": "unauthorized_financial_instruction",
                "severity": "high",
                "explanation": "Banks do not demand instant settlement through an unverified personal conversation channel.",
            }

    if rule_record:
        if channels and prohibited_channels and channels.intersection(prohibited_channels):
            bad_channel = sorted(channels.intersection(prohibited_channels))[0]
            return {
                "contradiction_type": "unofficial_communication_channel",
                "severity": "high" if bad_channel in {"whatsapp", "phone", "sms"} else "medium",
                "explanation": (
                    f"{institution or 'The institution'} does not use {bad_channel} "
                    "for the claimed action according to stored institutional rules."
                ),
            }

        if channels and allowed_channels and not channels.intersection(allowed_channels):
            return {
                "contradiction_type": "unsupported_communication_channel",
                "severity": "medium",
                "explanation": (
                    f"The observed channel set {sorted(channels)} does not match the stored official channels "
                    f"for {institution or 'the institution'}."
                ),
            }

    if institution and _contains_any(content, ["whatsapp", "telegram", "signal"]) and channels:
        if any(channel in {"whatsapp", "telegram", "signal"} for channel in channels):
            return {
                "contradiction_type": "improper_messaging_platform",
                "severity": "high",
                "explanation": f"{institution} should not be issuing official enforcement or payment instructions on consumer chat platforms.",
            }

    return {
        "contradiction_type": "",
        "severity": "low",
        "explanation": "No direct institutional contradiction detected.",
    }


def detect_contradictions(
    message: str,
    institution: Optional[str] = None,
    observed_channels: Optional[Iterable[str]] = None,
    rule_record: Optional[dict] = None,
    domain: Optional[str] = None,
) -> list[dict]:
    contradiction = detect_contradiction(
        message=message,
        institution=institution,
        observed_channels=observed_channels,
        rule_record=rule_record,
        domain=domain,
    )
    if contradiction.get("contradiction_type"):
        return [contradiction]
    return []
