"""Generate analytical KPI summaries and aggregated CSV outputs."""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CLEAN_FILE = BASE_DIR / "dataset" / "cleaned_sales_data.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_data() -> pd.DataFrame:
    if not CLEAN_FILE.exists():
        raise FileNotFoundError("Run data_cleaning.py first.")
    return pd.read_csv(CLEAN_FILE, parse_dates=["date"])


def compute_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Compute core executive KPIs matching SQL and Power BI definitions."""
    total_revenue = float(df["total amount"].sum())
    total_orders = int(df["transaction id"].nunique())
    unique_customers = int(df["customer id"].nunique())
    units_sold = int(df["quantity"].sum())
    aov = total_revenue / total_orders if total_orders > 0 else 0.0
    total_profit = float(df["profit"].sum()) if "profit" in df.columns else 0.0
    profit_margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    return {
        "Total Revenue": round(total_revenue, 2),
        "Total Orders": total_orders,
        "Unique Customers": unique_customers,
        "Units Sold": units_sold,
        "Average Order Value": round(aov, 2),
        "Total Profit": round(total_profit, 2),
        "Profit Margin (%)": round(profit_margin_pct, 2),
    }


def main():
    df = load_data()
    summary = compute_kpis(df)

    print("\n--- RETAIL SALES SUMMARY ---")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"{key}: {value:,.2f}")
        else:
            print(f"{key}: {value:,}")

    pd.DataFrame(
        [{"KPI": k, "Value": v} for k, v in summary.items()]
    ).to_csv(OUTPUT_DIR / "kpi_summary.csv", index=False)

    # Category summary
    agg_cols = {"total amount": "sum", "quantity": "sum", "transaction id": "nunique"}
    if "profit" in df.columns:
        agg_cols["profit"] = "sum"

    category_df = (
        df.groupby("product category", as_index=False)
        .agg(agg_cols)
        .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
        .sort_values("total_sales", ascending=False)
    )
    if "profit" in category_df.columns:
        category_df["profit_margin_pct"] = (category_df["profit"] / category_df["total_sales"] * 100).round(2)
    category_df.to_csv(OUTPUT_DIR / "category_sales.csv", index=False)

    # Monthly trend with MoM growth and running total
    monthly_df = (
        df.assign(year_month=df["date"].dt.to_period("M").astype(str))
        .groupby("year_month", as_index=False)
        .agg(agg_cols)
        .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
        .sort_values("year_month")
        .reset_index(drop=True)
    )
    monthly_df["running_total_sales"] = monthly_df["total_sales"].cumsum().round(2)
    monthly_df["mom_growth_pct"] = (monthly_df["total_sales"].pct_change() * 100).round(2)
    monthly_df.to_csv(OUTPUT_DIR / "monthly_sales.csv", index=False)

    # Top 10 products
    top_products = (
        df.groupby(["product category", "product name"], as_index=False)
        .agg(agg_cols)
        .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
        .sort_values("total_sales", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
    top_products["sales_rank"] = range(1, len(top_products) + 1)
    top_products.to_csv(OUTPUT_DIR / "top_10_products.csv", index=False)

    # Regional summary
    if "region" in df.columns:
        group_cols = ["market", "region"] if "market" in df.columns else ["region"]
        regional_df = (
            df.groupby(group_cols, as_index=False)
            .agg(agg_cols)
            .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
            .sort_values("total_sales", ascending=False)
        )
        regional_df["sales_share_pct"] = (
            regional_df["total_sales"] / regional_df["total_sales"].sum() * 100
        ).round(2)
        regional_df.to_csv(OUTPUT_DIR / "regional_sales.csv", index=False)

    # Segment summary
    if "segment" in df.columns:
        segment_df = (
            df.groupby("segment", as_index=False)
            .agg(agg_cols)
            .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
            .sort_values("total_sales", ascending=False)
        )
        segment_df.to_csv(OUTPUT_DIR / "segment_sales.csv", index=False)

    # Top 10 customers
    cust_group = ["customer id", "customer name"] if "customer name" in df.columns else ["customer id"]
    top_customers = (
        df.groupby(cust_group, as_index=False)
        .agg(agg_cols)
        .rename(columns={"transaction id": "orders", "total amount": "total_sales"})
        .sort_values("total_sales", ascending=False)
        .head(10)
    )
    top_customers.to_csv(OUTPUT_DIR / "top_customers.csv", index=False)

    # Remove stale gender_sales.csv if gender column is absent in current dataset
    gender_file = OUTPUT_DIR / "gender_sales.csv"
    if "gender" in df.columns:
        df.groupby("gender")["total amount"].sum().to_csv(gender_file)
    elif gender_file.exists():
        gender_file.unlink()

    print(f"\nAnalysis tables saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
