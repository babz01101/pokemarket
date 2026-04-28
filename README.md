# PokéMarket

A Streamlit dashboard that tracks **TCG sealed product and singles prices on eBay Australia**.
Scrapes sold + active listings, persists daily snapshots to CSV/JSON, renders price
history, deal/dip alerts, volatility, and a cross-game wishlist.

Currently covers:

- **Pokémon Sealed** — Sword & Shield, Scarlet & Violet, Mega Evolution eras
- **Pokémon Singles** — promos, IRs, SIRs (raw + graded)
- **Pokémon JP Singles** — PSA 10 Secret Rares from recent Japanese sets
  (Mega Brave, Mega Symphonia, Inferno X, Nihil Zero, Ninja Spinner)
- **One Piece Sealed** — main, extra, and premium boosters
- **Dragon Ball Super Fusion World** — fusion, manga, story boosters

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. The dashboard reads cached data from `data/` so it
loads instantly without scraping.

## Refreshing the data

Each tab has a 🔄 Refresh button that reruns the matching scraper. Or run them
directly from the command line:

```bash
python3 scraper.py                 # Pokemon EN sealed + singles
python3 scraper_pokemon_jp.py      # Japanese Pokemon PSA 10 SRs
python3 scraper_onepiece.py        # One Piece sealed
python3 scraper_dragonball.py      # Dragon Ball Super Fusion World
```

A scrape writes:

- `data/<prefix>prices_{sold,active}.csv` — daily aggregate stats per product
- `data/<prefix>sales_{sold,active}.json` — every individual listing seen

Prefixes: `""` Pokemon EN · `pj_` Pokemon JP · `op_` One Piece · `db_` Dragon Ball.

## Adding a new set

1. **Scraper** — append a dict to the `SETS` list in the relevant `scraper_*.py`:

   ```python
   {"name": "My New Set", "code": "ABC01", "product": "Booster Box",
    "query": "pokemon my new set booster box sealed",
    "title_must_any":  ["abc01", "abc-01", "my new set"],   # OR group: anchor
    "title_must":      ["booster box"],                      # AND group: required
    "title_must_not":  ["bundle", "etb"]}                    # exclusions
   ```

   The matcher is case-insensitive and runs on eBay listing titles. Use a
   generous `title_must_not` to keep counterfeits, bundles, and unrelated sets
   out of the price pool.

2. **Dashboard** — register the set in `app.py`:
   - Add an entry to the matching `*_SET_META` dict (release date + colour)
   - Add the product(s) to the matching `POKE_SETS` / `OP_SETS` / etc. list
   - Add the code to the matching `*_CATEGORIES` dict so it appears under a tab

3. Run the scraper to seed initial data, then commit `data/`.

## Filter design notes

- **Cross-set bleed** is the most common issue when adding a new set. eBay
  search results frequently mix sets with overlapping names (e.g. every SWSH
  listing contains "Sword & Shield"). Each set's `title_must_not` should list
  every *other* set name in the same era.
- **Counterfeits** show up most for high-value boxes (Evolving Skies,
  Charizard sets). Watch for `pcs`, `pieces`, `proxy`, `replica`, `custom` —
  bootleg loose-card boxes typically signal themselves with a piece count
  like "324/360PCS" in the title.
- **Japanese sets** opt in via `"allow_japanese": True` (loosens the
  English-only filter and accepts Japan-based sellers in addition to AU).
- **Card numbers that span sets** can be disambiguated with the `title_must_any_2`
  second OR-group — useful when set total `/N` collides between sets
  (e.g. Mega Brave and Mega Symphonia both run 064–092 with total 63).

## Data layout

```
data/
  prices_sold.csv          # Pokemon EN, all dates, one row per (product, date)
  prices_active.csv
  sales_sold.json          # Per-listing details, keyed by scrape date
  sales_active.json
  pj_*  op_*  db_*         # Same structure for the other games
  wishlist.json            # User-starred products, keyed "<prefix>|<code> <product>"
```

CSV schema: `date, code, name, product, median, avg, low, high, count`.

## Wishlist

Each tracker tab has an `⭐ Wishlist` panel. Picks persist to
`data/wishlist.json` and appear aggregated on the rightmost **⭐ Wishlist**
tab with the latest sold/active medians and discount %.

## Deployment

Streamlit Community Cloud auto-deploys from `main`. Point a new app at this
repo, set `app.py` as the entry, done. The dashboard is read-only on the
hosted version (refresh buttons need local CLI access to reach eBay).

## Stack

`streamlit` · `pandas` · `plotly` · `beautifulsoup4` · `requests`
