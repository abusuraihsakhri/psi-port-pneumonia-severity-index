"""API route, input validation, and audit-integrity tests."""
from fastapi.testclient import TestClient
from agents.api import app
from agents.base import AuditTrail
from psi_port import FIELD_NAMES


def test_api_exposes_browser_and_validated_psi():
    client = TestClient(app)
    homepage = client.get("/")
    assert homepage.status_code == 200
    assert "Pneumonia Severity Index" in homepage.text
    assert client.get("/psi.js").status_code == 200
    sample = {"age": 71, "sex": "male", **{name: False for name in FIELD_NAMES}}
    response = client.post("/api/psi", json=sample)
    assert response.status_code == 200
    assert response.json()["risk_class"] == "III"
    assert client.get("/health").status_code == 200


def test_api_rejects_unassessed_or_wrong_boolean_factors():
    client = TestClient(app)
    sample = {"age": 70, "sex": "male", **{name: False for name in FIELD_NAMES}}
    sample.pop("bun_ge_30")
    assert client.post("/api/psi", json=sample).status_code == 422
    sample["bun_ge_30"] = "unknown"
    assert client.post("/api/psi", json=sample).status_code == 422
    sample["bun_ge_30"] = False
    sample["age"] = 12
    assert client.post("/api/psi", json=sample).status_code == 422


def test_audit_verifies_signature_as_well_as_chain_links():
    audit = AuditTrail(secret_key="isolated-test-secret")
    audit.log("tester", "test", "EVALUATION", {"status": "ok"})
    audit.log("tester", "test", "EVALUATION", {"status": "ok"})
    assert audit.verify_integrity() is True
    public_copy = audit.get_trail()
    public_copy[0]["current_hash"] = "tampered"
    assert audit.verify_integrity() is True  # exposed objects are copies
    audit.logs[0]["actor"] = "attacker"
    assert audit.verify_integrity() is False


def test_audit_detects_tail_entry_forgery():
    audit = AuditTrail(secret_key="isolated-test-secret")
    audit.log("tester", "test", "EVALUATION", {"status": "ok"})
    audit.logs[-1]["current_hash"] = "0" * 64
    assert audit.verify_integrity() is False
