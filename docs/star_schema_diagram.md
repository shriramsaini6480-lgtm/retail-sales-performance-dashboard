# Star Schema Architecture & ER Diagram (Project 1)

## 1. Conceptual Star Schema

The raw flat CSV (`51,290` rows x `24` columns) is normalized into **1 Fact Table** (`fact_sales`) and **4 Conformed Dimension Tables** (`dim_date`, `dim_customer`, `dim_product`, `dim_geography`) to eliminate data redundancy and prevent fan-out joins.

> **Design Note on `dim_product`:** In the source dataset, `10,292` distinct `Product ID` values map to `10,768` unique `(Product ID, Product Name, Category, Sub-Category)` combinations. Using a surrogate integer `product_key` prevents many-to-many join inflation.

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_SALES : "order_date_key / ship_date_key"
    DIM_CUSTOMER ||--o{ FACT_SALES : "customer_id"
    DIM_PRODUCT ||--o{ FACT_SALES : "product_key"
    DIM_GEOGRAPHY ||--o{ FACT_SALES : "geography_key"

    FACT_SALES {
        NUMBER row_id PK
        VARCHAR2 order_id
        NUMBER order_date_key FK
        NUMBER ship_date_key FK
        VARCHAR2 customer_id FK
        NUMBER product_key FK
        NUMBER geography_key FK
        VARCHAR2 ship_mode
        VARCHAR2 order_priority
        NUMBER quantity
        NUMBER unit_price
        NUMBER discount
        NUMBER sales_amount
        NUMBER profit
        NUMBER shipping_cost
        NUMBER shipping_days
    }

    DIM_DATE {
        NUMBER date_key PK
        DATE full_date
        NUMBER year
        NUMBER quarter
        VARCHAR2 quarter_label
        NUMBER month_num
        VARCHAR2 month_name
        VARCHAR2 year_month
        NUMBER day_of_month
        VARCHAR2 day_name
        NUMBER is_weekend
    }

    DIM_CUSTOMER {
        VARCHAR2 customer_id PK
        VARCHAR2 customer_name
        VARCHAR2 segment
    }

    DIM_PRODUCT {
        NUMBER product_key PK
        VARCHAR2 product_id
        VARCHAR2 product_name
        VARCHAR2 category
        VARCHAR2 sub_category
    }

    DIM_GEOGRAPHY {
        NUMBER geography_key PK
        VARCHAR2 market
        VARCHAR2 region
        VARCHAR2 country
        VARCHAR2 state
        VARCHAR2 city
        VARCHAR2 postal_code
    }
```

---

## 2. Table Summary & Observed Row Counts

| Table | Role | Primary Key | Row Count | Notes |
|---|---|---|---|---|
| `fact_sales` | Fact (Grain: 1 order line) | `row_id` | `51,290` | Validated `quantity > 0` and `sales_amount > 0` |
| `dim_date` | Calendar Dimension | `date_key` (`YYYYMMDD`) | `1,468` | Covers all order dates & ship dates (`2011-01-01` to `2015-01-07`) |
| `dim_customer` | Customer Dimension | `customer_id` | `1,590` | 1:1 mapping with `customer_name` and `segment` |
| `dim_product` | Product Dimension | `product_key` (surrogate) | `10,768` | Preserves `Category -> Sub-Category -> Product Name` drill-down |
| `dim_geography` | Geography Dimension | `geography_key` (surrogate) | `3,847` | Preserves `Market -> Region -> Country -> State -> City` drill-down |
