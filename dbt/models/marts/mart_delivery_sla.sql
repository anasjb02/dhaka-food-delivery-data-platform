select
    city, order_hour,
    count(*) as delivered_orders,
    quantile_cont(delivery_time_min, 0.5) as p50_min,
    quantile_cont(delivery_time_min, 0.9) as p90_min
from {{ ref('fct_orders') }}
where is_delivered
group by 1, 2
