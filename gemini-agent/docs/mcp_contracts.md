# MCP Contracts

## Purpose

This document defines the Model Context Protocol contracts used by the Omnichannel Anti-Fraud Agent (Dual MCP). The MCP layer exposes deterministic verification tools to the ADK agent so Gemini can ground conclusions in procedural and domain evidence.

## MCP Design Principles

| Principle | Description |
| --- | --- |
| Structured I/O | Tool responses must be JSON-serializable and machine-readable |
| Deterministic semantics | Same request should yield consistent verification output |
| Explainable evidence | Each result includes both machine flags and human-readable reasoning |
| Timeout-tolerant | Agent continues safely if a tool is unavailable |
| Traceable | Every request carries a case ID and trace metadata |

## Contract Summary

| MCP Server | Primary Responsibility | Primary Tool |
| --- | --- | --- |
| MongoDB Atlas MCP | Institutional and legal procedure verification | `validate_institution_protocol` |
| Elasticsearch MCP | Domain similarity and typo-squatting verification | `verify_domain_similarity` |

## Common Request Envelope

```json
{
  "case_id": "CASE-2026-000184",
  "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
  "timestamp": "2026-05-29T16:32:11Z",
  "channel_type": "whatsapp",
  "locale": "en-IN",
  "source": "vertex-agent-runtime"
}
```

## MongoDB Atlas MCP

## Tool Name

`validate_institution_protocol`

## Request Schema

```json
{
  "case_id": "string",
  "trace_id": "string",
  "institution": "string",
  "observed_channel": "string",
  "observed_sender": "string",
  "observed_domain": "string",
  "claimed_action": "string",
  "claims": ["string"],
  "jurisdiction": "string"
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `case_id` | string | Yes | Correlates tool call to the fraud case |
| `trace_id` | string | Yes | Correlates tool call to distributed trace |
| `institution` | string | Yes | Detected institution or authority |
| `observed_channel` | string | Yes | WhatsApp, SMS, phone, email, website, etc. |
| `observed_sender` | string | No | Phone number, email, or sender ID |
| `observed_domain` | string | No | Domain linked to the institution claim |
| `claimed_action` | string | Yes | What the sender is asking the user to do |
| `claims` | array[string] | No | Important message assertions extracted by Gemini |
| `jurisdiction` | string | No | Country or region for procedure lookup |

## Response Schema

```json
{
  "institution_found": true,
  "official_channels": ["string"],
  "protocol_match": false,
  "violations": ["string"],
  "confidence": 0.0,
  "evidence_summary": "string",
  "recommended_interpretation": "string"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `institution_found` | boolean | Whether the institution exists in the trusted dataset |
| `official_channels` | array[string] | Known valid communication channels |
| `protocol_match` | boolean | Whether the observed scenario matches expected process |
| `violations` | array[string] | Specific rule or protocol deviations |
| `confidence` | number | MCP confidence in the match or violation assessment |
| `evidence_summary` | string | Human-readable evidence summary |
| `recommended_interpretation` | string | Guidance for the agent, such as likely impersonation |

## MongoDB Request Example

```json
{
  "case_id": "CASE-2026-000184",
  "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
  "institution": "State Bank of India",
  "observed_channel": "whatsapp",
  "observed_sender": "+91-98XXXXXX12",
  "observed_domain": "sbi-kvc-alert.in",
  "claimed_action": "Complete urgent KYC verification to avoid account freeze",
  "claims": [
    "Account will be frozen in 10 minutes",
    "User must click the provided link immediately"
  ],
  "jurisdiction": "IN"
}
```

## MongoDB Response Example

```json
{
  "institution_found": true,
  "official_channels": ["official website", "registered email", "branch visit", "verified app"],
  "protocol_match": false,
  "violations": [
    "KYC enforcement is not initiated through WhatsApp from personal mobile numbers",
    "Immediate account freeze threats are not standard customer-verification procedure",
    "Unverified external domain is not an approved institutional property"
  ],
  "confidence": 0.96,
  "evidence_summary": "Observed message deviates from known SBI communication and KYC workflow patterns.",
  "recommended_interpretation": "Likely banking impersonation or phishing attempt."
}
```

## Elasticsearch MCP

## Tool Name

`verify_domain_similarity`

## Request Schema

```json
{
  "case_id": "string",
  "trace_id": "string",
  "observed_domain": "string",
  "claimed_brand": "string",
  "top_k": 5,
  "similarity_methods": ["levenshtein", "jaro_winkler"]
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `case_id` | string | Yes | Correlates tool call to case |
| `trace_id` | string | Yes | Correlates tool call to trace |
| `observed_domain` | string | Yes | Domain extracted from evidence |
| `claimed_brand` | string | No | Institution or product brand implied by the content |
| `top_k` | integer | No | Number of official-candidate domains to return |
| `similarity_methods` | array[string] | No | Matching algorithms to run |

## Response Schema

```json
{
  "domain_found": false,
  "official_match": false,
  "matched_candidates": [
    {
      "domain": "string",
      "levenshtein_similarity": 0.0,
      "jaro_winkler_similarity": 0.0,
      "is_official": true
    }
  ],
  "typo_squatting_risk": "string",
  "confidence": 0.0,
  "evidence_summary": "string",
  "recommended_interpretation": "string"
}
```

| Field | Type | Description |
| --- | --- | --- |
| `domain_found` | boolean | Whether the observed domain is present in the corpus |
| `official_match` | boolean | Whether it is a known trusted domain |
| `matched_candidates` | array[object] | Closest official brand domains and similarity scores |
| `typo_squatting_risk` | string | `none`, `low`, `medium`, `high`, or `critical` |
| `confidence` | number | Confidence in the classification |
| `evidence_summary` | string | Human-readable domain assessment |
| `recommended_interpretation` | string | Agent-oriented interpretation |

## Elasticsearch Request Example

```json
{
  "case_id": "CASE-2026-000184",
  "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
  "observed_domain": "sbi-kvc-alert.in",
  "claimed_brand": "State Bank of India",
  "top_k": 3,
  "similarity_methods": ["levenshtein", "jaro_winkler"]
}
```

## Elasticsearch Response Example

```json
{
  "domain_found": false,
  "official_match": false,
  "matched_candidates": [
    {
      "domain": "sbi.co.in",
      "levenshtein_similarity": 0.84,
      "jaro_winkler_similarity": 0.91,
      "is_official": true
    },
    {
      "domain": "onlinesbi.sbi",
      "levenshtein_similarity": 0.79,
      "jaro_winkler_similarity": 0.88,
      "is_official": true
    }
  ],
  "typo_squatting_risk": "high",
  "confidence": 0.94,
  "evidence_summary": "Observed domain is not official and is highly similar to trusted SBI domains.",
  "recommended_interpretation": "Probable typo-squatting or phishing infrastructure."
}
```

## Tool Calling Specifications

| Condition | Tool Call |
| --- | --- |
| Institution detected in content | `validate_institution_protocol` |
| Domain or URL detected in content | `verify_domain_similarity` |
| Institution and domain both detected | Invoke both tools |
| Neither detected | No MCP call required |

## Agent Tool Call Pattern

```json
{
  "tool_name": "validate_institution_protocol",
  "arguments": {
    "case_id": "CASE-2026-000184",
    "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
    "institution": "State Bank of India",
    "observed_channel": "whatsapp",
    "observed_sender": "+91-98XXXXXX12",
    "observed_domain": "sbi-kvc-alert.in",
    "claimed_action": "Complete urgent KYC verification to avoid account freeze",
    "claims": ["Account will be frozen in 10 minutes"],
    "jurisdiction": "IN"
  }
}
```

```json
{
  "tool_name": "verify_domain_similarity",
  "arguments": {
    "case_id": "CASE-2026-000184",
    "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
    "observed_domain": "sbi-kvc-alert.in",
    "claimed_brand": "State Bank of India",
    "top_k": 3,
    "similarity_methods": ["levenshtein", "jaro_winkler"]
  }
}
```

## Agent Consumption Rules

| MCP Output Pattern | Agent Interpretation |
| --- | --- |
| `protocol_match = false` with explicit violations | Increase institutional deviation score materially |
| `official_match = false` and `typo_squatting_risk = high` | Treat domain as phishing evidence |
| `confidence < 0.5` | Use cautiously and reflect uncertainty in report |
| Tool timeout or error | Continue analysis and record verification degradation |

## Error Contract

```json
{
  "error": true,
  "error_type": "timeout",
  "message": "Elasticsearch query exceeded timeout threshold",
  "retryable": true
}
```

## Timeout and Retry Guidance

| Tool | Timeout Target | Retry Policy |
| --- | --- | --- |
| MongoDB MCP | 1000 ms | 1 fast retry |
| Elasticsearch MCP | 1000 ms | 1 fast retry |

If the retry also fails, set verification result to unavailable, continue scoring with behavioral evidence, and preserve trace annotations for debugging.

## Security Considerations

MCP requests can contain sensitive data such as phone numbers, suspicious domains, and institution claims. Recommended controls:

- Redact high-risk PII from logs where possible
- Use TLS for MCP transport
- Authenticate MCP servers with service credentials
- Validate all tool input fields against schema
- Prevent prompt injection from being passed unescaped into tool queries
