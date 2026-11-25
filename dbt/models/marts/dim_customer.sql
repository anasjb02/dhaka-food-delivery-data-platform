select
    user_id, gender, occupation, monthly_income, education, family_size, age,
    case
        when age < 25 then 'Under 25'
        when age < 35 then '25-34'
        when age < 45 then '35-44'
        else '45+'
    end as age_segment
from {{ ref('stg_users') }}
