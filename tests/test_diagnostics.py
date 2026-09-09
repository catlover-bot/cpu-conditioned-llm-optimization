from dataclasses import replace
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from cpucond import diagnostics as diag
from cpucond.diagnostic_config import DiagnosticConfig, QualityPolicy, load_config
from cpucond.experiment import audit_artifacts
from cpucond.process import ProcessResult


@pytest.fixture(scope="module")
def diagnostic_run(tmp_path_factory):
    config = DiagnosticConfig(measure_cases=((18, 17), (20, 17)), repeats=3, warmups=1,
                              size_rationale="Small integration inputs; final CLI preset separately runs 128/256.")
    path, record = diag.run_diagnostics(tmp_path_factory.mktemp("diagnostic-runs"), config=config)
    return path, record, config


@pytest.mark.integration
def test_controlled_pipeline_real_compiler(diagnostic_run):
    path, record, config = diagnostic_run
    assert record["status"] == "completed", record.get("artifact_errors")
    assert audit_artifacts(path) == []
    assert record["environment_role"] == "development_smoke"
    assert record["publishable_benchmark"] is False
    assert record["llm_api_called"] is False
    assert set(record["candidates"]) == {"reference", "identity", "deliberately_wrong", "unroll_1", "unroll_2", "unroll_4", "unroll_8", "unroll_16"}
    assert record["affinity"]["pinned"] and record["affinity"]["restored"]
    events = json.loads((path / "process-ledger.json").read_text())
    for name, candidate in record["candidates"].items():
        assert candidate["build"]["passed"]
        assert len(candidate["verification"]["cases"]) == len(config.cases())
        assert candidate["analysis"]["status"] == "available", candidate["analysis"]["reason"]
        assert candidate["analysis"]["program_sha256"] == candidate["program_sha256"]
        assert candidate["optimization"]["status"] == "available"
        assert sum(candidate["optimization"]["counts"].values()) > 0
        assert candidate["comparison"]["status"] in {"same_in_extracted_scope", "different_in_extracted_scope"}
        assert candidate["comparison"]["intended_transformation_status"] == "unknown"
        assert candidate["comparison"]["full_equivalence_claim"] is False
        assert candidate["verification"]["passed"] == (name != "deliberately_wrong")
        if name == "deliberately_wrong":
            assert all(c["category"] == "value_mismatch" for c in candidate["verification"]["cases"])
        else:
            assert all(c["passed"] for c in candidate["verification"]["cases"])
    ids_by_phase = {}
    for phase in diag.PHASES:
        info = record["phases"][phase]
        assert info["measurement_freeze_sha256"] == record["measurement_freeze_sha256"]
        assert "deliberately_wrong" not in info["measurements"]
        assert {x["candidate_id"] for x in info["skipped"]} == {"deliberately_wrong"}
        ids_by_phase[phase] = set()
        for name, cases in info["measurements"].items():
            assert len(cases) == 2
            for measurement in cases.values():
                assert measurement["passed"]
                assert len(measurement["samples"]) == 2 * (config.repeats + config.warmups)
                assert len(measurement["summary"]["paired_ratios"]) == config.repeats
                assert measurement["summary"]["candidate"]["iqr_ns"] >= 0
                for sample in measurement["samples"]:
                    event = events[sample["ledger_event_id"]]
                    assert event["stage"] == phase
                    assert event["program_sha256"] == record["candidates"][sample["implementation"]]["program_sha256"]
                    assert sample["experiment_phase"] == phase
                    assert sample["ledger_event_id"] not in ids_by_phase[phase]
                    ids_by_phase[phase].add(sample["ledger_event_id"])
        for order in info["candidate_order_by_case"]:
            assert set(order["candidate_ids"]) == set(record["candidates"]) - {"reference"}
    assert ids_by_phase["exploration"].isdisjoint(ids_by_phase["confirmation"])
    assert record["phases"]["exploration"]["candidate_order_by_case"] != record["phases"]["confirmation"]["candidate_order_by_case"]
    assert record["costs"]["stages"]["verification"]["verification_failures"] == len(config.cases())
    assert not any(e["stage"] in diag.PHASES and e["candidate_id"] == "deliberately_wrong" for e in events)
    report = json.loads((path / "report.json").read_text())
    wrong = report["candidates"]["deliberately_wrong"]
    for phase in diag.PHASES:
        assert all(x["observed_rank"] is None and x["summary"] is None for x in wrong["phases"][phase].values())
    assert all((path / name).stat().st_size for name in ("report.json", "report.csv", "report.md"))
    assert report["statistical_method"]["significance_testing"] is False


@pytest.mark.integration
def test_diagnostic_cpu_prompt_does_not_change_build(diagnostic_run, tmp_path):
    original, first, config = diagnostic_run
    before = (original / "experiment.json").read_bytes()
    _, second = diag.run_diagnostics(tmp_path, config=config, specification="TEST CPU EXTRA_SENTINEL CACHE_SENSITIVE_SENTINEL")
    assert first["compiler"] == second["compiler"]
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["prompts"]["common_payload"] == second["prompts"]["common_payload"]
    assert first["prompts"]["none"] == second["prompts"]["none"]
    assert first["prompts"]["spec"]["sha256"] != second["prompts"]["spec"]["sha256"]
    for name in first["candidates"]:
        assert [x["args"] for x in first["candidates"][name]["build"]["commands"]] == [x["args"] for x in second["candidates"][name]["build"]["commands"]]
    assert (original / "experiment.json").read_bytes() == before


@pytest.mark.integration
def test_reference_compile_failure_prevents_all_measurement(tmp_path, monkeypatch):
    make = diag.make_candidates
    monkeypatch.setattr(diag, "make_candidates", lambda: [replace(c, source="invalid C syntax") if c.candidate_id == "reference" else c for c in make()])
    def forbidden(*args, **kwargs):
        pytest.fail("unverified candidate reached measurement")
    monkeypatch.setattr(diag, "measure_pairs", forbidden)
    path, record = diag.run_diagnostics(tmp_path, config=DiagnosticConfig(measure_cases=((18, 17),), repeats=2, warmups=0))
    assert record["status"] == "failed"
    assert record["candidates"]["reference"]["verification"]["category"] == "compile_failure"
    assert all(not p["measurements"] for p in record["phases"].values())
    report = json.loads((path / "report.json").read_text())
    assert report["measure_cases"] == ["n18_seed17"]
    assert len((path / "report.csv").read_text().splitlines()) >= 17


@pytest.mark.integration
def test_analysis_unavailable_remains_explicit_not_a_fake_match(tmp_path, monkeypatch):
    import cpucond.code_analysis as analysis
    def unavailable(*args, **kwargs):
        raise analysis.AnalysisError("simulated unsupported extraction scope")
    monkeypatch.setattr(analysis, "extract_symbol_range", unavailable)
    path, record = diag.run_diagnostics(tmp_path, config=DiagnosticConfig(measure_cases=((18, 17),), repeats=2, warmups=0))
    assert record["status"] == "completed", record.get("artifact_errors")
    assert all(c["comparison"]["status"] == "analysis_unavailable" for c in record["candidates"].values())
    assert all("simulated" in c["analysis"]["reason"] for c in record["candidates"].values())
    assert "analysis_unavailable" in (path / "report.md").read_text()


def test_measurement_failure_never_invents_elapsed_time(tmp_path):
    ledger = diag.ProcessLedger()
    program = tmp_path / "program"
    program.write_bytes(b"original")
    ledger.expected_programs[str(program)] = diag.digest(program)
    program.write_bytes(b"changed")
    result = ledger.run([program, "measure", 18, 17])
    assert result.category == "artifact_changed"
    assert not ledger.events[-1]["process_attempted"]
    assert ledger.totals()["execution_count"] == 0


def test_diagnostic_measurement_lock_prevents_overlap():
    with diag.exclusive_measurements():
        with pytest.raises(RuntimeError, match="another"):
            with diag.exclusive_measurements():
                pytest.fail("second measurement acquired lock")


@pytest.mark.parametrize("settings", [
    {"timeout_seconds": True}, {"timeout_seconds": float("nan")}, {"repeats": 1},
    {"verification_sizes": (1, 2)}, {"verification_seeds": (17,)},
    {"measure_cases": ((0, 17),)}, {"measure_cases": ((18, -1),)},
    {"measure_cases": ((18, 17), (18, 17))}, {"confirmation_order_seed": 2026002},
])
def test_invalid_diagnostic_config_rejected(settings):
    with pytest.raises(ValueError):
        DiagnosticConfig(**settings)


@pytest.mark.parametrize("value", [[], {"quality": []}, {"measure_cases": [1]}, {"unknown": 4}])
def test_malformed_config_file_is_a_clear_value_error(tmp_path, value):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        load_config(path)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["program", "driver", "config", "verification"])
def test_frozen_inputs_cannot_change_between_phases(diagnostic_run, tmp_path, mutation):
    original, record, _ = diagnostic_run
    copy = tmp_path / "run"
    shutil.copytree(original, copy)
    relative = {"program": "candidates/unroll_2/program", "driver": "candidates/unroll_4/harness.c",
                "config": "config.json", "verification": "candidates/unroll_8/verification.json"}[mutation]
    with (copy / relative).open("ab") as stream:
        stream.write(b"\nchanged\n")
    with pytest.raises(RuntimeError, match="changed"):
        diag.verify_frozen_inputs(copy, record)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["missing_confirmation", "reused_samples", "missing_repetition", "wrong_input"])
def test_semantic_audit_rejects_coherently_rewritten_incomplete_measurement(diagnostic_run, tmp_path, mutation):
    """Even a refreshed file hash list cannot turn incomplete evidence into success."""
    original, source, _ = diagnostic_run
    copy = tmp_path / "run"
    shutil.copytree(original, copy)
    record = deepcopy(source)
    phase = record["phases"]["confirmation"]
    name, cid = "unroll_4", "n18_seed17"
    result_file = copy / "phases" / "confirmation" / f"{name}-{cid}.json"
    if mutation == "missing_confirmation":
        del phase["measurements"][name][cid]
        result_file.unlink()
    else:
        result = phase["measurements"][name][cid]
        if mutation == "reused_samples":
            result["samples"] = deepcopy(record["phases"]["exploration"]["measurements"][name][cid]["samples"])
            for sample in result["samples"]:
                sample["experiment_phase"] = "confirmation"
        elif mutation == "missing_repetition":
            result["samples"] = [s for s in result["samples"] if s["phase"] != "measurement" or s["repetition"] != 2]
        else:
            result["samples"][0]["size"] = 17
        result = diag.summarize_measurement(result, record["settings"]["quality"])
        phase["measurements"][name][cid] = result
        diag.write_json(result_file, result)
    diag.write_json(copy / "phases/confirmation/phase.json", phase)
    diag.write_reports(copy, record)
    record["artifacts"] = diag.artifact_manifest(copy)
    diag.write_json(copy / "experiment.json", record)
    assert diag.audit_diagnostic(copy), "a hash-consistent but semantically incomplete run must fail the audit"
