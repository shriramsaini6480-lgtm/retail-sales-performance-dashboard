"""Generate comprehensive data-quality and cross-layer reconciliation reports."""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = BASE_DIR / "dataset" / "sales_data.csv"
CLEAN_FILE = BASE_DIR / "dataset" / "cleaned_sales_data.csv"
STAR_SCHEMA_DIR = BASE_DIR / "dataset" / "star_schema"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "data_quality_report.txt"
SUMMARY_FILE = OUTPUT_DIR / "data_quality_summary.csv"


def main():
    print("\n========== DATA QUALITY REPORT ==========\n")

    if not SOURCE_FILE.exists():
        print("Original dataset not found!")
        return

    if not CLEAN_FILE.exists():
        print("Cleaned dataset not found! Run python data_cleaning.py first.")
        return

    source = pd.read_csv(SOURCE_FILE, encoding="latin1")
    cleaned = pd.read_csv(CLEAN_FILE)

    source.columns = source.columns.str.strip().str.lower().str.replace("_", " ", regex=False)
    cleaned.columns = cleaned.columns.str.strip().str.lower().str.replace("_", " ", regex=False)

    required_columns = [
        "date",
        "total amount",
        "quantity",
        "product name",
        "customer id",
        "transaction id",
    ]
    missing_columns = [col for col in required_columns if col not in cleaned.columns]
    if missing_columns:
        print("Required columns missing from cleaned dataset:", missing_columns)
        return

    sales_col = "sales" if "sales" in source.columns else ("total amount" if "total amount" in source.columns else None)
    if sales_col is None:
        print("Original dataset does not contain a 'sales' or 'total amount' column.")
        return

    original_rows = len(source)
    cleaned_rows = len(cleaned)
    removed_rows = original_rows - cleaned_rows

    if "postal code" in cleaned.columns:
        postal_code_missing = int(cleaned["postal code"].isnull().sum())
        other_missing = int(cleaned.drop(columns=["postal code"]).isnull().sum().sum())
    else:
        postal_code_missing = 0
        other_missing = int(cleaned.isnull().sum().sum())

    total_missing = postal_code_missing + other_missing
    duplicate_rows = int(cleaned.duplicated().sum())
    order_product_dups = (
        int(cleaned.duplicated(subset=["transaction id", "product id"]).sum())
        if "product id" in cleaned.columns else 0
    )

    dates = pd.to_datetime(cleaned["date"], errors="coerce")
    invalid_dates = int(dates.isna().sum())

    sales = pd.to_numeric(cleaned["total amount"], errors="coerce")
    invalid_sales = int(sales.isna().sum())
    non_positive_sales = int((sales <= 0).sum())

    quantity = pd.to_numeric(cleaned["quantity"], errors="coerce")
    invalid_quantity = int(quantity.isna().sum())
    non_positive_quantity = int((quantity <= 0).sum())

    unique_products = int(cleaned["product name"].nunique())
    unique_customers = int(cleaned["customer id"].nunique())
    unique_orders = int(cleaned["transaction id"].nunique())

    source_sales = float(pd.to_numeric(source[sales_col], errors="coerce").sum())
    cleaned_sales = float(sales.sum())
    difference_pct = (
        abs(source_sales - cleaned_sales) / abs(source_sales) * 100
        if source_sales != 0 else 0.0
    )
    accuracy_status = "PASSED" if difference_pct <= 0.1 else "FAILED"

    fact_file = STAR_SCHEMA_DIR / "fact_sales.csv"
    if fact_file.exists():
        fact_df = pd.read_csv(fact_file)
        star_rows = len(fact_df)
        star_sales = float(fact_df["sales_amount"].sum())
        star_diff_pct = (
            abs(source_sales - star_sales) / abs(source_sales) * 100
            if source_sales != 0 else 0.0
        )
    else:
        star_rows = 0
        star_sales = 0.0
        star_diff_pct = 0.0

    overall_status = (
        "PASSED"
        if (
            other_missing == 0
            and duplicate_rows == 0
            and invalid_dates == 0
            and invalid_sales == 0
            and non_positive_sales == 0
            and invalid_quantity == 0
            and non_positive_quantity == 0
            and accuracy_status == "PASSED"
        )
        else "REVIEW REQUIRED"
    )

    checks = [
        ("Original Rows", original_rows),
        ("Cleaned Rows", cleaned_rows),
        ("Star Schema Fact Rows", star_rows),
        ("Removed Rows", removed_rows),
        ("Missing Postal Codes (Non-US)", postal_code_missing),
        ("Missing Values in Other Columns", other_missing),
        ("Total Missing Values", total_missing),
        ("Exact Duplicate Rows", duplicate_rows),
        ("Repeated Order+Product Line Pairs", order_product_dups),
        ("Invalid Dates", invalid_dates),
        ("Invalid Sales Values", invalid_sales),
        ("Non-positive Sales Values", non_positive_sales),
        ("Invalid Quantity Values", invalid_quantity),
        ("Non-positive Quantity Values", non_positive_quantity),
        ("Unique Products", unique_products),
        ("Unique Customers", unique_customers),
        ("Unique Orders", unique_orders),
        ("Original Total Sales", round(source_sales, 2)),
        ("Cleaned Total Sales", round(cleaned_sales, 2)),
        ("Star Schema Total Sales", round(star_sales, 2)),
        ("Sales Difference Percentage", round(difference_pct, 4)),
        ("Star Schema Difference Percentage", round(star_diff_pct, 4)),
        ("Sales Accuracy Status", accuracy_status),
        ("Overall Data Quality Status", overall_status),
    ]

    summary = pd.DataFrame(checks, columns=["Quality Check", "Result"])
    summary.to_csv(SUMMARY_FILE, index=False)

    report = [
        "RETAIL SALES DATA QUALITY REPORT",
        "=" * 50,
        "",
        f"Original Rows:                    {original_rows:,}",
        f"Cleaned Rows:                     {cleaned_rows:,}",
        f"Star Schema Fact Rows:            {star_rows:,}",
        f"Removed Rows:                     {removed_rows:,}",
        "",
        "DATA QUALITY CHECKS",
        "-" * 50,
        f"Missing Postal Codes (Non-US):    {postal_code_missing:,}",
        f"Missing Values in Other Columns:  {other_missing:,}",
        f"Total Missing Values:             {total_missing:,}",
        f"Exact Duplicate Rows:             {duplicate_rows:,}",
        f"Repeated Order+Product Pairs:     {order_product_dups:,} (split order lines retained)",
        f"Invalid Dates:                    {invalid_dates:,}",
        f"Invalid Sales Values:             {invalid_sales:,}",
        f"Non-positive Sales Values:        {non_positive_sales:,}",
        f"Invalid Quantity Values:          {invalid_quantity:,}",
        f"Non-positive Quantity Values:     {non_positive_quantity:,}",
        "",
        "BUSINESS DATA",
        "-" * 50,
        f"Unique Products (Names):          {unique_products:,}",
        f"Unique Customers:                 {unique_customers:,}",
        f"Unique Orders:                    {unique_orders:,}",
        "",
        "SALES ACCURACY & RECONCILIATION",
        "-" * 50,
        f"Original Total Sales:             {source_sales:,.2f}",
        f"Cleaned Total Sales:              {cleaned_sales:,.2f}",
        f"Star Schema Fact Total Sales:     {star_sales:,.2f}",
        f"CSV vs Cleaned Difference:        {difference_pct:.4f}%",
        f"CSV vs Star Schema Difference:    {star_diff_pct:.4f}%",
        f"Accuracy Status (<= 0.1%):        {accuracy_status}",
        "",
        f"OVERALL DATA QUALITY STATUS:      {overall_status}",
        "",
        "END OF REPORT",
    ]

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print("\nReports saved:", REPORT_FILE, "and", SUMMARY_FILE)


if __name__ == "__main__":
    main()
