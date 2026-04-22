"""
PokeMarket Scraper — eBay Australia sold listings
Uses requests + BeautifulSoup (no headless browser needed).
Saves aggregate results to data/prices.csv and individual sales to data/sales.json.
"""

from __future__ import annotations

import csv
import json
import os
import re
import random
import time
from datetime import datetime
from pathlib import Path
from statistics import median as calc_median

import requests
from bs4 import BeautifulSoup

# ── Pokemon TCG sets to track ────────────────────────────────────────────────

# ── Singles / Promos ──
SINGLES = [
    {"name": "Promos", "code": "PROMO", "product": "EB Games Gengar 050/088",
     "query": "gengar 050 088 eb games promo stamped sealed",
     "title_must_any": ["gengar"],
     "title_must": ["050", "eb games"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    {"name": "Promos", "code": "PROMO", "product": "Eevee SVP 173 Black Star Promo",
     "query": "eevee svp 173 black star promo pokemon",
     "title_must_any": ["eevee"],
     "title_must": ["173", "promo"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    {"name": "Promos", "code": "PROMO", "product": "Lucario VSTAR SWSH291 Black Star Promo",
     "query": "lucario vstar swsh291 black star promo pokemon",
     "title_must_any": ["lucario"],
     "title_must": ["swsh291"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "mega"]},

    {"name": "Promos", "code": "PROMO", "product": "Mega Lucario ex MEP 033 Black Star Promo",
     "query": "mega lucario ex mep 033 black star promo pokemon",
     "title_must_any": ["lucario"],
     "title_must": ["033", "mega"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    {"name": "Promos", "code": "PROMO", "product": "Riolu 010 Mega Evolution ETB Promo",
     "query": "riolu 010 mega evolution etb promo pokemon",
     "title_must_any": ["riolu"],
     "title_must": ["010", "promo"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    {"name": "Promos", "code": "PROMO", "product": "Snorlax SVP 051 Pokemon 151 ETB Promo",
     "query": "snorlax svp 051 pokemon 151 etb promo",
     "title_must_any": ["snorlax"],
     "title_must": ["051", "promo"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    {"name": "Promos", "code": "PROMO", "product": "Venusaur 13 Black Star Promo",
     "query": "venusaur 13 black star promo pokemon",
     "title_must_any": ["venusaur"],
     "title_must": ["13", "promo"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "151", "base"]},

    # ── SV03 — Obsidian Flames singles ──
    {"name": "Obsidian Flames", "code": "SV03", "product": "Cleffa IR 202/197",
     "query": "cleffa 202 197 obsidian flames illustration rare pokemon",
     "title_must_any": ["cleffa"],
     "title_must": ["202"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    # ── SV06 — Twilight Masquerade singles ──
    {"name": "Twilight Masquerade", "code": "SV06", "product": "Chansey IR 187/167",
     "query": "chansey 187 167 twilight masquerade illustration rare pokemon",
     "title_must_any": ["chansey"],
     "title_must": ["187"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    # ── SV08 — Surging Sparks singles ──
    {"name": "Surging Sparks", "code": "SV08", "product": "Ceruledge IR 197/191",
     "query": "ceruledge 197 191 surging sparks illustration rare pokemon",
     "title_must_any": ["ceruledge"],
     "title_must": ["197"],
     "title_must_not": ["lot", "bundle", "japanese", "korean"]},

    # ── SV Promo — Detective Pikachu ──
    {"name": "Promos", "code": "PROMO", "product": "Detective Pikachu 098/SV-P Japanese Promo",
     "query": "detective pikachu 098 sv-p japanese promo pokemon",
     "title_must_any": ["pikachu"],
     "title_must": ["098", "detective"],
     "title_must_not": ["lot", "bundle"]},

    {"name": "Journey Together", "code": "JT", "product": "Lillie's Clefairy ex 184/159 SIR PSA 10",
     "query": "lillie's clefairy ex 184 159 journey together psa 10",
     "title_must_any": ["lillie", "clefairy"],
     "title_must": ["184", "psa 10"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa 9", "psa 8", "psa 7", "cgc", "bgs"]},

    {"name": "Journey Together", "code": "JT", "product": "Lillie's Clefairy ex 184/159 SIR PSA 9",
     "query": "lillie's clefairy ex 184 159 journey together psa 9",
     "title_must_any": ["lillie", "clefairy"],
     "title_must": ["184", "psa 9"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa 10", "psa 8", "psa 7", "cgc", "bgs"]},

    {"name": "Journey Together", "code": "JT", "product": "Lillie's Clefairy ex 184/159 SIR Raw",
     "query": "lillie's clefairy ex 184 159 journey together SIR",
     "title_must_any": ["lillie", "clefairy"],
     "title_must": ["184"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa", "cgc", "bgs", "beckett", "graded"]},

    # ── SV10 — Team Rocket's Mewtwo ex 231/182 SIR ──
    {"name": "Destined Rivals", "code": "SV10", "product": "Team Rocket's Mewtwo ex 231/182 SIR PSA 10",
     "query": "team rocket's mewtwo ex 231 182 psa 10",
     "title_must_any": ["mewtwo", "rocket"],
     "title_must": ["231", "psa 10"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa 9", "psa 8", "psa 7", "cgc", "bgs"]},

    {"name": "Destined Rivals", "code": "SV10", "product": "Team Rocket's Mewtwo ex 231/182 SIR PSA 9",
     "query": "team rocket's mewtwo ex 231 182 psa 9",
     "title_must_any": ["mewtwo", "rocket"],
     "title_must": ["231", "psa 9"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa 10", "psa 8", "psa 7", "cgc", "bgs"]},

    {"name": "Destined Rivals", "code": "SV10", "product": "Team Rocket's Mewtwo ex 231/182 SIR Raw",
     "query": "team rocket's mewtwo ex 231 182 SIR",
     "title_must_any": ["mewtwo", "rocket"],
     "title_must": ["231"],
     "title_must_not": ["lot", "bundle", "japanese", "korean", "psa", "cgc", "bgs", "beckett", "graded"]},
]

# Cross-set exclusions: each set must exclude the other set names from titles
_OTHER_SETS = {
    "ME01": ["phantasmal flames", "ascended heroes", "perfect order", "chaos rising"],
    "ME02": ["ascended heroes", "perfect order", "chaos rising"],
    "ME2.5": ["phantasmal flames", "perfect order", "chaos rising"],
    "ME03": ["phantasmal flames", "ascended heroes", "chaos rising"],
}

_SV_OTHER_SETS = {
    "SV01": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV02": ["obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV03": ["paldea", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV04": ["paldea", "obsidian", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV05": ["paldea", "obsidian", "paradox", "twilight", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV06": ["paldea", "obsidian", "paradox", "temporal", "stellar", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV07": ["paldea", "obsidian", "paradox", "temporal", "twilight", "surging", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV08": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "fates", "151", "destined", "journey", "bolt", "flare"],
    "SV09": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "bolt", "flare"],
    "SV10": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "journey", "bolt", "flare"],
    "SV11": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "151", "destined", "journey"],
    "SV3.5": ["paldea", "obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "fates", "destined", "journey", "bolt", "flare"],
    "SV4.5": ["obsidian", "paradox", "temporal", "twilight", "stellar", "surging", "151", "destined", "journey", "bolt", "flare"],
}

SETS = [
    # ── ME01 — Mega Evolution (Sep 2025) ──
    #    title_must_any: at least one of these must appear (handles "ME01", "ME-01", "mega evolution base")
    {"name": "Mega Evolution",    "code": "ME01",  "product": "Booster Box",
     "query": "mega evolution ME01 booster box sealed",
     "title_must_any": ["me01", "me-01", "mega evolution"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _OTHER_SETS["ME01"]},

    {"name": "Mega Evolution",    "code": "ME01",  "product": "Enhanced Booster Box",
     "query": "mega evolution ME01 enhanced booster box sealed",
     "title_must_any": ["me01", "me-01", "mega evolution"],
     "title_must": ["enhanced"],
     "title_must_not": ["bundle"] + _OTHER_SETS["ME01"]},

    {"name": "Mega Evolution",    "code": "ME01",  "product": "ETB",
     "query": "mega evolution ME01 elite trainer box sealed",
     "title_must_any": ["me01", "me-01", "mega evolution"],
     "title_must": ["elite trainer"],
     "title_must_not": ["pokemon centre", "pokemon center", "bundle"] + _OTHER_SETS["ME01"]},

    {"name": "Mega Evolution",    "code": "ME01",  "product": "PC ETB",
     "query": "mega evolution ME01 pokemon centre elite trainer box sealed",
     "title_must_any": ["me01", "me-01", "mega evolution"],
     "title_must": ["elite trainer"],
     "title_must_not": [] + _OTHER_SETS["ME01"]},

    {"name": "Mega Evolution",    "code": "ME01",  "product": "Booster Bundle",
     "query": "mega evolution ME01 booster bundle sealed",
     "title_must_any": ["me01", "me-01", "mega evolution"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box"] + _OTHER_SETS["ME01"]},

    # ── ME02 — Phantasmal Flames (Nov 2025) ──
    {"name": "Phantasmal Flames", "code": "ME02",  "product": "Booster Box",
     "query": "phantasmal flames booster box sealed",
     "title_must_any": ["me02", "me-02", "phantasmal flames"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _OTHER_SETS["ME02"]},

    {"name": "Phantasmal Flames", "code": "ME02",  "product": "ETB",
     "query": "phantasmal flames elite trainer box sealed",
     "title_must_any": ["me02", "me-02", "phantasmal flames"],
     "title_must": ["elite trainer"],
     "title_must_not": ["pokemon centre", "pokemon center", "bundle"] + _OTHER_SETS["ME02"]},

    {"name": "Phantasmal Flames", "code": "ME02",  "product": "PC ETB",
     "query": "phantasmal flames pokemon centre elite trainer box sealed",
     "title_must_any": ["me02", "me-02", "phantasmal flames"],
     "title_must": ["elite trainer"],
     "title_must_not": [] + _OTHER_SETS["ME02"]},

    {"name": "Phantasmal Flames", "code": "ME02",  "product": "Booster Bundle",
     "query": "phantasmal flames booster bundle sealed",
     "title_must_any": ["me02", "me-02", "phantasmal flames"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box"] + _OTHER_SETS["ME02"]},

    # ── ME2.5 — Ascended Heroes (Jan 2026) ──
    {"name": "Ascended Heroes",   "code": "ME2.5", "product": "ETB",
     "query": "ascended heroes elite trainer box sealed",
     "title_must_any": ["me2.5", "me2 5", "ascended heroes"],
     "title_must": ["elite trainer"],
     "title_must_not": ["pokemon centre", "pokemon center", "bundle"] + _OTHER_SETS["ME2.5"]},

    {"name": "Ascended Heroes",   "code": "ME2.5", "product": "PC ETB",
     "query": "ascended heroes pokemon centre elite trainer box sealed",
     "title_must_any": ["me2.5", "me2 5", "ascended heroes"],
     "title_must": ["elite trainer"],
     "title_must_not": [] + _OTHER_SETS["ME2.5"]},

    {"name": "Ascended Heroes",   "code": "ME2.5", "product": "Booster Bundle",
     "query": "ascended heroes booster bundle sealed",
     "title_must_any": ["me2.5", "me2 5", "ascended heroes"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box"] + _OTHER_SETS["ME2.5"]},

    # ── ME03 — Perfect Order (Mar 2026) ──
    {"name": "Perfect Order",     "code": "ME03",  "product": "Booster Box",
     "query": "perfect order ME03 booster box sealed",
     "title_must_any": ["me03", "me-03", "perfect order"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _OTHER_SETS["ME03"]},

    {"name": "Perfect Order",     "code": "ME03",  "product": "ETB",
     "query": "perfect order ME03 elite trainer box sealed",
     "title_must_any": ["me03", "me-03", "perfect order"],
     "title_must": ["elite trainer"],
     "title_must_not": ["pokemon centre", "pokemon center", "bundle"] + _OTHER_SETS["ME03"]},

    {"name": "Perfect Order",     "code": "ME03",  "product": "PC ETB",
     "query": "perfect order ME03 pokemon centre elite trainer box sealed",
     "title_must_any": ["me03", "me-03", "perfect order"],
     "title_must": ["elite trainer"],
     "title_must_not": [] + _OTHER_SETS["ME03"]},

    {"name": "Perfect Order",     "code": "ME03",  "product": "Booster Bundle",
     "query": "perfect order ME03 booster bundle sealed",
     "title_must_any": ["me03", "me-03", "perfect order"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box"] + _OTHER_SETS["ME03"]},

    # ── SV01 — Scarlet & Violet Base Set (Mar 2023) ──
    {"name": "Scarlet & Violet",  "code": "SV01",  "product": "Booster Box",
     "query": "pokemon scarlet violet SV01 base booster box sealed",
     "title_must_any": ["sv01", "sv 01", "sv-01", "scarlet & violet", "scarlet and violet"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV01"]},

    {"name": "Scarlet & Violet",  "code": "SV01",  "product": "ETB",
     "query": "pokemon scarlet violet SV01 base elite trainer box sealed",
     "title_must_any": ["sv01", "sv 01", "sv-01", "scarlet & violet", "scarlet and violet"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV01"]},

    # ── SV02 — Paldea Evolved (Jun 2023) ──
    {"name": "Paldea Evolved",    "code": "SV02",  "product": "Booster Box",
     "query": "pokemon paldea evolved booster box sealed",
     "title_must_any": ["sv02", "sv 02", "sv-02", "paldea evolved"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV02"]},

    {"name": "Paldea Evolved",    "code": "SV02",  "product": "ETB",
     "query": "pokemon paldea evolved elite trainer box sealed",
     "title_must_any": ["sv02", "sv 02", "sv-02", "paldea evolved"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV02"]},

    # ── SV03 — Obsidian Flames (Aug 2023) ──
    {"name": "Obsidian Flames",   "code": "SV03",  "product": "Booster Box",
     "query": "pokemon obsidian flames booster box sealed",
     "title_must_any": ["sv03", "sv 03", "sv-03", "obsidian flames"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV03"]},

    {"name": "Obsidian Flames",   "code": "SV03",  "product": "ETB",
     "query": "pokemon obsidian flames elite trainer box sealed",
     "title_must_any": ["sv03", "sv 03", "sv-03", "obsidian flames"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV03"]},

    # ── SV04 — Paradox Rift (Nov 2023) ──
    {"name": "Paradox Rift",      "code": "SV04",  "product": "Booster Box",
     "query": "pokemon paradox rift booster box sealed",
     "title_must_any": ["sv04", "sv 04", "sv-04", "paradox rift"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV04"]},

    {"name": "Paradox Rift",      "code": "SV04",  "product": "ETB",
     "query": "pokemon paradox rift elite trainer box sealed",
     "title_must_any": ["sv04", "sv 04", "sv-04", "paradox rift"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV04"]},

    # ── SV05 — Temporal Forces (Mar 2024) ──
    {"name": "Temporal Forces",   "code": "SV05",  "product": "Booster Box",
     "query": "pokemon temporal forces booster box sealed",
     "title_must_any": ["sv05", "sv 05", "sv-05", "temporal forces"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV05"]},

    {"name": "Temporal Forces",   "code": "SV05",  "product": "ETB",
     "query": "pokemon temporal forces elite trainer box sealed",
     "title_must_any": ["sv05", "sv 05", "sv-05", "temporal forces"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV05"]},

    # ── SV06 — Twilight Masquerade (May 2024) ──
    {"name": "Twilight Masquerade", "code": "SV06", "product": "Booster Box",
     "query": "pokemon twilight masquerade booster box sealed",
     "title_must_any": ["sv06", "sv 06", "sv-06", "twilight masquerade"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV06"]},

    {"name": "Twilight Masquerade", "code": "SV06", "product": "ETB",
     "query": "pokemon twilight masquerade elite trainer box sealed",
     "title_must_any": ["sv06", "sv 06", "sv-06", "twilight masquerade"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV06"]},

    # ── SV07 — Stellar Crown (Aug 2024) ──
    {"name": "Stellar Crown",    "code": "SV07",  "product": "Booster Box",
     "query": "pokemon stellar crown booster box sealed",
     "title_must_any": ["sv07", "sv 07", "sv-07", "stellar crown"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV07"]},

    {"name": "Stellar Crown",    "code": "SV07",  "product": "ETB",
     "query": "pokemon stellar crown elite trainer box sealed",
     "title_must_any": ["sv07", "sv 07", "sv-07", "stellar crown"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV07"]},

    # ── SV08 — Surging Sparks (Nov 2024) ──
    {"name": "Surging Sparks",   "code": "SV08",  "product": "Booster Box",
     "query": "pokemon surging sparks booster box sealed",
     "title_must_any": ["sv08", "sv 08", "sv-08", "surging sparks"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV08"]},

    {"name": "Surging Sparks",   "code": "SV08",  "product": "ETB",
     "query": "pokemon surging sparks elite trainer box sealed",
     "title_must_any": ["sv08", "sv 08", "sv-08", "surging sparks"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV08"]},

    # ── SV09 — Journey Together (Mar 2025) ──
    {"name": "Journey Together",  "code": "SV09",  "product": "Booster Box",
     "query": "pokemon journey together SV09 booster box sealed",
     "title_must_any": ["sv09", "sv 09", "sv-09", "journey together"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV09"]},

    {"name": "Journey Together",  "code": "SV09",  "product": "ETB",
     "query": "pokemon journey together SV09 elite trainer box sealed",
     "title_must_any": ["sv09", "sv 09", "sv-09", "journey together"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV09"]},

    # ── SV10 — Destined Rivals (Apr 2025) ──
    {"name": "Destined Rivals",   "code": "SV10",  "product": "Booster Box",
     "query": "pokemon destined rivals SV10 booster box sealed",
     "title_must_any": ["sv10", "sv 10", "sv-10", "destined rivals"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV10"]},

    {"name": "Destined Rivals",   "code": "SV10",  "product": "ETB",
     "query": "pokemon destined rivals SV10 elite trainer box sealed",
     "title_must_any": ["sv10", "sv 10", "sv-10", "destined rivals"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV10"]},

    # ── SV11 — Black Bolt & White Flare (Jun 2025) ──
    {"name": "Black Bolt & White Flare", "code": "SV11", "product": "Booster Box",
     "query": "pokemon black bolt white flare SV11 booster box sealed",
     "title_must_any": ["sv11", "sv 11", "sv-11", "black bolt", "white flare"],
     "title_must": ["booster box"],
     "title_must_not": ["enhanced", "bundle", "etb", "trainer box"] + _SV_OTHER_SETS["SV11"]},

    {"name": "Black Bolt & White Flare", "code": "SV11", "product": "ETB",
     "query": "pokemon black bolt white flare SV11 elite trainer box sealed",
     "title_must_any": ["sv11", "sv 11", "sv-11", "black bolt", "white flare"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV11"]},

    # ── SV3.5 — Pokemon 151 (Sep 2023) ──
    {"name": "Pokemon 151",      "code": "SV3.5", "product": "ETB",
     "query": "pokemon 151 elite trainer box sealed",
     "title_must_any": ["sv3.5", "sv 3.5", "151"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle"] + _SV_OTHER_SETS["SV3.5"]},

    {"name": "Pokemon 151",      "code": "SV3.5", "product": "Booster Bundle",
     "query": "pokemon 151 booster bundle sealed",
     "title_must_any": ["sv3.5", "sv 3.5", "151"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box", "elite trainer", "trainer box"] + _SV_OTHER_SETS["SV3.5"]},

    # ── SV4.5 — Paldean Fates (Jan 2024) ──
    {"name": "Paldean Fates",    "code": "SV4.5", "product": "ETB",
     "query": "pokemon paldean fates elite trainer box sealed",
     "title_must_any": ["sv4.5", "sv 4.5", "paldean fates"],
     "title_must": ["elite trainer"],
     "title_must_not": ["bundle", "evolved"] + _SV_OTHER_SETS["SV4.5"]},

    {"name": "Paldean Fates",    "code": "SV4.5", "product": "Booster Bundle",
     "query": "pokemon paldean fates booster bundle sealed",
     "title_must_any": ["sv4.5", "sv 4.5", "paldean fates"],
     "title_must": ["bundle"],
     "title_must_not": ["booster box", "elite trainer", "trainer box", "evolved"] + _SV_OTHER_SETS["SV4.5"]},
]

# ── Helpers ───────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


MAX_PAGES = 3  # Scrape up to 3 pages per product (eBay shows ~60 cards/page)


def build_url(query: str, sold: bool = True, page: int = 1, location: str = "au") -> str:
    """Build an eBay AU search URL.

    ``location`` selects the seller-location filter:
      * ``"au"`` — Australia only (default; LH_PrefLoc=1)
      * ``"au_jp"`` — Australia + Japan via eBay's multi-country filter
    """
    q = query.replace(" ", "+")
    page_param = f"&_pgn={page}" if page > 1 else ""

    if location == "au_jp":
        # AU + JP: explicit located-in country filter. Country IDs: AU=15, JP=101.
        loc_param = "&LH_PrefLoc=99&_salic=1%2C15%2C101"
    else:
        loc_param = "&LH_PrefLoc=1"

    if sold:
        return (
            f"https://www.ebay.com.au/sch/i.html?_nkw={q}"
            f"&LH_Sold=1&LH_Complete=1{loc_param}&_sop=13{page_param}"
        )
    else:
        # Active listings, sorted by price + shipping (lowest first)
        return (
            f"https://www.ebay.com.au/sch/i.html?_nkw={q}"
            f"{loc_param}&LH_BIN=1&_sop=15{page_param}"
        )


def parse_price(text: str):
    """Extract a numeric AUD price from eBay price text."""
    text = text.replace(",", "").replace("AU $", "").replace("A $", "").strip()
    match = re.search(r"[\d]+\.?\d*", text)
    return float(match.group()) if match else None


def filter_outliers(listings: list[dict]) -> list[dict]:
    """Remove statistical outliers using IQR method."""
    if len(listings) < 4:
        return listings

    prices = sorted(l["price"] for l in listings)
    q1 = prices[len(prices) // 4]
    q3 = prices[3 * len(prices) // 4]
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [l for l in listings if lower <= l["price"] <= upper]


def get_session() -> requests.Session:
    """Create a requests session with realistic browser headers."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-AU,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    })
    return s


# ── Scraper ───────────────────────────────────────────────────────────────────

def _parse_page(soup: BeautifulSoup, set_info: dict, sold: bool) -> list[dict]:
    """Parse one page of eBay search results and return validated listings."""
    cards = soup.select(".s-card")
    use_new_layout = len(cards) > 0
    if not use_new_layout:
        cards = soup.select(".s-item")

    listings: list[dict] = []

    for card in cards:
        if use_new_layout:
            title_el = card.select_one(".s-card__title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if "shop on ebay" in title.lower():
                continue

            price_el = card.select_one(".s-card__price")
            if not price_el:
                continue
            price_text = price_el.get_text(strip=True)

            link_el = card.select_one("a[href*='ebay.com']") or card.select_one("a")
            listing_url = link_el["href"] if link_el and link_el.get("href") else ""

            # Get sold date (e.g. "Sold  1 Apr 2026") or listing date
            sold_date = ""
            caption_el = card.select_one(".s-card__caption")
            if caption_el:
                caption_text = caption_el.get_text(strip=True)
                date_match = re.search(r'(\d{1,2}\s+\w{3}\s+\d{4})', caption_text)
                if date_match:
                    if sold:
                        sold_date = date_match.group(1)

            # Seller info — only available in sold search results
            seller_name = ""
            seller_feedback = ""
            secondary_el = card.select_one(".su-card-container__attributes__secondary")
            if secondary_el:
                sec_text = secondary_el.get_text(" ", strip=True)
                fm = re.search(r'\((\d[\d,]*)\)', sec_text)
                if fm:
                    seller_feedback = fm.group(1).replace(",", "")
                nm = re.match(r'^(\S+)', sec_text.strip())
                if nm and nm.group(1).lower() not in {"sponsored", "new", "listing", "ebay"}:
                    seller_name = nm.group(1)

            # Check seller location. By default we keep only AU sellers;
            # JP-allowing sets also accept Japan-based sellers.
            location = ""
            for row in card.select(".s-card__attribute-row"):
                row_text = row.get_text(strip=True)
                if row_text.startswith("from "):
                    location = row_text
                    break
            if location:
                loc_lower = location.lower()
                allowed = ["australia"]
                if set_info.get("allow_japanese", False):
                    allowed.append("japan")
                if not any(a in loc_lower for a in allowed):
                    continue
        else:
            title_el = card.select_one(".s-item__title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if "shop on ebay" in title.lower():
                continue

            price_el = card.select_one(".s-item__price")
            if not price_el:
                continue
            price_text = price_el.get_text(strip=True)

            link_el = card.select_one(".s-item__link")
            listing_url = link_el["href"] if link_el and link_el.get("href") else ""
            sold_date = ""
            seller_name = ""
            seller_feedback = ""

            location_el = card.select_one(".s-item__location")
            if location_el:
                loc_text = location_el.get_text(strip=True).lower()
                if loc_text and "australia" not in loc_text:
                    continue

        # Skip price ranges like "$100.00 to $200.00"
        if "to" in price_text.lower():
            continue

        # Only include AUD prices
        if "AU" not in price_text and "A $" not in price_text:
            continue

        # Skip multi-item lots
        title_lower = title.lower()
        if re.search(r'\b\d+\s*x\b|\bx\s*\d+\b|\blot\b|\bbulk\b|\bcase\b', title_lower):
            continue

        # Language filters — opt-out for sets that explicitly track non-English cards.
        allow_japanese = set_info.get("allow_japanese", False)
        if not allow_japanese:
            if any(kw in title_lower for kw in ["japanese", "japan", "korean", "chinese", "jp ", "jpn", "kor"]):
                continue
            if re.search(r'[\u3000-\u9fff\uac00-\ud7af]', title):
                continue
        else:
            # Still exclude Korean/Chinese when scraping Japanese-specific sets.
            if any(kw in title_lower for kw in ["korean", "chinese", " kor ", "kor "]):
                continue
            if re.search(r'[\uac00-\ud7af]', title):  # Hangul only
                continue

        # Title validation
        title_must_any = set_info.get("title_must_any", [])
        if title_must_any and not any(kw in title_lower for kw in title_must_any):
            continue
        title_must_any_2 = set_info.get("title_must_any_2", [])
        if title_must_any_2 and not any(kw in title_lower for kw in title_must_any_2):
            continue
        title_must = set_info.get("title_must", [])
        if title_must and not all(kw in title_lower for kw in title_must):
            continue
        title_must_not = set_info.get("title_must_not", [])
        if title_must_not and any(kw in title_lower for kw in title_must_not):
            continue

        price = parse_price(price_text)
        if price and 20 < price < 5000:
            clean_url = listing_url.split("?")[0] if listing_url else ""
            entry = {
                "title": title,
                "price": price,
                "url": clean_url,
            }
            if sold:
                if sold_date:
                    entry["date"] = sold_date
                if seller_name:
                    entry["seller"] = seller_name
                if seller_feedback:
                    entry["feedback"] = seller_feedback
            listings.append(entry)

    return listings


def scrape_set(session: requests.Session, set_info: dict, sold: bool = True) -> tuple[dict | None, list[dict]]:
    """Scrape sold or active listings for one Pokemon set across multiple pages.
    Returns (aggregate_stats, individual_listings)."""
    mode = "sold" if sold else "active"
    print(f"  Fetching: {set_info['code']} {set_info['product']} ({mode})...", end=" ", flush=True)

    all_listings: list[dict] = []
    seen_urls: set[str] = set()

    for page in range(1, MAX_PAGES + 1):
        url = build_url(
            set_info["query"], sold=sold, page=page,
            location=set_info.get("location", "au"),
        )

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"HTTP error on page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        page_listings = _parse_page(soup, set_info, sold)

        if not page_listings:
            break  # No more results — stop pagination

        # De-duplicate by URL across pages
        new_count = 0
        for lst in page_listings:
            u = lst.get("url", "")
            if u and u in seen_urls:
                continue
            if u:
                seen_urls.add(u)
            all_listings.append(lst)
            new_count += 1

        if new_count == 0:
            break  # All duplicates — reached end of results

        # Brief pause between pages
        if page < MAX_PAGES:
            time.sleep(random.uniform(0.8, 1.8))

    if not all_listings:
        print(f"no listings found")
        return None, []

    # Filter outliers
    raw_count = len(all_listings)
    all_listings = filter_outliers(all_listings)
    outliers_removed = raw_count - len(all_listings)

    prices = [l["price"] for l in all_listings]
    avg = sum(prices) / len(prices)
    med = calc_median(prices)
    low, high = min(prices), max(prices)

    pages_fetched = min(MAX_PAGES, len(seen_urls) // 40 + 1) if seen_urls else 1
    suffix = f" ({outliers_removed} outliers removed)" if outliers_removed else ""
    print(f"{len(prices)} sales ({len(seen_urls)} unique across {pages_fetched}p) | Med: ${med:.2f} | Avg: ${avg:.2f} | Range: ${low:.2f}-${high:.2f}{suffix}")

    stats = {
        "name": set_info["name"],
        "code": set_info["code"],
        "product": set_info["product"],
        "avg": round(avg, 2),
        "median": round(med, 2),
        "low": round(low, 2),
        "high": round(high, 2),
        "count": len(prices),
    }

    return stats, all_listings


# ── Data persistence ──────────────────────────────────────────────────────────

def save_results(results: list[dict], mode: str = "sold"):
    """Save today's aggregate results to CSV, replacing any earlier scrape from the same day."""
    DATA_DIR.mkdir(exist_ok=True)
    csv_path = DATA_DIR / f"prices_{mode}.csv"
    today = datetime.now().strftime("%Y-%m-%d")
    fieldnames = ["date", "code", "name", "product", "median", "avg", "low", "high", "count"]

    existing: list[dict] = []
    if csv_path.exists():
        with open(csv_path, newline="") as f:
            existing = [row for row in csv.DictReader(f) if row["date"] != today]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)
        for r in results:
            writer.writerow({"date": today, **r})

    print(f"\n  {mode.capitalize()} data saved to {csv_path}")


def save_sales(all_sales: dict[str, list[dict]], mode: str = "sold"):
    """Save individual listings to JSON (keyed by date > product label)."""
    DATA_DIR.mkdir(exist_ok=True)
    sales_path = DATA_DIR / f"sales_{mode}.json"
    today = datetime.now().strftime("%Y-%m-%d")

    existing = {}
    if sales_path.exists():
        with open(sales_path) as f:
            existing = json.load(f)

    existing[today] = all_sales

    with open(sales_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"  Individual {mode} listings saved to {sales_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def _scrape_mode(session: requests.Session, sold: bool,
                 items: list | None = None) -> tuple[list[dict], dict[str, list[dict]]]:
    """Scrape a list of items for one mode (sold or active)."""
    if items is None:
        items = SETS + SINGLES
    mode = "sold" if sold else "active"
    results = []
    all_sales: dict[str, list[dict]] = {}

    for i, set_info in enumerate(items):
        stats, listings = scrape_set(session, set_info, sold=sold)
        if stats:
            results.append(stats)
            label = f"{set_info['code']} {set_info['product']}"
            all_sales[label] = listings
        if i < len(items) - 1:
            delay = random.uniform(1.5, 4.0)
            time.sleep(delay)

    if results:
        save_results(results, mode=mode)
        save_sales(all_sales, mode=mode)

    return results, all_sales


def _run_items(items: list, label: str = "PokeMarket") -> list[dict]:
    """Run scraper for a specific list of items."""
    print("=" * 55)
    print(f"  {label} Scraper — eBay Australia")
    print("=" * 55)

    session = get_session()

    print("\n--- SOLD LISTINGS ---")
    sold_results, _ = _scrape_mode(session, sold=True, items=items)

    time.sleep(random.uniform(3.0, 6.0))

    print("\n--- ACTIVE LISTINGS ---")
    active_results, _ = _scrape_mode(session, sold=False, items=items)

    for tag, results in [("SOLD", sold_results), ("ACTIVE", active_results)]:
        print(f"\n{'=' * 75}")
        print(f"  {tag}")
        print(f"  {'Code':<8} {'Set':<25} {'Type':<20} {'Median':>10} {'Count':>6}")
        print("-" * 75)
        for r in results:
            print(f"  {r['code']:<8} {r['name']:<25} {r['product']:<20} ${r['median']:>8.2f} {r['count']:>6}")
        print("=" * 75)

    if not sold_results and not active_results:
        print("  No data collected. eBay may be rate-limiting.")
        print("  Try again in a few minutes.")

    return sold_results + active_results


def run():
    """Scrape all Pokemon products (sealed + singles)."""
    return _run_items(SETS + SINGLES, "PokeMarket")


def run_sealed():
    """Scrape only Pokemon sealed products."""
    return _run_items(SETS, "Pokemon Sealed")


def run_singles():
    """Scrape only Pokemon singles."""
    return _run_items(SINGLES, "Pokemon Singles")


if __name__ == "__main__":
    run()
