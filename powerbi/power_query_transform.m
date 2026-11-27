// ============================================================================
// Project 1: Retail Sales Performance Dashboard
// File: powerbi/power_query_transform.m
// Purpose: Power Query M script to load Star Schema CSVs (or Oracle Views)
// Update `BaseFolder` to your local clone path before refreshing in Power BI.
// ============================================================================

let
    BaseFolder = "C:\path\to\Retail_Sales_Performance_Python\dataset\star_schema\",

    LoadFactSales = let
        Source = Csv.Document(File.Contents(BaseFolder & "fact_sales.csv"), [Delimiter=",", Columns=16, Encoding=65001, QuoteStyle=QuoteStyle.None]),
        PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
        ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
            {"row_id", Int64.Type},
            {"order_id", type text},
            {"order_date_key", Int64.Type},
            {"ship_date_key", Int64.Type},
            {"customer_id", type text},
            {"product_key", Int64.Type},
            {"geography_key", Int64.Type},
            {"ship_mode", type text},
            {"order_priority", type text},
            {"quantity", Int64.Type},
            {"unit_price", type number},
            {"discount", type number},
            {"sales_amount", type number},
            {"profit", type number},
            {"shipping_cost", type number},
            {"shipping_days", Int64.Type}
        })
    in
        ChangedType
in
    LoadFactSales
