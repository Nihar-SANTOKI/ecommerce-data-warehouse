{{ config(materialized='table') }}

WITH monthly_revenue AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        COUNT(DISTINCT f.order_id) AS total_orders,
        COUNT(DISTINCT f.customer_key) AS unique_customers,
        SUM(f.total_amount) AS total_revenue,
        SUM(f.profit_amount) AS total_profit,
        AVG(f.total_amount) AS avg_order_value,
        SUM(f.quantity) AS total_quantity_sold
    FROM {{ ref('fact_orders') }} f
    JOIN {{ ref('dim_dates') }} d ON f.date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
),

revenue_with_growth AS (
    SELECT
        *,
        LAG(total_revenue, 1) OVER (ORDER BY year, month) AS prev_month_revenue,
        LAG(total_orders, 1) OVER (ORDER BY year, month) AS prev_month_orders
    FROM monthly_revenue
)

SELECT
    year,
    month,
    month_name,
    total_orders,
    unique_customers,
    total_revenue,
    total_profit,
    ROUND(total_profit / total_revenue * 100, 2) AS profit_margin_pct,
    avg_order_value,
    total_quantity_sold,
    CASE 
        WHEN prev_month_revenue > 0 THEN 
            ROUND(((total_revenue - prev_month_revenue) / prev_month_revenue) * 100, 2)
        ELSE NULL 
    END AS revenue_growth_pct,
    CASE 
        WHEN prev_month_orders > 0 THEN 
            ROUND(((total_orders - prev_month_orders) / prev_month_orders) * 100, 2)
        ELSE NULL 
    END AS order_growth_pct,
    CURRENT_TIMESTAMP AS dw_created_at,
    CURRENT_TIMESTAMP AS dw_updated_at
FROM revenue_with_growth
ORDER BY year, month