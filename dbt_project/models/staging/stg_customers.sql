{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        customer_id,
        first_name,
        last_name,
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
        is_active,
        created_at,
        updated_at
    FROM {{ source('snow', 'customers') }}
    WHERE is_active = true
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_key,
    customer_id,
    TRIM(UPPER(first_name)) AS first_name,
    TRIM(UPPER(last_name)) AS last_name,
    LOWER(TRIM(email)) AS email,
    phone,
    address_line_1,
    address_line_2,
    city,
    state,
    country,
    postal_code,
    registration_date,
    COALESCE(customer_segment, 'UNKNOWN') AS customer_segment,
    created_at,
    updated_at
FROM source_data