"""
PokeMarket Dashboard — Mega Evolution dip-buying tracker.
Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

from scraper import run as run_scraper, SETS

DATA_DIR = Path(__file__).parent / "data"

# ── Set metadata ─────────────────────────────────────────────────────────────

SET_META = {
    "ME01":  {"name": "Mega Evolution",    "released": "Sep 2025", "color": "#ffcb05"},
    "ME02":  {"name": "Phantasmal Flames", "released": "Nov 2025", "color": "#ff6b35"},
    "ME2.5": {"name": "Ascended Heroes",   "released": "Jan 2026", "color": "#7b68ee"},
    "ME03":  {"name": "Perfect Order",     "released": "Mar 2026", "color": "#00c9a7"},
}

PRODUCT_TYPES = sorted(set(s["product"] for s in SETS))
SET_CODES = list(SET_META.keys())

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

    /* Chip / pill filters */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header-container">
    <div>
        <p class="header-title">PokeMarket</p>
        <p class="header-subtitle">Mega Evolution Sealed Product Tracker &mdash; eBay Australia &mdash; Buy the Dip</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Controls")

    if st.button("Refresh Prices", type="primary", use_container_width=True):
        with st.spinner("Scraping eBay AU (sold + active)..."):
            results = run_scraper()
        if results:
            st.success(f"Updated {len(results)} products!")
            st.rerun()
        else:
            st.error("No data returned — try again shortly.")

    st.markdown("---")
    st.markdown('<p class="section-label">Filter by set</p>', unsafe_allow_html=True)

    selected_sets = st.multiselect(
        "Sets",
        options=SET_CODES,
        default=SET_CODES,
        format_func=lambda c: f"{c} — {SET_META[c]['name']}",
        label_visibility="collapsed",
    )

    st.markdown('<p class="section-label">Filter by product type</p>', unsafe_allow_html=True)

    selected_types = st.multiselect(
        "Product types",
        options=PRODUCT_TYPES,
        default=PRODUCT_TYPES,
        label_visibility="collapsed",
    )

    st.markdown("---")

    price_metric = st.radio(
        "Price metric",
        options=["median", "avg"],
        format_func=lambda x: "Median" if x == "median" else "Average",
        index=0,
        horizontal=True,
    )

    st.markdown("---")
    st.markdown('<p class="section-label">Dip detection</p>', unsafe_allow_html=True)
    rolling_window = st.slider("Rolling avg window (days)", 3, 30, 7)
    dip_threshold = st.slider("Dip threshold (%)", 1, 25, 5,
                               help="Alert when price drops this % below rolling average")

# Build selected product labels from set + type filters
selected = []
for s in SETS:
    label = f"{s['code']} {s['product']}"
    if s['code'] in selected_sets and s['product'] in selected_types:
        selected.append(label)

# ── Helpers ──────────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#999"),
    margin=dict(t=30, b=60, l=60, r=20),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
)


def get_set_color(label: str) -> str:
    code = label.split(" ")[0]
    return SET_META.get(code, {}).get("color", "#ffcb05")


def load_data(mode: str) -> pd.DataFrame | None:
    csv_path = DATA_DIR / f"prices_{mode}.csv"
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df["label"] = df["code"] + " " + df["product"]
    df = df[df["label"].isin(selected)]
    return df if not df.empty else None


def load_sales(mode: str) -> dict | None:
    sales_path = DATA_DIR / f"sales_{mode}.json"
    if not sales_path.exists():
        return None
    with open(sales_path) as f:
        return json.load(f)


def build_date_timeline(sales_data: dict, selected_labels: list, mode: str) -> pd.DataFrame | None:
    """Build a day-by-day price timeline from individual listing dates.

    For sold mode uses the individual sold date; for active uses listing_date.
    De-dupes by URL so listings scraped on multiple days are only counted once.
    """
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


# ── Panel renderer ───────────────────────────────────────────────────────────

def render_panel(df: pd.DataFrame, sales_data: dict | None, mode: str):
    metric_label = "Median" if price_metric == "median" else "Average"
    mode_label = "Sold" if mode == "sold" else "Active"
    accent = "#ffcb05" if mode == "sold" else "#4fc3f7"

    latest_date = df["date"].max()
    latest = df[df["date"] == latest_date].sort_values(price_metric, ascending=False)

    # ── Metrics
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

    # ── Deals (active tab only)
    if mode == "active":
        sold_df = load_data("sold")
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

    # ── Dip alerts (sold tab only)
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

    # ── Bar chart — latest snapshot
    st.markdown("")
    bar_data = latest[["label", price_metric]].sort_values(price_metric, ascending=False).copy()
    bar_data["color"] = bar_data["label"].apply(get_set_color)

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
    st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{mode}")

    # ── Date-based price timeline (uses individual listing dates for rich history)
    timeline_df = build_date_timeline(sales_data, selected, mode)
    if timeline_df is not None and not timeline_df.empty:
        st.markdown(
            f'<p class="section-label">{"Sold" if mode == "sold" else "Listing"} price timeline — by individual date</p>',
            unsafe_allow_html=True
        )
        fig_timeline = go.Figure()
        for label in sorted(timeline_df["label"].unique()):
            prod_data = timeline_df[timeline_df["label"] == label].sort_values("date")
            color = get_set_color(label)
            metric_col = price_metric  # "median" or "avg"
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
        st.plotly_chart(fig_timeline, use_container_width=True, key=f"timeline_{mode}")
    else:
        if mode == "sold":
            st.info("Sold date timeline will appear once listings with individual dates have been scraped.")

    # ── Scrape-date snapshot trend (shows how collected data evolves day-to-day)
    if df["date"].nunique() > 1:
        with st.expander("Snapshot trend — price by scrape date", expanded=False):
            pivot = df.pivot_table(index="date", columns="label", values=price_metric)
            colors = [get_set_color(c) for c in pivot.columns]

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
            st.plotly_chart(fig_line, use_container_width=True, key=f"line_{mode}")

    # ── Volatility table (sold only)
    if mode == "sold" and df["date"].nunique() > 1:
        with st.expander("Volatility & day-over-day change", expanded=False):
            rows = []
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
                rows.append({
                    "Product": label,
                    "Current ($)": current,
                    "Prev ($)": prev,
                    "Change (%)": round(day_change, 1),
                    "Low ($)": prices.min(),
                    "High ($)": prices.max(),
                    "Vol (%)": round(volatility, 1),
                })
            if rows:
                vol_df = pd.DataFrame(rows)
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

    # ── Detailed breakdown
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

    # ── Individual listings — sortable dataframe with eBay links
    with st.expander(f"Individual {mode_label.lower()} listings — click any column header to sort", expanded=False):
        if sales_data:
            latest_sales_date = max(sales_data.keys()) if sales_data else None
            if latest_sales_date and sales_data[latest_sales_date]:
                day_sales = sales_data[latest_sales_date]
                available = sorted([p for p in day_sales.keys() if p in selected])
                if available:
                    pick = st.selectbox("Product", options=available, key=f"sales_{mode}",
                                        label_visibility="collapsed")
                    if pick and pick in day_sales:
                        listings = day_sales[pick]
                        if listings:
                            # Build DataFrame
                            df_rows = []
                            for lst in listings:
                                row: dict = {
                                    "Title": lst["title"].replace("Opens in a new window or tab", "").strip(),
                                    "Price (AUD)": lst["price"],
                                    "Link": lst.get("url", ""),
                                }
                                if mode == "sold":
                                    # Sold mode: date + seller info available from eBay
                                    row["Sold"] = lst.get("date", "—")
                                    row["Seller"] = lst.get("seller", "—")
                                    row["Feedback"] = lst.get("feedback", "—")
                                df_rows.append(row)

                            list_df = pd.DataFrame(df_rows).sort_values("Price (AUD)")
                            # Convert Feedback to numeric for proper sorting
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
            st.info("No listing data yet. Click Refresh Prices.")


# ── Main content ─────────────────────────────────────────────────────────────

sold_df = load_data("sold")
active_df = load_data("active")

if sold_df is None and active_df is None:
    st.info("No data yet. Click **Refresh Prices** in the sidebar to scrape eBay for the first time.")
    st.stop()

# ── Sold vs Active comparison — sortable dataframe
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

# ── Tabs
tab_sold, tab_active = st.tabs(["Sold Prices", "Active Listings"])

with tab_sold:
    if sold_df is not None:
        render_panel(sold_df, load_sales("sold"), "sold")
    else:
        st.info("No sold data yet. Click Refresh Prices.")

with tab_active:
    if active_df is not None:
        render_panel(active_df, load_sales("active"), "active")
    else:
        st.info("No active listing data yet. Click Refresh Prices.")

# ── Footer
st.markdown("---")
st.markdown(
    '<p style="color:#555; font-size:0.75rem; text-align:center;">'
    'Data sourced from eBay Australia &bull; Prices in AUD &bull; English listings only &bull; AU sellers only</p>',
    unsafe_allow_html=True,
)
