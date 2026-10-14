from copy import deepcopy
import csv
import json
import math

import pytest

from cpucond.diagnostic_reporting import (
    DEFAULT_QUALITY, build_report, summarize_measurement, write_reports,
)


def measurement(name="unroll_1", base=(100, 200, 300, 400), candidate=(100, 100, 100, 100)):
    samples = [{"phase": "warmup", "implementation": name, "elapsed_ns": 999999,
                "repetition": 0, "category": "ok", "size": 128, "seed": 17}]
    for repetition, (reference_ns, candidate_ns) in enumerate(zip(base, candidate)):
        order = ("reference", name) if repetition % 2 == 0 else (name, "reference")
        for position, implementation in enumerate(order):
            samples.append({"phase": "measurement", "implementation": implementation,
                            "elapsed_ns": reference_ns if implementation == "reference" else candidate_ns,
                            "repetition": repetition, "position": position, "order": list(order),
                            "category": "ok", "size": 128, "seed": 17})
    return {"passed": True, "samples": samples, "summary": {"stale": 12345}}


def metadata(name, passed=True, **kwargs):
    return {"unroll_factor": 1 if name.startswith("unroll") else None,
            "origin": "deterministic_generator" if name.startswith("unroll") else "handwritten_fixture",
            "role": "reference" if name == "reference" else "candidate", "comparison_baseline": "reference",
            "build": {"passed": True}, "verification": {"passed": passed, "category": "ok" if passed else "value_mismatch",
                "cases": [] if passed else [{"passed": False, "category": "value_mismatch", "reason": "first mismatch at index 1"}]},
            "analysis": {"status": "available", "evidence_file": f"candidates/{name}/kernel.disasm"},
            "comparison": {"status": "different_in_compared_scope", "reason": "raw kernel bytes differ", "complete_equivalence": False},
            "optimization": {"status": "available", "counts": {"Passed": 1, "Missed": 2, "Analysis": 3},
                             "record_path": f"candidates/{name}/kernel.opt.yaml"}, **kwargs}


def record():
    names = ("reference", "unroll_1", "unroll_2", "unroll_4", "deliberately_wrong")
    result = {"run_id": "synthetic", "environment_role": "development_smoke", "publishable_benchmark": False,
              "manifest_sha256": "f" * 64, "git": {"commit": "a" * 40},
              "settings": {"quality": {**DEFAULT_QUALITY, "min_median_ns": 1},
                           "measure_cases": [{"size": 128, "seed": 17}]},
              "candidates": {name: metadata(name, name != "deliberately_wrong") for name in names}, "phases": {}}
    for phase, order in (("exploration", ("unroll_1", "unroll_2", "unroll_4")),
                         ("confirmation", ("unroll_4", "unroll_2", "unroll_1"))):
        result["phases"][phase] = {"phase": phase, "order_seed": 17 if phase == "exploration" else 23,
                                  "candidate_order_by_case": [{"case_id": "n128_seed17", "order": list(order)}],
                                  "measurements": {name: {"n128_seed17": measurement(name, (100,) * 4, (100 * (index + 1),) * 4)}
                                                   for index, name in enumerate(order)}}
    return result


def test_summary_uses_raw_complete_pairs_linear_iqr_and_excludes_warmups():
    raw = measurement()
    original = deepcopy(raw)
    result = summarize_measurement(raw)
    assert raw == original
    assert result["passed"]
    assert result["samples"] == raw["samples"]
    summary = result["summary"]
    assert "stale" not in summary
    assert summary["baseline"]["median_ns"] == 250
    assert summary["baseline"]["q1_ns"] == 175
    assert summary["baseline"]["q3_ns"] == 325
    assert summary["baseline"]["iqr_ns"] == 150
    assert summary["candidate"]["count"] == 4
    assert summary["candidate"]["iqr_ns"] == 0
    assert summary["paired_ratios"] == [1, 2, 3, 4]
    assert summary["median_paired_ratio"] == 2.5
    assert summary["paired_ratio_iqr"] == 1.5
    assert "reference elapsed_ns / candidate elapsed_ns" in summary["ratio_definition"]
    codes = {warning["code"] for warning in result["warnings"]}
    assert {"measurement_too_short", "high_relative_iqr", "high_paired_ratio_relative_iqr"} <= codes


def test_ratios_pair_by_repetition_not_raw_array_position():
    raw = measurement()
    raw["samples"] = list(reversed(raw["samples"]))
    result = summarize_measurement(raw)
    assert result["summary"]["paired_ratios"] == [1, 2, 3, 4]


def test_failed_samples_are_retained_without_partial_summary():
    raw = measurement()
    raw["passed"] = False
    raw["samples"][-1] = {"phase": "measurement", "category": "timeout"}
    result = summarize_measurement(raw)
    assert result["samples"] == raw["samples"]
    assert result["summary"] is None
    assert result["passed"] is False
    assert result["warnings"][0]["code"] == "measurement_failed"
    assert result["warnings"][0]["failure_category"] == "timeout"


@pytest.mark.parametrize("mutation,code", [
    (lambda raw: raw.update(samples=[]), "measurement_samples_missing"),
    (lambda raw: raw["samples"].pop(), "incomplete_measurement_pairs"),
    (lambda raw: raw["samples"].append(deepcopy(raw["samples"][-1])), "incomplete_measurement_pairs"),
    (lambda raw: raw["samples"][-1].update(seed=99), "incomplete_measurement_pairs"),
    (lambda raw: raw["samples"][-1].update(implementation="unroll_999"), "incomplete_measurement_pairs"),
    (lambda raw: raw["samples"][-1].update(elapsed_ns=0), "invalid_measurement_samples"),
    (lambda raw: raw["samples"][-1].update(elapsed_ns=-1), "invalid_measurement_samples"),
    (lambda raw: raw["samples"][-1].update(elapsed_ns=math.nan), "invalid_measurement_samples"),
    (lambda raw: raw["samples"][-1].update(elapsed_ns=math.inf), "invalid_measurement_samples"),
    (lambda raw: raw["samples"][-1].update(elapsed_ns=True), "invalid_measurement_samples"),
    (lambda raw: raw["samples"][0].update(category="timeout"), "measurement_failed"),
    (lambda raw: raw.update(samples=raw["samples"][:3]), "insufficient_measurement_pairs"),
])
def test_incomplete_or_invalid_samples_never_become_zero_or_success(mutation, code):
    raw = measurement()
    mutation(raw)
    result = summarize_measurement(raw)
    assert result["summary"] is None
    assert result["passed"] is False
    assert result["warnings"][0]["code"] == code


def test_missing_measurement_has_explicit_warning_and_null_summary():
    result = summarize_measurement(None)
    assert result["summary"] is None
    assert result["warnings"][0]["code"] == "measurement_missing"


@pytest.mark.parametrize("quality", [{"min_median_ns": -1}, {"max_relative_iqr": math.nan},
                                     {"near_tie_fraction": True}, {"rank_tolerance": 1.5}])
def test_invalid_quality_thresholds_rejected(quality):
    with pytest.raises(ValueError, match="quality"):
        summarize_measurement(measurement(), quality)


def test_declared_quality_thresholds_are_applied_without_changing_results():
    first = summarize_measurement(measurement(), {"min_median_ns": 1, "max_relative_iqr": 2})
    second = summarize_measurement(measurement(), {"min_median_ns": 1000, "max_relative_iqr": 0.01})
    assert first["summary"] == second["summary"]
    assert first["warnings"] == []
    assert second["warnings"]


def test_report_separates_phases_ranks_valid_candidates_and_records_instability():
    raw = record()
    original = deepcopy(raw)
    report = build_report(raw)
    assert raw == original
    assert report["manifest_sha256"] == "f" * 64
    candidate = report["candidates"]["unroll_1"]
    exploration = candidate["phases"]["exploration"]["n128_seed17"]
    confirmation = candidate["phases"]["confirmation"]["n128_seed17"]
    assert exploration["summary"]["median_paired_ratio"] == 1
    assert confirmation["summary"]["median_paired_ratio"] == pytest.approx(1 / 3)
    assert exploration["observed_rank"] == 1
    assert confirmation["observed_rank"] == 3
    assert any(warning["code"] == "rank_unstable" for warning in candidate["warnings"])
    assert any(warning["code"] == "observed_winner_changed" for warning in report["warnings"])
    assert candidate["evidence_files"] == ["candidates/unroll_1/kernel.disasm", "candidates/unroll_1/kernel.opt.yaml"]
    assert candidate["optimization"]["counts"] == {"Passed": 1, "Missed": 2, "Analysis": 3}
    for phase in ("exploration", "confirmation"):
        wrong = report["candidates"]["deliberately_wrong"]["phases"][phase]["n128_seed17"]
        baseline = report["candidates"]["reference"]["phases"][phase]["n128_seed17"]
        assert wrong["summary"] is None and wrong["observed_rank"] is None
        assert wrong["status"] == "verification_failed"
        assert baseline["summary"] is None and baseline["observed_rank"] is None
        assert baseline["status"] == "baseline_measured_in_pairs"
        assert {entry["candidate_id"] for entry in report["phases"][phase]["rankings"]["n128_seed17"]} == {"unroll_1", "unroll_2", "unroll_4"}
    assert "first mismatch at index 1" in report["candidates"]["deliberately_wrong"]["failure_reason"]


def test_wrong_candidate_injected_measurement_gets_no_timing_or_rank():
    raw = record()
    raw["phases"]["exploration"]["measurements"]["deliberately_wrong"] = {"n128_seed17": measurement("deliberately_wrong", (10**8,) * 4, (1,) * 4)}
    report = build_report(raw)
    wrong = report["candidates"]["deliberately_wrong"]["phases"]["exploration"]["n128_seed17"]
    assert wrong["summary"] is None
    assert wrong["observed_rank"] is None
    assert any(warning["code"] == "unverified_measurement_ignored" for warning in wrong["warnings"])


def test_missing_phase_and_failed_measurement_are_not_success_or_zero():
    raw = record()
    del raw["phases"]["confirmation"]
    del raw["phases"]["exploration"]["measurements"]["unroll_2"]
    raw["phases"]["exploration"]["measurements"]["unroll_1"]["n128_seed17"]["passed"] = False
    report = build_report(raw)
    for name in ("unroll_1", "unroll_2"):
        result = report["candidates"][name]["phases"]["exploration"]["n128_seed17"]
        assert result["observed_rank"] is None
        assert result["summary"] is None
    assert report["phases"]["confirmation"]["rankings"]["n128_seed17"] == []
    assert any(warning["code"] == "phase_missing" for warning in report["warnings"])


def test_tied_candidates_share_rank_and_near_ties_are_not_significance_claims():
    raw = record()
    for phase in raw["phases"].values():
        for name in ("unroll_1", "unroll_2", "unroll_4"):
            phase["measurements"][name]["n128_seed17"] = measurement(name, (100,) * 4, (100,) * 4)
    report = build_report(raw)
    rankings = report["phases"]["exploration"]["rankings"]["n128_seed17"]
    assert [item["observed_rank"] for item in rankings] == [1, 1, 1]
    assert any(warning["code"] == "near_tie" for warning in report["warnings"])
    assert not any(warning["code"] in ("rank_unstable", "observed_winner_changed") for warning in report["warnings"])
    assert report["statistical_method"]["significance_testing"] is False


def test_scope_unavailable_optimization_absence_and_evidence_are_preserved():
    raw = record()
    raw["candidates"]["unroll_1"]["comparison"] = {"status": "comparison_unavailable", "reason": "kernel symbol missing"}
    raw["candidates"]["unroll_1"]["optimization"] = {"status": "unavailable", "reason": "compiler rejected recording option"}
    report = build_report(raw)
    candidate = report["candidates"]["unroll_1"]
    assert candidate["comparison"] == raw["candidates"]["unroll_1"]["comparison"]
    assert candidate["optimization"] == raw["candidates"]["unroll_1"]["optimization"]


def test_report_writers_preserve_nulls_in_json_blanks_in_csv_and_phase_separation(tmp_path):
    raw = record()
    files = write_reports(tmp_path, raw)
    assert files == {"json": "report.json", "csv": "report.csv", "markdown": "report.md"}
    saved = json.loads((tmp_path / files["json"]).read_text())
    assert saved == build_report(raw)
    with (tmp_path / files["csv"]).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 10
    for row in rows:
        if row["candidate_id"] in ("reference", "deliberately_wrong"):
            assert row["candidate_median_ns"] == ""
            assert row["median_paired_ratio"] == ""
            assert row["observed_rank"] == ""
    markdown = (tmp_path / files["markdown"]).read_text()
    assert "## exploration" in markdown and "## confirmation" in markdown
    assert "publishable_benchmark=false" in markdown
    assert "有意差検定は実施していません" in markdown
    assert "first mismatch at index 1" in markdown
    assert "kernel.disasm" in markdown
    assert "baseline_measured_in_pairs" in markdown


def test_list_pair_configured_cases_survive_all_failed_verification():
    raw = record()
    raw["settings"]["measure_cases"] = [[128, 17], [256, 17]]
    for candidate in raw["candidates"].values():
        candidate["verification"] = {"passed": False, "category": "reference_failure"}
    for phase in raw["phases"].values():
        phase["measurements"] = {}
    report = build_report(raw)
    assert report["measure_cases"] == ["n128_seed17", "n256_seed17"]
    assert set(report["candidates"]["unroll_1"]["phases"]["confirmation"]) == {"n128_seed17", "n256_seed17"}
    assert all(item["observed_rank"] is None for candidate in report["candidates"].values()
               for phase in candidate["phases"].values() for item in phase.values())


def test_candidate_local_evidence_paths_are_qualified_without_rewriting_root_paths():
    raw = record()
    candidate = raw["candidates"]["unroll_1"]
    candidate["analysis"] = {"disassembly_path": "kernel.disasm"}
    candidate["optimization"] = {"record_path": "kernel.opt.yaml"}
    candidate["comparison"]["evidence_paths"] = ["candidates/reference/analysis.json", "candidates/unroll_1/analysis.json"]
    candidate["evidence"] = {"build_path": "candidates/unroll_1/build.json"}
    paths = build_report(raw)["candidates"]["unroll_1"]["evidence_files"]
    assert paths == ["candidates/reference/analysis.json", "candidates/unroll_1/analysis.json", "candidates/unroll_1/build.json",
                     "candidates/unroll_1/kernel.disasm", "candidates/unroll_1/kernel.opt.yaml"]


def test_failed_build_excludes_even_inconsistent_successful_verification():
    raw = record()
    raw["candidates"]["unroll_1"]["build"]["passed"] = False
    result = build_report(raw)["candidates"]["unroll_1"]["phases"]["exploration"]["n128_seed17"]
    assert result["status"] == "build_failed"
    assert result["summary"] is None and result["observed_rank"] is None


def test_raw_candidate_identity_mismatch_does_not_acquire_other_candidates_rank():
    raw = record()
    raw["phases"]["exploration"]["measurements"]["unroll_1"]["n128_seed17"] = measurement("unroll_2")
    result = build_report(raw)["candidates"]["unroll_1"]["phases"]["exploration"]["n128_seed17"]
    assert result["summary"] is None and result["observed_rank"] is None
    assert result["warnings"][0]["code"] == "measurement_candidate_mismatch"


def test_report_is_reproducible_after_sorted_experiment_json_round_trip():
    raw = record()
    round_trip = json.loads(json.dumps(raw, sort_keys=True))
    assert build_report(raw) == build_report(round_trip)
