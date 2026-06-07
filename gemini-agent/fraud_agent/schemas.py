from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


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
class GuardianProfile:
    guardian_name: str
    guardian_phone: str = ""
    guardian_email: str = ""
    escalation_enabled: bool = True


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
    gemini_reasoning: Dict[str, Any] = field(default_factory=dict)
    alert_status: str = "not_required"

    def to_dict(self) -> dict:
        return asdict(self)
