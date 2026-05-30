# Omnichannel Anti-Fraud Agent (Dual MCP) Architecture

## Overview

The Omnichannel Anti-Fraud Agent is a dual-layer reasoning system built on Google Cloud Agent Development Kit (ADK), Gemini 3.1 Flash, and Vertex AI Agent Runtime. The platform analyzes text, audio, and image evidence of suspected scams, verifies institutional and domain-level claims through external MCP tools, produces a structured threat report, and escalates high-risk cases to a guardian workflow.

The design goal is to combine fast multimodal reasoning with deterministic verification. Gemini performs behavioral interpretation and entity extraction, while MongoDB Atlas MCP and Elasticsearch MCP provide institution-rule and domain-verification evidence to reduce hallucinated conclusions and strengthen auditability.

## Design Goals

| Goal | Implementation |
| --- | --- |
| Multimodal fraud detection | Gemini ingests text, OCR output, speech transcripts, and image-derived entities |
| Low-latency hackathon deployability | Gemini 3.1 Flash with Vertex AI Agent Runtime |
| Deterministic verification | Dual MCP tool layer for procedural and domain validation |
| Structured outputs | Threat report JSON schema aligned with `schemas/threat_report.json` |
| Enterprise observability | Cloud Trace spans across agent and tool execution |
| Event-driven escalations | Eventarc and Cloud Functions for alerts and blacklist workflows |

## High-Level Architecture

```text
                                 +----------------------------------+
                                 |        Streamlit Frontend        |
                                 |  Upload text / audio / images    |
                                 +----------------+-----------------+
                                                  |
                                                  v
                                 +----------------------------------+
                                 |     Ingress / Preprocessing      |
                                 |  OCR, speech-to-text, metadata   |
                                 +----------------+-----------------+
                                                  |
                                                  v
                         +------------------------------------------------------+
                         | Vertex AI Agent Runtime + Google Cloud ADK Agent     |
                         |                                                      |
                         |  1. Entity extraction                                |
                         |  2. Behavioral threat analysis                       |
                         |  3. Tool routing and evidence fusion                 |
                         |  4. Structured threat report generation              |
                         +-------------------+------------------+---------------+
                                             |                  |
                           Institution found |                  | Domain / URL found
                                             |                  |
                                             v                  v
                       +---------------------------+    +---------------------------+
                       | MongoDB Atlas MCP Server  |    | Elasticsearch MCP Server  |
                       | - Communication rules     |    | - Fuzzy domain matching   |
                       | - Legal procedures        |    | - Typo-squatting checks   |
                       | - Protocol deviations     |    | - Levenshtein similarity  |
                       +-------------+-------------+    | - Jaro-Winkler similarity |
                                     |                  +-------------+-------------+
                                     +------------------------+--------+
                                                              |
                                                              v
                         +------------------------------------------------------+
                         | Threat Report + Decision Layer                       |
                         | - Threat score                                       |
                         | - Risk level                                         |
                         | - Recommended action                                 |
                         | - Guardian alert flag                                |
                         | - Blacklist candidate                                |
                         +-------------------+------------------+---------------+
                                             |                  |
                               score >= 0.8  |                  | offender details
                                             v                  v
                           +-------------------------+   +-------------------------+
                           | Eventarc + Cloud Funcs  |   | Blacklist Persistence   |
                           | - Twilio alerts         |   | institution/domain/ID   |
                           | - SendGrid emails       |   | case linkage            |
                           +-------------------------+   +-------------------------+
```

## Core Components

## 1. Streamlit Frontend

The Streamlit application serves as the analyst and end-user entry point. It accepts text, audio, and image evidence and displays the structured threat report and recommended actions.

Responsibilities:

- Capture user-submitted evidence
- Provide case metadata such as user ID, channel, locale, and timestamp
- Display the generated threat report
- Surface critical alerts and recommended response actions

## 2. Preprocessing Layer

The preprocessing stage converts all inputs into a normalized evidence package before the agent starts reasoning.

| Input Type | Preprocessing Action |
| --- | --- |
| Text | Normalization, language cleanup, token-safe truncation |
| Audio | Speech-to-text transcript generation and speaker metadata extraction |
| Image | OCR, logo/domain extraction, visible phone number detection |

Outputs from preprocessing:

- `normalized_text`
- `extracted_media_entities`
- `channel_type`
- `source_metadata`

## 3. ADK Agent Orchestrator

The agent is implemented with Google Cloud ADK and runs on Vertex AI Agent Runtime. This orchestration layer is responsible for prompting Gemini with the fraud topology, dispatching MCP tool calls when institutions or domains are detected, merging behavioral and verification evidence, and producing the final threat report.

## 4. Gemini 3.1 Flash Reasoning Engine

Gemini 3.1 Flash is used for low-latency reasoning and structured generation. It performs named entity extraction, scam-pattern recognition, behavioral scoring across the three weighted dimensions, evidence synthesis from MCP results, and threat report generation in JSON schema format.

Gemini is the probabilistic reasoning layer. It does not act alone on institutional or domain authenticity when verification evidence is available; instead, it uses MCP results as grounded evidence.

## 5. MongoDB Atlas MCP Server

MongoDB Atlas MCP acts as the institutional and procedural truth source.

It stores and validates:

- Official communication channels for banks, regulators, police, and courts
- Legal notification rules and escalation paths
- Institution-specific payment instructions and fraud caveats
- Known protocol deviations used in impersonation scams

Typical queries:

- Is WhatsApp a valid communication channel for this bank?
- Can a police department request immediate account liquidation by phone?
- Does this institution use personal mobile numbers for account verification?

## 6. Elasticsearch MCP Server

Elasticsearch MCP provides fuzzy domain intelligence to detect suspicious domains and phishing infrastructure.

Capabilities:

- Exact and fuzzy domain matching against a trusted-domain corpus
- Typo-squatting detection
- Levenshtein similarity scoring
- Jaro-Winkler similarity scoring
- Domain risk classification based on distance to official brands

## 7. Eventarc and Cloud Functions

Eventarc is used to fan out critical fraud events and post-decision workflows. Cloud Functions handle serverless side effects such as Twilio alerts, SendGrid emails, blacklist writes, and downstream notifications.

## 8. Cloud Trace

Cloud Trace provides end-to-end distributed tracing across:

- Streamlit request lifecycle
- Agent runtime reasoning stages
- MCP tool calls
- Event-triggered alert functions

## Dual-Layer Reasoning Model

## Layer 1: Behavioral Threat Analysis

Gemini scores the interaction using the threat topology:

| Dimension | Weight | Purpose |
| --- | --- | --- |
| Artificial Urgency | 25% | Detect pressure, immediacy, panic induction |
| Social Coercion | 25% | Detect isolation, threats, secrecy, authority coercion |
| Institutional Deviations | 50% | Detect violations of known legal or institutional procedures |

Layer 1 answers: "Does the content behave like a scam?"

## Layer 2: Verification Layer

MCP tools validate claims grounded in external evidence:

| MCP | Verification Focus |
| --- | --- |
| MongoDB Atlas MCP | Institution channels, legal procedures, protocol compliance |
| Elasticsearch MCP | Domain legitimacy, typo-squatting, fuzzy similarity |

Layer 2 answers: "Do the factual claims align with trusted institutional and domain records?"

## Data Flow

```text
1. User submits evidence via Streamlit
2. Input is normalized into text + metadata
3. Gemini extracts entities:
   - institution
   - phone number
   - website/domain
   - payment method
4. If institution exists:
   - call MongoDB MCP
5. If domain exists:
   - call Elasticsearch MCP
6. Gemini fuses behavioral and verification evidence
7. Gemini computes weighted threat score
8. Structured threat report is generated
9. If score >= 0.8:
   - publish alert event
   - invoke guardian notifications
10. Offender indicators are written to blacklist store
11. Final report is returned to Streamlit
```

## Cloud Services Mapping

| Capability | Google Cloud Service |
| --- | --- |
| Agent orchestration | Vertex AI Agent Runtime |
| Agent implementation | Google Cloud ADK |
| Model inference | Gemini 3.1 Flash |
| Event routing | Eventarc |
| Alert execution | Cloud Functions |
| Tracing | Cloud Trace |
| Optional artifact storage | Cloud Storage |
| Secret management | Secret Manager |
| IAM controls | IAM |

## MCP Interaction Model

The agent uses MCP as a tool-contract layer rather than embedding verification logic directly in the model prompt. This improves portability and trust.

```text
Gemini reasoning step
      |
      +--> detect institution --> MongoDB MCP request --> procedural evidence
      |
      +--> detect domain      --> Elastic MCP request --> domain evidence
      |
      +--> evidence fusion    --> final threat score and report
```

MCP interaction principles:

- Tool invocation is conditional, not mandatory for every request
- Tool outputs are structured and machine-readable
- Gemini uses tool evidence as a weighted input, not as free-form narrative
- Tool failures degrade gracefully and are reflected in the report

## Persistence Model

| Store | Data |
| --- | --- |
| Case store | Threat reports, evidence metadata, trace IDs, timestamps |
| Blacklist store | Suspicious phone numbers, domains, payment handles, institutions, recurrence count |

Blacklist writes occur only when the threat score exceeds threshold, evidence quality is sufficient, and the case is classified as a blacklist candidate.

## Security Boundaries

```text
[User Browser]
     |
 TLS |
     v
[Streamlit Frontend]
     |
 Authenticated service call
     v
[Vertex AI Agent Runtime]
     |
 IAM-scoped outbound tool calls
     +--> [MongoDB MCP Server]
     +--> [Elasticsearch MCP Server]
     |
 Eventarc authenticated event
     v
[Cloud Functions -> Twilio / SendGrid]
```

Security controls:

- Service-to-service authentication using IAM or signed credentials
- Secret storage in Secret Manager for Twilio, SendGrid, MongoDB, and Elasticsearch credentials
- Input sanitization for user-provided URLs and filenames
- PII-aware logging with redaction before telemetry export
- Rate limits to prevent abuse of alerting workflows

## Architectural Strengths

This design is strong for hackathon and enterprise review because it demonstrates practical multimodal fraud detection, clear separation of probabilistic reasoning and deterministic verification, event-driven response automation, operational readiness through tracing and structured outputs, and extensibility to additional MCP tools and new scam categories.
