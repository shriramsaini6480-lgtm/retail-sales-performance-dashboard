# Retail Sales Performance Dashboard (Project 1)

An end-to-end **Retail & E-Commerce Analytics** solution built with **Python (`pandas`, `plotly`, `streamlit`)**, **Oracle SQL (Star Schema DDL, Window Functions, Views)**, and **Power BI (DAX, Power Query M, Drill-Down Guide)**, reconciled across every layer to **0.0000% variance**.

---

## Project Architecture

```text
Kaggle CSV (dataset/sales_data.csv: 51,290 rows, $12,642,501.91)
   │
   ▼  data_cleaning.py (pandas cleaning, date parsing, negative/null/dup checks)
Cleaned CSV + Star Schema CSVs (dataset/star_schema/: dim_date, dim_customer, dim_product, dim_geography, fact_sales)
   │
   ├──► Oracle SQL (sql/01_ddl_star_schema.sql -> 02_load_data.sql -> 03_analytical_queries.sql -> 04_views.sql)
   ├──► Data Quality & Reconciliation (data_quality_report.py, sql/load_and_verify.py)
   ├──► Power BI Semantic Layer (powerbi/measures.dax, power_query_transform.m, theme.json, build guide)
   └──► Interactive Dashboard & Charts (app.py, analysis.py, visualizations.py)
```

---

## Reconciliation & Acceptance Criteria Summary

| Check | Requirement | Observed Result | Status |
|---|---|---|---|
| Source vs Cleaned vs SQL Row Count | Exact match | `51,290` / `51,290` / `51,290` | PASSED |
| Total Sales Accuracy | Within `0.1%` | `$12,642,501.91` (`0.0000%` variance) | PASSED |
| KPI Cards | At least `5` KPIs | `6+` KPIs (Sales, Orders, Customers, Units, AOV, Profit & Margin %) | PASSED |
| Interactive Slicers | At least `3` slicers | `5` slicers (`Date`, `Region`, `Category`, `Segment`, `Market`) | PASSED |
| Core Analytics | Top 10 products & monthly trend | Verified in Python, SQL (`RANK`, `SUM OVER`, `LAG`), and BI | PASSED |

---

## Folder Structure

```text
Retail_Sales_Performance_Python/
├── dataset/
│   ├── sales_data.csv                    # Raw Kaggle Global Superstore CSV (51,290 rows)
│   ├── cleaned_sales_data.csv            # Cleaned flat dataset
│   └── star_schema/                      # Normalized CSVs for Oracle & Power BI
│       ├── dim_date.csv
│       ├── dim_customer.csv
│       ├── dim_product.csv
│       ├── dim_geography.csv
│       └── fact_sales.csv
├── sql/
│   ├── 01_ddl_star_schema.sql            # Oracle DDL (staging, dimensions, fact, indexes)
│   ├── 02_load_data.sql                  # Oracle MERGE/INSERT star-schema load + reconciliation
│   ├── 03_analytical_queries.sql         # JOIN, GROUP BY, RANK, DENSE_RANK, LAG, SUM OVER
│   ├── 04_views.sql                      # 7 Oracle reporting views (incl. vw_powerbi_sales_model)
│   ├── fact_sales.ctl                    # SQL*Loader control file
│   └── load_and_verify.py                # Local SQLite verification & Oracle batch loader
├── powerbi/
│   ├── measures.dax                      # DAX measures (KPIs, MoM/YoY, Top 10 Rank, Regional Share)
│   ├── power_query_transform.m           # Power Query M starter script
│   ├── theme.json                        # Executive Power BI theme
│   └── POWERBI_DASHBOARD_GUIDE.md        # Step-by-step .pbix assembly & drill-down guide
├── docs/
│   ├── problem_statement_and_kpis.md     # Problem statement & formal KPI formulas
│   ├── star_schema_diagram.md            # Mermaid ER diagram & table specifications
│   ├── insights_summary.md               # Executive business findings & recommendations
│   └── demo_video_script.md              # 2–3 minute demo walkthrough script
├── notebooks/
│   └── retail_sales_analysis.ipynb       # Reproducible exploratory & KPI notebook
├── outputs/
│   ├── data_quality_report.txt           # Audit & reconciliation report
│   ├── data_quality_summary.csv          # Tabular quality metrics
│   ├── sql_reconciliation.csv            # CSV vs SQL star-schema reconciliation
│   ├── kpi_summary.csv, top_10_products.csv, monthly_sales.csv, regional_sales.csv, ...
│   └── charts/                           # Saved PNG charts
├── tests/
│   └── test_retail_pipeline.py           # Automated tests (nulls, dups, negatives, dates, region slicer)
├── data_cleaning.py
├── data_quality_report.py
├── analysis.py
├── visualizations.py
├── dashboard_logic.py
├── app.py                                # Interactive Streamlit dashboard
└── requirements.txt
```

---

## Quick Start

### 1. Run the Python Pipeline & Dashboard
```powershell
python -m pip install -r requirements.txt
python data_cleaning.py
python data_quality_report.py
python analysis.py
python visualizations.py
python sql/load_and_verify.py --mode local
python -m unittest discover -s tests -v
streamlit run app.py
```

### 2. Run on Oracle Database (19c / 21c / 23ai)
1. Execute `sql/01_ddl_star_schema.sql` in SQL*Plus / SQLcl / Oracle SQL Developer.
2. Load star-schema CSVs using `python sql/load_and_verify.py --mode oracle` (set `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`), or load via SQL*Loader (`sql/fact_sales.ctl`) + `sql/02_load_data.sql`.
3. Create reporting views with `sql/04_views.sql` and run `sql/03_analytical_queries.sql`.

### 3. Build the Power BI Workbook (`.pbix`)
Follow [powerbi/POWERBI_DASHBOARD_GUIDE.md](powerbi/POWERBI_DASHBOARD_GUIDE.md) in **Power BI Desktop** using either your Oracle views or `dataset/star_schema/*.csv`, paste [powerbi/measures.dax](powerbi/measures.dax), apply [powerbi/theme.json](powerbi/theme.json), and save as `powerbi/Retail_Sales_Performance.pbix`.

### 4. Publish to GitHub
```powershell
git init
git add .
git commit -m "Complete Project 1: Retail Sales Performance Dashboard"
git remote add origin <your-github-repo-url>
git push -u origin main
```
