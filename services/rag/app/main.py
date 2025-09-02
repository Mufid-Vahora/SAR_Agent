from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


app = FastAPI(title="RAG Retriever")

INDEX_DIR = os.getenv("INDEX_DIR", "/data/indexes")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


class QueryRequest(BaseModel):
    cache_key: str
    query: str
    k: int = 5


@app.post("/query")
def query(req: QueryRequest):
    index_path = os.path.join(INDEX_DIR, f"{req.cache_key}.faiss")
    meta_path = os.path.join(INDEX_DIR, f"{req.cache_key}.txt")
    if not os.path.exists(index_path) or not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Index not found; run template fetch first")
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        corpus = [line.strip() for line in f.readlines()]
    model = get_embedder()
    q = model.encode([req.query], normalize_embeddings=True).astype(np.float32)
    scores, idxs = index.search(q, req.k)
    idxs = idxs[0]
    scores = scores[0]
    results = []
    for i, s in zip(idxs, scores):
        if i < 0 or i >= len(corpus):
            continue
        results.append({"text": corpus[i], "score": float(s)})
    return {"results": results}


@app.get("/")
def root():
    return {"service": "rag", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"ok": True}


