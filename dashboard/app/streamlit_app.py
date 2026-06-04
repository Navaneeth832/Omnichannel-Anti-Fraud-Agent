import base64
import json
import mimetypes
import os
import random
import time
from datetime import datetime
from io import BytesIO

import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  PAGE CONFIG
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
st.set_page_config(
    page_title="FraudShield ΓÇö Anti-Fraud Intelligence",
    page_icon="≡ƒ¢í∩╕Å",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  GLOBAL CSS ΓÇö injected once at startup
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-base:      #0B0F19;
    --bg-card:      #111827;
    --bg-elevated:  #1A2332;
    --bg-overlay:   #1E2A3A;
    --accent:       #4F8CFF;
    --accent-glow:  rgba(79,140,255,0.25);
    --accent-dim:   rgba(79,140,255,0.12);
    --accent2:      #7C3AED;
    --success:      #22C55E;
    --success-dim:  rgba(34,197,94,0.12);
    --warning:      #F59E0B;
    --warning-dim:  rgba(245,158,11,0.12);
    --danger:       #EF4444;
    --danger-dim:   rgba(239,68,68,0.12);
    --info:         #06B6D4;
    --info-dim:     rgba(6,182,212,0.12);
    --text-primary:   #F8FAFC;
    --text-secondary: #94A3B8;
    --text-muted:     #475569;
    --border:         rgba(255,255,255,0.06);
    --border-hover:   rgba(79,140,255,0.3);
    --shadow-sm:      0 1px 3px rgba(0,0,0,0.4);
    --shadow-md:      0 4px 16px rgba(0,0,0,0.4);
    --shadow-glow:    0 0 20px rgba(79,140,255,0.18);
    --r-sm:  6px;
    --r-md:  10px;
    --r-lg:  14px;
    --r-xl:  20px;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 4rem !important; max-width: 1440px; }

/* Subtle grid */
body::after {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(79,140,255,0.012) 1px, transparent 1px),
        linear-gradient(90deg, rgba(79,140,255,0.012) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none; z-index: 0;
}

/* ΓöÇΓöÇ Logo section ΓöÇΓöÇ */
.fs-logo-section {
    display: flex; align-items: center; gap: 18px;
    padding: 2.5rem 0 0; position: relative; z-index: 1;
}
.fs-logo-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1;
    background: linear-gradient(135deg, #F8FAFC 0%, #4F8CFF 60%, #7C3AED 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 5px;
}
.fs-logo-tagline {
    font-size: 0.78rem; font-weight: 500; letter-spacing: 0.18em;
    color: var(--text-muted); text-transform: uppercase;
}
.fs-logo-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--accent-dim); border: 1px solid rgba(79,140,255,0.25);
    border-radius: 999px; padding: 5px 14px;
    font-size: 0.72rem; font-weight: 700; color: var(--accent);
    letter-spacing: 0.08em; text-transform: uppercase; margin-left: auto;
}
.fs-pulse-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--success); box-shadow: 0 0 6px var(--success);
    animation: pulseDot 2s ease-in-out infinite; display: inline-block;
}
@keyframes pulseDot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.4; transform:scale(0.8); }
}

/* ΓöÇΓöÇ Nav ΓöÇΓöÇ */
.fs-nav {
    position: sticky; top: 0; z-index: 100;
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    background: rgba(11,15,25,0.88); border-bottom: 1px solid var(--border);
    margin: 1.5rem -2rem 0; padding: 0 2rem;
    display: flex; align-items: center; gap: 2px; height: 52px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.fs-nav-item {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 14px; border-radius: var(--r-sm);
    font-size: 0.82rem; font-weight: 600; color: var(--text-secondary);
    cursor: default; transition: all 0.2s; border: 1px solid transparent;
    white-space: nowrap; letter-spacing: 0.01em;
}
.fs-nav-item:hover { color: var(--text-primary); background: var(--bg-elevated); border-color: var(--border); }
.fs-nav-item.active { color: var(--accent); background: var(--accent-dim); border-color: rgba(79,140,255,0.2); }
.fs-nav-sep { width:1px; height:20px; background:var(--border); margin:0 8px; }
.fs-nav-right { margin-left: auto; display:flex; align-items:center; gap:10px; }
.fs-status-chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 600;
    background: var(--success-dim); border: 1px solid rgba(34,197,94,0.2); color: var(--success);
}

/* ΓöÇΓöÇ KPI cards ΓöÇΓöÇ */
.fs-kpi-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--r-lg); padding: 1.4rem 1.6rem; position: relative;
    overflow: hidden; transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
    box-shadow: var(--shadow-sm); animation: fadeUp 0.5s ease both;
}
.fs-kpi-card:hover { border-color: var(--border-hover); transform: translateY(-2px); box-shadow: var(--shadow-md), var(--shadow-glow); }
.fs-kpi-accent-line { position:absolute; top:0; left:0; right:0; height:2px; }
.fs-kpi-icon {
    width:38px; height:38px; border-radius: var(--r-sm);
    display:flex; align-items:center; justify-content:center;
    font-size:1.1rem; margin-bottom:1rem;
}
.fs-kpi-value { font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:700; letter-spacing:-0.03em; line-height:1; color:var(--text-primary); margin-bottom:4px; }
.fs-kpi-label { font-size:0.72rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:10px; }
.fs-kpi-delta { display:inline-flex; align-items:center; gap:4px; font-size:0.76rem; font-weight:600; padding:2px 8px; border-radius:999px; }
.delta-up   { background:var(--success-dim); color:var(--success); }
.delta-down { background:var(--danger-dim);  color:var(--danger); }

/* ΓöÇΓöÇ Section header ΓöÇΓöÇ */
.fs-section-header { display:flex; align-items:center; gap:12px; margin:2.5rem 0 1.2rem; animation:fadeUp 0.5s ease both; }
.fs-section-icon { width:32px; height:32px; border-radius:var(--r-sm); background:var(--accent-dim); border:1px solid rgba(79,140,255,0.2); display:flex; align-items:center; justify-content:center; font-size:0.9rem; flex-shrink:0; }
.fs-section-title { font-family:'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600; color:var(--text-primary); letter-spacing:-0.01em; }
.fs-section-desc { font-size:0.78rem; color:var(--text-muted); margin-top:1px; }
.fs-section-line { flex:1; height:1px; background:var(--border); }

/* ΓöÇΓöÇ Channel cards ΓöÇΓöÇ */
.fs-channel-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--r-xl); padding: 1.6rem; height:100%;
    transition: border-color 0.3s, box-shadow 0.3s; animation: fadeUp 0.5s ease both;
}
.fs-channel-card:hover { border-color: var(--border-hover); box-shadow: var(--shadow-md); }
.fs-channel-badge {
    display:inline-flex; align-items:center; gap:6px; padding:4px 10px;
    border-radius:999px; font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
    text-transform:uppercase; margin-bottom:10px;
}
.badge-audio { background:rgba(124,58,237,0.15); color:#A78BFA; border:1px solid rgba(124,58,237,0.25); }
.badge-image { background:rgba(6,182,212,0.12);  color:#22D3EE; border:1px solid rgba(6,182,212,0.2); }
.badge-text  { background:rgba(79,140,255,0.12); color:var(--accent); border:1px solid rgba(79,140,255,0.2); }
.fs-channel-title { font-family:'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600; color:var(--text-primary); letter-spacing:-0.01em; margin-bottom:4px; }
.fs-channel-desc  { font-size:0.78rem; color:var(--text-muted); margin-bottom:1rem; }
.fs-channel-divider { height:1px; background:var(--border); margin:0 0 1rem; }

/* ΓöÇΓöÇ PDF Preview ΓöÇΓöÇ */
.fs-pdf-preview {
    background: var(--bg-elevated); border: 1px solid rgba(6,182,212,0.2);
    border-radius: var(--r-lg); padding: 1.2rem; margin-top: 0.5rem;
    display: flex; align-items: center; gap: 14px;
}
.fs-pdf-icon {
    width: 48px; height: 48px; border-radius: var(--r-md);
    background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.25);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; flex-shrink: 0;
}
.fs-pdf-name { font-family:'Space Grotesk',sans-serif; font-size:0.88rem; font-weight:600; color:var(--text-primary); margin-bottom:3px; word-break:break-all; }
.fs-pdf-meta { font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--text-muted); }
.fs-pdf-badge { display:inline-flex; align-items:center; gap:5px; padding:3px 9px; border-radius:999px; font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; background:rgba(239,68,68,0.12); color:#F87171; border:1px solid rgba(239,68,68,0.25); margin-top:5px; }

/* ΓöÇΓöÇ Results section ΓöÇΓöÇ */
.fs-results-divider { border:none; border-top:1px solid var(--border); margin:2rem 0 1rem; }

.fs-threat-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--r-xl); padding: 1.8rem 1.6rem; text-align:center;
    position:relative; overflow:hidden; animation:fadeUp 0.4s ease both;
}
.fs-threat-card::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(circle at 50% 0%, rgba(79,140,255,0.07) 0%, transparent 65%);
    pointer-events:none;
}

.fs-risk-badge {
    display:inline-flex; align-items:center; gap:8px; padding:6px 18px;
    border-radius:var(--r-md); font-family:'Space Grotesk',sans-serif;
    font-size:1rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
}
.risk-critical { background:var(--danger-dim);  color:var(--danger);  border:1px solid rgba(239,68,68,0.3); }
.risk-high      { background:var(--warning-dim); color:var(--warning); border:1px solid rgba(245,158,11,0.3); }
.risk-medium    { background:rgba(251,191,36,0.1); color:#FBBF24;      border:1px solid rgba(251,191,36,0.25); }
.risk-low       { background:var(--success-dim); color:var(--success); border:1px solid rgba(34,197,94,0.3); }

.fs-case-panel { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--r-md); padding:10px 14px; margin-top:1rem; }
.fs-case-id { font-family:'JetBrains Mono',monospace; font-size:1rem; font-weight:500; color:var(--accent); margin-bottom:3px; }
.fs-case-ts { font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--text-muted); }

.fs-info-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--r-lg); padding:1.2rem 1.4rem; margin-bottom:1rem;
}
.fs-info-label {
    font-size:0.68rem; font-weight:700; letter-spacing:0.15em;
    text-transform:uppercase; color:var(--text-muted); margin-bottom:6px;
}
.fs-info-value {
    font-family:'Space Grotesk',sans-serif; font-size:1.05rem;
    font-weight:600; color:var(--text-primary);
}

.fs-action-banner {
    border-radius:var(--r-lg); padding:1.1rem 1.4rem;
    display:flex; align-items:flex-start; gap:12px; margin-bottom:1rem;
}
.fs-action-title { font-size:0.68rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:5px; }
.fs-action-text  { font-size:0.9rem; font-weight:500; line-height:1.5; color:var(--text-primary); }

/* Channel bars */
.fs-channel-row { display:flex; align-items:center; gap:12px; margin-bottom:1rem; }
.fs-channel-name { font-size:0.8rem; font-weight:600; color:var(--text-secondary); width:78px; flex-shrink:0; }
.fs-bar-track    { flex:1; background:var(--bg-elevated); border-radius:999px; height:8px; overflow:hidden; }
.fs-bar-fill     { height:100%; border-radius:999px; transition:width 1.2s cubic-bezier(0.4,0,0.2,1); }
.fs-bar-score    { font-family:'JetBrains Mono',monospace; font-size:0.8rem; font-weight:500; width:36px; text-align:right; }

/* Signals */
.fs-signal-item {
    display:flex; align-items:flex-start; gap:12px; padding:10px 6px;
    border-bottom:1px solid rgba(255,255,255,0.04); border-radius:6px;
    transition:background 0.2s;
}
.fs-signal-item:last-child { border-bottom:none; }
.fs-signal-item:hover      { background:rgba(79,140,255,0.04); }
.fs-signal-dot { width:9px; height:9px; border-radius:50%; border:2px solid; flex-shrink:0; margin-top:5px; }
.fs-signal-body { flex:1; }
.fs-signal-text { font-size:0.85rem; color:var(--text-primary); font-weight:500; line-height:1.4; }
.fs-signal-meta { display:flex; align-items:center; gap:8px; margin-top:3px; flex-wrap:wrap; }
.fs-signal-time { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:var(--text-muted); }
.fs-signal-ch   { font-size:0.63rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; padding:2px 7px; border-radius:4px; }
.fs-signal-num  { font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:var(--text-muted); }

/* Integration table */
.fs-int-row { display:flex; align-items:center; gap:12px; padding:9px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.fs-int-row:last-child { border-bottom:none; }
.fs-int-name   { font-weight:600; font-size:0.83rem; color:var(--text-primary); width:170px; flex-shrink:0; }
.fs-int-badge  { font-family:'JetBrains Mono',monospace; font-size:0.66rem; font-weight:500; padding:3px 8px; border-radius:4px; background:var(--warning-dim); color:var(--warning); border:1px solid rgba(245,158,11,0.2); flex-shrink:0; }
.fs-int-desc   { font-size:0.78rem; color:var(--text-muted); }

.fs-meta-row { display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.fs-meta-row:last-child { border-bottom:none; }
.fs-meta-key  { font-size:0.78rem; color:var(--text-muted); font-weight:500; }
.fs-meta-val  { font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--accent); font-weight:500; }

/* Webhook panel */
.fs-webhook-label { font-size:0.68rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px; }

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F8CFF 0%, #6B5FE8 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--r-md) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important; font-size: 1rem !important;
    letter-spacing: 0.04em !important; padding: 0.75rem 2rem !important;
    transition: all 0.25s !important;
    box-shadow: 0 4px 16px rgba(79,140,255,0.35) !important;
    text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(79,140,255,0.5), 0 0 0 4px rgba(79,140,255,0.1) !important;
}
.stButton > button {
    background: var(--bg-elevated) !important; color: var(--text-primary) !important;
    border: 1px solid var(--border) !important; border-radius: var(--r-md) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 0.88rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { background: var(--bg-overlay) !important; border-color: var(--border-hover) !important; }

/* Progress */
.stProgress > div > div { background: linear-gradient(90deg, #4F8CFF, #7C3AED) !important; border-radius: 999px !important; }
.stProgress > div { background: var(--bg-elevated) !important; border-radius: 999px !important; height: 6px !important; }

/* File uploader */
.stFileUploader > div { background: var(--bg-elevated) !important; border: 1px dashed rgba(79,140,255,0.25) !important; border-radius: var(--r-lg) !important; transition: border-color 0.25s !important; }
.stFileUploader > div:hover { border-color: rgba(79,140,255,0.5) !important; background: rgba(79,140,255,0.04) !important; }
.stFileUploader label { color: var(--text-secondary) !important; font-family: 'Plus Jakarta Sans',sans-serif !important; }

/* Textarea */
.stTextArea textarea {
    background: var(--bg-elevated) !important; color: var(--text-primary) !important;
    border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.9rem !important; line-height: 1.6 !important;
}
.stTextArea textarea:focus { border-color: var(--border-hover) !important; box-shadow: 0 0 0 3px rgba(79,140,255,0.08) !important; }
.stTextArea textarea::placeholder { color: var(--text-muted) !important; }

/* Expander */
details { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; overflow: hidden !important; }
details summary { padding: 1rem 1.4rem !important; font-family: 'Space Grotesk',sans-serif !important; font-size: 0.9rem !important; font-weight: 600 !important; color: var(--text-primary) !important; }
details[open] summary { border-bottom: 1px solid var(--border) !important; }

/* Alerts */
div[data-testid="stSuccessMessage"] { background: var(--success-dim) !important; border: 1px solid rgba(34,197,94,0.2) !important; border-radius: var(--r-md) !important; }
div[data-testid="stInfoMessage"]    { background: var(--info-dim)    !important; border: 1px solid rgba(6,182,212,0.2)  !important; border-radius: var(--r-md) !important; }
div[data-testid="stWarningMessage"] { background: var(--warning-dim) !important; border: 1px solid rgba(245,158,11,0.2) !important; border-radius: var(--r-md) !important; }
div[data-testid="stErrorMessage"]   { background: var(--danger-dim)  !important; border: 1px solid rgba(239,68,68,0.2)  !important; border-radius: var(--r-md) !important; }

/* Metrics */
div[data-testid="stMetric"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; padding: 1rem 1.2rem !important; }
div[data-testid="stMetricValue"] { font-family: 'Space Grotesk',sans-serif !important; color: var(--text-primary) !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* Image */
.stImage img { border-radius: var(--r-lg) !important; border: 1px solid var(--border) !important; }

/* Caption */
.stCaption { color: var(--text-muted) !important; font-size: 0.75rem !important; }

/* Divider */
hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 1.5rem 0 !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--bg-card) !important; border-right: 1px solid var(--border) !important; }

/* Scrollbar */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius:3px; }

/* Spinner animation used inline */
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  HELPER ΓÇö safe HTML component
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def _html(html_str: str, height: int = 0):
    wrapper = f"""
    <html><head>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:transparent; font-family:'Plus Jakarta Sans',sans-serif; color:#F8FAFC; }}
    :root {{
        --bg-card:#111827; --bg-elevated:#1A2332; --bg-overlay:#1E2A3A;
        --accent:#4F8CFF; --accent-dim:rgba(79,140,255,0.12);
        --success:#22C55E; --success-dim:rgba(34,197,94,0.12);
        --warning:#F59E0B; --warning-dim:rgba(245,158,11,0.12);
        --danger:#EF4444;  --danger-dim:rgba(239,68,68,0.12);
        --text-primary:#F8FAFC; --text-secondary:#94A3B8; --text-muted:#475569;
        --border:rgba(255,255,255,0.06); --r-sm:6px; --r-md:10px; --r-lg:14px; --r-xl:20px;
    }}
    @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes pulseDot {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.4; }} }}
    @keyframes float {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-4px); }} }}
    </style>
    </head><body>{html_str}</body></html>
    """
    components.html(wrapper, height=height, scrolling=False)


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  UTILITY FUNCTIONS
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def get_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def encode_image_base64(image_file) -> str:
    return base64.b64encode(image_file.getvalue()).decode("utf-8")

def build_upload_tuple(uploaded_file):
    if uploaded_file is None:
        return None
    content_type = getattr(uploaded_file, "type", None) or mimetypes.guess_type(uploaded_file.name)[0]
    return (uploaded_file.name, uploaded_file.getvalue(), content_type or "application/octet-stream")

def validate_inputs(audio_file, image_file, text_input: str) -> bool:
    return any([audio_file is not None, image_file is not None, text_input.strip()])

def is_pdf(uploaded_file) -> bool:
    if uploaded_file is None:
        return False
    return (
        getattr(uploaded_file, "type", "") == "application/pdf"
        or uploaded_file.name.lower().endswith(".pdf")
    )

def format_file_size(size_bytes: int) -> str:
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes / 1024:.1f} KB"

def post_media_to_agent_builder(audio_file, image_file, text_input: str) -> dict:
    webhook_url = os.getenv("AGENT_BUILDER_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {"status": "skipped", "message": "AGENT_BUILDER_WEBHOOK_URL is not configured."}
    headers = {}
    bearer_token = os.getenv("AGENT_BUILDER_WEBHOOK_BEARER_TOKEN", "").strip()
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    payload = {
        "timestamp": get_timestamp(), "source": "streamlit_dashboard",
        "channels": json.dumps({"audio": audio_file is not None, "image": image_file is not None, "text": bool(text_input.strip())}),
        "text": text_input.strip(),
    }
    files = {}
    if build_upload_tuple(audio_file): files["audio"] = build_upload_tuple(audio_file)
    if build_upload_tuple(image_file): files["image"] = build_upload_tuple(image_file)
    timeout_secs = int(os.getenv("AGENT_BUILDER_WEBHOOK_TIMEOUT_SECS", "30"))
    try:
        response = requests.post(webhook_url, data=payload, files=files or None, headers=headers, timeout=timeout_secs)
        response.raise_for_status()
        body = response.text.strip()
        if len(body) > 500: body = body[:500] + "..."
        return {"status": "success", "message": f"Webhook accepted request ({response.status_code}).", "status_code": response.status_code, "response_body": body}
    except requests.RequestException as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        body = exc.response.text.strip()[:500] if getattr(exc, "response", None) else ""
        return {"status": "error", "message": f"Webhook POST failed: {exc}", "status_code": status_code, "response_body": body}


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  ANALYSIS ENGINE
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def analyze_audio(audio_file) -> dict:
    if audio_file is None:
        return {"score": 0, "signals": [], "summary": "No audio provided."}
    time.sleep(0.4)
    score = random.randint(55, 92)
    return {"score": score, "signals": [
        "Synthetic voice characteristics detected (TTS artifacts)",
        "Urgency language pattern matched fraud corpus",
        "Caller ID spoofing metadata present",
        "Speech cadence anomaly: 2.3╧â above baseline",
    ], "summary": f"Audio analysis complete. {score}% fraud probability."}

def analyze_image(image_file) -> dict:
    if image_file is None:
        return {"score": 0, "signals": [], "summary": "No image provided."}
    time.sleep(0.4)
    score = random.randint(45, 88)

    # PDF-specific signals vs image signals
    if is_pdf(image_file):
        signals = [
            "PDF document submitted for forensic analysis",
            "Embedded metadata stripped ΓÇö common in fraudulent documents",
            "Font substitution detected ΓÇö possible template reuse",
            "Digital signature absent ΓÇö document authenticity unverified",
            "Hidden layers or form fields identified in PDF structure",
        ]
        summary = f"PDF document analysis complete. {score}% fraud probability."
    else:
        signals = [
            "QR code detected ΓÇö destination URL suspicious",
            "Logo manipulation: 87% similarity to known phishing template",
            "Metadata stripped ΓÇö likely screenshot from dark-web tool",
            "Brand impersonation: HDFC Bank (confidence 0.94)",
        ]
        summary = f"Image analysis complete. {score}% fraud probability."

    return {"score": score, "signals": signals, "summary": summary}

def analyze_text(text_input: str) -> dict:
    if not text_input.strip():
        return {"score": 0, "signals": [], "summary": "No text provided."}
    time.sleep(0.3)
    score = random.randint(60, 95)
    fraud_keywords = ["otp", "urgent", "verify", "click", "account", "suspended",
                      "prize", "winner", "kyc", "bank", "reward", "limited time"]
    hits = [kw for kw in fraud_keywords if kw.lower() in text_input.lower()]
    signals = [f"Phishing keyword detected: '{kw}'" for kw in hits[:3]] or ["No obvious keywords ΓÇö deeper semantic analysis recommended"]
    signals += ["Sender domain not in trusted registry", f"Message entropy score: {random.uniform(3.1, 4.8):.2f} (elevated)"]
    return {"score": score, "signals": signals, "summary": f"Text analysis complete. {score}% fraud probability."}

def aggregate_results(audio_res: dict, image_res: dict, text_res: dict) -> dict:
    scores = [r["score"] for r in [audio_res, image_res, text_res] if r["score"] > 0]
    if not scores:
        return {}
    composite = int(0.6 * max(scores) + 0.4 * (sum(scores) / len(scores)))
    composite = min(composite, 99)
    if composite >= 80:
        risk_level, risk_class = "CRITICAL", "critical"
        action = "≡ƒÜ¿ Immediately block transaction. Escalate to Fraud Response Team. Preserve evidence for forensics."
        threat_type = "Multi-channel coordinated fraud attack"
    elif composite >= 65:
        risk_level, risk_class = "HIGH", "high"
        action = "ΓÜá∩╕Å Flag account for manual review. Trigger step-up authentication. Notify customer."
        threat_type = "Targeted phishing / social engineering"
    elif composite >= 45:
        risk_level, risk_class = "MEDIUM", "medium"
        action = "≡ƒôï Add to watchlist. Monitor next 24h activity. Send fraud awareness alert to user."
        threat_type = "Suspicious activity ΓÇö possible reconnaissance"
    else:
        risk_level, risk_class = "LOW", "low"
        action = "Γ£à Log for audit. No immediate action required. Routine monitoring continues."
        threat_type = "Low-confidence anomaly"
    return {
        "composite_score": composite, "risk_level": risk_level, "risk_class": risk_class,
        "threat_type": threat_type, "recommended_action": action,
        "all_signals": audio_res.get("signals",[]) + image_res.get("signals",[]) + text_res.get("signals",[]),
        "audio_score": audio_res["score"], "image_score": image_res["score"], "text_score": text_res["score"],
        "timestamp": get_timestamp(), "case_id": f"CASE-{random.randint(100000,999999)}",
    }


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  DESIGN HELPERS
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def _score_color(s: int) -> str:
    if s >= 80: return "#EF4444"
    if s >= 65: return "#F59E0B"
    if s >= 45: return "#FBBF24"
    return "#22C55E"

def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  LOGO SVG
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

LOGO_SVG = """
<svg width="64" height="64" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sg" x1="0" y1="0" x2="72" y2="72" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#4F8CFF"/><stop offset="50%" stop-color="#7C3AED"/><stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
    <linearGradient id="ig" x1="0" y1="0" x2="72" y2="72" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#1E3A6E"/><stop offset="100%" stop-color="#2D1B69"/>
    </linearGradient>
    <radialGradient id="rg" cx="50%" cy="40%" r="45%">
      <stop offset="0%" stop-color="rgba(79,140,255,0.22)"/><stop offset="100%" stop-color="transparent"/>
    </radialGradient>
    <filter id="gf"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <path d="M36 4L10 14V34C10 50 21 63 36 68C51 63 62 50 62 34V14L36 4Z" fill="url(#sg)" opacity="0.22" filter="url(#gf)"/>
  <path d="M36 7L13 16V34C13 48.5 23 60.5 36 65C49 60.5 59 48.5 59 34V16L36 7Z" fill="url(#ig)" stroke="url(#sg)" stroke-width="1.5"/>
  <path d="M36 7L13 16V34C13 48.5 23 60.5 36 65C49 60.5 59 48.5 59 34V16L36 7Z" fill="url(#rg)"/>
  <line x1="22" y1="28" x2="50" y2="28" stroke="#4F8CFF" stroke-width="0.8" stroke-opacity="0.45" stroke-dasharray="3 2"/>
  <line x1="22" y1="36" x2="50" y2="36" stroke="#4F8CFF" stroke-width="0.8" stroke-opacity="0.25" stroke-dasharray="4 3"/>
  <line x1="24" y1="43" x2="48" y2="43" stroke="#4F8CFF" stroke-width="0.8" stroke-opacity="0.18" stroke-dasharray="3 2"/>
  <line x1="28" y1="21" x2="28" y2="51" stroke="#7C3AED" stroke-width="0.8" stroke-opacity="0.38" stroke-dasharray="3 3"/>
  <line x1="36" y1="17" x2="36" y2="55" stroke="#4F8CFF" stroke-width="0.8" stroke-opacity="0.2"  stroke-dasharray="4 2"/>
  <line x1="44" y1="21" x2="44" y2="51" stroke="#7C3AED" stroke-width="0.8" stroke-opacity="0.38" stroke-dasharray="3 3"/>
  <circle cx="28" cy="28" r="2.5" fill="#4F8CFF" filter="url(#gf)"/>
  <circle cx="44" cy="28" r="2.5" fill="#7C3AED" filter="url(#gf)"/>
  <circle cx="28" cy="43" r="2.5" fill="#06B6D4" filter="url(#gf)"/>
  <circle cx="44" cy="43" r="2.5" fill="#4F8CFF" filter="url(#gf)"/>
  <circle cx="36" cy="36" r="7"   fill="rgba(79,140,255,0.1)" stroke="url(#sg)" stroke-width="1.5"/>
  <circle cx="36" cy="36" r="3.5" fill="url(#sg)"/>
  <circle cx="36" cy="36" r="1.5" fill="white" opacity="0.92"/>
  <circle cx="36" cy="13" r="1.5" fill="#4F8CFF" opacity="0.8"/>
  <circle cx="20" cy="19" r="1"   fill="#7C3AED" opacity="0.6"/>
  <circle cx="52" cy="19" r="1"   fill="#7C3AED" opacity="0.6"/>
</svg>
"""

# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  PDF ICON SVG
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

PDF_ICON_SVG = """
<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="28" height="28" rx="6" fill="rgba(239,68,68,0.15)"/>
  <path d="M7 5h10l4 4v14H7V5z" fill="none" stroke="#F87171" stroke-width="1.4" stroke-linejoin="round"/>
  <path d="M17 5v4h4" fill="none" stroke="#F87171" stroke-width="1.4" stroke-linejoin="round"/>
  <text x="14" y="19" text-anchor="middle" font-family="Space Grotesk,sans-serif"
        font-size="5.5" font-weight="700" fill="#F87171" letter-spacing="0.3">PDF</text>
</svg>
"""


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  UI COMPONENTS
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def render_logo():
    _html(f"""
    <div style="display:flex;align-items:center;gap:18px;padding:2.5rem 0 0">
      <div style="flex-shrink:0;animation:float 4s ease-in-out infinite">{LOGO_SVG}</div>
      <div style="flex:1">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:2.5rem;font-weight:700;
                    letter-spacing:-0.02em;line-height:1;margin-bottom:6px;
                    background:linear-gradient(135deg,#F8FAFC 0%,#4F8CFF 60%,#7C3AED 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
          FraudShield
        </div>
        <div style="font-size:0.75rem;font-weight:500;letter-spacing:0.18em;color:#475569;text-transform:uppercase">
          Omnichannel Anti-Fraud Intelligence Platform
        </div>
      </div>
      <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(79,140,255,0.12);
                  border:1px solid rgba(79,140,255,0.25);border-radius:999px;padding:6px 16px;
                  font-size:0.72rem;font-weight:700;color:#4F8CFF;letter-spacing:0.08em;text-transform:uppercase;flex-shrink:0">
        <span style="width:7px;height:7px;border-radius:50%;background:#22C55E;
                     box-shadow:0 0 6px #22C55E;display:inline-block;animation:pulseDot 2s infinite"></span>
        System Online
      </div>
    </div>
    """, height=120)


def render_nav():
    st.markdown("""
    <div class="fs-nav">
      <div class="fs-nav-item active">≡ƒ¢í∩╕Å Threat Analysis</div>
      <div class="fs-nav-item">≡ƒôè Analytics</div>
      <div class="fs-nav-item">≡ƒôü Case History</div>
      <div class="fs-nav-item">≡ƒöî Integrations</div>
      <div class="fs-nav-item">ΓÜÖ∩╕Å Settings</div>
      <div class="fs-nav-sep"></div>
      <div class="fs-nav-right">
        <span class="fs-status-chip">
          <span style="width:6px;height:6px;border-radius:50%;background:#22C55E;box-shadow:0 0 5px #22C55E;display:inline-block"></span>
          All Systems Operational
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_bar():
    cases     = random.randint(1200, 1800)
    threats   = random.randint(300, 600)
    c_delta   = random.randint(40, 120)
    t_delta   = random.randint(10, 40)

    kpis = [
        ("≡ƒöì", "#4F8CFF", "79,140,255", f"{cases:,}",   f"+{c_delta}",  "Cases Today",     True),
        ("≡ƒÜ¿", "#EF4444", "239,68,68",  f"{threats:,}", f"+{t_delta}",  "Threats Blocked", True),
        ("ΓÜí", "#22C55E", "34,197,94",  "1.8s",         "ΓêÆ0.2s",        "Avg Analysis",    False),
        ("≡ƒÄ»", "#F59E0B", "245,158,11", "97.4%",        "+0.3%",        "Detection Acc.",  True),
    ]

    cols = st.columns(4, gap="medium")
    for i, (col, (icon, color, rgb, value, delta, label, up)) in enumerate(zip(cols, kpis)):
        with col:
            delta_bg    = f"rgba({rgb},0.12)" if up else "rgba(239,68,68,0.12)"
            delta_color = color if up else "#EF4444"
            st.markdown(f"""
            <div class="fs-kpi-card" style="animation-delay:{i*0.06}s">
              <div class="fs-kpi-accent-line" style="background:linear-gradient(90deg,{color},transparent)"></div>
              <div class="fs-kpi-icon" style="background:rgba({rgb},0.12);color:{color}">{icon}</div>
              <div class="fs-kpi-value">{value}</div>
              <div class="fs-kpi-label">{label}</div>
              <span class="fs-kpi-delta" style="background:{delta_bg};color:{delta_color}">{delta}</span>
            </div>
            """, unsafe_allow_html=True)


def render_section_header(icon: str, title: str, desc: str = ""):
    desc_html = f'<div class="fs-section-desc">{desc}</div>' if desc else ""
    st.markdown(f"""
    <div class="fs-section-header">
      <div class="fs-section-icon">{icon}</div>
      <div><div class="fs-section-title">{title}</div>{desc_html}</div>
      <div class="fs-section-line"></div>
    </div>
    """, unsafe_allow_html=True)


def render_pdf_preview(image_file):
    """Render a styled PDF preview card inside an iframe."""
    size_str  = format_file_size(image_file.size)
    file_name = image_file.name

    _html(f"""
    <div style="background:#1A2332;border:1px solid rgba(239,68,68,0.22);border-radius:14px;
                padding:1.1rem 1.2rem;display:flex;align-items:center;gap:14px;
                animation:fadeUp 0.35s ease both;margin-top:4px">

      <!-- PDF icon -->
      <div style="width:52px;height:52px;border-radius:10px;background:rgba(239,68,68,0.12);
                  border:1px solid rgba(239,68,68,0.28);display:flex;align-items:center;
                  justify-content:center;font-size:1.6rem;flex-shrink:0">
        ≡ƒôä
      </div>

      <!-- File info -->
      <div style="flex:1;min-width:0">
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;font-weight:600;
                    color:#F8FAFC;margin-bottom:3px;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis"
             title="{file_name}">{file_name}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#475569;
                    margin-bottom:6px">{size_str}</div>
        <div style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;
                    border-radius:999px;font-size:0.65rem;font-weight:700;
                    letter-spacing:0.1em;text-transform:uppercase;
                    background:rgba(239,68,68,0.12);color:#F87171;
                    border:1px solid rgba(239,68,68,0.28)">
          ≡ƒôï PDF Document ΓÇö Queued for forensic analysis
        </div>
      </div>

      <!-- Check mark -->
      <div style="width:32px;height:32px;border-radius:50%;background:rgba(34,197,94,0.12);
                  border:1px solid rgba(34,197,94,0.3);display:flex;align-items:center;
                  justify-content:center;flex-shrink:0;font-size:1rem">
        Γ£ô
      </div>
    </div>
    """, height=110)


def render_input_sections():
    render_section_header("Γ¼ç", "Submit Evidence",
                           "Upload media across any combination of channels for multi-vector analysis")

    col_a, col_b, col_c = st.columns(3, gap="medium")

    # ΓöÇΓöÇ Channel 01 ΓÇö Audio ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    with col_a:
        st.markdown("""
        <div class="fs-channel-card">
          <span class="fs-channel-badge badge-audio">≡ƒÄÖ Channel 01 ΓÇö Audio</span>
          <div class="fs-channel-title">Voice &amp; Call Recording</div>
          <div class="fs-channel-desc">Upload suspicious call recordings for voice biometric and deepfake analysis</div>
          <div class="fs-channel-divider"></div>
        </div>
        """, unsafe_allow_html=True)
        audio_file = st.file_uploader("Upload call recording", type=["wav", "mp3"], key="audio_upload",
                                      help="Supports .wav and .mp3. Max recommended: 50MB.")
        if audio_file:
            st.success(f"Γ£ô `{audio_file.name}` ({format_file_size(audio_file.size)})")
            st.audio(audio_file)

    # ΓöÇΓöÇ Channel 02 ΓÇö Image / PDF ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    with col_b:
        st.markdown("""
        <div class="fs-channel-card">
          <span class="fs-channel-badge badge-image">≡ƒû╝ Channel 02 ΓÇö Image / Doc</span>
          <div class="fs-channel-title">Screenshots &amp; Documents</div>
          <div class="fs-channel-desc">
            Upload screenshots, fake documents, QR codes, or <strong style="color:#22D3EE">PDF files</strong>
            for visual &amp; document forensics
          </div>
          <div class="fs-channel-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        image_file = st.file_uploader(
            "Upload suspicious image or PDF document",
            type=["jpg", "jpeg", "png", "pdf"],
            key="image_upload",
            help="Supports .jpg, .jpeg, .png and .pdf  ┬╖  Max recommended: 50 MB",
        )

        if image_file:
            if is_pdf(image_file):
                # ΓöÇΓöÇ PDF preview ΓöÇΓöÇ
                render_pdf_preview(image_file)
                st.caption("≡ƒôä PDF document ready ΓÇö document forensics pipeline will be applied.")
            else:
                # ΓöÇΓöÇ Image preview ΓöÇΓöÇ
                img = Image.open(BytesIO(image_file.getvalue()))
                st.image(img, caption=f"Γ£ô {image_file.name}", use_container_width=True)

    # ΓöÇΓöÇ Channel 03 ΓÇö Text ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    with col_c:
        st.markdown("""
        <div class="fs-channel-card">
          <span class="fs-channel-badge badge-text">≡ƒÆ¼ Channel 03 ΓÇö Text</span>
          <div class="fs-channel-title">SMS, Email &amp; Chat</div>
          <div class="fs-channel-desc">Paste suspicious messages for NLP-based phishing and social engineering detection</div>
          <div class="fs-channel-divider"></div>
        </div>
        """, unsafe_allow_html=True)
        text_input = st.text_area("Paste suspicious message", height=180, key="text_input",
            placeholder="Paste SMS, email body, chat message...\n\nExample:\n'Dear customer, your account has been suspended. Click here to verify your OTP immediately.'",
            help="Supports SMS, email, WhatsApp, chat.")
        if text_input.strip():
            st.caption(f"≡ƒô¥ {len(text_input.split())} words ┬╖ {len(text_input)} chars")

    return audio_file, image_file, text_input


def render_analyze_button() -> bool:
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([3, 2, 3])
    with col_c:
        return st.button("≡ƒöì  ANALYZE THREAT", use_container_width=True, type="primary")


def render_analysis_progress(audio_file, image_file, text_input: str):
    steps = [
        ("≡ƒÄÖ  Scanning audio channelΓÇª",  lambda: analyze_audio(audio_file)   if audio_file  else analyze_audio(None)),
        ("≡ƒû╝   Scanning image/doc channelΓÇª", lambda: analyze_image(image_file) if image_file else analyze_image(None)),
        ("≡ƒÆ¼  Scanning text channelΓÇª",   lambda: analyze_text(text_input)    if text_input.strip() else analyze_text("")),
        ("≡ƒºá  Aggregating intelligenceΓÇª", None),
        ("Γ£à  Complete",                  None),
    ]
    bar     = st.progress(0)
    status  = st.empty()
    results = []
    total   = len(steps)

    for i, (label, fn) in enumerate(steps):
        status.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;font-size:0.84rem;'
            f'color:#94A3B8;padding:4px 0">'
            f'<span style="width:16px;height:16px;border:2px solid #1A2332;border-top-color:#4F8CFF;'
            f'border-radius:50%;animation:spin 0.8s linear infinite;display:inline-block;flex-shrink:0"></span>'
            f'{label}</div>',
            unsafe_allow_html=True
        )
        bar.progress(int((i / total) * 100))
        if fn:
            results.append(fn())
        else:
            time.sleep(0.3)

    bar.progress(100)
    status.empty()

    audio_res = results[0] if len(results) > 0 else analyze_audio(None)
    image_res = results[1] if len(results) > 1 else analyze_image(None)
    text_res  = results[2] if len(results) > 2 else analyze_text("")

    result = aggregate_results(audio_res, image_res, text_res)
    result["webhook_delivery"] = post_media_to_agent_builder(audio_file, image_file, text_input)
    return result


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  RESULTS RENDERING
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def render_score_panel(result: dict):
    score      = result["composite_score"]
    risk_class = result["risk_class"]
    risk_level = result["risk_level"]
    case_id    = result["case_id"]
    timestamp  = result["timestamp"]
    color      = _score_color(score)

    r    = 52
    circ = 2 * 3.14159 * r
    dash = circ * (score / 100)
    gap  = circ - dash
    off  = circ * 0.25

    risk_styles = {
        "critical": ("rgba(239,68,68,0.12)",   "rgba(239,68,68,0.3)",   "#EF4444"),
        "high":     ("rgba(245,158,11,0.12)",  "rgba(245,158,11,0.3)",  "#F59E0B"),
        "medium":   ("rgba(251,191,36,0.1)",   "rgba(251,191,36,0.25)","#FBBF24"),
        "low":      ("rgba(34,197,94,0.12)",   "rgba(34,197,94,0.3)",   "#22C55E"),
    }
    badge_bg, badge_border, badge_color = risk_styles[risk_class]

    _html(f"""
    <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);border-radius:20px;
                padding:1.8rem 1.4rem;text-align:center;position:relative;overflow:hidden;
                animation:fadeUp 0.4s ease both">
      <div style="position:absolute;top:0;left:0;right:0;bottom:0;
                  background:radial-gradient(circle at 50% 0%,rgba(79,140,255,0.07) 0%,transparent 65%);
                  pointer-events:none"></div>
      <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;
                  text-transform:uppercase;color:#475569;margin-bottom:1.2rem">THREAT SCORE</div>
      <div style="position:relative;width:160px;height:160px;margin:0 auto 1.4rem">
        <svg viewBox="0 0 120 120" width="160" height="160" style="display:block">
          <circle cx="60" cy="60" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
          <circle cx="60" cy="60" r="{r}" fill="none" stroke="{color}" stroke-width="10"
            stroke-dasharray="{dash:.2f} {gap:.2f}" stroke-dashoffset="{off:.2f}"
            stroke-linecap="round"
            style="filter:drop-shadow(0 0 8px {color}88);transition:stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)"/>
          <text x="60" y="52" text-anchor="middle"
            font-family="Space Grotesk,sans-serif" font-size="30" font-weight="700" fill="{color}">{score}</text>
          <text x="60" y="68" text-anchor="middle"
            font-family="Plus Jakarta Sans,sans-serif" font-size="9" font-weight="600"
            fill="#94A3B8" letter-spacing="1">FRAUD PROB.</text>
        </svg>
      </div>
      <div style="text-align:center;margin-bottom:1.2rem">
        <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 20px;
                     border-radius:10px;font-family:'Space Grotesk',sans-serif;font-size:0.95rem;
                     font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
                     background:{badge_bg};border:1px solid {badge_border};color:{badge_color}">
          {risk_level} RISK
        </span>
      </div>
      <div style="background:#1A2332;border:1px solid rgba(255,255,255,0.06);
                  border-radius:10px;padding:10px 14px;text-align:left">
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;
                    font-weight:500;color:#4F8CFF;margin-bottom:3px">{case_id}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#475569">{timestamp}</div>
      </div>
    </div>
    """, height=430)


def render_threat_meta(result: dict):
    risk_class = result["risk_class"]
    color      = _score_color(result["composite_score"])

    action_styles = {
        "critical": ("rgba(239,68,68,0.1)",   "rgba(239,68,68,0.25)",   "#EF4444"),
        "high":     ("rgba(245,158,11,0.1)",  "rgba(245,158,11,0.25)",  "#F59E0B"),
        "medium":   ("rgba(251,191,36,0.08)", "rgba(251,191,36,0.2)",   "#FBBF24"),
        "low":      ("rgba(34,197,94,0.1)",   "rgba(34,197,94,0.25)",   "#22C55E"),
    }
    a_bg, a_border, a_color = action_styles[risk_class]

    channels = [
        ("≡ƒÄÖ Audio", result["audio_score"]),
        ("≡ƒû╝ Image",  result["image_score"]),
        ("≡ƒÆ¼ Text",   result["text_score"]),
    ]
    bars_html = ""
    for ch_label, s in channels:
        if s == 0:
            continue
        bc = _score_color(s)
        bars_html += f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <div style="font-size:0.79rem;font-weight:600;color:#94A3B8;width:78px;flex-shrink:0">{ch_label}</div>
          <div style="flex:1;background:#1A2332;border-radius:999px;height:8px;overflow:hidden">
            <div style="width:{s}%;height:100%;border-radius:999px;
                        background:linear-gradient(90deg,{bc},{bc}bb)"></div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.79rem;
                      font-weight:500;color:{bc};width:36px;text-align:right">{s}%</div>
        </div>"""

    action_text = result["recommended_action"].replace("{","{{").replace("}","}}")
    threat_type = result["threat_type"].replace("{","{{").replace("}","}}")

    _html(f"""
    <div style="display:flex;flex-direction:column;gap:12px;animation:fadeUp 0.4s ease both">
      <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);
                  border-radius:14px;padding:1.1rem 1.3rem">
        <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;
                    text-transform:uppercase;color:#475569;margin-bottom:6px">THREAT CLASSIFICATION</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;
                    font-weight:600;color:#F8FAFC">{threat_type}</div>
      </div>
      <div style="background:{a_bg};border:1px solid {a_border};border-radius:14px;padding:1.1rem 1.3rem">
        <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;
                    text-transform:uppercase;color:{a_color};margin-bottom:6px">RECOMMENDED ACTION</div>
        <div style="font-size:0.9rem;font-weight:500;color:#F8FAFC;line-height:1.55">{action_text}</div>
      </div>
      <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);
                  border-radius:14px;padding:1.1rem 1.3rem">
        <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;
                    text-transform:uppercase;color:#475569;margin-bottom:14px">CHANNEL BREAKDOWN</div>
        {bars_html}
      </div>
    </div>
    """, height=430)


def render_signals(signals: list):
    channel_map = (["Audio"] * 4 + ["Image"] * 4 + ["Text"] * 4) * 3
    tag_styles  = {
        "Audio": ("#A78BFA", "rgba(124,58,237,0.15)", "rgba(124,58,237,0.3)"),
        "Image": ("#22D3EE", "rgba(6,182,212,0.12)",  "rgba(6,182,212,0.25)"),
        "Text":  ("#4F8CFF", "rgba(79,140,255,0.12)", "rgba(79,140,255,0.25)"),
    }

    rows = ""
    for i, sig in enumerate(signals, 1):
        ch              = channel_map[min(i-1, len(channel_map)-1)]
        dot_color, tag_bg, tag_border = tag_styles[ch]
        ts = datetime.utcnow().strftime("%H:%M:%S.") + f"{random.randint(0,999):03d}"
        line_html = (f'<div style="width:1px;flex:1;min-height:14px;'
                     f'background:linear-gradient(to bottom,{dot_color}44,transparent)"></div>'
                     if i < len(signals) else "")
        rows += f"""
        <div style="display:flex;align-items:flex-start;gap:12px;padding:9px 6px;
                    border-bottom:{'1px solid rgba(255,255,255,0.04)' if i < len(signals) else 'none'};
                    border-radius:6px">
          <div style="display:flex;flex-direction:column;align-items:center;padding-top:4px">
            <div style="width:9px;height:9px;border-radius:50%;border:2px solid {dot_color};
                        background:{dot_color}22;flex-shrink:0"></div>
            {line_html}
          </div>
          <div style="flex:1">
            <div style="font-size:0.84rem;color:#F8FAFC;font-weight:500;line-height:1.4">{sig}</div>
            <div style="display:flex;align-items:center;gap:8px;margin-top:3px;flex-wrap:wrap">
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.67rem;color:#475569">UTC {ts}</span>
              <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;
                           padding:2px 7px;border-radius:4px;background:{tag_bg};
                           color:{dot_color};border:1px solid {tag_border}">{ch}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.63rem;color:#475569">#{i:02d}</span>
            </div>
          </div>
        </div>"""

    _html(f"""
    <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);
                border-radius:14px;padding:1.2rem 1.4rem;animation:fadeUp 0.4s ease both">
      <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;
                  color:#475569;margin-bottom:1rem">≡ƒöÄ DETECTED SIGNALS ({len(signals)})</div>
      {rows}
    </div>
    """, height=max(200, len(signals) * 75 + 60))


def render_integration_panel(result: dict):
    integrations = [
        ("Agent Builder",     "Orchestration layer"),
        ("Gemini 2.0 Flash",  "Multimodal AI"),
        ("MongoDB MCP",       "Case storage"),
        ("Elasticsearch MCP", "Threat intel search"),
        ("Speech-to-Text",    "Audio transcription"),
        ("Vertex AI Vision",  "Document analysis"),
    ]
    int_rows = "".join(f"""
    <div style="display:flex;align-items:center;gap:12px;padding:9px 0;
                border-bottom:{'1px solid rgba(255,255,255,0.04)' if i < len(integrations)-1 else 'none'}">
      <div style="font-weight:600;font-size:0.82rem;color:#F8FAFC;width:165px;flex-shrink:0">{name}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.64rem;padding:3px 8px;border-radius:4px;
                  background:rgba(245,158,11,0.12);color:#F59E0B;border:1px solid rgba(245,158,11,0.2);flex-shrink:0">PENDING</div>
      <div style="font-size:0.77rem;color:#475569">{desc}</div>
    </div>""" for i, (name, desc) in enumerate(integrations))

    meta_items = {
        "Engine":  "FraudShield v2.0",
        "Model":   "Gemini 2.0 Flash",
        "DB":      "MongoDB MCP",
        "Search":  "Elasticsearch MCP",
        "Signals": str(len(result["all_signals"])),
    }
    meta_rows = "".join(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;
                border-bottom:{'1px solid rgba(255,255,255,0.04)' if i < len(meta_items)-1 else 'none'}">
      <span style="font-size:0.77rem;color:#475569;font-weight:500">{k}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.77rem;color:#4F8CFF;font-weight:500">{v}</span>
    </div>""" for i, (k, v) in enumerate(meta_items.items()))

    _html(f"""
    <div style="display:flex;flex-direction:column;gap:12px;animation:fadeUp 0.4s ease both">
      <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:1.2rem 1.4rem">
        <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:#475569;margin-bottom:12px">
          ≡ƒöî INTEGRATION STATUS
        </div>
        {int_rows}
      </div>
      <div style="background:#111827;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:1.2rem 1.4rem">
        <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;color:#475569;margin-bottom:12px">
          CASE METADATA
        </div>
        {meta_rows}
      </div>
    </div>
    """, height=560)


def render_results(result: dict):
    if not result:
        return

    render_section_header("ΓÜí", "Threat Analysis Report",
                           f"Case {result['case_id']} ┬╖ Generated {result['timestamp']}")

    col_score, col_meta = st.columns([1, 2], gap="large")
    with col_score:
        render_score_panel(result)
    with col_meta:
        render_threat_meta(result)

    webhook = result.get("webhook_delivery", {})
    if webhook:
        st.markdown('<div class="fs-webhook-label">≡ƒöî Agent Builder Webhook</div>', unsafe_allow_html=True)
        if webhook["status"] == "success":
            st.success(webhook["message"])
        elif webhook["status"] == "skipped":
            st.info(webhook["message"])
        else:
            st.warning(webhook["message"])
        if webhook.get("status_code"):
            st.caption(f"HTTP {webhook['status_code']}")
        if webhook.get("response_body"):
            st.code(webhook["response_body"], language="text")

    st.markdown("<br>", unsafe_allow_html=True)

    col_sig, col_int = st.columns([3, 2], gap="large")
    with col_sig:
        render_signals(result["all_signals"])
    with col_int:
        render_integration_panel(result)


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  SIDEBAR
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem;padding-top:0.5rem">
          <div style="width:32px;height:32px;flex-shrink:0">{LOGO_SVG}</div>
          <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                        font-size:1rem;color:#F8FAFC">FraudShield</div>
            <div style="font-size:0.68rem;color:#475569;letter-spacing:0.04em">v2.1.0 Enterprise</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**System Status**")
        st.markdown("""
        <div style="display:flex;align-items:center;gap:8px;margin:6px 0">
          <span style="width:7px;height:7px;border-radius:50%;background:#22C55E;
                       box-shadow:0 0 6px #22C55E;display:inline-block"></span>
          <span style="font-size:0.82rem;color:#94A3B8">All systems operational</span>
        </div>
        <div style="font-size:0.76rem;color:#475569;margin-top:3px">Mode: Simulation</div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**ΓÜÖ∩╕Å Configuration**")
        threshold = st.slider("Alert Threshold (%)", 0, 100, 65)
        st.caption(f"Threats ΓëÑ {threshold}% trigger alerts.")

        st.markdown("---")
        st.markdown("**≡ƒôû About**")
        st.caption(
            "FraudShield detects fraud signals across audio, image, PDF, and text "
            "channels using multi-modal AI. Built for Google Cloud hackathon."
        )
        st.markdown("---")
        st.caption("┬⌐ 2025 Anti-Fraud Team ┬╖ FraudShield Enterprise")


# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
#  MAIN
# ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ

def main():
    render_sidebar()
    render_logo()
    render_nav()

    st.markdown("<br>", unsafe_allow_html=True)
    render_kpi_bar()

    audio_file, image_file, text_input = render_input_sections()
    clicked = render_analyze_button()

    if clicked:
        if not validate_inputs(audio_file, image_file, text_input):
            st.error("ΓÜá∩╕Å Please provide at least one input (audio, image/PDF, or text) before analysing.")
        else:
            st.info("ΓÜí Omnichannel analysis in progress ΓÇö scanning all submitted channelsΓÇª")
            with st.spinner(""):
                result = render_analysis_progress(audio_file, image_file, text_input)
            st.success("Γ£à Analysis complete ΓÇö threat report generated below.")
            render_results(result)


if __name__ == "__main__":
    main()
