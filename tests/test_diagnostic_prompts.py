"""Allowlisted offline diagnostic prompts cannot consume experiment results."""

from dataclasses import asdict, replace
import hashlib
import inspect
import json

import pytest

from cpucond import host
from cpucond.diagnostic_prompts import SELECTION_OUTPUT, write_diagnostic_prompts
from cpucond.models import CompilerTarget, ExecutionContract, ExperimentRecord, HostObservation
from cpucond.prompts import CPU_SECTION_HEADER
from cpucond.transformations import FACTORS, make_candidates


CPU_TEXT = "Explicit CPU description: MODEL_SENTINEL; cache: CACHE_SENTINEL."


def test_prompts_share_payload_and_only_spec_discloses_supplied_cpu(tmp_path):
    contract = ExecutionContract()
    candidates = make_candidates()
    metadata = write_diagnostic_prompts(tmp_path, candidates, CPU_TEXT, contract)
    common = (tmp_path / "common_payload.json").read_text()
    none = (tmp_path / "none.txt").read_text()
    spec = (tmp_path / "spec.txt").read_text()
    assert none == common
    assert spec == common + CPU_SECTION_HEADER + CPU_TEXT + "\n"
    assert CPU_TEXT not in none
    assert (tmp_path / "cpu_spec.txt").read_text() == CPU_TEXT
    payload = json.loads(common)
    assert set(payload) == {"task", "reference_source", "contract", "options", "output_format"}
    assert payload["reference_source"] == candidates[0].source
    assert payload["contract"] == {"abi": contract.abi, "correctness": contract.correctness}
    assert payload["output_format"] == SELECTION_OUTPUT
    assert contract.output_format not in common
    assert metadata["llm_calls"] == 0
    assert metadata["purpose"] == "offline_diagnostic_selection_preparation"
    assert len(payload["options"]) == len(FACTORS)
    assert [item["option_id"] for item in payload["options"]] == [f"option_{i:02d}" for i in range(1, 6)]
    assert metadata["option_mapping"] == {f"option_{i:02d}": f"unroll_{factor}" for i, factor in enumerate(FACTORS, 1)}
    for item in payload["options"]:
        assert set(item) == {"option_id", "source"}
        candidate_id = metadata["option_mapping"][item["option_id"]]
        assert item["source"] == next(candidate.source for candidate in candidates if candidate.candidate_id == candidate_id)
    for key in ("common_payload", "cpu_spec", "none", "spec"):
        artifact = metadata[key]
        assert artifact["sha256"] == hashlib.sha256((tmp_path / artifact["path"]).read_bytes()).hexdigest()
    assert metadata["none"]["common_payload_sha256"] == metadata["spec"]["common_payload_sha256"]
    assert metadata["none"]["cpu_spec_sha256"] is None
    assert metadata["spec"]["cpu_spec_sha256"] == metadata["cpu_spec"]["sha256"]


def test_metadata_and_wrong_control_never_leak_into_option_text(tmp_path):
    candidates = [replace(item, role="ANSWER_LABEL_SENTINEL", comparison_baseline="rank=1 time_ns=123456789")
                  for item in make_candidates()]
    candidates[-1] = replace(candidates[-1], source="WRONG_CONTROL_SOURCE_SENTINEL")
    contract = replace(ExecutionContract(), output_format="RESULT_SENTINEL best=unroll_16 speedup=900")
    write_diagnostic_prompts(tmp_path, candidates, CPU_TEXT, contract)
    rendered = (tmp_path / "spec.txt").read_text()
    for forbidden in ("ANSWER_LABEL_SENTINEL", "rank=1", "123456789", "WRONG_CONTROL_SOURCE_SENTINEL",
                      "RESULT_SENTINEL", "unroll_16", "deliberately_wrong", "negative_control",
                      "handwritten_fixture", "comparison_baseline", "elapsed_ns", "speedup"):
        assert forbidden not in rendered


def test_generation_ignores_candidate_list_order(tmp_path):
    candidates = make_candidates()
    first = write_diagnostic_prompts(tmp_path / "first", candidates, CPU_TEXT, ExecutionContract())
    second = write_diagnostic_prompts(tmp_path / "second", list(reversed(candidates)), CPU_TEXT, ExecutionContract())
    assert first == second
    for filename in ("common_payload.json", "none.txt", "spec.txt", "cpu_spec.txt"):
        assert (tmp_path / "first" / filename).read_bytes() == (tmp_path / "second" / filename).read_bytes()


def test_prompt_cpu_context_cannot_change_compiler_or_read_observations(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("diagnostic prompt attempted to inspect the local host or compiler")
    monkeypatch.setattr(host, "observe_host", forbidden)
    monkeypatch.setattr(host, "discover_compiler", forbidden)
    monkeypatch.setenv("HOSTNAME", "HOSTNAME_SENTINEL")
    compiler = CompilerTarget("/BUILD_PATH_SENTINEL/clang", "VERSION_SENTINEL", target_flags=("-march=TARGET_SENTINEL",))
    before = asdict(compiler)
    first = write_diagnostic_prompts(tmp_path / "first", make_candidates(), CPU_TEXT, ExecutionContract())
    second = write_diagnostic_prompts(tmp_path / "second", make_candidates(), "Another explicitly supplied CPU", ExecutionContract())
    assert first["none"] == second["none"]
    assert first["spec"]["sha256"] != second["spec"]["sha256"]
    assert before == asdict(compiler)
    text = (tmp_path / "first" / "spec.txt").read_text()
    for sentinel in ("HOSTNAME_SENTINEL", "BUILD_PATH_SENTINEL", "VERSION_SENTINEL", "TARGET_SENTINEL"):
        assert sentinel not in text
    assert list(inspect.signature(write_diagnostic_prompts).parameters) == ["directory", "candidates", "context_spec", "contract"]


@pytest.mark.parametrize("candidates", [
    ExperimentRecord(candidates={"elapsed_ns": 1234}),
    [{"source": "C source", "rank": 1}],
    [HostObservation(cpu_model="HOST_SENTINEL")],
])
def test_measured_records_and_untyped_payloads_are_rejected_before_writes(tmp_path, candidates):
    with pytest.raises(TypeError, match="Candidate"):
        write_diagnostic_prompts(tmp_path, candidates, CPU_TEXT, ExecutionContract())
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("spec", ["", " ", None, 123])
def test_empty_or_invalid_cpu_spec_is_rejected_before_writes(tmp_path, spec):
    with pytest.raises(ValueError):
        write_diagnostic_prompts(tmp_path, make_candidates(), spec, ExecutionContract())
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("mutation", [
    lambda items: items[1:],
    lambda items: items + [items[2]],
    lambda items: items[:2] + items[3:],
    lambda items: [replace(item, source="") if item.candidate_id == "unroll_2" else item for item in items],
])
def test_missing_or_duplicate_options_fail_before_writing(tmp_path, mutation):
    with pytest.raises(ValueError):
        write_diagnostic_prompts(tmp_path, mutation(make_candidates()), CPU_TEXT, ExecutionContract())
    assert not list(tmp_path.iterdir())


def test_existing_prompt_artifacts_are_never_overwritten(tmp_path):
    existing = tmp_path / "none.txt"
    existing.write_text("previous-run-prompt")
    with pytest.raises(FileExistsError):
        write_diagnostic_prompts(tmp_path, make_candidates(), CPU_TEXT, ExecutionContract())
    assert existing.read_text() == "previous-run-prompt"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["none.txt"]
