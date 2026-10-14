"""Lifecycle integration with local Clang; all response content here is synthetic."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import shutil

import pytest

from cpucond.diagnostic_config import DiagnosticConfig
from cpucond.diagnostics import run_diagnostics
from cpucond import selection
from cpucond.__main__ import main


@pytest.fixture(scope="module")
def pilots(tmp_path_factory):
    if not shutil.which("clang"):
        pytest.skip("Clang required for the pilot integration test")
    root = tmp_path_factory.mktemp("selection-integration")
    source, record = run_diagnostics(root / "source", config=DiagnosticConfig(repeats=2, warmups=0))
    assert record["status"] == "completed"
    real, _ = selection.prepare_pilot(root / "pilots", source)
    synthetic, _ = selection.prepare_pilot(root / "pilots", source, cohort="synthetic")
    return {"root": root, "source": source, "real": real, "synthetic": synthetic}


def copied(pilots, tmp_path, cohort="synthetic"):
    directory = tmp_path / cohort
    shutil.copytree(pilots[cohort], directory)
    return directory


def answer(directory, request, *, option=None, invalid=False):
    raw = directory / "incoming" / request["request_key"] / "response.txt"
    metadata = directory / "incoming" / request["request_key"] / "metadata.json"
    selection.write_json(raw, {"request_id": request["request_id"],
                             "selected_option_id": option or ("absent" if invalid else next(iter(request["option_mapping"])))})
    selection.write_json(metadata, selection.read_json(directory / request["metadata_template_path"]))
    return raw, metadata


def test_export_status_and_separate_cohorts(pilots):
    for cohort in ("real", "synthetic"):
        directory = pilots[cohort]
        status = selection.pilot_status(directory)
        assert status["counts"] == {"received": 0, "valid": 0, "invalid": 0, "missing": 20, "total": 20}
        assert status["status"] == ("awaiting_real_responses" if cohort == "real" else "software_ready")
        assert selection.check_pilot(directory)["passed"]
        assert (directory / "runner_source/selection.py").read_bytes() == Path(selection.__file__).read_bytes()
    real = selection.read_json(pilots["real"] / "protocol.json")
    synthetic = selection.read_json(pilots["synthetic"] / "protocol.json")
    assert [r["prompt_sha256"] for r in real["requests"]] == [r["prompt_sha256"] for r in synthetic["requests"]]
    assert real["compiler"]["target_flags"] == []
    assert real["target_mode"] == "compiler_default_generic"


def test_scoring_before_freeze_does_not_measure(pilots, tmp_path, monkeypatch):
    directory = copied(pilots, tmp_path)
    monkeypatch.setattr(selection, "run_diagnostics", lambda *a, **k: pytest.fail("unfrozen answers must not start measurement"))
    with pytest.raises(ValueError, match="frozen"):
        selection.score_pilot(directory)
    with pytest.raises(ValueError, match="empty"):
        selection.freeze_answers(directory)
    assert not (directory / "scoring-attempts").exists()


def test_first_attempt_invalid_and_correction_cannot_replace_it(pilots, tmp_path):
    directory = copied(pilots, tmp_path)
    request = selection.read_json(directory / "protocol.json")["requests"][0]
    raw, metadata = answer(directory, request, invalid=True)
    imported = selection.import_answer(directory, request["request_key"], raw, metadata)
    assert imported["attempt"]["status"] == "invalid"
    with pytest.raises(ValueError, match="duplicate"):
        selection.import_answer(directory, request["request_key"], raw, metadata)
    raw, metadata = answer(directory, request)
    corrected = selection.import_answer(directory, request["request_key"], raw, metadata)
    assert corrected["attempt"]["attempt_index"] == 2
    assert corrected["attempt"]["status"] == "valid"
    frozen = selection.freeze_answers(directory)
    assert frozen["counts"] == {"received": 1, "valid": 0, "invalid": 1, "missing": 19, "total": 20}
    assert len(frozen["attempts"]) == 2
    assert selection.check_pilot(directory)["passed"]
    with pytest.raises(ValueError, match="frozen"):
        selection.import_answer(directory, request["request_key"], raw, metadata)
    with pytest.raises(ValueError, match="already"):
        selection.freeze_answers(directory)


def test_real_pair_state_and_explicit_missing_denominator(pilots, tmp_path):
    directory = copied(pilots, tmp_path, "real")
    requests = selection.read_json(directory / "protocol.json")["requests"]
    pair = [r for r in requests if r["request_id"] == requests[0]["request_id"]]
    assert len(pair) == 2
    for request in pair:
        raw, metadata = answer(directory, request)
        selection.import_answer(directory, request["request_key"], raw, metadata)
    status = selection.pilot_status(directory)
    assert status["status"] == "real_pilot_partial"
    assert status["counts"]["missing"] == 18
    assert status["real_response_count"] == 2 and status["synthetic_response_count"] == 0
    frozen = selection.freeze_answers(directory)
    assert frozen["counts"]["total"] == 20
    assert selection.check_pilot(directory)["passed"]


def test_synthetic_command_refuses_real_cohort(pilots, tmp_path):
    directory = copied(pilots, tmp_path, "real")
    with pytest.raises(ValueError, match="real pilot"):
        selection.synthetic_answers(directory)
    assert not (directory / "responses").exists()


@pytest.fixture(scope="module")
def scored(pilots, tmp_path_factory):
    directory = copied(pilots, tmp_path_factory.mktemp("scored-fixture"))
    with redirect_stdout(io.StringIO()):
        for command in ("synthetic", "freeze", "score", "check"):
            assert main(["pilot", command, str(directory)]) == 0
    return directory


def test_synthetic_end_to_end_scores_one_shared_fresh_measurement(scored, pilots):
    checked = selection.check_pilot(scored)
    assert checked["passed"], checked
    assert checked["pilot"]["synthetic_response_count"] == 20
    assert checked["pilot"]["real_response_count"] == 0
    assert checked["pilot"]["status"] == "software_ready"
    score = selection.read_json(scored / "score.json")
    record = selection.read_json(scored / score["measurement_directory"] / "experiment.json")
    assert record["run_id"] != selection.read_json(pilots["source"] / "experiment.json")["run_id"]
    assert all("deliberately_wrong" not in phase["measurements"] for phase in record["phases"].values())
    report = selection.read_json(scored / score["reports"]["json"])
    assert report["independent_measurement_runs"] == 1
    assert report["shared_measurement_run_id"] == record["run_id"]
    assert report["cohort"] == "synthetic"
    with pytest.raises(ValueError, match="already scored"):
        selection.score_pilot(scored)


def test_changed_protocol_blocks_collection(pilots, tmp_path):
    directory = copied(pilots, tmp_path)
    with (directory / "protocol.json").open("a") as stream:
        stream.write(" ")
    checked = selection.check_pilot(directory)
    assert not checked["passed"]
    assert "protocol changed" in checked["errors"][0]


def test_shared_measurement_and_report_tampering_detected(scored, tmp_path):
    directory = tmp_path / "copy"
    shutil.copytree(scored, directory)
    score = selection.read_json(directory / "score.json")
    report = directory / score["reports"]["json"]
    with report.open("a") as stream:
        stream.write(" ")
    assert not selection.check_pilot(directory)["passed"]


def test_old_run_cannot_be_imported_as_new_score(pilots, tmp_path, monkeypatch):
    directory = copied(pilots, tmp_path)
    selection.synthetic_answers(directory)
    selection.freeze_answers(directory)
    old = selection.read_json(pilots["source"] / "experiment.json")
    monkeypatch.setattr(selection, "run_diagnostics", lambda *a, **k: (pilots["source"], old))
    with pytest.raises(ValueError):
        selection.score_pilot(directory)
    assert not (directory / "score.json").exists()
    attempts = list((directory / "scoring-attempts").glob("*/attempt.json"))
    assert len(attempts) == 1 and selection.read_json(attempts[0])["status"] == "failed"


def test_changed_runner_or_target_prevents_measurement(pilots, tmp_path, monkeypatch):
    directory = copied(pilots, tmp_path)
    selection.synthetic_answers(directory)
    selection.freeze_answers(directory)
    monkeypatch.setattr(selection, "run_diagnostics", lambda *a, **k: pytest.fail("preflight failure must not measure"))
    monkeypatch.setattr(selection, "_preflight", lambda p: (_ for _ in ()).throw(ValueError("target changed")))
    with pytest.raises(ValueError, match="target changed"):
        selection.score_pilot(directory)
    assert not (directory / "scoring-attempts").exists()


def test_pilot_lock_excludes_overlapping_mutations(pilots, tmp_path):
    directory = copied(pilots, tmp_path)
    with selection.mutation_lock(directory):
        with pytest.raises(RuntimeError, match="mutation"):
            with selection.mutation_lock(directory):
                pytest.fail("second mutation lock acquired")


def test_prepare_cannot_create_even_a_directory_inside_old_run(tmp_path):
    source = tmp_path / "old-run"
    source.mkdir()
    marker = source / "preserved.txt"
    marker.write_text("unchanged")
    with pytest.raises(ValueError, match="inside the source run"):
        selection.prepare_pilot(source, source)
    assert list(source.iterdir()) == [marker]
    assert marker.read_text() == "unchanged"
