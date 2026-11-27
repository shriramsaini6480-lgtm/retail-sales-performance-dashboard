-- ============================================================================
-- Project 1: Retail Sales Performance Dashboard
-- Script: 04_views.sql
-- Purpose: Reusable Oracle reporting views for BI & Power BI connectivity
-- ============================================================================

CREATE OR REPLACE VIEW vw_sales_kpi_summary AS
SELECT
    COUNT(*)                                                   AS row_count,
    COUNT(DISTINCT order_id)                                   AS total_orders,
    COUNT(DISTINCT customer_id)                                AS unique_customers,
    SUM(quantity)                                              AS units_sold,
    ROUND(SUM(sales_amount), 2)                                AS total_sales,
    ROUND(SUM(profit), 2)                                      AS total_profit,
    ROUND(SUM(sales_amount) / COUNT(DISTINCT order_id), 2)     AS avg_order_value,
    ROUND((SUM(profit) / NULLIF(SUM(sales_amount), 0)) * 100, 2) AS profit_margin_pct
FROM fact_sales;

CREATE OR REPLACE VIEW vw_monthly_sales_trend AS
WITH monthly_base AS (
    SELECT
        d.year,
        d.quarter,
        d.month_num,
        d.year_month,
        COUNT(DISTINCT f.order_id)    AS total_orders,
        SUM(f.quantity)               AS units_sold,
        ROUND(SUM(f.sales_amount), 2) AS monthly_sales,
        ROUND(SUM(f.profit), 2)       AS monthly_profit
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    GROUP BY d.year, d.quarter, d.month_num, d.year_month
)
SELECT
    year,
    quarter,
    month_num,
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
FROM monthly_base;

CREATE OR REPLACE VIEW vw_top_10_products AS
SELECT *
FROM (
    SELECT
        RANK() OVER (ORDER BY SUM(f.sales_amount) DESC) AS sales_rank,
        p.category,
        p.sub_category,
        p.product_name,
        COUNT(DISTINCT f.order_id)    AS order_count,
        SUM(f.quantity)               AS units_sold,
        ROUND(SUM(f.sales_amount), 2) AS total_sales,
        ROUND(SUM(f.profit), 2)       AS total_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.category, p.sub_category, p.product_name
)
WHERE sales_rank <= 10;

CREATE OR REPLACE VIEW vw_regional_sales AS
SELECT
    g.market,
    g.region,
    g.country,
    COUNT(DISTINCT f.order_id)    AS total_orders,
    COUNT(DISTINCT f.customer_id) AS unique_customers,
    SUM(f.quantity)               AS units_sold,
    ROUND(SUM(f.sales_amount), 2) AS total_sales,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales_amount), 0)) * 100, 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_geography g ON f.geography_key = g.geography_key
GROUP BY g.market, g.region, g.country;

CREATE OR REPLACE VIEW vw_category_performance AS
SELECT
    p.category,
    p.sub_category,
    COUNT(DISTINCT f.order_id)    AS total_orders,
    SUM(f.quantity)               AS units_sold,
    ROUND(SUM(f.sales_amount), 2) AS total_sales,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales_amount), 0)) * 100, 2) AS profit_margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category, p.sub_category;

CREATE OR REPLACE VIEW vw_customer_performance AS
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(DISTINCT f.order_id)    AS total_orders,
    SUM(f.quantity)               AS units_purchased,
    ROUND(SUM(f.sales_amount), 2) AS total_sales,
    ROUND(SUM(f.profit), 2)       AS total_profit,
    DENSE_RANK() OVER (ORDER BY SUM(f.sales_amount) DESC) AS customer_rank
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment;

-- Denormalized reporting view for Power BI Import / DirectQuery
CREATE OR REPLACE VIEW vw_powerbi_sales_model AS
SELECT
    f.row_id,
    f.order_id,
    od.full_date      AS order_date,
    od.year           AS order_year,
    od.quarter_label  AS order_quarter,
    od.month_num      AS order_month_num,
    od.month_name     AS order_month_name,
    od.year_month     AS order_year_month,
    sd.full_date      AS ship_date,
    f.ship_mode,
    f.order_priority,
    c.customer_id,
    c.customer_name,
    c.segment,
    g.market,
    g.region,
    g.country,
    g.state,
    g.city,
    g.postal_code,
    p.product_key,
    p.product_id,
    p.category,
    p.sub_category,
    p.product_name,
    f.quantity,
    f.unit_price,
    f.discount,
    f.sales_amount,
    f.profit,
    f.shipping_cost,
    f.shipping_days
FROM fact_sales f
JOIN dim_date od     ON f.order_date_key = od.date_key
JOIN dim_date sd     ON f.ship_date_key  = sd.date_key
JOIN dim_customer c  ON f.customer_id    = c.customer_id
JOIN dim_product p   ON f.product_key    = p.product_key
JOIN dim_geography g ON f.geography_key  = g.geography_key;
