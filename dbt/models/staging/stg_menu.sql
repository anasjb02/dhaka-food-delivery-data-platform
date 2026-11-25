select
    menu_id,
    r_id as restaurant_id,
    f_id as food_id,
    cuisine,
    price
from {{ source('raw', 'menu') }}
