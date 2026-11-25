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
    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"cd /opt/project/dbt && {VENV}/dbt build --exclude tag:ai --profiles-dir .",
    )
    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"cd /opt/project && {VENV}/python ai/enrich_reviews.py",
    )
    dbt_build_ai = BashOperator(
        task_id="dbt_build_ai",
        bash_command=f"cd /opt/project/dbt && {VENV}/dbt build --select tag:ai --profiles-dir .",
    )
    load_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai
