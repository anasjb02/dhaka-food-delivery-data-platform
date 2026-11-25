select
    user_id,
    name as user_name,
    lower(email) as email,
    "Age" as age,
    "Gender" as gender,
    "Marital Status" as marital_status,
    "Occupation" as occupation,
    "Monthly Income" as monthly_income,
    "Educational Qualifications" as education,
    "Family size" as family_size
from {{ source('raw', 'users') }}
