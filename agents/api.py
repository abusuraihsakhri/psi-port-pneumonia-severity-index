"""
FastAPI REST API Server for Psi Port Pneumonia Severity Index.
"""
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictBool, create_model
from psi_port import calculate_metrics, FIELD_NAMES
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Psi Port Pneumonia Severity Index API",
    description="Adult PSI/PORT clinical risk calculator and legacy task audit services",
    version="3.1.0",
)


PSIRequest = create_model(
    "PSIRequest", age=(int, Field(ge=18, le=120)),
    sex=(Literal["male", "female"], ...),
    **{name: (StrictBool, ...) for name in FIELD_NAMES},
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "healthy", "service": "psi-port-pneumonia-severity-index", "version": "3.1.0"}


@app.post("/api/psi")
def api_psi(payload: PSIRequest):
    """Calculate adult PSI. Required boolean fields must be explicitly assessed."""
    return calculate_metrics(**payload.model_dump())


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}

# Serve the same offline-capable, dependency-free calculator at the API root.
# Registered last so API routes retain priority.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent / "static", html=True), name="calculator")
