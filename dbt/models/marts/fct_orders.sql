{{ config(materialized='incremental', unique_key='order_id', incremental_strategy='delete+insert') }}
select
    order_id, ordered_at, order_date,
    extract(hour from ordered_at) as order_hour,
    user_id, restaurant_id, area, city,
    subtotal, discount, delivery_fee, vat, sales_amount,
    payment_method, order_status, is_delivered,
    customer_rating, delivery_time_min
from {{ ref('stg_orders') }}
{% if is_incremental() %}
where ordered_at > (select max(ordered_at) from {{ this }})
{% endif %}
