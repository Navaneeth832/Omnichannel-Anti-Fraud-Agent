from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Any

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_environment() -> None:
    if load_dotenv is not None:
        root = Path(__file__).resolve().parents[2]
        load_dotenv(root / ".env")
        load_dotenv(Path.cwd() / ".env")


def get_env(key: str, default: Any = None) -> Any:
    # Try Streamlit secrets first
    if hasattr(st, "secrets") and key in st.secrets:
        return st.secrets[key]
    
    # Fallback to environment variables
    load_environment()
    return os.getenv(key, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = get_env(name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    value = get_env(name)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a decimal number.") from exc


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
    trusted_guardian_name: str
    trusted_guardian_phone: str
    trusted_guardian_email: str


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=get_env("GEMINI_API_KEY", ""),
        mongodb_uri=get_env("MONGODB_URI", ""),
        mongodb_database=get_env("MONGODB_DATABASE", "fraud_agent"),
        elastic_node=get_env("ELASTIC_NODE", ""),
        elastic_api_key=get_env("ELASTIC_API_KEY", ""),
        elasticsearch_index=get_env("ELASTICSEARCH_INDEX", "anti-scam-threat-registry"),
        twilio_account_sid=get_env("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=get_env("TWILIO_AUTH_TOKEN", ""),
        twilio_phone_number=get_env("TWILIO_PHONE_NUMBER", ""),
        sendgrid_api_key=get_env("SENDGRID_API_KEY", ""),
        sendgrid_from_email=get_env("SENDGRID_FROM_EMAIL", ""),
        fraud_alert_threshold=env_float("FRAUD_ALERT_THRESHOLD", 0.8),
        production_mode=env_bool("PRODUCTION_MODE", False),
        strict_production_mode=env_bool("STRICT_PRODUCTION_MODE", False),
        agent_builder_webhook_url=get_env("AGENT_BUILDER_WEBHOOK_URL", ""),
        gcp_project_id=get_env("GCP_PROJECT_ID", ""),
        trusted_guardian_name=get_env("TRUSTED_GUARDIAN_NAME", "Trusted Guardian"),
        trusted_guardian_phone=get_env("TRUSTED_GUARDIAN_PHONE", ""),
        trusted_guardian_email=get_env("TRUSTED_GUARDIAN_EMAIL", ""),
    )


def validate_startup(required: Iterable[str] | None = None) -> None:
    settings = get_settings()
    names = list(required or [])
    if settings.strict_production_mode:
        names.extend(["GEMINI_API_KEY", "MONGODB_URI", "ELASTIC_NODE", "ELASTIC_API_KEY"])
    
    missing = []
    for name in dict.fromkeys(names):
        if not get_env(name):
            missing.append(name)
            
    if missing:
        raise RuntimeError(
            "Missing required production configuration: "
            + ", ".join(missing)
            + ". Set these variables in .env or Streamlit secrets."
        )