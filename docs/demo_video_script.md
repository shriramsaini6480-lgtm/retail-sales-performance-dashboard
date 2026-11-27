# Demo Video Recording Script (2–3 Minutes)

Use this checklist when recording your screen walkthrough (e.g., via OBS Studio or Loom):

1. **0:00 – 0:30 | Problem & Architecture Overview**
   - Show `README.md` and `docs/star_schema_diagram.md`.
   - Explain the pipeline: Kaggle Retail Sales CSV (`51,290` rows) -> Python `pandas` cleaning & star-schema normalization -> Oracle SQL analytics & views -> Power BI & Streamlit KPI dashboards.

2. **0:30 – 1:05 | Python Data Cleaning, Quality Report & Automated Tests**
   - Run in terminal:
     - `python data_cleaning.py`
     - `python data_quality_report.py`
     - `python -m unittest discover -s tests -v`
   - Highlight `0` missing critical fields, `0` invalid dates, `0.0000%` sales variance (`$12,642,501.91` reconciled), and unit tests passing for null/duplicate rows, negative amounts, date format errors, and region slicer.

3. **1:05 – 1:40 | Oracle SQL Star Schema & Window Functions**
   - Show `sql/01_ddl_star_schema.sql`, `sql/03_analytical_queries.sql`, and `sql/04_views.sql`.
   - Run `python sql/load_and_verify.py --mode local` (or SQL*Plus/SQL Developer connected to Oracle) showing Top 10 products (`RANK()`), running total & MoM growth (`SUM() OVER`, `LAG()`), and SQL reconciliation (`51,290` rows, `$12,642,501.91`).

4. **1:40 – 2:45 | Live Dashboard Walkthrough (Streamlit + Power BI)**
   - Open `streamlit run app.py` (and/or `powerbi/Retail_Sales_Performance.pbix` built using `powerbi/POWERBI_DASHBOARD_GUIDE.md`).
   - Show the **6 KPI cards**, **Monthly Trend**, **Top 10 Products**, and **Regional Breakdown**.
   - Demonstrate **Region slicer**, **Category slicer**, **Date Range slicer**, and **Category -> Sub-Category / Market -> Region -> Country drill-downs**.
   - Highlight the key insight: *EU Central* leads sales, *Technology* leads margin (`13.99%`), while *Furniture -> Tables* loses `-$64,083.39`.
