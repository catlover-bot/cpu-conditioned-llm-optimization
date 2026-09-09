"""Append-only manual pilot lifecycle: export, collect, freeze, then measure.

This module never queries an LLM. Real answers must come from independent,
tool-free sessions; synthetic answers exercise software only.
"""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from .diagnostic_config import load_config
from .diagnostics import run_diagnostics
from .experiment import audit_artifacts, git_state
from .host import discover_compiler, observe_host


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value, *, exclusive=False):
    with Path(path).open("x" if exclusive else "w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def unique_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]


def child(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("artifact path must remain within the pilot directory")
    return path


@contextmanager
def mutation_lock(directory):
    with (Path(directory) / ".pilot.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another pilot mutation is active") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def check_static(directory):
    """Validate the sealed task without consulting responses or measurements."""
    from .selection_protocol import validate_protocol
    directory = Path(directory)
    pilot = read_json(directory / "pilot.json")
    if pilot["schema_version"] != "3.0" or pilot["cohort"] not in ("real", "synthetic"):
        raise ValueError("unsupported pilot schema or cohort")
    if digest(directory / "protocol.json") != pilot["protocol_sha256"]:
        raise ValueError("protocol changed after export")
    if digest(directory / "static-manifest.json") != pilot["static_manifest_sha256"]:
        raise ValueError("static manifest changed after export")
    manifest = read_json(directory / "static-manifest.json")
    expected = {"protocol.json", "provenance.json"}
    for folder in ("sources", "requests", "runner_source"):
        expected.update(str(path.relative_to(directory)) for path in (directory / folder).rglob("*") if path.is_file())
    if set(manifest) != expected or not (directory / "runner_source/selection.py").is_file():
        raise ValueError("static manifest/source provenance is incomplete or contains unexpected files")
    for path, expected in manifest.items():
        if digest(child(directory, path)) != expected:
            raise ValueError(f"sealed task artifact changed: {path}")
    protocol = read_json(directory / "protocol.json")
    if protocol["export_cohort"] != pilot["cohort"]:
        raise ValueError("real and synthetic cohorts must remain separate")
    errors = validate_protocol(directory)
    if errors:
        raise ValueError("invalid frozen task: " + "; ".join(errors))


def _measurement_identity(protocol, record, binding):
    from .selection_protocol import host_fingerprint
    if host_fingerprint(record["host"]) != protocol["current_target_host"]:
        raise ValueError("measured host differs from the fixed target")
    if record["git"] != binding["git"]:
        raise ValueError("measurement code provenance differs from scoring invocation")
    if record["run_id"] != binding["measurement_run_id"]:
        raise ValueError("shared measurement run ID differs")


def _source_snapshot(directory):
    package = Path(__file__).resolve().parent
    snapshot = directory / "runner_source"
    snapshot.mkdir()
    for source in sorted(package.glob("*.py")):
        shutil.copyfile(source, snapshot / source.name)
    shutil.copyfile(package.parents[1] / "pyproject.toml", snapshot / "pyproject.toml")


def _assert_runner_snapshot(directory):
    package = Path(__file__).resolve().parent
    snapshot = directory / "runner_source"
    expected = {p.name for p in package.glob("*.py")} | {"pyproject.toml"}
    if {p.name for p in snapshot.iterdir()} != expected:
        raise ValueError("runner source set changed; export a new protocol")
    for saved in snapshot.iterdir():
        current = package.parents[1] / saved.name if saved.name == "pyproject.toml" else package / saved.name
        if saved.read_bytes() != current.read_bytes():
            raise ValueError("runner code changed since task export; export a new protocol")


def _preflight(protocol):
    from .selection_protocol import host_fingerprint
    compiler = json.loads(json.dumps(asdict(discover_compiler(protocol["compiler"]["compiler"]))))
    if compiler != protocol["compiler"]:
        raise ValueError("CompilerTarget differs from the frozen protocol; create a new protocol")
    observed = json.loads(json.dumps(asdict(observe_host())))
    fingerprint = host_fingerprint(observed)
    if fingerprint != protocol["current_target_host"] or fingerprint != protocol["source_target_host"]:
        raise ValueError("observed target differs from protocol/source host; create a protocol on the intended host")
    return {"checked_utc": now(), "compiler": compiler, "host": observed,
            "host_identity_scope": "Matching observed guest attributes, not proof of physical machine identity."}


def prepare_pilot(output, source_run, *, config=None, cohort="real"):
    from .selection_protocol import export_protocol
    if cohort not in ("real", "synthetic"):
        raise ValueError("cohort must be real or synthetic")
    source_run = Path(source_run).resolve()
    directory = Path(output).resolve() / cohort / unique_id()
    if directory.is_relative_to(source_run):
        raise ValueError("pilot output must not modify or be inside the source run")
    directory.mkdir(parents=True, exist_ok=False)
    protocol = export_protocol(directory, source_run=source_run, config=config, cohort=cohort)
    observed = _preflight(protocol)
    _source_snapshot(directory)
    write_json(directory / "provenance.json", {"created_utc": now(), "git": git_state(Path(__file__).resolve().parent),
               "preflight": observed, "environment_role": "development_smoke", "publishable_benchmark": False}, exclusive=True)
    for request in protocol["requests"]:
        child(directory, request["raw_response_path"]).parent.mkdir(parents=True, exist_ok=True)
    manifest = read_json(directory / "static-manifest.json")
    for path in [directory / "provenance.json", *(directory / "runner_source").iterdir()]:
        manifest[str(path.relative_to(directory))] = digest(path)
    write_json(directory / "static-manifest.json", manifest)
    write_json(directory / "pilot.json", {"schema_version": "3.0", "pilot_id": directory.name,
               "cohort": cohort, "created_utc": now(), "protocol_sha256": digest(directory / "protocol.json"),
               "static_manifest_sha256": digest(directory / "static-manifest.json"), "software_ready": True,
               "status": "awaiting_real_responses" if cohort == "real" else "software_ready",
               "collection_state": "open", "environment_role": "development_smoke", "publishable_benchmark": False,
               "llm_api_called": False}, exclusive=True)
    check_static(directory)
    return directory, pilot_status(directory)


def _status_from(pilot, snapshot, *, scored=False):
    if pilot["cohort"] == "synthetic":
        return "software_ready"
    if snapshot["counts"]["received"] == 0:
        return "awaiting_real_responses"
    if scored and snapshot["counts"]["valid"] == snapshot["counts"]["total"]:
        return "real_pilot_complete"
    return "real_pilot_partial"


def pilot_status(directory):
    from .selection_responses import collect_responses
    directory = Path(directory)
    check_static(directory)
    pilot = read_json(directory / "pilot.json")
    snapshot = collect_responses(directory)
    scored = (directory / "score.json").is_file()
    if scored:
        score = read_json(directory / "score.json")
        if score["status"] != "completed" or digest(directory / "score.json") != pilot.get("score_sha256"):
            raise ValueError("score is incomplete or changed; no completed pilot status is available")
    return {"pilot_directory": str(directory.resolve()), "software_ready": True,
            "status": _status_from(pilot, snapshot, scored=scored), "cohort": pilot["cohort"],
            "collection_state": "frozen" if (directory / "freeze.json").exists() else "open",
            "scored": scored, "counts": snapshot["counts"],
            "real_response_count": snapshot["counts"]["received"] if pilot["cohort"] == "real" else 0,
            "synthetic_response_count": snapshot["counts"]["received"] if pilot["cohort"] == "synthetic" else 0,
            "environment_role": "development_smoke", "publishable_benchmark": False}


def import_answer(directory, request_key, response, metadata):
    from .selection_responses import import_response
    directory = Path(directory)
    with mutation_lock(directory):
        check_static(directory)
        attempt = import_response(directory, request_key, response, metadata)
        status = pilot_status(directory)
        pilot = read_json(directory / "pilot.json")
        pilot["status"] = status["status"]
        write_json(directory / "pilot.json", pilot)
        return {"attempt": attempt, "pilot": status}


def freeze_answers(directory):
    from .selection_responses import collect_responses
    directory = Path(directory)
    with mutation_lock(directory):
        check_static(directory)
        if (directory / "freeze.json").exists():
            raise ValueError("answers already frozen; create a separate pilot for new answers")
        snapshot = collect_responses(directory)
        if not snapshot["counts"]["received"]:
            raise ValueError("cannot freeze an empty response collection")
        snapshot["frozen_utc"] = now()
        snapshot["primary_attempt_policy"] = "first_attempt_only"
        write_json(directory / "freeze.json", snapshot, exclusive=True)
        pilot = read_json(directory / "pilot.json")
        pilot.update(freeze_sha256=digest(directory / "freeze.json"), collection_state="frozen",
                     status=_status_from(pilot, snapshot))
        write_json(directory / "pilot.json", pilot)
        return snapshot


def check_freeze(directory):
    from .selection_responses import collect_responses
    directory = Path(directory)
    check_static(directory)
    pilot = read_json(directory / "pilot.json")
    if "freeze_sha256" not in pilot or digest(directory / "freeze.json") != pilot["freeze_sha256"]:
        raise ValueError("answers are not frozen or the freeze changed")
    frozen = read_json(directory / "freeze.json")
    reconstructed = collect_responses(directory)
    if any(frozen.get(key) != value for key, value in reconstructed.items()):
        raise ValueError("responses/attempts changed after freeze")
    return frozen


def score_pilot(directory):
    """Only create a fresh local diagnostic after freezing; no old-run argument."""
    from .selection_scoring import score_selection, write_selection_reports
    directory = Path(directory).resolve()
    with mutation_lock(directory):
        frozen = check_freeze(directory)
        if (directory / "score.json").exists():
            raise ValueError("pilot already scored; refusing replacement or repeated selection of results")
        _assert_runner_snapshot(directory)
        protocol = read_json(directory / "protocol.json")
        preflight = _preflight(protocol)
        attempt = directory / "scoring-attempts" / unique_id()
        attempt.mkdir(parents=True, exist_ok=False)
        binding = {"status": "running", "started_utc": now(), "cohort": frozen["cohort"],
                   "protocol_sha256": digest(directory / "protocol.json"),
                   "freeze_sha256": digest(directory / "freeze.json"), "preflight": preflight,
                   "git": git_state(Path(__file__).resolve().parent),
                   "scored_phase": "confirmation", "unscored_phase": "exploration",
                   "scope": "One fresh shared measurement run; all response and offline policy scores share it."}
        write_json(attempt / "attempt.json", binding, exclusive=True)
        try:
            write_json(attempt / "measurement-config.json", protocol["measurement_config"], exclusive=True)
            config = load_config(attempt / "measurement-config.json")
            measured_dir, record = run_diagnostics(attempt / "measurements", config=config,
                                                 compiler=protocol["compiler"]["compiler"],
                                                 specification=protocol["cpu_context"]["text"],
                                                 cpu=protocol["target"]["measurement_cpu"])
            binding.update(measurement_directory=str(measured_dir.relative_to(directory)),
                           measurement_run_id=record["run_id"], measurement_sha256=digest(measured_dir / "experiment.json"))
            errors = audit_artifacts(measured_dir)
            if record["status"] != "completed" or errors:
                raise ValueError("new independent diagnostic failed: " + "; ".join(errors))
            _measurement_identity(protocol, record, binding)
            if check_freeze(directory) != frozen:
                raise ValueError("answers changed during measurement")
            report = score_selection(protocol, frozen, record)
            files = write_selection_reports(attempt, report)
            binding.update(status="completed", completed_utc=now(), reports={key: str((attempt / path).relative_to(directory)) for key, path in files.items()})
            binding["report_hashes"] = {path: digest(directory / path) for path in binding["reports"].values()}
            write_json(attempt / "attempt.json", binding)
            write_json(directory / "score.json", {"attempt_path": str((attempt / "attempt.json").relative_to(directory)),
                       "attempt_sha256": digest(attempt / "attempt.json"), **binding}, exclusive=True)
            pilot = read_json(directory / "pilot.json")
            pilot.update(status=_status_from(pilot, frozen, scored=True), score_sha256=digest(directory / "score.json"))
            write_json(directory / "pilot.json", pilot)
            checked = check_pilot(directory)
            if not checked["passed"]:
                raise ValueError("scored pilot audit failed: " + "; ".join(checked["errors"]))
            return {"pilot": pilot_status(directory), "score": binding}
        except BaseException as exc:
            binding.update(status="failed", completed_utc=now(), failure={"category": type(exc).__name__, "reason": str(exc)})
            write_json(attempt / "attempt.json", binding)
            raise


def synthetic_answers(directory):
    """Deterministic plumbing fixtures; never an experimental LLM participant."""
    directory = Path(directory)
    check_static(directory)
    pilot, protocol = read_json(directory / "pilot.json"), read_json(directory / "protocol.json")
    if pilot["cohort"] != "synthetic":
        raise ValueError("synthetic fixtures cannot be imported into a real pilot")
    results = []
    for index, request in enumerate(protocol["requests"]):
        raw = child(directory, request["raw_response_path"])
        metadata_path = child(directory, request["metadata_path"])
        # Choose presentation positions without consulting any measured results.
        option = list(request["option_mapping"])[index % 5]
        write_json(raw, {"request_id": request["request_id"], "selected_option_id": option,
                        "rationale_short": "Synthetic software fixture; no LLM response."}, exclusive=True)
        metadata = read_json(child(directory, request["metadata_template_path"]))
        metadata.update(cohort="synthetic", acquisition_method="synthetic_fixture", obtained_at=now(),
                        acquisition_source="cpucond pilot synthetic: deterministic software fixture")
        metadata["missing_reasons"].pop("obtained_at", None)
        metadata["missing_reasons"].pop("acquisition_source", None)
        metadata["blinding"]["limitations"] = ["Synthetic software fixture; no real LLM session or blinding was evaluated."]
        write_json(metadata_path, metadata, exclusive=True)
        results.append(import_answer(directory, request["request_key"], raw, metadata_path)["attempt"])
    return {"imported_synthetic_attempts": len(results), "pilot": pilot_status(directory)}


def check_pilot(directory):
    """Reconstruct primary responses and reports, including fresh-run lineage."""
    from .selection_scoring import score_selection, write_selection_reports
    import tempfile
    directory = Path(directory).resolve()
    errors = []
    try:
        status = pilot_status(directory)
        pilot = read_json(directory / "pilot.json")
        if pilot["status"] != status["status"] or pilot["collection_state"] != status["collection_state"]:
            raise ValueError("pilot status differs from response/score evidence")
        if (directory / "freeze.json").exists():
            frozen = check_freeze(directory)
        if (directory / "score.json").exists():
            score = read_json(directory / "score.json")
            attempt_path = child(directory, score["attempt_path"])
            if digest(directory / "score.json") != pilot["score_sha256"] or digest(attempt_path) != score["attempt_sha256"]:
                raise ValueError("scoring record changed")
            if {k: v for k, v in score.items() if k not in ("attempt_path", "attempt_sha256")} != read_json(attempt_path):
                raise ValueError("score/attempt metadata differ")
            if score["status"] != "completed" or score["freeze_sha256"] != pilot["freeze_sha256"] or score["protocol_sha256"] != pilot["protocol_sha256"]:
                raise ValueError("score is not bound to the frozen task and answers")
            if datetime.fromisoformat(score["started_utc"]) < datetime.fromisoformat(frozen["frozen_utc"]):
                raise ValueError("measurement was started before response freeze")
            measured_dir = child(directory, score["measurement_directory"])
            if not measured_dir.is_relative_to(attempt_path.parent / "measurements"):
                raise ValueError("measurement was not created inside this scoring attempt")
            if digest(measured_dir / "experiment.json") != score["measurement_sha256"]:
                raise ValueError("shared measurement changed")
            errors.extend(audit_artifacts(measured_dir))
            record = read_json(measured_dir / "experiment.json")
            protocol = read_json(directory / "protocol.json")
            _measurement_identity(protocol, record, score)
            rebuilt = score_selection(protocol, frozen, record)
            with tempfile.TemporaryDirectory(prefix="cpucond-pilot-audit-") as temporary:
                generated = write_selection_reports(Path(temporary), rebuilt)
                for key, filename in generated.items():
                    saved = child(directory, score["reports"][key])
                    if digest(saved) != score["report_hashes"][score["reports"][key]] or saved.read_bytes() != (Path(temporary) / filename).read_bytes():
                        raise ValueError("policy report does not match raw frozen answers and shared measurements")
        return {"passed": not errors, "errors": errors, "pilot": status}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        return {"passed": False, "errors": [*errors, str(exc)]}
