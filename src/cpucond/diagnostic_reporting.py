"""Pure summaries and transparent reports for controlled C diagnostics.

No measurement is performed here. Statistics are rebuilt from complete raw pairs,
and exploration and confirmation never share a sample or an aggregate.
"""

from copy import deepcopy
import csv
import json
import math
from pathlib import Path
import statistics


DEFAULT_QUALITY = {
    "min_median_ns": 100_000,
    "max_relative_iqr": 0.20,
    "rank_tolerance": 1,
    "near_tie_fraction": 0.03,
}
PHASES = ("exploration", "confirmation")
QUANTILE_METHOD = "linear interpolation at (sample_count - 1) * probability"
RATIO_DEFINITION = "reference elapsed_ns / candidate elapsed_ns within the same measured pair; greater than 1 favors candidate"


def _quality(settings):
    result = {**DEFAULT_QUALITY, **(settings or {})}
    for name in ("min_median_ns", "max_relative_iqr", "near_tie_fraction"):
        value = result[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"quality {name} must be a finite nonnegative number")
    if type(result["rank_tolerance"]) is not int or result["rank_tolerance"] < 0:
        raise ValueError("quality rank_tolerance must be a nonnegative integer")
    return result


def _warning(code, reason, **context):
    return {"code": code, "reason": reason, **context}


def _quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _statistics(values, suffix="_ns"):
    median = statistics.median(values)
    q1 = _quantile(values, 0.25)
    q3 = _quantile(values, 0.75)
    return {
        "count": len(values), "median" + suffix: median,
        "min" + suffix: min(values), "max" + suffix: max(values),
        "mad" + suffix: statistics.median(abs(x - median) for x in values),
        "population_stdev" + suffix: statistics.pstdev(values),
        "q1" + suffix: q1, "q3" + suffix: q3, "iqr" + suffix: q3 - q1,
        "relative_iqr": (q3 - q1) / median,
    }


def summarize_measurement(measurement, quality=None):
    """Return a copy enriched from raw, non-warmup complete reference pairs.

    Failed/incomplete data retains its raw samples but has a null summary, never
    a fabricated zero or partial successful aggregate. Invalid input is recorded
    as a failed measurement so it cannot acquire a performance rank.
    """
    quality = _quality(quality)
    result = deepcopy(measurement) if isinstance(measurement, dict) else {"samples": []}
    result.update(summary=None, warnings=[])

    def fail(code, reason, **context):
        result["passed"] = False
        result["warnings"].append(_warning(code, reason, **context))
        return result

    if measurement is None:
        return fail("measurement_missing", "No measurement was recorded.")
    if not isinstance(measurement, dict) or measurement.get("passed") is not True:
        samples = result.get("samples", [])
        failed = next((sample for sample in samples if isinstance(sample, dict) and sample.get("category", "ok") != "ok"), {}) if isinstance(samples, list) else {}
        return fail("measurement_failed", "The measurement did not complete successfully; partial samples are not summarized.",
                    failure_category=failed.get("category") or result.get("category"),
                    failure_reason=failed.get("reason") or result.get("reason"))
    raw = result.get("samples")
    if not isinstance(raw, list) or any(not isinstance(sample, dict) for sample in raw):
        return fail("invalid_measurement_samples", "The raw sample collection is missing or invalid.")
    if any(sample.get("category", "ok") != "ok" for sample in raw):
        return fail("measurement_failed", "A raw execution failed, including any warmup execution.")
    if any(sample.get("phase") not in ("measurement", "warmup") for sample in raw):
        return fail("invalid_measurement_samples", "Every raw sample must identify its warmup or measurement phase.")
    measured = [sample for sample in raw if sample.get("phase") == "measurement"]
    if not measured:
        return fail("measurement_samples_missing", "No non-warmup timing samples were recorded.")
    pairs = {}
    candidate_names = set()
    for sample in measured:
        elapsed = sample.get("elapsed_ns")
        repetition = sample.get("repetition")
        name = sample.get("implementation")
        if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
                or not math.isfinite(elapsed) or elapsed <= 0
                or type(repetition) is not int or repetition < 0
                or not isinstance(name, str) or not name):
            return fail("invalid_measurement_samples", "Every measured sample needs a positive finite duration, nonnegative integer repetition and implementation.")
        pair = pairs.setdefault(repetition, {})
        if name in pair:
            return fail("incomplete_measurement_pairs", "A repetition contains duplicate implementation samples.")
        pair[name] = sample
        if name != "reference":
            candidate_names.add(name)
    if len(candidate_names) != 1:
        return fail("incomplete_measurement_pairs", "Each measurement must compare exactly one candidate with reference.")
    candidate = next(iter(candidate_names))
    baseline, candidate_times, ratios = [], [], []
    for repetition in sorted(pairs):
        pair = pairs[repetition]
        if set(pair) != {"reference", candidate}:
            return fail("incomplete_measurement_pairs", "Every measured repetition must contain both reference and candidate.")
        if any(pair["reference"].get(key) != pair[candidate].get(key) for key in ("size", "seed")):
            return fail("incomplete_measurement_pairs", "The reference and candidate in a pair used different inputs.")
        base = pair["reference"]["elapsed_ns"]
        value = pair[candidate]["elapsed_ns"]
        baseline.append(base)
        candidate_times.append(value)
        ratios.append(base / value)
    if len(pairs) < 2:
        return fail("insufficient_measurement_pairs", "At least two complete measured pairs are required; one fastest observation is insufficient.")
    if any(not math.isfinite(ratio) for ratio in ratios):
        return fail("invalid_measurement_samples", "A paired ratio is not finite.")
    ratio_statistics = _statistics(ratios, suffix="")
    summary = {
        "candidate_implementation": candidate,
        "baseline": _statistics(baseline), "candidate": _statistics(candidate_times),
        "paired_ratios": ratios, "paired_repetitions": sorted(pairs),
        "median_paired_ratio": ratio_statistics["median"],
        "paired_ratio_q1": ratio_statistics["q1"], "paired_ratio_q3": ratio_statistics["q3"],
        "paired_ratio_iqr": ratio_statistics["iqr"],
        "paired_ratio_relative_iqr": ratio_statistics["relative_iqr"],
        "quantile_method": QUANTILE_METHOD, "ratio_definition": RATIO_DEFINITION,
        "interpretation": "development_smoke_only; observed timings without significance testing or CPU specialization claims",
    }
    for implementation in ("baseline", "candidate"):
        values = summary[implementation]
        if values["median_ns"] < quality["min_median_ns"]:
            result["warnings"].append(_warning(
                "measurement_too_short", "Median duration is below the predeclared timing-quality threshold; timer overhead may matter.",
                implementation=implementation, observed=values["median_ns"], threshold=quality["min_median_ns"]))
        if values["relative_iqr"] > quality["max_relative_iqr"]:
            result["warnings"].append(_warning(
                "high_relative_iqr", "Duration IQR / median exceeds the predeclared variability threshold.",
                implementation=implementation, observed=values["relative_iqr"], threshold=quality["max_relative_iqr"]))
    if summary["paired_ratio_relative_iqr"] > quality["max_relative_iqr"]:
        result["warnings"].append(_warning(
            "high_paired_ratio_relative_iqr", "Paired-ratio IQR / median exceeds the predeclared variability threshold.",
            observed=summary["paired_ratio_relative_iqr"], threshold=quality["max_relative_iqr"]))
    result.update(passed=True, summary=summary)
    return result


def _failure_reason(verification):
    if not isinstance(verification, dict):
        return "verification_result_missing"
    if verification.get("passed") is True:
        return None
    reasons = [verification.get("reason") or verification.get("category") or "verification_failed"]
    for case in verification.get("cases", []):
        if isinstance(case, dict) and case.get("passed") is not True:
            reason = case.get("reason") or case.get("category") or "verification_failed"
            if reason not in reasons:
                reasons.append(reason)
    return "; ".join(str(reason) for reason in reasons)


def _evidence_paths(value):
    found = set()

    def visit(item, path_context=False):
        if isinstance(item, dict):
            for key, child in item.items():
                visit(child, path_context or any(token in key for token in ("path", "file", "artifact", "evidence")))
        elif isinstance(item, list):
            for child in item:
                visit(child, path_context)
        elif path_context and isinstance(item, str) and ("/" in item or "\\" in item or item.endswith((".json", ".yaml", ".s", ".ll", ".disasm", ".bin", ".bytes", ".txt", ".o", ".c", ".h"))):
            found.add(item)

    visit(value)
    return sorted(found)


def _candidate_evidence_paths(candidate_id, candidate):
    def qualify(path, owner):
        return path if path.startswith(("candidates/", "/")) or ":" in path else f"candidates/{owner}/{path}"

    paths = _evidence_paths({key: candidate[key] for key in ("analysis", "optimization", "evidence")})
    result = {qualify(path, candidate_id) for path in paths}
    comparison = candidate.get("comparison") or {}
    for key, value in comparison.items():
        owner = candidate.get("comparison_baseline") if key == "left" else candidate_id
        for path in _evidence_paths({key: value}):
            result.add(qualify(path, owner or candidate_id))
    return sorted(result)


def _phase_records(record):
    value = record.get("phases", {})
    if isinstance(value, list):
        return {item["phase"]: item for item in value if isinstance(item, dict) and item.get("phase") in PHASES}
    return value if isinstance(value, dict) else {}


def _case_ids(record, phases):
    result = []
    for case in record.get("settings", {}).get("measure_cases", []):
        if isinstance(case, str):
            case_id = case
        elif isinstance(case, dict):
            case_id = case.get("case_id") or f"n{case['size']}_seed{case['seed']}"
        elif isinstance(case, (list, tuple)) and len(case) == 2:
            case_id = f"n{case[0]}_seed{case[1]}"
        else:
            continue
        if case_id not in result:
            result.append(case_id)
    for phase in phases.values():
        for cases in phase.get("measurements", {}).values():
            for case_id in cases:
                if case_id not in result:
                    result.append(case_id)
    return result


def _candidate_order(pair):
    candidate_id, candidate = pair
    if candidate_id == "reference":
        return (0, 0, candidate_id)
    if candidate_id == "identity":
        return (1, 0, candidate_id)
    factor = candidate.get("unroll_factor")
    return (2, factor, candidate_id) if type(factor) is int else (3, 0, candidate_id)


def build_report(record):
    """Build a JSON-serializable diagnostic report without mutating the run."""
    quality = _quality(record.get("settings", {}).get("quality"))
    raw_phases = _phase_records(record)
    cases = _case_ids(record, raw_phases)
    report = {
        "schema_version": "cpucond.diagnostic-report.v1", "run_id": record.get("run_id"),
        "environment_role": record.get("environment_role"),
        "publishable_benchmark": record.get("publishable_benchmark"),
        "manifest_sha256": record.get("manifest_sha256"), "git": deepcopy(record.get("git")),
        "quality": quality, "measure_cases": cases,
        "statistical_method": {
            "quantiles": QUANTILE_METHOD, "ratio": RATIO_DEFINITION,
            "ranking": "descending median paired ratio within each phase and input case; exact ties share competition rank; reference is excluded",
            "warmups": "excluded from every summary and ranking", "significance_testing": False,
            "phases": "summarized independently, never pooled",
        },
        "limitations": [
            "WSL development_smoke; publishable_benchmark=false",
            "Observed fastest candidate is not proven globally optimal; no significance test is performed.",
            "Comparisons concern only the extracted kernel scope, not complete executable equivalence.",
            "Code differences do not prove the intended transformation survived optimization or explain timing differences.",
            "Deterministic C candidates and offline prompts are not an LLM experiment.",
        ],
        "candidates": {}, "phases": {}, "warnings": [],
    }
    for candidate_id, candidate in sorted(record.get("candidates", {}).items(), key=_candidate_order):
        verification = deepcopy(candidate.get("verification"))
        item = {key: deepcopy(candidate.get(key)) for key in (
            "unroll_factor", "origin", "role", "comparison_baseline", "source_sha256", "build", "analysis", "optimization", "comparison", "evidence")}
        item.update(candidate_id=candidate_id, verification=verification,
                    failure_reason=_failure_reason(verification), phases={}, warnings=[])
        item["evidence_files"] = _candidate_evidence_paths(candidate_id, item)
        report["candidates"][candidate_id] = item
    for phase in PHASES:
        phase_record = raw_phases.get(phase, {})
        phase_report = {key: deepcopy(phase_record.get(key)) for key in ("order_seed", "candidate_order_by_case")}
        phase_report.update(phase=phase, rankings={}, warnings=[])
        report["phases"][phase] = phase_report
        if phase not in raw_phases:
            phase_report["warnings"].append(_warning("phase_missing", "The requested phase has no saved record.", phase=phase))
        measurements = phase_record.get("measurements", {})
        for candidate_id, candidate in report["candidates"].items():
            candidate["phases"][phase] = {}
            verified = isinstance(candidate["verification"], dict) and candidate["verification"].get("passed") is True
            build_failed = isinstance(candidate["build"], dict) and candidate["build"].get("passed") is False
            for case_id in cases:
                measurement = measurements.get(candidate_id, {}).get(case_id)
                result = {"status": None, "summary": None, "warnings": [], "observed_rank": None}
                if build_failed:
                    result["status"] = "build_failed"
                    result["warnings"].append(_warning("build_failed", "The candidate build failed; any measurement data is excluded."))
                elif candidate_id == "reference":
                    has_pairs = any(
                        isinstance(candidate_cases, dict) and isinstance(candidate_cases.get(case_id), dict)
                        and any(sample.get("phase") == "measurement" and sample.get("implementation") == "reference"
                                and sample.get("category") == "ok" for sample in candidate_cases[case_id].get("samples", []))
                        for candidate_cases in measurements.values())
                    result["status"] = ("baseline_measured_in_pairs" if has_pairs else "baseline_pair_measurements_missing") if verified else "verification_failed"
                elif not verified:
                    result["status"] = "verification_failed"
                    result["warnings"].append(_warning("verification_failed", candidate["failure_reason"]))
                    if measurement is not None:
                        result["warnings"].append(_warning("unverified_measurement_ignored", "Unverified measurement data was excluded from summaries and rankings."))
                else:
                    summary = summarize_measurement(measurement, quality)
                    if summary["passed"] and summary["summary"]["candidate_implementation"] != candidate_id:
                        summary.update(passed=False, summary=None, warnings=[_warning(
                            "measurement_candidate_mismatch", "Raw samples belong to a different candidate ID; data was excluded.")])
                    result.update(status="measured" if summary["passed"] else "measurement_failed" if measurement is not None else "measurement_missing",
                                  summary=summary["summary"], warnings=summary["warnings"])
                result["warnings"] = [{**warning, "candidate_id": candidate_id, "phase": phase, "case_id": case_id} for warning in result["warnings"]]
                candidate["phases"][phase][case_id] = result
                candidate["warnings"].extend(result["warnings"])
        for case_id in cases:
            ranked = sorted(
                ((candidate_id, candidate["phases"][phase][case_id]["summary"]["median_paired_ratio"])
                 for candidate_id, candidate in report["candidates"].items()
                 if candidate["phases"][phase][case_id]["status"] == "measured"),
                key=lambda row: (-row[1], row[0]))
            phase_report["rankings"][case_id] = []
            previous, rank = None, None
            for position, (candidate_id, ratio) in enumerate(ranked, start=1):
                if previous is None or ratio != previous:
                    rank = position
                report["candidates"][candidate_id]["phases"][phase][case_id]["observed_rank"] = rank
                phase_report["rankings"][case_id].append({"candidate_id": candidate_id, "observed_rank": rank, "median_paired_ratio": ratio})
                previous = ratio
            for left, right in zip(ranked, ranked[1:]):
                fraction = (left[1] - right[1]) / left[1]
                if fraction <= quality["near_tie_fraction"]:
                    phase_report["warnings"].append(_warning(
                        "near_tie", "Adjacent observed ratios are within the predeclared near-tie threshold; this is not evidence of a significant difference or equivalence.",
                        phase=phase, case_id=case_id, candidate_ids=[left[0], right[0]],
                        observed=fraction, threshold=quality["near_tie_fraction"]))
    for case_id in cases:
        orders = {phase: {item["candidate_id"]: item["observed_rank"] for item in report["phases"][phase]["rankings"][case_id]} for phase in PHASES}
        shared = orders["exploration"].keys() & orders["confirmation"].keys()
        for candidate_id in sorted(shared):
            change = abs(orders["exploration"][candidate_id] - orders["confirmation"][candidate_id])
            if change > quality["rank_tolerance"]:
                warning = _warning("rank_unstable", "Observed rank changed across independent phases beyond the predeclared tolerance.",
                                   candidate_id=candidate_id, case_id=case_id, observed=change,
                                   threshold=quality["rank_tolerance"], ranks={phase: orders[phase][candidate_id] for phase in PHASES})
                report["candidates"][candidate_id]["warnings"].append(warning)
        winners = {phase: sorted(candidate_id for candidate_id, rank in ranks.items() if rank == 1) for phase, ranks in orders.items()}
        if all(winners.values()) and winners["exploration"] != winners["confirmation"]:
            report["warnings"].append(_warning("observed_winner_changed", "The observed fastest candidate set changed between phases; no globally optimal candidate is established.",
                                               case_id=case_id, winners=winners))
    for candidate in report["candidates"].values():
        report["warnings"].extend(candidate["warnings"])
    for phase in report["phases"].values():
        report["warnings"].extend(phase["warnings"])
    return report


def _comparison_status(candidate):
    comparison = candidate.get("comparison") or {}
    return comparison.get("status") or comparison.get("category") or "comparison_unavailable"


def _compact(value):
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _optimization_summary(candidate):
    optimization = candidate.get("optimization")
    if not isinstance(optimization, dict):
        return {"status": "unavailable", "reason": "No optimization record was supplied; absence is not evidence of no optimization."}
    result = {key: value for key, value in optimization.items() if key not in ("records", "remarks", "raw", "stdout", "stderr")}
    examples, seen = [], set()
    counts = {}
    for remark in optimization.get("remarks", []):
        key = tuple(remark.get(field) for field in ("kind", "pass_raw", "name_raw", "function_raw"))
        kind = remark.get("kind")
        if key in seen or counts.get(kind, 0) >= 3:
            continue
        seen.add(key)
        counts[kind] = counts.get(kind, 0) + 1
        examples.append({field: remark.get(field) for field in ("kind", "pass_raw", "name_raw", "function_raw", "start_line")})
    if examples:
        result["remark_examples"] = examples
        result["example_selection"] = "first three distinct pass/name/function records per kind; complete records remain in optimization.json and the raw YAML"
    return result


def _csv_rows(report):
    for candidate_id, candidate in report["candidates"].items():
        for phase in PHASES:
            for case_id, measurement in candidate["phases"][phase].items():
                summary = measurement["summary"] or {}
                baseline = summary.get("baseline", {})
                candidate_stats = summary.get("candidate", {})
                warnings = [warning for warning in candidate["warnings"] if warning.get("case_id") == case_id and warning.get("phase", phase) == phase]
                warnings += [warning for warning in report["phases"][phase]["warnings"] if warning.get("case_id") == case_id and candidate_id in warning.get("candidate_ids", [])]
                yield {
                    "candidate_id": candidate_id, "unroll_factor": candidate["unroll_factor"],
                    "origin": candidate["origin"], "role": candidate["role"],
                    "verification_passed": (candidate["verification"] or {}).get("passed"),
                    "failure_reason": candidate["failure_reason"], "comparison_baseline": candidate["comparison_baseline"],
                    "comparison_status": _comparison_status(candidate), "evidence_files": _compact(candidate["evidence_files"]),
                    "optimization_summary": _compact(_optimization_summary(candidate)),
                    "phase": phase, "case_id": case_id, "measurement_status": measurement["status"],
                    "observed_rank": measurement["observed_rank"],
                    "measured_pairs": candidate_stats.get("count"),
                    "baseline_median_ns": baseline.get("median_ns"), "baseline_iqr_ns": baseline.get("iqr_ns"),
                    "candidate_median_ns": candidate_stats.get("median_ns"), "candidate_iqr_ns": candidate_stats.get("iqr_ns"),
                    "median_paired_ratio": summary.get("median_paired_ratio"), "paired_ratio_iqr": summary.get("paired_ratio_iqr"),
                    "warnings": _compact(warnings),
                }


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ") if value is not None else "—"


def _number(value):
    return f"{value:.5g}" if isinstance(value, (int, float)) else "—"


def render_markdown(report):
    lines = [
        "# Controlled transformation diagnostics", "",
        f"Run: `{report['run_id']}`", "",
        "これは gemm_smoke の既知の C 変換を比較する development_smoke です。",
        "`publishable_benchmark=false`。正式な PolyBench、LLM 実験、CPU 特化の有効性の評価ではありません。", "",
        "速度比は同じペアの参照実行時間 / 候補実行時間です。1 より大きければそのペアで候補が速いことを示します。",
        "順位は各条件・各フェーズ内のペア速度比の中央値の降順です。完全同率は同順位とし、後続順位を飛ばします。",
        "参照実装は各ペアで計測されるため、独立した候補順位や架空の単独計測値は付けません。", "",
        "IQR は q75 − q25、分位点はソート済み標本の (N − 1) × p で線形補間します。",
        "ウォームアップは集計から除外します。exploration と confirmation は別の実行を別々に集計します。",
        "観測された最速候補は、真に最適な候補を証明しません。有意差検定は実施していません。", "",
        "事前に固定した品質基準: `" + _compact(report["quality"]) + "`", "",
        "## 候補・正しさ・実行コード", "",
        "| 候補 ID | 展開率 | 生成元 | 検証 | 失敗理由 | 比較基準 | 対象コード比較 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for candidate_id, candidate in report["candidates"].items():
        passed = (candidate["verification"] or {}).get("passed")
        lines.append("| " + " | ".join(_cell(value) for value in (
            candidate_id, candidate["unroll_factor"], candidate["origin"],
            "passed" if passed is True else "failed / missing", candidate["failure_reason"],
            candidate["comparison_baseline"], _comparison_status(candidate))) + " |")
    lines += ["", "比較は抽出した対象カーネルの範囲に限ります。実行ファイル全体の同一性や関数外依存の同一性を証明しません。",
              "コード差だけでは意図した展開が残ったか、性能差の原因かは判断できません。", ""]
    for candidate_id, candidate in report["candidates"].items():
        comparison = candidate["comparison"] or {}
        optimization = _optimization_summary(candidate)
        lines += [f"### {_cell(candidate_id)}", "",
                  "比較範囲: " + _cell(comparison.get("scope")), "",
                  "比較不能・制約の理由: " + _cell(comparison.get("reason") or comparison.get("limitations")), "",
                  "意図した変換の残存: `" + _cell(comparison.get("intended_transformation_status", "unknown")) + "`", "",
                  "最適化レポート: `" + _cell(optimization.get("status", "unavailable")) + "`。種類別件数: `" + _cell(_compact(optimization.get("counts"))) + "`。", ""]
        if optimization.get("reason"):
            lines += ["レポートの制約: " + _cell(optimization["reason"]), ""]
        if optimization.get("remark_examples"):
            lines += ["記録された最適化の例（種類ごとに最初の異なる 3 件まで。全記録は JSON / YAML を参照）:", ""]
            for remark in optimization["remark_examples"]:
                lines.append("- " + " / ".join(_cell(remark.get(field)) for field in ("kind", "pass_raw", "name_raw", "function_raw")) + f"（YAML 行 {remark.get('start_line')}）")
            lines.append("")
        if candidate["evidence_files"]:
            lines += ["証拠ファイル:", ""] + [f"- `{path}`" for path in candidate["evidence_files"]] + [""]
        else:
            lines += ["証拠ファイルのパスは未記録です。比較可能性は report.json の analysis / comparison を確認してください。", ""]
    for phase in PHASES:
        phase_report = report["phases"][phase]
        lines += [f"## {phase}", "", f"候補順の seed: `{phase_report['order_seed']}`", "",
                  "実行順: `" + _cell(_compact(phase_report["candidate_order_by_case"])) + "`", "",
                  "| 候補 | 条件 | 状態 | 観測順位 | 候補中央値 ns | 候補 IQR ns | 参照中央値 ns | 参照 IQR ns | ペア速度比中央値 | 速度比 IQR |",
                  "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for candidate_id, candidate in report["candidates"].items():
            for case_id, measurement in candidate["phases"][phase].items():
                summary = measurement["summary"] or {}
                baseline, candidate_stats = summary.get("baseline", {}), summary.get("candidate", {})
                lines.append("| " + " | ".join(_cell(value) for value in (
                    candidate_id, case_id, measurement["status"], measurement["observed_rank"],
                    _number(candidate_stats.get("median_ns")), _number(candidate_stats.get("iqr_ns")),
                    _number(baseline.get("median_ns")), _number(baseline.get("iqr_ns")),
                    _number(summary.get("median_paired_ratio")), _number(summary.get("paired_ratio_iqr")))) + " |")
        lines.append("")
    lines += ["## 品質警告", ""]
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append("- `" + _cell(warning["code"]) + "`: " + _cell(_compact({key: value for key, value in warning.items() if key != "code"})))
    else:
        lines.append("固定した品質基準に該当する警告はありません。このことは性能差の統計的有意性を示しません。")
    lines += ["", "## 解釈上の制限", "",
              "- 正しさは指定した有限 float64 入力に対する全要素ビット比較であり、形式的な同値性証明ではありません。",
              "- 最適化レポートの欠損を、最適化が行われなかった証拠とは扱いません。",
              "- 同一コードや同等に見える性能も正常な結果です。高速化やコード差は合格条件にしていません。",
              "- オフラインの候補選択プロンプトは診断用であり、将来の自由な C コード最適化を置き換えません。", ""]
    return "\n".join(lines)


def write_reports(directory, record):
    """Write report.json/report.csv/report.md and return their relative paths."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    report = build_report(record)
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    rows = list(_csv_rows(report))
    with (directory / "report.csv").open("w", encoding="utf-8", newline="") as stream:
        fieldnames = list(rows[0]) if rows else ["candidate_id", "phase", "case_id", "measurement_status"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (directory / "report.md").write_text(render_markdown(report), encoding="utf-8")
    return {"json": "report.json", "csv": "report.csv", "markdown": "report.md"}
