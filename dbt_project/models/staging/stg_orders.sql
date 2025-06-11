{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        order_id,
        customer_id,
        product_id,
        order_date,
        quantity,
        unit_price,
        discount_amount,
        tax_amount,
        total_amount,
        order_status,
        payment_method,
        shipping_address,
        created_at,
        updated_at
    FROM {{ source('snow', 'orders') }}
    WHERE order_status IN ('COMPLETED', 'SHIPPED', 'DELIVERED')
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['order_id', 'product_id']) }} AS order_key,
    order_id,
    customer_id,
    product_id,
    -- Ensure proper date formatting for join with dim_dates
    DATE(order_date) AS order_date,
    quantity,
    unit_price,
    COALESCE(discount_amount, 0) AS discount_amount,
    COALESCE(tax_amount, 0) AS tax_amount,
    total_amount,
    order_status,
    payment_method,
    shipping_address,
    created_at,
    updated_at
FROM source_data