select restaurant_id, restaurant_name, city, rating, avg_cost_bdt, cuisine, address
from {{ ref('stg_restaurants') }}
