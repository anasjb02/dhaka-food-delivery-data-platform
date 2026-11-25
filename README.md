# Dhaka Food Delivery Data Platform

An end-to-end batch data pipeline on a synthetic Bangladesh food-delivery dataset: raw CSVs → DuckDB → dbt (staging, dimensions, facts, marts) → Airflow, with a local-LLM enrichment step that turns free-text reviews into structured sentiment and topic columns.

Based on Darshil Parmar's [Zomato AI Data Engineering tutorial](https://github.com/darshilparmar/zomato-ai-data-engineering-end-to-end-project). I rebuilt it from scratch and changed the data, stack and models (see below).

## Architecture

CSV files → DuckDB `raw` schema → dbt staging views → dbt gold tables → LLM enrichment → AI mart, orchestrated by one Airflow DAG:

`load_raw → dbt_build_core → enrich_reviews → dbt_build_ai`

## What I changed from the tutorial

- **Bangladeshi dataset.** Wrote a Python generator (`scripts/generate_bd_data.py`) for <ORDERS> orders, <REVIEWS> reviews, <RESTAURANTS> restaurants and <USERS> users across Dhaka, Chattogram, Sylhet, Khulna and Rajshahi, with BDT prices, bKash/Nagad/cash-on-delivery payments, lunch and dinner peaks, and monsoon delivery delays.
- **Fully local, free stack.** DuckDB replaces S3 + Snowflake, so anyone can run it at no cost.
- **Local LLM.** Llama 3.2 3B via Ollama classifies review sentiment and topic, instead of OpenAI. Output is idempotent, so reviews are never processed twice.
- **My own models.** Incremental `fct_orders`; marts for daily city revenue (7-day rolling GMV window function), restaurant ranking per city, delivery SLA (p50/p90) and review insights.
- **Data quality.** <N> dbt tests (uniqueness, not-null, relationships, accepted values) plus a custom revenue reconciliation test.

## Run it

```bash
python -m venv .venv && source .venv/Scripts/activate
pip install dbt-duckdb duckdb pandas requests
python scripts/generate_bd_data.py
python scripts/load_raw.py
cd dbt && dbt build --exclude tag:ai --profiles-dir .
```

For the full pipeline: `cd airflow && docker compose up -d --build`, open http://localhost:8082, and trigger `bd_food_pipeline`. Ollama (with `llama3.2:3b`) must be running for the enrichment step.

## Screenshots

**Airflow DAG**

![Airflow DAG](docs/screenshots/airflow_dag_graph.png)

**dbt lineage**

![dbt lineage](docs/screenshots/dbt_lineage.png)

## Challenges and lessons

- DuckDB misdetected the CSV header on a one-column table; fixed by declaring `header=true` explicitly.
- Installing dbt next to Airflow broke Airflow's dependencies; solved by putting dbt in its own virtualenv inside the Docker image.
- A shared dbt cache between Windows and the Linux container caused parse errors; disabled partial parsing.
- Docker filled the system drive; learned to monitor disk usage and clean images and build cache.
- The 3B model assigns one topic per review, so multi-topic reviews are only partly captured. A larger model or multi-label output would improve this.

## Limitations

The data is synthetic, so findings illustrate the pipeline, not real-world behaviour. The LLM labels were spot-checked, not formally evaluated.
