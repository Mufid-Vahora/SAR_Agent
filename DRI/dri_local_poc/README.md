
# Dynamic Risk Intelligence (DRI) — Local PoC (Neo4j + PyG + Ollama gemma:2b)

This is a lightweight, end-to-end implementation aligned with the uploaded DRI PoC document — with the GenAI layer swapped to **Ollama `gemma:2b`** so everything runs **fully on your laptop**. fileciteturn0file0

## Components
- **Data**: synthetic CSVs with embedded circular-transaction patterns (`/dri_synthetic_data`). (Already generated.)
- **Graph DB**: Neo4j Community Edition (local Docker).
- **Detection**: PyTorch Geometric (GAT) for node-level "is_in_cycle" prediction.
- **Explainability**: Retrieval-style prompt to **Ollama `gemma:2b`** via local REST API.
- **UI**: Streamlit app that lists alerts, shows a small subgraph, and renders the LLM narrative.
- **Orchestration**: `run_all.py` runs data load → train → detect → explain for a tiny demo flow.
- (Optional) Airflow/Streamlit expansion phases are called out in the PoC. fileciteturn0file0

> NOTE: This PoC is intentionally small so it runs on a typical laptop. It mirrors the document’s architecture—Knowledge Graph, GNN, GenAI Copilot, Streamlit—swapping Mistral for **gemma:2b on Ollama** per your ask. fileciteturn0file0

---

## Quickstart

### 0) Prereqs
- Docker Desktop (or Docker Engine)
- Python 3.10+
- `ollama` installed locally and the model pulled:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh   # or see official instructions
  ollama pull gemma:2b
  ollama serve &  # ensure API at http://localhost:11434
  ```

### 1) Start Neo4j
```bash
docker compose up -d   # starts neo4j:5 community at bolt://localhost:7687 (user: neo4j / pass: password)
```

### 2) Create & activate venv, install deps
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) Load synthetic CSVs into Neo4j
```bash
python neo4j_loader.py --csv-root ../dri_synthetic_data
```

### 4) Train tiny GNN (GAT) on the graph
```bash
python gnn_train.py --epochs 5
```

### 5) Run detection + explanation
```bash
python detect_and_explain.py --topk 5
```

This writes JSON explanations to `artifacts/explanations.jsonl`.

### 6) Launch Streamlit UI
```bash
streamlit run streamlit_app.py
```
Open the URL printed in the terminal, pick an alert, view the graph and narrative.

---

## Project Layout
```
dri_local_poc/
  README.md
  requirements.txt
  docker-compose.yml
  neo4j_loader.py
  gnn_train.py
  detect_and_explain.py
  streamlit_app.py
  run_all.py
dri_synthetic_data/     # generated next to this folder (already created)
```
The document this follows defines the 3 pillars (Graph DB, GNN, GenAI) plus a simple demo UI and basic KPIs; this PoC aligns with that scope. fileciteturn0file0
