"""
Japanese Pokemon Singles Scraper — eBay Australia PSA 10 Secret Rares.
Reuses core scraping logic from scraper.py.

Scope: Japanese-language singles only, PSA 10 only, Secret Rares only.
"""

from __future__ import annotations

import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path

from scraper import get_session, scrape_set, DATA_DIR


# ── Set definitions ──────────────────────────────────────────────────────────
#
# Each set lists its SR card names keyed by card number. The set total is
# encoded in the /NN suffix markers so titles like "111/083" match regardless
# of whether sellers use zero-padded or unpadded totals.

NINJA_SPINNER_NAMES = {
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

NIHIL_ZERO_NAMES = {
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

INFERNO_X_NAMES = {
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

MEGA_BRAVE_NAMES = {
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

MEGA_SYMPHONIA_NAMES = {
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


# ── Card builder ─────────────────────────────────────────────────────────────

_EXCLUDE_COMMON = [
    "psa 9", "psa 8", "psa 7", "psa 6",
    "cgc", "bgs", "beckett", "ace grading",
    "english", "chinese", "korean",
    "lot of", "bundle", "sealed", "booster box",
]


def _build_card(
    num: int,
    *,
    code: str,
    set_name: str,
    names: dict[int, str],
    set_total: int,
    query_prefix: str,
    set_markers: list[str],
) -> dict:
    """Generic PSA 10 SR card entry for a Japanese Pokemon set.

    ``set_markers`` must be strong enough to distinguish the set from others
    that share card numbers (e.g. Mega Brave vs Mega Symphonia both run
    64–92 with set total 63). For those we rely on the set name / code
    rather than the shared "/63" total.
    """
    padded = f"{num:03d}"
    card_name = names.get(num, "")
    product = (
        f"{card_name} #{padded} SR PSA 10" if card_name
        else f"#{padded} SR PSA 10"
    )
    return {
        "name": set_name,
        "code": code,
        "product": product,
        "query": f"{query_prefix} {padded} psa 10",
        "allow_japanese": True,
        "location": "au_jp",
        "title_must_any": [
            f"{padded}/", f"{num}/{set_total}", f"{num}/{set_total:03d}",
            f"#{num}",
        ],
        "title_must_any_2": set_markers,
        "title_must": ["psa 10"],
        "title_must_not": list(_EXCLUDE_COMMON),
    }


# ── Sets ─────────────────────────────────────────────────────────────────────

def _ninja_spinner(num: int) -> dict:
    return _build_card(
        num, code="NINJA", set_name="Ninja Spinner",
        names=NINJA_SPINNER_NAMES, set_total=83,
        query_prefix="pokemon japanese ninja spinner",
        # /83 is unique to Ninja Spinner so safe to include as a marker.
        set_markers=["ninja spinner", "/83", "/083", "m4 ", "m4-", "m4:"],
    )


def _nihil_zero(num: int) -> dict:
    return _build_card(
        num, code="NIHIL", set_name="Nihil Zero",
        names=NIHIL_ZERO_NAMES, set_total=80,
        query_prefix="pokemon japanese nihil zero",
        # /80 is shared with Inferno X, so we exclude it and rely on name/code.
        set_markers=["nihil zero", "m3 ", "m3-", "m3:", "m-3"],
    )


def _inferno_x(num: int) -> dict:
    return _build_card(
        num, code="INFX", set_name="Inferno X",
        names=INFERNO_X_NAMES, set_total=80,
        query_prefix="pokemon japanese inferno x",
        set_markers=["inferno x", "m2 ", "m2-", "m2:", "m-2"],
    )


def _mega_brave(num: int) -> dict:
    return _build_card(
        num, code="MBRAVE", set_name="Mega Brave",
        names=MEGA_BRAVE_NAMES, set_total=63,
        query_prefix="pokemon japanese mega brave",
        # /63 collides with Mega Symphonia — use name/code only.
        set_markers=["mega brave", "m1l", "m1-l", "m1 l"],
    )


def _mega_symphonia(num: int) -> dict:
    return _build_card(
        num, code="MSYMPH", set_name="Mega Symphonia",
        names=MEGA_SYMPHONIA_NAMES, set_total=63,
        query_prefix="pokemon japanese mega symphonia",
        set_markers=["mega symphonia", "m1s", "m1-s", "m1 s"],
    )


SETS = (
    [_ninja_spinner(n)   for n in range(84, 121)]  # M4  084–120
    + [_nihil_zero(n)     for n in range(81, 118)]  # M3  081–117
    + [_inferno_x(n)      for n in range(81, 117)]  # M2  081–116
    + [_mega_brave(n)     for n in range(64, 93)]   # M1L 064–092
    + [_mega_symphonia(n) for n in range(64, 93)]   # M1S 064–092
)


# ── Data persistence ─────────────────────────────────────────────────────────

def save_results(results: list[dict], mode: str = "sold"):
    DATA_DIR.mkdir(exist_ok=True)
    csv_path = DATA_DIR / f"pj_prices_{mode}.csv"
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
    DATA_DIR.mkdir(exist_ok=True)
    sales_path = DATA_DIR / f"pj_sales_{mode}.json"
    today = datetime.now().strftime("%Y-%m-%d")

    existing = {}
    if sales_path.exists():
        with open(sales_path) as f:
            existing = json.load(f)

    existing[today] = all_sales

    with open(sales_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"  Individual {mode} listings saved to {sales_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def _scrape_mode(session, sold: bool):
    mode = "sold" if sold else "active"
    results = []
    all_sales: dict[str, list[dict]] = {}

    for i, set_info in enumerate(SETS):
        stats, listings = scrape_set(session, set_info, sold=sold)
        if stats:
            results.append(stats)
            label = f"{set_info['code']} {set_info['product']}"
            all_sales[label] = listings
        if i < len(SETS) - 1:
            delay = random.uniform(1.5, 4.0)
            time.sleep(delay)

    if results:
        save_results(results, mode=mode)
        save_sales(all_sales, mode=mode)

    return results, all_sales


def run():
    print("=" * 55)
    print("  Japanese Pokemon Singles Scraper — eBay Australia")
    print("  (PSA 10 Secret Rares only)")
    print("=" * 55)

    session = get_session()

    print("\n--- SOLD LISTINGS ---")
    sold_results, _ = _scrape_mode(session, sold=True)

    time.sleep(random.uniform(3.0, 6.0))

    print("\n--- ACTIVE LISTINGS ---")
    active_results, _ = _scrape_mode(session, sold=False)

    for label, results in [("SOLD", sold_results), ("ACTIVE", active_results)]:
        print(f"\n{'=' * 75}")
        print(f"  {label}")
        print(f"  {'Code':<8} {'Set':<20} {'Card':<20} {'Median':>10} {'Count':>6}")
        print("-" * 75)
        for r in results:
            print(f"  {r['code']:<8} {r['name']:<20} {r['product']:<20} ${r['median']:>8.2f} {r['count']:>6}")
        print("=" * 75)

    if not sold_results and not active_results:
        print("  No data collected. eBay may be rate-limiting.")

    return sold_results + active_results


def run_singles():
    """Alias for run() — only singles are tracked for Pokemon JP."""
    return run()


if __name__ == "__main__":
    run()
