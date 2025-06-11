{{ config(materialized='table') }}

WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('1900-01-01' as date)",
        end_date="cast('2030-12-31' as date)"
    ) }}
),

date_dimension AS (
    SELECT
        date_day AS full_date,
        {{ dbt_utils.generate_surrogate_key(['date_day']) }} AS date_key,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        EXTRACT(MONTH FROM date_day) AS month,
        EXTRACT(DAY FROM date_day) AS day,
        EXTRACT(DAYOFWEEK FROM date_day) AS day_of_week,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        DAYNAME(date_day) AS day_name,
        MONTHNAME(date_day) AS month_name,
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM date_day) IN (1, 7) THEN TRUE 
            ELSE FALSE 
        END AS is_weekend,
        CASE 
            WHEN date_day IN (
                '1900-01-01',  -- Fallback date
                '2024-01-01', '2024-07-04', '2024-12-25',
                '2025-01-01', '2025-07-04', '2025-12-25',
                '2026-01-01', '2026-07-04', '2026-12-25'
                -- Add more holidays as needed
            ) THEN TRUE 
            ELSE FALSE 
        END AS is_holiday
    FROM date_spine
)

SELECT
    date_key,
    full_date,
    year,
    quarter,
    month,
    day,
    day_of_week,
    week_of_year,
    day_name,
    month_name,
    is_weekend,
    is_holiday,
    CONCAT('Q', quarter, ' ', year) AS quarter_name,
    CONCAT(month_name, ' ', year) AS month_year,
    CURRENT_TIMESTAMP AS dw_created_at,
    CURRENT_TIMESTAMP AS dw_updated_at
FROM date_dimension