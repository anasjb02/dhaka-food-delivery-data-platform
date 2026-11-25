select
    order_item_id,
    order_id,
    r_id as restaurant_id,
    f_id as food_id,
    price,
    quantity,
    line_amount
from {{ source('raw', 'order_items') }}
