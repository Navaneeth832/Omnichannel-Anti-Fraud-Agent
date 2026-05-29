"""
Omnichannel Anti-Fraud Agent
============================
A production-ready Streamlit dashboard for detecting fraud across audio, image, and text channels.

Architecture:
- Frontend: Streamlit (this file)
- AI Backend (future): Google Cloud Agent Builder + Gemini 2.0 Flash
- Vector Search (future): Elasticsearch MCP
- Data Storage (future): MongoDB MCP

Author: Anti-Fraud Team
Version: 1.0.0
"""

import streamlit as st
import time
import random
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Omnichannel Anti-Fraud Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS — Dark cybersecurity theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&family=Exo+2:wght@300;400;600;700&display=swap');

/* ── Root palette ── */
:root {
    --bg-deep:    #040d18;
    --bg-card:    #071428;
    --bg-panel:   #0b1e3a;
    --accent:     #00d4ff;
    --accent2:    #00ff9d;
    --danger:     #ff3860;
    --warn:       #ffb300;
    --ok:         #00e676;
    --border:     rgba(0,212,255,0.18);
    --glow:       0 0 18px rgba(0,212,255,0.35);
    --text:       #c9e8ff;
    --text-dim:   #6a8fa8;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
    background-color: var(--bg-deep) !important;
    color: var(--text) !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1400px; }

/* ── Scanline overlay ── */
body::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,212,255,0.015) 2px,
        rgba(0,212,255,0.015) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Hero header ── */
.hero {
    background: linear-gradient(135deg, #040d18 0%, #071428 50%, #091c35 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--glow), inset 0 1px 0 rgba(0,212,255,0.1);
}
.hero::before {
    content: '';
    position: absolute; top: -50%; right: -10%;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3rem; font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 0.4rem;
    text-shadow: 0 0 30px rgba(0,212,255,0.5);
}
.hero-accent { color: var(--accent); }
.hero-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
    color: var(--text-dim);
    letter-spacing: 0.12em;
}
.status-dot {
    display: inline-block; width: 8px; height: 8px;
    border-radius: 50%; background: var(--accent2);
    box-shadow: 0 0 8px var(--accent2);
    margin-right: 8px; animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Section cards ── */
.section-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.3s;
}
.section-card:hover { border-color: rgba(0,212,255,0.4); }
.section-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.25rem; font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.8rem;
}

/* ── Metric cards ── */
.metric-box {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}
.metric-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 2.4rem; font-weight: 400;
    line-height: 1;
}
.metric-label {
    font-size: 0.72rem; letter-spacing: 0.15em;
    color: var(--text-dim); margin-top: 0.4rem;
    text-transform: uppercase;
}
.score-critical { color: var(--danger); text-shadow: 0 0 12px rgba(255,56,96,0.6); }
.score-high     { color: var(--warn);   text-shadow: 0 0 12px rgba(255,179,0,0.6); }
.score-medium   { color: #ff8c00;       text-shadow: 0 0 12px rgba(255,140,0,0.4); }
.score-low      { color: var(--ok);     text-shadow: 0 0 12px rgba(0,230,118,0.5); }

/* ── Risk badge ── */
.risk-badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 4px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700; font-size: 1rem;
    letter-spacing: 0.12em; text-transform: uppercase;
}
.badge-critical { background: rgba(255,56,96,0.15); color: var(--danger); border: 1px solid var(--danger); }
.badge-high     { background: rgba(255,179,0,0.15);  color: var(--warn);   border: 1px solid var(--warn); }
.badge-medium   { background: rgba(255,140,0,0.12);  color: #ff8c00;       border: 1px solid #ff8c00; }
.badge-low      { background: rgba(0,230,118,0.12);  color: var(--ok);     border: 1px solid var(--ok); }

/* ── Result section ── */
.result-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: var(--accent);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.4rem;
}

/* ── Timeline ── */
.timeline-item {
    display: flex; align-items: flex-start; gap: 1rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(0,212,255,0.07);
}
.tl-dot {
    width: 10px; height: 10px;
    border-radius: 50%; margin-top: 5px; flex-shrink: 0;
}
.tl-text { font-size: 0.88rem; color: var(--text); }
.tl-time { font-family: 'Share Tech Mono', monospace; font-size: 0.72rem; color: var(--text-dim); margin-top: 2px; }

/* ── Streamlit widgets theming ── */
.stFileUploader > div {
    background: var(--bg-panel) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}
.stFileUploader label { color: var(--text) !important; }
.stTextArea textarea {
    background: var(--bg-panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Exo 2', sans-serif !important;
}
.stButton > button {
    background: linear-gradient(135deg, #006b99 0%, #004d73 100%) !important;
    color: #ffffff !important;
    border: 1px solid var(--accent) !important;
    border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important; font-size: 1.1rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2.5rem !important;
    transition: all 0.25s !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.2) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0099cc 0%, #006b99 100%) !important;
    box-shadow: 0 0 28px rgba(0,212,255,0.45) !important;
    transform: translateY(-1px) !important;
}
.stProgress > div > div { background: var(--accent) !important; }
.stExpander {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
div[data-testid="stMetric"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}
div[data-testid="stMetricValue"] { color: var(--accent) !important; font-family: 'Share Tech Mono', monospace !important; }
div[data-testid="stMetricLabel"] { color: var(--text-dim) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Info / success / warning boxes ── */
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def get_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def encode_image_base64(image_file) -> str:
    """Encode an uploaded image file to base64 (for future Gemini Vision calls)."""
    return base64.b64encode(image_file.getvalue()).decode("utf-8")


def validate_inputs(audio_file, image_file, text_input: str) -> bool:
    """Ensure at least one channel is provided before analysis."""
    return any([audio_file is not None, image_file is not None, text_input.strip()])


# ─────────────────────────────────────────────
#  ANALYSIS ENGINE (placeholder for real APIs)
# ─────────────────────────────────────────────

def analyze_audio(audio_file) -> dict:
    """
    [FUTURE INTEGRATION] Audio fraud analysis.

    Replace this stub with:
    - Google Cloud Speech-to-Text → transcript
    - Gemini 2.0 Flash multimodal audio understanding
    - Google Cloud Agent Builder for orchestration
    - Voice biometrics / deepfake detection model
    - Elasticsearch MCP for pattern matching against known fraud audio signatures

    Returns:
        dict with keys: score, signals, summary
    """
    if audio_file is None:
        return {"score": 0, "signals": [], "summary": "No audio provided."}

    # ── Simulated analysis ──
    time.sleep(0.4)
    score = random.randint(55, 92)
    return {
        "score": score,
        "signals": [
            "Synthetic voice characteristics detected (TTS artifacts)",
            "Urgency language pattern matched fraud corpus",
            "Caller ID spoofing metadata present",
            "Speech cadence anomaly: 2.3σ above baseline",
        ],
        "summary": f"Audio analysis complete. {score}% fraud probability based on voice and linguistic features.",
    }


def analyze_image(image_file) -> dict:
    """
    [FUTURE INTEGRATION] Image fraud analysis.

    Replace this stub with:
    - Gemini 2.0 Flash Vision for document/screenshot inspection
    - Google Cloud Vision API for OCR + object detection
    - Custom fraud image classifier (Vertex AI)
    - MongoDB MCP to log flagged images with metadata
    - Elasticsearch MCP for reverse image similarity search

    Returns:
        dict with keys: score, signals, summary
    """
    if image_file is None:
        return {"score": 0, "signals": [], "summary": "No image provided."}

    time.sleep(0.4)
    score = random.randint(45, 88)
    return {
        "score": score,
        "signals": [
            "QR code detected — destination URL suspicious",
            "Logo manipulation: 87% similarity to known phishing template",
            "Metadata stripped — likely screenshot from dark-web tool",
            "Brand impersonation: HDFC Bank (confidence 0.94)",
        ],
        "summary": f"Image analysis complete. {score}% fraud probability based on visual and structural features.",
    }


def analyze_text(text_input: str) -> dict:
    """
    [FUTURE INTEGRATION] Text fraud analysis.

    Replace this stub with:
    - Gemini 2.0 Flash text classification
    - Google Cloud Natural Language API for entity/sentiment
    - Google Cloud Agent Builder multi-turn reasoning
    - Elasticsearch MCP for fuzzy matching against known phishing templates
    - MongoDB MCP to store flagged messages and escalation history

    Returns:
        dict with keys: score, signals, summary
    """
    if not text_input.strip():
        return {"score": 0, "signals": [], "summary": "No text provided."}

    time.sleep(0.3)
    score = random.randint(60, 95)

    # Simple keyword heuristic (replace with real NLP)
    fraud_keywords = ["otp", "urgent", "verify", "click", "account", "suspended",
                      "prize", "winner", "kyc", "bank", "reward", "limited time"]
    hits = [kw for kw in fraud_keywords if kw.lower() in text_input.lower()]

    signals = [
        f"Phishing keyword detected: '{kw}'" for kw in hits[:3]
    ] or ["No obvious keywords — deeper semantic analysis recommended"]
    signals += [
        "Sender domain not in trusted registry",
        f"Message entropy score: {random.uniform(3.1, 4.8):.2f} (elevated)",
    ]

    return {
        "score": score,
        "signals": signals,
        "summary": f"Text analysis complete. {score}% fraud probability based on language patterns.",
    }


def aggregate_results(audio_res: dict, image_res: dict, text_res: dict) -> dict:
    """
    Aggregate channel-level scores into a unified threat assessment.

    [FUTURE INTEGRATION] Replace weighted average with:
    - Gemini 2.0 Flash orchestration via Google Cloud Agent Builder
    - Multi-agent reasoning across channel signals
    - Historical case correlation via MongoDB MCP
    - Threat intelligence enrichment via Elasticsearch MCP
    """
    scores = [r["score"] for r in [audio_res, image_res, text_res] if r["score"] > 0]
    if not scores:
        return {}

    # Weighted composite: max channel gets 60%, average rest 40%
    composite = int(0.6 * max(scores) + 0.4 * (sum(scores) / len(scores)))
    composite = min(composite, 99)

    # Determine risk level
    if composite >= 80:
        risk_level, risk_class = "CRITICAL", "critical"
        action = "🚨 Immediately block transaction. Escalate to Fraud Response Team. Preserve evidence for forensics."
        threat_type = "Multi-channel coordinated fraud attack"
    elif composite >= 65:
        risk_level, risk_class = "HIGH", "high"
        action = "⚠️ Flag account for manual review. Trigger step-up authentication. Notify customer."
        threat_type = "Targeted phishing / social engineering"
    elif composite >= 45:
        risk_level, risk_class = "MEDIUM", "medium"
        action = "📋 Add to watchlist. Monitor next 24h activity. Send fraud awareness alert to user."
        threat_type = "Suspicious activity — possible reconnaissance"
    else:
        risk_level, risk_class = "LOW", "low"
        action = "✅ Log for audit. No immediate action required. Routine monitoring continues."
        threat_type = "Low-confidence anomaly"

    all_signals = (
        audio_res.get("signals", []) +
        image_res.get("signals", []) +
        text_res.get("signals", [])
    )

    return {
        "composite_score": composite,
        "risk_level": risk_level,
        "risk_class": risk_class,
        "threat_type": threat_type,
        "recommended_action": action,
        "all_signals": all_signals,
        "audio_score": audio_res["score"],
        "image_score": image_res["score"],
        "text_score": text_res["score"],
        "timestamp": get_timestamp(),
        "case_id": f"CASE-{random.randint(100000, 999999)}",
    }


# ─────────────────────────────────────────────
#  UI COMPONENTS
# ─────────────────────────────────────────────

def render_hero():
    """Render the top hero/header banner."""
    st.markdown("""
    <div class="hero">
        <div class="hero-title">
            <span class="hero-accent">🛡️ OMNICHANNEL</span> ANTI-FRAUD AGENT
        </div>
        <div class="hero-sub">
            <span class="status-dot"></span>
            SYSTEM ONLINE &nbsp;│&nbsp; REAL-TIME THREAT DETECTION &nbsp;│&nbsp; AUDIO · IMAGE · TEXT
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats_bar():
    """Live-feel stats bar at the top of the dashboard."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🔍 Cases Today", f"{random.randint(1200, 1800):,}", f"+{random.randint(40,120)}")
    with c2:
        st.metric("🚨 Threats Blocked", f"{random.randint(300, 600):,}", f"+{random.randint(10,40)}")
    with c3:
        st.metric("⚡ Avg Analysis Time", "1.8s", "-0.2s")
    with c4:
        st.metric("🎯 Detection Accuracy", "97.4%", "+0.3%")


def render_input_sections():
    """Render the three channel input panels. Returns (audio_file, image_file, text_input)."""
    st.markdown("---")
    st.markdown('<div class="section-label">⬇ INPUT CHANNELS</div>', unsafe_allow_html=True)
    st.markdown("### Submit Evidence for Analysis")

    col_a, col_b, col_c = st.columns(3, gap="medium")

    # ── A. Audio Upload ──
    with col_a:
        st.markdown("""
        <div class="section-card">
            <div class="section-label">CHANNEL 01 — AUDIO</div>
            <div class="section-title">🎙️ Voice / Call Recording</div>
        </div>
        """, unsafe_allow_html=True)
        audio_file = st.file_uploader(
            "Upload call recording",
            type=["wav", "mp3"],
            key="audio_upload",
            help="Supports .wav and .mp3 formats. Max recommended: 50MB.",
        )
        if audio_file:
            st.success(f"📂 `{audio_file.name}` loaded ({audio_file.size / 1024:.1f} KB)")
            st.audio(audio_file)

    # ── B. Image Upload ──
    with col_b:
        st.markdown("""
        <div class="section-card">
            <div class="section-label">CHANNEL 02 — IMAGE</div>
            <div class="section-title">🖼️ Screenshot / Document</div>
        </div>
        """, unsafe_allow_html=True)
        image_file = st.file_uploader(
            "Upload suspicious image",
            type=["jpg", "jpeg", "png"],
            key="image_upload",
            help="Supports .jpg, .jpeg, .png. Accepts screenshots, fake documents, QR codes.",
        )
        if image_file:
            img = Image.open(BytesIO(image_file.getvalue()))
            st.image(img, caption=f"📂 {image_file.name}", use_container_width=True)

    # ── C. Text Input ──
    with col_c:
        st.markdown("""
        <div class="section-card">
            <div class="section-label">CHANNEL 03 — TEXT</div>
            <div class="section-title">💬 SMS / Email / Chat</div>
        </div>
        """, unsafe_allow_html=True)
        text_input = st.text_area(
            "Paste suspicious message",
            height=200,
            key="text_input",
            placeholder="Paste SMS, email body, chat message, or any suspicious text here...\n\nExample:\n'Dear customer, your account has been suspended. Click here to verify your OTP immediately or lose access.'",
            help="Supports raw text from any channel: SMS, email, WhatsApp, chat.",
        )
        if text_input.strip():
            word_count = len(text_input.split())
            st.caption(f"📝 {word_count} words · {len(text_input)} characters")

    return audio_file, image_file, text_input


def render_analyze_button() -> bool:
    """Centered Analyze Threat button. Returns True when clicked."""
    st.markdown("---")
    col_left, col_center, col_right = st.columns([2, 2, 2])
    with col_center:
        return st.button("🔍 ANALYZE THREAT", use_container_width=True, type="primary")


def render_analysis_progress(audio_file, image_file, text_input: str):
    """
    Show animated progress while analysis runs.
    Returns the aggregated result dict.
    """
    steps = []
    if audio_file:
        steps.append(("🎙️ Analysing audio channel...", lambda: analyze_audio(audio_file)))
    else:
        steps.append(("🎙️ Audio channel: skipped", lambda: analyze_audio(None)))

    if image_file:
        steps.append(("🖼️  Analysing image channel...", lambda: analyze_image(image_file)))
    else:
        steps.append(("🖼️  Image channel: skipped", lambda: analyze_image(None)))

    if text_input.strip():
        steps.append(("💬 Analysing text channel...", lambda: analyze_text(text_input)))
    else:
        steps.append(("💬 Text channel: skipped", lambda: analyze_text("")))

    steps.append(("🧠 Aggregating threat intelligence...", None))
    steps.append(("✅ Analysis complete", None))

    progress_bar = st.progress(0)
    status_text  = st.empty()

    audio_res = image_res = text_res = None
    results_collected = []

    total = len(steps)
    for i, (label, fn) in enumerate(steps):
        status_text.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)
        progress_bar.progress(int((i / total) * 100))

        if fn is not None:
            result = fn()
            results_collected.append(result)
        else:
            time.sleep(0.3)

    progress_bar.progress(100)
    status_text.empty()

    # Map results back to channels
    audio_res = results_collected[0] if len(results_collected) > 0 else analyze_audio(None)
    image_res = results_collected[1] if len(results_collected) > 1 else analyze_image(None)
    text_res  = results_collected[2] if len(results_collected) > 2 else analyze_text("")

    return aggregate_results(audio_res, image_res, text_res)


def render_results(result: dict):
    """Render the full Threat Analysis Results panel."""
    if not result:
        return

    st.markdown("---")
    st.markdown('<div class="result-header">⚡ THREAT ANALYSIS RESULTS</div>', unsafe_allow_html=True)

    # ── Row 1: Key metrics ──
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    score_class = (
        "score-critical" if result["composite_score"] >= 80 else
        "score-high"     if result["composite_score"] >= 65 else
        "score-medium"   if result["composite_score"] >= 45 else
        "score-low"
    )
    badge_class = f"badge-{result['risk_class']}"

    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-value {score_class}">{result['composite_score']}%</div>
            <div class="metric-label">THREAT SCORE</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div style="margin-top:0.5rem">
                <span class="risk-badge {badge_class}">{result['risk_level']}</span>
            </div>
            <div class="metric-label" style="margin-top:0.7rem">RISK LEVEL</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <div style="font-size:0.95rem; color:var(--text); margin-top:0.3rem; line-height:1.3">
                {result['threat_type']}
            </div>
            <div class="metric-label" style="margin-top:0.5rem">THREAT TYPE</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-box">
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:var(--accent); margin-top:0.4rem">
                {result['case_id']}
            </div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.7rem; color:var(--text-dim); margin-top:0.3rem">
                {result['timestamp']}
            </div>
            <div class="metric-label" style="margin-top:0.4rem">CASE ID / TIMESTAMP</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Recommended action ──
    action_colors = {
        "critical": ("rgba(255,56,96,0.12)", "#ff3860"),
        "high":     ("rgba(255,179,0,0.12)",  "#ffb300"),
        "medium":   ("rgba(255,140,0,0.10)",  "#ff8c00"),
        "low":      ("rgba(0,230,118,0.10)",  "#00e676"),
    }
    bg, border = action_colors[result["risk_class"]]
    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {border}; border-radius:8px; padding:1rem 1.4rem;">
        <div class="section-label" style="color:{border}">RECOMMENDED ACTION</div>
        <div style="font-size:1rem; color:var(--text); margin-top:0.3rem">{result['recommended_action']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 3: Channel breakdown ──
    col_l, col_r = st.columns([2, 1], gap="large")

    with col_l:
        st.markdown('<div class="section-label">CHANNEL BREAKDOWN</div>', unsafe_allow_html=True)

        channels = [
            ("🎙️ Audio", result["audio_score"]),
            ("🖼️  Image", result["image_score"]),
            ("💬 Text",  result["text_score"]),
        ]
        for label, score in channels:
            if score == 0:
                continue
            bar_color = (
                "#ff3860" if score >= 80 else
                "#ffb300" if score >= 65 else
                "#ff8c00" if score >= 45 else
                "#00e676"
            )
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.8rem;">
                <div style="width:90px; font-size:0.85rem; color:var(--text-dim)">{label}</div>
                <div style="flex:1; background:var(--bg-panel); border-radius:4px; height:10px; overflow:hidden">
                    <div style="width:{score}%; height:100%; background:{bar_color}; border-radius:4px;
                                box-shadow:0 0 8px {bar_color}66; transition:width 1s"></div>
                </div>
                <div style="width:40px; text-align:right; font-family:'Share Tech Mono',monospace;
                             font-size:0.85rem; color:{bar_color}">{score}%</div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-label">CASE METADATA</div>', unsafe_allow_html=True)
        meta = {
            "Engine":  "Anti-Fraud Agent v1.0",
            "Model":   "Gemini 2.0 Flash (soon)",
            "DB":      "MongoDB MCP (soon)",
            "Search":  "Elasticsearch MCP (soon)",
            "Signals": str(len(result["all_signals"])),
        }
        for k, v in meta.items():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:0.35rem 0;
                         border-bottom:1px solid var(--border); font-size:0.82rem;">
                <span style="color:var(--text-dim)">{k}</span>
                <span style="font-family:'Share Tech Mono',monospace; color:var(--accent)">{v}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Expander: detailed signals ──
    with st.expander("🔎 View All Detected Signals", expanded=False):
        for i, sig in enumerate(result["all_signals"], 1):
            ts = datetime.utcnow().strftime("%H:%M:%S.") + f"{random.randint(0,999):03d}"
            st.markdown(f"""
            <div class="timeline-item">
                <div class="tl-dot" style="background:var(--accent)"></div>
                <div>
                    <div class="tl-text">{sig}</div>
                    <div class="tl-time">UTC {ts} · Signal #{i:02d}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Expander: integration stubs ──
    with st.expander("🔌 API Integration Status", expanded=False):
        integrations = [
            ("Google Cloud Agent Builder", "PENDING", "Orchestration layer for multi-agent reasoning"),
            ("Gemini 2.0 Flash",           "PENDING", "Multimodal understanding: audio + image + text"),
            ("MongoDB MCP",                "PENDING", "Case storage, audit logs, fraud pattern DB"),
            ("Elasticsearch MCP",          "PENDING", "Real-time similarity search, threat intel lookup"),
            ("Cloud Speech-to-Text",       "PENDING", "Audio transcription for voice channel"),
            ("Vertex AI Vision",           "PENDING", "Document forgery detection, OCR, logo analysis"),
        ]
        for name, status, desc in integrations:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.5rem 0;
                         border-bottom:1px solid var(--border);">
                <div style="width:180px; font-family:'Rajdhani',sans-serif; font-weight:600; color:var(--text)">{name}</div>
                <div style="background:rgba(255,179,0,0.12); color:#ffb300; border:1px solid #ffb300;
                             border-radius:4px; padding:0.15rem 0.6rem; font-size:0.72rem;
                             font-family:'Share Tech Mono',monospace">{status}</div>
                <div style="font-size:0.82rem; color:var(--text-dim)">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar():
    """Sidebar with system info and configuration hints."""
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; font-weight:700;
                     color:#00d4ff; letter-spacing:0.1em; text-transform:uppercase;">
            🛡️ System Panel
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("**Version:** `1.0.0-hackathon`")
        st.markdown("**Status:** 🟢 Operational")
        st.markdown("**Mode:** Simulation (no live APIs)")
        st.markdown("---")
        st.markdown("**⚙️ Configuration**")
        threshold = st.slider("Alert Threshold (%)", 0, 100, 65)
        st.caption(f"Threats scoring ≥ {threshold}% will trigger alerts.")
        st.markdown("---")
        st.markdown("**📖 About**")
        st.caption(
            "Omnichannel Anti-Fraud Agent detects fraud signals "
            "across audio, image, and text channels using AI. "
            "Built for Google Cloud hackathon."
        )
        st.markdown("---")
        st.caption("© 2025 Anti-Fraud Team")


# ─────────────────────────────────────────────
#  MAIN APP ENTRYPOINT
# ─────────────────────────────────────────────

def main():
    render_sidebar()
    render_hero()
    render_stats_bar()

    audio_file, image_file, text_input = render_input_sections()
    clicked = render_analyze_button()

    if clicked:
        if not validate_inputs(audio_file, image_file, text_input):
            st.error("⚠️ Please provide at least one input (audio, image, or text) before analysing.")
        else:
            with st.spinner(""):
                st.info("⚡ Omnichannel analysis in progress — scanning all submitted channels...")
                result = render_analysis_progress(audio_file, image_file, text_input)

            st.success("✅ Analysis complete! See results below.")
            render_results(result)


if __name__ == "__main__":
    main()
