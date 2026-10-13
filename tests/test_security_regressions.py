"""Regression checks for input safety, HMAC integrity, and API behavior."""
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from agents.api import app
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor

def test_audit_rejects_modified_signature_fields():
    trail = AuditTrail(secret_key="regression-test-secret")
    trail.log("Supervisor", "system", "TASK", {"status": "OK"})
    trail.log("Supervisor", "system", "TASK", {"status": "OK"})
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "Other"
    assert not trail.verify_integrity()

def test_audit_detects_modified_signature():
    trail = AuditTrail(secret_key="regression-test-secret")
    trail.log("Supervisor", "system", "TASK", {"status": "OK"})
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()

def test_external_log_snapshot_is_not_mutable_internal_state():
    trail = AuditTrail(secret_key="regression-test-secret")
    trail.log("Supervisor", "system", "TASK", {"status": "OK"})
    view = trail.get_trail()
    view[0]["actor"] = "Other"
    view.append({})
    assert trail.verify_integrity()
    assert len(trail.get_trail()) == 1

@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_metrics_rejected(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="SYNTHETIC", primary_metric=value)
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="T", target_identifier="SYNTHETIC", primary_metric=1, secondary_metric=value)

def test_metadata_identifiers_rejected():
    supervisor = SystemSupervisor()
    with pytest.raises(SecurityException):
        supervisor.process_task(SystemTaskPayload(
            task_id="DEMO", target_identifier="SYNTHETIC", primary_metric=1,
            attributes={"contact": "not-real@example.com"},
        ))

def test_api_validates_and_serves_console():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    assert 'id="audit-form"' in client.get("/").text
    assert client.get("/app.js").status_code == 200
    assert client.get("/styles.css").status_code == 200
    good = client.post("/api/audit", json={
        "task_id": "DEMO", "target_identifier": "SYNTHETIC",
        "primary_metric": 29, "secondary_metric": 1,
    })
    assert good.status_code == 200
    assert good.json()["overall_urgency"] == "ELEVATED_RISK"
    assert good.json()["audit_hash"]
    bad = client.post("/api/audit", json={
        "task_id": "MRN-994827", "target_identifier": "SYNTHETIC", "primary_metric": 2,
    })
    assert bad.status_code == 422
    assert "MRN-994827" not in bad.text
    bad2 = client.post("/api/audit", json={
        "task_id": "DEMO", "target_identifier": "SYNTHETIC", "primary_metric": "NaN",
    })
    assert bad2.status_code == 422

def test_second_coordinator_nonfinite_and_phi_rejected():
    from telehealth_audit.models import FrontierPayload
    from telehealth_audit.agents import TeleHealthAuditCoordinator
    coord = TeleHealthAuditCoordinator()
    with pytest.raises(ValueError):
        coord.process(FrontierPayload("T", "SYNTHETIC", float("nan"), 1, "NOMINAL"))
    with pytest.raises(SecurityException):
        coord.process(FrontierPayload("T", "SYNTHETIC", 1, 1, "NOMINAL", attributes={"email": "not-real@example.com"}))
