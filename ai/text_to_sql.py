"""Chat with the warehouse: English question -> DuckDB SQL -> result (read-only)."""
import os, re
import duckdb, requests
import streamlit as st

DB = "dbt/warehouse.duckdb"
MODEL = os.getenv("SQL_MODEL", "qwen2.5-coder:3b")
URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
TABLES = ["mart_daily_city_revenue", "mart_restaurant_performance",
          "mart_delivery_sla", "mart_review_insights"]
BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|"
    r"install|load|export|call|set)\b", re.I)

HINTS = """Table notes:
- mart_daily_city_revenue: one row per order_date and city. Columns orders, delivered_orders, gmv (revenue in BDT), cancel_rate, aov, gmv_rolling_7d.
- mart_restaurant_performance: one row per restaurant. Columns restaurant_name, city, cuisine, total_orders, gmv (revenue in BDT), avg_customer_rating, avg_delivery_min, city_gmv_rank.
- mart_delivery_sla: one row per city and order_hour. Columns delivered_orders, p50_min, p90_min.
- mart_review_insights: review counts by city, restaurant, sentiment (positive/neutral/negative) and topic.

Rules:
- Use only these tables. Prefer ONE table and avoid joins.
- Revenue means the gmv column.
- Cities are Dhaka, Chattogram, Sylhet, Khulna, Rajshahi.

Examples:
Q: Top 5 restaurants in Dhaka by revenue
SELECT restaurant_name, gmv FROM mart_restaurant_performance WHERE city = 'Dhaka' ORDER BY gmv DESC LIMIT 5
Q: Which city has the highest cancel rate?
SELECT city, 1 - SUM(delivered_orders) * 1.0 / SUM(orders) AS cancel_rate FROM mart_daily_city_revenue GROUP BY city ORDER BY cancel_rate DESC LIMIT 1
Q: How many negative reviews per city?
SELECT city, SUM(review_count) AS negative_reviews FROM mart_review_insights WHERE sentiment = 'negative' GROUP BY city ORDER BY negative_reviews DESC
"""


def schema_text():
    con = duckdb.connect(DB, read_only=True)
    marks = ",".join(["?"] * len(TABLES))
    rows = con.execute(
        "select table_name, column_name, data_type from information_schema.columns "
        f"where table_schema='main' and table_name in ({marks}) "
        "order by table_name, ordinal_position", TABLES).fetchall()
    con.close()
    out = {}
    for t, c, d in rows:
        out.setdefault(t, []).append(f"{c} {d}")
    return "\n".join(f"{t}({', '.join(cols)})" for t, cols in out.items())


def system_prompt():
    return ("You write exactly one DuckDB SQL SELECT query. Reply with SQL only, "
            "no explanation, no markdown.\n\nSchema:\n" + schema_text() + "\n\n" + HINTS)


def chat(messages):
    r = requests.post(URL, timeout=180, json={
        "model": MODEL, "stream": False,
        "options": {"temperature": 0}, "messages": messages})
    sql = r.json()["message"]["content"]
    return sql.replace("```sql", "").replace("```", "").strip().rstrip(";")


def is_safe(sql):
    s = sql.strip().lower()
    return (s.startswith("select") or s.startswith("with")) \
        and ";" not in s and not BLOCKED.search(s)


def run_sql(sql):
    con = duckdb.connect(DB, read_only=True)
    try:
        return con.execute(f"select * from ({sql}) limit 200").df()
    finally:
        con.close()


st.title("Chat with the warehouse")
question = st.text_input("Ask a question", "Top 5 restaurants in Dhaka by revenue")
if st.button("Run") and question:
    msgs = [{"role": "system", "content": system_prompt()},
            {"role": "user", "content": question}]
    sql = chat(msgs)
    for attempt in range(2):
        st.code(sql, language="sql")
        if not is_safe(sql):
            st.error("Blocked: only a single read-only SELECT is allowed.")
            break
        try:
            st.dataframe(run_sql(sql))
            break
        except Exception as e:
            if attempt == 0:
                st.warning(f"First attempt failed ({e}). Retrying once...")
                msgs += [{"role": "assistant", "content": sql},
                         {"role": "user", "content": f"That query failed with: {e}. "
                          "Fix it. Reply with SQL only."}]
                sql = chat(msgs)
            else:
                st.error(f"Query failed: {e}")
