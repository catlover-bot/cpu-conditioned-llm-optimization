"""Blind answer import tests use synthetic files only; no model or process runs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from cpucond import selection_responses as responses


def save_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    # The lifecycle module owns static-input auditing. These isolated tests retain
    # response-side protocol-hash validation and exercise real files throughout.
    monkeypatch.setattr(responses, "_check_static", lambda root: None)
    requests = []
    for condition in ("none", "spec"):
        requests.append({"request_key": "n128-t01-" + condition, "request_id": "n128-t01", "size": 128,
                         "seed": 17, "trial": 1, "condition": condition, "prompt_path": condition + ".txt",
                         "prompt_sha256": ("a" if condition == "none" else "b") * 64,
                         "option_mapping": {"option_01": "unroll_4", "option_02": "unroll_1",
                                            "option_03": "unroll_16", "option_04": "unroll_2", "option_05": "unroll_8"}})
    protocol = {"policies": {"first_attempt_policy": "first_attempt_only"}, "requests": requests}
    save_json(tmp_path / "protocol.json", protocol)
    save_json(tmp_path / "pilot.json", {"cohort": "real", "status": "awaiting_real_responses",
                                         "protocol_sha256": hashlib.sha256((tmp_path / "protocol.json").read_bytes()).hexdigest()})
    return tmp_path, requests


def metadata(request, cohort="real", method="manual_transcription"):
    return {"cohort": cohort, "acquisition_method": method, "model_identifier": None, "obtained_at": None,
            "prompt_hash": request["prompt_sha256"], "generation_settings": None, "usage": None,
            "missing_reasons": {name: "Not available from the supplied export." for name in
                                ("model_identifier", "obtained_at", "generation_settings", "usage")},
            "blinding": {"independent_session": None, "no_tools": None, "no_prior_results": None,
                         "limitations": ["Manual transfer does not independently establish session isolation or tool use."]}}


def answer(request, option="option_01", **fields):
    return json.dumps({"request_id": request["request_id"], "selected_option_id": option, **fields}, ensure_ascii=False).encode()


def import_bytes(root, request, raw, supplied_metadata=None):
    raw_path, metadata_path = root / "incoming.raw", root / "incoming.metadata.json"
    raw_path.write_bytes(raw)
    save_json(metadata_path, supplied_metadata if supplied_metadata is not None else metadata(request))
    return responses.import_response(root, request["request_key"], raw_path, metadata_path)


def test_valid_raw_original_metadata_provenance_and_missing_denominator(pilot):
    root, requests = pilot
    raw = answer(requests[0], rationale_short="短い説明") + b"\r\n"
    imported = import_bytes(root, requests[0], raw)
    assert imported["status"] == "valid" and imported["selected_candidate_id"] == "unroll_4"
    assert imported["attempt_id"] == "attempt-0001" and imported["primary_attempt"] is True
    assert (root / imported["files"]["raw_response"]["path"]).read_bytes() == raw
    assert imported["metadata"]["model_identifier"] is None
    assert imported["metadata"]["provenance"]["model_information_status"] == "self_reported"
    snapshot = responses.collect_responses(root)
    assert snapshot["counts"] == {"total": 2, "received": 1, "valid": 1, "invalid": 0, "missing": 1}
    assert snapshot == responses.collect_responses(root)
    assert snapshot["requests"][1]["status"] == "missing"
    assert snapshot["requests"][1]["selected_candidate_id"] is None
    assert snapshot["requests"][1]["metadata"] is None
    assert snapshot["attempts"][0]["attempt_manifest_sha256"] == imported["attempt_manifest_sha256"]


@pytest.mark.parametrize("raw,reason", [
    (b"", "invalid_json"),
    (b"```json\n{}\n```", "invalid_json"),
    (b"{} {}", "invalid_json"),
    (b"[]", "response_must_be_one_object"),
    (b'{"request_id":"n128-t01","request_id":"n128-t01","selected_option_id":"option_01"}', "duplicate_json_key"),
    (b'{"request_id":"n128-t01","selected_option_id":"option_01","rationale_short":NaN}', "non_finite_json_constant"),
    (b'{"request_id":"n128-t01","selected_option_id":"option_01","rationale_short":1e999}', "non_finite_json_number"),
    (b'{"request_id":"n128-t01","selected_option_id":"option_01","rationale_short":"\\ud800"}', "invalid_unicode_string"),
    (b"\xff", "invalid_utf8"),
    (b'{"request_id":"other","selected_option_id":"option_01"}', "request_id_mismatch"),
    (b'{"request_id":"n128-t01","selected_option_id":"option_99"}', "unknown_option_id"),
    (b'{"request_id":"n128-t01","selected_option_id":["option_01","option_02"]}', "selected_option_id_must_be_one_string"),
    (b'{"request_id":"n128-t01","selected_option_id":"option_01","confidence":1}', "unknown_response_fields"),
    (b'{"request_id":"n128-t01"}', "missing_response_fields"),
])
def test_invalid_answers_are_preserved_without_automatic_correction(pilot, raw, reason):
    root, requests = pilot
    result = import_bytes(root, requests[0], raw)
    assert result["status"] == "invalid" and result["invalid_reason"] == reason
    assert result["selected_candidate_id"] is None
    assert (root / result["files"]["raw_response"]["path"]).read_bytes() == raw
    assert responses.collect_responses(root)["counts"] == {"total": 2, "received": 1, "valid": 0, "invalid": 1, "missing": 1}


def test_rationale_length_boundary_counts_characters(pilot):
    _, requests = pilot
    assert responses.parse_response(answer(requests[0], rationale_short="あ" * 500), requests[0])["status"] == "valid"
    assert responses.parse_response(answer(requests[0], rationale_short="あ" * 501), requests[0])["status"] == "invalid"
    assert responses.parse_response(answer(requests[0], rationale_short=None), requests[0])["status"] == "invalid"


def test_invalid_first_attempt_stays_primary_after_valid_correction(pilot):
    root, requests = pilot
    first = import_bytes(root, requests[0], b"not structured")
    second = import_bytes(root, requests[0], answer(requests[0], "option_03"))
    assert second["attempt_id"] == "attempt-0002" and second["primary_attempt"] is False
    snapshot = responses.collect_responses(root)
    assert snapshot["primary_attempt_policy"] == "first_attempt_only"
    assert snapshot["counts"]["invalid"] == 1 and snapshot["counts"]["valid"] == 0
    assert snapshot["requests"][0]["raw_response_sha256"] == first["raw_response_sha256"]
    assert snapshot["requests"][0]["selected_candidate_id"] is None
    assert len(snapshot["attempts"]) == 2 and snapshot["attempts"][1]["status"] == "valid"


def test_duplicate_raw_is_rejected_even_with_different_metadata(pilot):
    root, requests = pilot
    raw = answer(requests[0])
    import_bytes(root, requests[0], raw)
    changed = metadata(requests[0])
    changed["model_identifier"] = "self-reported-model"
    with pytest.raises(ValueError, match="duplicate"):
        import_bytes(root, requests[0], raw, changed)
    assert len(responses.collect_responses(root)["attempts"]) == 1


def test_none_spec_may_receive_same_text_but_require_their_own_prompt_hash(pilot):
    root, requests = pilot
    raw = answer(requests[0])
    import_bytes(root, requests[0], raw)
    with pytest.raises(ValueError, match="prompt_hash"):
        import_bytes(root, requests[1], raw, metadata(requests[0]))
    import_bytes(root, requests[1], raw)
    assert responses.collect_responses(root)["counts"]["valid"] == 2


@pytest.mark.parametrize("mutation", ["cohort", "method", "prompt", "model_missing_reason", "time_naive", "time_invalid",
                                       "blinding_type", "blinding_limitations", "unknown_field", "settings_type"])
def test_bad_metadata_rejects_import_without_creating_an_attempt(pilot, mutation):
    root, requests = pilot
    data = metadata(requests[0])
    if mutation == "cohort":
        data["cohort"] = "synthetic"
    elif mutation == "method":
        data["acquisition_method"] = "synthetic_fixture"
    elif mutation == "prompt":
        data["prompt_hash"] = "f" * 64
    elif mutation == "model_missing_reason":
        del data["missing_reasons"]["model_identifier"]
    elif mutation == "time_naive":
        data["obtained_at"] = "2026-09-10T12:00:00"
    elif mutation == "time_invalid":
        data["obtained_at"] = "unknown"
    elif mutation == "blinding_type":
        data["blinding"]["no_tools"] = 1
    elif mutation == "blinding_limitations":
        data["blinding"]["limitations"] = []
    elif mutation == "unknown_field":
        data["api_verified"] = True
    else:
        data["generation_settings"] = "temperature inferred"
    with pytest.raises(ValueError):
        import_bytes(root, requests[0], answer(requests[0]), data)
    assert not (root / "responses").exists()


def test_api_export_identifier_is_imported_unverified_and_timezone_retained(pilot):
    root, requests = pilot
    data = metadata(requests[0], method="api_export")
    data.update(model_identifier="reported-provider-model", obtained_at="2026-09-10T12:00:00+09:00",
                generation_settings={"temperature": 0}, usage={"input_tokens": 100, "output_tokens": 10})
    imported = import_bytes(root, requests[0], answer(requests[0]), data)
    saved = imported["metadata"]
    assert saved["model_identifier"] == "reported-provider-model"
    assert saved["obtained_at"] == data["obtained_at"]
    assert saved["usage"] == data["usage"]
    assert saved["provenance"]["model_information_status"] == "imported_unverified"
    assert saved["provenance"]["api_identity_verified"] is False


def test_synthetic_cohort_cannot_accept_manual_real_metadata(pilot):
    root, requests = pilot
    control = json.loads((root / "pilot.json").read_text())
    control["cohort"] = "synthetic"
    save_json(root / "pilot.json", control)
    with pytest.raises(ValueError, match="mixed"):
        import_bytes(root, requests[0], answer(requests[0]), metadata(requests[0], cohort="synthetic"))
    result = import_bytes(root, requests[0], answer(requests[0]), metadata(requests[0], cohort="synthetic", method="synthetic_fixture"))
    assert result["metadata"]["provenance"]["model_information_status"] == "synthetic_fixture"
    assert responses.collect_responses(root)["cohort"] == "synthetic"


def test_freeze_blocks_new_attempts_but_snapshot_remains_readable(pilot):
    root, requests = pilot
    import_bytes(root, requests[0], answer(requests[0]))
    frozen = responses.collect_responses(root)
    save_json(root / "freeze.json", frozen)
    with pytest.raises(ValueError, match="frozen"):
        import_bytes(root, requests[1], answer(requests[1]))
    assert responses.collect_responses(root) == frozen


@pytest.mark.parametrize("file", ["response.raw", "metadata.raw.json", "metadata.json", "parsed.json", "attempt.json"])
def test_changed_response_evidence_is_rejected(pilot, file):
    root, requests = pilot
    result = import_bytes(root, requests[0], answer(requests[0]))
    path = root / "responses" / requests[0]["request_key"] / result["attempt_id"] / file
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        responses.collect_responses(root)


def test_unknown_request_and_changed_protocol_are_rejected(pilot):
    root, requests = pilot
    raw, meta = root / "incoming.raw", root / "incoming.metadata.json"
    raw.write_bytes(answer(requests[0]))
    save_json(meta, metadata(requests[0]))
    with pytest.raises(ValueError, match="unknown request"):
        responses.import_response(root, "../../escape", raw, meta)
    path = root / "protocol.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="protocol changed"):
        responses.collect_responses(root)


def test_answer_code_is_preserved_as_invalid_data_without_evaluation(pilot, monkeypatch):
    root, requests = pilot
    def forbidden(*args, **kwargs):
        pytest.fail("answer text was evaluated or executed")
    monkeypatch.setattr("builtins.eval", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    raw = b"__import__('os').system('touch must-not-exist')"
    assert import_bytes(root, requests[0], raw)["status"] == "invalid"
    assert not (root / "must-not-exist").exists()


def test_attempt_sequence_gap_and_unknown_request_artifacts_are_rejected(pilot):
    root, requests = pilot
    result = import_bytes(root, requests[0], answer(requests[0]))
    directory = root / "responses" / requests[0]["request_key"]
    (directory / result["attempt_id"]).rename(directory / "attempt-0002")
    with pytest.raises(ValueError, match="sequence"):
        responses.collect_responses(root)
