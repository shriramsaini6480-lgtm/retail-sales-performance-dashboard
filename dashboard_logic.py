"""Pure filtering, KPI, and aggregation helpers shared by Streamlit app and tests."""

from datetime import date
import pandas as pd


def apply_dashboard_filters(
    df: pd.DataFrame,
    date_range: tuple[date, date] | None = None,
    regions: list[str] | None = None,
    categories: list[str] | None = None,
    segments: list[str] | None = None,
    markets: list[str] | None = None,
) -> pd.DataFrame:
    """Filter retail sales DataFrame by date range, region, category, segment, and market."""
    filtered = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(filtered["date"]):
        filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")

    if date_range is not None and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered["date"].dt.date >= start_date)
            & (filtered["date"].dt.date <= end_date)
        ]

    if regions is not None and "region" in filtered.columns:
        filtered = filtered[filtered["region"].isin(regions)]

    if categories is not None and "product category" in filtered.columns:
        filtered = filtered[filtered["product category"].isin(categories)]

    if segments is not None and "segment" in filtered.columns:
        filtered = filtered[filtered["segment"].isin(segments)]

    if markets is not None and "market" in filtered.columns:
        filtered = filtered[filtered["market"].isin(markets)]

    return filtered


def compute_dashboard_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Compute 6 executive KPIs for the filtered dataset."""
    revenue = float(df["total amount"].sum())
    orders = int(df["transaction id"].nunique())
    customers = int(df["customer id"].nunique())
    units = int(df["quantity"].sum())
    aov = revenue / orders if orders > 0 else 0.0
    profit = float(df["profit"].sum()) if "profit" in df.columns else 0.0
    margin_pct = (profit / revenue * 100) if revenue > 0 else 0.0

    return {
        "total_sales": round(revenue, 2),
        "total_orders": orders,
        "unique_customers": customers,
        "units_sold": units,
        "average_order_value": round(aov, 2),
        "total_profit": round(profit, 2),
        "profit_margin_pct": round(margin_pct, 2),
    }


def get_top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N products sorted by total sales descending."""
    if df.empty:
        return pd.DataFrame(columns=["product name", "total amount", "quantity"])
    agg = {"total amount": "sum", "quantity": "sum"}
    if "profit" in df.columns:
        agg["profit"] = "sum"
    return (
        df.groupby("product name", as_index=False)
        .agg(agg)
        .sort_values("total amount", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def get_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Return chronological monthly sales trend."""
    if df.empty:
        return pd.DataFrame(columns=["Month", "Sales"])
    dt = pd.to_datetime(df["date"])
    monthly = (
        df.assign(_period=dt.dt.to_period("M"))
        .groupby("_period", as_index=False)["total amount"]
        .sum()
        .sort_values("_period")
    )
    monthly["Month"] = monthly["_period"].astype(str)
    return monthly[["Month", "total amount"]].rename(columns={"total amount": "Sales"}).reset_index(drop=True)
