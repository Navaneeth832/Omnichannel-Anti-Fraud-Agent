from __future__ import annotations

import unittest

from fraud_agent.mcp.mongo_adapter import save_blacklist_entry
from fraud_agent.orchestrator import analyze_text


def _assert_common_scam_properties(testcase: unittest.TestCase, result: dict) -> None:
    testcase.assertGreaterEqual(result["threat_score"], 0.8)
    testcase.assertEqual(result["risk_level"], "CRITICAL")
    testcase.assertTrue(result["guardian_alert_required"])
    testcase.assertTrue(result["blacklist_candidate"])
    testcase.assertTrue(result["reasoning_summary"])
    testcase.assertTrue(result["verification_results"]["mongodb_check"])
    testcase.assertTrue(result["verification_results"]["elastic_check"])


class Phase3IntegrationTests(unittest.TestCase):
    def test_digital_arrest_scam(self):
        result = analyze_text(
            "This is cyber police. Do not disconnect this call. You are under digital arrest for money laundering. "
            "Transfer funds to the safe account immediately."
        )
        _assert_common_scam_properties(self, result)
        self.assertEqual(result["fraud_type"], "digital_arrest_scam")
        self.assertGreaterEqual(result["behavioral_analysis"]["institutional_deviation"], 0.9)
        self.assertTrue(result["contradictions"])
        self.assertEqual(result["contradictions"][0]["contradiction_type"], "impossible_legal_procedure")

    def test_fake_sbi_officer(self):
        result = analyze_text(
            "SBI officer on WhatsApp says your account will be frozen in 10 minutes unless you make immediate payment."
        )
        _assert_common_scam_properties(self, result)
        self.assertEqual(result["fraud_type"], "banking_impersonation")
        self.assertIn(result["detected_entities"]["institution"], {"SBI", "State Bank of India"})
        self.assertTrue(
            any(
                contradiction["contradiction_type"]
                in {"unofficial_communication_channel", "unauthorized_financial_instruction"}
                for contradiction in result["contradictions"]
            )
        )

    def test_whatsapp_cbi_scam(self):
        result = analyze_text(
            "CBI officer on WhatsApp says you are under investigation and must stay on the line for a video arrest."
        )
        _assert_common_scam_properties(self, result)
        self.assertEqual(result["fraud_type"], "authority_impersonation")
        self.assertTrue(
            any(
                contradiction["contradiction_type"]
                in {"improper_messaging_platform", "impossible_legal_procedure"}
                for contradiction in result["contradictions"]
            )
        )

    def test_blacklisted_number(self):
        save_blacklist_entry(
            {
                "offender_identity": "+919876543210",
                "identity_type": "phone_number",
                "reported_carrier_platform": "whatsapp",
                "claimed_persona": "Police officer",
                "calculated_threat_score": 0.97,
                "scam_type": "authority_impersonation",
                "timestamp_logged": "2026-06-07T00:00:00Z",
            }
        )
        result = analyze_text(
            "Police officer on call says the number +91 9876543210 is under review and demands an immediate transfer."
        )
        _assert_common_scam_properties(self, result)
        self.assertTrue(result["blacklist_hits"])
        self.assertEqual(result["blacklist_hits"][0]["identity_type"], "phone_number")
        self.assertGreaterEqual(result["behavioral_analysis"]["institutional_deviation"], 0.95)

    def test_clean_legitimate_message(self):
        result = analyze_text(
            "State Bank of India reminder: your monthly statement is available in the official mobile app. "
            "If you need support, please visit the branch or use the registered customer care channel."
        )
        self.assertLessEqual(result["threat_score"], 0.3)
        self.assertEqual(result["risk_level"], "LOW")
        self.assertFalse(result["guardian_alert_required"])
        self.assertFalse(result["blacklist_candidate"])
        self.assertEqual(result["contradictions"], [])
        self.assertTrue(result["verification_results"]["mongodb_check"])


if __name__ == "__main__":
    unittest.main()

