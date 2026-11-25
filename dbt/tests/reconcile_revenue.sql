-- fails if the mart's total revenue differs from the fact table's
with a as (select sum(gmv) as mart_total from {{ ref('mart_daily_city_revenue') }}),
     b as (select sum(sales_amount) as fact_total from {{ ref('fct_orders') }} where is_delivered)
select * from a, b where abs(mart_total - fact_total) > 0.01
