"""Prospective task/schema tests; no real LLM calls or expected speedups."""
from copy import deepcopy
import hashlib
import json

import pytest
from cpucond import local_llm as llm
from cpucond.local_cohort import _check_task_output_pair
from cpucond.models import CompilerTarget
from cpucond.selection_protocol import _requests, DEFAULT_CONFIG
from cpucond.selection_responses import parse_response
from cpucond.selection_task_v2 import (
    PROMPT_REVISION, LOCAL_SCHEMA, FORMAT, response_schema, local_config_v2,
)
from cpucond.transformations import make_candidates
from dataclasses import asdict


def stub():
    all_sources = {c.candidate_id: {"source": c.source} for c in make_candidates()}
    return {"compiler": asdict(CompilerTarget("clang", "clang version 18.1.3", target_triple="x86_64-linux-gnu")),
            "config": deepcopy(DEFAULT_CONFIG), "reference": all_sources["reference"],
            "candidates": {k: v for k, v in all_sources.items() if k.startswith("unroll_")},
            "cpu_context": {"text": "CPU_SENTINEL: explicitly supplied observation"}}


def requests(revised):
    protocol = stub()
    if revised: protocol["prompt_revision"] = PROMPT_REVISION
    return list(_requests(protocol))


def test_old_task_has_no_new_objective_or_schema():
    result = requests(False)
    assert len(result) == 20
    assert all("LOWEST KERNEL EXECUTION TIME" not in prompt for _, _, prompt in result)
    assert all("json_schema" not in json.loads(common)["output_format"] for _, common, _ in result)


def test_revised_protocol_has_objective_and_schema():
    for req, common, prompt in requests(True):
        obj = json.loads(common)
        assert "LOWEST KERNEL EXECUTION TIME" in obj["task"]
        assert obj["output_format"]["json_schema"] == response_schema(req)
        assert hashlib.sha256(prompt.encode()).hexdigest() == req["prompt_sha256"]


def test_revision_keeps_all_noninstruction_inputs_and_balanced_mapping():
    for old, new in zip(requests(False), requests(True)):
        for field in ("size", "trial", "condition", "option_mapping", "request_id"):
            assert old[0][field] == new[0][field]
        a, b = json.loads(old[1]), json.loads(new[1])
        a.pop("task"); b.pop("task")
        b["output_format"].pop("json_schema")
        assert a == b


def test_none_spec_share_everything_except_additional_cpu_section():
    reqs = requests(True)
    for i in range(0, len(reqs), 2):
        none, spec = reqs[i:i+2]
        assert none[1] == spec[1]
        assert "CPU_SENTINEL" not in none[2]
        assert spec[2].startswith(none[2])
        assert "CPU_SENTINEL" in spec[2]
        assert response_schema(none[0]) == response_schema(spec[0])


def test_unknown_revision_is_rejected():
    protocol = stub(); protocol["prompt_revision"] = "unreviewed"
    with pytest.raises(ValueError, match="revision"): list(_requests(protocol))


def test_config_legacy_and_v2_are_separate(local_config):
    original = deepcopy(local_config)
    revised = local_config_v2(local_config, 23456)
    llm.validate_config(local_config); llm.validate_config(revised)
    assert local_config == original and revised["options"] == original["options"]
    assert revised["model_digest"] == original["model_digest"]
    assert revised["format"] == FORMAT
    for version, fmt in ((LOCAL_SCHEMA, "json"), (llm.SCHEMA, FORMAT)):
        broken = deepcopy(local_config); broken.update(schema_version=version, format=fmt)
        with pytest.raises(ValueError): llm.validate_config(broken)


def test_payload_sends_schema_not_marker_and_does_not_change_model_options(local_config):
    config = local_config_v2(local_config, 23456)
    for req, _, prompt in requests(True):
        payload = llm.build_payload(config, req, prompt)
        assert payload["format"] == response_schema(req)
        assert payload["raw"] and not payload["stream"]
        assert payload["options"]["seed"] == config["seeds"][req["trial"] - 1]
        assert payload["model"] == local_config["model"]
        assert "context" not in payload and "messages" not in payload
        assert "tools" not in payload
        assert llm.context_bound(config, req, prompt)["required_context_upper_bound"] <= 16384
        preflight = llm.build_payload(config, req, prompt, preflight=True)
        assert preflight["format"] == payload["format"]
        assert preflight["options"]["num_predict"] == 1


def test_all_candidates_remain_allowed_and_missing_id_remains_invalid():
    req = requests(True)[0][0]
    schema = response_schema(req)
    assert schema["required"] == ["request_id", "selected_option_id"]
    assert schema["properties"]["request_id"]["enum"] == [req["request_id"]]
    assert schema["properties"]["selected_option_id"]["enum"] == list(req["option_mapping"])
    for option in req["option_mapping"]:
        raw = json.dumps({"request_id": req["request_id"], "selected_option_id": option}).encode()
        assert parse_response(raw, req)["status"] == "valid"
    raw = b'{"selected_option_id":"option_01"}'
    assert parse_response(raw, req)["invalid_reason"] == "missing_response_fields"


def test_task_and_decoding_revision_must_match(local_config):
    revised = local_config_v2(local_config, 23456)
    _check_task_output_pair({}, local_config)
    _check_task_output_pair({"prompt_revision": PROMPT_REVISION}, revised)
    with pytest.raises(ValueError): _check_task_output_pair({}, revised)
    with pytest.raises(ValueError): _check_task_output_pair({"prompt_revision": PROMPT_REVISION}, local_config)


def test_bad_schema_identifiers_rejected():
    for request in ({"request_id": None,"option_mapping":{"a":"b"}},
                    {"request_id": "x","option_mapping": {}},
                    {"request_id": "x","option_mapping": {1:"b"}}):
        with pytest.raises(ValueError): response_schema(request)

# File-backed protocol lifecycle with explicitly synthetic test transport context.
from test_selection_protocol import source_run


def test_versioned_export_clone_and_empty_summary(tmp_path, source_run, local_config, monkeypatch):
    from cpucond import selection, local_cohort
    from cpucond.selection_followup import summarize
    monkeypatch.setattr(selection, "_preflight", lambda protocol: {"test_fixture": True})
    monkeypatch.setattr(local_cohort, "_preflight", lambda protocol: {"test_fixture": True})
    old, _ = selection.prepare_pilot(tmp_path / "old", source_run)
    old_hashes = {p.relative_to(old): selection.digest(p) for p in old.rglob("*") if p.is_file()}
    task, _ = selection.prepare_pilot(tmp_path / "v2-task", source_run, prompt_revision=PROMPT_REVISION)
    local, status = local_cohort.prepare_local_pilot(tmp_path / "v2-local", task, local_config_v2(local_config, 23456))
    assert status["counts"]["missing"] == 20
    assert selection.check_pilot(local)["passed"]
    assert selection.check_pilot(old)["passed"]
    assert old_hashes == {p.relative_to(old): selection.digest(p) for p in old.rglob("*") if p.is_file()}
    summary = summarize(local)
    assert summary["counts"]["received"] == 0
    assert all(group["missing"] == 5 for group in summary["groups"])
    assert summary["reports"] is None
