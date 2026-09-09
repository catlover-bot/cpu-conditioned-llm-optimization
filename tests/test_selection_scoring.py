from copy import deepcopy
import csv
import hashlib
import json

import pytest

from cpucond.selection_scoring import CANDIDATES, score_selection, write_selection_reports


def protocol_hash(value):
    return hashlib.sha256((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()).hexdigest()


def source(name):
    text = "/* synthetic source identity " + name + " */\n"
    return {"source": text, "source_sha256": hashlib.sha256(text.encode()).hexdigest()}


def samples(name, size, candidate_time):
    result = []
    for repetition in range(4):
        order = ["reference", name] if repetition % 2 == 0 else [name, "reference"]
        for position, implementation in enumerate(order):
            result.append({"phase": "measurement", "repetition": repetition, "position": position, "order": order,
                           "implementation": implementation, "size": size, "seed": 17, "category": "ok",
                           "elapsed_ns": size // 128 * (1_000_000 if implementation == "reference" else candidate_time)})
    return {"passed": True, "samples": result, "summary": {"median_paired_ratio": 999999999}}


def inputs(cohort="synthetic"):
    names = ("reference", "identity", *CANDIDATES, "deliberately_wrong")
    sources = {name: source(name) for name in names}
    config = {"measure_cases": [[128, 17], [256, 17]], "repeats": 4, "warmups": 0,
              "quality": {"min_median_ns": 100000, "max_relative_iqr": 0.2, "rank_tolerance": 1, "near_tie_fraction": 0.03}}
    protocol = {"schema_version": "3.0", "export_cohort": cohort, "execution_contract": {"input_kind": "finite_float64"},
                "source_run": {"run_id": "old-goal002"}, "compiler": {"compiler": "test-clang", "target_flags": []},
                "measurement_config": config, "candidates": {name: sources[name] for name in CANDIDATES},
                "reference": sources["reference"], "controls": {name: sources[name] for name in ("identity", "deliberately_wrong")},
                "policies": {"near_tie_fraction": 0.03, "measurement_phase": "confirmation", "quality_warning_action": "withhold_decisive_judgment"},
                "requests": []}
    freeze = {"cohort": cohort, "frozen_utc": "2026-09-10T00:00:00+00:00", "requests": []}
    for size in (128, 256):
        for trial in range(1, 6):
            options = {f"option_{position}": name for position, name in enumerate(CANDIDATES)}
            for condition in ("none", "spec"):
                request_id = f"n{size}-t{trial:02}"
                request_key = request_id + "-" + condition
                protocol["requests"].append({"request_key": request_key, "request_id": request_id, "size": size, "seed": 17,
                                             "trial": trial, "condition": condition, "option_mapping": options})
                freeze["requests"].append({"request_key": request_key, "status": "valid", "selected_candidate_id": CANDIDATES[trial - 1],
                                           "attempt_id": "attempt-1", "invalid_reason": None, "raw_response_sha256": "a" * 64,
                                           "metadata": {"cohort": cohort, "model_id": None,
                                                        "blinding": {"independent_session": True, "no_tools": True, "no_prior_results": True}}})
    freeze["protocol_sha256"] = protocol_hash(protocol)
    measurement = {"run_id": "new-after-freeze", "kernel": "gemm_smoke", "environment_role": "development_smoke", "publishable_benchmark": False,
                   "compiler": deepcopy(protocol["compiler"]), "settings": deepcopy(config), "execution_contract": deepcopy(protocol["execution_contract"]),
                   "candidates": {name: {"source_sha256": sources[name]["source_sha256"], "build": {"passed": True},
                                          "verification": {"passed": name != "deliberately_wrong"}} for name in names},
                   "phases": {"confirmation": {"phase": "confirmation", "started_utc": "2026-09-10T00:01:00Z", "measurements": {
                       name: {f"n{size}_seed17": samples(name, size, time) for size in (128, 256)}
                       for name, time in zip(CANDIDATES, (1000000, 800000, 600000, 400000, 200000))}},
                       "exploration": {}}}
    measurement["phases"]["exploration"] = deepcopy(measurement["phases"]["confirmation"])
    measurement["phases"]["exploration"]["phase"] = "exploration"
    return protocol, freeze, measurement


def test_scores_all_twenty_from_raw_confirmation_and_preserves_inputs():
    values = inputs()
    original = deepcopy(values)
    report = score_selection(*values)
    assert values == original
    assert report["counts"] == {"planned": 20, "actual": 20, "valid": 20, "invalid": 0, "missing": 0}
    assert report["real_response_count"] == 0
    assert report["synthetic_response_count"] == 20
    assert report["independent_measurement_runs"] == 1
    assert report["shared_measurement_run_id"] == "new-after-freeze"
    rows = {row["request_key"]: row for row in report["requests"]}
    assert rows["n128-t01-none"]["observed_time_ns"] == 1000000
    assert rows["n128-t01-none"]["reference_ratio"] == 1
    assert rows["n128-t01-none"]["loss_to_observed_best_fraction"] == 4
    assert rows["n128-t05-spec"]["loss_to_observed_best_fraction"] == 0
    assert all(row["judgment_status"] == "descriptive_only" for row in rows.values())
    assert report["paired_change_counts"] == {"planned_pairs": 10, "valid_pairs": 10, "changed": 0}
    assert all(item["counts"] == {name: 1 for name in CANDIDATES} for item in report["selection_frequencies"])


def test_cached_summaries_never_influence_scoring():
    protocol, freeze, measurement = inputs()
    expected = score_selection(protocol, freeze, measurement)
    for candidate in measurement["phases"]["confirmation"]["measurements"].values():
        for item in candidate.values():
            item["summary"] = {"candidate": {"median_ns": 1}, "median_paired_ratio": 9999}
            item["warnings"] = [{"code": "stale"}]
    assert score_selection(protocol, freeze, measurement) == expected


def test_all_fixed_policies_and_uniform_expectation_are_always_included():
    report = score_selection(*inputs())
    assert len(report["policies"]) == 28  # Four size/condition groups, each seven policies.
    policies = {policy["policy_id"]: policy for policy in report["policies"] if policy["size"] == 128 and policy["condition"] == "none"}
    assert set(policies) == {"llm_none", "uniform_random_exact_expectation", *("always_" + name for name in CANDIDATES)}
    random = policies["uniform_random_exact_expectation"]
    assert random["mean_observed_time_ns"] == 600000
    assert random["mean_reference_ratio"] == pytest.approx((1 + 1.25 + 1 / .6 + 2.5 + 5) / 5)
    assert random["mean_loss_to_observed_best_fraction"] == 2
    assert random["probabilities"] == {name: 0.2 for name in CANDIDATES}
    assert all(policy["offline_policy_scoring"] is True for policy in policies.values())
    assert policies["always_unroll_16"]["mean_observed_time_ns"] == 200000
    assert policies["always_unroll_1"]["mean_loss_to_observed_best_fraction"] == 4


def test_missing_and_invalid_responses_remain_in_denominators_without_imputation():
    protocol, freeze, measurement = inputs("real")
    freeze["requests"] = freeze["requests"][2:]
    freeze["requests"][0].update(status="invalid", selected_candidate_id=None, invalid_reason="unknown option")
    report = score_selection(protocol, freeze, measurement)
    assert report["counts"] == {"planned": 20, "actual": 18, "valid": 17, "invalid": 1, "missing": 2}
    assert report["real_response_count"] == 18 and report["synthetic_response_count"] == 0
    for row in report["requests"]:
        if row["status"] != "valid":
            assert all(row[key] is None for key in ("observed_time_ns", "reference_ratio", "loss_to_observed_best_fraction"))
    policy = next(policy for policy in report["policies"] if policy["policy_id"] == "llm_none" and policy["size"] == 128)
    assert policy["planned_request_count"] == 5
    assert policy["scored_count"] == 3
    assert policy["response_counts"]["invalid"] == policy["response_counts"]["missing"] == 1
    assert policy["selection_frequency"]["denominator"] == 5
    assert policy["judgment_status"] == "deferred"
    assert report["paired_change_counts"]["valid_pairs"] == 8


def test_zero_real_answers_has_twenty_missing_and_no_fabricated_llm_values():
    protocol, freeze, measurement = inputs("real")
    freeze["requests"] = []
    report = score_selection(protocol, freeze, measurement)
    assert report["counts"] == {"planned": 20, "actual": 0, "valid": 0, "invalid": 0, "missing": 20}
    assert report["real_response_count"] == 0
    llm_policies = [policy for policy in report["policies"] if policy["policy_id"].startswith("llm_")]
    assert all(policy["mean_observed_time_ns"] is None for policy in llm_policies)
    assert len(report["policies"]) == 28


def test_paired_none_spec_changes_use_internal_ids():
    protocol, freeze, measurement = inputs()
    freeze["requests"][1]["selected_candidate_id"] = "unroll_16"
    report = score_selection(protocol, freeze, measurement)
    assert report["paired_change_counts"]["changed"] == 1
    pair = report["paired_changes"][0]
    assert pair["selection_changed"] is True
    assert pair["none"]["selected_candidate_id"] == "unroll_1"
    assert pair["spec"]["selected_candidate_id"] == "unroll_16"


def test_near_ties_are_tolerance_observations_not_correct_or_incorrect():
    protocol, freeze, measurement = inputs()
    measurement["phases"]["confirmation"]["measurements"]["unroll_8"]["n128_seed17"] = samples("unroll_8", 128, 204000)
    report = score_selection(protocol, freeze, measurement)
    row = next(row for row in report["requests"] if row["request_key"] == "n128-t04-none")
    assert row["near_tie"] is True
    assert row["loss_to_observed_best_fraction"] == pytest.approx(.02)
    assert row["judgment_status"] == "descriptive_only"
    assert not ({"correct", "incorrect", "accuracy"} & set(row))
    assert report["measurement_table"]["n128_seed17"]["near_tie_candidate_ids"] == ["unroll_8", "unroll_16"]


def test_quality_warnings_hold_judgment_for_all_choices_in_affected_case():
    protocol, freeze, measurement = inputs()
    measurement["phases"]["confirmation"]["measurements"]["unroll_1"]["n128_seed17"] = samples("unroll_1", 128, 1)
    report = score_selection(protocol, freeze, measurement)
    row = next(row for row in report["requests"] if row["request_key"] == "n128-t05-spec")
    assert row["observed_time_ns"] == 200000
    assert row["judgment_status"] == "deferred"
    assert any(warning["code"] == "measurement_too_short" for warning in row["warnings"])
    assert all(policy["judgment_status"] == "deferred" for policy in report["policies"] if policy["size"] == 128)


@pytest.mark.parametrize("declaration", [None, False, "true"])
def test_real_blinding_unknown_or_false_is_recorded_without_guessing(declaration):
    protocol, freeze, measurement = inputs("real")
    freeze["requests"][0]["metadata"]["blinding"]["no_prior_results"] = declaration
    report = score_selection(protocol, freeze, measurement)
    row = report["requests"][0]
    assert row["metadata"]["model_id"] is None
    assert row["metadata"]["blinding"]["no_prior_results"] == declaration
    assert row["judgment_status"] == "deferred"
    assert row["blinding_status"] == "unknown_or_not_satisfied"
    assert row["observed_time_ns"] == 1000000


def test_true_manual_blinding_declarations_are_self_reported_not_verified():
    report = score_selection(*inputs("real"))
    assert all(row["blinding_status"] == "self_reported_not_independently_verified" for row in report["requests"])


@pytest.mark.parametrize("failure", ["missing", "unverified", "failed", "wrong_input"])
def test_incomplete_measurement_table_does_not_substitute_best_over_survivors(failure):
    protocol, freeze, measurement = inputs()
    measured = measurement["phases"]["confirmation"]["measurements"]
    if failure == "missing":
        del measured["unroll_16"]["n128_seed17"]
    elif failure == "unverified":
        measurement["candidates"]["unroll_16"]["verification"]["passed"] = False
    elif failure == "failed":
        measured["unroll_16"]["n128_seed17"]["passed"] = False
    else:
        measured["unroll_16"]["n128_seed17"]["samples"][0]["seed"] = 42
    report = score_selection(protocol, freeze, measurement)
    case = report["measurement_table"]["n128_seed17"]
    assert case["observed_best_time_ns"] is None
    assert case["observed_best_candidate_ids"] == []
    assert case["judgment_status"] == "deferred"
    assert all(candidate["loss_to_observed_best_fraction"] is None for candidate in case["candidates"].values())
    random = next(policy for policy in report["policies"] if policy["policy_id"] == "uniform_random_exact_expectation" and policy["size"] == 128)
    assert random["mean_observed_time_ns"] is None


@pytest.mark.parametrize("mutation,reason", [
    (lambda p, f, m: f.update(protocol_sha256="a" * 64), "protocol hash"),
    (lambda p, f, m: m.update(run_id="old-goal002"), "old source run"),
    (lambda p, f, m: m["phases"]["confirmation"].update(started_utc="2026-09-09T23:59:59Z"), "before responses"),
    (lambda p, f, m: m["phases"]["confirmation"].update(started_utc="2026-09-10T01:00:00"), "UTC timestamp"),
    (lambda p, f, m: m["compiler"].update(target_flags=["-march=native"]), "CompilerTarget"),
    (lambda p, f, m: m["settings"].update(repeats=100), "settings"),
    (lambda p, f, m: m["execution_contract"].update(tolerance=1), "execution contract"),
    (lambda p, f, m: m["candidates"]["unroll_1"].update(source_sha256="b" * 64), "source changed"),
    (lambda p, f, m: f["requests"][0]["metadata"].update(cohort="real"), "mixed real and synthetic"),
    (lambda p, f, m: f["requests"][0].update(cohort="real"), "mixed real and synthetic"),
    (lambda p, f, m: f["requests"].append(deepcopy(f["requests"][0])), "duplicate requests"),
    (lambda p, f, m: f["requests"][0].update(selected_candidate_id="identity"), "unknown candidate"),
    (lambda p, f, m: f.update(counts={"actual": 7}), "count mismatch"),
])
def test_protocol_freeze_and_new_measurement_gates(mutation, reason):
    protocol, freeze, measurement = inputs()
    mutation(protocol, freeze, measurement)
    with pytest.raises(ValueError, match=reason):
        score_selection(protocol, freeze, measurement)


def test_paired_protocol_mapping_cannot_silently_change_between_conditions():
    protocol, freeze, measurement = inputs()
    protocol["requests"][1]["option_mapping"] = dict(zip(protocol["requests"][1]["option_mapping"], reversed(CANDIDATES)))
    freeze["protocol_sha256"] = protocol_hash(protocol)
    with pytest.raises(ValueError, match="different common"):
        score_selection(protocol, freeze, measurement)


def test_report_writers_keep_missing_values_blank_and_prevent_overwrite(tmp_path):
    protocol, freeze, measurement = inputs("real")
    freeze["requests"] = freeze["requests"][1:]
    report = score_selection(protocol, freeze, measurement)
    paths = write_selection_reports(tmp_path, report)
    assert paths == {"json": "selection-report.json", "csv": "selection-report.csv", "markdown": "selection-report.md"}
    assert json.loads((tmp_path / paths["json"]).read_text()) == report
    with (tmp_path / paths["csv"]).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 48
    missing = next(row for row in rows if row["request_key"] == "n128-t01-none")
    assert missing["observed_time_ns"] == missing["reference_ratio"] == missing["loss_to_observed_best_fraction"] == ""
    text = (tmp_path / paths["markdown"]).read_text()
    assert "独立した計測 run は **1**" in text
    assert "publishable_benchmark=false" in text
    assert "無効 0、未回答 1" in text
    assert "uniform_random_exact_expectation" in text
    with pytest.raises(ValueError, match="already exists"):
        write_selection_reports(tmp_path, report)


@pytest.mark.parametrize("mutation", [
    lambda item: item.update(samples=item["samples"][:4]),
    lambda item: item["samples"][0].update(experiment_phase="exploration"),
    lambda item: item["samples"][0].update(position=1),
    lambda item: item["samples"][0].update(pair_candidate="unroll_16"),
])
def test_frozen_sample_count_phase_and_order_must_match_before_scoring(mutation):
    protocol, freeze, measurement = inputs()
    mutation(measurement["phases"]["confirmation"]["measurements"]["unroll_1"]["n128_seed17"])
    report = score_selection(protocol, freeze, measurement)
    candidate = report["measurement_table"]["n128_seed17"]["candidates"]["unroll_1"]
    assert candidate["observed_time_ns"] is None
    assert candidate["warnings"][0]["code"] == "measurement_identity_mismatch"


def test_reference_verification_failure_prevents_any_candidate_scoring():
    protocol, freeze, measurement = inputs()
    measurement["candidates"]["reference"]["verification"]["passed"] = False
    report = score_selection(protocol, freeze, measurement)
    assert all(row["observed_time_ns"] is None for row in report["requests"])


def test_new_run_cross_phase_rank_warnings_defer_judgment_without_pooling_metrics():
    protocol, freeze, measurement = inputs()
    original = score_selection(protocol, freeze, measurement)
    measurement["phases"]["exploration"]["measurements"]["unroll_1"]["n128_seed17"] = samples("unroll_1", 128, 150000)
    changed = score_selection(protocol, freeze, measurement)
    original_rows = {row["request_key"]: row for row in original["requests"]}
    for row in changed["requests"]:
        assert all(row[key] == original_rows[row["request_key"]][key] for key in ("observed_time_ns", "reference_ratio", "loss_to_observed_best_fraction"))
        if row["size"] == 128:
            assert row["judgment_status"] == "deferred"
            assert {"rank_unstable", "observed_winner_changed"} <= {warning["code"] for warning in row["warnings"]}
        else:
            assert row["judgment_status"] == "descriptive_only"
    for previous, current in zip(original["policies"], changed["policies"]):
        assert all(previous[key] == current[key] for key in ("mean_observed_time_ns", "mean_reference_ratio", "mean_loss_to_observed_best_fraction"))


@pytest.mark.parametrize("counts", [{"received": 19}, {"total": 19}, {"received": True}])
def test_freeze_received_total_count_aliases_are_validated(counts):
    protocol, freeze, measurement = inputs()
    freeze["counts"] = counts
    with pytest.raises(ValueError, match="count mismatch"):
        score_selection(protocol, freeze, measurement)


def test_freeze_received_total_count_aliases_are_explicitly_supported():
    protocol, freeze, measurement = inputs()
    freeze["counts"] = {"received": 20, "total": 20, "valid": 20, "invalid": 0, "missing": 0}
    assert score_selection(protocol, freeze, measurement)["counts"]["actual"] == 20


def test_real_protocol_cannot_score_synthetic_freeze_even_with_a_matching_hash():
    protocol, freeze, measurement = inputs()
    protocol["export_cohort"] = "real"
    freeze["protocol_sha256"] = protocol_hash(protocol)
    with pytest.raises(ValueError, match="cohorts differ"):
        score_selection(protocol, freeze, measurement)
