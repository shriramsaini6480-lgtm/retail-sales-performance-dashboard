"""Automated test suite covering Project 1 test cases & acceptance criteria."""

from datetime import date
from pathlib import Path
import tempfile
import unittest
import pandas as pd

from analysis import compute_kpis
from dashboard_logic import (
    apply_dashboard_filters,
    compute_dashboard_kpis,
    get_monthly_trend,
    get_top_products,
)
from data_cleaning import clean_sales_dataframe, export_star_schema

BASE_DIR = Path(__file__).resolve().parent.parent


class TestCleaningEdgeCases(unittest.TestCase):
    """Test cases: null/duplicate rows, negative amounts, date format errors."""

    def _sample_raw_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            # Valid row (DD-MM-YYYY)
            {
                "Row ID": 1,
                "Order ID": "ORD-1",
                "Order Date": "31-07-2012",
                "Ship Date": "02-08-2012",
                "Customer ID": "C-1",
                "Customer Name": "Alice",
                "Segment": "Consumer",
                "Market": "US",
                "Region": "East",
                "Country": "United States",
                "State": "New York",
                "City": "New York City",
                "Postal Code": "10024",
                "Product ID": "P-1",
                "Category": "Technology",
                "Sub-Category": "Phones",
                "Product Name": "Smart Phone A",
                "Sales": 200.0,
                "Quantity": 2,
                "Discount": 0.0,
                "Profit": 50.0,
                "Shipping Cost": 10.0,
                "Ship Mode": "Second Class",
                "Order Priority": "High",
            },
            # Exact duplicate of row 1 -> should be dropped
            {
                "Row ID": 1,
                "Order ID": "ORD-1",
                "Order Date": "31-07-2012",
                "Ship Date": "02-08-2012",
                "Customer ID": "C-1",
                "Customer Name": "Alice",
                "Segment": "Consumer",
                "Market": "US",
                "Region": "East",
                "Country": "United States",
                "State": "New York",
                "City": "New York City",
                "Postal Code": "10024",
                "Product ID": "P-1",
                "Category": "Technology",
                "Sub-Category": "Phones",
                "Product Name": "Smart Phone A",
                "Sales": 200.0,
                "Quantity": 2,
                "Discount": 0.0,
                "Profit": 50.0,
                "Shipping Cost": 10.0,
                "Ship Mode": "Second Class",
                "Order Priority": "High",
            },
            # Null customer ID -> should be dropped
            {
                "Row ID": 2,
                "Order ID": "ORD-2",
                "Order Date": "2013-02-15",
                "Ship Date": "2013-02-17",
                "Customer ID": None,
                "Customer Name": "Bob",
                "Segment": "Corporate",
                "Market": "EU",
                "Region": "Central",
                "Country": "Germany",
                "State": "Berlin",
                "City": "Berlin",
                "Postal Code": None,
                "Product ID": "P-2",
                "Category": "Furniture",
                "Sub-Category": "Chairs",
                "Product Name": "Chair B",
                "Sales": 150.0,
                "Quantity": 1,
                "Discount": 0.1,
                "Profit": 20.0,
                "Shipping Cost": 5.0,
                "Ship Mode": "Standard Class",
                "Order Priority": "Medium",
            },
            # Negative sales amount -> should be dropped
            {
                "Row ID": 3,
                "Order ID": "ORD-3",
                "Order Date": "2013-03-10",
                "Ship Date": "2013-03-12",
                "Customer ID": "C-3",
                "Customer Name": "Cara",
                "Segment": "Corporate",
                "Market": "EU",
                "Region": "Central",
                "Country": "France",
                "State": "Ile-de-France",
                "City": "Paris",
                "Postal Code": None,
                "Product ID": "P-2",
                "Category": "Furniture",
                "Sub-Category": "Chairs",
                "Product Name": "Chair B",
                "Sales": -100.0,
                "Quantity": 1,
                "Discount": 0.0,
                "Profit": -20.0,
                "Shipping Cost": 5.0,
                "Ship Mode": "Standard Class",
                "Order Priority": "Low",
            },
            # Date format error -> should be dropped
            {
                "Row ID": 4,
                "Order ID": "ORD-4",
                "Order Date": "not-a-date",
                "Ship Date": "2013-04-05",
                "Customer ID": "C-4",
                "Customer Name": "Dan",
                "Segment": "Home Office",
                "Market": "APAC",
                "Region": "Oceania",
                "Country": "Australia",
                "State": "NSW",
                "City": "Sydney",
                "Postal Code": None,
                "Product ID": "P-3",
                "Category": "Office Supplies",
                "Sub-Category": "Paper",
                "Product Name": "Paper C",
                "Sales": 75.0,
                "Quantity": 3,
                "Discount": 0.0,
                "Profit": 15.0,
                "Shipping Cost": 4.0,
                "Ship Mode": "First Class",
                "Order Priority": "High",
            },
            # Valid row with ISO YYYY-MM-DD date format
            {
                "Row ID": 5,
                "Order ID": "ORD-5",
                "Order Date": "2014-11-20",
                "Ship Date": "2014-11-22",
                "Customer ID": "C-5",
                "Customer Name": "Eva",
                "Segment": "Consumer",
                "Market": "APAC",
                "Region": "Oceania",
                "Country": "Australia",
                "State": "Victoria",
                "City": "Melbourne",
                "Postal Code": None,
                "Product ID": "P-4",
                "Category": "Technology",
                "Sub-Category": "Accessories",
                "Product Name": "Headset D",
                "Sales": 300.0,
                "Quantity": 3,
                "Discount": 0.0,
                "Profit": 90.0,
                "Shipping Cost": 12.0,
                "Ship Mode": "Same Day",
                "Order Priority": "Critical",
            },
        ])

    def test_cleaning_removes_dups_nulls_negatives_and_bad_dates(self):
        cleaned, audit = clean_sales_dataframe(self._sample_raw_df())
        self.assertEqual(audit["original_rows"], 6)
        self.assertEqual(audit["exact_duplicates_removed"], 1)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(set(cleaned["transaction id"]), {"ORD-1", "ORD-5"})
        self.assertAlmostEqual(float(cleaned["total amount"].sum()), 500.0)

    def test_star_schema_export_preserves_totals(self):
        cleaned, _ = clean_sales_dataframe(self._sample_raw_df())
        with tempfile.TemporaryDirectory() as tmp:
            counts = export_star_schema(cleaned, Path(tmp))
            self.assertEqual(counts["fact_sales"], 2)
            fact = pd.read_csv(Path(tmp) / "fact_sales.csv")
            self.assertAlmostEqual(float(fact["sales_amount"].sum()), 500.0)

    def test_region_slicer_and_kpis(self):
        cleaned, _ = clean_sales_dataframe(self._sample_raw_df())
        oceania = apply_dashboard_filters(cleaned, regions=["Oceania"])
        self.assertEqual(len(oceania), 1)
        kpis = compute_dashboard_kpis(oceania)
        self.assertAlmostEqual(kpis["total_sales"], 300.0)
        self.assertEqual(kpis["total_orders"], 1)
        self.assertEqual(kpis["units_sold"], 3)

        date_filtered = apply_dashboard_filters(
            cleaned, date_range=(date(2014, 1, 1), date(2014, 12, 31))
        )
        self.assertEqual(len(date_filtered), 1)
        self.assertEqual(date_filtered.iloc[0]["region"], "Oceania")


class TestProductionDatasetReconciliation(unittest.TestCase):
    """Verify full 51,290-row dataset reconciliation & acceptance criteria."""

    @classmethod
    def setUpClass(cls):
        cls.raw_df = pd.read_csv(BASE_DIR / "dataset" / "sales_data.csv", encoding="latin1")
        cls.clean_df = pd.read_csv(BASE_DIR / "dataset" / "cleaned_sales_data.csv", parse_dates=["date"])
        cls.fact_df = pd.read_csv(BASE_DIR / "dataset" / "star_schema" / "fact_sales.csv")

    def test_row_counts_and_sales_within_0_1_pct(self):
        raw_sales = float(pd.to_numeric(self.raw_df["Sales"], errors="coerce").sum())
        clean_sales = float(self.clean_df["total amount"].sum())
        fact_sales = float(self.fact_df["sales_amount"].sum())

        self.assertEqual(len(self.raw_df), 51290)
        self.assertEqual(len(self.clean_df), 51290)
        self.assertEqual(len(self.fact_df), 51290)

        diff_clean = abs(raw_sales - clean_sales) / raw_sales * 100
        diff_fact = abs(raw_sales - fact_sales) / raw_sales * 100
        self.assertLessEqual(diff_clean, 0.1)
        self.assertLessEqual(diff_fact, 0.1)

    def test_kpis_top_10_and_monthly_trend(self):
        kpis = compute_kpis(self.clean_df)
        self.assertGreaterEqual(len(kpis), 5)
        self.assertAlmostEqual(kpis["Total Revenue"], 12642501.91, places=2)

        top10 = get_top_products(self.clean_df, 10)
        self.assertEqual(len(top10), 10)
        self.assertEqual(top10.iloc[0]["product name"], "Apple Smart Phone, Full Size")

        monthly = get_monthly_trend(self.clean_df)
        self.assertEqual(len(monthly), 48)
        self.assertEqual(monthly.iloc[0]["Month"], "2011-01")
        self.assertEqual(monthly.iloc[-1]["Month"], "2014-12")


if __name__ == "__main__":
    unittest.main()
