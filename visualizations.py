"""Generate static matplotlib charts from cleaned retail sales data."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset" / "cleaned_sales_data.csv"
OUT_DIR = BASE_DIR / "outputs" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError("Run data_cleaning.py first.")
    df = pd.read_csv(DATA_FILE, parse_dates=["date"])

    # 1. Monthly sales trend
    monthly = df.groupby(df["date"].dt.to_period("M"))["total amount"].sum()
    plt.figure(figsize=(12, 5))
    monthly.plot(marker="o", linewidth=2, color="#1f77b4")
    plt.title("Monthly Sales Trend (2011 - 2014)")
    plt.xlabel("Month")
    plt.ylabel("Total Sales ($)")
    plt.xticks(rotation=45)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "monthly_sales.png", dpi=150)
    plt.close()

    # 2. Sales by product category
    category = df.groupby("product category")["total amount"].sum().sort_values()
    plt.figure(figsize=(9, 5))
    category.plot(kind="barh", color="#2ca02c")
    plt.title("Sales by Product Category")
    plt.xlabel("Total Sales ($)")
    plt.ylabel("Product Category")
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "category_sales.png", dpi=150)
    plt.close()

    # 3. Top 10 products by sales
    top10 = df.groupby("product name")["total amount"].sum().nlargest(10).sort_values()
    plt.figure(figsize=(11, 6))
    top10.plot(kind="barh", color="#ff7f0e")
    plt.title("Top 10 Products by Sales Revenue")
    plt.xlabel("Total Sales ($)")
    plt.ylabel("Product Name")
    plt.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "top_10_products.png", dpi=150)
    plt.close()

    # 4. Regional sales
    if "region" in df.columns:
        region = df.groupby("region")["total amount"].sum().sort_values()
        plt.figure(figsize=(10, 6))
        region.plot(kind="barh", color="#9467bd")
        plt.title("Sales by Region")
        plt.xlabel("Total Sales ($)")
        plt.ylabel("Region")
        plt.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(OUT_DIR / "regional_sales.png", dpi=150)
        plt.close()

    # 5. Weekday sales
    weekday = df.groupby("day name")["total amount"].sum()
    weekday = weekday.reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).dropna()
    plt.figure(figsize=(9, 5))
    weekday.plot(kind="bar", color="#17becf")
    plt.title("Sales by Day of Week")
    plt.xlabel("Day")
    plt.ylabel("Total Sales ($)")
    plt.xticks(rotation=30)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "weekday_sales.png", dpi=150)
    plt.close()

    print(f"Charts saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
