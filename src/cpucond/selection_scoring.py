"""Offline scoring of frozen selections against one new confirmation table.

This module neither obtains model responses nor executes a compiler or kernel.
Request counts are never interpreted as independent performance measurements.
"""

from copy import deepcopy
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics

from .diagnostic_reporting import build_report, summarize_measurement


CANDIDATES = tuple(f"unroll_{factor}" for factor in (1, 2, 4, 8, 16))
CONDITIONS = ("none", "spec")
BLINDING_FIELDS = ("independent_session", "no_tools", "no_prior_results")
METRICS = ("observed_time_ns", "reference_ratio", "loss_to_observed_best_fraction")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _sha(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _utc(value, label):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{label} must be an explicit UTC timestamp") from exc
    _require(parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0,
             f"{label} must be an explicit UTC timestamp")
    return parsed


def _warn(code, reason, **context):
    return {"code": code, "reason": reason, **context}


def _validate(protocol, freeze, measurement):
    _require(protocol.get("schema_version") == "3.0", "unsupported selection protocol schema")
    _require(freeze.get("cohort") in ("real", "synthetic"), "cohort must be real or synthetic")
    _require(protocol.get("export_cohort") == freeze["cohort"], "protocol and freeze cohorts differ; real and synthetic must stay separate")
    _require(freeze.get("protocol_sha256") == _sha(protocol), "response freeze protocol hash mismatch")
    _require(set(protocol.get("candidates", {})) == set(CANDIDATES), "protocol must contain the fixed five candidates")
    _require(measurement.get("environment_role") == "development_smoke" and measurement.get("publishable_benchmark") is False,
             "measurement must retain development_smoke classification")
    _require(measurement.get("kernel") == "gemm_smoke", "measurement uses a different kernel")
    _require(measurement.get("run_id") and measurement["run_id"] != protocol.get("source_run", {}).get("run_id"),
             "old source run cannot be reused as independent confirmation")
    _require(measurement.get("compiler") == protocol.get("compiler") and isinstance(protocol.get("compiler"), dict),
             "measurement CompilerTarget differs from protocol")
    _require(isinstance(protocol.get("execution_contract"), dict)
             and protocol["execution_contract"] == measurement.get("execution_contract"),
             "measurement execution contract differs from protocol")
    config = protocol.get("measurement_config")
    _require(isinstance(config, dict) and measurement.get("settings") == config,
             "measurement settings differ from protocol")
    _require(isinstance(config.get("quality"), dict), "protocol measurement quality policy missing")
    confirmation = measurement.get("phases", {}).get("confirmation")
    _require(isinstance(confirmation, dict) and confirmation.get("phase") == "confirmation",
             "new confirmation phase is missing")
    _require(_utc(confirmation.get("started_utc"), "confirmation start") >= _utc(freeze.get("frozen_utc"), "response freeze"),
             "confirmation was measured before responses were frozen")
    measured_candidates = measurement.get("candidates", {})
    _require(set(CANDIDATES) | {"reference", "identity", "deliberately_wrong"} <= set(measured_candidates),
             "measurement must retain all fixed candidates and controls")
    source_entries = dict(protocol["candidates"])
    if isinstance(protocol.get("reference"), dict):
        source_entries["reference"] = protocol["reference"]
    source_entries.update(protocol.get("controls", {}))
    for name, entry in source_entries.items():
        _require(name in measured_candidates, f"measurement candidate missing: {name}")
        _require(isinstance(entry.get("source"), str) and hashlib.sha256(entry["source"].encode("utf-8")).hexdigest() == entry.get("source_sha256"),
                 f"protocol candidate source hash mismatch: {name}")
        _require(measured_candidates[name].get("source_sha256") == entry["source_sha256"],
                 f"measurement candidate source changed: {name}")
        for filename, shared_source in protocol.get("shared_sources", {}).items():
            _require(measured_candidates[name].get("build", {}).get("source_hashes", {}).get(filename) == shared_source.get("sha256"),
                     f"measurement shared driver/header source changed: {name}/{filename}")
    requests = protocol.get("requests")
    _require(isinstance(requests, list) and bool(requests), "protocol requests are missing")
    keys, pairs = set(), {}
    configured_cases = {tuple(case) for case in config.get("measure_cases", [])}
    for request in requests:
        key = request.get("request_key")
        _require(isinstance(key, str) and key not in keys, "protocol request keys must be unique")
        keys.add(key)
        _require(request.get("condition") in CONDITIONS, "unsupported selection condition")
        _require((request.get("size"), request.get("seed")) in configured_cases, "request input was not fixed for measurement")
        mapping = request.get("option_mapping", {})
        _require(len(mapping) == 5 and set(mapping.values()) == set(CANDIDATES), "request must expose exactly the fixed five choices")
        pair = pairs.setdefault(request.get("request_id"), {})
        _require(request["condition"] not in pair, "duplicate condition for a paired request")
        pair[request["condition"]] = request
    for pair in pairs.values():
        _require(set(pair) == set(CONDITIONS), "protocol must contain paired none/spec requests")
        _require(all(pair["none"].get(key) == pair["spec"].get(key) for key in ("size", "seed", "trial", "option_mapping")),
                 "paired none/spec requests have different common conditions")
    near_tie = protocol.get("policies", {}).get("near_tie_fraction")
    _require(isinstance(near_tie, (int, float)) and not isinstance(near_tie, bool) and math.isfinite(near_tie) and near_tie >= 0,
             "a finite nonnegative near-tie threshold must be fixed in the protocol")
    _require(protocol.get("policies", {}).get("measurement_phase") == "confirmation", "scoring requires the confirmation-only policy")
    _require(protocol.get("policies", {}).get("quality_warning_action") == "withhold_decisive_judgment",
             "protocol must withhold decisive judgment on quality warnings")
    frozen = {}
    for item in freeze.get("requests", []):
        key = item.get("request_key")
        _require(key in keys and key not in frozen, "freeze contains unknown or duplicate requests")
        _require(item.get("status") in ("valid", "invalid", "missing"), "unknown frozen response status")
        _require(item.get("cohort", freeze["cohort"]) == freeze["cohort"], "mixed real and synthetic cohorts are forbidden")
        metadata = item.get("metadata")
        _require(metadata is None or isinstance(metadata, dict), "response metadata must be an object or null")
        if metadata is not None:
            _require(metadata.get("cohort", freeze["cohort"]) == freeze["cohort"], "mixed real and synthetic cohorts are forbidden")
        if item["status"] == "valid":
            _require(item.get("selected_candidate_id") in CANDIDATES, "valid response selected an unknown candidate")
        else:
            _require(item.get("selected_candidate_id") is None, "invalid or missing responses cannot select a candidate")
        frozen[key] = item
    return requests, frozen, confirmation, near_tie


def _measurement_table(protocol, confirmation, measurement, near_tie):
    table = {}
    quality = protocol["measurement_config"]["quality"]
    reference = measurement["candidates"]["reference"]
    reference_verified = reference.get("build", {}).get("passed") is True and reference.get("verification", {}).get("passed") is True
    cases = sorted({(request["size"], request["seed"]) for request in protocol["requests"]})
    for size, seed in cases:
        case_id = f"n{size}_seed{seed}"
        case = {"size": size, "seed": seed, "candidates": {}, "warnings": [], "observed_best_time_ns": None,
                "observed_best_candidate_ids": [], "near_tie_candidate_ids": [], "judgment_status": "deferred"}
        for name in CANDIDATES:
            candidate = measurement["candidates"][name]
            raw = confirmation.get("measurements", {}).get(name, {}).get(case_id)
            verified = reference_verified and candidate.get("build", {}).get("passed") is True and candidate.get("verification", {}).get("passed") is True
            if not verified:
                result = {"passed": False, "summary": None, "warnings": [_warn("verification_failed", "Candidate has not passed the fixed verification contract; timing is excluded.")]}
            else:
                result = summarize_measurement(raw, quality)
                if result["passed"]:
                    valid_identity = result["summary"].get("candidate_implementation") == name
                    planned = []
                    config = protocol["measurement_config"]
                    for phase, count in (("warmup", config["warmups"]), ("measurement", config["repeats"])):
                        for repetition in range(count):
                            order = ["reference", name] if repetition % 2 == 0 else [name, "reference"]
                            planned.extend({"phase": phase, "repetition": repetition, "position": position, "implementation": implementation,
                                            "order": order, "size": size, "seed": seed} for position, implementation in enumerate(order))
                    valid_inputs = len(result["samples"]) == len(planned) and all(
                        all(sample.get(key) == value for key, value in expected.items())
                        and sample.get("experiment_phase", "confirmation") == "confirmation"
                        and sample.get("pair_candidate", name) == name
                        for sample, expected in zip(result["samples"], planned))
                    if not valid_identity or not valid_inputs:
                        result = {"passed": False, "summary": None, "warnings": [_warn("measurement_identity_mismatch", "Raw confirmation samples do not match the fixed candidate, input, phase, repetition count or execution order.")]}
            summary = result["summary"]
            item = {"candidate_id": name, "verification_passed": verified, "measurement_passed": result["passed"],
                    "observed_time_ns": summary["candidate"]["median_ns"] if summary else None,
                    "observed_iqr_ns": summary["candidate"]["iqr_ns"] if summary else None,
                    "reference_ratio": summary["median_paired_ratio"] if summary else None,
                    "paired_ratios": summary["paired_ratios"] if summary else None,
                    "loss_to_observed_best_fraction": None, "near_tie": None,
                    "warnings": [{**warning, "candidate_id": name, "case_id": case_id} for warning in result["warnings"]]}
            case["candidates"][name] = item
            case["warnings"].extend(item["warnings"])
        if all(item["measurement_passed"] for item in case["candidates"].values()):
            best = min(item["observed_time_ns"] for item in case["candidates"].values())
            case["observed_best_time_ns"] = best
            for name, item in case["candidates"].items():
                item["loss_to_observed_best_fraction"] = item["observed_time_ns"] / best - 1
                item["near_tie"] = item["loss_to_observed_best_fraction"] <= near_tie
                if item["observed_time_ns"] == best:
                    case["observed_best_candidate_ids"].append(name)
                if item["near_tie"]:
                    case["near_tie_candidate_ids"].append(name)
            if not case["warnings"]:
                case["judgment_status"] = "descriptive_only"
        else:
            case["warnings"].append(_warn("incomplete_fixed_candidate_table", "The fixed five-candidate measurement table is incomplete; no best over a surviving subset is substituted.", case_id=case_id))
        table[case_id] = case
    # Reuse the existing, predeclared rank-stability diagnostic. Exploration
    # contributes only to this quality gate, never to scored timing metrics.
    diagnostic = build_report(measurement)
    for warning in diagnostic["warnings"]:
        code, case_id = warning["code"], warning.get("case_id")
        if case_id not in table:
            continue
        relevant = code == "rank_unstable" and warning.get("candidate_id") in CANDIDATES
        if code == "observed_winner_changed":
            winners = {name for names in warning.get("winners", {}).values() for name in names}
            relevant = bool(winners & set(CANDIDATES))
        if relevant:
            table[case_id]["warnings"].append({**deepcopy(warning), "source": "recomputed_new_run_cross_phase_quality",
                                               "scoring_role": "quality gate only; scored numeric metrics remain confirmation-only"})
            table[case_id]["judgment_status"] = "deferred"
    return table


def _counts(rows):
    counts = {"planned": len(rows), "actual": sum(row["status"] != "missing" for row in rows)}
    counts.update({status: sum(row["status"] == status for row in rows) for status in ("valid", "invalid", "missing")})
    return counts


def _blinding(metadata, cohort):
    if cohort == "synthetic":
        return "synthetic_not_model_evidence", []
    declarations = (metadata or {}).get("blinding")
    declarations = declarations if isinstance(declarations, dict) else {}
    unavailable = [field for field in BLINDING_FIELDS if declarations.get(field) is not True]
    if unavailable:
        return "unknown_or_not_satisfied", [_warn("blinding_not_established", "Independent session, no tools and no prior results are not all declared true; decisive interpretation is withheld.", fields=unavailable)]
    return "self_reported_not_independently_verified", []


def _frequency(rows):
    result = {name: sum(row["status"] == "valid" and row["selected_candidate_id"] == name for row in rows) for name in CANDIDATES}
    return {"counts": result, "denominator": len(rows), "fractions_of_planned": {name: count / len(rows) for name, count in result.items()} if rows else {},
            "invalid": sum(row["status"] == "invalid" for row in rows), "missing": sum(row["status"] == "missing" for row in rows)}


def _metric_means(items):
    # Missing observations remain explicitly counted outside this aggregate.
    return {"mean_" + key: statistics.mean(values) if (values := [item[key] for item in items if item[key] is not None]) else None for key in METRICS}


def _policies(rows, table):
    groups = sorted({(row["size"], row["seed"], row["condition"]) for row in rows})
    results = []
    for size, seed, condition in groups:
        selected = [row for row in rows if (row["size"], row["seed"], row["condition"]) == (size, seed, condition)]
        case_id = f"n{size}_seed{seed}"
        case = table[case_id]
        common = {"size": size, "seed": seed, "condition": condition, "planned_request_count": len(selected),
                  "shared_measurement_case_id": case_id, "independent_measurement_runs": 1}
        valid_metrics = [row for row in selected if row["status"] == "valid" and row["observed_time_ns"] is not None]
        results.append({**common, "policy_id": "llm_" + condition, "policy_kind": "frozen_response_selection",
                        "offline_policy_scoring": True, "response_counts": _counts(selected), "scored_count": len(valid_metrics),
                        "selection_frequency": _frequency(selected), **_metric_means(valid_metrics),
                        "summary_scope": "available valid responses only; invalid/missing remain in planned_request_count and response_counts",
                        "judgment_status": "deferred" if len(valid_metrics) != len(selected) or any(row["judgment_status"] == "deferred" for row in selected) else "descriptive_only",
                        "warnings": [warning for row in selected for warning in row["warnings"]]})
        for name in CANDIDATES:
            candidate = case["candidates"][name]
            results.append({**common, "policy_id": "always_" + name, "policy_kind": "fixed_selection",
                            "offline_policy_scoring": True, "response_counts": None,
                            "scored_count": len(selected) if candidate["measurement_passed"] else 0,
                            **{"mean_" + key: candidate[key] for key in METRICS},
                            "summary_scope": "one saved candidate measurement reused for every policy decision; not repeated measurements",
                            "judgment_status": case["judgment_status"], "warnings": deepcopy(case["warnings"])})
        complete = all(candidate["measurement_passed"] for candidate in case["candidates"].values())
        results.append({**common, "policy_id": "uniform_random_exact_expectation", "policy_kind": "uniform_random",
                        "offline_policy_scoring": True, "response_counts": None, "scored_count": len(selected) if complete else 0,
                        "probabilities": {name: 1 / len(CANDIDATES) for name in CANDIDATES},
                        **(_metric_means(list(case["candidates"].values())) if complete else {"mean_" + key: None for key in METRICS}),
                        "summary_scope": "exact expectation across all five saved candidate metrics; no random draws or new kernel executions",
                        "ratio_expectation": "arithmetic mean of the five median paired reference ratios, not a ratio of expected times",
                        "judgment_status": case["judgment_status"], "warnings": deepcopy(case["warnings"])})
    return results


def score_selection(protocol, freeze, measurement_record):
    """Score every planned request; invalid/missing choices keep null metrics.

    File provenance and freeze/measurement lifecycle are also audited by the
    caller. This pure gate checks hashes, settings, sources, cohort and time
    ordering, and recomputes confirmation summaries instead of trusting reports.
    """
    requests, frozen, confirmation, near_tie = _validate(protocol, freeze, measurement_record)
    table = _measurement_table(protocol, confirmation, measurement_record, near_tie)
    rows = []
    for request in sorted(requests, key=lambda item: (item["size"], item["seed"], item["trial"], item["condition"])):
        answer = frozen.get(request["request_key"], {"status": "missing", "selected_candidate_id": None})
        row = {key: deepcopy(request[key]) for key in ("request_key", "request_id", "size", "seed", "trial", "condition")}
        row.update({key: deepcopy(answer.get(key)) for key in ("status", "selected_candidate_id", "attempt_id", "invalid_reason", "raw_response_sha256", "metadata")})
        row.update(cohort=freeze["cohort"], shared_measurement_run_id=measurement_record["run_id"], measurement_phase="confirmation",
                   observed_time_ns=None, observed_iqr_ns=None, reference_ratio=None, loss_to_observed_best_fraction=None,
                   near_tie=None, judgment_status="not_scored", warnings=[])
        row["blinding_status"], blinding_warnings = _blinding(row["metadata"], freeze["cohort"])
        if answer["status"] == "valid":
            case = table[f"n{request['size']}_seed{request['seed']}"]
            candidate = case["candidates"][answer["selected_candidate_id"]]
            row.update({key: candidate[key] for key in (*METRICS, "observed_iqr_ns", "near_tie")})
            row["warnings"] = deepcopy(case["warnings"]) + blinding_warnings
            row["judgment_status"] = "deferred" if row["warnings"] or case["judgment_status"] == "deferred" else "descriptive_only"
        else:
            row["warnings"].append(_warn("response_" + answer["status"], answer.get("invalid_reason") or "No valid candidate selection is available; planned denominator is retained."))
        rows.append(row)
    counts = _counts(rows)
    recorded_counts = freeze.get("counts", {})
    for key, value in recorded_counts.items():
        mapped = {"received": "actual", "total": "planned"}.get(key, key)
        if mapped in counts:
            _require(type(value) is int and value == counts[mapped], f"frozen response count mismatch: {key}")
    paired = []
    for request_id in sorted({row["request_id"] for row in rows}):
        pair = {row["condition"]: row for row in rows if row["request_id"] == request_id}
        valid = all(pair[condition]["status"] == "valid" for condition in CONDITIONS)
        paired.append({"request_id": request_id, "size": pair["none"]["size"], "seed": pair["none"]["seed"], "trial": pair["none"]["trial"],
                       "none": {key: pair["none"][key] for key in ("request_key", "status", "selected_candidate_id")},
                       "spec": {key: pair["spec"][key] for key in ("request_key", "status", "selected_candidate_id")},
                       "selection_changed": pair["none"]["selected_candidate_id"] != pair["spec"]["selected_candidate_id"] if valid else None,
                       "interpretation": "paired choice change only; no independent performance replicate"})
    policies = _policies(rows, table)
    report = {"schema_version": "3.0", "report_type": "blind_selection_offline_scoring", "cohort": freeze["cohort"],
              "protocol_sha256": freeze["protocol_sha256"], "response_freeze_sha256": _sha(freeze),
              "environment_role": "development_smoke", "publishable_benchmark": False,
              "counts": counts, "real_response_count": counts["actual"] if freeze["cohort"] == "real" else 0,
              "synthetic_response_count": counts["actual"] if freeze["cohort"] == "synthetic" else 0,
              "requests": rows, "paired_changes": paired, "paired_change_counts": {
                  "planned_pairs": len(paired), "valid_pairs": sum(item["selection_changed"] is not None for item in paired),
                  "changed": sum(item["selection_changed"] is True for item in paired)},
              "selection_frequencies": [{"size": policy["size"], "seed": policy["seed"], "condition": policy["condition"], **policy["selection_frequency"]}
                                        for policy in policies if policy["policy_kind"] == "frozen_response_selection"],
              "policies": policies, "measurement_table": table, "measurement_phase": "confirmation",
              "shared_measurement_run_id": measurement_record["run_id"], "independent_measurement_runs": 1,
              "shared_measurement": "all response and policy scores reuse one confirmation run; request counts are not independent timing replicates",
              "metrics": {"observed_time_ns": "candidate median kernel time from new confirmation only",
                          "reference_ratio": "median of paired reference time / candidate time, greater than 1 favors candidate",
                          "loss_to_observed_best_fraction": "selected candidate median / minimum median among all five fixed candidates - 1",
                          "near_tie": f"loss <= predeclared {near_tie}; descriptive tolerance, not correctness or statistical equivalence",
                          "quality_diagnostics": "Existing new-run exploration/confirmation rank_unstable and observed_winner_changed warnings are recomputed solely for judgment withholding; phase timing samples are never pooled.",
                          "aggregation": "arithmetic mean of available valid response metrics with planned, invalid, missing and scored counts explicitly retained"},
              "warnings": [warning for case in table.values() for warning in case["warnings"]],
              "limitations": ["Small development pilot; no significance, power or global optimality claim.",
                              "New-run cross-phase rank stability is a quality diagnostic only; every scored time, ratio and loss uses confirmation alone.",
                              "The task was seen by developers; not an unseen benchmark or held-out task.",
                              "Manual blinding and model metadata are self-reported, not independently verified.",
                              "All fixed and random policies use offline policy scoring; this is not a search performed by the LLM.",
                              "One host only; cross-CPU adaptation and free C code optimization are not evaluated."]}
    if freeze["cohort"] == "synthetic":
        report["limitations"].insert(0, "Synthetic software exercise only; no real LLM behavior or CPU understanding was measured.")
    if protocol.get("acquisition_backend") == "ollama_local":
        report["acquisition_backend"] = "ollama_local"
        report["local_model_config"] = deepcopy(protocol["local_llm"])
        report["limitations"] = [item for item in report["limitations"] if not item.startswith("Manual blinding")]
        report["limitations"].append(
            "Local payloads, server/model evidence and raw API responses are archived separately; "
            "the model receives only the fixed system instruction and this request's prompt. "
            "Prior developer exposure and external machine load remain limitations.")
    report["warnings"].extend({**warning, "request_key": row["request_key"]} for row in rows for warning in row["warnings"] if warning["code"].startswith(("blinding", "response_")))
    return report


def _csv_rows(report):
    for row in report["requests"]:
        yield {"row_kind": "response", "cohort": report["cohort"], "policy_id": "llm_" + row["condition"],
               "request_key": row["request_key"], "size": row["size"], "seed": row["seed"], "condition": row["condition"],
               "status": row["status"], "candidate_id": row["selected_candidate_id"], "planned_count": 1,
               "actual_count": int(row["status"] != "missing"), "valid_count": int(row["status"] == "valid"),
               "invalid_count": int(row["status"] == "invalid"), "missing_count": int(row["status"] == "missing"),
               "scored_count": int(row["observed_time_ns"] is not None), **{key: row[key] for key in METRICS},
               "judgment_status": row["judgment_status"], "shared_measurement_run_id": report["shared_measurement_run_id"],
               "independent_measurement_runs": 1, "warnings": json.dumps(row["warnings"], ensure_ascii=False, sort_keys=True)}
    for policy in report["policies"]:
        counts = policy["response_counts"] or {}
        yield {"row_kind": "policy_mean_or_exact_expectation", "cohort": report["cohort"], "policy_id": policy["policy_id"],
               "request_key": None, "size": policy["size"], "seed": policy["seed"], "condition": policy["condition"],
               "status": "offline_policy_scoring", "candidate_id": None, "planned_count": policy["planned_request_count"],
               **{key + "_count": counts.get(key) for key in ("actual", "valid", "invalid", "missing")},
               "scored_count": policy["scored_count"], **{key: policy["mean_" + key] for key in METRICS},
               "judgment_status": policy["judgment_status"], "shared_measurement_run_id": report["shared_measurement_run_id"],
               "independent_measurement_runs": 1, "warnings": json.dumps(policy["warnings"], ensure_ascii=False, sort_keys=True)}


def _cell(value):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    counts = report["counts"]
    lines = ["# Blind candidate-selection pilot", "", f"コホート: **{report['cohort']}**。", "",
             ("合成回答の動作確認であり、実 LLM の結果ではありません。" if report["cohort"] == "synthetic"
              else "Ollama ローカルモデルの実回答です。固定 payload、API 原本、モデル・サーバー証拠を別途保存しています。"
              if report.get("acquisition_backend") == "ollama_local"
              else "実回答の取得情報・盲検条件はメタデータに従います。手動申告を独立検証済みとは扱いません。"),
             "", f"計画 {counts['planned']}、取り込み {counts['actual']}、有効 {counts['valid']}、無効 {counts['invalid']}、未回答 {counts['missing']}。",
             "", f"実 LLM 回答 {report['real_response_count']}、synthetic 回答 {report['synthetic_response_count']}。", "",
             f"全採点で共有した計測 run: `{report['shared_measurement_run_id']}`。独立した計測 run は **1**。",
             "各回答は同じ confirmation 測定表を参照します。20 回答を 20 回の独立した性能測定とは数えません。", "",
             "`development_smoke`、`publishable_benchmark=false`。開発中に既知だった課題であり、unseen / held-out 評価ではありません。", "",
             "時間は候補のカーネル時間の中央値（ns）、速度比はペアごとの reference / candidate の中央値です。",
             "損失は候補時間 / 固定 5 候補内の最小中央値 − 1。僅差は事前の許容差による記述であり、正解・不正解や統計的同等性を示しません。",
             "品質警告や盲検条件の不明点があれば判定を保留し、観測値を残します。",
             "新規 run の exploration / confirmation 間の順位変動は既存の品質診断としてだけ再利用します。時間・速度比・損失の採点は confirmation のみです。", "", "## 回答ごとの採点", "",
             "| Request | 条件 | 状態 | 候補 | 時間 ns | 対参照比 | 観測最良からの損失 | 僅差範囲内 | 判定 |",
             "|---|---|---|---|---:|---:|---:|---|---|"]
    for row in report["requests"]:
        lines.append("| " + " | ".join(_cell(row[key]) for key in ("request_key", "condition", "status", "selected_candidate_id", *METRICS, "near_tie", "judgment_status")) + " |")
    lines += ["", "## 方策比較", "", "固定 5 方策をすべて掲載します。一様ランダムは 5 候補を確率 1/5 で選ぶ厳密な期待値で、追加の抽選・測定はしていません。",
              "全方策が offline policy scoring です。LLM 方策の平均は有効かつ採点可能な回答だけを使い、計画母数・無効・欠損・採点数を併記します。", "",
              "| サイズ | 条件 | 方策 | 計画 | 採点 | 無効 | 未回答 | 平均/期待時間 ns | 平均/期待速度比 | 平均/期待損失 | 判定 |",
              "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for policy in report["policies"]:
        counts = policy["response_counts"] or {}
        values = [policy["size"], policy["condition"], policy["policy_id"], policy["planned_request_count"], policy["scored_count"],
                  counts.get("invalid"), counts.get("missing"), *(policy["mean_" + key] for key in METRICS), policy["judgment_status"]]
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    lines += ["", "## 選択頻度と対応する試行の変化", ""]
    for frequency in report["selection_frequencies"]:
        lines.append(f"- n={frequency['size']} / {frequency['condition']}: " + _cell(json.dumps(frequency["counts"], sort_keys=True)) + f" / 計画母数 {frequency['denominator']}、無効 {frequency['invalid']}、未回答 {frequency['missing']}。")
    changes = report["paired_change_counts"]
    lines += ["", f"none/spec 対応ペア: 計画 {changes['planned_pairs']}、両方有効 {changes['valid_pairs']}、選択変更 {changes['changed']}。", "",
              "| ペア | none | spec | 選択変更 |", "|---|---|---|---|"]
    for pair in report["paired_changes"]:
        lines.append("| " + " | ".join(_cell(value) for value in (pair["request_id"], pair["none"]["selected_candidate_id"], pair["spec"]["selected_candidate_id"], pair["selection_changed"])) + " |")
    lines += ["", "## 品質警告・制限", ""]
    lines += ["- " + _cell(json.dumps(warning, ensure_ascii=False, sort_keys=True)) for warning in report["warnings"]]
    lines += ["- " + limitation for limitation in report["limitations"]]
    lines += ["", "モデル ID・生成設定・使用量・履歴分離は取得したメタデータだけを保存し、不明情報は推測しません。", ""]
    return "\n".join(lines)


def write_selection_reports(directory, report):
    """Save a report once; never silently overwrite an existing scoring output."""
    directory = Path(directory)
    paths = {"json": "selection-report.json", "csv": "selection-report.csv", "markdown": "selection-report.md"}
    _require(not any((directory / name).exists() for name in paths.values()), "selection report output already exists")
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / paths["json"]).open("x", encoding="utf-8") as stream:
        stream.write(_canonical(report))
    rows = list(_csv_rows(report))
    with (directory / paths["csv"]).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["row_kind"])
        writer.writeheader()
        writer.writerows(rows)
    with (directory / paths["markdown"]).open("x", encoding="utf-8") as stream:
        stream.write(render_markdown(report))
    return paths
