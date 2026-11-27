"""Clean retail sales CSV data and export star-schema dimension/fact tables."""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset" / "sales_data.csv"
CLEAN_FILE = BASE_DIR / "dataset" / "cleaned_sales_data.csv"
STAR_SCHEMA_DIR = BASE_DIR / "dataset" / "star_schema"

COLUMN_ALIASES = {
    "order date": "date",
    "order id": "transaction id",
    "category": "product category",
    "sales": "total amount",
}

REQUIRED_COLUMNS = [
    "date",
    "transaction id",
    "customer id",
    "product category",
    "product name",
    "quantity",
    "total amount",
]


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read CSV trying common encodings."""
    for encoding in ("utf-8", "utf-8-sig", "latin1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode CSV file: {path}")


def parse_dates_safely(series: pd.Series) -> pd.Series:
    """Parse mixed date strings (DD-MM-YYYY, YYYY-MM-DD, MM/DD/YYYY) safely."""
    cleaned = series.astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    # Try ISO YYYY-MM-DD first where applicable, then day-first, then general fallback.
    iso_mask = cleaned.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(cleaned.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    non_iso = ~iso_mask
    if non_iso.any():
        parsed.loc[non_iso] = pd.to_datetime(cleaned.loc[non_iso], errors="coerce", dayfirst=True)
    # Fallback for US-style dates (e.g., 07/31/2012) that failed dayfirst parsing
    still_nat = parsed.isna() & cleaned.notna()
    if still_nat.any():
        parsed.loc[still_nat] = pd.to_datetime(cleaned.loc[still_nat], errors="coerce", dayfirst=False)
    return parsed


def clean_sales_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Standardize, validate, and clean raw retail sales data.

    Returns the cleaned DataFrame and a dictionary of cleaning audit metrics.
    """
    df = raw_df.copy()
    df.columns = [str(c).strip().lower().replace("_", " ") for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing columns: " + ", ".join(missing)
            + "\nAvailable columns: " + ", ".join(df.columns)
        )

    original_rows = len(df)

    # Trim whitespace in string columns while preserving missing values
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())

    # 1. Remove exact duplicate rows
    before_dedup = len(df)
    df = df.drop_duplicates().copy()
    exact_duplicates_removed = before_dedup - len(df)

    # 2. Parse order date (and ship date if present)
    df["date"] = parse_dates_safely(df["date"])
    invalid_dates_removed = int(df["date"].isna().sum())
    if "ship date" in df.columns:
        df["ship date"] = parse_dates_safely(df["ship date"])

    # 3. Convert numeric columns
    numeric_cols = ["quantity", "total amount", "discount", "profit", "shipping cost"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Drop rows missing mandatory business fields
    before_nulls = len(df)
    df = df.dropna(subset=REQUIRED_COLUMNS).copy()
    null_or_unparseable_removed = before_nulls - len(df)

    # 5. Remove negative/zero sales and quantities
    before_range = len(df)
    df = df[(df["quantity"] > 0) & (df["total amount"] > 0)].copy()
    non_positive_removed = before_range - len(df)

    # 6. Derived metrics & calendar attributes
    df["price per unit"] = (df["total amount"] / df["quantity"]).round(4)
    if "profit" in df.columns:
        df["profit margin pct"] = ((df["profit"] / df["total amount"]) * 100).round(2)

    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month name"] = df["date"].dt.strftime("%b")
    df["year month"] = df["date"].dt.strftime("%Y-%m")
    df["day name"] = df["date"].dt.day_name()

    if "ship date" in df.columns:
        df["shipping days"] = (df["ship date"] - df["date"]).dt.days
        df["ship date"] = df["ship date"].dt.strftime("%Y-%m-%d")

    # Ensure row id exists as integer surrogate if absent
    if "row id" not in df.columns:
        df.insert(0, "row id", range(1, len(df) + 1))
    else:
        df["row id"] = pd.to_numeric(df["row id"], errors="coerce")
        if df["row id"].isna().any():
            df["row id"] = range(1, len(df) + 1)
        df["row id"] = df["row id"].astype(int)

    audit = {
        "original_rows": original_rows,
        "cleaned_rows": len(df),
        "removed_rows": original_rows - len(df),
        "exact_duplicates_removed": exact_duplicates_removed,
        "invalid_dates_detected": invalid_dates_removed,
        "null_or_unparseable_removed": null_or_unparseable_removed,
        "non_positive_removed": non_positive_removed,
    }
    return df, audit


def export_star_schema(df: pd.DataFrame, out_dir: Path = STAR_SCHEMA_DIR) -> dict[str, int]:
    """Normalize cleaned flat table into 4 dimensions + 1 fact CSV for Oracle & Power BI."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # dim_date: span order dates and ship dates
    order_dates = pd.to_datetime(df["date"])
    all_dates = [order_dates]
    if "ship date" in df.columns:
        all_dates.append(pd.to_datetime(df["ship date"], errors="coerce").dropna())
    combined_dates = pd.Series(pd.concat(all_dates).dropna().unique()).sort_values()

    dim_date = pd.DataFrame({
        "date_key": combined_dates.dt.strftime("%Y%m%d").astype(int),
        "full_date": combined_dates.dt.strftime("%Y-%m-%d"),
        "year": combined_dates.dt.year,
        "quarter": combined_dates.dt.quarter,
        "quarter_label": "Q" + combined_dates.dt.quarter.astype(str) + " " + combined_dates.dt.year.astype(str),
        "month_num": combined_dates.dt.month,
        "month_name": combined_dates.dt.strftime("%b"),
        "year_month": combined_dates.dt.strftime("%Y-%m"),
        "day_of_month": combined_dates.dt.day,
        "day_name": combined_dates.dt.day_name(),
        "is_weekend": combined_dates.dt.day_of_week.isin([5, 6]).astype(int),
    })
    dim_date.to_csv(out_dir / "dim_date.csv", index=False)

    # dim_customer
    cust_cols = ["customer id"]
    if "customer name" in df.columns:
        cust_cols.append("customer name")
    if "segment" in df.columns:
        cust_cols.append("segment")
    dim_customer = df[cust_cols].drop_duplicates(subset=["customer id"]).copy()
    dim_customer = dim_customer.rename(columns={
        "customer id": "customer_id",
        "customer name": "customer_name",
    })
    if "customer_name" not in dim_customer.columns:
        dim_customer["customer_name"] = dim_customer["customer_id"]
    if "segment" not in dim_customer.columns:
        dim_customer["segment"] = "General"
    dim_customer = dim_customer.sort_values("customer_id").reset_index(drop=True)
    dim_customer.to_csv(out_dir / "dim_customer.csv", index=False)

    # dim_product (surrogate key handles Product IDs that share multiple Product Names)
    prod_src_cols = [c for c in ["product id", "product name", "product category", "sub-category"] if c in df.columns]
    dim_product = df[prod_src_cols].drop_duplicates().sort_values(prod_src_cols).reset_index(drop=True)
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))
    dim_product = dim_product.rename(columns={
        "product id": "product_id",
        "product name": "product_name",
        "product category": "category",
        "sub-category": "sub_category",
    })
    if "product_id" not in dim_product.columns:
        dim_product["product_id"] = "PROD-" + dim_product["product_key"].astype(str)
    if "sub_category" not in dim_product.columns:
        dim_product["sub_category"] = "General"
    dim_product.to_csv(out_dir / "dim_product.csv", index=False)

    # dim_geography
    geo_map = {
        "market": "market",
        "region": "region",
        "country": "country",
        "state": "state",
        "city": "city",
        "postal code": "postal_code",
    }
    geo_df = pd.DataFrame(index=df.index)
    for src, dst in geo_map.items():
        if src in df.columns:
            if dst == "postal_code":
                # Preserve clean string postal code without trailing '.0'
                vals = df[src].apply(
                    lambda v: "" if pd.isna(v) else (str(int(v)) if isinstance(v, float) and v.is_integer() else str(v).removesuffix(".0"))
                )
                geo_df[dst] = vals
            else:
                geo_df[dst] = df[src].fillna("Unknown").astype(str)
        else:
            geo_df[dst] = "" if dst == "postal_code" else "Unknown"

    geo_cols = ["market", "region", "country", "state", "city", "postal_code"]
    dim_geography = geo_df[geo_cols].drop_duplicates().sort_values(geo_cols).reset_index(drop=True)
    dim_geography.insert(0, "geography_key", range(1, len(dim_geography) + 1))
    dim_geography.to_csv(out_dir / "dim_geography.csv", index=False)

    # Map surrogate keys back to fact_sales
    prod_lookup_cols = ["product_id", "product_name", "category", "sub_category"]
    fact_src = df.copy()
    fact_src["product_id"] = fact_src["product id"] if "product id" in fact_src.columns else ""
    fact_src["product_name"] = fact_src["product name"]
    fact_src["category"] = fact_src["product category"]
    fact_src["sub_category"] = fact_src["sub-category"] if "sub-category" in fact_src.columns else "General"
    if "product id" not in df.columns:
        # Match by product_name + category
        prod_merge = dim_product[["product_key", "product_name", "category", "sub_category"]]
        fact_src = fact_src.merge(prod_merge, on=["product_name", "category", "sub_category"], how="left")
    else:
        fact_src = fact_src.merge(dim_product[["product_key"] + prod_lookup_cols], on=prod_lookup_cols, how="left")

    for dst in geo_cols:
        fact_src[dst] = geo_df[dst].values
    fact_src = fact_src.merge(dim_geography, on=geo_cols, how="left")

    fact_sales = pd.DataFrame({
        "row_id": fact_src["row id"].astype(int),
        "order_id": fact_src["transaction id"].astype(str),
        "order_date_key": pd.to_datetime(fact_src["date"]).dt.strftime("%Y%m%d").astype(int),
        "ship_date_key": (
            pd.to_datetime(fact_src["ship date"], errors="coerce").dt.strftime("%Y%m%d").fillna("0").astype(int)
            if "ship date" in fact_src.columns else pd.to_datetime(fact_src["date"]).dt.strftime("%Y%m%d").astype(int)
        ),
        "customer_id": fact_src["customer id"].astype(str),
        "product_key": fact_src["product_key"].astype(int),
        "geography_key": fact_src["geography_key"].astype(int),
        "ship_mode": fact_src["ship mode"].astype(str) if "ship mode" in fact_src.columns else "Standard",
        "order_priority": fact_src["order priority"].astype(str) if "order priority" in fact_src.columns else "Medium",
        "quantity": fact_src["quantity"].astype(int),
        "unit_price": fact_src["price per unit"].round(4),
        "discount": fact_src["discount"].round(4) if "discount" in fact_src.columns else 0.0,
        "sales_amount": fact_src["total amount"].round(4),
        "profit": fact_src["profit"].round(4) if "profit" in fact_src.columns else 0.0,
        "shipping_cost": fact_src["shipping cost"].round(4) if "shipping cost" in fact_src.columns else 0.0,
        "shipping_days": fact_src["shipping days"].fillna(0).astype(int) if "shipping days" in fact_src.columns else 0,
    })
    fact_sales.to_csv(out_dir / "fact_sales.csv", index=False)

    return {
        "dim_date": len(dim_date),
        "dim_customer": len(dim_customer),
        "dim_product": len(dim_product),
        "dim_geography": len(dim_geography),
        "fact_sales": len(fact_sales),
    }


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Please save the Kaggle CSV as dataset/sales_data.csv"
        )

    raw_df = read_csv_safely(DATA_FILE)
    cleaned_df, audit = clean_sales_dataframe(raw_df)
    cleaned_df.to_csv(CLEAN_FILE, index=False)
    schema_counts = export_star_schema(cleaned_df)

    print("\n========== DATA CLEANING SUMMARY ==========")
    print(f"Original rows: {audit['original_rows']:,}")
    print(f"Clean rows: {audit['cleaned_rows']:,}")
    print(f"Removed rows: {audit['removed_rows']:,}")
    print(f"Unique products (names): {cleaned_df['product name'].nunique():,}")
    print(f"Total sales: {cleaned_df['total amount'].sum():,.2f}")
    print(f"Saved cleaned data to: {CLEAN_FILE}")
    print(f"Exported star schema to: {STAR_SCHEMA_DIR} -> {schema_counts}")
    print("===========================================\n")


if __name__ == "__main__":
    main()
