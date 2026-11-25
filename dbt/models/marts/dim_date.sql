select
    d::date as date_day,
    year(d) as year,
    month(d) as month,
    monthname(d) as month_name,
    dayname(d) as day_name,
    dayofweek(d) in (5, 6) as is_weekend  -- Bangladesh weekend: Fri-Sat
from generate_series(date '2025-11-01', date '2026-12-31', interval 1 day) as t(d)
