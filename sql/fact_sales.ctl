-- SQL*Loader Control File for fact_sales.csv
-- Usage: sqlldr userid=user/pass@dsn control=sql/fact_sales.ctl log=sql/fact_sales.log
OPTIONS (SKIP=1, DIRECT=TRUE)
LOAD DATA
INFILE 'dataset/star_schema/fact_sales.csv'
BADFILE 'sql/fact_sales.bad'
DISCARDFILE 'sql/fact_sales.dsc'
TRUNCATE
INTO TABLE fact_sales
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
TRAILING NULLCOLS
(
    row_id,
    order_id,
    order_date_key,
    ship_date_key,
    customer_id,
    product_key,
    geography_key,
    ship_mode,
    order_priority,
    quantity,
    unit_price,
    discount,
    sales_amount,
    profit,
    shipping_cost,
    shipping_days
)
