from __future__ import annotations

import html
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from reproguard.agents import AuditOrchestrator
from reproguard.reports import report_to_json, report_to_markdown
from reproguard.viz import evidence_graph_dot

APP_VERSION = "0.3.0"


# -----------------------------
# Helpers
# -----------------------------
def evidence_box(text: str | None) -> None:
    if not text:
        st.markdown(
            '<div class="rg-empty-mini">No explicit evidence detected by the current baseline rule set.</div>',
            unsafe_allow_html=True,
        )
        return
    safe = html.escape(text.strip())
    st.markdown(
        f"""
        <div class="rg-evidence">
            <div class="rg-evidence-label">Evidence captured from paper</div>
            <div>{safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def coverage_label(score: float) -> tuple[str, str]:
    if score >= 90:
        return "Very high coverage", "Most baseline reproducibility signals were detected."
    if score >= 75:
        return "High coverage", "Most baseline signals were detected; a few items still need review."
    if score >= 50:
        return "Moderate coverage", "Several important details were found, but meaningful gaps remain."
    return "Limited coverage", "Many reproducibility signals were not detected and require review."


def action_text(item) -> str:
    lookup = {
        "problem": "State the research objective, hypothesis, or research question explicitly.",
        "dataset": "Identify the dataset/data source and provide a clear access path.",
        "split": "Document train/validation/test splitting or cross-validation.",
        "preprocessing": "Describe preprocessing and data-transformation steps.",
        "model": "Specify the model or architecture clearly.",
        "hyperparameters": "Report the important training hyperparameters.",
        "seed": "Report random seeds or deterministic settings.",
        "metrics": "Define the evaluation metrics used.",
        "baselines": "Add a baseline, comparator, or ablation where appropriate.",
        "code": "Provide an implementation/code availability statement.",
        "hardware": "Document software and compute environment details.",
        "statistics": "Report uncertainty, repeated runs, or statistical testing where appropriate.",
    }
    return lookup.get(item.key, f"Review the missing documentation for: {item.label}.")


def chip(text: str, tone: str = "neutral") -> str:
    return f'<span class="rg-chip rg-chip-{tone}">{html.escape(text)}</span>'


def kpi_card(label: str, value: str, detail: str = "", accent: str = "cyan") -> None:
    st.markdown(
        f"""
        <div class="rg-kpi rg-kpi-{accent}">
            <div class="rg-kpi-top"><span class="rg-kpi-dot"></span>{html.escape(label)}</div>
            <div class="rg-kpi-value">{html.escape(value)}</div>
            <div class="rg-kpi-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str | None = None, eyebrow: str | None = None) -> None:
    eyebrow_html = f'<div class="rg-eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""
    subtitle_html = f'<div class="rg-section-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="rg-section-head">
            {eyebrow_html}
            <div class="rg-section-title">{html.escape(title)}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def finding_card(title: str, copy: str, tone: str = "neutral") -> None:
    st.markdown(
        f"""
        <div class="rg-finding rg-finding-{tone}">
            <div class="rg-finding-orb"></div>
            <div>
                <div class="rg-finding-title">{html.escape(title)}</div>
                <div class="rg-finding-copy">{html.escape(copy)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Page setup
# -----------------------------
icon_path = ROOT / "assets" / "reproguard.ico"
st.set_page_config(
    page_title="ReproGuard AI",
    page_icon=str(icon_path) if icon_path.exists() else "🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Visual system
# -----------------------------
st.markdown(
    """
    <style>
    :root {
        --bg-0: #050713;
        --bg-1: #080d1b;
        --bg-2: #0b1224;
        --panel: rgba(13, 21, 39, .74);
        --panel-strong: rgba(16, 26, 47, .92);
        --panel-soft: rgba(15, 25, 44, .58);
        --border: rgba(146, 173, 214, .16);
        --border-strong: rgba(92, 225, 255, .28);
        --text: #f4f8ff;
        --muted: #91a1bb;
        --muted-2: #6f809d;
        --cyan: #5ce1ff;
        --cyan-2: #28b8f5;
        --mint: #69f2c1;
        --violet: #a68cff;
        --amber: #ffc96b;
        --red: #ff7b8b;
        --good: #58e3a1;
    }

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    body { background: var(--bg-0); }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 12% 12%, rgba(34, 210, 238, .10), transparent 28%),
            radial-gradient(circle at 86% 18%, rgba(166, 140, 255, .11), transparent 25%),
            radial-gradient(circle at 58% 90%, rgba(70, 243, 191, .07), transparent 25%),
            linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 46%, #060915 100%);
        color: var(--text);
        overflow-x: hidden;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background-image:
            linear-gradient(rgba(130, 162, 210, .035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(130, 162, 210, .035) 1px, transparent 1px);
        background-size: 42px 42px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,.72), transparent 88%);
    }

    [data-testid="stAppViewContainer"]::after {
        content: "";
        position: fixed;
        top: -260px;
        left: 14vw;
        width: 70vw;
        height: 420px;
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
        background: radial-gradient(ellipse, rgba(67, 222, 255, .12), rgba(149, 99, 255, .055) 42%, transparent 72%);
        filter: blur(44px);
        animation: rg-aurora 11s ease-in-out infinite alternate;
    }

    @keyframes rg-aurora {
        0% { transform: translate3d(-4%, 0, 0) scale(1); opacity: .65; }
        50% { transform: translate3d(4%, 5%, 0) scale(1.08); opacity: .95; }
        100% { transform: translate3d(0, -3%, 0) scale(.98); opacity: .72; }
    }

    @keyframes rg-float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }

    @keyframes rg-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(92,225,255,.25), 0 0 18px rgba(92,225,255,.24); }
        50% { box-shadow: 0 0 0 7px rgba(92,225,255,0), 0 0 28px rgba(92,225,255,.44); }
    }

    @keyframes rg-scan {
        0% { transform: translateX(-35%); opacity: 0; }
        15% { opacity: 1; }
        85% { opacity: .65; }
        100% { transform: translateX(135%); opacity: 0; }
    }

    @keyframes rg-rise {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }

    [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer,
    [data-testid="collapsedControl"], [data-testid="stSidebar"] {
        display: none !important;
    }

    .block-container {
        position: relative;
        z-index: 2;
        padding-top: 1.15rem;
        padding-bottom: 4rem;
        max-width: 1500px;
    }

    .rg-ambient {
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }
    .rg-orb {
        position: absolute;
        border-radius: 999px;
        filter: blur(1px);
        opacity: .42;
        animation: rg-float 7s ease-in-out infinite;
    }
    .rg-orb-1 { width: 7px; height: 7px; background: var(--cyan); left: 7%; top: 27%; box-shadow: 0 0 28px 8px rgba(92,225,255,.33); }
    .rg-orb-2 { width: 5px; height: 5px; background: var(--violet); right: 11%; top: 42%; animation-delay: -2s; box-shadow: 0 0 30px 9px rgba(166,140,255,.34); }
    .rg-orb-3 { width: 6px; height: 6px; background: var(--mint); left: 29%; bottom: 13%; animation-delay: -4s; box-shadow: 0 0 32px 8px rgba(105,242,193,.28); }

    .rg-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: .88rem 1rem;
        margin-bottom: 1.35rem;
        border: 1px solid var(--border);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(17, 28, 50, .80), rgba(10, 17, 33, .76));
        backdrop-filter: blur(18px) saturate(125%);
        -webkit-backdrop-filter: blur(18px) saturate(125%);
        box-shadow: 0 18px 70px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.04);
        position: sticky;
        top: .7rem;
        z-index: 8;
        animation: rg-rise .55s ease-out both;
    }

    .rg-brand { display:flex; align-items:center; gap:.72rem; min-width: 0; }
    .rg-brand-mark {
        position: relative;
        width: 42px;
        height: 42px;
        border-radius: 13px;
        display:grid;
        place-items:center;
        color:#041018;
        font-weight: 950;
        letter-spacing: -.04em;
        background: linear-gradient(135deg, var(--cyan), var(--mint));
        box-shadow: 0 0 0 1px rgba(255,255,255,.18), 0 0 36px rgba(92,225,255,.18);
        overflow:hidden;
    }
    .rg-brand-mark::after {
        content:"";
        position:absolute;
        inset:-1px;
        background: linear-gradient(110deg, transparent 25%, rgba(255,255,255,.7) 45%, transparent 64%);
        transform: translateX(-135%);
        animation: rg-scan 5.5s ease-in-out infinite;
    }
    .rg-brand-name { font-size:1.06rem; font-weight:850; letter-spacing:-.02em; color:var(--text); }
    .rg-brand-sub { font-size:.72rem; color:var(--muted); margin-top:.06rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .rg-nav-right { display:flex; align-items:center; gap:.55rem; }
    .rg-live {
        display:inline-flex; align-items:center; gap:.4rem;
        padding:.38rem .62rem; border-radius:999px;
        border:1px solid rgba(105,242,193,.20); background:rgba(105,242,193,.07);
        color:#a7f7d8; font-size:.71rem; font-weight:750;
    }
    .rg-live-dot { width:7px; height:7px; border-radius:50%; background:var(--mint); animation: rg-pulse 1.8s ease-out infinite; }
    .rg-version { color:var(--muted); font-size:.72rem; padding:.35rem .58rem; border:1px solid var(--border); border-radius:999px; }

    .rg-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(117, 183, 230, .16);
        border-radius: 28px;
        padding: clamp(1.7rem, 3vw, 3.3rem);
        min-height: 430px;
        background:
            linear-gradient(145deg, rgba(15, 27, 49, .88), rgba(8, 15, 31, .78)),
            radial-gradient(circle at 82% 20%, rgba(105,242,193,.12), transparent 30%),
            radial-gradient(circle at 65% 80%, rgba(92,225,255,.09), transparent 25%);
        box-shadow: 0 30px 110px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.04);
        animation: rg-rise .7s .06s ease-out both;
    }
    .rg-hero::before {
        content:"";
        position:absolute;
        width:480px;
        height:480px;
        border-radius:50%;
        right:-120px;
        top:-160px;
        border:1px solid rgba(92,225,255,.12);
        box-shadow: 0 0 0 60px rgba(92,225,255,.018), 0 0 0 120px rgba(166,140,255,.015);
    }
    .rg-hero::after {
        content:"";
        position:absolute;
        height:1px;
        width:58%;
        top:0;
        left:8%;
        background:linear-gradient(90deg, transparent, rgba(92,225,255,.75), rgba(166,140,255,.45), transparent);
        box-shadow:0 0 22px rgba(92,225,255,.45);
        animation: rg-scan 6.8s linear infinite;
    }
    .rg-hero-grid {
        display:grid;
        grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr);
        gap:clamp(1.4rem,3vw,3rem);
        align-items:center;
        position:relative;
        z-index:2;
    }
    .rg-kicker { font-size:.75rem; text-transform:uppercase; letter-spacing:.16em; font-weight:800; color:#8ce9ff; margin-bottom:.72rem; }
    .rg-title { margin:0; font-size:clamp(2.35rem,4.4vw,4.7rem); line-height:.98; letter-spacing:-.055em; font-weight:900; color:var(--text); max-width:950px; }
    .rg-title .glow { color:#79eaff; text-shadow:0 0 28px rgba(92,225,255,.18); }
    .rg-copy { margin-top:1.1rem; max-width:760px; color:#9fb0c9; line-height:1.72; font-size:clamp(.96rem,1.3vw,1.08rem); }
    .rg-pill-row { display:flex; flex-wrap:wrap; gap:.55rem; margin-top:1.25rem; }
    .rg-tech-pill { padding:.42rem .62rem; border:1px solid var(--border); border-radius:999px; background:rgba(255,255,255,.025); color:#b8c7dc; font-size:.72rem; }

    .rg-scope-orbit {
        position:relative;
        min-height:300px;
        display:grid;
        place-items:center;
    }
    .rg-core {
        position:relative;
        width:154px; height:154px; border-radius:50%;
        display:grid; place-items:center; text-align:center;
        border:1px solid rgba(92,225,255,.28);
        background:radial-gradient(circle at 35% 28%, rgba(92,225,255,.16), rgba(12,23,42,.74) 62%);
        box-shadow:0 0 60px rgba(92,225,255,.12), inset 0 0 32px rgba(92,225,255,.06);
        animation:rg-float 6s ease-in-out infinite;
    }
    .rg-core::before, .rg-core::after {
        content:""; position:absolute; border-radius:50%; inset:-38px; border:1px solid rgba(116,157,216,.12);
    }
    .rg-core::after { inset:-78px; border-style:dashed; animation:spin 20s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    .rg-core strong { display:block; color:var(--text); font-size:1.05rem; }
    .rg-core span { display:block; color:var(--muted); font-size:.72rem; margin-top:.25rem; }
    .rg-orbit-label { position:absolute; padding:.4rem .56rem; border-radius:10px; border:1px solid var(--border); background:rgba(8,15,30,.78); color:#c8d5e8; font-size:.7rem; box-shadow:0 10px 35px rgba(0,0,0,.22); }
    .rg-orbit-1 { top:20px; left:12%; }
    .rg-orbit-2 { top:44px; right:5%; }
    .rg-orbit-3 { bottom:42px; left:4%; }
    .rg-orbit-4 { bottom:25px; right:9%; }

    .rg-intake-shell {
        margin-top:1rem;
        padding:1rem;
        border-radius:20px;
        border:1px solid var(--border);
        background:rgba(8, 15, 30, .70);
        backdrop-filter:blur(16px);
        box-shadow:0 18px 60px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.03);
        animation: rg-rise .72s .12s ease-out both;
    }
    .rg-intake-label { font-size:.72rem; color:#7f90ab; text-transform:uppercase; letter-spacing:.1em; font-weight:800; }
    .rg-intake-title { margin-top:.25rem; font-size:1.04rem; color:var(--text); font-weight:800; }
    .rg-intake-copy { margin-top:.2rem; color:var(--muted); font-size:.82rem; line-height:1.5; }

    .rg-privacy {
        margin-top:.8rem;
        display:flex;
        align-items:flex-start;
        gap:.55rem;
        padding:.72rem .82rem;
        border:1px solid rgba(105,242,193,.12);
        border-radius:12px;
        background:rgba(105,242,193,.045);
        color:#94b6ae;
        font-size:.75rem;
        line-height:1.48;
    }

    .rg-report-shell {
        position:relative;
        overflow:hidden;
        border:1px solid var(--border);
        border-radius:24px;
        background:linear-gradient(145deg,rgba(15,26,47,.88),rgba(8,14,28,.80));
        padding:1.15rem 1.2rem;
        box-shadow:0 24px 90px rgba(0,0,0,.26), inset 0 1px 0 rgba(255,255,255,.04);
        animation:rg-rise .55s ease-out both;
    }
    .rg-report-shell::after {
        content:"";
        position:absolute;
        left:-10%; top:0; width:45%; height:1px;
        background:linear-gradient(90deg,transparent,var(--cyan),transparent);
        box-shadow:0 0 20px rgba(92,225,255,.52);
        animation:rg-scan 5.8s linear infinite;
    }
    .rg-report-top { display:flex; justify-content:space-between; gap:1rem; align-items:flex-start; position:relative; z-index:2; }
    .rg-report-title { font-size:clamp(1.35rem,2vw,2.05rem); line-height:1.18; color:var(--text); font-weight:850; letter-spacing:-.025em; margin-top:.55rem; }
    .rg-report-meta { color:var(--muted); font-size:.78rem; margin-top:.4rem; }

    .rg-chip { display:inline-flex; align-items:center; gap:.32rem; border-radius:999px; padding:.28rem .52rem; font-size:.67rem; font-weight:800; border:1px solid transparent; }
    .rg-chip-success { background:rgba(88,227,161,.08); color:#8df0bd; border-color:rgba(88,227,161,.18); }
    .rg-chip-warning { background:rgba(255,201,107,.08); color:#ffd58c; border-color:rgba(255,201,107,.19); }
    .rg-chip-neutral { background:rgba(255,255,255,.035); color:#aebcd0; border-color:var(--border); }
    .rg-chip-info { background:rgba(92,225,255,.07); color:#85eaff; border-color:rgba(92,225,255,.18); }

    .rg-score-wrap {
        position:relative;
        min-height:190px;
        display:grid;
        place-items:center;
        border:1px solid var(--border);
        border-radius:20px;
        background:rgba(8,14,28,.58);
        overflow:hidden;
    }
    .rg-score-wrap::before {
        content:"";
        position:absolute;
        width:180px; height:180px; border-radius:50%;
        background:radial-gradient(circle, rgba(92,225,255,.09), transparent 65%);
        filter:blur(4px);
    }
    .rg-score-ring {
        --score: 0;
        position:relative;
        width:148px; height:148px; border-radius:50%;
        display:grid; place-items:center;
        background:conic-gradient(var(--cyan) calc(var(--score) * 1%), rgba(122,146,180,.12) 0);
        box-shadow:0 0 34px rgba(92,225,255,.10);
    }
    .rg-score-ring::before {
        content:""; position:absolute; inset:9px; border-radius:50%;
        background:#0a1222;
        box-shadow:inset 0 0 30px rgba(92,225,255,.055);
    }
    .rg-score-inner { position:relative; z-index:2; text-align:center; }
    .rg-score-value { font-size:2.2rem; line-height:1; font-weight:900; letter-spacing:-.055em; color:var(--text); }
    .rg-score-label { font-size:.6rem; margin-top:.35rem; color:#7f91ad; text-transform:uppercase; letter-spacing:.09em; font-weight:800; }
    .rg-score-caption { position:absolute; bottom:14px; left:14px; right:14px; text-align:center; color:#8da0bd; font-size:.7rem; }

    .rg-kpi {
        position:relative;
        overflow:hidden;
        min-height:122px;
        border:1px solid var(--border);
        border-radius:18px;
        background:linear-gradient(180deg,rgba(15,25,44,.75),rgba(9,16,31,.70));
        padding:.92rem 1rem;
        transition:transform .22s ease, border-color .22s ease, box-shadow .22s ease;
    }
    .rg-kpi:hover { transform:translateY(-3px); border-color:rgba(92,225,255,.26); box-shadow:0 16px 38px rgba(0,0,0,.18); }
    .rg-kpi::after { content:""; position:absolute; top:0; left:0; width:100%; height:1px; background:linear-gradient(90deg,transparent,rgba(92,225,255,.36),transparent); opacity:.55; }
    .rg-kpi-top { display:flex; align-items:center; gap:.42rem; font-size:.65rem; text-transform:uppercase; letter-spacing:.08em; color:#7f91ad; font-weight:850; }
    .rg-kpi-dot { width:6px; height:6px; border-radius:50%; background:var(--cyan); box-shadow:0 0 16px rgba(92,225,255,.75); }
    .rg-kpi-violet .rg-kpi-dot { background:var(--violet); box-shadow:0 0 16px rgba(166,140,255,.65); }
    .rg-kpi-mint .rg-kpi-dot { background:var(--mint); box-shadow:0 0 16px rgba(105,242,193,.65); }
    .rg-kpi-amber .rg-kpi-dot { background:var(--amber); box-shadow:0 0 16px rgba(255,201,107,.55); }
    .rg-kpi-value { color:var(--text); font-size:1.65rem; line-height:1.1; font-weight:900; letter-spacing:-.04em; margin-top:.58rem; }
    .rg-kpi-detail { color:#8192ad; font-size:.72rem; line-height:1.42; margin-top:.3rem; }

    .rg-section-head { margin-top:.1rem; margin-bottom:.72rem; }
    .rg-eyebrow { color:#6f839f; text-transform:uppercase; letter-spacing:.11em; font-size:.63rem; font-weight:850; margin-bottom:.25rem; }
    .rg-section-title { font-size:1.12rem; color:var(--text); font-weight:850; letter-spacing:-.02em; }
    .rg-section-subtitle { color:var(--muted); font-size:.78rem; line-height:1.5; margin-top:.2rem; max-width:860px; }

    .rg-finding {
        position:relative;
        display:grid;
        grid-template-columns:10px 1fr;
        gap:.7rem;
        padding:.82rem .9rem;
        margin-bottom:.58rem;
        border:1px solid var(--border);
        border-radius:14px;
        background:rgba(11,20,37,.68);
        transition:transform .18s ease,border-color .18s ease,background .18s ease;
    }
    .rg-finding:hover { transform:translateX(3px); border-color:rgba(92,225,255,.22); background:rgba(13,24,43,.78); }
    .rg-finding-orb { width:8px; height:8px; margin-top:.25rem; border-radius:50%; background:#6d7f99; box-shadow:0 0 16px rgba(109,127,153,.2); }
    .rg-finding-warning .rg-finding-orb { background:var(--amber); box-shadow:0 0 18px rgba(255,201,107,.35); }
    .rg-finding-success .rg-finding-orb { background:var(--mint); box-shadow:0 0 18px rgba(105,242,193,.35); }
    .rg-finding-title { color:#e8f1ff; font-size:.84rem; font-weight:800; }
    .rg-finding-copy { color:#8799b5; font-size:.75rem; line-height:1.48; margin-top:.12rem; }

    .rg-evidence {
        margin-top:.58rem;
        padding:.78rem .85rem;
        border:1px solid rgba(113,143,186,.14);
        border-left:2px solid rgba(92,225,255,.36);
        border-radius:12px;
        background:#070d19;
        color:#b7c5d9;
        font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
        font-size:.74rem; line-height:1.6;
        white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word;
    }
    .rg-evidence-label { color:#68dff8; font-family:Inter,ui-sans-serif,sans-serif; font-size:.61rem; font-weight:850; text-transform:uppercase; letter-spacing:.09em; margin-bottom:.35rem; }
    .rg-empty, .rg-empty-mini { border:1px dashed rgba(136,163,201,.18); border-radius:14px; background:rgba(255,255,255,.018); color:#7589a7; padding:1rem; font-size:.78rem; }
    .rg-empty-mini { padding:.72rem .8rem; margin-top:.55rem; }

    .rg-info-strip {
        padding:.72rem .82rem;
        border:1px solid rgba(92,225,255,.12);
        border-radius:12px;
        background:linear-gradient(90deg,rgba(92,225,255,.055),rgba(166,140,255,.035));
        color:#a0b2ca; font-size:.75rem; line-height:1.5;
    }

    div[data-testid="stFileUploader"] section {
        border:1px dashed rgba(92,225,255,.30) !important;
        background:linear-gradient(180deg,rgba(13,24,43,.72),rgba(9,17,32,.66)) !important;
        border-radius:16px !important;
        min-height:126px;
        transition:border-color .22s ease,box-shadow .22s ease,transform .22s ease;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color:rgba(92,225,255,.65) !important;
        box-shadow:0 0 36px rgba(92,225,255,.08);
        transform:translateY(-1px);
    }
    div[data-testid="stFileUploader"] * { color:#afbdd0 !important; }

    .stButton > button, .stDownloadButton > button {
        min-height:42px;
        border-radius:12px !important;
        border:1px solid rgba(117,151,197,.20) !important;
        background:linear-gradient(180deg,rgba(18,31,54,.92),rgba(10,19,36,.92)) !important;
        color:#dfeaff !important;
        font-weight:780 !important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.03);
        transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform:translateY(-2px);
        border-color:rgba(92,225,255,.42) !important;
        box-shadow:0 12px 28px rgba(0,0,0,.20),0 0 26px rgba(92,225,255,.06) !important;
        color:#fff !important;
    }
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#36d9ff,#4adbb9) !important;
        color:#041017 !important;
        border-color:transparent !important;
        box-shadow:0 10px 30px rgba(54,217,255,.14) !important;
    }
    .stButton > button[kind="primary"]:hover { box-shadow:0 14px 34px rgba(54,217,255,.22) !important; }

    [data-testid="stPopover"] button { border-radius:12px !important; }
    [data-testid="stPopoverBody"] {
        background:#0a1222 !important;
        border:1px solid var(--border) !important;
        color:var(--text) !important;
        box-shadow:0 24px 80px rgba(0,0,0,.45) !important;
    }

    div[data-baseweb="tab-list"] {
        gap:.25rem;
        border:1px solid var(--border);
        border-radius:14px;
        background:rgba(9,16,31,.62);
        padding:.25rem;
        overflow-x:auto;
    }
    button[data-baseweb="tab"] {
        border-radius:10px !important;
        color:#8497b3 !important;
        font-weight:760 !important;
        padding:.55rem .72rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background:rgba(92,225,255,.08) !important;
        color:#dff8ff !important;
    }
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] p { font-size:.76rem; }

    [data-testid="stDataFrame"] {
        border:1px solid var(--border);
        border-radius:14px;
        overflow:hidden;
        background:#0a1222;
    }

    [data-testid="stExpander"] {
        border:1px solid var(--border) !important;
        border-radius:14px !important;
        background:rgba(10,18,34,.58) !important;
        overflow:hidden;
        margin-bottom:.45rem;
    }
    [data-testid="stExpander"] summary:hover { background:rgba(92,225,255,.035); }

    [data-testid="stMetric"] {
        border:1px solid var(--border);
        border-radius:12px;
        padding:.65rem .72rem;
        background:rgba(8,15,29,.58);
    }

    [data-testid="stProgress"] > div > div > div > div { background:linear-gradient(90deg,var(--cyan),var(--mint)) !important; box-shadow:0 0 18px rgba(92,225,255,.2); }

    .stAlert { border-radius:13px !important; border:1px solid var(--border) !important; background:rgba(11,19,35,.76) !important; color:#aebed3 !important; }
    input { color:var(--text) !important; }
    label, p, h1, h2, h3, h4, h5, h6 { color:inherit; }

    @media (max-width: 980px) {
        .rg-hero-grid { grid-template-columns:1fr; }
        .rg-scope-orbit { min-height:250px; }
        .rg-nav-right .rg-version { display:none; }
    }
    @media (max-width: 700px) {
        .block-container { padding-left:.75rem; padding-right:.75rem; }
        .rg-hero { border-radius:20px; padding:1.35rem; }
        .rg-title { font-size:2.35rem; }
        .rg-nav { top:.35rem; border-radius:14px; }
        .rg-brand-sub { display:none; }
        .rg-live { display:none; }
        .rg-report-top { flex-direction:column; }
    }
    </style>
    <div class="rg-ambient" aria-hidden="true">
      <div class="rg-orb rg-orb-1"></div>
      <div class="rg-orb rg-orb-2"></div>
      <div class="rg-orb rg-orb-3"></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state
# -----------------------------
for key, default in {
    "rg_report": None,
    "rg_file_name": None,
    "rg_is_demo": False,
    "rg_online": True,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# -----------------------------
# Top navigation + settings
# -----------------------------
nav_left, nav_mid, nav_settings = st.columns([4.7, 1.2, 1.1], vertical_alignment="center")
with nav_left:
    st.markdown(
        """
        <div class="rg-nav" style="margin-bottom:0; position:relative; top:auto;">
          <div class="rg-brand">
            <div class="rg-brand-mark">RG</div>
            <div>
              <div class="rg-brand-name">ReproGuard AI</div>
              <div class="rg-brand-sub">Research evidence & reproducibility intelligence</div>
            </div>
          </div>
          <div class="rg-nav-right">
            <div class="rg-live"><span class="rg-live-dot"></span>Engine ready</div>
            <div class="rg-version">v0.3.0 · local-first</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with nav_mid:
    if st.session_state.rg_report is not None:
        if st.button("New audit", use_container_width=True):
            st.session_state.rg_report = None
            st.session_state.rg_file_name = None
            st.session_state.rg_is_demo = False
            st.rerun()
    else:
        st.markdown('<div style="height:42px"></div>', unsafe_allow_html=True)
with nav_settings:
    with st.popover("Audit settings", use_container_width=True):
        st.markdown("#### Verification")
        st.session_state.rg_online = st.toggle(
            "Online verification",
            value=bool(st.session_state.rg_online),
            help="Resolve DOI metadata and inspect public GitHub repositories.",
        )
        contact_email = st.text_input(
            "Contact email (optional)",
            value=os.getenv("REPROGUARD_CONTACT_EMAIL", ""),
            help="Optional polite API identifier for scholarly metadata services.",
        )
        github_token = st.text_input(
            "GitHub token (optional)",
            value=os.getenv("GITHUB_TOKEN", ""),
            type="password",
            help="Improves GitHub API rate limits; never written to reports.",
        )
        st.caption("The PDF is processed locally. Only detected DOI/GitHub identifiers are queried when online verification is enabled.")

online = bool(st.session_state.rg_online)
# Ensure variables exist when popover is closed between reruns.
contact_email = locals().get("contact_email", os.getenv("REPROGUARD_CONTACT_EMAIL", ""))
github_token = locals().get("github_token", os.getenv("GITHUB_TOKEN", ""))

st.write("")


# -----------------------------
# Intake / landing experience
# -----------------------------
if st.session_state.rg_report is None:
    st.markdown(
        """
        <section class="rg-hero">
          <div class="rg-hero-grid">
            <div>
              <div class="rg-kicker">Research integrity · automated evidence audit</div>
              <h1 class="rg-title">Verify the evidence <span class="glow">behind the research.</span></h1>
              <div class="rg-copy">ReproGuard turns a research paper into a traceable audit of citations, methodology, code availability, and reproducibility signals — without pretending to judge whether the science itself is true.</div>
              <div class="rg-pill-row">
                <span class="rg-tech-pill">Citation metadata</span>
                <span class="rg-tech-pill">Method evidence</span>
                <span class="rg-tech-pill">Repository health</span>
                <span class="rg-tech-pill">Claim traceability</span>
                <span class="rg-tech-pill">Local-first parsing</span>
              </div>
            </div>
            <div class="rg-scope-orbit" aria-hidden="true">
              <div class="rg-core"><div><strong>Audit Engine</strong><span>Extract → Verify → Trace</span></div></div>
              <div class="rg-orbit-label rg-orbit-1">Citations</div>
              <div class="rg-orbit-label rg-orbit-2">Methods</div>
              <div class="rg-orbit-label rg-orbit-3">Code</div>
              <div class="rg-orbit-label rg-orbit-4">Evidence</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="rg-intake-shell">
          <div class="rg-intake-label">Start a research audit</div>
          <div class="rg-intake-title">Drop in a paper. ReproGuard will build the evidence map.</div>
          <div class="rg-intake-copy">PDF text is processed on this computer. Optional online checks only resolve identifiers such as DOI and public GitHub URLs.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    upload_col, engine_col = st.columns([1.55, .75], gap="large")
    with upload_col:
        uploaded = st.file_uploader(
            "Research paper PDF",
            type=["pdf"],
            help="Maximum upload size is configured to 100 MB.",
            label_visibility="collapsed",
        )
        a1, a2 = st.columns([1, 1])
        with a1:
            run_upload = st.button(
                "Run evidence audit",
                type="primary",
                use_container_width=True,
                disabled=uploaded is None,
            )
        with a2:
            use_demo = st.button("Explore demo audit", use_container_width=True)

        st.markdown(
            '<div class="rg-privacy"><span style="color:#69f2c1">●</span><div><b style="color:#b8d7cf">Privacy by design.</b> Your PDF remains local. Crossref/OpenAlex/GitHub only receive identifiers that ReproGuard detects when online verification is enabled.</div></div>',
            unsafe_allow_html=True,
        )

    with engine_col:
        st.markdown(
            f"""
            <div class="rg-intake-shell" style="margin-top:0; height:100%;">
              <div class="rg-intake-label">Audit pipeline</div>
              <div class="rg-intake-title">Four layers of verification</div>
              <div class="rg-finding" style="margin-top:.7rem"><div class="rg-finding-orb" style="background:#5ce1ff;box-shadow:0 0 18px rgba(92,225,255,.35)"></div><div><div class="rg-finding-title">01 · Extract</div><div class="rg-finding-copy">Read document text, DOI references and code links.</div></div></div>
              <div class="rg-finding"><div class="rg-finding-orb" style="background:#a68cff;box-shadow:0 0 18px rgba(166,140,255,.35)"></div><div><div class="rg-finding-title">02 · Verify</div><div class="rg-finding-copy">Resolve scholarly metadata and repository availability.</div></div></div>
              <div class="rg-finding"><div class="rg-finding-orb" style="background:#69f2c1;box-shadow:0 0 18px rgba(105,242,193,.35)"></div><div><div class="rg-finding-title">03 · Audit</div><div class="rg-finding-copy">Measure documentation completeness across reproducibility signals.</div></div></div>
              <div class="rg-finding"><div class="rg-finding-orb" style="background:#ffc96b;box-shadow:0 0 18px rgba(255,201,107,.30)"></div><div><div class="rg-finding-title">04 · Trace</div><div class="rg-finding-copy">Expose evidence and the decision path for human review.</div></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    pdf_bytes = None
    file_name = None
    is_demo = False

    if uploaded is not None and run_upload:
        pdf_bytes = uploaded.getvalue()
        file_name = uploaded.name
    elif use_demo:
        demo_path = ROOT / "examples" / "sample_research_paper.pdf"
        if demo_path.exists():
            pdf_bytes = demo_path.read_bytes()
            file_name = demo_path.name
            is_demo = True
        else:
            st.error("Bundled demo file is missing.")

    if pdf_bytes:
        with st.status("ReproGuard is building the evidence map", expanded=True) as status:
            st.write("Parsing paper structure and research identifiers…")
            auditor = AuditOrchestrator(
                contact_email=contact_email.strip() or None,
                github_token=github_token.strip() or None,
                online=online,
            )
            report = auditor.audit_pdf(pdf_bytes, file_name or "paper.pdf")
            st.write("Resolving citations and research code…")
            st.write("Scoring reproducibility documentation…")
            st.write("Building traceability graph…")
            status.update(label="Evidence audit complete", state="complete", expanded=False)

        st.session_state.rg_report = report
        st.session_state.rg_file_name = file_name
        st.session_state.rg_is_demo = is_demo
        st.rerun()


# -----------------------------
# Results dashboard
# -----------------------------
else:
    report = st.session_state.rg_report
    file_name = st.session_state.rg_file_name or "paper.pdf"
    is_demo = bool(st.session_state.rg_is_demo)

    verified = sum(1 for c in report.citations if c.status.value == "verified")
    live_repos = sum(1 for r in report.repositories if r.exists)
    applicable = [item for item in report.reproducibility_items if item.applicable]
    detected_items = [item for item in applicable if item.detected]
    missing_items = [item for item in applicable if not item.detected]
    label, interpretation = coverage_label(report.rci_score)

    safe_title = html.escape(report.extracted_title or file_name)
    safe_file = html.escape(file_name)
    mode_label = "Demo paper" if is_demo else "Uploaded paper"
    mode_tone = "info" if is_demo else "neutral"
    network_label = "Online verification" if online else "Offline audit"
    network_tone = "success" if online else "neutral"

    st.markdown(
        f"""
        <section class="rg-report-shell">
          <div class="rg-report-top">
            <div>
              <div>{chip('Audit complete','success')} {chip(mode_label,mode_tone)} {chip(network_label,network_tone)}</div>
              <div class="rg-report-title">{safe_title}</div>
              <div class="rg-report-meta">{safe_file} · {report.page_count} pages · {report.character_count:,} extracted characters</div>
            </div>
            <div style="text-align:right;color:#6f809d;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800;">Evidence session<br><span style="color:#b8c8db;font-size:.76rem;letter-spacing:0;text-transform:none;">Local workspace</span></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if is_demo:
        st.markdown(
            '<div class="rg-info-strip" style="margin-top:.75rem"><b style="color:#8ce9ff">Demo mode:</b> this sample intentionally includes every baseline reproducibility signal, so an RCI of 100 is expected. Use a real paper to evaluate practical behaviour.</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    score_col, k1, k2, k3, k4 = st.columns([1.22, 1, 1, 1, 1], gap="medium")
    with score_col:
        st.markdown(
            f"""
            <div class="rg-score-wrap">
              <div class="rg-score-ring" style="--score:{max(0,min(100,report.rci_score)):.1f}">
                <div class="rg-score-inner"><div class="rg-score-value">{report.rci_score:.0f}</div><div class="rg-score-label">RCI / 100</div></div>
              </div>
              <div class="rg-score-caption">{html.escape(label)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k1:
        kpi_card("Methods signals", f"{len(detected_items)}/{len(applicable)}", "Detected in extracted paper text", "cyan")
    with k2:
        kpi_card("DOIs verified", f"{verified}/{len(report.citations)}" if report.citations else "0", "Resolved through scholarly metadata", "violet")
    with k3:
        kpi_card("Repositories", f"{live_repos}/{len(report.repositories)}" if report.repositories else "0", "Public research code reachable", "mint")
    with k4:
        kpi_card("Review items", str(len(missing_items)), "Signals needing manual attention", "amber")

    st.markdown(
        f'<div class="rg-info-strip" style="margin-top:.78rem"><b style="color:#ddecff">Interpretation:</b> {html.escape(interpretation)} RCI measures documentation coverage only — not scientific truth, novelty, validity, or publication quality.</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    tabs = st.tabs([
        "Mission control",
        "Citations",
        "Methods & evidence",
        "Code intelligence",
        "Traceability",
        "Export",
    ])

    with tabs[0]:
        st.write("")
        left, right = st.columns([1.18, 1], gap="large")
        with left:
            section_title("Priority review", "The issues most likely to block independent reproduction.", "Action layer")
            if missing_items:
                for item in missing_items[:7]:
                    finding_card(item.label, action_text(item), "warning")
                if len(missing_items) > 7:
                    st.caption(f"{len(missing_items) - 7} more review item(s) are available under Methods & evidence.")
            else:
                finding_card("No baseline blockers detected", "All current baseline reproducibility signals were found. The evidence still requires human verification.", "success")

        with right:
            section_title("Audit fingerprint", "A compact technical profile of what ReproGuard found.", "Signal layer")
            profile_rows = [
                ("Reproducibility checks", f"{len(detected_items)} detected / {len(applicable)} applicable"),
                ("Citation identifiers", f"{report.doi_count} DOI(s) detected"),
                ("Citation verification", f"{verified} verified"),
                ("Code repositories", f"{len(report.repositories)} referenced / {live_repos} reachable"),
                ("Verification mode", "Online metadata checks" if online else "Local-only baseline"),
            ]
            for title, copy in profile_rows:
                finding_card(title, copy)

        st.write("")
        section_title("Coverage matrix", "A machine-readable view of detected versus missing documentation signals.", "Evidence map")
        coverage_rows = [
            {
                "Area": item.label,
                "Status": "Detected" if item.detected else "Not detected",
                "Baseline check": item.description,
            }
            for item in applicable
        ]
        st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

        if report.warnings:
            with st.expander(f"System cautions ({len(report.warnings)})", expanded=False):
                for warning in report.warnings:
                    st.warning(warning)

    with tabs[1]:
        st.write("")
        section_title("Citation verification", "DOI identifiers are compared with scholarly metadata sources when online verification is enabled.", "Scholarly metadata")
        if report.citations:
            rows = []
            for citation in report.citations:
                rows.append(
                    {
                        "DOI": citation.doi,
                        "Status": citation.status.value,
                        "Resolved title": citation.crossref_title or citation.openalex_title,
                        "Year": citation.year,
                        "Publisher": citation.publisher,
                        "Similarity": citation.metadata_similarity,
                        "Sources": ", ".join(citation.sources_checked),
                        "Issues": "; ".join(citation.issues),
                    }
                )
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption("Identifier resolution does not validate the scientific claims made by the cited work.")
        else:
            st.markdown('<div class="rg-empty">No DOI identifiers were detected in the extracted text.</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.write("")
        m1, m2, m3 = st.columns(3)
        with m1:
            kpi_card("Applicable checks", str(len(applicable)), "Baseline reproducibility criteria", "violet")
        with m2:
            kpi_card("Detected", str(len(detected_items)), "Signals supported by extracted evidence", "mint")
        with m3:
            kpi_card("Not detected", str(len(missing_items)), "Items requiring manual review", "amber")

        st.write("")
        if missing_items:
            section_title("Missing or unclear", "These signals were not detected by the current baseline rules.", "Review queue")
            for item in missing_items:
                with st.expander(f"Review · {item.label}", expanded=False):
                    st.write(item.description)
                    st.markdown(f"**Recommended documentation:** {action_text(item)}")
                    evidence_box(item.evidence)

        section_title("Detected evidence", "Open an item to inspect the exact passage captured from the paper.", "Evidence ledger")
        if detected_items:
            for item in detected_items:
                with st.expander(f"Detected · {item.label}", expanded=False):
                    st.write(item.description)
                    evidence_box(item.evidence)
        else:
            st.markdown('<div class="rg-empty">No reproducibility evidence was detected by the current rule set.</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.write("")
        section_title("Code intelligence", "Inspect public GitHub repositories referenced by the paper and selected repository-level reproducibility signals.", "Repository layer")
        if not report.repositories:
            st.markdown('<div class="rg-empty">No public GitHub repository URL was detected in the extracted paper text.</div>', unsafe_allow_html=True)
        for repo in report.repositories:
            repo_name = f"{repo.owner or '?'} / {repo.repo or '?'}"
            with st.container(border=True):
                top1, top2 = st.columns([2.8, 1])
                with top1:
                    st.markdown(f"### {repo_name}")
                    st.caption(repo.url)
                with top2:
                    st.markdown(chip("Reachable", "success") if repo.exists else chip("Unconfirmed", "warning"), unsafe_allow_html=True)

                if repo.exists:
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Stars", repo.stars if repo.stars is not None else "—")
                    r2.metric("Forks", repo.forks if repo.forks is not None else "—")
                    r3.metric("License", repo.license_name or "Not detected")
                    r4.metric("Last push", repo.last_pushed_at[:10] if repo.last_pushed_at else "—")
                    sig_rows = [
                        {"Repository signal": s.label, "Status": "Detected" if s.detected else "Missing", "Evidence": s.evidence or ""}
                        for s in repo.signals
                    ]
                    if sig_rows:
                        st.dataframe(pd.DataFrame(sig_rows), use_container_width=True, hide_index=True)
                else:
                    st.warning("Repository could not be confirmed as reachable by the current audit.")
                for issue in repo.issues:
                    st.warning(issue)

    with tabs[4]:
        st.write("")
        graph_tab, trace_tab = st.tabs(["Evidence graph", "Audit trace"])
        with graph_tab:
            section_title("Evidence graph", "Maps the paper to citations, repositories and reproducibility evidence so the audit can be inspected rather than merely trusted.", "Traceability")
            try:
                st.graphviz_chart(evidence_graph_dot(report), use_container_width=True)
            except Exception:
                st.code(evidence_graph_dot(report), language="dot")
        with trace_tab:
            section_title("Audit trace", "The Plan → Act → Observe → Evaluate → Replan workflow used by the baseline orchestrator.", "Agent workflow")
            trace_rows = [event.model_dump() for event in report.trace]
            st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.write("")
        section_title("Export audit record", "Preserve the audit as structured JSON or a human-readable Markdown report.", "Research artifact")
        json_text = report_to_json(report)
        md_text = report_to_markdown(report)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "Download JSON audit",
                json_text,
                file_name=f"{Path(file_name).stem}.reproguard.json",
                mime="application/json",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "Download Markdown report",
                md_text,
                file_name=f"{Path(file_name).stem}.reproguard.md",
                mime="text/markdown",
                use_container_width=True,
            )
        st.markdown(
            '<div class="rg-info-strip" style="margin-top:.8rem">Recommended research workflow: retain the JSON as the machine-readable audit artifact and the Markdown file as the human-review companion.</div>',
            unsafe_allow_html=True,
        )
