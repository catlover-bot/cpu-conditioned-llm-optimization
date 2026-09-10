"""Publication guard regression with inert measurements, not performance data."""
from pathlib import Path

import pytest

from cpucond import selection, selection_scoring
from test_selection_protocol import source_run


def test_failed_score_audit_cannot_publish_a_completed_pointer(tmp_path, source_run, monkeypatch):
    monkeypatch.setattr(selection, "_preflight", lambda protocol: {"inert_fixture": True})
    pilot, _ = selection.prepare_pilot(tmp_path / "pilots", source_run, cohort="synthetic")
    selection.synthetic_answers(pilot)
    selection.freeze_answers(pilot)

    def inert_measurement(output, **kwargs):
        output.mkdir(parents=True)
        record = {"status": "completed", "run_id": "inert-new-measurement"}
        selection.write_json(output / "experiment.json", record)
        return output, record

    def inert_reports(directory, report):
        selection.write_json(directory / "inert-report.json", report)
        return {"json": "inert-report.json"}

    monkeypatch.setattr(selection, "run_diagnostics", inert_measurement)
    monkeypatch.setattr(selection, "audit_artifacts", lambda directory: [])
    monkeypatch.setattr(selection, "_measurement_identity", lambda *a: None)
    monkeypatch.setattr(selection_scoring, "score_selection", lambda *a: {"synthetic_test_only": True})
    monkeypatch.setattr(selection_scoring, "write_selection_reports", inert_reports)
    monkeypatch.setattr(selection, "_audit_score_record", lambda *a: (_ for _ in ()).throw(ValueError("injected final audit failure")))
    with pytest.raises(ValueError, match="injected final audit failure"):
        selection.score_pilot(pilot)
    assert not (pilot / "score.json").exists()
    attempt = next((pilot / "scoring-attempts").glob("*/attempt.json"))
    record = selection.read_json(attempt)
    assert record["status"] == "failed"
    assert record["failure"]["reason"] == "injected final audit failure"
    assert selection.check_pilot(pilot)["passed"]
