"""Interactive Streamlit Sales Performance Dashboard (Project 1)."""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_logic import (
    apply_dashboard_filters,
    compute_dashboard_kpis,
    get_monthly_trend,
    get_top_products,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset" / "cleaned_sales_data.csv"
SOURCE_FILE = BASE_DIR / "dataset" / "sales_data.csv"
STAR_FACT_FILE = BASE_DIR / "dataset" / "star_schema" / "fact_sales.csv"

st.set_page_config(
    page_title="Retail Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Retail Sales Performance Dashboard")
st.caption("Executive Sales, Profitability, Regional & Product Analytics (CSV -> Python -> Star Schema -> BI)")

if not DATA_FILE.exists():
    st.error("Cleaned dataset not found. Run: python data_cleaning.py")
    st.stop()

df = pd.read_csv(DATA_FILE, parse_dates=["date"])

required_columns = [
    "date",
    "transaction id",
    "customer id",
    "product category",
    "product name",
    "quantity",
    "total amount",
]
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.stop()

# ---------------- SIDEBAR SLICERS (4+ SLICERS) ----------------
st.sidebar.header("Dashboard Slicers")

min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.sidebar.date_input(
    "1. Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

chosen_regions = None
if "region" in df.columns:
    regions = sorted(df["region"].dropna().unique().tolist())
    chosen_regions = st.sidebar.multiselect("2. Region", regions, default=regions)

categories = sorted(df["product category"].dropna().unique().tolist())
chosen_categories = st.sidebar.multiselect("3. Product Category", categories, default=categories)

chosen_segments = None
if "segment" in df.columns:
    segments = sorted(df["segment"].dropna().unique().tolist())
    chosen_segments = st.sidebar.multiselect("4. Customer Segment", segments, default=segments)

chosen_markets = None
if "market" in df.columns:
    markets = sorted(df["market"].dropna().unique().tolist())
    chosen_markets = st.sidebar.multiselect("5. Market", markets, default=markets)

valid_range = date_range if isinstance(date_range, (tuple, list)) and len(date_range) == 2 else None
filtered = apply_dashboard_filters(
    df,
    date_range=valid_range,
    regions=chosen_regions,
    categories=chosen_categories,
    segments=chosen_segments,
    markets=chosen_markets,
)

if filtered.empty:
    st.warning("No records match the selected slicers.")
    st.stop()

# ---------------- EXECUTIVE KPI CARDS (6 KPIs) ----------------
kpis = compute_dashboard_kpis(filtered)

st.subheader("Key Performance Indicators")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sales", f"${kpis['total_sales']:,.2f}")
c2.metric("Total Orders", f"{kpis['total_orders']:,}")
c3.metric("Unique Customers", f"{kpis['unique_customers']:,}")
c4.metric("Units Sold", f"{kpis['units_sold']:,}")
c5.metric("Avg Order Value", f"${kpis['average_order_value']:,.2f}")
c6.metric("Total Profit (Margin)", f"${kpis['total_profit']:,.2f}", f"{kpis['profit_margin_pct']:.2f}%")

# ---------------- MONTHLY TREND ----------------
st.subheader("Monthly Sales Trend")
monthly = get_monthly_trend(filtered)
monthly_chart = px.line(
    monthly,
    x="Month",
    y="Sales",
    markers=True,
    title="Monthly Sales Revenue Trend",
)
monthly_chart.update_layout(xaxis_title="Month", yaxis_title="Total Sales ($)")
st.plotly_chart(monthly_chart, width="stretch")

# ---------------- CATEGORY & TOP 10 PRODUCTS ----------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Category & Sub-Category Drill-Down")
    drill_level = st.radio(
        "Hierarchy Level",
        ["Product Category", "Sub-Category"],
        horizontal=True,
    )
    group_col = "product category" if drill_level == "Product Category" or "sub-category" not in filtered.columns else "sub-category"
    cat_df = (
        filtered.groupby(group_col, as_index=False)["total amount"]
        .sum()
        .sort_values("total amount", ascending=False)
    )
    cat_chart = px.bar(
        cat_df,
        x=group_col,
        y="total amount",
        color=group_col,
        title=f"Revenue by {drill_level}",
        labels={group_col: drill_level, "total amount": "Total Sales ($)"},
    )
    st.plotly_chart(cat_chart, width="stretch")

with col_right:
    st.subheader("Top 10 Products by Sales")
    top_products = get_top_products(filtered, n=10).sort_values("total amount", ascending=True)
    product_chart = px.bar(
        top_products,
        x="total amount",
        y="product name",
        orientation="h",
        title="Top 10 Products by Revenue",
        labels={"total amount": "Total Sales ($)", "product name": "Product Name"},
    )
    st.plotly_chart(product_chart, width="stretch")

# ---------------- REGIONAL DRILL-DOWN ----------------
if "region" in filtered.columns:
    st.subheader("Regional Sales Performance & Drill-Down")
    geo_options = [c for c in ["market", "region", "country"] if c in filtered.columns]
    geo_level = st.radio("Geography Level", [g.title() for g in geo_options], horizontal=True)
    geo_col = geo_level.lower()
    geo_df = (
        filtered.groupby(geo_col, as_index=False)[["total amount", "profit"] if "profit" in filtered.columns else ["total amount"]]
        .sum()
        .sort_values("total amount", ascending=False)
        .head(15)
    )
    region_chart = px.bar(
        geo_df,
        x=geo_col,
        y="total amount",
        color="profit" if "profit" in geo_df.columns else geo_col,
        title=f"Top {geo_level}s by Sales Revenue",
        labels={geo_col: geo_level, "total amount": "Total Sales ($)", "profit": "Profit ($)"},
    )
    st.plotly_chart(region_chart, width="stretch")

# ---------------- CROSS-LAYER RECONCILIATION ----------------
st.subheader("Cross-Layer Reconciliation (Source CSV vs Cleaned CSV vs Star Schema)")
if SOURCE_FILE.exists():
    source_df = pd.read_csv(SOURCE_FILE, encoding="latin1")
    source_df.columns = source_df.columns.str.strip().str.lower().str.replace("_", " ", regex=False)
    sales_col = "sales" if "sales" in source_df.columns else "total amount"
    source_total = float(pd.to_numeric(source_df[sales_col], errors="coerce").sum())
    cleaned_total = float(df["total amount"].sum())
    diff_pct = abs(cleaned_total - source_total) / abs(source_total) * 100 if source_total != 0 else 0.0

    rec_rows = [
        {"Layer": "Raw Source CSV (sales_data.csv)", "Row Count": len(source_df), "Total Sales ($)": round(source_total, 2)},
        {"Layer": "Cleaned CSV (cleaned_sales_data.csv)", "Row Count": len(df), "Total Sales ($)": round(cleaned_total, 2)},
    ]
    if STAR_FACT_FILE.exists():
        fact_df = pd.read_csv(STAR_FACT_FILE)
        rec_rows.append(
            {"Layer": "Star Schema Fact (fact_sales.csv)", "Row Count": len(fact_df), "Total Sales ($)": round(float(fact_df["sales_amount"].sum()), 2)}
        )

    st.table(pd.DataFrame(rec_rows))
    if diff_pct <= 0.1:
        st.success(f"Reconciliation PASSED: variance is {diff_pct:.4f}% (within 0.1% threshold).")
    else:
        st.warning(f"Reconciliation variance is {diff_pct:.4f}% (above 0.1%).")

# ---------------- TRANSACTION TABLE & EXPORT ----------------
st.subheader("Filtered Transaction Data")
st.dataframe(filtered.head(1000), width="stretch")
st.download_button(
    label="Download Filtered Data (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_retail_sales.csv",
    mime="text/csv",
)
