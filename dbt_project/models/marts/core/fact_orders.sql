{{ config(
    materialized='table',
    unique_key='order_key'
) }}

WITH order_facts AS (
    SELECT
        o.order_key,
        c.customer_key,
        p.product_key,
        -- Use COALESCE to handle missing date matches, defaulting to a specific date_key
        COALESCE(d.date_key, 
                 (SELECT date_key FROM {{ ref('dim_dates') }} WHERE full_date = '1900-01-01')
                ) AS date_key,
        o.order_id,
        o.quantity,
        o.unit_price,
        o.discount_amount,
        o.tax_amount,
        o.total_amount,
        (o.quantity * o.unit_price) AS gross_amount,
        ((o.quantity * o.unit_price) - o.discount_amount) AS net_amount,
        (o.quantity * COALESCE(p.cost_price, 0)) AS total_cost,
        (o.total_amount - (o.quantity * COALESCE(p.cost_price, 0))) AS profit_amount,
        o.order_status,
        o.payment_method,
        o.created_at,
        -- Add flag to identify records with missing date matches
        CASE WHEN d.date_key IS NULL THEN 1 ELSE 0 END AS missing_date_flag
    FROM {{ ref('stg_orders') }} o
    LEFT JOIN {{ ref('dim_customers') }} c
        ON o.customer_id = c.customer_id
    LEFT JOIN {{ ref('dim_products') }} p
        ON o.product_id = p.product_id
    LEFT JOIN {{ ref('dim_dates') }} d
        ON o.order_date = d.full_date
)

SELECT
    order_key,
    customer_key,
    product_key,
    date_key,
    order_id,
    quantity,
    unit_price,
    discount_amount,
    tax_amount,
    total_amount,
    gross_amount,
    net_amount,
    total_cost,
    profit_amount,
    CASE
        WHEN total_cost > 0 THEN ROUND((profit_amount / total_cost) * 100, 2)
        ELSE 0
    END AS profit_margin_pct,
    order_status,
    payment_method,
    created_at,
    missing_date_flag,
    CURRENT_TIMESTAMP AS dw_created_at,
    CURRENT_TIMESTAMP AS dw_updated_at
FROM order_facts