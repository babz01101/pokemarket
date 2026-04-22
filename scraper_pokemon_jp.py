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


# ── Card builders ────────────────────────────────────────────────────────────

# Ninja Spinner SR card names (084–120)
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


def _ninja_spinner_card(num: int) -> dict:
    """Build a Ninja Spinner SR PSA 10 entry for card number ``num``.

    Ninja Spinner set total is 83, so every card prints as "xxx/83"
    (or "xxx/083"). We pin identification to the set-total pattern
    rather than the word "ninja" (which matches Greninja-named cards
    in other sets like Crimson Haze).
    """
    padded = f"{num:03d}"
    card_name = NINJA_SPINNER_NAMES.get(num, "")
    product = f"{card_name} #{padded} SR PSA 10" if card_name else f"#{padded} SR PSA 10"
    return {
        "name": "Ninja Spinner",
        "code": "NINJA",
        "product": product,
        "query": f"pokemon japanese ninja spinner {padded} psa 10",
        "allow_japanese": True,
        "location": "au_jp",
        # Group 1: at least one card-number form must appear.
        "title_must_any": [f"{padded}/", f"{num}/83", f"{num}/083", f"#{num}"],
        # Group 2: a Ninja Spinner set marker must appear (excludes other
        # sets that also contain cards numbered 84-120 like Crimson Haze).
        # Accepts the phrase "ninja spinner" (never part of a single-word
        # Pokemon name like Greninja), the set total "/83" / "/083", or
        # the Japanese set code "m4" used in many listing titles.
        "title_must_any_2": ["ninja spinner", "/83", "/083", "m4 ", "m4-", "m4:"],
        # Grade must appear.
        "title_must": ["psa 10"],
        # Exclude other grades, graders, bundles, and other-language cards.
        "title_must_not": [
            "psa 9", "psa 8", "psa 7", "psa 6",
            "cgc", "bgs", "beckett", "ace grading",
            "english", "chinese", "korean",
            "lot of", "bundle", "sealed", "booster box",
        ],
    }


# ── Sets ─────────────────────────────────────────────────────────────────────

SETS = [_ninja_spinner_card(n) for n in range(84, 121)]  # 084 through 120


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
