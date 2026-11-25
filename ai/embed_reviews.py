"""Embed review text with a local Ollama model into ai.review_embeddings."""
import os
import duckdb, requests

DB = "dbt/warehouse.duckdb"
BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_N = int(os.getenv("EMBED_N", "2000"))
BATCH = 32

con = duckdb.connect(DB)
con.execute("create schema if not exists ai")
con.execute("create table if not exists ai.review_embeddings "
            "(review_id bigint, embedding float[])")

rows = con.execute("""
    select r.review_id, r.review_text
    from main.stg_reviews r
    left join ai.review_embeddings e using (review_id)
    where e.review_id is null
    order by r.review_id
    limit ?""", [EMBED_N]).fetchall()

done = 0
for i in range(0, len(rows), BATCH):
    chunk = rows[i:i + BATCH]
    resp = requests.post(f"{BASE}/api/embed", timeout=300,
                         json={"model": MODEL, "input": [t for _, t in chunk]})
    resp.raise_for_status()
    vecs = resp.json()["embeddings"]
    con.executemany("insert into ai.review_embeddings values (?, ?)",
                    [(rid, v) for (rid, _), v in zip(chunk, vecs)])
    done += len(chunk)
    print(f"{done}/{len(rows)}")
print(f"embedded {done} reviews")
