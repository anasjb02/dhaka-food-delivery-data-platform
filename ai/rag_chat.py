"""Chat with your reviews (RAG): embed question -> retrieve similar reviews -> answer."""
import os
import duckdb, numpy as np, requests
import streamlit as st

DB = "dbt/warehouse.duckdb"
BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")
TOP_K = 8


@st.cache_resource
def load_index():
    con = duckdb.connect(DB, read_only=True)
    rows = con.execute("""
        select e.review_id, e.embedding, d.city
        from ai.review_embeddings e
        join main.stg_reviews r on r.review_id = e.review_id
        join main.dim_restaurants d on d.restaurant_id = r.restaurant_id
        order by e.review_id""").fetchall()
    con.close()
    ids = np.array([r[0] for r in rows])
    mat = np.array([r[1] for r in rows], dtype=np.float32)
    if len(rows):
        mat /= np.linalg.norm(mat, axis=1, keepdims=True)
    cities = np.array([r[2] for r in rows])
    return ids, mat, cities


def embed(text):
    r = requests.post(f"{BASE}/api/embed", timeout=120,
                      json={"model": EMBED_MODEL, "input": [text]})
    r.raise_for_status()
    v = np.array(r.json()["embeddings"][0], dtype=np.float32)
    return v / np.linalg.norm(v)


def retrieve(question, city):
    ids, mat, cities = load_index()
    mask = np.ones(len(ids), dtype=bool) if city == "All" else (cities == city)
    scores = mat[mask] @ embed(question)
    top = np.argsort(-scores)[:300]
    chosen = ids[mask][top]
    con = duckdb.connect(DB, read_only=True)
    marks = ",".join(["?"] * len(chosen))
    rows = con.execute(f"""
        select r.review_id, d.restaurant_name, d.city, r.rating, r.review_text
        from main.stg_reviews r
        join main.dim_restaurants d on d.restaurant_id = r.restaurant_id
        where r.review_id in ({marks})""", [int(x) for x in chosen]).fetchall()
    con.close()
    order = {int(x): i for i, x in enumerate(chosen)}
    rows = sorted(rows, key=lambda r: order[r[0]])
    seen, unique = set(), []
    for r in rows:
        key = tuple(sorted(x.strip() for x in r[4].split(".") if x.strip()))
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique[:TOP_K]


def answer(question, reviews):
    context = "\n".join(
        f"[{i}] ({city}, {rest}, rating {rating}) {text}"
        for i, (_, rest, city, rating, text) in enumerate(reviews, 1))
    prompt = ("Answer the question using ONLY the customer reviews below. "
              "Cite review numbers like [2]. If the reviews do not contain "
              "the answer, say so.\n\n"
              f"Reviews:\n{context}\n\nQuestion: {question}")
    r = requests.post(f"{BASE}/api/chat", timeout=300, json={
        "model": CHAT_MODEL, "stream": False, "options": {"temperature": 0},
        "messages": [{"role": "user", "content": prompt}]})
    r.raise_for_status()
    return r.json()["message"]["content"]


st.title("Chat with your reviews")
ids, _, cities = load_index()
if len(ids) == 0:
    st.error("No embeddings yet. Run: python ai/embed_reviews.py")
    st.stop()
st.caption(f"{len(ids)} embedded reviews")
city = st.selectbox("City", ["All"] + sorted(set(cities.tolist())))
question = st.text_input("Ask about the reviews", "What do customers complain about?")
if st.button("Ask") and question:
    reviews = retrieve(question, city)
    st.subheader("Answer")
    st.write(answer(question, reviews))
    st.subheader("Sources")
    for i, (_, rest, c, rating, text) in enumerate(reviews, 1):
        st.write(f"**[{i}]** {rest} ({c}), rating {rating}: {text}")
