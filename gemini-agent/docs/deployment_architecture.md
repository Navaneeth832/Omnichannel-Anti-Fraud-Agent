# Deployment Architecture

## Overview

This document describes how to deploy the Omnichannel Anti-Fraud Agent (Dual MCP) across the frontend, agent runtime, verification layer, event-driven alerting, and operational security boundaries.

The target deployment model is intentionally hackathon-friendly while still reflecting enterprise architecture principles.

## Deployment Topology

```text
                        +--------------------------------------+
                        |         End Users / Analysts         |
                        +------------------+-------------------+
                                           |
                                           v
                        +--------------------------------------+
                        |         Streamlit Frontend           |
                        |  Upload evidence, review reports     |
                        +------------------+-------------------+
                                           |
                                           v
              +----------------------------------------------------------------+
              |             Vertex AI Agent Runtime + ADK Agent                |
              |  Gemini 3.1 Flash reasoning, tool routing, threat reporting   |
              +-----------------------+------------------------+---------------+
                                      |                        |
                                      v                        v
                     +----------------------------+   +--------------------------+
                     | MongoDB Atlas MCP Server   |   | Elasticsearch MCP Server |
                     +-------------+--------------+   +-------------+------------+
                                   |                                |
                                   +---------------+----------------+
                                                   |
                                                   v
                           +-----------------------------------------------+
                           | Threat decision / event publish               |
                           +-------------------+---------------------------+
                                               |
                                               v
                                    +----------------------+
                                    |       Eventarc       |
                                    +----------+-----------+
                                               |
                        +----------------------+----------------------+
                        |                                             |
                        v                                             v
              +------------------------+                   +------------------------+
              |     Cloud Function     |                   |     Cloud Function     |
              |   Twilio alert sender  |                   |  SendGrid mail sender  |
              +------------------------+                   +------------------------+
                                               |
                                               v
                                    +----------------------+
                                    |  Blacklist Storage   |
                                    +----------------------+
```

## Deployment Components

## 1. Streamlit Frontend Deployment

The Streamlit frontend provides evidence upload, threat report visualization, alert status display, and case review. Recommended deployment is containerized Streamlit on Cloud Run for managed HTTPS, autoscaling, and fast iteration.

## 2. Vertex AI Agent Deployment

The core agent should be deployed on Vertex AI Agent Runtime.

| Item | Recommendation |
| --- | --- |
| Runtime | Vertex AI Agent Runtime |
| Model | Gemini 3.1 Flash |
| Orchestration | Google Cloud ADK |
| Service account | Dedicated least-privilege runtime identity |
| Region | Same region as alerting and observability services where feasible |

## 3. MCP Server Deployment

MongoDB Atlas MCP and Elasticsearch MCP can be deployed as internal service endpoints accessible from the agent runtime.

| MCP | Suggested Hosting |
| --- | --- |
| MongoDB Atlas MCP | Cloud Run or GKE service connected to Atlas |
| Elasticsearch MCP | Cloud Run or GKE service connected to Elastic cluster |

Requirements:

- authenticated access only
- request schema validation
- outbound TLS to Atlas and Elasticsearch backends
- per-request trace propagation

## 4. Eventarc Deployment

Eventarc is used for asynchronous workflows when critical risk thresholds are crossed.

| Event Type | Trigger |
| --- | --- |
| `fraud.case.critical` | `threat_score >= 0.8` |
| `fraud.case.blacklist_candidate` | confirmed offender indicators available |
| `fraud.case.alert_failed` | alert provider delivery initiation failed |

## 5. Cloud Functions Deployment

Cloud Functions execute lightweight post-decision tasks.

| Function | Purpose |
| --- | --- |
| `send_guardian_sms` | Send Twilio SMS alert |
| `send_guardian_email` | Send SendGrid email alert |
| `persist_blacklist_record` | Store suspicious entities for future checks |
| `notify_review_queue` | Optional analyst or SOC notification |

Design guidance:

- Keep functions single-purpose
- Make each function idempotent using `case_id`
- Use retries for transient external-provider failures
- Emit structured logs and trace context

## 6. Twilio and SendGrid Integration

Twilio handles urgent mobile notifications; SendGrid handles email-based escalation.

| Provider | Best Use |
| --- | --- |
| Twilio | Immediate guardian alert, SMS or voice |
| SendGrid | Detailed threat report delivery, audit-friendly email trail |

## Deployment Sequence

```text
1. Deploy Streamlit frontend
2. Deploy ADK agent to Vertex AI Agent Runtime
3. Deploy MongoDB Atlas MCP server
4. Deploy Elasticsearch MCP server
5. Configure Eventarc triggers
6. Deploy Cloud Functions for Twilio, SendGrid, and blacklist persistence
7. Bind secrets, IAM, and trace/logging configuration
8. Run end-to-end validation with synthetic fraud cases
```

## Network and Security Architecture

```text
[Internet Users]
      |
    HTTPS
      v
[Streamlit on Cloud Run]
      |
      | authenticated service call
      v
[Vertex AI Agent Runtime]
      |
      +--> [MongoDB MCP Service] ---> [MongoDB Atlas]
      |
      +--> [Elastic MCP Service] ---> [Elasticsearch]
      |
      +--> [Eventarc] ---> [Cloud Functions] ---> [Twilio / SendGrid]
```

## Security Considerations

### Identity and Access

- Use dedicated service accounts per workload
- Grant Vertex runtime access only to required MCP endpoints and observability services
- Limit Cloud Functions to the minimum provider secrets they need
- Use IAM-based invocation restrictions wherever possible

### Secrets Management

Store these in Secret Manager:

- MongoDB Atlas credentials
- Elasticsearch credentials
- Twilio SID and auth token
- SendGrid API key
- optional signing keys for webhook validation

### Data Protection

- Encrypt data in transit with TLS
- Redact PII in logs and traces
- Avoid storing raw user uploads longer than needed
- Tokenize or hash blacklist entities if direct storage is not required

### Input Hardening

- Validate all uploaded file types
- Scan extracted URLs before presentation to users
- Rate-limit upload endpoints
- Apply schema validation before MCP calls

## High Availability Considerations

For a hackathon, single-region deployment is acceptable. For enterprise hardening:

- deploy frontend and agent services across multiple zones
- keep MCP services stateless
- replicate trusted-domain and institution datasets
- use provider retries and dead-letter handling for alert events

## Operational Configuration

| Parameter | Guidance |
| --- | --- |
| Agent request timeout | 7 to 10 seconds |
| MCP per-call timeout | 1 second with one retry |
| Alert retry window | 1 to 5 minutes depending on severity |
| Trace sampling | 100% for demo, tuned sampling for scale |
| Function memory | Sized for lightweight JSON processing and provider calls |

## Release Strategy

| Environment | Purpose |
| --- | --- |
| `dev` | Local and rapid iteration |
| `demo` | Hackathon judge environment with stable seeded data |
| `prod` | Hardened deployment with governed secrets and IAM |

Promotion controls:

- use infrastructure as code where possible
- test MCP contracts before promoting builds
- maintain seeded fraud scenarios for regression testing

## Demo Readiness Checklist

- Confirm Streamlit upload flow works for text, audio, and image
- Validate at least one digital arrest case and one phishing-domain case
- Confirm Cloud Trace shows end-to-end spans
- Confirm `threat_score >= 0.8` triggers Twilio or SendGrid alert
- Confirm blacklist persistence is visible for repeated offender indicators

## Why This Deployment Design Is Strong

This architecture is credible because it balances a fast hackathon path with real operational discipline: managed frontend and runtime services, clean separation between reasoning and verification, event-driven alerting, explicit security and observability controls, and extensibility for more channels, institutions, and MCP tools.
