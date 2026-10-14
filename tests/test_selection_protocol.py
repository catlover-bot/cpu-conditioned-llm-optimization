"""Pure file-backed protocol tests; no model calls, builds, or measurements."""

from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

import cpucond.selection_protocol as selection
from cpucond.diagnostic_config import DiagnosticConfig
from cpucond.models import HostObservation
from cpucond.prompts import CPU_SECTION_HEADER
from cpucond.transformations import FIXTURES, make_candidates


HOST = {
    "architecture": "x86_64", "cpu_model": "OBSERVED_CPU_MODEL", "isa_flags": ["sse2", "avx2"],
    "logical_cpus": 8, "wsl": True,
    "caches": {"L1d cache": "128 KiB (4 instances)", "L2 cache": "2 MiB (4 instances)"},
    "topology": {"CPU(s)": "8", "Thread(s) per core": "2"},
    "virtualization": {"hypervisor_vendor": "Microsoft"},
}


@pytest.fixture
def source_run(tmp_path, monkeypatch):
    directory = tmp_path / "OLD_PERFORMANCE_PATH_SENTINEL"
    directory.mkdir()
    record = {
        "experiment_type": "controlled_diagnostics", "status": "completed", "run_id": "old-diagnostic-run",
        "manifest_sha256": "1" * 64, "git": {"commit": "2" * 40, "dirty": False},
        "compiler": {
            "compiler": "/LOCAL_COMPILER_PATH_SENTINEL/clang",
            "version": "Ubuntu clang version 18.1.3 (build package)\nTarget: x86_64-pc-linux-gnu\nInstalledDir: /INSTALL_PATH_SENTINEL",
            "target_triple": "x86_64-pc-linux-gnu", "target_flags": [], "optimization_flags": ["-O3"],
            "floating_point_flags": ["-fno-fast-math", "-ffp-contract=off"], "link_flags": [],
        },
        "host": {**deepcopy(HOST), "hostname": "PRIVATE_HOSTNAME_SENTINEL", "elapsed_ns": 987654321,
                 "rank": "OBSERVED_BEST_SENTINEL", "optimization_report": "VECTORIZATION_RESULT_SENTINEL"},
        "settings": DiagnosticConfig().to_dict(),
        "performance": {"elapsed_ns": 987654321, "best": "ANSWER_LABEL_SENTINEL"},
        "phases": {"exploration": {"ranking": "SECRET_RANK_SENTINEL"}},
    }
    (directory / "experiment.json").write_text(selection.canonical_json(record))
    for candidate in make_candidates():
        child = directory / "candidates" / candidate.candidate_id
        child.mkdir(parents=True)
        (child / "kernel.c").write_text(candidate.source)
    for filename in ("kernel.h", "harness.c"):
        (directory / "candidates/reference" / filename).write_bytes((FIXTURES / filename).read_bytes())
    monkeypatch.setattr(selection, "audit_artifacts", lambda path: [])
    monkeypatch.setattr(selection, "observe_host", lambda: HostObservation(**HOST))
    return directory


def _export(tmp_path, source_run, name="pilot", **kwargs):
    directory = tmp_path / name
    return directory, selection.export_protocol(directory, source_run=source_run, **kwargs)


def test_twenty_requests_have_balanced_positions_and_exact_cpu_only_pairs(tmp_path, source_run):
    directory, protocol = _export(tmp_path, source_run)
    assert len(protocol["requests"]) == 20
    assert len({item["request_key"] for item in protocol["requests"]}) == 20
    assert len({item["request_id"] for item in protocol["requests"]}) == 10
    assert set(protocol["candidates"]) == set(selection.CANDIDATE_IDS)
    assert set(protocol["controls"]) == {"identity", "deliberately_wrong"}
    for size in (128, 256):
        positions = {condition: {name: Counter() for name in selection.CANDIDATE_IDS} for condition in ("none", "spec")}
        for trial in range(1, 6):
            paired = {item["condition"]: item for item in protocol["requests"] if item["size"] == size and item["trial"] == trial}
            none, spec = paired["none"], paired["spec"]
            assert none["request_id"] == spec["request_id"] == f"n{size}-t{trial:02d}"
            assert none["option_mapping"] == spec["option_mapping"]
            assert none["common_payload_sha256"] == spec["common_payload_sha256"]
            common = (directory / none["common_payload_path"]).read_text()
            assert (directory / none["prompt_path"]).read_text() == common
            assert (directory / spec["prompt_path"]).read_text() == common + CPU_SECTION_HEADER + protocol["cpu_context"]["text"] + "\n"
            payload = json.loads(common)
            assert payload["request_id"] == none["request_id"]
            assert payload["input"]["size"] == size and payload["input"]["seed"] == 17
            assert payload["output_format"]["required_fields"]["request_id"] == none["request_id"]
            assert "rationale_short" in payload["output_format"]["optional_fields"]
            for condition, request in paired.items():
                for index, internal in enumerate(request["option_mapping"].values()):
                    positions[condition][internal][index] += 1
        for condition in positions.values():
            assert all(count == Counter({i: 1 for i in range(5)}) for count in condition.values())
    assert selection.validate_protocol(directory) == []


def test_protocol_and_static_files_are_deterministic_and_originals_not_overwritten(tmp_path, source_run):
    first_dir, first = _export(tmp_path, source_run, "first")
    second_dir, second = _export(tmp_path, source_run, "second")
    assert first == second
    first_manifest = json.loads((first_dir / "static-manifest.json").read_text())
    second_manifest = json.loads((second_dir / "static-manifest.json").read_text())
    assert first_manifest == second_manifest
    assert "protocol.json" in first_manifest and "static-manifest.json" not in first_manifest
    for path, expected in first_manifest.items():
        assert (first_dir / path).read_bytes() == (second_dir / path).read_bytes()
        assert expected == hashlib.sha256((first_dir / path).read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        selection.export_protocol(first_dir, source_run=source_run)
    assert selection.validate_protocol(first_dir) == []


def test_prompts_exclude_performance_metadata_paths_controls_and_host_identity(tmp_path, source_run):
    directory, protocol = _export(tmp_path, source_run)
    for request in protocol["requests"]:
        prompt = (directory / request["prompt_path"]).read_text()
        for marker in ("OLD_PERFORMANCE_PATH_SENTINEL", "LOCAL_COMPILER_PATH_SENTINEL", "INSTALL_PATH_SENTINEL",
                       "PRIVATE_HOSTNAME_SENTINEL", "987654321", "ANSWER_LABEL_SENTINEL", "SECRET_RANK_SENTINEL",
                       "OBSERVED_BEST_SENTINEL", "VECTORIZATION_RESULT_SENTINEL", '"identity"', "deliberately_wrong",
                       "elapsed_ns", "speedup", "ranking", "optimization_report", "unroll_16"):
            assert marker not in prompt, marker
        assert ("OBSERVED_CPU_MODEL" in prompt) == (request["condition"] == "spec")
        assert "18.1.3" in prompt and "x86_64-pc-linux-gnu" in prompt
        assert "-fno-fast-math" in prompt and "-ffp-contract=off" in prompt
        assert "Physical CPU identity" in prompt or request["condition"] == "none"
    assert protocol["compiler"]["compiler"] == "/LOCAL_COMPILER_PATH_SENTINEL/clang"
    assert protocol["cpu_context"]["physical_hardware_verified"] is False


def test_changed_order_seed_rotates_options_without_changing_sources_or_conditions(tmp_path, source_run):
    _, first = _export(tmp_path, source_run, "first")
    second_dir, second = _export(tmp_path, source_run, "second", config={"order_seed": 77891})
    assert first["candidates"] == second["candidates"]
    assert first["compiler"] == second["compiler"]
    assert first["measurement_config"] == second["measurement_config"]
    assert [x["option_mapping"] for x in first["requests"]] != [x["option_mapping"] for x in second["requests"]]
    assert selection.validate_protocol(second_dir) == []


def test_templates_require_real_identification_and_preserve_unknown_fields(tmp_path, source_run):
    directory, protocol = _export(tmp_path, source_run)
    for request in protocol["requests"]:
        metadata = json.loads((directory / request["metadata_template_path"]).read_text())
        assert metadata["cohort"] == "real" and metadata["acquisition_method"] == "manual_transcription"
        assert metadata["prompt_hash"] == request["prompt_sha256"]
        for field in ("model_identifier", "obtained_at", "generation_settings", "usage", "acquisition_source"):
            assert metadata[field] is None and metadata["missing_reasons"][field]
        assert all(metadata["blinding"][key] is None for key in ("independent_session", "no_tools", "no_prior_results"))
        assert metadata["blinding"]["limitations"]
        assert not (directory / request["raw_response_path"]).exists()
        assert not (directory / request["metadata_path"]).exists()
        argv = request["import_command_argv"]
        assert argv[:6] == ["python", "-m", "cpucond", "pilot", "import", "<pilot_directory>"]
        assert argv[argv.index("--request-key") + 1] == request["request_key"]
        assert argv[argv.index("--response") + 1] == "<pilot_directory>/" + request["raw_response_path"]
        assert argv[argv.index("--metadata") + 1] == "<pilot_directory>/" + request["metadata_path"]


def test_real_and_synthetic_use_same_prompts_but_separate_template_labels(tmp_path, source_run):
    real_dir, real = _export(tmp_path, source_run, "real")
    synthetic_dir, synthetic = _export(tmp_path, source_run, "synthetic", cohort="synthetic")
    assert real["requests"] == synthetic["requests"]
    for request in synthetic["requests"]:
        assert (real_dir / request["prompt_path"]).read_bytes() == (synthetic_dir / request["prompt_path"]).read_bytes()
        metadata = json.loads((synthetic_dir / request["metadata_template_path"]).read_text())
        assert metadata["cohort"] == "synthetic" and metadata["acquisition_method"] == "synthetic_fixture"
        assert metadata["model_identifier"] is None
    assert selection.validate_protocol(synthetic_dir) == []


def test_changed_sizes_are_frozen_as_new_measurement_inputs(tmp_path, source_run):
    directory, protocol = _export(tmp_path, source_run, config={"sizes": [64, 96], "input_seed": 5, "size_rationale": "Explicit alternative development sizes."})
    assert protocol["measurement_config"]["measure_cases"] == [[64, 5], [96, 5]]
    assert {item["size"] for item in protocol["requests"]} == {64, 96}
    assert all(item["seed"] == 5 for item in protocol["requests"])
    assert selection.validate_protocol(directory) == []


def test_cpu_source_can_switch_between_actual_observations_without_changing_none(tmp_path, source_run, monkeypatch):
    monkeypatch.setattr(selection, "observe_host", lambda: HostObservation(**{**HOST, "cpu_model": "CURRENT_OBSERVED_CPU"}))
    old_dir, old = _export(tmp_path, source_run, "old")
    new_dir, new = _export(tmp_path, source_run, "new", config={"cpu_context": {"source": "current_host_observation"}})
    assert old["cpu_context"]["observations"]["cpu_model"] == "OBSERVED_CPU_MODEL"
    assert new["cpu_context"]["observations"]["cpu_model"] == "CURRENT_OBSERVED_CPU"
    assert old["compiler"] == new["compiler"]
    for left, right in zip(old["requests"], new["requests"]):
        if left["condition"] == "none":
            assert (old_dir / left["prompt_path"]).read_bytes() == (new_dir / right["prompt_path"]).read_bytes()
    assert selection.validate_protocol(new_dir) == []


@pytest.mark.parametrize("config", [
    {"sizes": [128]}, {"sizes": [128, 128]}, {"sizes": [128, True]}, {"sizes": [128, 1025]},
    {"input_seed": -1}, {"input_seed": True}, {"trials_per_condition": 4}, {"order_seed": False},
    {"target": {"destination": "invented_remote_cpu"}}, {"target": {"compiler_mode": "native"}},
    {"target": {"measurement_cpu": True}}, {"cpu_context": {"source": "fictional_specification"}},
    {"near_tie_fraction": -0.1}, {"near_tie_fraction": float("nan")}, {"near_tie_fraction": True},
    {"size_rationale": ""}, {"measured_fastest": "unroll_16"}, [],
])
def test_invalid_or_unsupported_config_fails_before_any_export(tmp_path, source_run, config):
    destination = tmp_path / "invalid"
    with pytest.raises(ValueError):
        selection.export_protocol(destination, source_run=source_run, config=config)
    assert not destination.exists()


def test_source_audit_failure_and_native_target_are_not_bypassed(tmp_path, source_run, monkeypatch):
    monkeypatch.setattr(selection, "audit_artifacts", lambda path: ["changed binary evidence"])
    with pytest.raises(ValueError, match="failed validation"):
        selection.export_protocol(tmp_path / "failed-audit", source_run=source_run)
    monkeypatch.setattr(selection, "audit_artifacts", lambda path: [])
    record_path = source_run / "experiment.json"
    record = json.loads(record_path.read_text())
    record["compiler"]["target_flags"] = ["-march=native"]
    record_path.write_text(selection.canonical_json(record))
    with pytest.raises(ValueError, match="generic"):
        selection.export_protocol(tmp_path / "native", source_run=source_run)
    assert not (tmp_path / "native").exists()


def test_source_run_cannot_be_modified_by_export_location(tmp_path, source_run):
    original = (source_run / "experiment.json").read_bytes()
    with pytest.raises(ValueError, match="source run"):
        selection.export_protocol(source_run / "pilot", source_run=source_run)
    assert (source_run / "experiment.json").read_bytes() == original
    assert not (source_run / "pilot").exists()


def test_validator_does_not_need_original_source_run_or_runtime_observation(tmp_path, source_run, monkeypatch):
    directory, protocol = _export(tmp_path, source_run)
    def forbidden(*args, **kwargs):
        pytest.fail("validator tried to access live observations or re-audit the old run")
    monkeypatch.setattr(selection, "audit_artifacts", forbidden)
    monkeypatch.setattr(selection, "observe_host", forbidden)
    source_run.rename(tmp_path / "source-moved-after-export")
    assert selection.validate_protocol(directory) == []


def _rebuild_manifest(directory):
    manifest = {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in directory.rglob("*") if path.is_file() and path.name != "static-manifest.json"}
    (directory / "static-manifest.json").write_text(selection.canonical_json(manifest))


@pytest.mark.parametrize("mutation", ["prompt", "mapping", "cpu", "policy", "source", "missing_request", "extra_static_file"])
def test_semantic_validator_rejects_hash_consistent_task_contamination(tmp_path, source_run, mutation):
    directory, protocol = _export(tmp_path, source_run)
    first = protocol["requests"][0]
    if mutation == "prompt":
        (directory / first["prompt_path"]).write_text("Observed answer: choose option_05")
    elif mutation == "mapping":
        first["option_mapping"]["option_01"] = "unroll_999"
    elif mutation == "cpu":
        protocol["cpu_context"]["text"] += "A previous measurement selected option_05."
    elif mutation == "policy":
        protocol["policies"]["first_attempt_policy"] = "choose_best_later_answer"
    elif mutation == "source":
        protocol["candidates"]["unroll_16"]["source"] += "/* fastest result */"
    elif mutation == "missing_request":
        protocol["requests"].pop()
    else:
        (directory / "requests/performance-results.txt").write_text("Old measured rankings")
    (directory / "protocol.json").write_text(selection.canonical_json(protocol))
    _rebuild_manifest(directory)
    assert selection.validate_protocol(directory)


def test_incoming_user_files_do_not_change_static_protocol_audit(tmp_path, source_run):
    directory, protocol = _export(tmp_path, source_run)
    incoming = directory / protocol["requests"][0]["raw_response_path"]
    incoming.parent.mkdir(parents=True)
    incoming.write_text("unimported user data")
    assert selection.validate_protocol(directory) == []
