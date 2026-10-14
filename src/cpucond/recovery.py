"""Explicit, append-only recovery of a failed local pilot's acquired answers.

The acquisition protocol and response bytes are reused unchanged. Only runner
provenance and a new freeze/measurement event sequence are created. This is not
another independent response cohort, and never regenerates an answer.
"""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import fcntl
from pathlib import Path
import shutil
import sys

from .clock_provenance import event_fields
from .experiment import git_state
from . import selection as lifecycle

MARKER = "local-evidence/reused-acquisition.json"
ORIGIN = "local-evidence/recovery-origin"
SCHEMA = "cpucond.local-answer-recovery.v1"


def tree_hashes(directory):
    """Hash regular files, rejecting links; never include the coordination lock."""
    root = Path(directory)
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"recovery refuses symbolic links: {path}")
        if path.is_file() and path.relative_to(root).as_posix() != ".pilot.lock":
            result[path.relative_to(root).as_posix()] = lifecycle.digest(path)
    return result


@contextmanager
def _read_lock(source):
    # Normal pilots already have this lock. Opening read-only leaves all source
    # bytes unchanged; a concurrent mutation is refused, not overwritten.
    lock = source / ".pilot.lock"
    if not lock.exists():
        yield
        return
    with lock.open("rb") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("source pilot is being modified; recovery stopped") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _failed_score_evidence(source, frozen):
    """Require an actual failed score, not a completed result to cherry-pick."""
    pointer = source / "score.json"
    if not pointer.is_file():
        raise ValueError("this recovery requires the preserved failed score.json")
    score = lifecycle.read_json(pointer)
    attempt_path = lifecycle.child(source, score["attempt_path"])
    attempt = lifecycle.read_json(attempt_path)
    failure = attempt.get("failure", {})
    if attempt.get("status") != "failed":
        raise ValueError("refusing to replace a successful or running scoring attempt")
    if ("before response freeze" not in failure.get("reason", "")
            and "before responses were frozen" not in failure.get("reason", "")):
        raise ValueError("source failure is not the reviewed freeze/score clock-order failure")
    if not datetime.fromisoformat(score["started_utc"]) < datetime.fromisoformat(frozen["frozen_utc"]):
        raise ValueError("source lacks the recorded freeze-to-score UTC reversal")
    return {"score_path": "score.json", "attempt_path": str(attempt_path.relative_to(source)),
            "failure": failure, "source_score_is_not_accepted": True}


def prepare_recovery(output, source_pilot):
    """Audit raw source evidence and copy it unchanged, without HTTP or inference."""
    from .local_llm import audit_local
    from .selection_responses import collect_responses

    source = Path(source_pilot).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError("recovery output cannot be inside the source pilot")
    if (source / MARKER).exists():
        raise ValueError("use the original failed pilot, not a nested recovery")
    with _read_lock(source):
        before = tree_hashes(source)
        frozen = lifecycle.check_freeze(source)  # Raw answers + API evidence, not the broken score pointer.
        old = lifecycle.read_json(source / "pilot.json")
        if old.get("cohort") != "real" or old.get("acquisition_backend") != "ollama_local":
            raise ValueError("recovery requires a real ollama_local source")
        audit = audit_local(source)
        if not audit.get("passed"):
            raise ValueError("source acquisition audit failed: " + "; ".join(audit.get("errors", [])))
        failure = _failed_score_evidence(source, frozen)
        protocol = lifecycle.read_json(source / "protocol.json")
        observed = lifecycle._preflight(protocol)  # Keep the actual target/compiler unchanged.
        directory = output / "local" / lifecycle.unique_id()
        directory.mkdir(parents=True, exist_ok=False)
        for name in ("sources", "requests", "local-evidence", "local-acquisition", "responses"):
            folder = source / name
            if folder.exists():
                shutil.copytree(folder, directory / name)
        shutil.copyfile(source / "protocol.json", directory / "protocol.json")
        saved = directory / ORIGIN
        saved.mkdir(parents=True, exist_ok=False)
        for name in ("protocol.json", "pilot.json", "freeze.json", "static-manifest.json", "provenance.json", "score.json"):
            shutil.copyfile(source / name, saved / name)
        shutil.copyfile(lifecycle.child(source, failure["attempt_path"]), saved / "failed-attempt.json")
        shutil.copytree(source / "runner_source", saved / "runner_source")
        copied = {path: value for path, value in before.items()
                  if path.startswith(("sources/", "requests/", "local-acquisition/", "responses/"))}
        origin_hashes = {p.relative_to(directory).as_posix(): lifecycle.digest(p)
                         for p in saved.rglob("*") if p.is_file()}
        marker = {"schema_version": SCHEMA, **event_fields("copied"),
                  "source_directory": str(source), "source_pilot_id": old["pilot_id"],
                  "source_protocol_sha256": lifecycle.digest(source / "protocol.json"),
                  "source_freeze_sha256": lifecycle.digest(source / "freeze.json"),
                  "source_tree_sha256": before, "reused_file_sha256": copied,
                  "origin_snapshot_sha256": origin_hashes,
                  "original_counts": frozen["counts"], "failed_score": failure,
                  "interpretation": "Identical acquired answers, not new independent LLM observations. Failed scores are retained only as provenance, never used for ranking.",
                  "new_model_requests": 0, "old_times_rewritten": False}
        lifecycle.write_json(directory / MARKER, marker, exclusive=True)
        lifecycle._source_snapshot(directory)
        lifecycle.write_json(directory / "provenance.json", {
            **event_fields("created"), "git": git_state(Path(__file__).resolve().parent),
            "preflight": observed, "acquisition_backend": "ollama_local", "recovery_lineage": MARKER,
            "environment_role": "development_smoke", "publishable_benchmark": False,
        }, exclusive=True)
        manifest = tree_hashes(directory)
        lifecycle.write_json(directory / "static-manifest.json", {
            key: value for key, value in manifest.items()
            if key == "protocol.json" or key == "provenance.json"
            or key.startswith(("sources/", "requests/", "runner_source/", "local-evidence/"))
        }, exclusive=True)
        pilot = {key: deepcopy(value) for key, value in old.items()
                 if key not in ("freeze_sha256", "score_sha256")}
        pilot.update(pilot_id=directory.name, created_utc=lifecycle.now(),
                     static_manifest_sha256=lifecycle.digest(directory / "static-manifest.json"),
                     collection_state="open", status="real_pilot_partial", reused_acquisition=True,
                     new_model_requests=0)
        lifecycle.write_json(directory / "pilot.json", pilot, exclusive=True)
        lifecycle.check_static(directory)
        restored = collect_responses(directory)
        for key, value in restored.items():
            if frozen.get(key) != value:
                raise ValueError(f"recovery changed frozen response evidence: {key}")
        if not audit_local(directory)["passed"]:
            raise ValueError("copied local acquisition did not pass audit")
        if tree_hashes(source) != before:
            raise ValueError("source pilot changed during recovery; copied run is not accepted")
        lifecycle.write_json(directory / "recovery-state.json", {
            "stage": "prepared", "source_unchanged": True, "new_model_requests": 0,
            "original_counts": frozen["counts"], "lineage": MARKER,
        }, exclusive=True)
        return directory


def validate_recovery_lineage(directory):
    """Validate inherited answers on every static check; no recursive lifecycle calls."""
    directory = Path(directory)
    marker = lifecycle.read_json(directory / MARKER)
    if (marker.get("schema_version") != SCHEMA or marker.get("new_model_requests") != 0
            or marker.get("old_times_rewritten") is not False):
        raise ValueError("invalid recovery lineage")
    if lifecycle.digest(directory / "protocol.json") != marker["source_protocol_sha256"]:
        raise ValueError("recovery changed the acquisition protocol")
    for path, expected in {**marker["origin_snapshot_sha256"], **marker["reused_file_sha256"]}.items():
        if lifecycle.digest(lifecycle.child(directory, path)) != expected:
            raise ValueError(f"reused original evidence changed: {path}")
    if lifecycle.digest(directory / ORIGIN / "freeze.json") != marker["source_freeze_sha256"]:
        raise ValueError("original freeze snapshot changed")
    frozen = lifecycle.read_json(directory / ORIGIN / "freeze.json")
    if frozen["counts"] != marker["original_counts"]:
        raise ValueError("original response counts changed")
    # Responses/preflight/acquired payloads are fixed. Only a newly observed
    # unload may be appended before the new recovery freeze.
    for folder in ("responses", "local-acquisition"):
        for relative in tree_hashes(directory / folder):
            full = folder + "/" + relative
            if full not in marker["reused_file_sha256"] and not full.startswith("local-acquisition/unloads/"):
                raise ValueError(f"new answer/acquisition artifact in a recovery: {full}")


def recover_local(output, source_pilot, *, prepare_only=False):
    """Fresh unload + freeze + score; no code path can ask the model a question."""
    from .local_llm import unload_local
    source = Path(source_pilot).resolve()
    completed = []
    for state_path in sorted((Path(output).resolve() / "local").glob("*/recovery-state.json")):
        state = lifecycle.read_json(state_path)
        marker_path = state_path.parent / MARKER
        if state.get("stage") == "completed" and marker_path.exists():
            prior = lifecycle.read_json(marker_path)
            if prior.get("source_directory") == str(source):
                completed.append((state_path.parent, state, prior))
    if len(completed) > 1:
        raise ValueError("multiple completed recoveries exist; refusing to select a preferred result")
    if completed:
        prior_dir, state, prior = completed[0]
        checked = lifecycle.check_pilot(prior_dir)
        if not checked["passed"] or tree_hashes(source) != prior["source_tree_sha256"]:
            raise ValueError("existing recovery or original source no longer passes audit")
        return {"passed": True, **state, "reused_existing_completed_recovery": True}
    directory = prepare_recovery(output, source_pilot)
    print(f"Recovery pilot: {directory}", file=sys.stderr, flush=True)
    marker = lifecycle.read_json(directory / MARKER)
    try:
        if prepare_only:
            return {"passed": True, "stage": "prepared", "pilot_directory": str(directory),
                    "counts": marker["original_counts"], "new_model_requests": 0}
        # This uses the original verified local endpoint and PID. A stopped or
        # replaced server is a blocker, not a reason to fake an unload record.
        unload_local(directory)
        lifecycle.freeze_answers(directory)
        result = lifecycle.score_pilot(directory)
        checked = lifecycle.check_pilot(directory)
        if not checked["passed"]:
            raise ValueError("recovered score audit failed: " + "; ".join(checked["errors"]))
        if tree_hashes(Path(source_pilot).resolve()) != marker["source_tree_sha256"]:
            raise ValueError("original pilot changed during recovery execution")
        state = {"stage": "completed", "source_unchanged": True, "new_model_requests": 0,
                 "pilot_directory": str(directory), "counts": result["pilot"]["counts"],
                 "reports": result["score"]["reports"], "lineage": MARKER,
                 "independent_new_response_cohort": False}
        lifecycle.write_json(directory / "recovery-state.json", state)
        return {"passed": True, **state}
    except BaseException as exc:
        lifecycle.write_json(directory / "recovery-failure.json", {
            "category": type(exc).__name__, "reason": str(exc),
            "source_unchanged": tree_hashes(Path(source_pilot).resolve()) == marker["source_tree_sha256"],
            "new_model_requests": 0,
            "instruction": "Preserve this run; do not regenerate answers or delete failed scoring files.",
        }, exclusive=True)
        raise
