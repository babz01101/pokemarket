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

from scraper import run as run_pokemon_scraper, SETS as POKE_SETS, SINGLES as POKE_SINGLES
from scraper_onepiece import run as run_op_scraper, SETS as OP_SETS

DATA_DIR = Path(__file__).parent / "data"

# ── Game metadata ──────────────────────────────────────────────────────────────

POKE_SET_META = {
    "ME01":  {"name": "Mega Evolution",    "released": "Sep 2025", "color": "#ffcb05"},
    "ME02":  {"name": "Phantasmal Flames", "released": "Nov 2025", "color": "#ff6b35"},
    "ME2.5": {"name": "Ascended Heroes",   "released": "Jan 2026", "color": "#7b68ee"},
    "ME03":  {"name": "Perfect Order",     "released": "Mar 2026", "color": "#00c9a7"},
    "PROMO": {"name": "EB Games Promos",   "released": "2026",     "color": "#e040fb"},
    "JT":    {"name": "Journey Together",  "released": "Mar 2025", "color": "#f06292"},
    "SV10":  {"name": "Destined Rivals",   "released": "Apr 2025", "color": "#9c27b0"},
}

OP_SET_META = {
    "OP-01":  {"name": "Romance Dawn",             "released": "Dec 2022", "color": "#e74c3c"},
    "OP-02":  {"name": "Paramount War",             "released": "Mar 2023", "color": "#3498db"},
    "OP-03":  {"name": "Pillars of Strength",       "released": "Jun 2023", "color": "#e67e22"},
    "OP-04":  {"name": "Kingdoms of Intrigue",      "released": "Sep 2023", "color": "#9b59b6"},
    "OP-05":  {"name": "Awakening of the New Era",  "released": "Dec 2023", "color": "#f1c40f"},
    "OP-06":  {"name": "Wings of the Captain",      "released": "Mar 2024", "color": "#1abc9c"},
    "OP-07":  {"name": "500 Years in the Future",   "released": "Jun 2024", "color": "#2ecc71"},
    "OP-08":  {"name": "Two Legends",               "released": "Sep 2024", "color": "#e91e63"},
    "OP-09":  {"name": "Emperors in the New World",  "released": "Dec 2024", "color": "#3f51b5"},
    "OP-10":  {"name": "Royal Blood",               "released": "Mar 2025", "color": "#c0392b"},
    "OP-11":  {"name": "A Fist of Divine Speed",    "released": "Jun 2025", "color": "#27ae60"},
    "OP-12":  {"name": "Legacy of the Master",      "released": "Sep 2025", "color": "#607d8b"},
    "OP-13":  {"name": "Carrying on His Will",      "released": "Nov 2025", "color": "#ff7043"},
    "OP-14":  {"name": "The Azure Sea's Seven",     "released": "Jan 2026", "color": "#00bcd4"},
    "EB-01":  {"name": "Memorial Collection",       "released": "2024",     "color": "#ec407a"},
    "EB-02":  {"name": "Anime 25th Collection",     "released": "2025",     "color": "#ffb300"},
    "EB-03":  {"name": "Heroines Edition",          "released": "2025",     "color": "#f48fb1"},
    "EB-04":  {"name": "Egghead Crisis",            "released": "2025",     "color": "#80cbc4"},
    "PRB-01": {"name": "Card The Best",             "released": "2024",     "color": "#cd7f32"},
    "PRB-02": {"name": "Card The Best Vol.2",       "released": "2025",     "color": "#b0bec5"},
}

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PokeMarket",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ───────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] * { color: #e0e0f0; }
    [data-testid="stSidebar"] hr { border-color: #2a2a4a; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,203,5,0.15);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255,203,5,0.08);
    }
    div[data-testid="stMetric"] label {
        color: #8888aa !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Header */
    .header-container {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.5rem;
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffcb05 0%, #ff9800 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .header-subtitle {
        color: #8888aa;
        font-size: 0.9rem;
        margin: 0;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
    }

    /* Alert cards */
    .alert-card {
        border-radius: 12px;
        padding: 1rem 1.3rem;
        margin-bottom: 0.6rem;
        backdrop-filter: blur(10px);
    }
    .alert-card.buy {
        background: linear-gradient(135deg, rgba(76,175,80,0.12) 0%, rgba(76,175,80,0.05) 100%);
        border: 1px solid rgba(76,175,80,0.3);
    }
    .alert-card.deal {
        background: linear-gradient(135deg, rgba(255,152,0,0.12) 0%, rgba(255,152,0,0.05) 100%);
        border: 1px solid rgba(255,152,0,0.3);
    }
    .alert-card h4 {
        margin: 0 0 0.25rem 0;
        font-size: 0.95rem;
        font-weight: 600;
    }
    .alert-card.buy h4 { color: #4caf50; }
    .alert-card.deal h4 { color: #ff9800; }
    .alert-card p { margin: 0; color: #999; font-size: 0.88rem; }
    .alert-card strong { color: #e0e0e0; }

    /* Section headers */
    .section-label {
        color: #8888aa;
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
        background: #0e1117 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.06) !important;
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
</style>
""", unsafe_allow_html=True)

# ── Shared helpers ───────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#999"),
    margin=dict(t=30, b=60, l=60, r=20),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
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
    return set_meta.get(code, {}).get("color", "#ffcb05")


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
    st.markdown(f"""
    <div class="header-container">
        <div>
            <p class="header-title">PokeMarket</p>
            <p class="header-subtitle">TCG Price Tracker &mdash; eBay Australia &mdash; Buy the Dip</p>
            <p style="color:#666; font-size:0.75rem; margin:0.2rem 0 0 0;">Last updated: {_last_updated}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Pokemon", type="primary", use_container_width=True):
            with st.spinner("Scraping Pokemon..."):
                results = run_pokemon_scraper()
            if results:
                st.success(f"Updated {len(results)} products!")
                st.rerun()
            else:
                st.error("No data — try again shortly.")
    with col2:
        if st.button("Refresh One Piece", type="primary", use_container_width=True):
            with st.spinner("Scraping One Piece..."):
                results = run_op_scraper()
            if results:
                st.success(f"Updated {len(results)} products!")
                st.rerun()
            else:
                st.error("No data — try again shortly.")

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
        for prefix, game in [("", "Pokemon"), ("op_", "One Piece")]:
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
                        deals.append((row["label"], active_price, sold_price, pct))

            if deals:
                st.markdown("")
                for label, ap, sp, pct in sorted(deals, key=lambda x: -x[3]):
                    st.markdown(f"""
                    <div class="alert-card deal">
                        <h4>DEAL: {label}</h4>
                        <p>Active: <strong>${ap:.2f}</strong> &nbsp;&bull;&nbsp;
                        Sold: <strong>${sp:.2f}</strong> &nbsp;&bull;&nbsp;
                        <strong>{pct:.1f}% below sold value</strong></p>
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
                    <h4>BUY SIGNAL: {label}</h4>
                    <p>Current: <strong>${lp:.2f}</strong> &nbsp;&bull;&nbsp;
                    {rolling_window}d avg: <strong>${la:.2f}</strong> &nbsp;&bull;&nbsp;
                    <strong>{pct:.1f}% below average</strong></p>
                </div>
                """, unsafe_allow_html=True)

    # Bar chart
    st.markdown("")
    bar_data = latest[["label", price_metric]].sort_values(price_metric, ascending=False).copy()
    bar_data["color"] = bar_data["label"].apply(lambda l: get_set_color(l, set_meta))

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=bar_data["label"],
        y=bar_data[price_metric],
        text=bar_data[price_metric].apply(lambda v: f"${v:.0f}"),
        textposition="outside",
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
            prod_data = timeline_df[timeline_df["label"] == label].sort_values("date")
            color = get_set_color(label, set_meta)
            metric_col = price_metric
            fig_timeline.add_trace(go.Scatter(
                x=prod_data["date"],
                y=prod_data[metric_col],
                name=label,
                mode="lines+markers",
                line=dict(width=2.5, color=color, shape="spline", smoothing=1.2),
                marker=dict(
                    size=prod_data["count"].clip(upper=12) + 4,
                    color=color,
                    opacity=0.85,
                    line=dict(width=1, color="rgba(0,0,0,0.3)"),
                ),
                customdata=prod_data[["count"]].values,
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "%{x|%d %b %Y}<br>"
                    f"Price: $%{{y:.2f}}<br>"
                    "Listings on day: %{customdata[0]}<extra></extra>"
                ),
            ))
        timeline_layout = {**PLOTLY_LAYOUT}
        timeline_layout["xaxis"] = dict(
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickformat="%d %b",
        )
        fig_timeline.update_layout(
            **timeline_layout,
            xaxis_title="",
            yaxis_title=f"{metric_label} price (AUD)",
            hovermode="closest",
            height=430,
        )
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
                fig_line.add_trace(go.Scatter(
                    x=pivot.index,
                    y=pivot[col],
                    name=col,
                    mode="lines+markers",
                    line=dict(width=2.5, color=colors[i], shape="spline", smoothing=1.2),
                    marker=dict(size=6),
                    hovertemplate=f"{col}<br>" + "%{x|%d %b}<br>$%{y:.2f}<extra></extra>",
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
                    "Product": label,
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
                        lambda v: "color: #4caf50" if isinstance(v, (int, float)) and v < 0 else
                                  "color: #f44336" if isinstance(v, (int, float)) and v > 0 else "",
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
                                        label_visibility="collapsed")
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


# ── Game tab renderer ────────────────────────────────────────────────────────

def render_game(game_key: str, set_meta: dict, all_items: list, data_prefix: str):
    set_codes = list(set_meta.keys())
    set_options = {c: f"{c} — {set_meta[c]['name']}" for c in set_codes}

    selected_sets = st.pills(
        "Sets",
        options=set_codes,
        default=set_codes,
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

    # Load data
    sold_df = load_data("sold", selected, data_prefix)
    active_df = load_data("active", selected, data_prefix)

    if sold_df is None and active_df is None:
        st.info("No data yet. Click the Refresh button in the sidebar to scrape eBay.")
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
            comp_df.columns = ["Product", "Sold (AUD)", "Active (AUD)", "Discount (%)"]

            def _color_discount(val):
                if not isinstance(val, (int, float)):
                    return ""
                return "color: #4caf50; font-weight: 600" if val > 0 else (
                    "color: #f44336; font-weight: 600" if val < 0 else ""
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


# ── Main content ─────────────────────────────────────────────────────────────

tab_pokemon, tab_onepiece = st.tabs(["Pokemon", "One Piece"])

with tab_pokemon:
    render_game("poke", POKE_SET_META, POKE_SETS + POKE_SINGLES, "")

with tab_onepiece:
    render_game("op", OP_SET_META, OP_SETS, "op_")

# ── Footer
st.markdown("---")
st.markdown(
    '<p style="color:#555; font-size:0.75rem; text-align:center;">'
    'Data sourced from eBay Australia &bull; Prices in AUD &bull; English listings only &bull; AU sellers only</p>',
    unsafe_allow_html=True,
)
