# 🛡️ Omnichannel Anti-Fraud Agent

A production-ready Streamlit dashboard for detecting fraud across **audio**, **image**, and **text** channels — built for the Google Cloud AI Hackathon.

---

## 📁 Folder Structure

```
omnichannel-anti-fraud-agent/
│
├── streamlit_app.py          # Main application (entry point)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── assets/                   # Static assets (logos, icons — add as needed)
│
├── utils/                    # Future utility modules
│   ├── __init__.py
│   ├── audio_utils.py        # Audio preprocessing helpers (librosa, pydub)
│   ├── image_utils.py        # Image preprocessing helpers (PIL, cv2)
│   └── text_utils.py         # Text cleaning / NLP helpers
│
└── components/               # Future reusable UI components
    ├── __init__.py
    ├── results_panel.py      # Threat results display
    └── sidebar.py            # Sidebar configuration panel
```

---

## 🚀 Quick Start

### 1. Clone / extract the project
```bash
cd omnichannel-anti-fraud-agent
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run streamlit_app.py
```

The app opens at **http://localhost:8501**

---

## 🔌 Future API Integrations

| Service | Purpose | Status |
|---|---|---|
| **Google Cloud Agent Builder** | Multi-agent orchestration & reasoning | Pending |
| **Gemini 2.0 Flash** | Multimodal understanding (audio + image + text) | Pending |
| **Cloud Speech-to-Text** | Audio channel transcription | Pending |
| **Vertex AI Vision** | Document forgery, OCR, logo analysis | Pending |
| **MongoDB MCP** | Case storage, audit trail, fraud pattern DB | Pending |
| **Elasticsearch MCP** | Similarity search, threat intelligence lookup | Pending |

To enable, uncomment the relevant packages in `requirements.txt` and replace the stub functions in `streamlit_app.py`:
- `analyze_audio()` → connect to Speech-to-Text + Gemini
- `analyze_image()` → connect to Vision API + Gemini
- `analyze_text()` → connect to Gemini + Elasticsearch MCP
- `aggregate_results()` → connect to Agent Builder orchestration

---

## 🏗️ Architecture

```
User Browser
    │
    ▼
Streamlit Frontend (streamlit_app.py)
    │
    ├─ Audio Channel → Cloud Speech-to-Text → Gemini 2.0 Flash
    ├─ Image Channel → Cloud Vision API   → Gemini 2.0 Flash
    └─ Text  Channel → Gemini 2.0 Flash   → Elasticsearch MCP
                                │
                    Google Cloud Agent Builder
                    (Multi-agent orchestration)
                                │
                    ┌───────────┴────────────┐
                 MongoDB MCP           Elasticsearch MCP
              (Case storage)         (Threat intelligence)
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
MONGODB_URI=mongodb+srv://...
ELASTICSEARCH_URL=https://...
ELASTICSEARCH_API_KEY=...
GEMINI_API_KEY=...
AGENT_BUILDER_WEBHOOK_URL=https://your-agent-builder-webhook
AGENT_BUILDER_WEBHOOK_BEARER_TOKEN=optional-bearer-token
AGENT_BUILDER_WEBHOOK_TIMEOUT_SECS=30
```

### Agent Builder webhook payload

The Streamlit app now sends submitted evidence directly to `AGENT_BUILDER_WEBHOOK_URL` with Python `requests.post(...)`.

- Text is sent as the `text` form field.
- Audio is sent as the `audio` multipart file field.
- Images are sent as the `image` multipart file field.
- Metadata fields include `timestamp`, `source`, and `channels`.

If the webhook URL is not configured, the dashboard continues to use the same local production orchestrator entry point without external webhook delivery.

---

## 📝 License

MIT — Free for hackathon and commercial use.
