"""Create a separately sealed real-local cohort from an existing manual task."""

from copy import deepcopy
from pathlib import Path
import shutil

from .experiment import git_state
from .selection import (check_static, child, digest, now, pilot_status, read_json,
                        unique_id, write_json, _preflight, _source_snapshot)


BACKEND = "ollama_local"


def prepare_local_pilot(output, source_pilot, local_config, *, evidence_files=()):
    """Copy the source task bytes and fix acquisition settings before any answers.

    The existing real/synthetic schema is retained: this is a new real cohort
    with an explicit local backend, unique path, and independently frozen data.
    Evidence files are explicit small files, never model directories.
    """
    from .local_llm import validate_local_config
    source = Path(source_pilot).resolve()
    check_static(source)
    original = read_json(source / "protocol.json")
    if original["export_cohort"] != "real" or original.get("acquisition_backend") is not None:
        raise ValueError("local cohorts require an existing manual real task as their source")
    validate_local_config(local_config)
    _check_task_output_pair(original, local_config)
    inputs = [Path(path).resolve() for path in evidence_files]
    if any(not path.is_file() or path.is_symlink() for path in inputs):
        raise ValueError("setup evidence must be explicitly named regular files")
    directory = Path(output).resolve() / "local" / unique_id()
    if directory.is_relative_to(source):
        raise ValueError("local cohort must not be written inside the source pilot")
    protocol = deepcopy(original)
    protocol.update(acquisition_backend=BACKEND, local_llm=deepcopy(local_config),
                    protocol_revision=("goal0032-explicit-latency-v1" if original.get("prompt_revision") else "goal003.1-local-v1"))
    preflight = _preflight(protocol)
    directory.mkdir(parents=True, exist_ok=False)
    for folder in ("sources", "requests"):
        shutil.copytree(source / folder, directory / folder)
    saved_source = directory / "local-evidence" / "source-pilot"
    saved_source.mkdir(parents=True)
    for filename in ("protocol.json", "pilot.json", "static-manifest.json", "provenance.json"):
        shutil.copyfile(source / filename, saved_source / filename)
    setup = []
    for index, path in enumerate(inputs):
        destination = directory / "local-evidence" / "setup" / f"{index:03d}-{path.name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        setup.append({"source_path": str(path), "path": destination.relative_to(directory).as_posix(),
                      "sha256": digest(destination)})
    protocol["source_pilot"] = {
        "path": str(source), "pilot_id": read_json(source / "pilot.json")["pilot_id"],
        "protocol_sha256": digest(source / "protocol.json"),
        "static_manifest_sha256": digest(source / "static-manifest.json"),
        "snapshot_path": "local-evidence/source-pilot",
        "reused_artifacts": {path.relative_to(source).as_posix(): digest(path)
                             for folder in ("sources", "requests")
                             for path in sorted((source / folder).rglob("*")) if path.is_file()},
        "scope": "Exact prompt, common payload, metadata-template and C source bytes; responses and measurements were not copied.",
    }
    protocol["local_setup_evidence"] = setup
    write_json(directory / "protocol.json", protocol, exclusive=True)
    _source_snapshot(directory)
    write_json(directory / "provenance.json", {
        "created_utc": now(), "git": git_state(Path(__file__).resolve().parent),
        "preflight": preflight, "acquisition_backend": BACKEND,
        "source_pilot": deepcopy(protocol["source_pilot"]),
        "environment_role": "development_smoke", "publishable_benchmark": False,
    }, exclusive=True)
    for request in protocol["requests"]:
        child(directory, request["raw_response_path"]).parent.mkdir(parents=True, exist_ok=True)
    manifest = {path.relative_to(directory).as_posix(): digest(path)
                for path in sorted(directory.rglob("*")) if path.is_file()}
    write_json(directory / "static-manifest.json", manifest, exclusive=True)
    write_json(directory / "pilot.json", {
        "schema_version": "3.0", "pilot_id": directory.name, "cohort": "real",
        "acquisition_backend": BACKEND, "created_utc": now(),
        "protocol_sha256": digest(directory / "protocol.json"),
        "static_manifest_sha256": digest(directory / "static-manifest.json"),
        "software_ready": True, "status": "awaiting_real_responses", "collection_state": "open",
        "environment_role": "development_smoke", "publishable_benchmark": False, "llm_api_called": False,
    }, exclusive=True)
    check_static(directory)
    return directory, pilot_status(directory)


def validate_local_protocol(directory, protocol):
    """Verify copied task lineage without requiring the source directory to exist."""
    from .local_llm import validate_local_config
    directory = Path(directory)
    if protocol.get("acquisition_backend") != BACKEND or protocol["export_cohort"] != "real":
        raise ValueError("local backend must belong to a separate real cohort")
    validate_local_config(protocol["local_llm"])
    _check_task_output_pair(protocol, protocol["local_llm"])
    lineage = protocol["source_pilot"]
    snapshot = child(directory, lineage["snapshot_path"])
    if digest(snapshot / "protocol.json") != lineage["protocol_sha256"]:
        raise ValueError("source pilot protocol snapshot changed")
    if digest(snapshot / "static-manifest.json") != lineage["static_manifest_sha256"]:
        raise ValueError("source pilot manifest snapshot changed")
    original = read_json(snapshot / "protocol.json")
    additions = {"acquisition_backend", "local_llm", "protocol_revision", "source_pilot", "local_setup_evidence"}
    if {key: value for key, value in protocol.items() if key not in additions} != original:
        raise ValueError("the local task changed conditions inherited from the manual pilot")
    if original["export_cohort"] != "real" or original.get("acquisition_backend") is not None:
        raise ValueError("source task is not a manual real cohort")
    source_manifest = read_json(snapshot / "static-manifest.json")
    expected = {path: value for path, value in source_manifest.items()
                if path.startswith(("sources/", "requests/"))}
    if lineage["reused_artifacts"] != expected:
        raise ValueError("reused prompt/source lineage is incomplete")
    for path, value in expected.items():
        if digest(child(directory, path)) != value:
            raise ValueError("reused task artifact differs from its source hash")
    for item in protocol["local_setup_evidence"]:
        if digest(child(directory, item["path"])) != item["sha256"]:
            raise ValueError("local setup evidence changed")

    marker = directory / "local-evidence/reused-acquisition.json"
    if marker.exists():
        from .recovery import validate_recovery_lineage
        validate_recovery_lineage(directory)


def _check_task_output_pair(protocol, config):
    from .selection_task_v2 import PROMPT_REVISION, LOCAL_SCHEMA
    revised_task = protocol.get("prompt_revision") == PROMPT_REVISION
    revised_output = config.get("schema_version") == LOCAL_SCHEMA
    if revised_task != revised_output:
        raise ValueError("revised task and revised local decoding must be used together")
