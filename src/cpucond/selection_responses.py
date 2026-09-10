"""Import immutable blind-selection answers as data, retaining every attempt.

The caller holds the pilot mutation lock. Exclusive attempt-directory/file
creation additionally prevents silent overwrites through direct API calls.
No answer text is evaluated or passed to a process or a model.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re


ATTEMPT_SCHEMA = "cpucond.selection-response-attempt.v1"
PRIMARY_POLICY = "first_attempt_only"
_KEY = re.compile(r"[a-z0-9][a-z0-9_-]{0,127}\Z")
_ATTEMPT = re.compile(r"attempt-([0-9]{4,})\Z")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


class _InvalidJSON(ValueError):
    pass


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise _InvalidJSON("duplicate_json_key")
            result[key] = value
        return result

    def constant(value):
        raise _InvalidJSON("non_finite_json_constant")

    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _InvalidJSON("invalid_utf8") from exc
    try:
        parsed = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        pending = [parsed]
        while pending:
            value = pending.pop()
            if isinstance(value, str):
                try:
                    value.encode("utf-8", errors="strict")
                except UnicodeEncodeError as exc:
                    raise _InvalidJSON("invalid_unicode_string") from exc
            elif isinstance(value, float) and not math.isfinite(value):
                raise _InvalidJSON("non_finite_json_number")
            elif isinstance(value, dict):
                pending.extend(value)
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        return parsed
    except _InvalidJSON:
        raise
    except (ValueError, RecursionError) as exc:
        raise _InvalidJSON("invalid_json") from exc


def _check_static(pilot_dir):
    # Delayed import avoids a cycle with selection's lifecycle/CLI orchestration.
    from .selection import check_static
    check_static(pilot_dir)


def _context(pilot_dir):
    root = Path(pilot_dir)
    _check_static(root)
    pilot = _strict_json((root / "pilot.json").read_bytes())
    protocol_bytes = (root / "protocol.json").read_bytes()
    protocol = _strict_json(protocol_bytes)
    if type(pilot) is not dict or type(protocol) is not dict:
        raise ValueError("pilot and protocol must be JSON objects")
    if pilot.get("cohort") not in ("real", "synthetic"):
        raise ValueError("pilot cohort must be real or synthetic")
    if pilot.get("protocol_sha256") != _sha(protocol_bytes):
        raise ValueError("protocol changed after pilot creation")
    if protocol.get("policies", {}).get("first_attempt_policy") != PRIMARY_POLICY:
        raise ValueError("protocol must preregister first_attempt_only scoring")
    requests = protocol["requests"]
    if not isinstance(requests, list) or not requests:
        raise ValueError("protocol requests are missing")
    keys = [request["request_key"] for request in requests]
    if any(not isinstance(key, str) or not _KEY.fullmatch(key) for key in keys) or len(set(keys)) != len(keys):
        raise ValueError("protocol request keys must be unique safe identifiers")
    return root, pilot, protocol


def parse_response(raw, request):
    """Classify an exact raw UTF-8 response; invalid responses are never repaired."""
    result = {"status": "invalid", "selected_option_id": None, "selected_candidate_id": None,
              "rationale_short": None, "invalid_reason": None}
    try:
        data = _strict_json(raw)
        if type(data) is not dict:
            raise ValueError("response_must_be_one_object")
        if set(data) - {"request_id", "selected_option_id", "rationale_short"}:
            raise ValueError("unknown_response_fields")
        if not {"request_id", "selected_option_id"}.issubset(data):
            raise ValueError("missing_response_fields")
        if type(data["request_id"]) is not str or data["request_id"] != request["request_id"]:
            raise ValueError("request_id_mismatch")
        selected = data["selected_option_id"]
        if type(selected) is not str:
            raise ValueError("selected_option_id_must_be_one_string")
        if selected not in request["option_mapping"]:
            raise ValueError("unknown_option_id")
        if "rationale_short" in data and (type(data["rationale_short"]) is not str or len(data["rationale_short"]) > 500):
            raise ValueError("rationale_short_must_be_a_string_of_at_most_500_characters")
        result.update(status="valid", selected_option_id=selected,
                      selected_candidate_id=request["option_mapping"][selected], rationale_short=data.get("rationale_short"))
    except (ValueError, RecursionError) as exc:
        result["invalid_reason"] = str(exc) if not isinstance(exc, RecursionError) else "invalid_json"
    return result


def _parse_acquired(raw, request, metadata, pilot):
    parsed = parse_response(raw, request)
    if pilot.get("acquisition_backend") == "ollama_local":
        usage = metadata.get("usage") or {}
        reason = None
        if usage.get("context_mismatch") is True:
            reason = "context_mismatch"
        elif usage.get("output_truncated") is True or usage.get("done_reason") == "length" or usage.get("done") is False:
            reason = "output_truncated"
        if reason is not None:
            parsed.update(status="invalid", selected_option_id=None, selected_candidate_id=None,
                          rationale_short=None, invalid_reason=reason)
    return parsed


def _validate_metadata(raw, pilot, request):
    metadata = _strict_json(raw)
    required = {"cohort", "acquisition_method", "model_identifier", "obtained_at", "prompt_hash", "missing_reasons", "blinding"}
    optional = {"generation_settings", "usage", "acquisition_source"}
    if type(metadata) is not dict or not required.issubset(metadata) or set(metadata) - required - optional:
        raise ValueError("metadata has missing or unknown fields")
    cohort, method = metadata["cohort"], metadata["acquisition_method"]
    if cohort != pilot["cohort"]:
        raise ValueError("metadata cohort does not match the pilot")
    methods = ("synthetic_fixture",) if cohort == "synthetic" else ("manual_transcription", "api_export")
    if method not in methods:
        raise ValueError("synthetic and real acquisition methods cannot be mixed")
    if metadata["prompt_hash"] != request["prompt_sha256"]:
        raise ValueError("metadata prompt_hash does not match this request")
    missing = metadata["missing_reasons"]
    if type(missing) is not dict or any(type(key) is not str or type(value) is not str or not value.strip() for key, value in missing.items()):
        raise ValueError("missing_reasons must map field names to nonempty reasons")
    for key in ("generation_settings", "usage"):
        metadata.setdefault(key, None)
    for key in ("model_identifier", "obtained_at", "generation_settings", "usage", "acquisition_source"):
        if key not in metadata:
            continue
        value = metadata[key]
        if value is None:
            if not missing.get(key):
                raise ValueError(f"metadata {key} is unknown without a reason")
        elif key in ("generation_settings", "usage"):
            if type(value) is not dict:
                raise ValueError(f"metadata {key} must be an object or null")
        elif type(value) is not str or not value.strip():
            raise ValueError(f"metadata {key} must be a nonempty string or null")
    if metadata["obtained_at"] is not None:
        try:
            obtained = datetime.fromisoformat(metadata["obtained_at"])
        except ValueError as exc:
            raise ValueError("metadata obtained_at must be an ISO timestamp with timezone") from exc
        if obtained.utcoffset() is None:
            raise ValueError("metadata obtained_at must include a timezone")
    blinding = metadata["blinding"]
    flags = ("independent_session", "no_tools", "no_prior_results")
    if type(blinding) is not dict or set(blinding) != {*flags, "limitations"}:
        raise ValueError("blinding metadata fields are missing or unknown")
    if any(blinding[key] is not None and type(blinding[key]) is not bool for key in flags):
        raise ValueError("blinding flags must be boolean or null")
    limitations = blinding["limitations"]
    if type(limitations) is not list or any(type(value) is not str or not value.strip() for value in limitations):
        raise ValueError("blinding limitations must be a list of nonempty strings")
    if any(blinding[key] is not True for key in flags) and not limitations:
        raise ValueError("uncertain or unmet blinding conditions need an explicit limitation")
    metadata["provenance"] = {
        "model_information_status": {"manual_transcription": "self_reported", "api_export": "imported_unverified", "synthetic_fixture": "synthetic_fixture"}[method],
        "api_identity_verified": False,
        "blinding_independently_verified": False,
        "interpretation": "Imported acquisition, model and blinding claims are preserved as supplied; no provider API or session-history verification was performed.",
    }
    return metadata


def _request_directory(root, request_key):
    directory = root / "responses" / request_key
    if directory.is_symlink() or (root / "responses").is_symlink():
        raise ValueError("response directories cannot be symbolic links")
    return directory


def _load_attempts(root, pilot, request):
    directory = _request_directory(root, request["request_key"])
    if not directory.exists():
        return []
    entries = list(directory.iterdir())
    if any(not entry.is_dir() or entry.is_symlink() or not _ATTEMPT.fullmatch(entry.name) for entry in entries):
        raise ValueError("unexpected response-attempt artifact")
    entries.sort(key=lambda entry: int(_ATTEMPT.fullmatch(entry.name)[1]))
    attempts, seen_raw = [], set()
    for index, folder in enumerate(entries, 1):
        if folder.name != f"attempt-{index:04d}":
            raise ValueError("response attempt sequence is incomplete or renumbered")
        expected_files = {"response.raw", "metadata.raw.json", "metadata.json", "parsed.json", "attempt.json"}
        if {path.name for path in folder.iterdir()} != expected_files or any(path.is_symlink() or not path.is_file() for path in folder.iterdir()):
            raise ValueError("response attempt is incomplete or contains unexpected artifacts")
        record_bytes = (folder / "attempt.json").read_bytes()
        record = _strict_json(record_bytes)
        raw = (folder / "response.raw").read_bytes()
        metadata_raw = (folder / "metadata.raw.json").read_bytes()
        metadata = _validate_metadata(metadata_raw, pilot, request)
        parsed = _parse_acquired(raw, request, metadata, pilot)
        expected = _attempt_record(root, folder, pilot, request, index, raw, metadata_raw, metadata, parsed, record["imported_utc"])
        if record != expected or record_bytes != _json_bytes(expected):
            raise ValueError("response attempt metadata or hashes were altered")
        if (folder / "metadata.json").read_bytes() != _json_bytes(metadata) or (folder / "parsed.json").read_bytes() != _json_bytes(parsed):
            raise ValueError("response parsed metadata does not match its raw original")
        if record["raw_response_sha256"] in seen_raw:
            raise ValueError("duplicate raw response in the same request")
        seen_raw.add(record["raw_response_sha256"])
        attempts.append({**record, "attempt_manifest_sha256": _sha(record_bytes), "metadata": metadata})
    return attempts


def _attempt_record(root, folder, pilot, request, index, raw, metadata_raw, metadata, parsed, imported_utc):
    imported = datetime.fromisoformat(imported_utc)
    if imported.utcoffset() is None:
        raise ValueError("attempt import timestamp must include a timezone")
    files = {"raw_response": ("response.raw", raw), "raw_metadata": ("metadata.raw.json", metadata_raw),
             "metadata": ("metadata.json", _json_bytes(metadata)), "parsed": ("parsed.json", _json_bytes(parsed))}
    return {"schema_version": ATTEMPT_SCHEMA, "request_key": request["request_key"], "request_id": request["request_id"],
            "cohort": pilot["cohort"], "protocol_sha256": pilot["protocol_sha256"], "prompt_sha256": request["prompt_sha256"],
            "attempt_id": folder.name, "attempt_index": index, "imported_utc": imported_utc,
            "status": parsed["status"], "selected_candidate_id": parsed["selected_candidate_id"], "invalid_reason": parsed["invalid_reason"],
            "raw_response_sha256": _sha(raw), "raw_metadata_sha256": _sha(metadata_raw),
            "metadata_sha256": _sha(_json_bytes(metadata)), "parsed_sha256": _sha(_json_bytes(parsed)),
            "files": {key: {"path": str((folder / filename).relative_to(root)), "sha256": _sha(data)} for key, (filename, data) in files.items()}}


def import_response(pilot_dir, request_key, raw_path, metadata_path):
    """Retain one immutable attempt; metadata errors do not create an attempt."""
    root, pilot, protocol = _context(pilot_dir)
    if (root / "freeze.json").exists():
        raise ValueError("responses are frozen; imports require a new pilot")
    request = next((item for item in protocol["requests"] if item["request_key"] == request_key), None)
    if request is None:
        raise ValueError("unknown request_key")
    raw, metadata_raw = Path(raw_path).read_bytes(), Path(metadata_path).read_bytes()
    metadata = _validate_metadata(metadata_raw, pilot, request)
    parsed = _parse_acquired(raw, request, metadata, pilot)
    existing = _load_attempts(root, pilot, request)
    if any(item["raw_response_sha256"] == _sha(raw) for item in existing):
        raise ValueError("duplicate raw response for this request; no attempt was written")
    index = len(existing) + 1
    directory = _request_directory(root, request_key)
    directory.mkdir(parents=True, exist_ok=True)
    folder = directory / f"attempt-{index:04d}"
    folder.mkdir(exist_ok=False)
    record = _attempt_record(root, folder, pilot, request, index, raw, metadata_raw, metadata, parsed,
                             datetime.now(timezone.utc).isoformat())
    contents = {"response.raw": raw, "metadata.raw.json": metadata_raw, "metadata.json": _json_bytes(metadata),
                "parsed.json": _json_bytes(parsed), "attempt.json": _json_bytes(record)}
    for filename, data in contents.items():
        with (folder / filename).open("xb") as stream:
            stream.write(data)
    return {**record, "attempt_manifest_sha256": _sha(contents["attempt.json"]), "metadata": metadata, "primary_attempt": index == 1}


def collect_responses(pilot_dir):
    """Return a deterministic freeze snapshot, selecting only each first attempt."""
    root, pilot, protocol = _context(pilot_dir)
    rows, attempts = [], []
    response_root = root / "responses"
    if response_root.is_symlink():
        raise ValueError("response directories cannot be symbolic links")
    known = {request["request_key"] for request in protocol["requests"]}
    if response_root.exists() and any(path.name not in known for path in response_root.iterdir()):
        raise ValueError("responses contain an unknown request directory")
    for request in protocol["requests"]:
        imported = _load_attempts(root, pilot, request)
        attempts.extend(imported)
        first = imported[0] if imported else None
        rows.append({"request_key": request["request_key"], "status": first["status"] if first else "missing",
                     "selected_candidate_id": first["selected_candidate_id"] if first else None,
                     "attempt_id": first["attempt_id"] if first else None,
                     "invalid_reason": first["invalid_reason"] if first else None,
                     "raw_response_sha256": first["raw_response_sha256"] if first else None,
                     "metadata": first["metadata"] if first else None})
    counts = {status: sum(row["status"] == status for row in rows) for status in ("valid", "invalid", "missing")}
    counts.update(received=counts["valid"] + counts["invalid"], total=len(rows))
    return {"cohort": pilot["cohort"], "protocol_sha256": pilot["protocol_sha256"],
            "primary_attempt_policy": PRIMARY_POLICY, "requests": rows, "counts": counts, "attempts": attempts}
