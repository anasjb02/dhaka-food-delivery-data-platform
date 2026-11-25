select
    order_id,
    cast(order_timestamp as timestamp) as ordered_at,
    order_date,
    user_id,
    r_id as restaurant_id,
    split_part(restaurant_city, ',', 1) as area,
    split_part(restaurant_city, ',', 2) as city,
    subtotal, discount, delivery_fee,
    gst as vat,
    sales_amount, payment_method, order_status,
    order_status = 'Delivered' as is_delivered,
    customer_rating, delivery_time_min
from {{ source('raw', 'orders') }}