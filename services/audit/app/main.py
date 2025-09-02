from fastapi import FastAPI
from pydantic import BaseModel
import os
import psycopg2
import json


app = FastAPI(title="Audit Service")

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://sar:sarpass@postgres:5432/sar")


class AuditEvent(BaseModel):
    job_id: str
    event_type: str
    payload: dict


@app.on_event("startup")
def startup():
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            job_id TEXT,
            event_type TEXT,
            payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    cur.close()
    conn.close()


@app.post("/audit")
def audit(event: AuditEvent):
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_events (job_id, event_type, payload) VALUES (%s, %s, %s)",
        (event.job_id, event.event_type, json.dumps(event.payload)),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}


