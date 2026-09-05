"""
Automated Pytest Test Suite for Telehealth Encounter Documentation Agent.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main, _parse_bool


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_parse_bool():
    """Test boolean parsing from various input types."""
    # True values
    assert _parse_bool(True) is True
    assert _parse_bool("True") is True
    assert _parse_bool("true") is True
    assert _parse_bool("TRUE") is True
    assert _parse_bool("1") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("Y") is True
    assert _parse_bool("on") is True
    assert _parse_bool(1) is True

    # False values
    assert _parse_bool(False) is False
    assert _parse_bool("False") is False
    assert _parse_bool("false") is False
    assert _parse_bool("FALSE") is False
    assert _parse_bool("0") is False
    assert _parse_bool("no") is False
    assert _parse_bool("N") is False
    assert _parse_bool("off") is False
    assert _parse_bool(0) is False
    assert _parse_bool("") is False
    assert _parse_bool("random") is False


def test_input_validation_string_length():
    """Test that oversized inputs are rejected."""
    supervisor = SystemSupervisor(model_provider="mock")

    # Test task_id too long
    with pytest.raises(ValueError, match="task_id exceeds maximum length"):
        supervisor.process_task(SystemTaskPayload(
            task_id="X" * 129,
            target_identifier="KEY-01",
            primary_metric=10.0,
        ))

    # Test target_identifier too long
    with pytest.raises(ValueError, match="target_identifier exceeds maximum length"):
        supervisor.process_task(SystemTaskPayload(
            task_id="TASK-01",
            target_identifier="X" * 257,
            primary_metric=10.0,
        ))

    # Test status_descriptor too long
    with pytest.raises(ValueError, match="status_descriptor exceeds maximum length"):
        supervisor.process_task(SystemTaskPayload(
            task_id="TASK-01",
            target_identifier="KEY-01",
            primary_metric=10.0,
            status_descriptor="X" * 65,
        ))

    # Test boundary values (should pass)
    supervisor.process_task(SystemTaskPayload(
        task_id="X" * 128,
        target_identifier="X" * 256,
        primary_metric=10.0,
        status_descriptor="X" * 64,
    ))


def test_batch_csv_with_invalid_data(tmp_path):
    """Test that batch processing handles invalid CSV data gracefully."""
    import csv

    # Create a CSV with some invalid rows
    csv_file = tmp_path / "test_input.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task_id", "target_identifier", "primary_metric", "secondary_metric", "is_critical_flag", "status_descriptor"])
        writer.writerow(["TASK-01", "TARGET-01", "28.4", "14.2", "True", "DISCORDANT"])
        writer.writerow(["TASK-02", "TARGET-02", "invalid", "4.1", "False", "NOMINAL"])  # Invalid primary_metric
        writer.writerow(["TASK-03", "TARGET-03", "35.0", "not_a_number", "True", "ANOMALY"])  # Invalid secondary_metric
        writer.writerow(["TASK-04", "TARGET-04", "12.0", "4.1", "False", "NOMINAL"])

    output_file = tmp_path / "test_output.csv"

    # Should not raise, should skip invalid rows
    result = main(["batch", "-i", str(csv_file), "-o", str(output_file)])
    assert result == 0

    # Check output file
    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have processed 2 valid rows (skipping the 2 invalid ones)
    assert len(rows) == 2
    assert rows[0]["task_id"] == "TASK-01"
    assert rows[1]["task_id"] == "TASK-04"
