"""AI Quiz Generator — Streamlit application."""

import streamlit as st
from dotenv import load_dotenv
from html import escape as _esc

from ppt_parser import (
    extract_ppt_text,
    validate_pptx,
    get_content_preview,
    UnsupportedFormatError,
    CorruptedFileError,
    EmptyPresentationError,
)
from quiz_generator import generate_quiz, score_quiz, DifficultyLevel

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens ──────────────────────────────────────────────────────────

_NAVY_DARK  = "#0d2137"
_NAVY       = "#1a3a5c"
_NAVY_MID   = "#1e4a7a"
_GOLD       = "#d4a843"
_GOLD_LT    = "#f0c878"
_WHITE      = "#ffffff"
_WHITE_DIM  = "rgba(255,255,255,0.72)"
_GLASS      = "rgba(255,255,255,0.07)"
_GLASS_LT   = "rgba(255,255,255,0.04)"
_BORDER     = "rgba(255,255,255,0.11)"
_SHADOW     = "rgba(0,0,0,0.35)"

# ── CSS ────────────────────────────────────────────────────────────────────

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── shell ── */
html, body, .stApp {{
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(135deg, {_NAVY_DARK} 0%, {_NAVY} 60%, {_NAVY_MID} 100%) !important;
    color: {_WHITE} !important;
    min-height: 100vh;
}}
.main .block-container {{
    padding: 1.75rem 2.25rem 3rem !important;
    max-width: 1100px;
}}

/* ── sidebar ── */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {_NAVY_DARK} 0%, #112440 100%) !important;
    border-right: 1px solid {_BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {_WHITE} !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: {_WHITE} !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(212,168,67,0.15) !important;
    border-color: {_GOLD} !important;
    color: {_GOLD} !important;
}}

/* ── typography ── */
h1 {{ color: {_WHITE} !important; font-weight: 700; font-size: 1.85rem !important; }}
h2 {{ color: {_WHITE} !important; font-weight: 600; }}
h3 {{ color: {_WHITE_DIM} !important; font-weight: 500; }}
p, li {{ color: {_WHITE_DIM} !important; }}
label {{ color: {_WHITE_DIM} !important; }}
small, .caption {{ color: rgba(255,255,255,0.4) !important; }}

/* ── glass card (static HTML only) ── */
.glass-card {{
    background: {_GLASS};
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid {_BORDER};
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    box-shadow: 0 8px 32px {_SHADOW};
    margin-bottom: 1.25rem;
}}
.glass-card-sm {{
    background: {_GLASS_LT};
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid {_BORDER};
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 4px 16px {_SHADOW};
    margin-bottom: 1rem;
}}

/* ── gold rule ── */
.gold-rule {{
    height: 3px;
    background: linear-gradient(90deg, {_GOLD}, {_GOLD_LT}, transparent);
    border: none;
    border-radius: 2px;
    margin: 0.85rem 0;
}}

/* ── logo area ── */
.logo-area {{
    text-align: center;
    padding: 1.25rem 1rem 0.6rem;
}}
.logo-icon {{ font-size: 2.8rem; display: block; margin-bottom: .2rem; }}
.logo-title {{
    font-size: 1.05rem; font-weight: 700;
    color: {_GOLD} !important;
    letter-spacing: .05em; text-transform: uppercase;
}}
.logo-sub {{
    font-size: .68rem; color: rgba(255,255,255,.35) !important;
    letter-spacing: .07em; text-transform: uppercase;
}}

/* ── sidebar step tracker ── */
.step-item {{
    display: flex; align-items: center; gap: .6rem;
    padding: .4rem .5rem; border-radius: 8px;
    margin-bottom: .2rem;
}}
.step-item.s-active  {{ background: rgba(212,168,67,.14); border-left: 3px solid {_GOLD}; }}
.step-item.s-done    {{ opacity: .8; }}
.step-item.s-pending {{ opacity: .38; }}
.step-dot {{
    width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .68rem; font-weight: 700; flex-shrink: 0;
}}
.step-dot.s-active  {{ background: {_GOLD}; color: {_NAVY_DARK}; }}
.step-dot.s-done    {{ background: #2ecc71; color: #fff; }}
.step-dot.s-pending {{ background: rgba(255,255,255,.12); color: rgba(255,255,255,.5); }}
.step-lbl {{ font-size: .8rem; font-weight: 500; }}
.step-lbl.s-active  {{ color: {_GOLD} !important; font-weight: 600; }}
.step-lbl.s-done    {{ color: #2ecc71 !important; }}
.step-lbl.s-pending {{ color: rgba(255,255,255,.45) !important; }}

/* ── progress stepper (main) ── */
.ps-wrap {{
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 1.75rem; gap: 0;
}}
.ps-step {{ display: flex; flex-direction: column; align-items: center; }}
.ps-bubble {{
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: .88rem;
    border: 2px solid transparent;
    transition: all .25s;
}}
.ps-bubble.s-active  {{
    background: {_GOLD}; color: {_NAVY_DARK};
    box-shadow: 0 0 0 4px rgba(212,168,67,.22);
}}
.ps-bubble.s-done    {{ background: #2ecc71; color: #fff; border-color: #2ecc71; }}
.ps-bubble.s-pending {{
    background: rgba(255,255,255,.07);
    color: rgba(255,255,255,.35);
    border-color: rgba(255,255,255,.14);
}}
.ps-lbl {{ font-size: .66rem; margin-top: .38rem; font-weight: 500;
           white-space: nowrap; letter-spacing: .025em; }}
.ps-lbl.s-active  {{ color: {_GOLD} !important; }}
.ps-lbl.s-done    {{ color: #2ecc71 !important; }}
.ps-lbl.s-pending {{ color: rgba(255,255,255,.3) !important; }}
.ps-line {{
    height: 2px; width: 72px; margin-bottom: 1.35rem; flex-shrink: 0;
}}
.ps-line.s-done    {{ background: #2ecc71; }}
.ps-line.s-active  {{ background: linear-gradient(90deg,#2ecc71,{_GOLD}); }}
.ps-line.s-pending {{ background: rgba(255,255,255,.1); }}

/* ── badges ── */
.badge {{
    display: inline-flex; align-items: center; gap: .28rem;
    padding: .22rem .7rem; border-radius: 20px;
    font-size: .7rem; font-weight: 600;
    letter-spacing: .04em; text-transform: uppercase;
}}
.b-gold  {{ background: rgba(212,168,67,.18); color: {_GOLD} !important;   border: 1px solid rgba(212,168,67,.38); }}
.b-green {{ background: rgba(46,204,113,.14); color: #2ecc71 !important;   border: 1px solid rgba(46,204,113,.32); }}
.b-blue  {{ background: rgba(82,168,232,.14); color: #52a8e8 !important;   border: 1px solid rgba(82,168,232,.28); }}
.b-red   {{ background: rgba(231,76,60,.14);  color: #e57373 !important;   border: 1px solid rgba(231,76,60,.28); }}

/* ── metric card (HTML) ── */
.mc {{
    background: {_GLASS}; border: 1px solid {_BORDER};
    border-radius: 14px; padding: 1.2rem 1.4rem;
    text-align: center; box-shadow: 0 4px 16px {_SHADOW};
}}
.mc-value {{ font-size: 2.1rem; font-weight: 700; color: {_GOLD} !important; line-height: 1; }}
.mc-label {{
    font-size: .72rem; color: rgba(255,255,255,.5) !important;
    text-transform: uppercase; letter-spacing: .06em; margin-top: .3rem;
}}

/* ── shimmer ── */
@keyframes shimmer {{
    0%   {{ background-position: -600px 0; }}
    100% {{ background-position: 600px 0; }}
}}
.shimmer {{
    background: linear-gradient(90deg,
        rgba(255,255,255,.03) 25%,
        rgba(255,255,255,.09) 50%,
        rgba(255,255,255,.03) 75%);
    background-size: 600px 100%;
    animation: shimmer 1.6s infinite linear;
    border-radius: 10px; margin-bottom: .6rem;
}}
.sh-line  {{ height: 16px; }}
.sh-block {{ height: 72px; }}

/* ── file uploader ── */
[data-testid="stFileUploader"] {{
    background: {_GLASS} !important;
    border: 2px dashed rgba(212,168,67,.38) !important;
    border-radius: 14px !important;
    transition: border-color .2s;
}}
[data-testid="stFileUploader"]:hover {{ border-color: {_GOLD} !important; }}

/* ── buttons ── */
.stButton > button {{
    border-radius: 10px !important;
    font-weight: 600 !important; font-size: .84rem !important;
    letter-spacing: .02em !important;
    transition: all .2s !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    background: rgba(255,255,255,.07) !important;
    color: {_WHITE} !important; padding: .5rem 1.2rem !important;
}}
.stButton > button:hover {{
    background: rgba(212,168,67,.16) !important;
    border-color: {_GOLD} !important; color: {_GOLD} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(212,168,67,.18) !important;
}}
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {_GOLD}, {_GOLD_LT}) !important;
    color: {_NAVY_DARK} !important; border-color: transparent !important;
    font-weight: 700 !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, {_GOLD_LT}, {_GOLD}) !important;
    color: {_NAVY_DARK} !important;
    box-shadow: 0 6px 20px rgba(212,168,67,.42) !important;
}}
.stButton > button:disabled {{
    opacity: .38 !important; cursor: not-allowed !important;
}}

/* ── progress bar ── */
.stProgress > div > div {{
    background: rgba(255,255,255,.08) !important;
    border-radius: 8px !important; height: 10px !important;
}}
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {_GOLD}, {_GOLD_LT}) !important;
    border-radius: 8px !important;
}}

/* ── st.metric ── */
[data-testid="stMetric"] {{
    background: {_GLASS} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 14px !important; padding: 1rem 1.2rem !important;
}}
[data-testid="stMetricValue"] {{
    color: {_GOLD} !important; font-weight: 700 !important;
    font-size: 1.9rem !important;
}}
[data-testid="stMetricLabel"] {{
    color: rgba(255,255,255,.5) !important;
    font-size: .72rem !important;
    text-transform: uppercase; letter-spacing: .05em;
}}

/* ── expanders ── */
[data-testid="stExpander"] {{
    background: {_GLASS_LT} !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 12px !important; margin-bottom: .45rem !important;
}}
[data-testid="stExpander"] summary {{
    color: {_WHITE} !important; font-weight: 500 !important;
}}
[data-testid="stExpander"] summary:hover {{ color: {_GOLD} !important; }}

/* ── slider ── */
[data-testid="stSlider"] > div > div > div > div {{ background: {_GOLD} !important; }}
[data-testid="stSlider"] div[role="slider"] {{
    background: {_GOLD} !important; border-color: {_GOLD} !important;
}}
[data-testid="stSlider"] .stSlider {{ color: {_GOLD} !important; }}

/* ── selectbox ── */
.stSelectbox > div > div {{
    background: rgba(255,255,255,.06) !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 10px !important; color: {_WHITE} !important;
}}
.stSelectbox > div > div:hover {{ border-color: {_GOLD} !important; }}
.stSelectbox svg {{ fill: {_GOLD} !important; }}

/* ── radio ── */
.stRadio > div {{ gap: .4rem !important; }}
.stRadio > div > label {{
    background: rgba(255,255,255,.05) !important;
    border: 1px solid {_BORDER} !important;
    border-radius: 10px !important;
    padding: .6rem 1rem !important;
    cursor: pointer !important;
    transition: all .18s !important;
    color: {_WHITE_DIM} !important;
    width: 100%;
}}
.stRadio > div > label:hover {{
    background: rgba(212,168,67,.1) !important;
    border-color: rgba(212,168,67,.45) !important;
    color: {_WHITE} !important;
}}
.stRadio > div > label[data-testid*="selected"] {{
    background: rgba(212,168,67,.14) !important;
    border-color: {_GOLD} !important; color: {_WHITE} !important;
}}

/* ── alerts ── */
[data-testid="stAlert"] {{ border-radius: 12px !important; border-width: 1px !important; }}

/* ── divider ── */
hr {{ border-color: {_BORDER} !important; }}

/* ── scrollbar ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,.16); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {_GOLD}; }}

/* ── upload — format chips ── */
.uz-chip {{
    background: rgba(212,168,67,.12);
    border: 1px solid rgba(212,168,67,.28);
    border-radius: 6px; padding: .2rem .65rem;
    font-size: .72rem; font-weight: 600;
    color: {_GOLD} !important; letter-spacing: .04em;
    display: inline-block;
}}

/* ── upload — file uploader widget overrides ── */
[data-testid="stFileUploader"] {{
    background: {_GLASS} !important;
    border: 2px dashed rgba(212,168,67,.35) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
    transition: border-color .22s, background .22s !important;
    text-align: center;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {_GOLD} !important;
    background: rgba(212,168,67,.05) !important;
}}
[data-testid="stFileUploader"] section {{
    border: none !important; background: transparent !important;
    padding: 0 !important;
}}
[data-testid="stFileUploader"] label {{
    color: rgba(255,255,255,.7) !important;
    font-size: .88rem !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] {{
    color: rgba(255,255,255,.5) !important;
    font-size: .8rem !important;
}}
[data-testid="baseButton-secondary"][data-testid*="File"] {{
    background: rgba(212,168,67,.15) !important;
    border-color: rgba(212,168,67,.4) !important;
    color: {_GOLD} !important;
}}

/* ── upload — file info card (success) ── */
.fi-card {{
    background: {_GLASS};
    border: 1px solid rgba(46,204,113,.35);
    border-radius: 14px; padding: 1.1rem 1.4rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.28);
    margin: .75rem 0 1rem;
}}
.fi-card.fi-error {{
    border-color: rgba(231,76,60,.38);
    background: rgba(231,76,60,.04);
}}
.fi-header {{
    display: flex; align-items: center;
    justify-content: space-between;
    flex-wrap: wrap; gap: .5rem;
    margin-bottom: .8rem;
}}
.fi-name-row {{
    display: flex; align-items: center; gap: .6rem;
}}
.fi-icon {{ font-size: 1.55rem; }}
.fi-name {{
    font-size: .92rem; font-weight: 600;
    color: {_WHITE} !important; word-break: break-all;
    max-width: 360px;
}}
.fi-stats {{
    display: flex; gap: 2.2rem; flex-wrap: wrap;
    padding-top: .75rem;
    border-top: 1px solid rgba(255,255,255,.08);
}}
.fi-stat {{ display: flex; flex-direction: column; gap: .1rem; }}
.fi-stat-label {{
    font-size: .62rem; text-transform: uppercase;
    letter-spacing: .07em; color: rgba(255,255,255,.36) !important;
}}
.fi-stat-value {{
    font-size: .95rem; font-weight: 700; color: {_GOLD} !important;
}}
.fi-stat-value.white {{ color: {_WHITE} !important; }}

/* ── upload — error detail ── */
.fi-error-msg {{
    background: rgba(231,76,60,.09);
    border: 1px solid rgba(231,76,60,.22);
    border-radius: 8px; padding: .55rem .85rem;
    font-size: .8rem; color: #e57373 !important;
    margin-top: .7rem;
    display: flex; align-items: flex-start; gap: .4rem;
    line-height: 1.45;
}}

/* ── upload — idle placeholder ── */
.upload-idle {{
    text-align: center; padding: .6rem 0 1rem;
    color: rgba(255,255,255,.28) !important;
    font-size: .78rem;
}}

/* ── continue button disabled state ── */
.stButton > button:disabled {{
    opacity: .32 !important; cursor: not-allowed !important;
    background: rgba(255,255,255,.06) !important;
    border-color: rgba(255,255,255,.1) !important;
    color: rgba(255,255,255,.35) !important;
    transform: none !important;
}}

/* ── configure — ppt source summary card ── */
.ppt-source {{
    background: {_GLASS};
    border: 1px solid {_BORDER};
    border-radius: 14px;
    padding: 1rem 1.35rem;
    display: flex; align-items: center;
    justify-content: space-between;
    flex-wrap: wrap; gap: .75rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 16px {_SHADOW};
}}
.ppt-source-left {{
    display: flex; align-items: center; gap: .75rem;
}}
.ppt-source-icon {{ font-size: 1.8rem; }}
.ppt-source-name {{
    font-size: .95rem; font-weight: 600;
    color: {_WHITE} !important; margin-bottom: .15rem;
}}
.ppt-source-meta {{
    font-size: .72rem; color: rgba(255,255,255,.45) !important;
    letter-spacing: .02em;
}}
.ppt-source-stats {{
    display: flex; gap: .45rem; flex-wrap: wrap; align-items: center;
}}

/* ── configure — question count card ── */
.qcount-card {{
    background: {_GLASS};
    border: 1px solid {_BORDER};
    border-radius: 14px;
    padding: 1.25rem 1.5rem 1.1rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 16px {_SHADOW};
}}
.qcount-header {{
    display: flex; align-items: center;
    justify-content: space-between;
    margin-bottom: .7rem;
}}
.qcount-label {{
    font-size: .7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: rgba(255,255,255,.45) !important;
}}
.qcount-value {{
    font-size: 1.65rem; font-weight: 700;
    color: {_GOLD} !important; line-height: 1;
}}
.qcount-caption {{
    font-size: .75rem; color: rgba(255,255,255,.4) !important;
    margin-top: .55rem;
}}

/* ── configure — difficulty cards ── */
.diff-section-label {{
    font-size: .7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .08em;
    color: rgba(255,255,255,.45) !important;
    margin-bottom: .65rem;
}}
.diff-card {{
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 14px;
    padding: 1.25rem 1rem 1rem;
    text-align: center;
    transition: all .2s;
    cursor: pointer;
    min-height: 148px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: flex-start;
    gap: .3rem;
}}
.diff-card.selected {{
    background: rgba(212,168,67,.12);
    border-color: {_GOLD};
    box-shadow: 0 0 0 1px rgba(212,168,67,.35), 0 6px 20px rgba(212,168,67,.14);
}}
.diff-card:hover {{ background: rgba(255,255,255,.08); }}
.diff-card.selected:hover {{ background: rgba(212,168,67,.16); }}
.diff-icon {{ font-size: 2rem; margin-bottom: .1rem; }}
.diff-title {{
    font-size: .92rem; font-weight: 700; color: {_WHITE} !important;
}}
.diff-title.selected {{ color: {_GOLD} !important; }}
.diff-tag {{
    font-size: .65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em;
    padding: .18rem .55rem; border-radius: 20px;
    margin-top: .1rem;
}}
.diff-tag.simple  {{ background: rgba(46,204,113,.15);  color: #2ecc71 !important; }}
.diff-tag.medium  {{ background: rgba(212,168,67,.15);  color: {_GOLD} !important; }}
.diff-tag.complex {{ background: rgba(231,76,60,.15);   color: #e57373 !important; }}
.diff-desc {{
    font-size: .73rem; color: rgba(255,255,255,.45) !important;
    line-height: 1.45; margin-top: .2rem;
}}
.diff-check {{
    font-size: .68rem; font-weight: 700;
    color: {_GOLD} !important; margin-top: auto;
    padding-top: .4rem; letter-spacing: .04em;
}}

/* ── configure — settings summary bar ── */
.settings-bar {{
    background: rgba(212,168,67,.08);
    border: 1px solid rgba(212,168,67,.22);
    border-radius: 12px;
    padding: .85rem 1.25rem;
    display: flex; align-items: center;
    justify-content: space-between; flex-wrap: wrap;
    gap: .6rem; margin: 1rem 0;
}}
.settings-bar-text {{
    font-size: .82rem; color: rgba(255,255,255,.7) !important;
}}
.settings-bar-text strong {{ color: {_GOLD} !important; }}
.settings-bar-badges {{ display: flex; gap: .4rem; flex-wrap: wrap; }}

/* ── slide preview section ── */
.preview-section {{
    margin: 1.1rem 0 0;
}}
.preview-section-header {{
    display: flex; align-items: center;
    justify-content: space-between;
    margin-bottom: .65rem;
}}
.preview-section-title {{
    display: flex; align-items: center; gap: .45rem;
    font-size: .88rem; font-weight: 600; color: {_WHITE} !important;
}}
.preview-section-title .ps-icon {{ font-size: 1rem; }}

/* ── individual slide card ── */
.sp-card {{
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-left: 3px solid {_GOLD};
    border-radius: 10px;
    padding: .8rem 1.05rem .85rem;
    margin-bottom: .5rem;
    transition: background .18s;
}}
.sp-card:hover {{
    background: rgba(255,255,255,.06);
    border-left-color: {_GOLD_LT};
}}
.sp-header {{
    display: flex; align-items: center;
    justify-content: space-between;
    margin-bottom: .38rem;
}}
.sp-number {{
    font-size: .65rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .1em;
    color: {_GOLD} !important;
}}
.sp-content {{
    font-size: .82rem; color: rgba(255,255,255,.68) !important;
    line-height: 1.6; white-space: pre-wrap; word-break: break-word;
}}
.sp-content-full {{
    font-size: .82rem; color: rgba(255,255,255,.68) !important;
    line-height: 1.6; white-space: pre-wrap; word-break: break-word;
}}
.sp-empty {{
    font-size: .76rem; color: rgba(255,255,255,.26) !important;
    font-style: italic;
}}
.sp-truncated {{
    font-size: .72rem; color: rgba(212,168,67,.55) !important;
    margin-top: .3rem;
}}
</style>
"""

# ── HTML helpers ───────────────────────────────────────────────────────────

STEP_ORDER  = ["upload", "configure", "quiz", "results"]
STEP_LABELS = {"upload": "Upload", "configure": "Configure", "quiz": "Quiz", "results": "Results"}


def _html(content: str) -> None:
    st.markdown(content, unsafe_allow_html=True)


def _badge(text: str, variant: str = "gold") -> str:
    icons = {"gold": "✦", "green": "✔", "blue": "ℹ", "red": "✖"}
    return f'<span class="badge b-{variant}">{icons.get(variant,"✦")} {text}</span>'


def _metric_card(value: str, label: str) -> str:
    return (
        f'<div class="mc">'
        f'<div class="mc-value">{value}</div>'
        f'<div class="mc-label">{label}</div>'
        f'</div>'
    )


def _shimmer(lines: int = 3, block: bool = False) -> None:
    parts = '<div class="shimmer sh-block"></div>' if block else "".join(
        f'<div class="shimmer sh-line" style="width:{[100,82,65][i%3]}%"></div>'
        for i in range(lines)
    )
    _html(f'<div style="padding:.4rem 0">{parts}</div>')


def _gold_rule() -> None:
    _html('<div class="gold-rule"></div>')


# ── Slide preview helpers ───────────────────────────────────────────────────

_PREVIEW_CHARS = 200   # chars shown per slide in the inline preview
_PREVIEW_COUNT = 3     # slides shown without expanding


def _slide_card_html(slide: dict, truncate: bool = True) -> str:
    """Return the HTML string for one slide preview card."""
    num     = slide["slide_number"]
    content = slide.get("content", "").strip()

    if content:
        limit = _PREVIEW_CHARS if truncate else None
        snip  = content[:limit] if limit else content
        did_truncate = truncate and len(content) > _PREVIEW_CHARS
        css_cls = "sp-content" if truncate else "sp-content-full"
        body = (
            f'<div class="{css_cls}">{_esc(snip)}</div>'
            + ('<div class="sp-truncated">… content truncated</div>' if did_truncate else "")
        )
        empty_badge = ""
    else:
        body        = '<div class="sp-empty">— no text on this slide —</div>'
        empty_badge = _badge("Empty", "gold")

    return (
        f'<div class="sp-card">'
        f'  <div class="sp-header">'
        f'    <span class="sp-number">Slide {num}</span>'
        f'    {empty_badge}'
        f'  </div>'
        f'  {body}'
        f'</div>'
    )


def _render_slide_preview(slides: list, slide_count: int) -> None:
    """
    Render the inline 3-slide preview and the expandable full-slide list.
    """
    preview_slides   = slides[:_PREVIEW_COUNT]
    remaining_slides = slides[_PREVIEW_COUNT:]

    # ── section header ──
    showing = len(preview_slides)
    _html(f"""
    <div class="preview-section">
        <div class="preview-section-header">
            <div class="preview-section-title">
                <span class="ps-icon">📋</span>
                Content Preview
            </div>
            {_badge(f"Showing {showing} of {slide_count} slides", "blue")}
        </div>
    </div>
    """)

    # ── first 3 slides inline ──
    _html("".join(_slide_card_html(s, truncate=True) for s in preview_slides))

    # ── expandable: all slides ──
    label = (
        f"View all {slide_count} slides"
        if remaining_slides
        else f"View full content ({slide_count} slide{'s' if slide_count != 1 else ''})"
    )
    with st.expander(label, expanded=False):
        _html("".join(_slide_card_html(s, truncate=False) for s in slides))


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1_048_576:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / 1_048_576:.1f} MB"


# ── Progress stepper ───────────────────────────────────────────────────────


def _stepper() -> None:
    current = st.session_state.step
    cur_idx = STEP_ORDER.index(current)
    parts   = []

    for i, key in enumerate(STEP_ORDER):
        if i < cur_idx:
            state, dot = "s-done", "✓"
        elif i == cur_idx:
            state, dot = "s-active", str(i + 1)
        else:
            state, dot = "s-pending", str(i + 1)

        parts.append(
            f'<div class="ps-step">'
            f'<div class="ps-bubble {state}">{dot}</div>'
            f'<div class="ps-lbl {state}">{STEP_LABELS[key]}</div>'
            f'</div>'
        )
        if i < len(STEP_ORDER) - 1:
            line_state = "s-done" if i < cur_idx else ("s-active" if i == cur_idx else "s-pending")
            parts.append(f'<div class="ps-line {line_state}"></div>')

    _html(f'<div class="ps-wrap">{"".join(parts)}</div>')


# ── Session state ──────────────────────────────────────────────────────────


def _init_state() -> None:
    defaults = {
        "step": "upload",
        "ppt_data": None,
        "quiz": None,
        "user_answers": {},
        "current_question_idx": 0,
        "score_result": None,
        "num_questions": 10,
        "difficulty": "Medium",
        # upload tracking
        "upload_filename": None,
        "upload_size_bytes": 0,
        "upload_valid": False,
        "upload_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ── Navigation ─────────────────────────────────────────────────────────────


def go_to(step: str) -> None:
    st.session_state.step = step


def reset_app() -> None:
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    _init_state()


# ── Sidebar ────────────────────────────────────────────────────────────────


def render_sidebar() -> None:
    with st.sidebar:
        _html("""
        <div class="logo-area">
            <span class="logo-icon">🎯</span>
            <div class="logo-title">AI Quiz Generator</div>
            <div class="logo-sub">TechVest Global · 2025–26</div>
        </div>
        <div class="gold-rule"></div>
        """)

        cur_idx = STEP_ORDER.index(st.session_state.step)
        step_rows = [
            ("upload",    "Upload PPT"),
            ("configure", "Configure Quiz"),
            ("quiz",      "Take Quiz"),
            ("results",   "Results"),
        ]
        rows_html = ""
        for i, (key, label) in enumerate(step_rows):
            if i < cur_idx:
                state, dot = "s-done", "✓"
            elif i == cur_idx:
                state, dot = "s-active", str(i + 1)
            else:
                state, dot = "s-pending", str(i + 1)
            rows_html += (
                f'<div class="step-item {state}">'
                f'<div class="step-dot {state}">{dot}</div>'
                f'<span class="step-lbl {state}">{label}</span>'
                f'</div>'
            )
        _html(rows_html)
        _gold_rule()

        if st.session_state.ppt_data:
            d = st.session_state.ppt_data
            _html(f"""
            <div class="glass-card-sm">
                <div style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;
                            color:rgba(255,255,255,.4);margin-bottom:.5rem">Loaded File</div>
                <div style="display:flex;justify-content:space-between;margin-bottom:.28rem">
                    <span style="font-size:.78rem;color:rgba(255,255,255,.65)">Slides</span>
                    <span style="font-size:.78rem;font-weight:600;color:#d4a843">{d['slide_count']}</span>
                </div>
                <div style="display:flex;justify-content:space-between">
                    <span style="font-size:.78rem;color:rgba(255,255,255,.65)">Words</span>
                    <span style="font-size:.78rem;font-weight:600;color:#d4a843">{d['total_words']:,}</span>
                </div>
            </div>
            """)

        if st.session_state.step != "upload":
            if st.button("🔄 Start Over", use_container_width=True):
                reset_app()
                st.rerun()

        _html("""
        <div style="margin-top:2rem;text-align:center">
            <div style="font-size:.62rem;color:rgba(255,255,255,.28);line-height:1.7">
                Powered by OpenRouter · Built with Streamlit<br/>© 2025–26 TechVest Global
            </div>
        </div>
        """)


# ── Step 1 — Upload ────────────────────────────────────────────────────────


def _render_file_info_card() -> None:
    """Render the file details card after a file has been selected."""
    filename   = st.session_state.upload_filename or ""
    is_valid   = st.session_state.upload_valid
    error_msg  = st.session_state.upload_error or "File could not be validated."
    size_bytes = st.session_state.upload_size_bytes
    ppt_data   = st.session_state.ppt_data

    ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"

    if is_valid and ppt_data:
        _html(f"""
        <div class="fi-card">
            <div class="fi-header">
                <div class="fi-name-row">
                    <span class="fi-icon">📄</span>
                    <span class="fi-name">{filename}</span>
                </div>
                <div style="display:flex;gap:.4rem;align-items:center">
                    {_badge(ext, "blue")}
                    {_badge("Valid", "green")}
                </div>
            </div>
            <div class="fi-stats">
                <div class="fi-stat">
                    <span class="fi-stat-label">File Size</span>
                    <span class="fi-stat-value">{_format_size(size_bytes)}</span>
                </div>
                <div class="fi-stat">
                    <span class="fi-stat-label">Slides</span>
                    <span class="fi-stat-value">{ppt_data['slide_count']}</span>
                </div>
                <div class="fi-stat">
                    <span class="fi-stat-label">Words Extracted</span>
                    <span class="fi-stat-value">{ppt_data['total_words']:,}</span>
                </div>
            </div>
        </div>
        """)
    else:
        _html(f"""
        <div class="fi-card fi-error">
            <div class="fi-header">
                <div class="fi-name-row">
                    <span class="fi-icon">📄</span>
                    <span class="fi-name">{filename}</span>
                </div>
                <div style="display:flex;gap:.4rem;align-items:center">
                    {_badge(ext, "blue")}
                    {_badge("Invalid", "red")}
                </div>
            </div>
            <div class="fi-error-msg">
                <span>✖</span>
                <span>{error_msg}</span>
            </div>
        </div>
        """)


def render_upload_step() -> None:
    _stepper()

    # ── Page header ──
    _html("""
    <div class="glass-card">
        <h1 style="margin:0 0 .28rem">Upload Presentation</h1>
        <p style="margin:0;font-size:.9rem">
            Drag and drop or browse to select a
            <strong style="color:#d4a843">PPT or PPTX</strong> file.
            Only PowerPoint files are accepted — other formats are rejected automatically.
        </p>
    </div>
    """)

    # ── Drop zone header (above the Streamlit widget) ──
    _html("""
    <div style="text-align:center;padding:.75rem 0 .5rem">
        <div style="font-size:2.6rem;margin-bottom:.3rem">📁</div>
        <div style="font-size:.95rem;font-weight:600;color:#fff;margin-bottom:.18rem">
            Drop your PowerPoint file here
        </div>
        <div style="font-size:.78rem;color:rgba(255,255,255,.4);margin-bottom:.6rem">
            or use the browse button below
        </div>
        <div style="display:inline-flex;gap:.4rem">
            <span class="uz-chip">.PPT</span>
            <span class="uz-chip">.PPTX</span>
        </div>
    </div>
    """)

    # ── File uploader widget ──
    uploaded = st.file_uploader(
        "Choose a PowerPoint file",
        type=["ppt", "pptx"],
        help="Drag & drop or click Browse. Accepts .ppt and .pptx only.",
        label_visibility="collapsed",
    )

    # ── Process the selected file (only when it changes) ──
    if uploaded is not None:
        if uploaded.name != st.session_state.upload_filename:
            file_bytes = uploaded.read()
            st.session_state.upload_size_bytes = uploaded.size
            st.session_state.upload_filename   = uploaded.name

            try:
                with st.spinner("Reading and extracting slide content…"):
                    ppt_data = extract_ppt_text(file_bytes)
                st.session_state.ppt_data    = ppt_data
                st.session_state.upload_valid = True
                st.session_state.upload_error = None

            except UnsupportedFormatError as exc:
                st.session_state.ppt_data    = None
                st.session_state.upload_valid = False
                st.session_state.upload_error = str(exc)

            except CorruptedFileError as exc:
                st.session_state.ppt_data    = None
                st.session_state.upload_valid = False
                st.session_state.upload_error = str(exc)

            except EmptyPresentationError as exc:
                st.session_state.ppt_data    = None
                st.session_state.upload_valid = False
                st.session_state.upload_error = str(exc)

            except Exception as exc:
                st.session_state.ppt_data    = None
                st.session_state.upload_valid = False
                st.session_state.upload_error = f"Unexpected error: {exc}"

        _render_file_info_card()

    else:
        # User cleared the uploader — reset cached upload state
        if st.session_state.upload_filename is not None:
            st.session_state.upload_filename   = None
            st.session_state.upload_size_bytes = 0
            st.session_state.upload_valid      = False
            st.session_state.upload_error      = None
            st.session_state.ppt_data          = None

        _html('<div class="upload-idle">No file selected — upload a .ppt or .pptx to continue</div>')

    # ── Slide preview (only when valid) ──
    if st.session_state.ppt_data:
        d = st.session_state.ppt_data
        _render_slide_preview(d["slides"], d["slide_count"])

    # ── Continue button — always rendered, disabled until valid file is loaded ──
    is_ready = st.session_state.ppt_data is not None
    st.button(
        "Continue to Configure →" if is_ready else "Upload a valid file to continue",
        on_click=go_to,
        args=("configure",),
        type="primary",
        disabled=not is_ready,
        use_container_width=True,
    )


# ── Step 2 — Configure ────────────────────────────────────────────────────

_DIFF_META = {
    "Simple": {
        "icon":  "🟢",
        "tag":   "Beginner",
        "desc":  "Recall-based questions.\nFocused on definitions\nand key facts.",
        "tag_cls": "simple",
    },
    "Medium": {
        "icon":  "🟡",
        "tag":   "Intermediate",
        "desc":  "Application questions.\nRequires understanding\nand reasoning.",
        "tag_cls": "medium",
    },
    "Complex": {
        "icon":  "🔴",
        "tag":   "Advanced",
        "desc":  "Analysis questions.\nCritical thinking\nand deep insight.",
        "tag_cls": "complex",
    },
}


def _set_difficulty(d: str) -> None:
    st.session_state.difficulty = d


def render_configure_step() -> None:
    _stepper()

    # ── Guard: no PPT loaded ──
    if st.session_state.ppt_data is None:
        _html(f"""
        <div class="glass-card" style="border-color:rgba(212,168,67,.35)">
            {_badge("No Presentation", "gold")}
            <p style="margin:.5rem 0 0">
                Please upload a presentation before configuring the quiz.
            </p>
        </div>
        """)
        st.button("← Back to Upload", on_click=go_to, args=("upload",))
        return

    data     = st.session_state.ppt_data
    filename = st.session_state.upload_filename or "presentation.pptx"
    filesize = _format_size(st.session_state.upload_size_bytes)

    # ── Page header ──
    _html("""
    <div class="glass-card">
        <h1 style="margin:0 0 .28rem">Configure Quiz</h1>
        <p style="margin:0;font-size:.9rem">
            Choose how many questions to generate and the difficulty level,
            then hit <strong style="color:#d4a843">Generate Quiz</strong>.
        </p>
    </div>
    """)

    # ── Source PPT summary ──
    _html(f"""
    <div class="ppt-source">
        <div class="ppt-source-left">
            <span class="ppt-source-icon">📄</span>
            <div>
                <div class="ppt-source-name">{_esc(filename)}</div>
                <div class="ppt-source-meta">
                    {filesize} &nbsp;·&nbsp; uploaded this session
                </div>
            </div>
        </div>
        <div class="ppt-source-stats">
            {_badge(f"{data['slide_count']} Slides", "blue")}
            {_badge(f"{data['total_words']:,} Words", "gold")}
        </div>
    </div>
    """)

    # ── Question count ──
    _html("""
    <div class="qcount-card">
        <div class="qcount-header">
            <span class="qcount-label">Number of Questions</span>
        </div>
    """)

    num_q: int = st.slider(
        "Number of questions",
        min_value=5, max_value=30,
        value=st.session_state.num_questions, step=1,
        help="Drag to set how many multiple-choice questions the AI will generate.",
        label_visibility="collapsed",
    )
    st.session_state.num_questions = num_q

    _html(f"""
        <div class="qcount-caption">
            <strong style="color:#d4a843;font-size:.9rem">{num_q}</strong>
            &nbsp;questions will be generated from your {data['slide_count']} slides
        </div>
    </div>
    """)

    # ── Difficulty selection ──
    _html('<div class="diff-section-label">Difficulty Level</div>')

    diff_cols = st.columns(3)
    current_diff: DifficultyLevel = st.session_state.difficulty

    for col, diff in zip(diff_cols, ["Simple", "Medium", "Complex"]):
        meta      = _DIFF_META[diff]
        is_sel    = current_diff == diff
        card_cls  = "diff-card selected" if is_sel else "diff-card"
        title_cls = "diff-title selected" if is_sel else "diff-title"
        check_row = '<div class="diff-check">✓ Selected</div>' if is_sel else ""
        desc_html = _esc(meta["desc"]).replace("&#10;", "<br>").replace("\n", "<br>")

        with col:
            _html(f"""
            <div class="{card_cls}">
                <div class="diff-icon">{meta['icon']}</div>
                <div class="{title_cls}">{diff}</div>
                <div class="diff-tag {meta['tag_cls']}">{meta['tag']}</div>
                <div class="diff-desc">{desc_html}</div>
                {check_row}
            </div>
            """)
            if is_sel:
                st.button(
                    f"✓ {diff}",
                    key=f"diff_{diff}",
                    use_container_width=True,
                    type="primary",
                    disabled=True,
                )
            else:
                st.button(
                    f"Select {diff}",
                    key=f"diff_{diff}",
                    use_container_width=True,
                    on_click=_set_difficulty,
                    args=(diff,),
                )

    # ── Settings summary bar ──
    diff_badge_map = {"Simple": "green", "Medium": "gold", "Complex": "red"}

    _html(f"""
    <div class="settings-bar">
        <div class="settings-bar-text">
            Generating <strong>{num_q}</strong> questions &nbsp;·&nbsp;
            <strong>{current_diff}</strong> difficulty &nbsp;·&nbsp;
            from <strong>{_esc(filename)}</strong>
        </div>
        <div class="settings-bar-badges">
            {_badge(f"{num_q} Questions", "gold")}
            {_badge(current_diff, diff_badge_map.get(current_diff, "gold"))}
        </div>
    </div>
    """)

    # ── Actions ──
    col_back, col_gen = st.columns([1, 3])
    with col_back:
        st.button("← Back", on_click=go_to, args=("upload",), use_container_width=True)
    with col_gen:
        if st.button(
            "Generate Quiz ✨",
            type="primary",
            use_container_width=True,
            help=f"Generate {num_q} {current_diff} questions from your slides",
        ):
            _generate_and_advance(data["full_text"], num_q, current_diff)


def _generate_and_advance(full_text: str, num_questions: int, difficulty: DifficultyLevel) -> None:
    with st.spinner(f"Generating {num_questions} {difficulty} questions…"):
        quiz = generate_quiz(full_text, num_questions, difficulty)
    st.session_state.quiz                 = quiz
    st.session_state.user_answers         = {}
    st.session_state.current_question_idx = 0
    go_to("quiz")
    st.rerun()


# ── Step 3 — Quiz ─────────────────────────────────────────────────────────


def render_quiz_step() -> None:
    _stepper()

    quiz = st.session_state.quiz
    if quiz is None:
        _html(f"""
        <div class="glass-card" style="border-color:rgba(212,168,67,.35)">
            {_badge("No Quiz", "gold")}
            <p style="margin:.5rem 0 0">Configure and generate a quiz first.</p>
        </div>
        """)
        st.button("← Back to Configure", on_click=go_to, args=("configure",))
        return

    total    = quiz.total_questions
    idx      = st.session_state.current_question_idx
    question = quiz.questions[idx]
    answered = len(st.session_state.user_answers)

    diff_badge = {"Simple": "green", "Medium": "gold", "Complex": "red"}

    _html(f"""
    <div class="glass-card">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    flex-wrap:wrap;gap:.6rem;margin-bottom:.85rem">
            <div>
                <span style="font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;
                             color:rgba(255,255,255,.4)">Question</span>
                <span style="font-size:1.55rem;font-weight:700;color:#d4a843;
                             margin-left:.4rem">{idx + 1}</span>
                <span style="font-size:.85rem;color:rgba(255,255,255,.4)"> / {total}</span>
            </div>
            <div style="display:flex;gap:.45rem;flex-wrap:wrap">
                {_badge(quiz.difficulty, diff_badge.get(quiz.difficulty,"gold"))}
                {_badge(f"{answered} Answered", "blue")}
            </div>
        </div>
        <p style="margin:0;font-size:1.02rem;font-weight:500;
                  color:#fff;line-height:1.55">{question.text}</p>
    </div>
    """)

    st.progress((idx + 1) / total)

    options = {c.label: f"{c.label}.  {c.text}" for c in question.choices}
    current_answer = st.session_state.user_answers.get(question.number)

    selected_label = st.radio(
        "Choose your answer:",
        options=list(options.keys()),
        format_func=lambda k: options[k],
        index=list(options.keys()).index(current_answer) if current_answer in options else None,
        key=f"q_{question.number}",
        label_visibility="collapsed",
    )

    if selected_label:
        st.session_state.user_answers[question.number] = selected_label

    _gold_rule()

    col_prev, col_next, col_spacer, col_submit = st.columns([1, 1, 0.4, 2])

    with col_prev:
        if idx > 0:
            st.button("← Prev", on_click=_set_question_idx, args=(idx - 1,), use_container_width=True)

    with col_next:
        if idx < total - 1:
            st.button("Next →", on_click=_set_question_idx, args=(idx + 1,),
                      type="primary", use_container_width=True)

    with col_submit:
        unanswered = total - len(st.session_state.user_answers)
        if unanswered == 0:
            if st.button("Submit Quiz ✅", type="primary", use_container_width=True):
                _submit_quiz()
        else:
            st.button(
                f"Submit  ({unanswered} remaining)",
                disabled=True,
                use_container_width=True,
                help=f"Answer all {unanswered} remaining question(s) first.",
            )


def _set_question_idx(idx: int) -> None:
    st.session_state.current_question_idx = idx


def _submit_quiz() -> None:
    result = score_quiz(st.session_state.quiz, st.session_state.user_answers)
    st.session_state.score_result = result
    go_to("results")
    st.rerun()


# ── Step 4 — Results ──────────────────────────────────────────────────────


def render_results_step() -> None:
    _stepper()

    result = st.session_state.score_result
    if result is None:
        _html(f"""
        <div class="glass-card" style="border-color:rgba(212,168,67,.35)">
            {_badge("No Results", "gold")}
            <p style="margin:.5rem 0 0">Complete the quiz to see your results.</p>
        </div>
        """)
        st.button("← Back to Quiz", on_click=go_to, args=("quiz",))
        return

    pct           = result["score_pct"]
    b_html, msg   = _score_feedback(pct)

    _html(f"""
    <div class="glass-card">
        <h1 style="margin:0 0 .3rem">Your Results</h1>
        <div style="display:flex;align-items:center;gap:.65rem;flex-wrap:wrap">
            {b_html}
            <span style="font-size:.88rem;color:rgba(255,255,255,.65)">{msg}</span>
        </div>
    </div>
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        _html(_metric_card(f"{pct}%", "Score"))
    with col2:
        _html(_metric_card(f"{result['correct_count']} / {result['total']}", "Correct"))
    with col3:
        _html(_metric_card(str(result["incorrect_count"]), "Incorrect"))

    _html('<h2 style="font-size:1.05rem;margin:1.4rem 0 .7rem">Answer Review</h2>')

    for detail in result["details"]:
        _render_answer_detail(detail)

    _gold_rule()

    if st.button("🔄 Start a New Quiz", type="primary", use_container_width=True):
        reset_app()
        st.rerun()


def _score_feedback(pct: float) -> tuple[str, str]:
    if pct >= 80:
        return _badge("Excellent", "green"), "Outstanding performance! 🏆"
    elif pct >= 60:
        return _badge("Good", "blue"), "Solid effort — keep it up! 👍"
    elif pct >= 40:
        return _badge("Fair", "gold"), "Review the explanations below. 📚"
    else:
        return _badge("Needs Work", "red"), "Revisit the material and try again. 💪"


def _render_answer_detail(detail: dict) -> None:
    icon  = "✅" if detail["is_correct"] else "❌"
    q     = detail["question"]
    short = q[:72] + "…" if len(q) > 72 else q

    with st.expander(f"{icon}  Q{detail['number']}  —  {short}", expanded=not detail["is_correct"]):
        if detail["is_correct"]:
            st.success(f"Your answer: **{detail['selected_label']}. {detail['selected_text']}**")
        else:
            st.error(
                f"Your answer: **{detail['selected_label']}. {detail['selected_text']}**"
                if detail["selected_label"]
                else "Your answer: *(not answered)*"
            )
            st.success(f"Correct answer: **{detail['correct_label']}. {detail['correct_text']}**")

        if detail["explanation"]:
            st.markdown(f"**Explanation:** {detail['explanation']}")


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    _html(CUSTOM_CSS)
    render_sidebar()

    step = st.session_state.step
    if step == "upload":
        render_upload_step()
    elif step == "configure":
        render_configure_step()
    elif step == "quiz":
        render_quiz_step()
    elif step == "results":
        render_results_step()
    else:
        st.error(f"Unknown step: {step}")
        st.button("Reset", on_click=reset_app)


if __name__ == "__main__":
    main()
