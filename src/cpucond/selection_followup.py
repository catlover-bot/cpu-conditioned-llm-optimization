"""Prepare/run one separate prospective selection pilot. Never edits old answers."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

from . import selection as life
from . import local_llm as llm
from .local_cohort import prepare_local_pilot
from .selection_task_v2 import PROMPT_REVISION, LOCAL_SCHEMA, local_config_v2


def _require_followup(directory):
    life.check_static(directory)
    protocol = life.read_json(Path(directory) / "protocol.json")
    if (protocol.get("prompt_revision") != PROMPT_REVISION or
            protocol.get("local_llm", {}).get("schema_version") != LOCAL_SCHEMA):
        raise ValueError("this command accepts only the new explicit-latency/schema pilot")
    return protocol


def _verified_server(config):
    """Read-only discovery; never start/stop a service or rewrite an old PID."""
    pids = [config["server_pid"]]
    for process in Path("/proc").iterdir():
        if process.name.isdigit() and int(process.name) not in pids:
            try:
                if b"serve" in (process / "cmdline").read_bytes().split(b"\0"):
                    pids.append(int(process.name))
            except OSError:
                pass
    for pid in pids:
        try:
            llm.server_evidence(config["endpoint"], pid)
            return pid
        except (OSError, ValueError):
            pass
    raise ValueError("no verified local-only Ollama server owns the existing endpoint; do not download/reinstall; preserve files and report this error")


def prepare(source_pilot, output):
    source = Path(source_pilot).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError("output cannot be inside the old pilot")
    state_file = output / "followup-state.json"
    if state_file.exists():
        state = life.read_json(state_file)
        if state["source_pilot"] != str(source):
            raise ValueError("output is already bound to a different source")
        directory = Path(state["pilot_directory"])
        _require_followup(directory)
        for path, expected in state["old_source_hashes"].items():
            if life.digest(life.child(source, path)) != expected:
                raise ValueError("old source evidence changed")
        return {**{k: v for k, v in state.items() if k != "old_source_hashes"}, "existing_prepared_cohort": True}
    checked = life.check_pilot(source)
    if not checked["passed"]:
        raise ValueError("old completed pilot did not pass read-only audit")
    original = life.read_json(source / "protocol.json")
    if original.get("local_llm", {}).get("schema_version") != llm.SCHEMA:
        raise ValueError("source must be the original JSON-only local protocol")
    if not (source / "score.json").is_file():
        raise ValueError("use the completed recovery pilot, not the failed original")
    saved_hashes = {
        str(p.relative_to(source)): life.digest(p)
        for name in ("responses", "local-acquisition") for p in sorted((source / name).rglob("*"))
        if p.is_file()
    }
    for name in ("protocol.json", "pilot.json", "freeze.json", "score.json", "static-manifest.json"):
        saved_hashes[name] = life.digest(source / name)
    config = local_config_v2(original["local_llm"], _verified_server(original["local_llm"]))
    llm.validate_config(config)
    runtime = llm.verify_runtime(config, llm.OllamaClient(config["endpoint"], 30))
    output.mkdir(parents=True, exist_ok=True)
    # No measured performance is used to select a model, setting, option or order.
    task, _ = life.prepare_pilot(output / "task", Path(original["source_run"]["path"]),
                                config=deepcopy(original["config"]), cohort="real",
                                prompt_revision=PROMPT_REVISION)
    new_task = life.read_json(task / "protocol.json")
    for field in ("compiler", "reference", "candidates", "controls", "measurement_config", "cpu_context"):
        if new_task[field] != original[field]:
            raise ValueError(f"new task unexpectedly changed {field}; retain failed preparation")
    for old, new in zip(original["requests"], new_task["requests"], strict=True):
        for field in ("request_key", "request_id", "size", "trial", "condition", "option_mapping"):
            if new[field] != old[field]:
                raise ValueError(f"new task unexpectedly changed {field}")
    directory, status = prepare_local_pilot(output, task, config)
    protocol = _require_followup(directory)
    bounds = [llm.context_bound(config, r, life.child(directory, r["prompt_path"]).read_text(encoding="utf-8"))
              for r in protocol["requests"]]
    for path, expected in saved_hashes.items():
        if life.digest(life.child(source, path)) != expected:
            raise ValueError("old source changed during preparation")
    state = {"source_pilot": str(source), "pilot_directory": str(directory),
             "task_directory": str(task), "old_source_hashes": saved_hashes,
             "prompt_revision": PROMPT_REVISION, "protocol_sha256": life.digest(directory / "protocol.json"),
             "new_model_requests": 0, "old_source_unchanged": True,
             "max_context_upper_bound": max(b["required_context_upper_bound"] for b in bounds),
             "configured_context": config["options"]["num_ctx"],
             "model": config["model"], "model_digest": config["model_digest"],
             "server_pid": runtime["server"]["pid"], "counts": status["counts"]}
    life.write_json(state_file, state, exclusive=True)
    return {k: v for k, v in state.items() if k != "old_source_hashes"}


def summarize(directory):
    from .selection_responses import collect_responses
    directory = Path(directory).resolve()
    protocol = _require_followup(directory)
    snapshot = collect_responses(directory)
    by_key = {r["request_key"]: r for r in snapshot["requests"]}
    groups = []
    for size in (128, 256):
        for condition in ("none", "spec"):
            requests = [r for r in protocol["requests"] if r["size"] == size and r["condition"] == condition]
            rows = [by_key[r["request_key"]] for r in requests]
            counts = Counter(r["status"] for r in rows)
            first = sum(row["status"] == "valid" and row["selected_candidate_id"] ==
                        req["option_mapping"]["option_01"] for req, row in zip(requests, rows))
            groups.append({"size": size, "condition": condition, "planned": 5,
                           "valid": counts["valid"], "invalid": counts["invalid"], "missing": counts["missing"],
                           "first_position_among_valid": first,
                           "candidate_counts_among_valid": dict(Counter(r["selected_candidate_id"] for r in rows if r["status"] == "valid"))})
    score = life.read_json(directory / "score.json") if (directory / "score.json").exists() else None
    return {"pilot_directory": str(directory), "counts": snapshot["counts"], "groups": groups,
            "reports": None if score is None else score["reports"],
            "limitations": ["Position and option_01 identity are still confounded.",
                "Old/new differences cannot isolate objective wording from structured decoding.",
                "Schema validity does not show performance reasoning or CPU specialization.",
                "One development host, generic compiler target; no significance or cross-CPU claim."],
            "environment_role": "development_smoke", "publishable_benchmark": False}


def run(directory, timeout=1800):
    directory = Path(directory).resolve()
    _require_followup(directory)
    status = life.pilot_status(directory)
    if not status["scored"]:
        if status["collection_state"] == "open":
            print("=== Technical preflight: same new prompts, one output token; not research answers ===", flush=True)
            llm.preflight_local(directory, timeout=timeout)
            print("=== New independent responses: first two then remaining; no old answer is retried ===", flush=True)
            first = llm.run_local(directory, limit=2, timeout=timeout)
            print(json.dumps({"new_api_requests": first["new_api_requests"], "counts": first["pilot"]["counts"]}), flush=True)
            result = llm.run_local(directory, timeout=timeout)
            print(json.dumps({"new_api_requests": result["new_api_requests"], "counts": result["pilot"]["counts"]}), flush=True)
            if result["pilot"]["counts"]["received"] != 20:
                raise ValueError("not all initial answers were imported; preserved partial data, not frozen")
            print("=== Unload, freeze, independent confirmation ===", flush=True)
            llm.unload_local(directory)
            life.freeze_answers(directory)
        life.score_pilot(directory)
    checked = life.check_pilot(directory)
    if not checked["passed"]:
        raise ValueError("followup result did not pass artifact audit")
    result = summarize(directory)
    result["completion"] = "FOLLOWUP_COMPLETE"
    result["passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--source-pilot", type=Path, required=True)
    prep.add_argument("--output", type=Path, default=Path("runs/goal0032-explicit-selection"))
    for action in ("run", "summary"):
        p = sub.add_parser(action); p.add_argument("pilot", type=Path)
        if action == "run": p.add_argument("--timeout", type=float, default=1800)
    args = parser.parse_args()
    try:
        if args.action == "prepare": result = prepare(args.source_pilot, args.output)
        elif args.action == "run": result = run(args.pilot, args.timeout)
        else: result = summarize(args.pilot)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"followup: {exc}\n")


if __name__ == "__main__":
    main()
