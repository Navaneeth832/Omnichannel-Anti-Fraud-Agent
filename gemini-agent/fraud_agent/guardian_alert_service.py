from __future__ import annotations

import logging
from typing import Any, Dict, List

from .config import get_settings
from .mcp.mongo_adapter import get_guardian_profiles, save_alert_log
from .schemas import GuardianProfile

try:
    from twilio.rest import Client as TwilioClient
except ImportError:  # pragma: no cover
    TwilioClient = None

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
except ImportError:  # pragma: no cover
    SendGridAPIClient = None
    Mail = None

logger = logging.getLogger(__name__)


def _trusted_profiles() -> List[GuardianProfile]:
    profiles = []
    for item in get_guardian_profiles():
        profile = GuardianProfile(
            guardian_name=item.get("guardian_name", "Trusted Guardian"),
            guardian_phone=item.get("guardian_phone", ""),
            guardian_email=item.get("guardian_email", ""),
            escalation_enabled=bool(item.get("escalation_enabled", True)),
        )
        if profile.escalation_enabled and (profile.guardian_phone or profile.guardian_email):
            profiles.append(profile)
    return profiles


def _send_twilio_sms(to_phone_number: str, message_body: str) -> Dict[str, Any]:
    settings = get_settings()
    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
        return {"status": "skipped", "message": "Twilio is not fully configured."}
    if TwilioClient is None:
        return {"status": "skipped", "message": "Twilio client is not installed."}
    try:
        client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(to=to_phone_number, from_=settings.twilio_phone_number, body=message_body)
        return {"status": "success", "sid": message.sid}
    except Exception as exc:
        return {"status": "failed", "message": str(exc)}


def _send_sendgrid_email(to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
    settings = get_settings()
    if not all([settings.sendgrid_api_key, settings.sendgrid_from_email]):
        return {"status": "skipped", "message": "SendGrid is not fully configured."}
    if SendGridAPIClient is None or Mail is None:
        return {"status": "skipped", "message": "SendGrid client is not installed."}
    try:
        message = Mail(from_email=settings.sendgrid_from_email, to_emails=to_email, subject=subject, html_content=html_content)
        response = SendGridAPIClient(settings.sendgrid_api_key).send(message)
        return {"status": "success", "status_code": response.status_code, "body": (response.body or b"").decode("utf-8", "replace") if isinstance(response.body, bytes) else response.body}
    except Exception as exc:
        return {"status": "failed", "message": str(exc)}


def send_fraud_alert(threat_score: float, case_id: str, summary: str, trusted_contacts: List[GuardianProfile] | None = None) -> Dict[str, Any]:
    settings = get_settings()
    if threat_score < settings.fraud_alert_threshold:
        return {"status": "skipped", "message": "Threat score below alert threshold.", "logs": []}
    contacts = trusted_contacts if trusted_contacts is not None else _trusted_profiles()
    if not contacts:
        log = save_alert_log(case_id, "guardian", "skipped", {"message": "No trusted guardian contacts configured."})
        return {"status": "skipped", "message": "No trusted guardian contacts configured.", "logs": [log]}
    alert_message = f"Fraud alert for case {case_id}. Threat score {threat_score:.2f}. {summary}"
    subject = f"Fraud Alert: Case {case_id}"
    results: Dict[str, Any] = {"status": "sent", "logs": []}
    for profile in contacts:
        if profile.guardian_phone:
            response = _send_twilio_sms(profile.guardian_phone, alert_message)
            results["logs"].append(save_alert_log(case_id, "twilio", response.get("status", "unknown"), {"guardian_name": profile.guardian_name, **response}))
        if profile.guardian_email:
            response = _send_sendgrid_email(profile.guardian_email, subject, f"<p>{alert_message}</p>")
            results["logs"].append(save_alert_log(case_id, "sendgrid", response.get("status", "unknown"), {"guardian_name": profile.guardian_name, **response}))
    if not results["logs"]:
        results["status"] = "skipped"
    return results
