from __future__ import annotations

from typing import Any, Dict

from .config import get_settings
from .mcp import elastic_adapter, mongo_adapter


def _status(ok: bool, configured: bool) -> str:
    if ok:
        return "CONNECTED"
    return "DISCONNECTED" if configured else "MISCONFIGURED"


def check_gemini_status() -> Dict[str, Any]:
    settings = get_settings()
    return {"status": _status(bool(settings.gemini_api_key), bool(settings.gemini_api_key))}


def check_mongodb_status() -> Dict[str, Any]:
    settings = get_settings()
    if not settings.mongodb_uri:
        return {"status": "MISCONFIGURED"}
    try:
        mongo_adapter.ensure_schema_and_indexes()
        return {"status": "CONNECTED"}
    except Exception as exc:
        return {"status": "DISCONNECTED", "error": str(exc)}


def check_elasticsearch_status() -> Dict[str, Any]:
    settings = get_settings()
    if not (settings.elastic_node and settings.elastic_api_key):
        return {"status": "MISCONFIGURED"}
    try:
        elastic_adapter.ensure_index_mapping()
        return {"status": "CONNECTED"}
    except Exception as exc:
        return {"status": "DISCONNECTED", "error": str(exc)}


def check_twilio_status() -> Dict[str, str]:
    settings = get_settings()
    return {"status": _status(bool(settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number), bool(settings.twilio_account_sid or settings.twilio_auth_token or settings.twilio_phone_number))}


def check_sendgrid_status() -> Dict[str, str]:
    settings = get_settings()
    return {"status": _status(bool(settings.sendgrid_api_key and settings.sendgrid_from_email), bool(settings.sendgrid_api_key or settings.sendgrid_from_email))}


def check_system_health() -> Dict[str, Any]:
    return {"gemini": check_gemini_status(), "mongodb": check_mongodb_status(), "elasticsearch": check_elasticsearch_status(), "twilio": check_twilio_status(), "sendgrid": check_sendgrid_status()}


if __name__ == "__main__":
    import json
    print(json.dumps(check_system_health(), indent=2))
