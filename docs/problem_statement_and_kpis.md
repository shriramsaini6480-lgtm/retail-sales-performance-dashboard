# Problem Statement & KPI Definitions (Project 1)

## 1. Business Problem Statement
Global retail operations generate tens of thousands of order-line transactions across multiple markets, regions, product categories, and customer segments. Without a standardized cleaning, relational warehouse, and BI layer, leadership lacks reliable answers to:
- Which products, sub-categories, and regions drive top-line revenue vs. erode bottom-line margin?
- How do monthly sales evolve year-over-year, and when do seasonal peaks occur?
- Are raw CSV extracts, SQL warehouse tables, and BI dashboards reconciled to the exact dollar?

**Goal:** Build an end-to-end **Sales Performance Dashboard** pipeline combining **Python (`pandas`)** cleaning and star-schema preparation, **Oracle SQL** analytical modeling (`JOIN`, `GROUP BY`, window functions, reporting views), and **Power BI / Streamlit** interactive KPI dashboards reconciled within **0.1%** of the source CSV.

---

## 2. Dataset Overview
- **Source:** Retail Sales Dataset (`dataset/sales_data.csv`, Global Superstore schema)
- **Raw Volume:** 51,290 order-line records across 24 columns (`2011-01-01` to `2014-12-31`)
- **Granularity:** One row per order line item (`Row ID`)

---

## 3. Formal KPI Definitions

| # | KPI Name | Business Definition | Formula (Python / SQL / DAX) | Baseline Value |
|---|---|---|---|---|
| 1 | **Total Sales** | Gross net revenue across all valid order lines | `SUM(sales_amount)` | `$12,642,501.91` |
| 2 | **Total Orders** | Distinct customer orders placed | `COUNT(DISTINCT order_id)` | `25,035` |
| 3 | **Unique Customers** | Distinct active purchasing customers | `COUNT(DISTINCT customer_id)` | `1,590` |
| 4 | **Total Units Sold** | Cumulative item quantity shipped | `SUM(quantity)` | `178,312` |
| 5 | **Average Order Value (AOV)** | Mean revenue per distinct order | `SUM(sales_amount) / COUNT(DISTINCT order_id)` | `$504.99` |
| 6 | **Total Profit** | Net profit after cost & discounts | `SUM(profit)` | `$1,467,457.29` |
| 7 | **Profit Margin %** | Profit as a percentage of total sales | `(SUM(profit) / SUM(sales_amount)) * 100` | `11.61%` |
| 8 | **MoM Sales Growth %** | Month-over-month revenue change | `(Sales_t - Sales_{t-1}) / Sales_{t-1} * 100` | Varies by month |

---

## 4. Measurable Acceptance Criteria
1. **Data Accuracy:** Cleaned dataset and SQL star-schema `fact_sales` match raw CSV row counts and total sales within **0.1%** (observed variance: **0.0000%**).
2. **Core Visuals:** Top 10 products and chronological monthly trend match across Python, SQL, and BI.
3. **Interactive Controls:** Dashboard provides **>= 5 KPIs** (6+ delivered) and **>= 3 slicers** (`Order Date`, `Region`, `Product Category`, `Customer Segment`, `Market`) plus drill-down hierarchies.
