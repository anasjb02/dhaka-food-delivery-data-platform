with stats as (
    select
        restaurant_id,
        count(*) as total_orders,
        coalesce(sum(sales_amount) filter (where is_delivered), 0) as gmv,
        avg(customer_rating) as avg_customer_rating,
        avg(delivery_time_min) as avg_delivery_min
    from {{ ref('fct_orders') }}
    group by 1
)
select
    r.restaurant_id, r.restaurant_name, r.city, r.cuisine,
    s.total_orders, s.gmv, s.avg_customer_rating, s.avg_delivery_min,
    rank() over (partition by r.city order by s.gmv desc) as city_gmv_rank
from stats s
join {{ ref('dim_restaurants') }} r using (restaurant_id)
