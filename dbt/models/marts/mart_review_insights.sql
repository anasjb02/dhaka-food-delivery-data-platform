{{ config(tags=['ai']) }}
select
    d.city, d.restaurant_id, d.restaurant_name,
    e.sentiment, e.topic,
    count(*) as review_count,
    avg(r.rating) as avg_rating
from {{ ref('stg_reviews') }} r
join {{ source('ai', 'review_enriched') }} e using (review_id)
join {{ ref('dim_restaurants') }} d on d.restaurant_id = r.restaurant_id
group by 1, 2, 3, 4, 5
