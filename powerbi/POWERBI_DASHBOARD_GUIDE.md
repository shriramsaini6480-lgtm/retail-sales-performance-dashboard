# Power BI Dashboard Build Guide (Project 1)

> **Note:** Power BI Desktop (`.pbix`) is a Windows desktop binary format that must be assembled and saved inside Microsoft Power BI Desktop. All underlying star-schema tables (`dataset/star_schema/*.csv`), Oracle views (`sql/04_views.sql`), DAX measures (`powerbi/measures.dax`), Power Query M (`powerbi/power_query_transform.m`), and theme (`powerbi/theme.json`) are pre-built and reconciled here.

---

## 1. Data Ingestion (Oracle or Star Schema CSVs)

### Option A — Connect to Oracle Database
1. Open **Power BI Desktop** -> **Get Data** -> **Oracle database**.
2. Enter your Oracle Server/DSN (e.g., `localhost:1521/XEPDB1`) and load:
   - `FACT_SALES`
   - `DIM_DATE`
   - `DIM_CUSTOMER`
   - `DIM_PRODUCT`
   - `DIM_GEOGRAPHY`
   *(Or load the pre-joined `VW_POWERBI_SALES_MODEL` view for single-table import.)*

### Option B — Connect to Local Star Schema CSVs
1. Open **Get Data** -> **Text/CSV** and import all 5 files from `dataset/star_schema/`:
   - `fact_sales.csv`
   - `dim_date.csv`
   - `dim_customer.csv`
   - `dim_product.csv`
   - `dim_geography.csv`
2. Apply `powerbi/theme.json` via **View -> Themes -> Browse for themes**.

---

## 2. Star-Schema Relationships (Model View)

Create **Many-to-One (`*:1`) Single-Direction** relationships:
1. `fact_sales[order_date_key]` -> `dim_date[date_key]` (Active)
2. `fact_sales[ship_date_key]` -> `dim_date[date_key]` (Inactive, for `USERELATIONSHIP`)
3. `fact_sales[customer_id]` -> `dim_customer[customer_id]` (Active)
4. `fact_sales[product_key]` -> `dim_product[product_key]` (Active)
5. `fact_sales[geography_key]` -> `dim_geography[geography_key]` (Active)

Mark `dim_date` as the **Date Table** (`full_date`).

---

## 3. Create Hierarchies for Drill-Down

1. **Calendar Hierarchy** (`dim_date`):
   `year` -> `quarter_label` -> `month_name` (sort by `month_num`) -> `full_date`
2. **Product Hierarchy** (`dim_product`):
   `category` -> `sub_category` -> `product_name`
3. **Geography Hierarchy** (`dim_geography`):
   `market` -> `region` -> `country` -> `state` -> `city`

---

## 4. Import DAX Measures (`powerbi/measures.dax`)

Create a `_Measures` table and paste the measures from `powerbi/measures.dax`:
- **KPI Cards (6 cards)**: `[Total Sales]`, `[Total Orders]`, `[Unique Customers]`, `[Total Units Sold]`, `[Average Order Value]`, `[Profit Margin %]`

---

## 5. Dashboard Page Layout (Slicers, Visuals & Drill-Down)

### Top Bar — Slicers (4 Slicers; >= 3 required)
1. **Date Slicer** (`dim_date[full_date]` — Between slider)
2. **Region Slicer** (`dim_geography[region]` — Dropdown / Tile)
3. **Product Category Slicer** (`dim_product[category]` — Dropdown / Tile)
4. **Customer Segment Slicer** (`dim_customer[segment]` — Horizontal Tile)

### Row 1 — 6 Executive KPI Cards
- Total Sales (`$12.64M`)
- Total Orders (`25,035`)
- Unique Customers (`1,590`)
- Total Units Sold (`178,312`)
- Average Order Value (`$504.99`)
- Profit Margin % (`11.61%`)

### Row 2 — Core Trend & Regional Charts
1. **Monthly Sales Trend (Line Chart)**:
   - X-axis: `Calendar Hierarchy` (`year` -> `quarter_label` -> `month_name`) for drill-down
   - Y-axis: `[Total Sales]` (and secondary line `[Total Profit]` or `[Running Total Sales]`)
2. **Regional Sales & Profit (Clustered Bar / Map Visual)**:
   - Y-axis: `Geography Hierarchy` (`market` -> `region` -> `country`) for drill-down
   - X-axis: `[Total Sales]`, Color/Tooltip: `[Total Profit]`, `[Profit Margin %]`

### Row 3 — Product & Category Breakdown
1. **Top 10 Products (Horizontal Bar Chart)**:
   - Y-axis: `dim_product[product_name]`
   - X-axis: `[Total Sales]`
   - Visual-level filter: `Product Sales Rank` <= 10 (or Top N filter = Top 10 by `[Total Sales]`)
2. **Sales by Category & Sub-Category (Stacked Bar / Treemap with Drill-Down)**:
   - Group/Axis: `Product Hierarchy` (`category` -> `sub_category`)
   - Values: `[Total Sales]`, Tooltip: `[Profit Margin %]`

---

## 6. Reconciliation Checklist (Before Saving `Retail_Sales_Performance.pbix`)
Verify with all slicers cleared:
- `[Fact Row Count]` = **51,290**
- `[Total Sales]` = **$12,642,501.91** (0.0000% variance vs CSV and Oracle SQL)
- `[Total Orders]` = **25,035**
- `[Unique Customers]` = **1,590**
- Test **Region slicer** (`Central`, `Oceania`, `East`, etc.) and verify KPI cards, Top 10 products, and monthly trend update dynamically.
- Save final workbook as `powerbi/Retail_Sales_Performance.pbix`.
