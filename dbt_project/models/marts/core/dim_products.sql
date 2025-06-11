{{ config(
    materialized='table',
    unique_key='product_key'
) }}

SELECT
    product_key,
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    supplier,
    unit_price,
    cost_price,
    profit_margin_pct,
    CASE 
        WHEN profit_margin_pct >= 50 THEN 'HIGH'
        WHEN profit_margin_pct >= 25 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS profit_margin_tier,
    CASE 
        WHEN unit_price >= 1000 THEN 'PREMIUM'
        WHEN unit_price >= 100 THEN 'MID-RANGE'
        ELSE 'BUDGET'
    END AS price_tier,
    description,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP AS dw_created_at,
    CURRENT_TIMESTAMP AS dw_updated_at
FROM {{ ref('stg_products') }}