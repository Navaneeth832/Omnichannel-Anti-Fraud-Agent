# 🛡️ Omnichannel Anti-Fraud Agent

> **SentinelGuard AI** — A dual-layer multimodal fraud detection system powered by Gemini 2.5 Flash, MongoDB Atlas MCP, and Elasticsearch MCP.

Built for the **Google Cloud Rapid Agent Hackathon** using Google Cloud ADK and Vertex AI Agent Runtime.

-----

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Threat Scoring Framework](#threat-scoring-framework)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Dashboard Navigation](#dashboard-navigation)
- [Supported Fraud Types](#supported-fraud-types)
- [Tech Stack](#tech-stack)
- [Team](#team)
- [License](#license)

-----

## Overview

The **Omnichannel Anti-Fraud Agent** is a production-grade fraud detection platform that analyzes evidence of suspected scams across multiple channels — text, audio, image, and PDF. It combines fast probabilistic reasoning from Gemini with deterministic verification through MongoDB Atlas MCP and Elasticsearch MCP to produce structured, explainable threat reports.

### Key Capabilities

- **Multimodal Analysis** — submit text messages, audio recordings, screenshots, or PDF documents for fraud analysis
- **Dual-Layer Verification** — Gemini behavioral reasoning + MCP tool grounding for institution and domain validation
- **Structured Threat Reports** — every case outputs a full JSON report with threat score, risk level, fraud type, detected entities, and a recommended action
- **Guardian Alert System** — when threat score ≥ 0.8, the system automatically notifies trusted guardian contacts via Twilio SMS and SendGrid email
- **Blacklist Persistence** — confirmed fraud indicators (phone numbers, domains, institutions) are persisted for future lookups
- **Deterministic Fallback** — works offline without Gemini using a lexical scoring engine; no silent failures

-----

## Architecture

```
                        ┌────────────────────────────┐
                        │     Streamlit Frontend      │
                        │  Text / Audio / Image / PDF │
                        └────────────┬───────────────┘
                                     │
                                     ▼
                        ┌────────────────────────────┐
                        │  Preprocessing / Multimodal │
                        │  OCR • Speech-to-Text • PDF │
                        └────────────┬───────────────┘
                                     │
                                     ▼
                  ┌──────────────────────────────────────┐
                  │   Gemini 2.5 Flash  (ADK Agent)      │
                  │   Entity Extraction + Behavioral      │
                  │   Threat Analysis + Report Generation │
                  └───────────┬──────────────┬───────────┘
                              │              │
             Institution found│              │Domain / URL found
                              ▼              ▼
             ┌─────────────────────┐  ┌─────────────────────┐
             │  MongoDB Atlas MCP  │  │  Elasticsearch MCP  │
             │  Institution rules  │  │  Fuzzy domain match │
             │  Legal procedures   │  │  Typo-squatting     │
             │  Protocol checks    │  │  Levenshtein / JW   │
             └──────────┬──────────┘  └──────────┬──────────┘
                        └──────────┬─────────────┘
                                   ▼
                  ┌──────────────────────────────────────┐
                  │        Threat Score + Decision        │
                  │  Score • Risk Level • Recommended     │
                  │  Action • Guardian Flag • Blacklist   │
                  └───────────┬──────────────┬───────────┘
                              │              │
                 score ≥ 0.8  │              │ offender data
                              ▼              ▼
             ┌─────────────────────┐  ┌─────────────────────┐
             │  Guardian Alerts    │  │  Blacklist Store    │
             │  Twilio SMS         │  │  MongoDB persist    │
             │  SendGrid Email     │  │  Future lookups     │
             └─────────────────────┘  └─────────────────────┘
```

-----

## How It Works

### Pipeline Stages

|Stage                                |Description                                                                                                      |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------|
|**1. Evidence Normalization**        |Text, audio transcripts, OCR output, and PDF text are reduced to a single normalized evidence string             |
|**2. Gemini Entity Extraction**      |Gemini extracts institution, phone numbers, domains, emails, payment methods, and behavioral signals             |
|**3. MongoDB MCP Verification**      |If an institution is found, MongoDB validates official communication channels and legal procedures               |
|**4. Elasticsearch MCP Verification**|If a domain is found, Elasticsearch computes Levenshtein and Jaro-Winkler similarity for typo-squatting detection|
|**5. Contradiction Detection**       |Internal rules engine detects logical contradictions (e.g., WhatsApp-based legal arrest orders)                  |
|**6. Threat Scoring**                |Weighted composite score is computed from Urgency, Coercion, and Institutional Deviation                         |
|**7. Report Generation**             |A structured `ThreatReport` JSON is produced with all evidence, decisions, and recommended actions               |
|**8. Guardian Alert**                |When score ≥ 0.8, Twilio SMS and SendGrid email alerts are sent to trusted guardians                             |
|**9. Blacklist Persistence**         |Confirmed offender identifiers are written to MongoDB for future lookup                                          |

### Fallback Behavior

If `GEMINI_API_KEY` is not configured, the system automatically falls back to a deterministic lexical scoring engine that extracts entities and scores behavioral signals using keyword analysis — no configuration change required.

-----

## Threat Scoring Framework

The agent scores each case on **three weighted dimensions**:

|Dimension                  |Weight|What It Detects                                                                      |
|---------------------------|------|-------------------------------------------------------------------------------------|
|**Artificial Urgency**     |25%   |Time pressure, countdown language, account-freeze threats, panic-inducing language   |
|**Social Coercion**        |25%   |Arrest threats, secrecy demands, “stay on the line” pressure, authority impersonation|
|**Institutional Deviation**|50%   |Unofficial channels, impossible legal procedures, unauthorized payment requests      |

```
Threat Score = (Urgency × 0.25) + (Coercion × 0.25) + (Deviation × 0.50)
```

### Risk Bands

|Score      |Risk Level|Action                                       |
|-----------|----------|---------------------------------------------|
|0.00 – 0.30|🟢 LOW     |Return report only                           |
|0.31 – 0.60|🟡 MEDIUM  |Cautionary guidance                          |
|0.61 – 0.80|🟠 HIGH    |Block sender, verify institution             |
|0.81 – 1.00|🔴 CRITICAL|Guardian alert triggered, blacklist candidate|

### Example Scores

|Scenario                                                          |Score|Risk    |
|------------------------------------------------------------------|-----|--------|
|Digital arrest scam — “stay on the line, transfer to safe account”|0.96 |CRITICAL|
|SBI account freeze with typo-squatted domain                      |0.83 |CRITICAL|
|Phishing domain with brand transposition                          |0.71 |HIGH    |
|Vague suspicious email with mild pressure                         |0.21 |LOW     |

-----

## Project Structure

```
Omnichannel-Anti-Fraud-Agent/
│
├── dashboard/                         # Streamlit frontend
│   ├── app/
│   │   └── streamlit_app.py           # Main Streamlit application
│   ├── components/
│   │   ├── results_panel.py           # Threat report UI component
│   │   └── sidebar.py                 # Navigation sidebar
│   ├── utils/
│   │   ├── audio_utils.py             # Audio preprocessing helpers
│   │   ├── image_utils.py             # Image/OCR preprocessing helpers
│   │   └── text_utils.py              # Text normalization utilities
│   └── requirements.txt               # Dashboard dependencies
│
├── gemini-agent/                      # Core agent and backend
│   ├── fraud_agent/
│   │   ├── agent.py                   # ADK Agent definition (root_agent)
│   │   ├── orchestrator.py            # Full pipeline: entity → MCP → score → alert
│   │   ├── gemini_runtime.py          # Gemini API + deterministic fallback
│   │   ├── multimodal.py              # Audio, image, and PDF analysis entry points
│   │   ├── scoring.py                 # Threat score calculation and risk banding
│   │   ├── schemas.py                 # ThreatReport, BehavioralAnalysis, DetectedEntities
│   │   ├── contradictions.py          # Contradiction detection rules engine
│   │   ├── guardian_alert_service.py  # Twilio SMS + SendGrid email alerts
│   │   ├── observability.py           # Cloud Trace span context manager
│   │   ├── system_health.py           # Component health checks
│   │   ├── config.py                  # Settings loaded from environment
│   │   ├── utils.py                   # Entity extraction, normalization utilities
│   │   └── mcp/
│   │       ├── mongo_adapter.py       # MongoDB MCP: blacklist, cases, guardian profiles
│   │       └── elastic_adapter.py     # Elasticsearch MCP: domain fuzzy matching
│   ├── docs/
│   │   ├── architecture.md            # Full system architecture document
│   │   ├── agent_flow.md              # Pipeline stage-by-stage breakdown
│   │   ├── threat_scoring.md          # Scoring topology with worked examples
│   │   ├── deployment_architecture.md # GCP deployment guide
│   │   ├── mcp_contracts.md           # MCP tool contracts
│   │   └── observability.md           # Tracing and logging guide
│   ├── system_prompt/
│   │   └── fraud_topology.txt         # SentinelGuard AI system prompt
│   ├── schemas/
│   │   └── threat_report.json         # JSON schema for ThreatReport output
│   ├── tools/
│   │   ├── mongodb_mcp.py             # MongoDB MCP tool wrappers
│   │   └── elastic_mcp.py             # Elasticsearch MCP tool wrappers
│   ├── tester.py                      # Manual integration tester
│   ├── verify_project.py              # Pre-run environment verification
│   └── requirements.txt               # Agent dependencies
│
├── data/
│   ├── reference_scripts/             # Sample scam scripts for testing
│   └── test-cases/                    # Sample audio and PDF test cases
│
├── integrations/
│   └── member3_setup.md               # Team integration guide
│
├── system_prompt/
│   └── fraud_topology.txt             # Root-level copy of system prompt
│
├── tests/
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_phase3_integration.py     # MCP integration tests
│   └── test_production_pipeline.py    # End-to-end pipeline tests
│
├── .env.example                       # Environment variable template
├── .gitignore
└── LICENSE
```

-----

## Prerequisites

- Python **3.10** or later
- `ffmpeg` installed and on PATH (required for MP3 audio transcription)
- `tesseract-ocr` installed (required for image OCR)
- A Google account for Gemini API access (optional — deterministic fallback available)

Install system dependencies on Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y ffmpeg tesseract-ocr
```

On macOS with Homebrew:

```bash
brew install ffmpeg tesseract
```

-----

## Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/Omnichannel-Anti-Fraud-Agent.git
cd Omnichannel-Anti-Fraud-Agent

# Install dashboard dependencies
pip install -r dashboard/requirements.txt

# Install agent dependencies
pip install -r gemini-agent/requirements.txt
```

-----

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### Environment Variables

```env
# ── Gemini ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY=                    # Required for live Gemini analysis
                                   # Leave blank to use deterministic fallback

# ── MongoDB Atlas ───────────────────────────────────────────────────────────
MONGODB_URI=                       # MongoDB connection string
MONGODB_DATABASE=fraud_agent       # Database name (default: fraud_agent)

# ── Elasticsearch ───────────────────────────────────────────────────────────
ELASTIC_NODE=                      # Elasticsearch cluster endpoint
ELASTIC_API_KEY=                   # Elasticsearch API key
ELASTICSEARCH_INDEX=anti-scam-threat-registry

# ── Alert Services ──────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID=                # Twilio account SID
TWILIO_AUTH_TOKEN=                 # Twilio auth token
TWILIO_PHONE_NUMBER=               # Twilio sender phone number

SENDGRID_API_KEY=                  # SendGrid API key
SENDGRID_FROM_EMAIL=               # Verified sender email address

# ── Guardian Contact ────────────────────────────────────────────────────────
TRUSTED_GUARDIAN_NAME=             # Guardian display name
TRUSTED_GUARDIAN_PHONE=            # Guardian phone number (for SMS alerts)
TRUSTED_GUARDIAN_EMAIL=            # Guardian email address

# ── Deployment ──────────────────────────────────────────────────────────────
FRAUD_ALERT_THRESHOLD=0.8          # Score threshold for guardian alerts
PRODUCTION_MODE=false
STRICT_PRODUCTION_MODE=false       # Set true to disable all fallbacks

# ── Google Cloud ─────────────────────────────────────────────────────────────
GCP_PROJECT_ID=                    # GCP project ID for Vertex AI deployment
AGENT_BUILDER_WEBHOOK_URL=         # Agent Builder webhook endpoint
```

> **Tip:** All services are optional during development. If MongoDB, Elasticsearch, Twilio, or SendGrid are not configured, the system falls back to mock implementations automatically — no code changes needed.

-----

## Running the Application

### Streamlit Dashboard

```bash
cd dashboard
streamlit run app/streamlit_app.py
```

The dashboard will open at `http://localhost:8501`.

### Quick Programmatic Test

```python
from fraud_agent.orchestrator import analyze_text

result = analyze_text("CBI officer on WhatsApp demanding urgent transfer to a safe account")
print(result["risk_level"])      # CRITICAL
print(result["threat_score"])    # e.g. 0.94
print(result["fraud_type"])      # authority_impersonation
```

### Environment Verification

```bash
cd gemini-agent
python verify_project.py
```

-----

## Running Tests

```bash
# Run all tests from the repository root
pytest

# Run only MCP integration tests
pytest tests/test_phase3_integration.py

# Run production pipeline tests
pytest tests/test_production_pipeline.py
```

Tests run fully against mock backends when MongoDB and Elasticsearch environment variables are not set. No live credentials are required for local testing.

-----

## Dashboard Navigation

|Page                  |Description                                                                                                    |
|----------------------|---------------------------------------------------------------------------------------------------------------|
|**Victim View**       |Submit text, audio, image, or PDF evidence for analysis. Runs the full pipeline and displays the threat report.|
|**Guardian Alert Log**|View all guardian alerts sent via Twilio or SendGrid, with timestamps and delivery status.                     |
|**Case History**      |Browse all persisted cases stored in MongoDB, with expandable threat report detail.                            |
|**System Health**     |Live status check of all components: Gemini, MongoDB, Elasticsearch, Twilio, and SendGrid.                     |

-----

## Supported Fraud Types

|Fraud Type                |Description                                                        |
|--------------------------|-------------------------------------------------------------------|
|`digital_arrest_scam`     |Caller claims victim is under “digital arrest” for money laundering|
|`banking_impersonation`   |Fake bank officer demanding KYC verification or fund transfer      |
|`authority_impersonation` |Impersonating CBI, cyber police, or law enforcement                |
|`phishing`                |Suspicious domains or URLs impersonating official institutions     |
|`repeat_offender_campaign`|Blacklist match on known offender identifier                       |
|`impersonation_attempt`   |General impersonation without a specific recognized category       |

-----

## Tech Stack

|Layer                         |Technology                                  |
|------------------------------|--------------------------------------------|
|**Agent Orchestration**       |Google Cloud ADK, Vertex AI Agent Runtime   |
|**LLM**                       |Gemini 2.5 Flash                            |
|**Frontend**                  |Streamlit                                   |
|**Institutional Verification**|MongoDB Atlas MCP                           |
|**Domain Verification**       |Elasticsearch MCP                           |
|**Audio Transcription**       |SpeechRecognition + ffmpeg                  |
|**Image OCR**                 |Pytesseract + Pillow                        |
|**PDF Extraction**            |pypdf                                       |
|**SMS Alerts**                |Twilio                                      |
|**Email Alerts**              |SendGrid                                    |
|**Observability**             |Cloud Trace (OpenTelemetry-compatible spans)|
|**Data Validation**           |Pydantic                                    |
|**Testing**                   |Pytest                                      |

-----

## Team

Built as part of the **Google Cloud Rapid Agent Hackathon**.

|Role    |Responsibility                                        |
|--------|------------------------------------------------------|
|Member 1|Gemini Agent core, orchestrator pipeline, MCP adapters|
|Member 2|Streamlit dashboard, multimodal preprocessing, UI/UX  |
|Member 3|MongoDB + Elasticsearch integration, environment setup|
| Member 4 | Creating mock scam audio/images, managing GitHub, scripting/filming the demo video, and writing the Devpost submission. |



## License

This project is licensed under the terms in the <LICENSE> file.

-----

> *SentinelGuard AI — Detect. Verify. Protect.*
