"""
PokeMarket Dashboard — multi-game TCG price tracker.
Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime

# ── Lazy scraper imports (only when refresh buttons are clicked) ──────────────
# This avoids ImportError on Streamlit Cloud where scraping isn't needed.

def _run_poke_sealed():
    from scraper import run_sealed
    return run_sealed()

def _run_poke_singles():
    from scraper import run_singles
    return run_singles()

def _run_op_sealed():
    from scraper_onepiece import run_sealed
    return run_sealed()

def _run_db_sealed():
    from scraper_dragonball import run_sealed
    return run_sealed()

def _run_poke_jp_singles():
    from scraper_pokemon_jp import run_singles
    return run_singles()

# Set definitions are duplicated here so app.py has zero scraper dependencies.
# Keep in sync with scraper.py / scraper_onepiece.py when adding new sets.

POKE_SETS = [
    {"code": "ME01",  "product": "Booster Box"},
    {"code": "ME01",  "product": "ETB"},
    {"code": "ME02",  "product": "Booster Box"},
    {"code": "ME02",  "product": "ETB"},
    {"code": "ME2.5", "product": "Booster Box"},
    {"code": "ME2.5", "product": "ETB"},
    {"code": "ME03",  "product": "Booster Box"},
    {"code": "ME03",  "product": "ETB"},
    {"code": "ME03",  "product": "Booster Bundle"},
    {"code": "ME03",  "product": "PC ETB"},
    {"code": "SV01",  "product": "Booster Box"},
    {"code": "SV01",  "product": "ETB"},
    {"code": "SV02",  "product": "Booster Box"},
    {"code": "SV02",  "product": "ETB"},
    {"code": "SV03",  "product": "Booster Box"},
    {"code": "SV03",  "product": "ETB"},
    {"code": "SV04",  "product": "Booster Box"},
    {"code": "SV04",  "product": "ETB"},
    {"code": "SV05",  "product": "Booster Box"},
    {"code": "SV05",  "product": "ETB"},
    {"code": "SV06",  "product": "Booster Box"},
    {"code": "SV06",  "product": "ETB"},
    {"code": "SV07",  "product": "Booster Box"},
    {"code": "SV07",  "product": "ETB"},
    {"code": "SV08",  "product": "Booster Box"},
    {"code": "SV08",  "product": "ETB"},
    {"code": "SV09",  "product": "Booster Box"},
    {"code": "SV09",  "product": "ETB"},
    {"code": "SV10",  "product": "Booster Box"},
    {"code": "SV10",  "product": "ETB"},
    {"code": "SV11",  "product": "Booster Box"},
    {"code": "SV3.5", "product": "ETB"},
    {"code": "SV3.5", "product": "Booster Bundle"},
    {"code": "SV4.5", "product": "ETB"},
    {"code": "SV4.5", "product": "Booster Bundle"},
]

POKE_SINGLES = [
    {"code": "PROMO", "product": "EB Games Gengar 050/088"},
    {"code": "PROMO", "product": "Eevee SVP 173 Black Star Promo"},
    {"code": "PROMO", "product": "Lucario VSTAR SWSH291 Black Star Promo"},
    {"code": "PROMO", "product": "Mega Lucario ex MEP 033 Black Star Promo"},
    {"code": "PROMO", "product": "Riolu 010 Mega Evolution ETB Promo"},
    {"code": "PROMO", "product": "Snorlax SVP 051 Pokemon 151 ETB Promo"},
    {"code": "PROMO", "product": "Venusaur 13 Black Star Promo"},
    {"code": "PROMO", "product": "Detective Pikachu 098/SV-P Japanese Promo"},
    {"code": "SV03",  "product": "Cleffa IR 202/197"},
    {"code": "SV06",  "product": "Chansey IR 187/167"},
    {"code": "SV08",  "product": "Ceruledge IR 197/191"},
    {"code": "JT",    "product": "Lillie's Clefairy ex 184/159 SIR PSA 10"},
    {"code": "JT",    "product": "Lillie's Clefairy ex 184/159 SIR PSA 9"},
    {"code": "JT",    "product": "Lillie's Clefairy ex 184/159 SIR Raw"},
    {"code": "SV10",  "product": "Team Rocket's Mewtwo ex 231/182 SIR PSA 10"},
    {"code": "SV10",  "product": "Team Rocket's Mewtwo ex 231/182 SIR PSA 9"},
    {"code": "SV10",  "product": "Team Rocket's Mewtwo ex 231/182 SIR Raw"},
]

OP_SETS = [
    {"code": c, "product": "Booster Box"}
    for c in ["OP-01","OP-02","OP-03","OP-04","OP-05","OP-06","OP-07","OP-08",
              "OP-09","OP-10","OP-11","OP-12","OP-13","OP-14","OP-15","OP-16",
              "EB-01","EB-02","EB-03","PRB-01","PRB-02"]
]

DB_SETS = [
    {"code": c, "product": "Booster Box"}
    for c in ["FB01","FB02","FB03","FB04","FB05","FB06","FB07","FB08","FB09","FB10","FB11",
              "SB01","SB02","ST01"]
]

_NINJA_SPINNER_NAMES = {
    84: "Chespin", 85: "Fennekin", 86: "Froakie", 87: "Frogadier",
    88: "Ampharos", 89: "Xerneas", 90: "Claydol", 91: "Crobat",
    92: "Metang", 93: "Sliggoo", 94: "Tauros", 95: "Watchog",
    96: "Beedrill ex", 97: "Mega Pyroar ex", 98: "Mega Greninja ex",
    99: "Mega Floette ex", 100: "Gourgeist ex", 101: "Cobalion ex",
    102: "Mega Dragalge ex", 103: "Cinccino ex", 104: "Energy Retrieval",
    105: "Jumbo Ice Cream", 106: "Special Red Card", 107: "Tool Scrapper",
    108: "AZ's Tranquility", 109: "Philippe", 110: "Roxie's Performance",
    111: "Emma", 112: "Surfing Beach", 113: "Prism Tower",
    114: "Mega Greninja ex", 115: "Mega Floette ex", 116: "Mega Dragalge ex",
    117: "Cinccino ex", 118: "AZ's Tranquility", 119: "Roxie's Performance",
    120: "Mega Greninja ex",
}

_NIHIL_ZERO_NAMES = {
    81: "Spewpa", 82: "Rowlet", 83: "Talonflame", 84: "Aurorus",
    85: "Dedenne", 86: "Clefairy", 87: "Espurr", 88: "Probopass",
    89: "Tyrunt", 90: "Drapion", 91: "Doublade", 92: "Raticate",
    93: "Decidueye ex", 94: "Salazzle ex", 95: "Mega Starmie ex",
    96: "Mega Clefable ex", 97: "Mega Zygarde ex", 98: "Yveltal ex",
    99: "Mega Skarmory ex", 100: "Meowth ex", 101: "Energy Swatter",
    102: "Sacred Ash", 103: "Poké Pad", 104: "Wondrous Patch",
    105: "Tarragon", 106: "Naveen", 107: "Rosa's Encouragement",
    108: "Jacinthe", 109: "Forest of Vitality", 110: "Lumiose City",
    111: "Mega Starmie ex", 112: "Mega Clefable ex", 113: "Mega Zygarde ex",
    114: "Meowth ex", 115: "Rosa's Encouragement", 116: "Jacinthe",
    117: "Mega Zygarde ex",
}

_INFERNO_X_NAMES = {
    81: "Ludicolo", 82: "Nymble", 83: "Charcadet", 84: "Dewgong",
    85: "Piplup", 86: "Yamper", 87: "Zacian", 88: "Flygon",
    89: "Toxtricity", 90: "Togedemaru", 91: "Wigglytuff", 92: "Ambipom",
    93: "Mega Heracross ex", 94: "Mega Charizard X ex", 95: "Oricorio ex",
    96: "Rotom ex", 97: "Mismagius ex", 98: "Mega Sharpedo ex",
    99: "Empoleon ex", 100: "Mega Lopunny ex", 101: "Heat Burner",
    102: "Switch", 103: "Sacred Charm", 104: "Punk Helmet",
    105: "Grimsley's Move", 106: "Dawn", 107: "Firebreather",
    108: "Battle Colosseum", 109: "Ignition Energy",
    110: "Mega Charizard X ex", 111: "Oricorio ex", 112: "Rotom ex",
    113: "Mega Sharpedo ex", 114: "Mega Lopunny ex", 115: "Dawn",
    116: "Mega Charizard X ex",
}

_MEGA_BRAVE_NAMES = {
    64: "Bulbasaur", 65: "Ivysaur", 66: "Exeggutor", 67: "Vulpix",
    68: "Riolu", 69: "Marshadow", 70: "Garganacl", 71: "Spiritomb",
    72: "Shroodle", 73: "Steelix", 74: "Spearow", 75: "Yungoos",
    76: "Mega Venusaur ex", 77: "Mega Camerupt ex", 78: "Mega Lucario ex",
    79: "Mega Absol ex", 80: "Mega Mawile ex", 81: "Premium Power Pro",
    82: "Fight Gong", 83: "Night Stretcher", 84: "Air Balloon",
    85: "Lt. Surge's Deal", 86: "Lillie's Determination",
    87: "Mega Venusaur ex", 88: "Mega Lucario ex", 89: "Mega Absol ex",
    90: "Lt. Surge's Deal", 91: "Lillie's Determination",
    92: "Mega Lucario ex",
}

_MEGA_SYMPHONIA_NAMES = {
    64: "Shuckle", 65: "Ninjask", 66: "Litleo", 67: "Snover",
    68: "Clawitzer", 69: "Inteleon", 70: "Helioptile", 71: "Alakazam",
    72: "Shedinja", 73: "Houndstone", 74: "Delibird", 75: "Stufful",
    76: "Mega Abomasnow ex", 77: "Mega Manectric ex",
    78: "Mega Gardevoir ex", 79: "Mega Latias ex",
    80: "Mega Kangaskhan ex", 81: "Buddy-Buddy Poffin", 82: "Rare Candy",
    83: "Mega Signal", 84: "Acerola's Prank", 85: "Wally's Compassion",
    86: "Mystery Garden", 87: "Mega Gardevoir ex", 88: "Mega Latias ex",
    89: "Mega Kangaskhan ex", 90: "Acerola's Prank",
    91: "Wally's Compassion", 92: "Mega Gardevoir ex",
}


def _jp_entries(code: str, names: dict) -> list[dict]:
    return [
        {"code": code,
         "product": f"{names[n]} #{n:03d} SR PSA 10"}
        for n in sorted(names.keys())
    ]


POKE_JP_SINGLES = (
    _jp_entries("NINJA",  _NINJA_SPINNER_NAMES)
    + _jp_entries("NIHIL",  _NIHIL_ZERO_NAMES)
    + _jp_entries("INFX",   _INFERNO_X_NAMES)
    + _jp_entries("MBRAVE", _MEGA_BRAVE_NAMES)
    + _jp_entries("MSYMPH", _MEGA_SYMPHONIA_NAMES)
)

DATA_DIR = Path(__file__).parent / "data"

# ── Game metadata ──────────────────────────────────────────────────────────────

POKE_SET_META = {
    "ME01":  {"name": "Mega Evolution",    "released": "Sep 2025", "color": "#d4a017"},
    "ME02":  {"name": "Phantasmal Flames", "released": "Nov 2025", "color": "#e05a2b"},
    "ME2.5": {"name": "Ascended Heroes",   "released": "Jan 2026", "color": "#6356c9"},
    "ME03":  {"name": "Perfect Order",     "released": "Mar 2026", "color": "#00a88a"},
    "PROMO": {"name": "Promos",             "released": "2026",     "color": "#c030d8"},
    "JT":    {"name": "Journey Together",  "released": "Mar 2025", "color": "#d8507a"},
    "SV10":  {"name": "Destined Rivals",   "released": "Apr 2025", "color": "#7b1fa2"},
    "SV01":  {"name": "Scarlet & Violet",  "released": "Mar 2023", "color": "#d32f2f"},
    "SV02":  {"name": "Paldea Evolved",    "released": "Jun 2023", "color": "#388e3c"},
    "SV03":  {"name": "Obsidian Flames",   "released": "Aug 2023", "color": "#e64a19"},
    "SV04":  {"name": "Paradox Rift",      "released": "Nov 2023", "color": "#8e24aa"},
    "SV05":  {"name": "Temporal Forces",   "released": "Mar 2024", "color": "#1976d2"},
    "SV06":  {"name": "Twilight Masquerade", "released": "May 2024", "color": "#00838f"},
    "SV07":  {"name": "Stellar Crown",     "released": "Aug 2024", "color": "#c6a600"},
    "SV08":  {"name": "Surging Sparks",    "released": "Nov 2024", "color": "#e65100"},
    "SV09":  {"name": "Journey Together",   "released": "Mar 2025", "color": "#5e35b1"},
    "SV11":  {"name": "Black Bolt & White Flare", "released": "Jun 2025", "color": "#37474f"},
    "SV3.5": {"name": "Pokemon 151",       "released": "Sep 2023", "color": "#c62828"},
    "SV4.5": {"name": "Paldean Fates",     "released": "Jan 2024", "color": "#546e7a"},
}

OP_SET_META = {
    "OP-01":  {"name": "Romance Dawn",             "released": "Dec 2022", "color": "#c0392b"},
    "OP-02":  {"name": "Paramount War",             "released": "Mar 2023", "color": "#2471a3"},
    "OP-03":  {"name": "Pillars of Strength",       "released": "Jun 2023", "color": "#d35400"},
    "OP-04":  {"name": "Kingdoms of Intrigue",      "released": "Sep 2023", "color": "#7d3c98"},
    "OP-05":  {"name": "Awakening of the New Era",  "released": "Dec 2023", "color": "#b7950b"},
    "OP-06":  {"name": "Wings of the Captain",      "released": "Mar 2024", "color": "#148f77"},
    "OP-07":  {"name": "500 Years in the Future",   "released": "Jun 2024", "color": "#1e8449"},
    "OP-08":  {"name": "Two Legends",               "released": "Sep 2024", "color": "#c2185b"},
    "OP-09":  {"name": "Emperors in the New World",  "released": "Dec 2024", "color": "#283593"},
    "OP-10":  {"name": "Royal Blood",               "released": "Mar 2025", "color": "#922b21"},
    "OP-11":  {"name": "A Fist of Divine Speed",    "released": "Jun 2025", "color": "#1b7a3d"},
    "OP-12":  {"name": "Legacy of the Master",      "released": "Sep 2025", "color": "#455a64"},
    "OP-13":  {"name": "Carrying on His Will",      "released": "Nov 2025", "color": "#e64a19"},
    "OP-14":  {"name": "The Azure Sea's Seven",     "released": "Jan 2026", "color": "#00838f"},
    "OP-15":  {"name": "Adventure on Kami's Island", "released": "Mar 2026", "color": "#d84315"},
    "OP-16":  {"name": "The Time of Battle",        "released": "TBA",      "color": "#546e7a"},
    "EB-01":  {"name": "Memorial Collection",       "released": "2024",     "color": "#ad1457"},
    "EB-02":  {"name": "Anime 25th Collection",     "released": "2025",     "color": "#e68a00"},
    "EB-03":  {"name": "Heroines Edition",          "released": "2025",     "color": "#c2185b"},
    "PRB-01": {"name": "Card The Best",             "released": "2024",     "color": "#8d6e32"},
    "PRB-02": {"name": "Card The Best Vol.2",       "released": "2025",     "color": "#607d8b"},
}

DB_SET_META = {
    "FB01": {"name": "Awakened Pulse",     "released": "Feb 2024", "color": "#e65100"},
    "FB02": {"name": "Blazing Aura",       "released": "Jun 2024", "color": "#d84315"},
    "FB03": {"name": "Raging Roar",        "released": "Sep 2024", "color": "#c62828"},
    "FB04": {"name": "Ultra Limit",        "released": "Dec 2024", "color": "#6a1b9a"},
    "FB05": {"name": "New Adventure",      "released": "Mar 2025", "color": "#1565c0"},
    "FB06": {"name": "Rivals Clash",       "released": "Jun 2025", "color": "#2e7d32"},
    "FB07": {"name": "Wish For Shenron",   "released": "Sep 2025", "color": "#ad1457"},
    "FB08": {"name": "Saiyan's Pride",     "released": "Dec 2025", "color": "#ef6c00"},
    "FB09": {"name": "Dual Evolution",     "released": "Mar 2026", "color": "#00838f"},
    "FB10": {"name": "Cross Force",        "released": "TBA",      "color": "#5d4037"},
    "FB11": {"name": "Brightness of Hope", "released": "TBA",      "color": "#c6a600"},
    "SB01": {"name": "Manga Booster 01",   "released": "2024",     "color": "#37474f"},
    "SB02": {"name": "Manga Booster 02",   "released": "2025",     "color": "#546e7a"},
    "ST01": {"name": "Story Booster 01",   "released": "2024",     "color": "#7b1fa2"},
}

POKE_JP_SET_META = {
    "MBRAVE": {"name": "Mega Brave",     "released": "Aug 2025", "color": "#2e7d32"},
    "MSYMPH": {"name": "Mega Symphonia", "released": "Aug 2025", "color": "#6a1b9a"},
    "INFX":   {"name": "Inferno X",      "released": "Sep 2025", "color": "#e65100"},
    "NIHIL":  {"name": "Nihil Zero",     "released": "Jan 2026", "color": "#263238"},
    "NINJA":  {"name": "Ninja Spinner",  "released": "Apr 2026", "color": "#c2185b"},
}

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PokeMarket",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Light theme styling (inspired by 35mmc.com) ─────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    /* Force light background everywhere */
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    .main,
    .stApp {
        background-color: #fafafa !important;
        color: #313131 !important;
    }

    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* Sidebar — clean white */
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e0e0e0 !important;
    }
    [data-testid="stSidebar"] * { color: #313131 !important; }
    [data-testid="stSidebar"] hr { border-color: #e0e0e0 !important; }
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSlider span { color: #555 !important; }

    /* Override dark text on main area */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    label, .stSelectbox label, .stMultiSelect label {
        color: #313131 !important;
    }

    /* Metric cards — clean white cards with subtle shadow */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: transform 0.15s, box-shadow 0.15s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    div[data-testid="stMetric"] label {
        color: #888 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #313131 !important;
        font-weight: 700 !important;
    }

    /* Header */
    .header-container {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.5rem;
    }
    p.header-title,
    .header-container .header-title {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #0693e3 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    p.header-subtitle,
    .header-container .header-subtitle {
        color: #777 !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
    }

    /* Tabs — clean underline style */
    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        color: #555 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0693e3 !important;
    }

    /* Alert cards — light style */
    .alert-card {
        border-radius: 10px;
        padding: 1rem 1.3rem;
        margin-bottom: 0.6rem;
    }
    .alert-card.buy {
        background: #f0faf0 !important;
        border: 1px solid #c8e6c9;
    }
    .alert-card.deal {
        background: #fff8f0 !important;
        border: 1px solid #ffe0b2;
    }
    .alert-card h4 {
        margin: 0 0 0.25rem 0;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .alert-card.buy h4 { color: #2e7d32 !important; }
    .alert-card.deal h4 { color: #e65100 !important; }
    .alert-card p { margin: 0; color: #666 !important; font-size: 0.88rem; }
    .alert-card strong { color: #313131 !important; }

    /* Section headers */
    .section-label {
        color: #888;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Sticky filter bar */
    .sticky-filter-bar {
        position: sticky !important;
        top: 0px !important;
        z-index: 999 !important;
        background: #fafafa !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }

    /* Pills / segmented control */
    div[data-testid="stPills"] button {
        border-radius: 20px !important;
        font-size: 0.82rem !important;
        padding: 0.3rem 0.9rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 10px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    /* DataFrames — clean white */
    [data-testid="stDataFrame"],
    .stDataFrame {
        background: #ffffff !important;
        border-radius: 8px;
    }

    /* Expander headers */
    [data-testid="stExpander"] summary {
        color: #313131 !important;
        font-weight: 500;
    }

    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #e3f2fd !important;
        color: #1565c0 !important;
    }

    /* Buttons */
    .stButton button[kind="primary"] {
        background-color: #0693e3 !important;
        border: none !important;
        color: white !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #0574b8 !important;
    }

    /* Footer */
    footer { color: #999 !important; }

    /* Info boxes */
    [data-testid="stAlert"] {
        background: #f5f8ff !important;
        border: 1px solid #d6e4f0 !important;
        color: #313131 !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: #ffffff !important;
        border: 1px solid #d0d0d0 !important;
        color: #313131 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Shared helpers ───────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#fafafa",
    font=dict(family="Inter, sans-serif", size=13, color="#555"),
    margin=dict(t=30, b=60, l=60, r=20),
    xaxis=dict(gridcolor="#eee", zeroline=False),
    yaxis=dict(gridcolor="#ddd", zeroline=False, showgrid=True),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", font=dict(size=11, color="#313131")),
)


def _get_last_updated() -> str:
    candidates = list(DATA_DIR.glob("*prices_*.csv"))
    latest = None
    for p in candidates:
        if p.exists():
            mtime = p.stat().st_mtime
            if latest is None or mtime > latest:
                latest = mtime
    if latest:
        dt = datetime.fromtimestamp(latest)
        return dt.strftime("%-d %b %Y at %-I:%M %p")
    return "Never"


def get_set_color(label: str, set_meta: dict) -> str:
    code = label.split(" ")[0]
    return set_meta.get(code, {}).get("color", "#0693e3")


def fmt_label(label: str, set_meta: dict) -> str:
    """Format an internal '{code} {product}' label as '{code} {name} — {product}' for display."""
    parts = label.split(" ", 1)
    code = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    name = set_meta.get(code, {}).get("name", "")
    if name and rest:
        return f"{code} {name} — {rest}"
    if name:
        return f"{code} {name}"
    return label


def load_data(mode: str, selected: list, prefix: str = "") -> pd.DataFrame | None:
    csv_path = DATA_DIR / f"{prefix}prices_{mode}.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["label"] = df["code"] + " " + df["product"]
    df = df[df["label"].isin(selected)]
    return df if not df.empty else None


def load_sales(mode: str, prefix: str = "") -> dict | None:
    sales_path = DATA_DIR / f"{prefix}sales_{mode}.json"
    if not sales_path.exists():
        return None
    with open(sales_path) as f:
        return json.load(f)


def build_date_timeline(sales_data: dict, selected_labels: list, mode: str) -> pd.DataFrame | None:
    if not sales_data:
        return None
    date_field = "date" if mode == "sold" else "listing_date"
    rows = []
    seen_urls: set[str] = set()

    for _scrape_date, day_data in sales_data.items():
        for prod_label, listings_list in day_data.items():
            if prod_label not in selected_labels:
                continue
            for lst in listings_list:
                url = lst.get("url", "")
                if url:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                date_val = lst.get(date_field, "")
                if not date_val or date_val == "New listing":
                    continue
                rows.append({"label": prod_label, "date_str": date_val, "price": lst["price"]})

    if not rows:
        return None

    tdf = pd.DataFrame(rows)
    tdf["date"] = pd.to_datetime(tdf["date_str"], format="%d %b %Y", errors="coerce")
    tdf = tdf.dropna(subset=["date"])
    if tdf.empty:
        return None

    grouped = (
        tdf.groupby(["label", "date"])["price"]
        .agg(median="median", avg="mean", count="count")
        .reset_index()
    )
    return grouped


# ── Header ───────────────────────────────────────────────────────────────────

_last_updated = _get_last_updated()

with st.container():
    st.html(f"""
    <div style="margin-bottom: 0.5rem;">
        <div style="font-size: 2.2rem; font-weight: 700; color: #0693e3; line-height: 1.2;">PokeMarket</div>
        <div style="color: #777; font-size: 0.9rem;">TCG Price Tracker &mdash; eBay Australia &mdash; Buy the Dip</div>
        <div style="color: #999; font-size: 0.75rem; margin-top: 0.2rem;">Last updated: {_last_updated}</div>
    </div>
    """)

# JS to pin the header as sticky
import streamlit.components.v1 as _components
_components.html("""
<script>
(function() {
    function applySticky() {
        const doc = window.parent.document;
        const header = doc.querySelector('.header-title');
        if (!header) return false;
        let el = header;
        while (el) {
            if (el.getAttribute && el.getAttribute('data-testid') === 'stLayoutWrapper') {
                el.classList.add('sticky-filter-bar');
                return true;
            }
            el = el.parentElement;
        }
        return false;
    }
    if (!applySticky()) {
        const obs = new MutationObserver(() => { if (applySticky()) obs.disconnect(); });
        obs.observe(window.parent.document.body, {childList: true, subtree: true});
        setTimeout(() => obs.disconnect(), 10000);
    }
})();
</script>
""", height=0)

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Controls")
    st.markdown("---")

    price_metric = st.segmented_control(
        "Price metric",
        options=["median", "avg"],
        default="median",
        format_func=lambda x: "Median" if x == "median" else "Average",
        selection_mode="single",
    )
    if not price_metric:
        price_metric = "median"

    st.markdown("---")
    st.markdown('<p class="section-label">Dip detection</p>', unsafe_allow_html=True)
    rolling_window = st.slider("Rolling avg window (days)", 3, 30, 7)
    dip_threshold = st.slider("Dip threshold (%)", 1, 25, 5,
                               help="Alert when price drops this % below rolling average")

    st.markdown("---")

    def _build_export_csv() -> str:
        rows = []
        for prefix, game in [("", "Pokemon"), ("op_", "One Piece"),
                              ("db_", "Dragon Ball"), ("pj_", "Pokemon JP")]:
            for mode in ("sold", "active"):
                csv_path = DATA_DIR / f"{prefix}prices_{mode}.csv"
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    df.insert(0, "game", game)
                    df.insert(1, "mode", mode)
                    rows.append(df)
        if rows:
            return pd.concat(rows, ignore_index=True).to_csv(index=False)
        return ""

    csv_data = _build_export_csv()
    if csv_data:
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"pokemarket_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ── Panel renderer ───────────────────────────────────────────────────────────

def render_panel(df: pd.DataFrame, sales_data: dict | None, mode: str,
                 selected: list, set_meta: dict, game_key: str, data_prefix: str):
    metric_label = "Median" if price_metric == "median" else "Average"
    mode_label = "Sold" if mode == "sold" else "Active"

    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].sort_values(price_metric, ascending=False)

    # Metrics
    cols = st.columns(4)
    with cols[0]:
        st.metric("Products", len(latest))
    with cols[1]:
        st.metric("Total sales" if mode == "sold" else "Total listings", int(latest["count"].sum()))
    with cols[2]:
        if not latest.empty:
            top = latest.iloc[0]
            st.metric("Highest", f"${top[price_metric]:.2f}",
                      help=f"{top['code']} {top['product']}")
    with cols[3]:
        if not latest.empty:
            bot = latest.iloc[-1]
            st.metric("Lowest", f"${bot[price_metric]:.2f}",
                      help=f"{bot['code']} {bot['product']}")

    # Deals (active tab only)
    if mode == "active":
        sold_df = load_data("sold", selected, data_prefix)
        if sold_df is not None:
            sold_latest = sold_df[sold_df["date"] == sold_df["date"].max()]

            # Build lookup: product label -> cheapest listing URL
            cheapest_listings: dict[str, list[dict]] = {}
            if sales_data:
                latest_sales_date = max(sales_data.keys()) if sales_data else None
                if latest_sales_date and sales_data[latest_sales_date]:
                    for prod_label, listings_list in sales_data[latest_sales_date].items():
                        if listings_list:
                            sorted_listings = sorted(listings_list, key=lambda l: l["price"])
                            cheapest_listings[prod_label] = sorted_listings

            deals = []
            for _, row in latest.iterrows():
                sold_match = sold_latest[sold_latest["label"] == row["label"]]
                if sold_match.empty:
                    continue
                sold_price = sold_match.iloc[0][price_metric]
                active_price = row[price_metric]
                if sold_price > 0 and active_price < sold_price:
                    pct = ((sold_price - active_price) / sold_price) * 100
                    if pct >= 3:
                        top_listings = cheapest_listings.get(row["label"], [])[:3]
                        deals.append((row["label"], active_price, sold_price, pct, top_listings))

            if deals:
                st.markdown("")
                for label, ap, sp, pct, top_links in sorted(deals, key=lambda x: -x[3]):
                    links_html = ""
                    if top_links:
                        link_items = []
                        for lst in top_links:
                            url = lst.get("url", "")
                            price = lst.get("price", 0)
                            if url:
                                link_items.append(
                                    f'<a href="{url}" target="_blank" '
                                    f'style="color:#0693e3; text-decoration:none; font-size:0.82rem;">'
                                    f'${price:.2f} &rarr;</a>'
                                )
                        if link_items:
                            links_html = (
                                '<p style="margin:0.3rem 0 0 0;">'
                                + " &nbsp;&bull;&nbsp; ".join(link_items)
                                + '</p>'
                            )

                    st.markdown(f"""
                    <div class="alert-card deal">
                        <h4>DEAL: {fmt_label(label, set_meta)}</h4>
                        <p>Active: <strong>${ap:.2f}</strong> &nbsp;&bull;&nbsp;
                        Sold: <strong>${sp:.2f}</strong> &nbsp;&bull;&nbsp;
                        <strong>{pct:.1f}% below sold value</strong></p>
                        {links_html}
                    </div>
                    """, unsafe_allow_html=True)

    # Dip alerts (sold tab only)
    if mode == "sold" and df["date"].nunique() >= rolling_window:
        dips = []
        for label in df["label"].unique():
            prod_df = df[df["label"] == label].sort_values("date").set_index("date")
            if len(prod_df) < rolling_window:
                continue
            prod_df["ra"] = prod_df[price_metric].rolling(rolling_window, min_periods=rolling_window).mean()
            lp = prod_df[price_metric].iloc[-1]
            la = prod_df["ra"].iloc[-1]
            if pd.notna(la) and la > 0:
                pct = ((la - lp) / la) * 100
                if pct >= dip_threshold:
                    dips.append((label, lp, la, pct))

        if dips:
            st.markdown("")
            for label, lp, la, pct in sorted(dips, key=lambda x: -x[3]):
                st.markdown(f"""
                <div class="alert-card buy">
                    <h4>BUY SIGNAL: {fmt_label(label, set_meta)}</h4>
                    <p>Current: <strong>${lp:.2f}</strong> &nbsp;&bull;&nbsp;
                    {rolling_window}d avg: <strong>${la:.2f}</strong> &nbsp;&bull;&nbsp;
                    <strong>{pct:.1f}% below average</strong></p>
                </div>
                """, unsafe_allow_html=True)

    # Bar chart
    st.markdown("")
    bar_data = latest[["label", price_metric]].sort_values(price_metric, ascending=False).copy()
    bar_data["color"] = bar_data["label"].apply(lambda l: get_set_color(l, set_meta))
    bar_data["display"] = bar_data["label"].apply(lambda l: fmt_label(l, set_meta))

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=bar_data["display"],
        y=bar_data[price_metric],
        text=bar_data[price_metric].apply(lambda v: f"${v:.0f}"),
        textposition="outside",
        textfont=dict(color="#313131"),
        marker=dict(
            color=bar_data["color"],
            line=dict(width=0),
            cornerradius=6,
        ),
        hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>",
    ))
    fig_bar.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="",
        yaxis_title=f"{metric_label} (AUD)",
        xaxis_tickangle=-30,
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{game_key}_{mode}")

    # Date-based price timeline
    timeline_df = build_date_timeline(sales_data, selected, mode)
    if timeline_df is not None and not timeline_df.empty:
        st.markdown(
            f'<p class="section-label">{"Sold" if mode == "sold" else "Listing"} price timeline — by individual date</p>',
            unsafe_allow_html=True
        )
        fig_timeline = go.Figure()
        for label in sorted(timeline_df["label"].unique()):
            prod_data = timeline_df[timeline_df["label"] == label].sort_values("date").reset_index(drop=True)
            color = get_set_color(label, set_meta)
            metric_col = price_metric

            # Only label up to 4 key points: first, last, highest, lowest
            key_indices = set()
            if len(prod_data) > 0:
                key_indices.add(0)                                    # first
                key_indices.add(len(prod_data) - 1)                   # last
                key_indices.add(int(prod_data[metric_col].idxmax()))   # highest
                key_indices.add(int(prod_data[metric_col].idxmin()))   # lowest
            text_labels = [
                f"${v:.0f}" if i in key_indices else ""
                for i, v in enumerate(prod_data[metric_col])
            ]

            display_label = fmt_label(label, set_meta)
            fig_timeline.add_trace(go.Scatter(
                x=prod_data["date"],
                y=prod_data[metric_col],
                name=display_label,
                mode="lines+markers+text",
                text=text_labels,
                textposition="top center",
                textfont=dict(size=9, color=color),
                line=dict(width=2.5, color=color, shape="spline", smoothing=1.2),
                marker=dict(
                    size=prod_data["count"].clip(upper=12) + 4,
                    color=color,
                    opacity=0.85,
                    line=dict(width=1, color="rgba(255,255,255,0.6)"),
                ),
                customdata=prod_data[["count"]].values,
                hovertemplate=(
                    f"<b>{display_label}</b><br>"
                    "%{x|%d %b %Y}<br>"
                    f"Price: $%{{y:.2f}}<br>"
                    "Listings on day: %{customdata[0]}<extra></extra>"
                ),
            ))
        timeline_layout = {**PLOTLY_LAYOUT}
        timeline_layout["xaxis"] = dict(
            gridcolor="#eee",
            zeroline=False,
            tickformat="%d %b",
        )
        timeline_layout["yaxis"] = dict(
            gridcolor="#ccc",
            gridwidth=1,
            griddash="dot",
            zeroline=False,
            tickprefix="$",
            showgrid=True,
        )
        fig_timeline.update_layout(
            **timeline_layout,
            xaxis_title="",
            yaxis_title=f"{metric_label} price (AUD)",
            yaxis2=dict(
                overlaying="y",
                side="right",
                showgrid=False,
                tickprefix="$",
                matches="y",
            ),
            hovermode="closest",
            height=430,
        )
        # Add invisible trace to activate the right y-axis
        fig_timeline.add_trace(go.Scatter(
            x=[None], y=[None], yaxis="y2", showlegend=False,
        ))
        st.plotly_chart(fig_timeline, use_container_width=True, key=f"timeline_{game_key}_{mode}")
    else:
        if mode == "sold":
            st.info("Sold date timeline will appear once listings with individual dates have been scraped.")

    # Snapshot trend (if multiple scrape dates)
    if df["date"].nunique() > 1:
        with st.expander("Snapshot trend — price by scrape date", expanded=False):
            pivot = df.pivot_table(index="date", columns="label", values=price_metric)
            colors = [get_set_color(c, set_meta) for c in pivot.columns]

            fig_line = go.Figure()
            for i, col in enumerate(pivot.columns):
                disp = fmt_label(col, set_meta)
                fig_line.add_trace(go.Scatter(
                    x=pivot.index,
                    y=pivot[col],
                    name=disp,
                    mode="lines+markers",
                    line=dict(width=2.5, color=colors[i], shape="spline", smoothing=1.2),
                    marker=dict(size=6),
                    hovertemplate=f"{disp}<br>" + "%{x|%d %b}<br>$%{y:.2f}<extra></extra>",
                ))
            fig_line.update_layout(
                **PLOTLY_LAYOUT,
                xaxis_title="",
                yaxis_title=f"{metric_label} (AUD)",
                hovermode="x unified",
                height=380,
            )
            st.plotly_chart(fig_line, use_container_width=True, key=f"line_{game_key}_{mode}")

    # Volatility table (sold only)
    if mode == "sold" and df["date"].nunique() > 1:
        with st.expander("Volatility & day-over-day change", expanded=False):
            vol_rows = []
            for label in df["label"].unique():
                prod_df = df[df["label"] == label].sort_values("date")
                if len(prod_df) < 2:
                    continue
                prices = prod_df[price_metric]
                current = prices.iloc[-1]
                prev = prices.iloc[-2]
                day_change = ((current - prev) / prev) * 100 if prev else 0
                std_dev = prices.std()
                volatility = (std_dev / prices.mean()) * 100 if prices.mean() else 0
                vol_rows.append({
                    "Product": fmt_label(label, set_meta),
                    "Current ($)": current,
                    "Prev ($)": prev,
                    "Change (%)": round(day_change, 1),
                    "Low ($)": prices.min(),
                    "High ($)": prices.max(),
                    "Vol (%)": round(volatility, 1),
                })
            if vol_rows:
                vol_df = pd.DataFrame(vol_rows)
                st.dataframe(
                    vol_df.style.format({
                        "Current ($)": "${:.2f}", "Prev ($)": "${:.2f}",
                        "Change (%)": "{:+.1f}%", "Low ($)": "${:.2f}",
                        "High ($)": "${:.2f}", "Vol (%)": "{:.1f}%",
                    }).map(
                        lambda v: "color: #2e7d32" if isinstance(v, (int, float)) and v < 0 else
                                  "color: #c62828" if isinstance(v, (int, float)) and v > 0 else "",
                        subset=["Change (%)"],
                    ),
                    use_container_width=True, hide_index=True,
                )

    # Detailed breakdown
    with st.expander(f"Detailed breakdown — all {mode_label.lower()} data", expanded=True):
        display_df = latest[["code", "name", "product", "median", "avg", "low", "high", "count"]].reset_index(drop=True)
        count_label = "Sales" if mode == "sold" else "Listings"
        display_df.columns = ["Code", "Set", "Product", "Median ($)", "Avg ($)", "Low ($)", "High ($)", count_label]
        st.dataframe(
            display_df.style.format({
                "Median ($)": "${:.2f}", "Avg ($)": "${:.2f}",
                "Low ($)": "${:.2f}", "High ($)": "${:.2f}",
            }),
            use_container_width=True, hide_index=True,
        )

    # Individual listings
    with st.expander(f"Individual {mode_label.lower()} listings — click any column header to sort", expanded=False):
        if sales_data:
            latest_sales_date = max(sales_data.keys()) if sales_data else None
            if latest_sales_date and sales_data[latest_sales_date]:
                day_sales = sales_data[latest_sales_date]
                available = sorted([p for p in day_sales.keys() if p in selected])
                if available:
                    pick = st.selectbox("Product", options=available, key=f"sales_{game_key}_{mode}",
                                        label_visibility="collapsed",
                                        format_func=lambda l: fmt_label(l, set_meta))
                    if pick and pick in day_sales:
                        listings = day_sales[pick]
                        if listings:
                            df_rows = []
                            for lst in listings:
                                row: dict = {
                                    "Title": lst["title"].replace("Opens in a new window or tab", "").strip(),
                                    "Price (AUD)": lst["price"],
                                    "Link": lst.get("url", ""),
                                }
                                if mode == "sold":
                                    row["Sold"] = lst.get("date", "—")
                                    row["Seller"] = lst.get("seller", "—")
                                    row["Feedback"] = lst.get("feedback", "—")
                                df_rows.append(row)

                            list_df = pd.DataFrame(df_rows).sort_values("Price (AUD)")
                            if "Sold" in list_df.columns:
                                list_df["Sold"] = pd.to_datetime(list_df["Sold"], format="%d %b %Y", errors="coerce")
                            if "Feedback" in list_df.columns:
                                list_df["Feedback"] = pd.to_numeric(list_df["Feedback"], errors="coerce").fillna(0).astype(int)
                            col_config: dict = {
                                "Price (AUD)": st.column_config.NumberColumn(
                                    "Price (AUD)", format="$%.2f"
                                ),
                                "Link": st.column_config.LinkColumn(
                                    "eBay Link", display_text="View listing →"
                                ),
                            }
                            if mode == "sold" and "Sold" in list_df.columns:
                                col_config["Sold"] = st.column_config.DateColumn(
                                    "Sold", format="D MMM YYYY"
                                )
                            if mode == "sold" and "Feedback" in list_df.columns:
                                col_config["Feedback"] = st.column_config.NumberColumn(
                                    "Feedback", format="%d"
                                )

                            st.dataframe(
                                list_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config=col_config,
                            )
                            st.caption(f"{len(listings)} listings from {latest_sales_date}")
                        else:
                            st.info("No listings for this product.")
            else:
                st.info("No listing data yet.")
        else:
            st.info("No listing data yet. Click Refresh in the sidebar.")


# ── Category definitions ─────────────────────────────────────────────────────

# Pokemon sealed categories (booster boxes, ETBs, bundles)
POKE_SEALED_CODES = ["ME01", "ME02", "ME2.5", "ME03",
                     "SV01", "SV02", "SV03", "SV04", "SV05", "SV06", "SV07", "SV08", "SV09", "SV10", "SV11",
                     "SV3.5", "SV4.5"]

# Pokemon singles codes
POKE_SINGLES_CODES = ["PROMO", "JT", "SV10"]  # SV10 has both sealed and singles

POKE_SEALED_CATEGORIES = {
    "Scarlet & Violet": ["SV01", "SV02", "SV03", "SV04", "SV05", "SV06", "SV07", "SV08", "SV09", "SV10", "SV11"],
    "Special Sets": ["SV3.5", "SV4.5"],
    "Mega Evolution": ["ME01", "ME02", "ME2.5", "ME03"],
}

POKE_SINGLES_CATEGORIES = {
    "Promos": ["PROMO"],
    "Scarlet & Violet Sets": ["SV03", "SV06", "SV08"],
    "Journey Together": ["JT"],
    "Destined Rivals": ["SV10"],
}

OP_SEALED_CATEGORIES = {
    "Main Sets": ["OP-01", "OP-02", "OP-03", "OP-04", "OP-05", "OP-06", "OP-07",
                   "OP-08", "OP-09", "OP-10", "OP-11", "OP-12", "OP-13", "OP-14", "OP-15", "OP-16"],
    "Extra Boosters": ["EB-01", "EB-02", "EB-03"],
    "Premium Boosters": ["PRB-01", "PRB-02"],
}

OP_SINGLES_CATEGORIES = {}  # No OP singles yet

DB_SEALED_CATEGORIES = {
    "Fusion Boosters": ["FB01", "FB02", "FB03", "FB04", "FB05", "FB06",
                        "FB07", "FB08", "FB09", "FB10", "FB11"],
    "Manga Boosters": ["SB01", "SB02"],
    "Story Boosters": ["ST01"],
}

POKE_JP_SINGLES_CATEGORIES = {
    "Ninja Spinner":  ["NINJA"],
    "Nihil Zero":     ["NIHIL"],
    "Inferno X":      ["INFX"],
    "Mega Brave":     ["MBRAVE"],
    "Mega Symphonia": ["MSYMPH"],
}


# ── Wishlist persistence ─────────────────────────────────────────────────────
# Stored as a JSON list of "prefix|label" strings in data/wishlist.json.
# `prefix` maps back to the CSV file the item lives in; `label` is the raw
# "<code> <product>" string used as the internal key throughout the app.

WISHLIST_PATH = DATA_DIR / "wishlist.json"

# Map each data prefix to its display name + metadata needed by the Wishlist tab.
PREFIX_META = {
    "":    {"game": "Pokemon",     "set_meta": POKE_SET_META},
    "pj_": {"game": "Pokemon JP",  "set_meta": POKE_JP_SET_META},
    "op_": {"game": "One Piece",   "set_meta": OP_SET_META},
    "db_": {"game": "Dragon Ball", "set_meta": DB_SET_META},
}


def _wishlist_key(prefix: str, label: str) -> str:
    return f"{prefix}|{label}"


def _wishlist_split(key: str) -> tuple[str, str]:
    prefix, _, label = key.partition("|")
    return prefix, label


def load_wishlist() -> set[str]:
    if not WISHLIST_PATH.exists():
        return set()
    try:
        with open(WISHLIST_PATH) as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_wishlist(items: set[str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with open(WISHLIST_PATH, "w") as f:
        json.dump(sorted(items), f, indent=2)


def wishlist_multiselect(data_prefix: str, set_meta: dict, all_labels: list[str],
                         game_key: str) -> None:
    """Render a multiselect at the top of a tab that adds/removes products
    from the wishlist. Persists to disk on any change."""
    if not all_labels:
        return

    wishlist = load_wishlist()
    # Only show labels from this tab in both the options and the default.
    options = sorted(all_labels, key=lambda l: fmt_label(l, set_meta))
    label_to_display = {l: fmt_label(l, set_meta) for l in options}
    current = [l for l in options if _wishlist_key(data_prefix, l) in wishlist]

    with st.expander(f"⭐ Wishlist ({len(current)} from this tab)", expanded=False):
        st.caption("Pick any products to add to your Wishlist tab. "
                   "Remove a tag to un-star.")
        picked = st.multiselect(
            "Wishlist",
            options=options,
            default=current,
            format_func=lambda l: label_to_display[l],
            key=f"{game_key}_wishlist_picker",
            label_visibility="collapsed",
        )
        picked_set = set(picked)
        current_set = set(current)
        if picked_set != current_set:
            # Diff against the full wishlist (leave other tabs' items alone).
            new_wishlist = set(wishlist)
            for l in options:
                k = _wishlist_key(data_prefix, l)
                if l in picked_set:
                    new_wishlist.add(k)
                else:
                    new_wishlist.discard(k)
            save_wishlist(new_wishlist)
            st.rerun()


# ── Game tab renderer ────────────────────────────────────────────────────────

def render_game(game_key: str, set_meta: dict, all_items: list, data_prefix: str,
                categories: dict | None = None, refresh_fn=None, refresh_label: str = "Refresh"):
    # ── Refresh button ──
    if refresh_fn:
        col_ref, col_space = st.columns([1, 5])
        with col_ref:
            if st.button(f"🔄 {refresh_label}", key=f"{game_key}_refresh", type="primary", use_container_width=True):
                with st.spinner(f"Scraping {refresh_label}..."):
                    results = refresh_fn()
                if results:
                    st.success(f"Updated {len(results)} products!")
                    st.rerun()
                else:
                    st.error("No data — try again shortly.")

    # ── Wishlist management ──
    all_labels = [f"{it['code']} {it['product']}" for it in all_items]
    wishlist_multiselect(data_prefix, set_meta, all_labels, game_key)

    set_codes = list(set_meta.keys())
    set_options = {c: f"{c} — {set_meta[c]['name']}" for c in set_codes}

    # ── Categorised set filter ──
    if categories:
        # Select All / Deselect All
        col_btn1, col_btn2, col_spacer = st.columns([1, 1, 4])
        with col_btn1:
            if st.button("Select All", key=f"{game_key}_select_all", use_container_width=True):
                for cat_name, cat_codes in categories.items():
                    st.session_state[f"{game_key}_cat_{cat_name}"] = [
                        c for c in cat_codes if c in set_meta
                    ]
                st.rerun()
        with col_btn2:
            if st.button("Deselect All", key=f"{game_key}_deselect_all", use_container_width=True):
                for cat_name in categories:
                    st.session_state[f"{game_key}_cat_{cat_name}"] = []
                st.rerun()

        # One multiselect per category
        selected_sets = []
        num_cats = len(categories)
        cols = st.columns(num_cats)
        for i, (cat_name, cat_codes) in enumerate(categories.items()):
            valid_codes = [c for c in cat_codes if c in set_meta]
            cat_key = f"{game_key}_cat_{cat_name}"
            # Default to EMPTY on first load
            if cat_key not in st.session_state:
                st.session_state[cat_key] = []

            with cols[i]:
                chosen = st.multiselect(
                    cat_name,
                    options=valid_codes,
                    format_func=lambda c: set_options.get(c, c),
                    key=cat_key,
                )
                selected_sets.extend(chosen)
    else:
        # Fallback: simple pills (default empty)
        selected_sets = st.pills(
            "Sets", options=set_codes, default=[],
            selection_mode="multi",
            format_func=lambda c: set_options[c],
            key=f"{game_key}_sets",
        )

    # Build selected product labels
    selected = []
    for s in all_items:
        label = f"{s['code']} {s['product']}"
        if s['code'] in (selected_sets or []):
            selected.append(label)

    if not selected:
        st.info("Select one or more sets above to view price data.")
        return

    # Load data
    sold_df = load_data("sold", selected, data_prefix)
    active_df = load_data("active", selected, data_prefix)

    if sold_df is None and active_df is None:
        st.info("No data yet for the selected sets. Click the Refresh button in the sidebar to scrape eBay.")
        return

    # Sold vs Active comparison table
    if sold_df is not None and active_df is not None:
        sold_latest = sold_df[sold_df["date"] == sold_df["date"].max()]
        active_latest = active_df[active_df["date"] == active_df["date"].max()]

        merged = sold_latest[["label", price_metric]].merge(
            active_latest[["label", price_metric]],
            on="label", suffixes=("_sold", "_active"),
        )
        if not merged.empty:
            merged["discount"] = ((merged[f"{price_metric}_sold"] - merged[f"{price_metric}_active"])
                                   / merged[f"{price_metric}_sold"] * 100)
            merged = merged.sort_values("discount", ascending=False)

            comp_df = merged[["label", f"{price_metric}_sold", f"{price_metric}_active", "discount"]].copy()
            comp_df["label"] = comp_df["label"].apply(lambda l: fmt_label(l, set_meta))
            comp_df.columns = ["Product", "Sold (AUD)", "Active (AUD)", "Discount (%)"]

            def _color_discount(val):
                if not isinstance(val, (int, float)):
                    return ""
                return "color: #2e7d32; font-weight: 600" if val > 0 else (
                    "color: #c62828; font-weight: 600" if val < 0 else ""
                )

            def _fmt_discount(val):
                if not isinstance(val, (int, float)):
                    return val
                return f"+{val:.1f}%" if val > 0 else f"{val:.1f}%"

            st.dataframe(
                comp_df.style
                    .format({"Sold (AUD)": "${:.2f}", "Active (AUD)": "${:.2f}", "Discount (%)": _fmt_discount})
                    .map(_color_discount, subset=["Discount (%)"]),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Green = active listed below sold value (potential deal) | Red = active at premium over sold | Click any column header to sort")
            st.markdown("")

    # Sold / Active sub-tabs
    tab_sold, tab_active = st.tabs(["Sold Prices", "Active Listings"])

    with tab_sold:
        if sold_df is not None:
            render_panel(sold_df, load_sales("sold", data_prefix), "sold",
                        selected, set_meta, game_key, data_prefix)
        else:
            st.info("No sold data yet. Click Refresh in the sidebar.")

    with tab_active:
        if active_df is not None:
            render_panel(active_df, load_sales("active", data_prefix), "active",
                        selected, set_meta, game_key, data_prefix)
        else:
            st.info("No active listing data yet. Click Refresh in the sidebar.")


# ── Singles tab renderer (two-level: set → card) ────────────────────────────

def render_game_singles(game_key: str, set_meta: dict, all_items: list, data_prefix: str,
                        categories: dict | None = None, refresh_fn=None, refresh_label: str = "Refresh"):
    """Like render_game but with a two-level filter: set name → individual cards."""
    # ── Refresh button ──
    if refresh_fn:
        col_ref, col_space = st.columns([1, 5])
        with col_ref:
            if st.button(f"🔄 {refresh_label}", key=f"{game_key}_refresh", type="primary", use_container_width=True):
                with st.spinner(f"Scraping {refresh_label}..."):
                    results = refresh_fn()
                if results:
                    st.success(f"Updated {len(results)} products!")
                    st.rerun()
                else:
                    st.error("No data — try again shortly.")

    # ── Wishlist management ──
    all_labels = [f"{it['code']} {it['product']}" for it in all_items]
    wishlist_multiselect(data_prefix, set_meta, all_labels, game_key)

    if not categories:
        st.info("No singles categories configured yet.")
        return

    set_options = {c: f"{c} — {set_meta[c]['name']}" for c in set_meta}

    # ── Level 1: Set selector ──
    st.markdown('<p class="section-label">Select set</p>', unsafe_allow_html=True)

    # Build set-level options from categories
    all_set_codes = []
    for cat_codes in categories.values():
        all_set_codes.extend(cat_codes)

    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 4])
    with col_btn1:
        if st.button("Select All", key=f"{game_key}_select_all", use_container_width=True):
            st.session_state[f"{game_key}_sets"] = all_set_codes
            # Also select all cards for each set
            for code in all_set_codes:
                cards = [s["product"] for s in all_items if s["code"] == code]
                st.session_state[f"{game_key}_cards_{code}"] = cards
            st.rerun()
    with col_btn2:
        if st.button("Deselect All", key=f"{game_key}_deselect_all", use_container_width=True):
            st.session_state[f"{game_key}_sets"] = []
            for code in all_set_codes:
                st.session_state[f"{game_key}_cards_{code}"] = []
            st.rerun()

    if f"{game_key}_sets" not in st.session_state:
        st.session_state[f"{game_key}_sets"] = []

    selected_sets = st.multiselect(
        "Sets",
        options=all_set_codes,
        format_func=lambda c: set_options.get(c, c),
        key=f"{game_key}_sets",
        label_visibility="collapsed",
    )

    if not selected_sets:
        st.info("Select one or more sets above to view singles data.")
        return

    # ── Level 2: Card selector per set ──
    st.markdown('<p class="section-label">Select cards</p>', unsafe_allow_html=True)
    cols = st.columns(len(selected_sets))
    selected_labels = []

    for i, code in enumerate(selected_sets):
        cards_for_set = [s["product"] for s in all_items if s["code"] == code]
        card_key = f"{game_key}_cards_{code}"
        if card_key not in st.session_state:
            st.session_state[card_key] = []

        with cols[i]:
            chosen_cards = st.multiselect(
                set_options.get(code, code),
                options=cards_for_set,
                key=card_key,
            )
            for card in chosen_cards:
                selected_labels.append(f"{code} {card}")

    if not selected_labels:
        st.info("Select one or more cards above to view price data.")
        return

    # Load data
    sold_df = load_data("sold", selected_labels, data_prefix)
    active_df = load_data("active", selected_labels, data_prefix)

    if sold_df is None and active_df is None:
        st.info("No data yet for the selected cards. Click the Refresh button in the sidebar to scrape eBay.")
        return

    # Sold vs Active comparison table
    if sold_df is not None and active_df is not None:
        sold_latest = sold_df[sold_df["date"] == sold_df["date"].max()]
        active_latest = active_df[active_df["date"] == active_df["date"].max()]

        merged = sold_latest[["label", price_metric]].merge(
            active_latest[["label", price_metric]],
            on="label", suffixes=("_sold", "_active"),
        )
        if not merged.empty:
            merged["discount"] = ((merged[f"{price_metric}_sold"] - merged[f"{price_metric}_active"])
                                   / merged[f"{price_metric}_sold"] * 100)
            merged = merged.sort_values("discount", ascending=False)

            comp_df = merged[["label", f"{price_metric}_sold", f"{price_metric}_active", "discount"]].copy()
            comp_df["label"] = comp_df["label"].apply(lambda l: fmt_label(l, set_meta))
            comp_df.columns = ["Product", "Sold (AUD)", "Active (AUD)", "Discount (%)"]

            def _color_discount(val):
                if not isinstance(val, (int, float)):
                    return ""
                return "color: #2e7d32; font-weight: 600" if val > 0 else (
                    "color: #c62828; font-weight: 600" if val < 0 else ""
                )

            def _fmt_discount(val):
                if not isinstance(val, (int, float)):
                    return val
                return f"+{val:.1f}%" if val > 0 else f"{val:.1f}%"

            st.dataframe(
                comp_df.style
                    .format({"Sold (AUD)": "${:.2f}", "Active (AUD)": "${:.2f}", "Discount (%)": _fmt_discount})
                    .map(_color_discount, subset=["Discount (%)"]),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Green = active listed below sold value (potential deal) | Red = active at premium over sold")
            st.markdown("")

    # Sold / Active sub-tabs
    tab_sold, tab_active = st.tabs(["Sold Prices", "Active Listings"])

    with tab_sold:
        if sold_df is not None:
            render_panel(sold_df, load_sales("sold", data_prefix), "sold",
                        selected_labels, set_meta, game_key, data_prefix)
        else:
            st.info("No sold data yet. Click Refresh in the sidebar.")

    with tab_active:
        if active_df is not None:
            render_panel(active_df, load_sales("active", data_prefix), "active",
                        selected_labels, set_meta, game_key, data_prefix)
        else:
            st.info("No active listing data yet. Click Refresh in the sidebar.")


# ── Wishlist tab renderer ────────────────────────────────────────────────────

def render_wishlist():
    st.markdown("### ⭐ Wishlist")
    wishlist = load_wishlist()
    if not wishlist:
        st.info("Your wishlist is empty. Expand the **⭐ Wishlist** panel at the "
                "top of any tab to add products.")
        return

    # Load each prefix's latest sold + active medians once.
    latest_by_prefix: dict[str, dict[str, dict]] = {}
    for prefix in PREFIX_META:
        bucket: dict[str, dict] = {}
        for mode in ("sold", "active"):
            csv_path = DATA_DIR / f"{prefix}prices_{mode}.csv"
            if not csv_path.exists():
                continue
            df = pd.read_csv(csv_path, parse_dates=["date"])
            if df.empty:
                continue
            df["label"] = df["code"] + " " + df["product"]
            latest = df[df["date"] == df["date"].max()]
            for _, r in latest.iterrows():
                bucket.setdefault(r["label"], {})[mode] = {
                    "median": r["median"], "count": r["count"],
                }
        latest_by_prefix[prefix] = bucket

    rows = []
    for key in sorted(wishlist):
        prefix, label = _wishlist_split(key)
        if prefix not in PREFIX_META:
            continue
        meta = PREFIX_META[prefix]
        prices = latest_by_prefix.get(prefix, {}).get(label, {})
        sold = prices.get("sold", {})
        active = prices.get("active", {})

        sold_m = sold.get("median")
        active_m = active.get("median")
        discount = None
        if sold_m and active_m and sold_m > 0:
            discount = (sold_m - active_m) / sold_m * 100

        rows.append({
            "_key":    key,
            "Game":    meta["game"],
            "Product": fmt_label(label, meta["set_meta"]),
            "Sold":    sold_m,
            "Active":  active_m,
            "Δ%":      discount,
            "Active #": active.get("count"),
        })

    if not rows:
        st.info("No price data for wishlisted items yet.")
        return

    df = pd.DataFrame(rows)

    # ── Summary metrics ──
    total = len(df)
    with_prices = df["Sold"].notna().sum()
    deals = (df["Δ%"] > 0).sum()
    m1, m2, m3 = st.columns(3)
    m1.metric("Items", total)
    m2.metric("Priced", f"{with_prices}/{total}")
    m3.metric("Active < Sold", deals)

    # ── Render table with per-row remove checkbox ──
    df_display = df[["Game", "Product", "Sold", "Active", "Δ%", "Active #"]].copy()
    df_display.insert(0, "Remove", False)

    edited = st.data_editor(
        df_display,
        column_config={
            "Remove": st.column_config.CheckboxColumn(
                "Remove", help="Tick to remove from wishlist on save", width="small",
            ),
            "Sold":    st.column_config.NumberColumn("Sold (AUD)",   format="$%.2f"),
            "Active":  st.column_config.NumberColumn("Active (AUD)", format="$%.2f"),
            "Δ%":      st.column_config.NumberColumn("Discount",     format="%+.1f%%"),
            "Active #": st.column_config.NumberColumn("Active Count", format="%d"),
        },
        disabled=["Game", "Product", "Sold", "Active", "Δ%", "Active #"],
        hide_index=True,
        use_container_width=True,
        key="wishlist_editor",
    )

    to_remove = edited[edited["Remove"]].index.tolist()
    col_a, col_b = st.columns([1, 5])
    with col_a:
        if st.button("🗑  Remove ticked", type="primary",
                     disabled=len(to_remove) == 0, use_container_width=True):
            keys_to_remove = {df.iloc[i]["_key"] for i in to_remove}
            new_wishlist = wishlist - keys_to_remove
            save_wishlist(new_wishlist)
            st.rerun()
    with col_b:
        st.caption("Green = active below sold (potential deal) · Red = active above sold")


# ── Main content ─────────────────────────────────────────────────────────────

(tab_poke_sealed, tab_poke_singles, tab_poke_jp_singles,
 tab_op_sealed, tab_op_singles, tab_db_sealed, tab_wishlist) = st.tabs([
    "Pokemon Sealed", "Pokemon Singles", "Pokemon JP Singles",
    "One Piece Sealed", "One Piece Singles", "Dragon Ball Sealed",
    "⭐ Wishlist",
])

with tab_poke_sealed:
    render_game("poke_sealed", POKE_SET_META, POKE_SETS, "", POKE_SEALED_CATEGORIES,
                refresh_fn=_run_poke_sealed, refresh_label="Pokemon Sealed")

with tab_poke_singles:
    render_game_singles("poke_singles", POKE_SET_META, POKE_SINGLES, "", POKE_SINGLES_CATEGORIES,
                        refresh_fn=_run_poke_singles, refresh_label="Pokemon Singles")

with tab_poke_jp_singles:
    render_game_singles("poke_jp_singles", POKE_JP_SET_META, POKE_JP_SINGLES, "pj_",
                        POKE_JP_SINGLES_CATEGORIES,
                        refresh_fn=_run_poke_jp_singles, refresh_label="Pokemon JP Singles")

with tab_op_sealed:
    render_game("op_sealed", OP_SET_META, OP_SETS, "op_", OP_SEALED_CATEGORIES,
                refresh_fn=_run_op_sealed, refresh_label="One Piece Sealed")

with tab_op_singles:
    st.info("One Piece singles tracking coming soon. Add singles to scraper_onepiece.py to get started.")

with tab_db_sealed:
    render_game("db_sealed", DB_SET_META, DB_SETS, "db_", DB_SEALED_CATEGORIES,
                refresh_fn=_run_db_sealed, refresh_label="Dragon Ball Sealed")

with tab_wishlist:
    render_wishlist()

# ── Footer
st.markdown("---")
st.markdown(
    '<p style="color:#999; font-size:0.75rem; text-align:center;">'
    'Data sourced from eBay Australia &bull; Prices in AUD &bull; English listings only &bull; AU sellers only</p>',
    unsafe_allow_html=True,
)
