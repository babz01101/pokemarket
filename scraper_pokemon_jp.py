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

def _ninja_spinner_card(num: int) -> dict:
    """Build a Ninja Spinner SR PSA 10 entry for card number ``num``."""
    padded = f"{num:03d}"
    return {
        "name": "Ninja Spinner",
        "code": "NINJA",
        "product": f"#{padded} SR PSA 10",
        "query": f"pokemon japanese ninja spinner {padded} psa 10",
        "allow_japanese": True,
        # At least one form of the card number must appear in the title.
        "title_must_any": [padded, f"/{num}", f"#{num}", f" {num} "],
        # Set name + grade must both appear. Require "ninja" (accepts
        # both "Ninja Spinner" and "Ninja" variants in listing titles).
        "title_must": ["psa 10", "ninja"],
        # Exclude other grades, other graders, bundles, and English cards.
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
