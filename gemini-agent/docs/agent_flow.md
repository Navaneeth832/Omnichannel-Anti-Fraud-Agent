# Agent Execution Flow

## Purpose

This document defines the sequential reasoning and tool invocation pipeline for the Omnichannel Anti-Fraud Agent (Dual MCP). It describes how the ADK agent running on Vertex AI Agent Runtime processes multimodal evidence, invokes verification tools, computes risk, and triggers downstream actions.

## End-to-End Pipeline

```text
User Input
   |
   v
Normalize Evidence
   |
   v
Gemini Entity Extraction
   |
   +--> Institution? ---- yes ----> MongoDB MCP Verification
   |
   +--> Domain? --------- yes ----> Elasticsearch MCP Verification
   |
   v
Behavioral Threat Analysis
   |
   v
Evidence Fusion
   |
   v
Threat Score + Risk Level
   |
   v
Structured Threat Report
   |
   +--> score >= 0.8 ----> Guardian Alert Workflow
   |
   +--> blacklist_candidate ----> Persist offender indicators
   |
   v
Response to Frontend
```

## Sequential Execution Stages

## Stage 0: Request Initialization

The Streamlit frontend sends a case payload to the agent with `case_id`, `user_id`, `channel_type`, `input_type`, raw evidence, and locale and timestamp metadata.

The agent runtime opens a root trace span and assigns correlation IDs that follow all tool calls and downstream events.

## Stage 1: Evidence Normalization

All evidence is converted into a single reasoning package.

| Input | Normalization |
| --- | --- |
| Text | Trim, de-duplicate whitespace, preserve quoted message content |
| Audio | Speech transcript extraction, speaker-role hints |
| Image | OCR extraction, URL/phone/logo capture |

Normalized payload:

```json
{
  "case_id": "CASE-2026-000184",
  "channel_type": "whatsapp",
  "input_type": "image",
  "normalized_text": "Your bank account will be frozen in 10 minutes unless you verify at sbi-kvc-alert.in",
  "extracted_media_entities": {
    "phones": ["+91-98XXXXXX12"],
    "urls": ["https://sbi-kvc-alert.in"],
    "logos": ["State Bank of India"]
  }
}
```

## Stage 2: Entity Extraction with Gemini

Gemini 3.1 Flash extracts structured entities from the normalized evidence.

Target entities:

- Institution
- Website or domain
- Phone number
- Payment method
- Legal or enforcement claims
- Threat language and coercion signals

Expected internal extraction object:

```json
{
  "institution": "State Bank of India",
  "website": "sbi-kvc-alert.in",
  "phone_number": "+91-98XXXXXX12",
  "payment_method": null,
  "claims": [
    "Account will be frozen in 10 minutes",
    "Verify immediately through provided website"
  ]
}
```

## Stage 3: Tool Routing Decision

The agent evaluates whether tool verification is necessary.

| Condition | Action |
| --- | --- |
| Institution detected | Invoke MongoDB MCP |
| Domain or URL detected | Invoke Elasticsearch MCP |
| Neither detected | Continue with behavioral scoring only |
| Tool unavailable | Mark verification state as degraded and continue |

Routing pseudocode:

```text
if institution != null:
    call mongodb_mcp.validate_institution_protocol()

if website != null:
    call elastic_mcp.verify_domain_similarity()
```

## Stage 4: MongoDB MCP Verification

If an institution is mentioned, the agent sends a request to MongoDB MCP to validate institutional and procedural legitimacy.

Verification goals:

- Confirm known official communication channels
- Validate legal notification procedures
- Detect protocol violations
- Check whether the requested action matches normal institutional behavior

## Stage 5: Elasticsearch MCP Verification

If a domain is present, the agent sends a request to Elasticsearch MCP.

Verification goals:

- Search for official brand domains
- Compute Levenshtein distance
- Compute Jaro-Winkler similarity
- Flag likely typo-squatting or phishing domains

## Stage 6: Behavioral Threat Analysis

Gemini computes the three threat dimensions using the project topology:

| Dimension | Weight | Detection Focus |
| --- | --- | --- |
| Artificial Urgency | 0.25 | Time pressure, payment deadline, panic |
| Social Coercion | 0.25 | Fear, secrecy, authority pressure, isolation |
| Institutional Deviations | 0.50 | Unofficial channels, illegal or abnormal procedures |

## Stage 7: Evidence Fusion

Gemini fuses:

- Input content
- Extracted entities
- MongoDB procedural evidence
- Elasticsearch domain evidence
- Historical or blacklist matches if available

Fusion principles:

- Institutional deviation score is increased when MongoDB returns protocol violations
- Institutional deviation score is increased when phishing domains impersonate institutions
- A missing tool result does not imply safety
- Strong direct behavioral evidence can still produce a high risk score

## Stage 8: Threat Score Computation

Threat score formula:

```text
Threat Score =
  (Artificial Urgency * 0.25) +
  (Social Coercion * 0.25) +
  (Institutional Deviations * 0.50)
```

Risk bands:

| Score Range | Risk Level |
| --- | --- |
| 0.00 - 0.30 | LOW |
| 0.31 - 0.60 | MEDIUM |
| 0.61 - 0.80 | HIGH |
| 0.81 - 1.00 | CRITICAL |

## Stage 9: Threat Report Generation

The output must conform to the existing project schema.

```json
{
  "case_id": "CASE-2026-000184",
  "timestamp": "2026-05-29T16:32:11Z",
  "threat_score": 0.91,
  "risk_level": "CRITICAL",
  "fraud_type": "banking_impersonation",
  "behavioral_analysis": {
    "artificial_urgency": 0.92,
    "social_coercion": 0.71,
    "institutional_deviation": 0.95
  },
  "detected_entities": {
    "institution": "State Bank of India",
    "phone_number": "+91-98XXXXXX12",
    "website": "sbi-kvc-alert.in",
    "payment_method": ""
  },
  "verification_results": {
    "mongodb_check": "Institution does not issue KYC freeze notices over WhatsApp or personal mobile numbers.",
    "elastic_check": "Domain is highly similar to official brand domain and flagged as probable typo-squatting."
  },
  "reasoning_summary": "The message combines extreme time pressure with a suspicious domain and non-official communication pattern.",
  "recommended_action": "Do not click the link. Contact the bank through official channels and report the sender.",
  "guardian_alert_required": true,
  "blacklist_candidate": true
}
```

## Stage 10: Guardian Alert Decision

If `threat_score >= 0.8`, the agent publishes a critical fraud event. Eventarc routes the event to Cloud Functions which send Twilio and SendGrid notifications and optionally notify a guardian or case-response team.

## Stage 11: Blacklist Persistence

If the case is marked as a blacklist candidate, offender indicators such as phone numbers, phishing domains, payment handles, and impersonated institutions are persisted for future lookup.

## Tool Invocation Flow

```text
ADK Agent
  |
  +--> extract_entities()
  |
  +--> if institution:
  |       mongodb_mcp.validate_institution_protocol()
  |
  +--> if domain:
  |       elastic_mcp.verify_domain_similarity()
  |
  +--> compute_behavioral_scores()
  |
  +--> synthesize_verification_evidence()
  |
  +--> generate_threat_report()
  |
  +--> if score >= 0.8:
          emit_guardian_alert_event()
```

## Error Handling and Fallbacks

| Failure Mode | System Behavior |
| --- | --- |
| MongoDB MCP timeout | Continue analysis, mark verification as unavailable |
| Elastic MCP timeout | Continue analysis, lower confidence in domain verification |
| Invalid OCR | Fall back to text-only behavioral analysis |
| Alert delivery failure | Retry through Cloud Functions, preserve event record |
| Schema generation failure | Re-prompt Gemini with strict JSON schema enforcement |

## Latency Budget Guidance

| Stage | Target Latency |
| --- | --- |
| Preprocessing | 0.5 to 2.0 s |
| Gemini extraction and scoring | 1.0 to 3.0 s |
| MongoDB MCP | 0.2 to 1.0 s |
| Elasticsearch MCP | 0.2 to 1.0 s |
| Report generation | 0.5 to 1.5 s |
| Total interactive response | 2.0 to 6.5 s |

## Why This Flow Works

The pipeline is intentionally sequential at the reasoning level and conditional at the tool level. Every major decision point is explainable, tool calls are grounded in extracted entities, alerting is threshold-based and event-driven, and outputs remain structured and suitable for downstream automation.
