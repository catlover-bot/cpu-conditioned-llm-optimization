"""Recompute selected CPU aggregates from public files; stdlib only, no experiments."""
from pathlib import Path
import csv
import json
import math

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def truth(value):
    return value is True or isinstance(value, str) and value.lower() in {"true", "1"}


def geomean(values):
    values = list(values)
    if not values:
        return None
    if any(not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError("nonpositive/nonfinite selected speedup")
    return math.exp(sum(math.log(value) for value in values) / len(values))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    with (ROOT / "qwen14b-a40-inference/analysis/outcomes.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 900 and len({row["id"] for row in rows}) == 900, "Qwen14B IDs/count")
    valid = [row for row in rows if truth(row["measurement_valid"])]
    speeds = [float(row["speedup"]) for row in valid]
    original = load("qwen14b-a40-inference/summary.json")
    require(len(valid) == original["performance"]["measurement_valid"], "Qwen14B valid count")
    gm = geomean(speeds)
    require(math.isclose(gm, original["performance"]["geomean_speedup_valid"], rel_tol=1e-12),
            "Qwen14B aggregate mismatch")
    backend = {}
    for name in sorted({row["generation_backend"] for row in rows}):
        subset = [row for row in rows if row["generation_backend"] == name]
        selected = [row for row in subset if truth(row["measurement_valid"])]
        backend[name] = {"requests": len(subset), "measurement_valid": len(selected),
                         "geomean_speedup_valid": geomean(float(row["speedup"]) for row in selected)}
        recorded = original["by_generation_backend"][name]
        require(len(subset) == recorded["requests_total"] and len(selected) == recorded["measurement_valid"],
                "backend denominator mismatch")
        require(math.isclose(backend[name]["geomean_speedup_valid"],
                             recorded["geomean_speedup_valid"], rel_tol=1e-12),
                "backend speedup mismatch")
    validation = [json.loads(path.read_text()) for path in sorted((ROOT / "claude540/validation").glob("*.json"))]
    measurements = [json.loads(path.read_text()) for path in sorted((ROOT / "claude540/measurement").glob("*.json"))]
    require(len(validation) == 540 and len({row["id"] for row in validation}) == 540, "Claude validation IDs/count")
    passed_ids = {row["id"] for row in validation if row["passed"] is True}
    require(len(passed_ids) == 395, "Claude correctness eligibility")
    require(len(measurements) == 395 and {row["id"] for row in measurements} == passed_ids,
            "Claude measurement denominator mismatch")
    measured = [row for row in measurements if row["measurement_valid"] is True]
    require(len(measured) == 388, "Claude valid count")
    qwen = [json.loads(path.read_text()) for path in sorted((ROOT / "qwen32b-z1-h1/outcomes").glob("*.json"))]
    require(len(qwen) == 180 and len({row["id"] for row in qwen}) == 180, "Qwen Z1/H1 IDs/count")
    qwen_passed = sum(row["stage16c_correctness_pass"] is True for row in qwen)
    qwen_valid = [row for row in qwen if row["measurement_valid"] is True]
    require(qwen_passed == 144 and len(qwen_valid) == 136, "Qwen Z1/H1 terminal counts")
    ledger = [json.loads(line) for line in (ROOT / "qwen32b-526-revalidation/eligibility.jsonl").read_text().splitlines()]
    require(len(ledger) == 526 and len({row["id"] for row in ledger}) == 526, "Qwen526 IDs/count")
    admitted = sum(row["eligible_under_recorded_checks"] is True for row in ledger)
    require(admitted == 351, "Qwen526 recorded eligibility")
    ledger_by_id = {row["id"]: row for row in ledger}
    reused_p1 = [row for row in qwen if row["id"] in ledger_by_id]
    h1 = [row for row in qwen if row["condition"] == "H1"]
    require(len(reused_p1) == 90 and len(h1) == 90,
            "Qwen paired reevaluation must include 90 reused P1 slots and 90 H1 slots")
    require(all(row["condition"] == "P1" and row["form"] == "C" and
                row["source_sha256"] == ledger_by_id[row["id"]]["source_sha256"]
                for row in reused_p1), "Qwen reused P1 source identity differs")
    require(not any(row["id"] in ledger_by_id for row in h1),
            "H1 evaluation IDs overlap the earlier 526-slot ledger")
    return {
        "scope": "offline public aggregate checks; no model, compiler, GPU, API or network use",
        "formal_equivalence_proven": False,
        "qwen14b_cpu_candidates": {
            "requests": len(rows), "saved": sum(row["generation_status"] == "saved" for row in rows),
            "measurement_valid": len(valid), "geomean_speedup_valid": gm,
            "speedup_gt_1_02": sum(value > 1.02 for value in speeds), "generation_backends": backend},
        "claude540": {"requests": len(validation), "correctness_eligible": len(passed_ids),
                      "measurement_valid": len(measured), "measurement_invalid": len(measurements) - len(measured),
                      "geomean_speedup_conditional_valid": geomean(float(row["speedup"]) for row in measured)},
        "qwen32b_z1_h1_reevaluation": {
            "evaluation_slots": len(qwen), "reused_prior_P1_C_slots": len(reused_p1),
            "H1_comparison_slots": len(h1), "new_generation_calls_for_this_export": 0,
            "correctness_eligible": qwen_passed, "measurement_valid": len(qwen_valid)},
        "qwen32b526_recorded_revalidation": {"requests": len(ledger), "eligible": admitted,
                                            "new_generation_calls": 0, "new_performance_measurements": 0},
        "data_limits": ["Raw timings/native API outputs are locally retained, not included.",
                        "Historical hash fields identify originals, not sanitized copies.",
                        "Reevaluation exports are not additional generation requests."]}


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
