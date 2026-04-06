"""
One Piece TCG Scraper — eBay Australia booster box tracker.
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

# ── One Piece TCG sets to track (English booster boxes only) ─────────────────

SETS = [
    # ── Main sets OP-01 through OP-14 ──

    {"name": "Romance Dawn", "code": "OP-01", "product": "Booster Box",
     "query": "one piece OP01 romance dawn booster box english",
     "title_must_any": ["op-01", "op01", "romance dawn"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Paramount War", "code": "OP-02", "product": "Booster Box",
     "query": "one piece OP02 paramount war booster box english",
     "title_must_any": ["op-02", "op02", "paramount war", "summit war"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Pillars of Strength", "code": "OP-03", "product": "Booster Box",
     "query": "one piece OP03 pillars of strength booster box english",
     "title_must_any": ["op-03", "op03", "pillars of strength"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Kingdoms of Intrigue", "code": "OP-04", "product": "Booster Box",
     "query": "one piece OP04 kingdoms of intrigue booster box english",
     "title_must_any": ["op-04", "op04", "kingdoms of intrigue"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Awakening of the New Era", "code": "OP-05", "product": "Booster Box",
     "query": "one piece OP05 awakening new era booster box english",
     "title_must_any": ["op-05", "op05", "awakening of the new era", "new era"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Wings of the Captain", "code": "OP-06", "product": "Booster Box",
     "query": "one piece OP06 wings of the captain booster box english",
     "title_must_any": ["op-06", "op06", "wings of the captain"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "500 Years in the Future", "code": "OP-07", "product": "Booster Box",
     "query": "one piece OP07 500 years future booster box english",
     "title_must_any": ["op-07", "op07", "500 years"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Two Legends", "code": "OP-08", "product": "Booster Box",
     "query": "one piece OP08 two legends booster box english",
     "title_must_any": ["op-08", "op08", "two legends"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Emperors in the New World", "code": "OP-09", "product": "Booster Box",
     "query": "one piece OP09 emperors new world booster box english",
     "title_must_any": ["op-09", "op09", "emperors"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Royal Blood", "code": "OP-10", "product": "Booster Box",
     "query": "one piece OP10 royal blood booster box english",
     "title_must_any": ["op-10", "op10", "royal blood"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "A Fist of Divine Speed", "code": "OP-11", "product": "Booster Box",
     "query": "one piece OP11 fist divine speed booster box",
     "title_must_any": ["op-11", "op11", "divine speed"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Legacy of the Master", "code": "OP-12", "product": "Booster Box",
     "query": "one piece OP12 legacy master booster box",
     "title_must_any": ["op-12", "op12", "legacy of the master"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Carrying on His Will", "code": "OP-13", "product": "Booster Box",
     "query": "one piece OP13 carrying his will booster box",
     "title_must_any": ["op-13", "op13", "carrying on his will"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "The Azure Sea's Seven", "code": "OP-14", "product": "Booster Box",
     "query": "one piece OP14 azure sea seven booster box",
     "title_must_any": ["op-14", "op14", "azure sea"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Adventure on Kami's Island", "code": "OP-15", "product": "Booster Box",
     "query": "one piece OP15 adventure kami island booster box",
     "title_must_any": ["op-15", "op15", "kami"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "The Time of Battle", "code": "OP-16", "product": "Booster Box",
     "query": "one piece OP16 time of battle booster box",
     "title_must_any": ["op-16", "op16", "time of battle"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    # ── Extra Booster sets ──

    {"name": "Memorial Collection", "code": "EB-01", "product": "Booster Box",
     "query": "one piece EB01 memorial collection booster box",
     "title_must_any": ["eb-01", "eb01", "memorial collection"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Anime 25th Collection", "code": "EB-02", "product": "Booster Box",
     "query": "one piece EB02 anime 25th collection booster box",
     "title_must_any": ["eb-02", "eb02", "anime 25th"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    {"name": "Heroines Edition", "code": "EB-03", "product": "Booster Box",
     "query": "one piece EB03 heroines edition booster box",
     "title_must_any": ["eb-03", "eb03", "heroines"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},

    # ── Premium Booster sets ──

    {"name": "Card The Best", "code": "PRB-01", "product": "Booster Box",
     "query": "one piece PRB01 card the best booster box english",
     "title_must_any": ["prb-01", "prb01"],
     "title_must": ["booster box", "english"],
     "title_must_not": ["starter", "sleeve", "playmat", "vol.2", "vol 2", "vol2"]},

    {"name": "Card The Best Vol.2", "code": "PRB-02", "product": "Booster Box",
     "query": "one piece PRB02 card the best vol 2 booster box",
     "title_must_any": ["prb-02", "prb02"],
     "title_must": ["booster box"],
     "title_must_not": ["starter", "sleeve", "playmat"]},
]


# ── Data persistence ─────────────────────────────────────────────────────────

def save_results(results: list[dict], mode: str = "sold"):
    DATA_DIR.mkdir(exist_ok=True)
    csv_path = DATA_DIR / f"op_prices_{mode}.csv"
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
    sales_path = DATA_DIR / f"op_sales_{mode}.json"
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
    print("  One Piece TCG Scraper — eBay Australia")
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
    """Alias for run() — One Piece only has sealed products for now."""
    return run()


if __name__ == "__main__":
    run()
