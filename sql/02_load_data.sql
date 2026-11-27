-- ============================================================================
-- Project 1: Retail Sales Performance Dashboard
-- Script: 02_load_data.sql
-- Purpose: Populate Star Schema tables from staging or verify SQL*Loader loads
-- ============================================================================
-- Option A (Recommended): Load pre-normalized CSVs in dataset/star_schema/ via:
--   1. python sql/load_to_oracle.py
--   2. OR SQL*Loader using sql/star_schema_loader.ctl files
--
-- Option B: If staging data was loaded into stg_retail_sales, run the SQL
-- below to populate dim_date, dim_customer, dim_product, dim_geography,
-- and fact_sales inside Oracle.
-- ============================================================================

-- 1. Load dim_date from all distinct order_date and ship_date values
MERGE INTO dim_date tgt
USING (
    SELECT DISTINCT
        TO_NUMBER(TO_CHAR(d, 'YYYYMMDD')) AS date_key,
        d AS full_date,
        EXTRACT(YEAR FROM d) AS year,
        TO_NUMBER(TO_CHAR(d, 'Q')) AS quarter,
        'Q' || TO_CHAR(d, 'Q') || ' ' || TO_CHAR(d, 'YYYY') AS quarter_label,
        EXTRACT(MONTH FROM d) AS month_num,
        TO_CHAR(d, 'Mon', 'NLS_DATE_LANGUAGE=ENGLISH') AS month_name,
        TO_CHAR(d, 'YYYY-MM') AS year_month,
        EXTRACT(DAY FROM d) AS day_of_month,
        TRIM(TO_CHAR(d, 'Day', 'NLS_DATE_LANGUAGE=ENGLISH')) AS day_name,
        CASE WHEN TO_CHAR(d, 'DY', 'NLS_DATE_LANGUAGE=ENGLISH') IN ('SAT', 'SUN') THEN 1 ELSE 0 END AS is_weekend
    FROM (
        SELECT order_date AS d FROM stg_retail_sales WHERE order_date IS NOT NULL
        UNION
        SELECT ship_date AS d FROM stg_retail_sales WHERE ship_date IS NOT NULL
    )
) src
ON (tgt.date_key = src.date_key)
WHEN NOT MATCHED THEN
    INSERT (date_key, full_date, year, quarter, quarter_label, month_num, month_name, year_month, day_of_month, day_name, is_weekend)
    VALUES (src.date_key, src.full_date, src.year, src.quarter, src.quarter_label, src.month_num, src.month_name, src.year_month, src.day_of_month, src.day_name, src.is_weekend);

-- 2. Load dim_customer
MERGE INTO dim_customer tgt
USING (
    SELECT customer_id,
           MAX(customer_name) AS customer_name,
           MAX(segment) AS segment
    FROM stg_retail_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
) src
ON (tgt.customer_id = src.customer_id)
WHEN NOT MATCHED THEN
    INSERT (customer_id, customer_name, segment)
    VALUES (src.customer_id, src.customer_name, src.segment);

-- 3. Load dim_product
INSERT INTO dim_product (product_key, product_id, product_name, category, sub_category)
SELECT
    ROW_NUMBER() OVER (ORDER BY product_id, product_name, category, sub_category) AS product_key,
    product_id,
    product_name,
    category,
    sub_category
FROM (
    SELECT DISTINCT product_id, product_name, category, sub_category
    FROM stg_retail_sales
    WHERE product_id IS NOT NULL AND product_name IS NOT NULL
) s
WHERE NOT EXISTS (
    SELECT 1 FROM dim_product d
    WHERE d.product_id = s.product_id
      AND d.product_name = s.product_name
      AND d.category = s.category
      AND d.sub_category = s.sub_category
);

-- 4. Load dim_geography
INSERT INTO dim_geography (geography_key, market, region, country, state, city, postal_code)
SELECT
    ROW_NUMBER() OVER (ORDER BY market, region, country, state, city, postal_code) AS geography_key,
    market,
    region,
    country,
    state,
    city,
    postal_code
FROM (
    SELECT DISTINCT market, region, country, state, city, NVL(postal_code, '') AS postal_code
    FROM stg_retail_sales
) s
WHERE NOT EXISTS (
    SELECT 1 FROM dim_geography g
    WHERE g.market = s.market
      AND g.region = s.region
      AND g.country = s.country
      AND g.state = s.state
      AND g.city = s.city
      AND NVL(g.postal_code, '') = s.postal_code
);

-- 5. Load fact_sales
INSERT INTO fact_sales (
    row_id, order_id, order_date_key, ship_date_key, customer_id,
    product_key, geography_key, ship_mode, order_priority,
    quantity, unit_price, discount, sales_amount, profit, shipping_cost, shipping_days
)
SELECT
    s.row_id,
    s.order_id,
    TO_NUMBER(TO_CHAR(s.order_date, 'YYYYMMDD')) AS order_date_key,
    TO_NUMBER(TO_CHAR(s.ship_date, 'YYYYMMDD')) AS ship_date_key,
    s.customer_id,
    p.product_key,
    g.geography_key,
    s.ship_mode,
    s.order_priority,
    s.quantity,
    ROUND(s.sales_amount / s.quantity, 4) AS unit_price,
    s.discount,
    s.sales_amount,
    s.profit,
    s.shipping_cost,
    (s.ship_date - s.order_date) AS shipping_days
FROM stg_retail_sales s
JOIN dim_product p
  ON p.product_id = s.product_id
 AND p.product_name = s.product_name
 AND p.category = s.category
 AND p.sub_category = s.sub_category
JOIN dim_geography g
  ON g.market = s.market
 AND g.region = s.region
 AND g.country = s.country
 AND g.state = s.state
 AND g.city = s.city
 AND NVL(g.postal_code, '') = NVL(s.postal_code, '')
WHERE s.quantity > 0
  AND s.sales_amount > 0;

COMMIT;

-- Post-load reconciliation check
SELECT
    COUNT(*)                         AS fact_row_count,
    COUNT(DISTINCT order_id)         AS unique_orders,
    COUNT(DISTINCT customer_id)      AS unique_customers,
    SUM(quantity)                    AS total_units_sold,
    ROUND(SUM(sales_amount), 2)      AS total_sales,
    ROUND(SUM(profit), 2)            AS total_profit
FROM fact_sales;
