# Observability and Tracing

## Purpose

This document defines the observability strategy for the Omnichannel Anti-Fraud Agent (Dual MCP). The system uses Cloud Trace as the primary tracing backbone to understand request latency, tool behavior, decision paths, and downstream event execution across the entire fraud-detection workflow.

## Observability Goals

| Goal | Why It Matters |
| --- | --- |
| End-to-end traceability | Judges and operators need to see the full lifecycle of a fraud case |
| Model and tool attribution | Distinguish model latency from MCP latency |
| Debuggable decisions | Understand why a threat score was produced |
| Alert pipeline visibility | Confirm that critical cases triggered notifications |
| Safe operations | Detect timeouts, degraded verification, and delivery failures |

## Trace Topology

```text
[Streamlit Request]
       |
       v
[Root Trace Span: fraud_case_request]
       |
       +--> [Span: preprocess_input]
       |
       +--> [Span: gemini_entity_extraction]
       |
       +--> [Span: mongodb_mcp_verification]
       |
       +--> [Span: elastic_mcp_verification]
       |
       +--> [Span: threat_score_computation]
       |
       +--> [Span: threat_report_generation]
       |
       +--> [Span: guardian_alert_publish]
       |
       +--> [Span: blacklist_persistence]
```

## Cloud Trace Integration

Cloud Trace should be attached to every user case from the frontend boundary onward.

Key design points:

- Create one root span per case submission
- Propagate `trace_id` into all tool calls
- Annotate spans with case metadata, but redact sensitive content
- Link downstream Cloud Function executions back to the originating case trace

## Recommended Trace Attributes

| Attribute | Example |
| --- | --- |
| `case.id` | `CASE-2026-000184` |
| `input.type` | `image` |
| `channel.type` | `whatsapp` |
| `institution.detected` | `true` |
| `domain.detected` | `true` |
| `threat.score` | `0.91` |
| `risk.level` | `CRITICAL` |
| `guardian.alert.required` | `true` |
| `blacklist.candidate` | `true` |

## Span Design

Suggested spans:

- `fraud_case_request`
- `preprocess_input`
- `gemini_entity_extraction`
- `gemini_behavioral_analysis`
- `mongodb_mcp_verification`
- `elastic_mcp_verification`
- `threat_score_computation`
- `gemini_report_generation`
- `guardian_alert_publish`
- `twilio_notification_send`
- `sendgrid_notification_send`
- `blacklist_persistence`

## Agent Runtime Tracing

Vertex AI Agent Runtime should emit runtime-level spans for request acceptance, model invocation, tool invocation, retries, and final response emission. When possible, correlate custom application spans with runtime spans using the same trace context.

## Tool Execution Monitoring

MCP tools should record:

| Metric | Meaning |
| --- | --- |
| Request count | How often each tool is invoked |
| Success rate | How often tools return valid data |
| Timeout rate | How often tools breach latency budget |
| Average latency | Mean response duration |
| P95 latency | High-percentile latency for reliability review |
| Error class distribution | Timeout, bad request, unavailable backend |

## Example Trace Narrative

Case:

- User uploads a phishing screenshot
- OCR detects a bank logo and suspicious domain
- Gemini extracts the institution and URL
- MongoDB MCP returns protocol mismatch
- Elasticsearch MCP returns high typo-squatting risk
- Final score becomes `0.91`
- Eventarc publishes a critical alert event
- Twilio sends guardian SMS

This should appear in Trace as a single request tree with the decision path visible step-by-step.

## Logging Strategy

Tracing should be paired with structured logging.

```json
{
  "severity": "INFO",
  "case_id": "CASE-2026-000184",
  "trace_id": "3a81d72bbf7b4aef9a9fd4b6428c1093",
  "stage": "elastic_mcp_verification",
  "message": "Domain similarity verification completed",
  "official_match": false,
  "typo_squatting_risk": "high",
  "latency_ms": 214
}
```

Logging guidance:

- Log stage transitions and key decisions
- Avoid logging full raw user content unless explicitly redacted and required
- Mask phone numbers, email addresses, and account details
- Include case and trace identifiers in every structured log line

## Debugging Workflow

### Scenario 1: Threat Score Looks Too Low

1. Open the root trace for the affected case
2. Inspect `gemini_entity_extraction` to confirm correct entity detection
3. Inspect MCP spans for missed or failed tool calls
4. Inspect `threat_score_computation` attributes
5. Compare sub-scores against the visible message content

### Scenario 2: Alerts Were Not Delivered

1. Confirm `guardian_alert_publish` executed
2. Confirm Eventarc event routing completed
3. Inspect `twilio_notification_send` and `sendgrid_notification_send`
4. Check retry behavior and provider responses

### Scenario 3: MCP Timeout Causing Partial Reports

1. Inspect tool span latency
2. Check whether retry occurred
3. Inspect fallback branch in final report
4. Decide whether timeout budget should increase or query should be optimized

## Operational Dashboards

| Widget | Purpose |
| --- | --- |
| Cases per minute | Throughput |
| Average threat score | Risk trend |
| Critical alert count | Escalation volume |
| MongoDB MCP P95 latency | Procedural verification health |
| Elastic MCP P95 latency | Domain-verification health |
| Alert send failure rate | Downstream operational health |
| Blacklist write rate | Persistence and recurrence insight |

## SLO Recommendations

| Objective | Target |
| --- | --- |
| Interactive response success rate | 99.0% |
| Interactive response latency | P95 under 7 seconds |
| MCP verification success rate | 98.0% |
| Critical alert publish success rate | 99.5% |
| Guardian notification delivery initiation | 99.0% |

## Security and Privacy in Observability

Because the system handles sensitive fraud evidence:

- Store only minimum viable attributes in traces
- Redact raw scam content from logs unless necessary for secure debugging
- Restrict trace and log access using IAM roles
- Separate demo and production telemetry projects where possible

## Outcome

A strong observability design makes the system reviewable, defensible, and operable. For hackathon judging, tracing demonstrates architectural maturity. For enterprise deployment, it provides the evidence needed to explain decisions, investigate failures, and tune performance safely.
