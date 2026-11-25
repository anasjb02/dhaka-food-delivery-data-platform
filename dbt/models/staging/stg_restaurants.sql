select
    id as restaurant_id,
    name as restaurant_name,
    city,
    try_cast(rating as double) as rating,
    rating_count,
    try_cast(regexp_replace(cost, '[^0-9.]', '', 'g') as integer) as avg_cost_bdt,
    cuisine,
    address
from {{ source('raw', 'restaurants') }}
