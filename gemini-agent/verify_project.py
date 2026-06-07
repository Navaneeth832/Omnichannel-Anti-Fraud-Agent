from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

from fraud_agent.config import get_settings
from fraud_agent.mcp.elastic_adapter import ensure_index_mapping
from fraud_agent.mcp.mongo_adapter import ensure_schema_and_indexes
from fraud_agent.system_health import check_system_health

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str, failures: list[str]) -> None:
    print(f"FAIL: {message}")
    failures.append(message)


def dashboard_uses_orchestrator() -> bool:
    source = (ROOT / "dashboard" / "app" / "streamlit_app.py").read_text(encoding="utf-8")
    return "from fraud_agent.orchestrator import analyze_text" in source and "analyze_text(" in source


def no_forbidden_runtime_patterns() -> list[str]:
    banned = ["rand" + "om.", "synthetic threat", "nonproduction analysis", "example-only scoring", "canned signal", "stub implementation"]
    offenders = []
    for path in [*ROOT.glob("dashboard/**/*.py"), *ROOT.glob("gemini-agent/fraud_agent/**/*.py")]:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(term in text for term in banned):
            offenders.append(str(path.relative_to(ROOT)))
    return offenders


def main() -> int:
    failures: list[str] = []
    settings = get_settings()
    health = check_system_health()
    print("Omnichannel Anti-Fraud Agent Verification")
    for component, data in health.items():
        print(f"{component}: {data.get('status')}")
    if not dashboard_uses_orchestrator():
        fail("dashboard is not wired to orchestrator", failures)
    offenders = no_forbidden_runtime_patterns()
    if offenders:
        fail("forbidden runtime patterns found in " + ", ".join(offenders), failures)
    required = {
        "Gemini reachable/configured": bool(settings.gemini_api_key),
        "MongoDB reachable": health["mongodb"]["status"] == "CONNECTED",
        "Elasticsearch reachable": health["elasticsearch"]["status"] == "CONNECTED",
        "Twilio configured": health["twilio"]["status"] == "CONNECTED",
        "SendGrid configured": health["sendgrid"]["status"] == "CONNECTED",
    }
    for label, ok in required.items():
        if not ok:
            fail(label, failures)
    try:
        ensure_schema_and_indexes()
    except Exception as exc:
        fail(f"required MongoDB collections/indexes unavailable: {exc}", failures)
    try:
        ensure_index_mapping()
    except Exception as exc:
        fail(f"Elasticsearch index mapping unavailable: {exc}", failures)
    if failures:
        return 1
    print("PASS: production verification succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
