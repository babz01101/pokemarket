"""
Dragon Ball Super — Fusion World TCG Scraper — eBay Australia booster box tracker.
Reuses core scraping logic from scraper.py.
"""

from __future__ import annotations

import csv
import json
import random
import time
from datetime import datetime
from pathlib import Path

from scraper import get_session, scrape_set, DATA_DIR

# ── Dragon Ball Super Fusion World sets (English booster boxes only) ─────────

SETS = [
    # ── Main Fusion Boosters FB01–FB11 ──

    {"name": "Awakened Pulse", "code": "FB01", "product": "Booster Box",
     "query": "dragon ball super fusion world FB01 awakened pulse booster box english",
     "title_must_any": ["fb-01", "fb01", "awakened pulse"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Blazing Aura", "code": "FB02", "product": "Booster Box",
     "query": "dragon ball super fusion world FB02 blazing aura booster box english",
     "title_must_any": ["fb-02", "fb02", "blazing aura"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Raging Roar", "code": "FB03", "product": "Booster Box",
     "query": "dragon ball super fusion world FB03 raging roar booster box english",
     "title_must_any": ["fb-03", "fb03", "raging roar"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Ultra Limit", "code": "FB04", "product": "Booster Box",
     "query": "dragon ball super fusion world FB04 ultra limit booster box english",
     "title_must_any": ["fb-04", "fb04", "ultra limit"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "New Adventure", "code": "FB05", "product": "Booster Box",
     "query": "dragon ball super fusion world FB05 new adventure booster box english",
     "title_must_any": ["fb-05", "fb05", "new adventure"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Rivals Clash", "code": "FB06", "product": "Booster Box",
     "query": "dragon ball super fusion world FB06 rivals clash booster box english",
     "title_must_any": ["fb-06", "fb06", "rivals clash"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Wish For Shenron", "code": "FB07", "product": "Booster Box",
     "query": "dragon ball super fusion world FB07 wish for shenron booster box english",
     "title_must_any": ["fb-07", "fb07", "wish for shenron", "shenron"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Saiyan's Pride", "code": "FB08", "product": "Booster Box",
     "query": "dragon ball super fusion world FB08 saiyan pride booster box english",
     "title_must_any": ["fb-08", "fb08", "saiyan"],
     "title_must": ["booster box", "pride"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Dual Evolution", "code": "FB09", "product": "Booster Box",
     "query": "dragon ball super fusion world FB09 dual evolution booster box english",
     "title_must_any": ["fb-09", "fb09", "dual evolution"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Cross Force", "code": "FB10", "product": "Booster Box",
     "query": "dragon ball super fusion world FB10 cross force booster box english",
     "title_must_any": ["fb-10", "fb10", "cross force"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    {"name": "Brightness of Hope", "code": "FB11", "product": "Booster Box",
     "query": "dragon ball super fusion world FB11 brightness of hope booster box english",
     "title_must_any": ["fb-11", "fb11", "brightness of hope"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    # ── Manga Boosters ──

    {"name": "Manga Booster 01", "code": "SB01", "product": "Booster Box",
     "query": "dragon ball super fusion world SB01 manga booster box english",
     "title_must_any": ["sb-01", "sb01", "manga booster 01", "manga booster vol 1", "manga booster vol.1"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case", "sb-02", "sb02"]},

    {"name": "Manga Booster 02", "code": "SB02", "product": "Booster Box",
     "query": "dragon ball super fusion world SB02 manga booster 02 booster box english",
     "title_must_any": ["sb-02", "sb02", "manga booster 02", "manga booster vol 2", "manga booster vol.2"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter", "sleeve", "playmat", "case"]},

    # ── Story Booster ──

    {"name": "Story Booster 01", "code": "ST01", "product": "Booster Box",
     "query": "dragon ball super fusion world ST01 story booster box english",
     "title_must_any": ["st-01", "st01", "story booster 01", "story booster vol 1", "story booster vol.1"],
     "title_must": ["booster box"],
     "title_must_not": ["japanese", " jp", "starter deck", "sleeve", "playmat", "case"]},
]


# ── Data persistence ─────────────────────────────────────────────────────────

def save_results(results: list[dict], mode: str = "sold"):
    DATA_DIR.mkdir(exist_ok=True)
    csv_path = DATA_DIR / f"db_prices_{mode}.csv"
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
    sales_path = DATA_DIR / f"db_sales_{mode}.json"
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
    print("  Dragon Ball Super Fusion World Scraper — eBay Australia")
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
        print(f"  {'Code':<8} {'Set':<30} {'Type':<15} {'Median':>10} {'Count':>6}")
        print("-" * 75)
        for r in results:
            print(f"  {r['code']:<8} {r['name']:<30} {r['product']:<15} ${r['median']:>8.2f} {r['count']:>6}")
        print("=" * 75)

    if not sold_results and not active_results:
        print("  No data collected. eBay may be rate-limiting.")

    return sold_results + active_results


def run_sealed():
    """Alias for run() — Fusion World only has sealed products tracked for now."""
    return run()


if __name__ == "__main__":
    run()
