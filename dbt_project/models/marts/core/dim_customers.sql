{{ config(
    materialized='table',
    unique_key='customer_key'
) }}

SELECT
    customer_key,
    customer_id,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name,
    email,
    phone,
    address_line_1,
    address_line_2,
    city,
    state,
    country,
    postal_code,
    registration_date,
    customer_segment,
    CASE 
        WHEN registration_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'NEW'
        WHEN registration_date >= CURRENT_DATE - INTERVAL '365 days' THEN 'RECENT'
        ELSE 'ESTABLISHED'
    END AS customer_tenure,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP AS dw_created_at,
    CURRENT_TIMESTAMP AS dw_updated_at
FROM {{ ref('stg_customers') }}