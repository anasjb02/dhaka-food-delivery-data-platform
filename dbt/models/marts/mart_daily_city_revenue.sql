with daily as (
    select
        order_date, city,
        count(*) as orders,
        count(*) filter (where is_delivered) as delivered_orders,
        coalesce(sum(sales_amount) filter (where is_delivered), 0) as gmv,
        1 - (count(*) filter (where is_delivered))::double / count(*) as cancel_rate
    from {{ ref('fct_orders') }}
    group by 1, 2
)
select
    *,
    gmv / nullif(delivered_orders, 0) as aov,
    sum(gmv) over (
        partition by city order by order_date
        rows between 6 preceding and current row
    ) as gmv_rolling_7d
from daily
