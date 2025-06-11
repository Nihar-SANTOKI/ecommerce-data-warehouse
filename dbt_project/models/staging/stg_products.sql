{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        product_id,
        product_name,
        category,
        subcategory,
        brand,
        supplier,
        unit_price,
        cost_price,
        description,
        is_active,
        created_at,
        updated_at
    FROM {{ source('snow', 'products') }}
    WHERE is_active = true
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} AS product_key,
    product_id,
    TRIM(product_name) AS product_name,
    UPPER(TRIM(category)) AS category,
    UPPER(TRIM(subcategory)) AS subcategory,
    UPPER(TRIM(brand)) AS brand,
    TRIM(supplier) AS supplier,
    unit_price,
    cost_price,
    ROUND((unit_price - cost_price) / unit_price * 100, 2) AS profit_margin_pct,
    description,
    created_at,
    updated_at
FROM source_data