from datetime import datetime
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

VENV = "/home/airflow/dbt_venv/bin"

with DAG(
    dag_id="bd_food_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    tags=["bd_food"],
) as dag:
    load_raw = BashOperator(
        task_id="load_raw",
        bash_command=f"cd /opt/project && {VENV}/python scripts/load_raw.py",
    )
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd /opt/project/dbt && {VENV}/dbt build --profiles-dir .",
    )
    load_raw >> dbt_build
