"""Synthetic semantic-audit tests: no compilation, candidate execution or timing."""

from copy import deepcopy
from dataclasses import asdict
import json
import hashlib
from pathlib import Path
import random

import pytest

from cpucond.diagnostic_audit import (
    CANDIDATE_IDS, PHASES, _Audit, _canonical_warnings, _cost_totals,
    _planned_samples, audit_semantics,
)
from cpucond.diagnostic_config import DiagnosticConfig
from cpucond.diagnostic_prompts import write_diagnostic_prompts
from cpucond.diagnostic_reporting import summarize_measurement
from cpucond.models import ExecutionContract
from cpucond.transformations import make_candidates


def test_warning_order_canonicalization_preserves_observed_rank_and_pair_order():
    first = {"warnings": [{"code": "b"}, {"code": "a"}], "rankings": ["x", "y"], "paired_ratios": [1, 2]}
    second = deepcopy(first)
    second["warnings"].reverse()
    assert _canonical_warnings(first) == _canonical_warnings(second)
    second["rankings"].reverse()
    assert _canonical_warnings(first) != _canonical_warnings(second)


def test_costs_count_rejected_verification_separately_from_process_failure():
    common = {"stage": "verification", "process_attempted": True, "category": "ok", "wall_seconds": 0.2}
    events = [{**common, "verification_passed": False}, {**common, "verification_passed": True},
              {**common, "stage": "confirmation", "sample_phase": "warmup", "category": "timeout"},
              {**common, "stage": "confirmation", "sample_phase": "measurement", "process_attempted": False,
               "category": "artifact_changed", "wall_seconds": 0.0}]
    stages, count = _cost_totals(events)
    assert count == 3
    assert stages["verification"] == {"attempts": 2, "executions": 2, "process_failures": 0,
                                       "verification_failures": 1, "wall_seconds": 0.4}
    assert stages["confirmation/warmup"]["process_failures"] == 1
    assert stages["confirmation/measurement"]["executions"] == 0


def test_plan_keeps_warmups_separate_and_alternates_every_pair():
    samples = list(_planned_samples("identity", 1, 2))
    assert len(samples) == 6
    assert [x["phase"] for x in samples] == ["warmup"] * 2 + ["measurement"] * 4
    assert [x["implementation"] for x in samples] == ["reference", "identity", "reference", "identity", "identity", "reference"]


@pytest.fixture
def synthetic_measurements(tmp_path):
    config = DiagnosticConfig(measure_cases=((18, 17),), warmups=1, repeats=2, size_rationale="Synthetic audit fixture")
    record = {"measurement_freeze_sha256": "f" * 64, "candidates": {}, "phases": {}}
    for index, name in enumerate(CANDIDATE_IDS):
        record["candidates"][name] = {"program_sha256": str(index) * 64,
                                      "verification": {"passed": name != "deliberately_wrong", "category": "value_mismatch" if name == "deliberately_wrong" else "ok"}}
    audit = _Audit(tmp_path, record)
    audit.config, audit.events = config, []
    audit.runtime_dirs = {name: f"/recorded/candidates/{name}" for name in CANDIDATE_IDS}
    for phase_index, phase in enumerate(PHASES):
        seed = getattr(config, phase + "_order_seed")
        order = list(CANDIDATE_IDS[1:])
        random.Random(seed).shuffle(order)
        cid = "n18_seed17"
        row = {"phase": phase, "order_seed": seed, "measurement_freeze_sha256": "f" * 64,
               "started_utc": f"2026-09-09T00:0{phase_index * 2}:00+00:00",
               "completed_utc": f"2026-09-09T00:0{phase_index * 2 + 1}:00+00:00",
               "candidate_order_by_case": [{"case_id": cid, "candidate_ids": order}], "measurements": {}, "skipped": []}
        for position, name in enumerate(order):
            if name == "deliberately_wrong":
                row["skipped"].append({"candidate_id": name, "case_id": cid, "reason": "value_mismatch"})
                continue
            samples = []
            for planned in _planned_samples(name, config.warmups, config.repeats):
                implementation = planned["implementation"]
                args = [str(Path(audit.runtime_dirs[implementation]) / "program"), "measure", "18", "17"]
                program = record["candidates"][implementation]["program_sha256"]
                event_id = len(audit.events)
                value = {"elapsed_ns": 100000 + event_id, "checksum_bits": "a" * 16}
                process = {"args": args, "category": "ok", "returncode": 0, "stdout": json.dumps(value), "stderr": "", "wall_seconds": 0.001}
                samples.append({**planned, "size": 18, "seed": 17, "pair_candidate": name,
                                "candidate_order_position": position, "experiment_phase": phase,
                                "program_sha256": program, "ledger_event_id": event_id, "category": "ok",
                                "process": process, **value})
                audit.events.append({"event_id": event_id, "stage": phase, "candidate_id": name, "args": args,
                                     "cwd": None, "category": "ok", "returncode": 0, "wall_seconds": 0.001,
                                     "program_sha256": program, "expected_program_sha256": program,
                                     "process_attempted": True, "sample_phase": planned["phase"], "case_id": cid})
            measured = summarize_measurement({"passed": True, "samples": samples}, asdict(config.quality))
            measured.update(phase=phase, case_id=cid, candidate_id=name, measurement_freeze_sha256="f" * 64)
            row["measurements"][name] = {cid: measured}
        record["phases"][phase] = row
    return audit


def test_complete_synthetic_phases_have_unique_reproducible_event_sequences(synthetic_measurements):
    audit = synthetic_measurements
    audit.measurements()
    assert audit.errors == []
    assert audit.cursor == len(audit.events) == 72


@pytest.mark.parametrize("mutation", ["missing_candidate", "missing_case", "missing_warmup", "reused_event", "phase_changed",
                                       "shuffle_changed", "raw_output_changed", "summary_changed", "wrong_measured"])
def test_semantic_mutations_fail_even_without_file_hash_checks(synthetic_measurements, mutation):
    audit = synthetic_measurements
    phase = audit.record["phases"]["exploration"]
    name = next(iter(phase["measurements"]))
    measured = phase["measurements"][name]["n18_seed17"]
    if mutation == "missing_candidate":
        del phase["measurements"][name]
    elif mutation == "missing_case":
        del phase["measurements"][name]["n18_seed17"]
    elif mutation == "missing_warmup":
        measured["samples"].pop(0)
    elif mutation == "reused_event":
        measured["samples"][1]["ledger_event_id"] = measured["samples"][0]["ledger_event_id"]
    elif mutation == "phase_changed":
        measured["samples"][0]["experiment_phase"] = "confirmation"
    elif mutation == "shuffle_changed":
        phase["candidate_order_by_case"][0]["candidate_ids"].reverse()
    elif mutation == "raw_output_changed":
        measured["samples"][0]["elapsed_ns"] += 10
    elif mutation == "summary_changed":
        measured["summary"]["median_paired_ratio"] += 1
    else:
        phase["measurements"]["deliberately_wrong"] = deepcopy(phase["measurements"][name])
    try:
        audit.measurements()
    except (KeyError, IndexError):
        return  # audit_semantics converts missing required data into explicit errors.
    assert audit.errors


def test_empty_run_is_not_proven_complete(tmp_path):
    assert audit_semantics(tmp_path, {})


def test_prompt_audit_reconstructs_allowlisted_sources_and_cpu_only_difference(tmp_path):
    prompts = write_diagnostic_prompts(tmp_path / "prompts", make_candidates(), "Explicit CPU fixture", ExecutionContract())
    audit = _Audit(tmp_path, {"prompts": prompts})
    audit.prompts()
    assert audit.errors == []


def test_prompt_measurements_cannot_be_hidden_by_updated_file_hash(tmp_path):
    prompts = write_diagnostic_prompts(tmp_path / "prompts", make_candidates(), "Explicit CPU fixture", ExecutionContract())
    path = tmp_path / "prompts/common_payload.json"
    payload = json.loads(path.read_text())
    payload["median_ns"] = 123
    payload["correct_option"] = "option_01"
    changed = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    path.write_text(changed)
    prompts["common_payload"]["sha256"] = hashlib.sha256(changed.encode()).hexdigest()
    audit = _Audit(tmp_path, {"prompts": prompts})
    audit.prompts()
    assert any("allowlist" in error for error in audit.errors)
    assert any("hash/option" in error for error in audit.errors)
