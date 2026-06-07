from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_environment() -> None:
    if load_dotenv is not None:
        root = Path(__file__).resolve().parents[2]
        load_dotenv(root / ".env")
        load_dotenv(Path.cwd() / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a decimal number between 0 and 1.") from exc


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    mongodb_uri: str
    mongodb_database: str
    elastic_node: str
    elastic_api_key: str
    elasticsearch_index: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    sendgrid_api_key: str
    sendgrid_from_email: str
    fraud_alert_threshold: float
    production_mode: bool
    strict_production_mode: bool
    agent_builder_webhook_url: str
    gcp_project_id: str


def get_settings() -> Settings:
    load_environment()
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        mongodb_uri=os.getenv("MONGODB_URI", ""),
        mongodb_database=os.getenv("MONGODB_DATABASE", "fraud_agent"),
        elastic_node=os.getenv("ELASTIC_NODE", ""),
        elastic_api_key=os.getenv("ELASTIC_API_KEY", ""),
        elasticsearch_index=os.getenv("ELASTICSEARCH_INDEX", "anti-scam-threat-registry"),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
        twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
        sendgrid_api_key=os.getenv("SENDGRID_API_KEY", ""),
        sendgrid_from_email=os.getenv("SENDGRID_FROM_EMAIL", ""),
        fraud_alert_threshold=env_float("FRAUD_ALERT_THRESHOLD", 0.8),
        production_mode=env_bool("PRODUCTION_MODE", False),
        strict_production_mode=env_bool("STRICT_PRODUCTION_MODE", False),
        agent_builder_webhook_url=os.getenv("AGENT_BUILDER_WEBHOOK_URL", ""),
        gcp_project_id=os.getenv("GCP_PROJECT_ID", ""),
    )


def validate_startup(required: Iterable[str] | None = None) -> None:
    settings = get_settings()
    names = list(required or [])
    if settings.strict_production_mode:
        names.extend(["GEMINI_API_KEY", "MONGODB_URI", "ELASTIC_NODE", "ELASTIC_API_KEY"])
    missing = [name for name in dict.fromkeys(names) if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required production configuration: "
            + ", ".join(missing)
            + ". Set these variables in .env or the runtime environment."
        )
