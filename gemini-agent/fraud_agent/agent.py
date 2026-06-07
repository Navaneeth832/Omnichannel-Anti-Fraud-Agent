from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .orchestrator import analyze_text, run_pipeline

try:
    from google.adk.agents import Agent
except Exception:  # pragma: no cover - optional dependency
    Agent = None


class BehavioralAnalysis(BaseModel):
    artificial_urgency: float = Field(default=0.0, ge=0.0, le=1.0)
    social_coercion: float = Field(default=0.0, ge=0.0, le=1.0)
    institutional_deviation: float = Field(default=0.0, ge=0.0, le=1.0)


class DetectedEntities(BaseModel):
    institution: str = ""
    phone_number: str = ""
    website: str = ""
    payment_method: str = ""


class VerificationResults(BaseModel):
    mongodb_check: str = ""
    elastic_check: str = ""


class ThreatReport(BaseModel):
    case_id: str
    timestamp: str
    threat_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    fraud_type: str
    behavioral_analysis: BehavioralAnalysis
    detected_entities: DetectedEntities
    verification_results: VerificationResults
    reasoning_summary: str
    recommended_action: str
    guardian_alert_required: bool
    blacklist_candidate: bool
    contradictions: list[dict] = Field(default_factory=list)
    extracted_entities: dict = Field(default_factory=dict)
    blacklist_hits: list[dict] = Field(default_factory=list)


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "system_prompt" / "fraud_topology.txt"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except OSError:
        return "You are an anti-fraud analysis agent."


SYSTEM_PROMPT = _load_system_prompt()

root_agent = None
if Agent is not None:  # pragma: no cover - optional dependency
    root_agent = Agent(
        name="fraud_detector",
        model="gemini-2.5-flash",
        instruction=SYSTEM_PROMPT,
        output_schema=ThreatReport,
    )

