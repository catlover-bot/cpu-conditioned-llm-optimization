"""Local acquisition reuses a sealed task without touching its manual cohort."""

from collections import Counter
from copy import deepcopy

import pytest

from cpucond import local_cohort, selection
from cpucond.prompts import CPU_SECTION_HEADER
from cpucond.selection_protocol import CANDIDATE_IDS
from test_selection_protocol import source_run


@pytest.fixture
def manual_pilot(tmp_path, source_run, monkeypatch):
    monkeypatch.setattr(selection, "_preflight", lambda protocol: {"test_fixture": True})
    monkeypatch.setattr(local_cohort, "_preflight", lambda protocol: {"test_fixture": True})
    directory, _ = selection.prepare_pilot(tmp_path / "manual", source_run)
    return directory


def tree_hashes(directory):
    return {path.relative_to(directory).as_posix(): selection.digest(path)
            for path in directory.rglob("*") if path.is_file()}


def test_local_cohort_keeps_manual_inputs_balancing_and_generic_contract(tmp_path, manual_pilot, local_config):
    source_before = tree_hashes(manual_pilot)
    original = selection.read_json(manual_pilot / "protocol.json")
    directory, status = local_cohort.prepare_local_pilot(tmp_path / "new", manual_pilot, local_config)
    protocol = selection.read_json(directory / "protocol.json")
    assert directory.parent.name == "local"
    assert tree_hashes(manual_pilot) == source_before
    assert status["cohort"] == "real"
    assert status["real_response_count"] == status["synthetic_response_count"] == 0
    assert status["counts"]["total"] == status["counts"]["missing"] == 20
    assert status["environment_role"] == "development_smoke" and status["publishable_benchmark"] is False
    assert protocol["requests"] == original["requests"]
    assert protocol["compiler"] == original["compiler"]
    assert protocol["compiler"]["target_flags"] == []
    assert protocol["target_mode"] == "compiler_default_generic"
    assert protocol["measurement_config"] == original["measurement_config"]
    assert protocol["execution_contract"] == original["execution_contract"]
    assert protocol["local_llm"] == local_config
    assert protocol["source_pilot"]["protocol_sha256"] == selection.digest(manual_pilot / "protocol.json")
    for path, digest in protocol["source_pilot"]["reused_artifacts"].items():
        assert (directory / path).read_bytes() == (manual_pilot / path).read_bytes()
        assert selection.digest(directory / path) == digest
    for size in (128, 256):
        for trial in range(1, 6):
            pair = {request["condition"]: request for request in protocol["requests"]
                    if request["size"] == size and request["trial"] == trial}
            none = (directory / pair["none"]["prompt_path"]).read_text()
            spec = (directory / pair["spec"]["prompt_path"]).read_text()
            assert spec == none + CPU_SECTION_HEADER + protocol["cpu_context"]["text"] + "\n"
            assert pair["none"]["option_mapping"] == pair["spec"]["option_mapping"]
        for condition in ("none", "spec"):
            rows = [r for r in protocol["requests"] if r["size"] == size and r["condition"] == condition]
            for position in range(5):
                assert Counter(list(row["option_mapping"].values())[position] for row in rows) == Counter(CANDIDATE_IDS)
    checked = selection.check_pilot(directory)
    assert checked["passed"], checked


def test_real_manual_answers_and_prior_measurements_are_not_copied(tmp_path, manual_pilot, local_config):
    protocol = selection.read_json(manual_pilot / "protocol.json")
    request = protocol["requests"][0]
    raw = manual_pilot / request["raw_response_path"]
    metadata = manual_pilot / request["metadata_path"]
    selection.write_json(raw, {"request_id": request["request_id"], "selected_option_id": "option_01"})
    selection.write_json(metadata, selection.read_json(manual_pilot / request["metadata_template_path"]))
    selection.import_answer(manual_pilot, request["request_key"], raw, metadata)
    marker = manual_pilot / "scoring-attempts" / "old-rank.txt"
    marker.parent.mkdir()
    marker.write_text("DO_NOT_COPY_PRIOR_MEASUREMENTS")
    before = tree_hashes(manual_pilot)
    directory, status = local_cohort.prepare_local_pilot(tmp_path / "new", manual_pilot, local_config)
    assert tree_hashes(manual_pilot) == before
    assert status["counts"]["received"] == 0 and status["counts"]["missing"] == 20
    assert not (directory / "responses").exists()
    assert not (directory / "scoring-attempts").exists()
    assert not (directory / request["raw_response_path"]).exists()


def test_local_clone_rejects_synthetic_and_already_local_sources(tmp_path, source_run, manual_pilot, local_config):
    synthetic, _ = selection.prepare_pilot(tmp_path / "synthetic", source_run, cohort="synthetic")
    with pytest.raises(ValueError, match="manual real"):
        local_cohort.prepare_local_pilot(tmp_path / "bad", synthetic, local_config)
    directory, _ = local_cohort.prepare_local_pilot(tmp_path / "new", manual_pilot, local_config)
    with pytest.raises(ValueError, match="manual real"):
        local_cohort.prepare_local_pilot(tmp_path / "bad", directory, local_config)
    with pytest.raises(ValueError, match="real pilot"):
        selection.synthetic_answers(directory)


def test_local_clone_refuses_output_inside_source_without_writes(manual_pilot, local_config):
    before = tree_hashes(manual_pilot)
    with pytest.raises(ValueError, match="inside"):
        local_cohort.prepare_local_pilot(manual_pilot, manual_pilot, local_config)
    assert tree_hashes(manual_pilot) == before


def test_saved_provenance_is_standalone_and_setup_evidence_is_sealed(tmp_path, manual_pilot, local_config):
    evidence = tmp_path / "runtime-version.json"
    selection.write_json(evidence, {"version": "fixture-version"})
    directory, _ = local_cohort.prepare_local_pilot(tmp_path / "new", manual_pilot, local_config, evidence_files=[evidence])
    protocol = selection.read_json(directory / "protocol.json")
    manual_pilot.rename(manual_pilot.with_name("moved-manual"))
    checked = selection.check_pilot(directory)
    assert checked["passed"], checked
    saved = directory / protocol["local_setup_evidence"][0]["path"]
    saved.write_text("changed")
    assert not selection.check_pilot(directory)["passed"]


def test_local_protocol_rejects_condition_change_even_after_rehash(tmp_path, manual_pilot, local_config):
    directory, _ = local_cohort.prepare_local_pilot(tmp_path / "new", manual_pilot, local_config)
    protocol = selection.read_json(directory / "protocol.json")
    changed = deepcopy(protocol)
    changed["compiler"]["target_flags"] = ["-march=native"]
    with pytest.raises(ValueError, match="changed conditions"):
        local_cohort.validate_local_protocol(directory, changed)
