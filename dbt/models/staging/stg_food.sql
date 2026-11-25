select
    f_id as food_id,
    item as food_name,
    veg_or_non_veg as diet_type
from {{ source('raw', 'food') }}
