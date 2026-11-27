"""Optional Oracle Database batch loader + local SQLite star-schema verifier.

Usage:
  1. Local SQL verification (works out of the box, zero Oracle server needed):
       python sql/load_and_verify.py --mode local
  2. Oracle Database load (requires `pip install oracledb` and env vars):
       set ORACLE_USER=...
       set ORACLE_PASSWORD=...
       set ORACLE_DSN=localhost:1521/XEPDB1
       python sql/load_and_verify.py --mode oracle
"""

import argparse
import os
from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
STAR_DIR = BASE_DIR / "dataset" / "star_schema"
RAW_FILE = BASE_DIR / "dataset" / "sales_data.csv"
OUTPUT_DIR = BASE_DIR / "outputs"


def load_star_frames() -> dict[str, pd.DataFrame]:
    tables = ["dim_date", "dim_customer", "dim_product", "dim_geography", "fact_sales"]
    frames = {}
    for name in tables:
        path = STAR_DIR / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing star schema CSV: {path}. Run data_cleaning.py first.")
        frames[name] = pd.read_csv(path, keep_default_na=False)
    return frames


def verify_locally() -> None:
    """Load star schema into SQLite and execute Oracle-equivalent analytical SQL."""
    frames = load_star_frames()
    conn = sqlite3.connect(":memory:")
    for table_name, df in frames.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    # Reconciliation query
    recon = pd.read_sql_query(
        """
        SELECT
            COUNT(*) AS sql_row_count,
            COUNT(DISTINCT order_id) AS unique_orders,
            COUNT(DISTINCT customer_id) AS unique_customers,
            SUM(quantity) AS total_units_sold,
            ROUND(SUM(sales_amount), 2) AS sql_total_sales,
            ROUND(SUM(profit), 2) AS sql_total_profit
        FROM fact_sales
        """,
        conn,
    )

    # Top 10 products using JOIN + GROUP BY + RANK()
    top10_sql = pd.read_sql_query(
        """
        WITH product_perf AS (
            SELECT
                p.category,
                p.product_name,
                ROUND(SUM(f.sales_amount), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit,
                SUM(f.quantity) AS units_sold
            FROM fact_sales f
            JOIN dim_product p ON f.product_key = p.product_key
            GROUP BY p.category, p.product_name
        )
        SELECT
            RANK() OVER (ORDER BY total_sales DESC) AS sales_rank,
            category,
            product_name,
            units_sold,
            total_sales,
            total_profit
        FROM product_perf
        ORDER BY sales_rank
        LIMIT 10
        """,
        conn,
    )

    # Monthly trend with running total & MoM growth (window functions)
    monthly_sql = pd.read_sql_query(
        """
        WITH monthly_agg AS (
            SELECT
                d.year,
                d.month_num,
                d.year_month,
                ROUND(SUM(f.sales_amount), 2) AS monthly_sales
            FROM fact_sales f
            JOIN dim_date d ON f.order_date_key = d.date_key
            GROUP BY d.year, d.month_num, d.year_month
        )
        SELECT
            year_month,
            monthly_sales,
            ROUND(SUM(monthly_sales) OVER (ORDER BY year, month_num), 2) AS running_total_sales,
            ROUND(
                (monthly_sales - LAG(monthly_sales) OVER (ORDER BY year, month_num))
                * 100.0 / NULLIF(LAG(monthly_sales) OVER (ORDER BY year, month_num), 0),
                2
            ) AS mom_growth_pct
        FROM monthly_agg
        ORDER BY year, month_num
        """,
        conn,
    )

    # Regional sales with market partition rank
    regional_sql = pd.read_sql_query(
        """
        WITH region_agg AS (
            SELECT
                g.market,
                g.region,
                COUNT(DISTINCT f.order_id) AS total_orders,
                ROUND(SUM(f.sales_amount), 2) AS total_sales,
                ROUND(SUM(f.profit), 2) AS total_profit
            FROM fact_sales f
            JOIN dim_geography g ON f.geography_key = g.geography_key
            GROUP BY g.market, g.region
        )
        SELECT
            market,
            region,
            total_orders,
            total_sales,
            total_profit,
            RANK() OVER (PARTITION BY market ORDER BY total_sales DESC) AS rank_within_market
        FROM region_agg
        ORDER BY total_sales DESC
        """,
        conn,
    )

    # Cross-check against source CSV
    raw_df = pd.read_csv(RAW_FILE, encoding="latin1")
    raw_rows = len(raw_df)
    raw_sales = round(float(pd.to_numeric(raw_df["Sales"], errors="coerce").sum()), 2)
    sql_rows = int(recon.loc[0, "sql_row_count"])
    sql_sales = float(recon.loc[0, "sql_total_sales"])
    diff_pct = abs(raw_sales - sql_sales) / abs(raw_sales) * 100

    reconcile_df = pd.DataFrame([
        {"Source": "Raw Kaggle CSV (sales_data.csv)", "Rows": raw_rows, "Total Sales": raw_sales, "Variance %": 0.0},
        {"Source": "SQL Star Schema (fact_sales)", "Rows": sql_rows, "Total Sales": sql_sales, "Variance %": round(diff_pct, 4)},
    ])
    OUTPUT_DIR.mkdir(exist_ok=True)
    reconcile_df.to_csv(OUTPUT_DIR / "sql_reconciliation.csv", index=False)

    print("\n========== SQL STAR-SCHEMA VERIFICATION ==========")
    print(reconcile_df.to_string(index=False))
    print("\nTop 5 of Top 10 Products (SQL RANK):")
    print(top10_sql.head(5).to_string(index=False))
    print("\nFirst 5 Months Trend (SQL SUM OVER + LAG):")
    print(monthly_sql.head(5).to_string(index=False))
    print("\nTop 5 Regions (SQL PARTITION RANK):")
    print(regional_sql.head(5).to_string(index=False))
    print("==================================================\n")
    conn.close()


def load_to_oracle() -> None:
    """Batch insert star schema CSVs into Oracle Database using python-oracledb."""
    try:
        import oracledb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install python-oracledb (`pip install oracledb`) to load directly into Oracle.") from exc

    user = os.environ["ORACLE_USER"]
    password = os.environ["ORACLE_PASSWORD"]
    dsn = os.environ["ORACLE_DSN"]

    frames = load_star_frames()
    with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
        with conn.cursor() as cur:
            frames["dim_date"]["full_date"] = pd.to_datetime(frames["dim_date"]["full_date"])
            for table_name in ["dim_date", "dim_customer", "dim_product", "dim_geography", "fact_sales"]:
                df = frames[table_name]
                cols = ", ".join(df.columns)
                binds = ", ".join(f":{i + 1}" for i in range(len(df.columns)))
                sql = f"INSERT INTO {table_name} ({cols}) VALUES ({binds})"
                rows = [tuple(None if v == "" else v for v in row) for row in df.itertuples(index=False, name=None)]
                cur.executemany(sql, rows, batcherrors=False)
                print(f"Loaded {len(rows):,} rows into {table_name}")
        conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Load and verify Star Schema SQL.")
    parser.add_argument("--mode", choices=["local", "oracle"], default="local")
    args = parser.parse_args()
    if args.mode == "oracle":
        load_to_oracle()
    else:
        verify_locally()


if __name__ == "__main__":
    main()
