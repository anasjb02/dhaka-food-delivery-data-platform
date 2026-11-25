select
    review_id,
    order_id,
    user_id,
    restaurant_id,
    rating,
    comment as review_text,
    cast(review_date as date) as review_date
from {{ source('raw', 'reviews') }}
