"""Recovery tests use inert API fixtures; never real LLM responses or timings."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

from cpucond import local_cohort, local_llm as llm, recovery, selection
from cpucond.selection_responses import collect_responses
from test_selection_protocol import source_run


class InertAPI:
    def __init__(self, config, protocol, root):
        self.config, self.protocol, self.root = config, protocol, root
        self.loaded = False
        self.actual_calls, self.unloads = 0, 0

    @staticmethod
    def result(value):
        return json.dumps(value, ensure_ascii=False).encode(), value

    def get(self, path):
        if path == "/api/version":
            return self.result({"version": self.config["ollama_version"]})
        if path == "/api/tags":
            return self.result({"models": [{"name": self.config["model"], "digest": self.config["model_digest"]}]})
        if path == "/api/ps":
            return self.result({"models": [{"digest": self.config["model_digest"], "size_vram": 0,
                "context_length": self.config["options"]["num_ctx"]}] if self.loaded else []})
        pytest.fail("unexpected inert API path")

    def post(self, path, payload):
        if path == "/api/show":
            return self.result(deepcopy(self.config["model_show"]))
        assert path == "/api/generate"
        if payload.get("keep_alive") == 0:
            self.loaded = False
            self.unloads += 1
            return self.result({"done": True, "done_reason": "unload"})
        self.loaded = True
        request = next(row for row in self.protocol["requests"]
                       if llm.render_chat(self.config["system"], (self.root / row["prompt_path"]).read_text()) == payload["prompt"])
        preflight = payload["options"]["num_predict"] == 1
        if not preflight:
            self.actual_calls += 1
        # Deliberately retain seven invalid answers, like the reported counts.
        value = {} if not preflight and self.actual_calls <= 7 else {
            "request_id": request["request_id"], "selected_option_id": "option_01"}
        return self.result({"response": json.dumps(value), "done": True,
            "done_reason": "length" if preflight else "stop", "eval_count": 1 if preflight else 20,
            "prompt_eval_count": len(payload["prompt"].encode()) // 4})


@pytest.fixture
def failed_local(tmp_path, source_run, local_config, monkeypatch):
    monkeypatch.setattr(selection, "_preflight", lambda protocol: {"inert_preflight": True})
    monkeypatch.setattr(local_cohort, "_preflight", lambda protocol: {"inert_preflight": True})
    manual, _ = selection.prepare_pilot(tmp_path / "manual", source_run)
    root, _ = local_cohort.prepare_local_pilot(tmp_path / "original", manual, local_config)
    protocol = selection.read_json(root / "protocol.json")
    fake = InertAPI(local_config, protocol, root)
    monkeypatch.setattr(llm, "OllamaClient", lambda *args: fake)
    monkeypatch.setattr(llm, "server_evidence", lambda endpoint, pid: {"pid": pid})
    monkeypatch.setattr(llm, "runner_processes", lambda pid: [])
    llm.preflight_local(root)
    llm.run_local(root)
    llm.unload_local(root)
    frozen = selection.freeze_answers(root)
    assert frozen["counts"] == {"total": 20, "received": 20, "valid": 13, "invalid": 7, "missing": 0}
    # Construct a LEGACY FAILURE FIXTURE, not a repair of real evidence.
    frozen.pop("frozen_clock")
    selection.write_json(root / "freeze.json", frozen)
    pilot = selection.read_json(root / "pilot.json")
    pilot["freeze_sha256"] = selection.digest(root / "freeze.json")
    selection.write_json(root / "pilot.json", pilot)
    attempt = root / "scoring-attempts/old-failure/attempt.json"
    attempt.parent.mkdir(parents=True)
    selection.write_json(attempt, {"status": "failed", "failure": {
        "category": "ValueError", "reason": "scored pilot audit failed: measurement was started before response freeze"}})
    selection.write_json(root / "score.json", {"status": "completed", "attempt_path": "scoring-attempts/old-failure/attempt.json",
        "started_utc": (datetime.fromisoformat(frozen["frozen_utc"]) - timedelta(seconds=1.3)).isoformat()})
    return root, fake


def test_recovery_preserves_raw_answers_invalids_protocol_and_source_tree(failed_local, tmp_path):
    source, fake = failed_local
    before = recovery.tree_hashes(source)
    calls = fake.actual_calls
    new = recovery.prepare_recovery(tmp_path / "repaired", source)
    assert recovery.tree_hashes(source) == before
    assert fake.actual_calls == calls == 20
    assert (new / "protocol.json").read_bytes() == (source / "protocol.json").read_bytes()
    assert recovery.tree_hashes(new / "responses") == recovery.tree_hashes(source / "responses")
    assert recovery.tree_hashes(new / "local-acquisition") == recovery.tree_hashes(source / "local-acquisition")
    assert not (new / "score.json").exists() and not (new / "freeze.json").exists()
    assert not (new / "scoring-attempts").exists()
    assert collect_responses(new)["counts"] == selection.read_json(source / "freeze.json")["counts"]
    assert selection.check_pilot(new)["passed"]
    llm.unload_local(new)
    frozen = selection.freeze_answers(new)
    assert "frozen_clock" in frozen
    assert "frozen_clock" not in selection.read_json(source / "freeze.json")
    assert selection.check_pilot(new)["passed"]
    isolation = llm.assert_unloaded(new)
    score = {**recovery.event_fields("started"), "local_inference_isolation": isolation}
    assert selection._score_clock_warnings(new, frozen, score) == []
    assert fake.actual_calls == 20
    assert recovery.tree_hashes(source) == before


@pytest.mark.parametrize("action", [llm.preflight_local, llm.run_local])
def test_recovery_cannot_generate_new_answers(failed_local, tmp_path, action):
    source, fake = failed_local
    new = recovery.prepare_recovery(tmp_path / "repaired", source)
    with pytest.raises(ValueError, match="reused acquired answers"):
        action(new)
    assert fake.actual_calls == 20


@pytest.mark.parametrize("path", ["responses", "local-acquisition", "sources", "requests"])
def test_reused_bytes_are_bound_in_every_static_check(failed_local, tmp_path, path):
    source, _ = failed_local
    new = recovery.prepare_recovery(tmp_path / "repaired", source)
    file = next(p for p in (new / path).rglob("*") if p.is_file())
    file.write_bytes(file.read_bytes() + b" ")
    with pytest.raises(ValueError):
        selection.check_static(new)


def test_missing_response_raw_is_a_blocker_not_reconstructed(failed_local, tmp_path):
    source, fake = failed_local
    next((source / "responses").rglob("response.raw")).unlink()
    with pytest.raises(ValueError, match="incomplete"):
        recovery.prepare_recovery(tmp_path / "repaired", source)
    assert fake.actual_calls == 20
    assert not (tmp_path / "repaired").exists()


def test_recovery_cannot_replace_successful_scores_or_write_inside_source(failed_local, tmp_path):
    source, _ = failed_local
    before = recovery.tree_hashes(source)
    with pytest.raises(ValueError, match="inside"):
        recovery.prepare_recovery(source / "child", source)
    assert recovery.tree_hashes(source) == before
    path = source / "scoring-attempts/old-failure/attempt.json"
    selection.write_json(path, {"status": "completed"})
    with pytest.raises(ValueError, match="successful"):
        recovery.prepare_recovery(tmp_path / "repaired", source)


def test_prepare_only_has_no_http_calls_and_records_same_observations(failed_local, tmp_path, monkeypatch):
    source, _ = failed_local
    monkeypatch.setattr(llm, "OllamaClient", lambda *a: pytest.fail("prepare-only must be offline"))
    result = recovery.recover_local(tmp_path / "repaired", source, prepare_only=True)
    assert result["stage"] == "prepared" and result["counts"]["invalid"] == 7
    assert result["new_model_requests"] == 0


def test_closed_server_records_failure_without_modifying_source(failed_local, tmp_path, monkeypatch):
    source, _ = failed_local
    before = recovery.tree_hashes(source)
    monkeypatch.setattr(llm, "unload_local", lambda *a: (_ for _ in ()).throw(ValueError("server not verified")))
    with pytest.raises(ValueError, match="server not verified"):
        recovery.recover_local(tmp_path / "repaired", source)
    assert recovery.tree_hashes(source) == before
    failure = next((tmp_path / "repaired").rglob("recovery-failure.json"))
    assert selection.read_json(failure)["source_unchanged"] is True
    assert selection.read_json(failure)["new_model_requests"] == 0


def test_extra_acquisition_is_rejected_even_if_not_yet_imported(failed_local, tmp_path):
    source, _ = failed_local
    new = recovery.prepare_recovery(tmp_path / "repaired", source)
    extra = new / "local-acquisition/sessions/new-session.json"
    extra.parent.mkdir(exist_ok=True)
    extra.write_text("{}")
    with pytest.raises(ValueError, match="new answer/acquisition"):
        selection.check_static(new)


def test_completed_recovery_is_not_measured_again(failed_local, tmp_path, monkeypatch):
    source, fake = failed_local
    output = tmp_path / "repaired"
    new = recovery.prepare_recovery(output, source)
    # Inert completed-state fixture tests only the no-repeat branch.
    selection.write_json(new / "recovery-state.json", {
        "stage": "completed", "pilot_directory": str(new), "new_model_requests": 0,
        "counts": selection.read_json(source / "freeze.json")["counts"],
    })
    monkeypatch.setattr(selection, "check_pilot", lambda directory: {"passed": True})
    monkeypatch.setattr(llm, "unload_local", lambda *a: pytest.fail("must not unload or measure again"))
    result = recovery.recover_local(output, source)
    assert result["reused_existing_completed_recovery"] is True
    assert fake.actual_calls == 20


def test_multiple_completed_recoveries_are_not_ranked_or_selected(failed_local, tmp_path):
    source, _ = failed_local
    output = tmp_path / "repaired"
    for _ in range(2):
        new = recovery.prepare_recovery(output, source)
        selection.write_json(new / "recovery-state.json", {"stage": "completed"})
    with pytest.raises(ValueError, match="multiple completed recoveries"):
        recovery.recover_local(output, source)
