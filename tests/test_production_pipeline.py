from __future__ import annotations

import pytest

from fraud_agent.guardian_alert_service import send_fraud_alert
from fraud_agent.mcp.mongo_adapter import list_alert_logs, list_cases, save_case
from fraud_agent.multimodal import analyze_audio, analyze_image, analyze_pdf, extracted_identity_summary
from fraud_agent.orchestrator import analyze_text


def test_text_analysis_is_deterministic():
    text = "SBI officer on WhatsApp says your account will be frozen in 10 minutes unless you pay at sbi-secure-login.com."
    first = analyze_text(text, case_id="CASE-DETERMINISTIC")
    second = analyze_text(text, case_id="CASE-DETERMINISTIC")
    assert first["threat_score"] == second["threat_score"]
    assert first["fraud_type"] == second["fraud_type"]


def test_audio_transcription_enters_orchestrator(monkeypatch):
    monkeypatch.setattr("fraud_agent.multimodal.transcribe_audio", lambda data, suffix='.wav': "CBI WhatsApp video arrest immediately")
    result = analyze_audio(b"audio", suffix=".wav", case_id="CASE-AUDIO")
    assert result["case_id"] == "CASE-AUDIO"
    assert result["guardian_alert_required"] is True


def test_image_ocr_enters_orchestrator(monkeypatch):
    monkeypatch.setattr("fraud_agent.multimodal.extract_image_text", lambda data: "Police demand immediate transfer by WhatsApp under digital arrest")
    result = analyze_image(b"image", case_id="CASE-IMAGE")
    assert result["case_id"] == "CASE-IMAGE"
    assert result["threat_score"] >= 0.8


def test_pdf_text_enters_orchestrator(monkeypatch):
    monkeypatch.setattr("fraud_agent.multimodal.extract_pdf_text", lambda data: "SBI urgent payment at sbi-secure-login.com from fraud@example.com call +91 9876543210")
    result = analyze_pdf(b"pdf", case_id="CASE-PDF")
    assert result["case_id"] == "CASE-PDF"
    assert "sbi-secure-login.com" in result["extracted_entities"]["domains"]


def test_identity_extraction_summary():
    summary = extracted_identity_summary("Email help@bank.example, call +1 415 555 1212, visit secure-bank.example for SBI.")
    assert "bank.example" in summary["domains"]
    assert summary["emails"] == ["help@bank.example"]
    assert summary["phone_numbers"]
    assert "SBI" in summary["institutions"]


def test_case_persistence():
    report = analyze_text("State Bank of India statement available in official app.", case_id="CASE-PERSIST")
    cases = list_cases()
    assert any(case["case_id"] == report["case_id"] for case in cases)


def test_alert_generation_uses_only_trusted_contacts(monkeypatch):
    sent_to = []
    monkeypatch.setenv("TRUSTED_GUARDIAN_PHONE", "+15551234567")
    monkeypatch.setenv("TRUSTED_GUARDIAN_EMAIL", "guardian@example.com")
    monkeypatch.setattr("fraud_agent.guardian_alert_service._send_twilio_sms", lambda phone, body: sent_to.append(phone) or {"status": "success"})
    monkeypatch.setattr("fraud_agent.guardian_alert_service._send_sendgrid_email", lambda email, subject, html: sent_to.append(email) or {"status": "success"})
    result = send_fraud_alert(0.95, "CASE-ALERT", "Scammer identifiers must not receive alerts.")
    assert result["status"] == "sent"
    assert "+15551234567" in sent_to
    assert "guardian@example.com" in sent_to
    assert all(value not in {"+919876543210", "scammer@example.com"} for value in sent_to)
    assert any(log["case_id"] == "CASE-ALERT" for log in list_alert_logs())


def test_dashboard_imports_orchestrator():
    source = open("dashboard/app/streamlit_app.py", encoding="utf-8").read()
    assert "from fraud_agent.orchestrator import analyze_text" in source
    assert "from fraud_agent.multimodal import analyze_audio, analyze_image, analyze_pdf" in source
