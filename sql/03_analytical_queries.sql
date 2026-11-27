-- ============================================================================
-- Project 1: Retail Sales Performance Dashboard
-- Script: 03_analytical_queries.sql
-- Purpose: Business KPIs, JOINs, GROUP BY, and Oracle Window Functions
-- ============================================================================

-- 1. Executive KPI Summary (5+ Core KPIs)
SELECT
    COUNT(*)                                                AS line_items,
    COUNT(DISTINCT f.order_id)                              AS total_orders,
    COUNT(DISTINCT f.customer_id)                           AS unique_customers,
    SUM(f.quantity)                                         AS total_units_sold,
    ROUND(SUM(f.sales_amount), 2)                           AS total_sales,
    ROUND(SUM(f.profit), 2)                                 AS total_profit,
    ROUND(SUM(f.sales_amount) / COUNT(DISTINCT f.order_id), 2) AS avg_order_value,
    ROUND((SUM(f.profit) / SUM(f.sales_amount)) * 100, 2)   AS profit_margin_pct
FROM fact_sales f;

-- 2. Monthly Sales Trend with Running Total & MoM Growth % (Window Functions: SUM OVER, LAG)
WITH monthly_agg AS (
    SELECT
        d.year,
        d.month_num,
        d.year_month,
        COUNT(DISTINCT f.order_id)    AS total_orders,
        SUM(f.quantity)               AS units_sold,
        ROUND(SUM(f.sales_amount), 2) AS monthly_sales,
        ROUND(SUM(f.profit), 2)       AS monthly_profit
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.year, d.month_num, d.year_month
)
SELECT
    year_month,
    total_orders,
    units_sold,
    monthly_sales,
    monthly_profit,
    ROUND(SUM(monthly_sales) OVER (ORDER BY year, month_num), 2) AS running_total_sales,
    ROUND(
        (monthly_sales - LAG(monthly_sales) OVER (ORDER BY year, month_num))
        / NULLIF(LAG(monthly_sales) OVER (ORDER BY year, month_num), 0) * 100,
        2
    ) AS mom_growth_pct
FROM monthly_agg
ORDER BY year, month_num;

-- 3. Top 10 Products by Sales Revenue (JOIN + GROUP BY + RANK/DENSE_RANK + % of Total)
WITH product_perf AS (
    SELECT
        p.category,
        p.sub_category,
        p.product_name,
        COUNT(DISTINCT f.order_id)    AS orders_count,
        SUM(f.quantity)               AS units_sold,
        ROUND(SUM(f.sales_amount), 2) AS total_sales,
        ROUND(SUM(f.profit), 2)       AS total_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.category, p.sub_category, p.product_name
),
ranked_products AS (
    SELECT
        RANK() OVER (ORDER BY total_sales DESC)       AS sales_rank,
        DENSE_RANK() OVER (ORDER BY total_sales DESC) AS dense_sales_rank,
        category,
        sub_category,
        product_name,
        orders_count,
        units_sold,
        total_sales,
        total_profit,
        ROUND(total_sales / SUM(total_sales) OVER () * 100, 2) AS pct_of_total_sales
    FROM product_perf
)
SELECT *
FROM ranked_products
WHERE sales_rank <= 10
ORDER BY sales_rank;

-- 4. Regional & Market Performance (PARTITION BY Market Window Function)
WITH region_agg AS (
    SELECT
        g.market,
        g.region,
        COUNT(DISTINCT f.order_id)    AS total_orders,
        COUNT(DISTINCT f.customer_id) AS unique_customers,
        ROUND(SUM(f.sales_amount), 2) AS total_sales,
        ROUND(SUM(f.profit), 2)       AS total_profit
    FROM fact_sales f
    JOIN dim_geography g ON f.geography_key = g.geography_key
    GROUP BY g.market, g.region
)
SELECT
    market,
    region,
    total_orders,
    unique_customers,
    total_sales,
    total_profit,
    ROUND((total_profit / NULLIF(total_sales, 0)) * 100, 2) AS profit_margin_pct,
    ROUND(total_sales / SUM(total_sales) OVER () * 100, 2)  AS global_sales_share_pct,
    RANK() OVER (PARTITION BY market ORDER BY total_sales DESC) AS rank_within_market
FROM region_agg
ORDER BY total_sales DESC;

-- 5. Category & Sub-Category Performance with Category Contribution %
WITH subcat_agg AS (
    SELECT
        p.category,
        p.sub_category,
        SUM(f.quantity)               AS units_sold,
        ROUND(SUM(f.sales_amount), 2) AS total_sales,
        ROUND(SUM(f.profit), 2)       AS total_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.category, p.sub_category
)
SELECT
    category,
    sub_category,
    units_sold,
    total_sales,
    total_profit,
    ROUND((total_profit / NULLIF(total_sales, 0)) * 100, 2) AS profit_margin_pct,
    ROUND(total_sales / SUM(total_sales) OVER (PARTITION BY category) * 100, 2) AS pct_within_category,
    RANK() OVER (PARTITION BY category ORDER BY total_sales DESC) AS rank_in_category
FROM subcat_agg
ORDER BY category, rank_in_category;

-- 6. Top 10 Customers by Sales & Segment Breakdown
SELECT *
FROM (
    SELECT
        RANK() OVER (ORDER BY SUM(f.sales_amount) DESC) AS customer_rank,
        c.customer_id,
        c.customer_name,
        c.segment,
        COUNT(DISTINCT f.order_id)    AS order_count,
        SUM(f.quantity)               AS units_purchased,
        ROUND(SUM(f.sales_amount), 2) AS total_sales,
        ROUND(SUM(f.profit), 2)       AS total_profit
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    GROUP BY c.customer_id, c.customer_name, c.segment
)
WHERE customer_rank <= 10
ORDER BY customer_rank;

-- 7. Year-over-Year (YoY) Performance by Category
WITH yearly_cat AS (
    SELECT
        d.year,
        p.category,
        ROUND(SUM(f.sales_amount), 2) AS annual_sales,
        ROUND(SUM(f.profit), 2)       AS annual_profit
    FROM fact_sales f
    JOIN dim_date d    ON f.order_date_key = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY d.year, p.category
)
SELECT
    year,
    category,
    annual_sales,
    annual_profit,
    LAG(annual_sales) OVER (PARTITION BY category ORDER BY year) AS prev_year_sales,
    ROUND(
        (annual_sales - LAG(annual_sales) OVER (PARTITION BY category ORDER BY year))
        / NULLIF(LAG(annual_sales) OVER (PARTITION BY category ORDER BY year), 0) * 100,
        2
    ) AS yoy_growth_pct
FROM yearly_cat
ORDER BY category, year;
