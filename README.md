## SAR Agent Platform

Agent-based system for transforming pipe-delimited inputs into regulator-compliant XML (XSD-backed), with RAG-assisted schema mapping, validation, human-in-the-loop review, and submission.

### Components
- **Orchestrator Agent (FastAPI)**: Receives jobs, coordinates agents, tracks state in Redis/Postgres, produces/consumes messages.
- **Parser Agent**: Converts pipe-delimited files to normalized JSON rows and metadata.
- **Template Fetcher Agent**: Downloads/caches XSDs; parses and persists canonical schema; indexes docs in a vector DB.
- **RAG Agent**: Embeds and retrieves guidance/templates/examples for mapping.
- **LLM/Filler Agent**: Generates XML fragments or JSON→XML using retrieved context (Transformers/HF models).
- **Validator Agent**: Validates XML against XSD via xmlschema/lxml; emits diagnostics.
- **Format Selector Agent**: Analyzes pipe-formatted data complexity and recommends appropriate XSD format.
- **Audit Agent**: Stores prompts, context, outputs, validations, and user actions for traceability.
- **HITL UI**: Web UI for review/approval.
- **Submit Agent**: Sends approved XML to regulator e-file endpoints or exports for manual upload.

### Infra (docker-compose)
- Kafka + Zookeeper (message bus)
- Redis (task state / caching)
- Postgres (metadata)
- MinIO (artifact/object storage)
- Prometheus + Grafana (metrics)

### Quick start
1. Ensure Docker Desktop or Podman is installed.
2. Copy `.env.example` to `.env` and adjust values.
3. Launch infra:
   - Docker: `docker compose up -d`
4. Install dependencies:
   - `python -m venv .venv && ./.venv/Scripts/python -m pip install --upgrade pip`
   - `./.venv/Scripts/python -m pip install -r requirements.txt`
5. Run services locally (examples):
   - Template Fetcher: `./.venv/Scripts/python -m uvicorn services.template_fetcher.app.main:app --host 127.0.0.1 --port 8082`
   - RAG: `./.venv/Scripts/python -m uvicorn services.rag.app.main:app --host 127.0.0.1 --port 8083`
   - LLM: `./.venv/Scripts/python -m uvicorn services.llm_filler.app.main:app --host 127.0.0.1 --port 8084`
   - Validator: `./.venv/Scripts/python -m uvicorn services.validator.app.main:app --host 127.0.0.1 --port 8085`
   - Format Selector: `./.venv/Scripts/python -m uvicorn services.format_selector.app.main:app --host 127.0.0.1 --port 8086`
   - Orchestrator: `./.venv/Scripts/python -m uvicorn services.orchestrator.app.main:app --host 127.0.0.1 --port 8087`

### XSD Format Selection
The system now supports two distinct XSD formats for different levels of data complexity:
- **Format 1 (Complex)**: Comprehensive nested format for complex cases
- **Format 2 (Simple)**: Flat format for basic reporting

Use the orchestrator service for end-to-end processing:
```bash
# Start all services
.\ops\start-services.ps1

# Test the complete pipeline
.\ops\run-pipeline.ps1

# Run tests
.\ops\run-tests.ps1
```

### API (Orchestrator)
- `POST /api/jobs/upload` — upload pipe-delimited file to start ingestion
- `POST /api/jobs/{job_id}/start` — enqueue ingestion
- `GET /api/jobs/{job_id}` — job status

### Topics (Kafka)
- `ingestion` — raw file ingestion events
- `parsed-json` — normalized rows
- `template-requests` / `template-indexed`
- `rag-requests` / `rag-context`
- `filler-requests` / `xml-fragments`
- `validation-requests` / `validation-results`
- `audit-events`
- `submission-requests` / `submission-results`

### Development
- Python 3.10+
- FastAPI for agents; prefer uvicorn for local runs
- Sentence-Transformers + FAISS (or Milvus) for the RAG index
- Transformers (HF) for LLMs; prefer Apache/MIT models
- xmlschema/lxml for XSD validation

### License
Apache-2.0 (proposed). Update as needed.


