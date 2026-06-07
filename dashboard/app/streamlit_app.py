from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
AGENT_ROOT = ROOT / "gemini-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from fraud_agent.mcp.mongo_adapter import list_alert_logs, list_cases
from fraud_agent.multimodal import analyze_audio, analyze_image, analyze_pdf
from fraud_agent.orchestrator import analyze_text
from fraud_agent.system_health import check_system_health

st.set_page_config(page_title="Omnichannel Anti-Fraud Agent", page_icon="🛡️", layout="wide")

st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.metric-card { border: 1px solid #334155; border-radius: 14px; padding: 1rem; background: #0f172a; }
.ok { color: #22c55e; font-weight: 700; }
.warn { color: #f59e0b; font-weight: 700; }
.bad { color: #ef4444; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)


def render_report(report: dict) -> None:
    st.subheader("Threat Report")
    cols = st.columns(4)
    cols[0].metric("Threat Score", f"{report['threat_score']:.2f}")
    cols[1].metric("Risk Level", report["risk_level"])
    cols[2].metric("Fraud Type", report["fraud_type"].replace("_", " ").title())
    cols[3].metric("Alert Status", report.get("alert_status", "not_required"))
    st.write(report["reasoning_summary"])
    st.info(report["recommended_action"])
    left, right = st.columns(2)
    with left:
        st.markdown("#### Detected Entities")
        st.json(report["detected_entities"])
        st.markdown("#### Behavioral Analysis")
        st.json(report["behavioral_analysis"])
    with right:
        st.markdown("#### Verification")
        st.json(report["verification_results"])
        st.markdown("#### Contradictions")
        st.json(report.get("contradictions", []))


def victim_view() -> None:
    st.title("🛡️ Victim View")
    st.caption("Submit text, audio, image, or PDF evidence. Every path is routed through the production orchestrator.")
    tab_text, tab_audio, tab_image, tab_pdf = st.tabs(["Text", "Audio", "Image", "PDF"])
    with tab_text:
        text = st.text_area("Message or transcript", height=180)
        if st.button("Analyze Text", type="primary"):
            if not text.strip():
                st.error("Please enter evidence text before analysis.")
            else:
                with st.status("Running orchestrator pipeline", expanded=True) as status:
                    st.write("Gemini extraction → MongoDB → Elasticsearch → contradictions → scoring → alerts")
                    report = analyze_text(text)
                    status.update(label="Analysis complete", state="complete")
                st.session_state["latest_report"] = report
    with tab_audio:
        audio = st.file_uploader("Upload WAV or MP3", type=["wav", "mp3"])
        if st.button("Analyze Audio") and audio is not None:
            with st.spinner("Transcribing audio and routing transcript to orchestrator..."):
                report = analyze_audio(audio.getvalue(), suffix=Path(audio.name).suffix)
            st.session_state["latest_report"] = report
    with tab_image:
        image = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "tiff", "bmp"])
        if st.button("Analyze Image") and image is not None:
            with st.spinner("Extracting OCR text and routing to orchestrator..."):
                report = analyze_image(image.getvalue())
            st.session_state["latest_report"] = report
    with tab_pdf:
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if st.button("Analyze PDF") and pdf is not None:
            with st.spinner("Extracting PDF text and routing to orchestrator..."):
                report = analyze_pdf(pdf.getvalue())
            st.session_state["latest_report"] = report
    if "latest_report" in st.session_state:
        render_report(st.session_state["latest_report"])


def alert_log() -> None:
    st.title("📣 Guardian Alert Log")
    alerts = list_alert_logs(limit=100)
    if alerts:
        st.dataframe(alerts, use_container_width=True)
    else:
        st.info("No guardian alerts have been recorded yet.")


def case_history() -> None:
    st.title("📁 Case History")
    cases = list_cases(limit=100)
    if not cases:
        st.info("No persisted cases found.")
        return
    for case in cases:
        report = case.get("threat_report", {})
        with st.expander(f"{case.get('case_id')} · {report.get('risk_level')} · {case.get('timestamp')}"):
            render_report(report)


def system_health() -> None:
    st.title("❤️ System Health")
    health = check_system_health()
    rows = []
    for component, data in health.items():
        rows.append({"component": component, **data})
    st.dataframe(rows, use_container_width=True)


page = st.sidebar.radio("Navigation", ["Victim View", "Guardian Alert Log", "Case History", "System Health"])
if page == "Victim View":
    victim_view()
elif page == "Guardian Alert Log":
    alert_log()
elif page == "Case History":
    case_history()
else:
    system_health()
