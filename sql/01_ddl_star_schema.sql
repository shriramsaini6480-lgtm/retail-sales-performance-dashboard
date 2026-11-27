-- ============================================================================
-- Project 1: Retail Sales Performance Dashboard
-- Script: 01_ddl_star_schema.sql
-- Target RDBMS: Oracle Database 19c / 21c / 23ai
-- Purpose: Create staging table, star schema dimensions, fact table, and indexes
-- ============================================================================

-- Clean drop block (idempotent re-runs)
BEGIN
    EXECUTE IMMEDIATE 'DROP VIEW vw_powerbi_sales_model';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/

BEGIN
    FOR t IN (
        SELECT table_name FROM user_tables
        WHERE table_name IN (
            'FACT_SALES', 'DIM_DATE', 'DIM_CUSTOMER',
            'DIM_PRODUCT', 'DIM_GEOGRAPHY', 'STG_RETAIL_SALES'
        )
    ) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS PURGE';
    END LOOP;
END;
/

-- 1. Staging table matching raw/cleaned flat structure
CREATE TABLE stg_retail_sales (
    row_id          NUMBER(10),
    order_id        VARCHAR2(30),
    order_date      DATE,
    ship_date       DATE,
    ship_mode       VARCHAR2(30),
    customer_id     VARCHAR2(30),
    customer_name   VARCHAR2(120),
    segment         VARCHAR2(40),
    city            VARCHAR2(100),
    state           VARCHAR2(100),
    country         VARCHAR2(100),
    postal_code     VARCHAR2(20),
    market          VARCHAR2(30),
    region          VARCHAR2(40),
    product_id      VARCHAR2(40),
    category        VARCHAR2(50),
    sub_category    VARCHAR2(50),
    product_name    VARCHAR2(255),
    sales_amount    NUMBER(14, 4),
    quantity        NUMBER(10),
    discount        NUMBER(8, 4),
    profit          NUMBER(14, 4),
    shipping_cost   NUMBER(14, 4),
    order_priority  VARCHAR2(30)
);

-- 2. Dimension: Date
CREATE TABLE dim_date (
    date_key        NUMBER(8)     CONSTRAINT pk_dim_date PRIMARY KEY,
    full_date       DATE          NOT NULL,
    year            NUMBER(4)     NOT NULL,
    quarter         NUMBER(1)     NOT NULL,
    quarter_label   VARCHAR2(10)  NOT NULL,
    month_num       NUMBER(2)     NOT NULL,
    month_name      VARCHAR2(10)  NOT NULL,
    year_month      VARCHAR2(7)   NOT NULL,
    day_of_month    NUMBER(2)     NOT NULL,
    day_name        VARCHAR2(15)  NOT NULL,
    is_weekend      NUMBER(1)     NOT NULL CHECK (is_weekend IN (0, 1))
);

-- 3. Dimension: Customer
CREATE TABLE dim_customer (
    customer_id     VARCHAR2(30)  CONSTRAINT pk_dim_customer PRIMARY KEY,
    customer_name   VARCHAR2(120) NOT NULL,
    segment         VARCHAR2(40)  NOT NULL
);

-- 4. Dimension: Product (surrogate key handles Product IDs mapped to multiple names)
CREATE TABLE dim_product (
    product_key     NUMBER(10)    CONSTRAINT pk_dim_product PRIMARY KEY,
    product_id      VARCHAR2(40)  NOT NULL,
    product_name    VARCHAR2(255) NOT NULL,
    category        VARCHAR2(50)  NOT NULL,
    sub_category    VARCHAR2(50)  NOT NULL
);

-- 5. Dimension: Geography
CREATE TABLE dim_geography (
    geography_key   NUMBER(10)    CONSTRAINT pk_dim_geography PRIMARY KEY,
    market          VARCHAR2(30)  NOT NULL,
    region          VARCHAR2(40)  NOT NULL,
    country         VARCHAR2(100) NOT NULL,
    state           VARCHAR2(100) NOT NULL,
    city            VARCHAR2(100) NOT NULL,
    postal_code     VARCHAR2(20)
);

-- 6. Fact Table: Sales (Grain = 1 Order Line Item / Row ID)
CREATE TABLE fact_sales (
    row_id          NUMBER(10)    CONSTRAINT pk_fact_sales PRIMARY KEY,
    order_id        VARCHAR2(30)  NOT NULL,
    order_date_key  NUMBER(8)     NOT NULL CONSTRAINT fk_fact_order_date REFERENCES dim_date(date_key),
    ship_date_key   NUMBER(8)     NOT NULL CONSTRAINT fk_fact_ship_date REFERENCES dim_date(date_key),
    customer_id     VARCHAR2(30)  NOT NULL CONSTRAINT fk_fact_customer REFERENCES dim_customer(customer_id),
    product_key     NUMBER(10)    NOT NULL CONSTRAINT fk_fact_product REFERENCES dim_product(product_key),
    geography_key   NUMBER(10)    NOT NULL CONSTRAINT fk_fact_geography REFERENCES dim_geography(geography_key),
    ship_mode       VARCHAR2(30)  NOT NULL,
    order_priority  VARCHAR2(30)  NOT NULL,
    quantity        NUMBER(10)    NOT NULL CONSTRAINT chk_fact_qty_pos CHECK (quantity > 0),
    unit_price      NUMBER(14, 4) NOT NULL,
    discount        NUMBER(8, 4)  DEFAULT 0 NOT NULL,
    sales_amount    NUMBER(14, 4) NOT NULL CONSTRAINT chk_fact_sales_pos CHECK (sales_amount > 0),
    profit          NUMBER(14, 4) DEFAULT 0 NOT NULL,
    shipping_cost   NUMBER(14, 4) DEFAULT 0 NOT NULL,
    shipping_days   NUMBER(5)     DEFAULT 0 NOT NULL
);

-- Performance indexes for analytical joins and slicers
CREATE INDEX idx_fact_order_date ON fact_sales(order_date_key);
CREATE INDEX idx_fact_customer   ON fact_sales(customer_id);
CREATE INDEX idx_fact_product    ON fact_sales(product_key);
CREATE INDEX idx_fact_geography  ON fact_sales(geography_key);
CREATE INDEX idx_fact_order_id   ON fact_sales(order_id);
CREATE INDEX idx_dim_geo_region  ON dim_geography(market, region);
CREATE INDEX idx_dim_prod_cat    ON dim_product(category, sub_category);
CREATE INDEX idx_dim_date_ym     ON dim_date(year, month_num, year_month);
