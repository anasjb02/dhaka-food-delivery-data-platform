"""Enrich reviews with sentiment + topic using a local Ollama model."""
import json, os
import duckdb, requests

DB = "dbt/warehouse.duckdb"
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
SAMPLE_N = int(os.getenv("SAMPLE_N", "200"))
URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
TOPICS = ["food_quality", "delivery_speed", "packaging", "price_value",
          "portion_size", "order_accuracy", "service", "other"]
PROMPT = ("You classify food delivery reviews. Reply with JSON only, like "
          '{"sentiment": "positive", "topic": "delivery_speed"}. '
          "sentiment must be positive, neutral or negative. topic must be one of: "
          + ", ".join(TOPICS) + ".")

con = duckdb.connect(DB)
con.execute("create schema if not exists ai")
con.execute("""create table if not exists ai.review_enriched (
    review_id bigint, sentiment varchar, topic varchar,
    model varchar, enriched_at timestamp)""")

rows = con.execute("""
    select r.review_id, r.review_text
    from main.stg_reviews r
    left join ai.review_enriched e using (review_id)
    where e.review_id is null
    order by r.review_id
    limit ?""", [SAMPLE_N]).fetchall()

done = 0
for rid, text in rows:
    try:
        resp = requests.post(URL, timeout=120, json={
            "model": MODEL, "stream": False, "format": "json",
            "options": {"temperature": 0},
            "messages": [{"role": "system", "content": PROMPT},
                         {"role": "user", "content": text}],
        })
        out = json.loads(resp.json()["message"]["content"])
        sentiment = str(out.get("sentiment", "")).lower()
        topic = out.get("topic", "other")
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "unknown"
        if topic not in TOPICS:
            topic = "other"
    except Exception as e:
        print(f"review {rid} failed: {e}")
        continue
    con.execute("insert into ai.review_enriched values (?, ?, ?, ?, now())",
                [rid, sentiment, topic, MODEL])
    done += 1
    if done % 20 == 0:
        print(f"{done}/{len(rows)}")

print(f"enriched {done} reviews")
