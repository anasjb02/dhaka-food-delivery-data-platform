FROM apache/airflow:3.3.1
RUN python -m venv /home/airflow/dbt_venv \
 && /home/airflow/dbt_venv/bin/pip install --no-cache-dir dbt-duckdb duckdb requests
