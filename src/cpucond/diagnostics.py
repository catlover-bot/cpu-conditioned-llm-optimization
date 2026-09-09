"""Controlled transformations, linked-code evidence, and separate measurement phases."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
import time
import uuid

from .code_analysis import build_and_analyze, compare_kernels
from .diagnostic_config import DiagnosticConfig
from .diagnostic_prompts import write_diagnostic_prompts
from .diagnostic_reporting import summarize_measurement, write_reports
from .experiment import FIXTURES, cpu_affinity, digest, git_state, measure_pairs, write_json
from .host import discover_compiler, observe_host
from .models import ExecutionContract
from .process import ProcessResult, run_process
from .transformations import make_candidates
from .verification import validate_result

DIAGNOSTIC_SCHEMA = "2.0"
PHASES = ("exploration", "confirmation")


def case_id(size, seed):
    return f"n{size}_seed{seed}"


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ProcessLedger:
    """Count every candidate/tool invocation, including rejected/failed work."""
    def __init__(self):
        self.events = []
        self.stage = "setup"
        self.candidate = None
        self.expected_programs = {}

    def run(self, args, *, timeout=30.0, cwd=None):
        args = [str(x) for x in args]
        executable = str(Path(args[0]).resolve()) if Path(args[0]).is_absolute() else None
        expected = self.expected_programs.get(executable)
        observed = digest(executable) if expected and Path(executable).is_file() else None
        attempted = expected is None or observed == expected
        if not attempted:
            result = ProcessResult(args, "artifact_changed", None, "", "program changed after verification/build freeze", 0.0)
        else:
            result = run_process(args, timeout=timeout, cwd=cwd)
        event = {"event_id": len(self.events), "stage": self.stage, "candidate_id": self.candidate,
                 "args": args, "cwd": str(cwd) if cwd else None, "category": result.category,
                 "returncode": result.returncode, "process_attempted": attempted,
                 "wall_seconds": result.wall_seconds, "program_sha256": observed,
                 "expected_program_sha256": expected}
        self.events.append(event)
        return result

    def totals(self):
        stages = {}
        for event in self.events:
            label = event["stage"] + ("/" + event["sample_phase"] if event.get("sample_phase") else "")
            row = stages.setdefault(label, {"attempts": 0, "executions": 0, "process_failures": 0, "verification_failures": 0, "wall_seconds": 0.0})
            row["attempts"] += 1
            row["executions"] += int(event["process_attempted"])
            row["process_failures"] += int(event["category"] != "ok")
            row["verification_failures"] += int(event.get("verification_passed") is False)
            row["wall_seconds"] += event["wall_seconds"]
        return {"stages": stages, "execution_count": sum(x["process_attempted"] for x in self.events),
                "scope": "All build/analysis commands and candidate verification, warmup and measurement process calls; setup observations have separate operation durations."}


@contextmanager
def operation(record, name, candidate=None):
    started = time.perf_counter()
    item = {"operation": name, "candidate_id": candidate, "completed": False}
    try:
        yield
        item["completed"] = True
    finally:
        item["wall_seconds"] = time.perf_counter() - started
        record["operations"].append(item)


@contextmanager
def exclusive_measurements():
    """Prevent overlapping cpucond diagnostic phases by the same local user."""
    path = Path(tempfile.gettempdir()) / f"cpucond-measurements-{os.getuid()}.lock"
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another cpucond diagnostic measurement is active for this user") from exc
        try:
            yield {"path": str(path), "scope": "cpucond diagnostics for this local UID", "acquired": True}
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def verify_candidate(directory, cases, ledger, expected=None, timeout=30.0):
    validations, outputs = [], {}
    folder = directory / "verification"
    folder.mkdir()
    for n, seed in cases:
        cid = case_id(n, seed)
        process = ledger.run([directory / "program", "verify", n, seed], timeout=timeout)
        verdict, values = validate_result(process, n * n, expected[(n, seed)] if expected is not None else None)
        ledger.events[-1].update(verification_passed=verdict["passed"], verification_category=verdict["category"])
        stdout_path, stderr_path = folder / f"{cid}.stdout", folder / f"{cid}.stderr"
        stdout_path.write_text(process.stdout, encoding="utf-8")
        stderr_path.write_text(process.stderr, encoding="utf-8")
        metadata = process.to_dict()
        metadata.pop("stdout")
        metadata.pop("stderr")
        metadata.update(stdout_path=f"verification/{stdout_path.name}", stderr_path=f"verification/{stderr_path.name}",
                        stdout_sha256=digest(stdout_path), stderr_sha256=digest(stderr_path),
                        program_sha256=ledger.events[-1]["program_sha256"], ledger_event_id=ledger.events[-1]["event_id"])
        validations.append({"size": n, "seed": seed, **verdict, "process": metadata})
        if verdict["passed"]:
            outputs[(n, seed)] = values
    failures = [x for x in validations if not x["passed"]]
    return {"passed": not failures, "category": failures[0]["category"] if failures else "ok", "cases": validations}, outputs


def artifact_manifest(run_dir):
    return {str(p.relative_to(run_dir)): digest(p) for p in sorted(run_dir.rglob("*"))
            if p.is_file() and p.name != "experiment.json"}


def finalize(run_dir, record, ledger):
    record["costs"] = ledger.totals()
    write_json(run_dir / "process-ledger.json", ledger.events)
    write_json(run_dir / "operations.json", record["operations"])
    record["artifacts"] = artifact_manifest(run_dir)
    write_json(run_dir / "experiment.json", record)


def run_diagnostics(output, *, config=None, specification=None, compiler="clang", cpu=None):
    config = config or DiagnosticConfig()
    if not isinstance(config, DiagnosticConfig):
        raise TypeError("config must be DiagnosticConfig")
    record = {"schema_version": DIAGNOSTIC_SCHEMA, "experiment_type": "controlled_diagnostics",
              "environment_role": "development_smoke", "publishable_benchmark": False,
              "input_kind": "c", "kernel": "gemm_smoke", "status": "running", "llm_api_called": False,
              "settings": config.to_dict(), "operations": [], "candidates": {}, "phases": {}, "artifacts": {}}
    ledger = ProcessLedger()
    with operation(record, "setup_observations"):
        target = discover_compiler(compiler)
        record["compiler"] = asdict(target)
        record["host"] = asdict(observe_host())
        record["git"] = git_state(Path(__file__).resolve().parent)
        record["python"] = {"version": sys.version, "executable": sys.executable}
        tool_paths = {}
        record["tools"] = {}
        for key, executable in (("objdump", "llvm-objdump"), ("readobj", "llvm-readobj")):
            found = shutil.which(executable) or shutil.which(executable + "-18")
            if not found:
                raise RuntimeError(f"required analysis tool unavailable: {executable}")
            tool_paths[key] = str(Path(found).resolve())
            version = ledger.run([tool_paths[key], "--version"])
            if version.category != "ok":
                raise RuntimeError(f"analysis tool version probe failed: {executable}")
            record["tools"][key] = {"path": tool_paths[key], "version": version.to_dict()}
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = Path(output).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    record["run_id"] = run_id
    try:
        with operation(record, "generate_and_freeze_candidate_manifest"):
            candidates = make_candidates()
            snapshots = run_dir / "runner_source"
            snapshots.mkdir()
            for path in sorted(Path(__file__).parent.glob("*.py")):
                shutil.copyfile(path, snapshots / path.name)
            project = Path(__file__).resolve().parents[2] / "pyproject.toml"
            if project.is_file():
                shutil.copyfile(project, snapshots / project.name)
            write_json(run_dir / "config.json", config.to_dict())
            contract = ExecutionContract()
            record["execution_contract"] = asdict(contract)
            manifest = {"schema_version": DIAGNOSTIC_SCHEMA, "fixed_before_measurement": True,
                        "family": "independent_output_j_unrolling", "factors": [1, 2, 4, 8, 16],
                        "series_baseline": "unroll_1", "measurement_baseline": "reference",
                        "baseline_change": "Reference i-j-k is expressed as i-jblocks-k with one accumulator per independent output and a scalar tail. unroll_1 is the common generated baseline; other factors change only the number of outputs in a block.",
                        "compiler": asdict(target), "config_sha256": digest(run_dir / "config.json"),
                        "driver_sha256": digest(FIXTURES / "harness.c"), "header_sha256": digest(FIXTURES / "kernel.h"),
                        "generator_sha256": digest(snapshots / "transformations.py"),
                        "source_fp_directives": {"policy": "No source FP pragmas or reassociation directives; shared noinline declaration only.",
                                                 "driver_defines": ["_POSIX_C_SOURCE 200809L"], "kernel_fp_pragmas": []},
                        "candidates": []}
            for candidate in candidates:
                directory = run_dir / "candidates" / candidate.candidate_id
                directory.mkdir(parents=True)
                (directory / "kernel.c").write_text(candidate.source, encoding="utf-8")
                for filename in ("harness.c", "kernel.h"):
                    shutil.copyfile(FIXTURES / filename, directory / filename)
                item = {key: value for key, value in asdict(candidate).items() if key != "source"}
                item.update(source_sha256=digest(directory / "kernel.c"), source_path=f"candidates/{candidate.candidate_id}/kernel.c")
                manifest["candidates"].append(item)
                record["candidates"][candidate.candidate_id] = dict(item)
            write_json(run_dir / "candidate-manifest.json", manifest)
            record["manifest_sha256"] = digest(run_dir / "candidate-manifest.json")
            record["prompts"] = write_diagnostic_prompts(
                run_dir / "prompts", candidates,
                specification if specification is not None else "Synthetic diagnostic fixture: Example CPU, 32 KiB L1 data cache, 512 KiB L2 cache; not an observed host specification.",
                contract,
            )
        finalize(run_dir, record, ledger)
        ledger.stage = "build_analysis"
        for name, candidate in record["candidates"].items():
            ledger.candidate = name
            directory = run_dir / "candidates" / name
            with operation(record, "build_and_analyze", name):
                candidate.update(build_and_analyze(directory, target, tool_paths, timeout=config.timeout_seconds, run=ledger.run))
            candidate["evidence"] = {key: f"candidates/{name}/{file}" for key, file in (
                ("build_path", "build.json"), ("analysis_path", "analysis.json"), ("optimization_path", "optimization.json"))}
            candidate["verification"] = {"passed": False, "category": "not_run", "cases": []}
            if candidate["build"]["passed"]:
                candidate["program_sha256"] = digest(directory / "program")
                candidate["object_sha256"] = digest(directory / "kernel.o")
                ledger.expected_programs[str(directory / "program")] = candidate["program_sha256"]
        ledger.stage = "verification"
        reference_outputs = {}
        for name, candidate in record["candidates"].items():
            ledger.candidate = name
            directory = run_dir / "candidates" / name
            with operation(record, "verify", name):
                if not candidate["build"]["passed"]:
                    candidate["verification"]["category"] = candidate["build"]["category"]
                elif name != "reference" and not record["candidates"]["reference"]["verification"]["passed"]:
                    candidate["verification"]["category"] = "reference_failure"
                else:
                    candidate["verification"], values = verify_candidate(directory, config.cases(), ledger,
                                                                        None if name == "reference" else reference_outputs, config.timeout_seconds)
                    if name == "reference":
                        reference_outputs = values
                write_json(directory / "verification.json", candidate["verification"])
                baseline = record["candidates"][candidate["comparison_baseline"]]
                candidate["comparison"] = compare_kernels(baseline["analysis"], candidate["analysis"])
                candidate["comparison"]["baseline_candidate_id"] = candidate["comparison_baseline"]
                candidate["comparison"]["evidence_paths"] = [baseline["evidence"]["analysis_path"], candidate["evidence"]["analysis_path"]]
                write_json(directory / "comparison.json", candidate["comparison"])
        frozen = {"manifest_sha256": record["manifest_sha256"], "config_sha256": manifest["config_sha256"],
                  "programs": {name: c.get("program_sha256") for name, c in record["candidates"].items()},
                  "verification": {name: {"passed": c["verification"]["passed"],
                                           "path": f"candidates/{name}/verification.json",
                                           "sha256": digest(run_dir / "candidates" / name / "verification.json")}
                                   for name, c in record["candidates"].items()},
                  "selection_policy": "All verified non-reference candidates in both phases; no result-based filtering."}
        write_json(run_dir / "measurement-freeze.json", frozen)
        record["measurement_freeze_sha256"] = digest(run_dir / "measurement-freeze.json")
        with exclusive_measurements() as lock, cpu_affinity(cpu) as affinity:
            record["measurement_lock"] = lock
            record["affinity"] = affinity
            for phase in PHASES:
                with operation(record, phase):
                    verify_frozen_inputs(run_dir, record)
                    seed = getattr(config, phase + "_order_seed")
                    rng = random.Random(seed)
                    phase_record = {"phase": phase, "order_seed": seed, "started_utc": datetime.now(timezone.utc).isoformat(),
                                    "measurement_freeze_sha256": record["measurement_freeze_sha256"],
                                    "candidate_order_by_case": [], "measurements": {}, "skipped": []}
                    record["phases"][phase] = phase_record
                    phase_dir = run_dir / "phases" / phase
                    phase_dir.mkdir(parents=True)
                    ledger.stage = phase
                    for n, input_seed in config.measure_cases:
                        cid = case_id(n, input_seed)
                        order = [name for name in record["candidates"] if name != "reference"]
                        rng.shuffle(order)
                        phase_record["candidate_order_by_case"].append({"case_id": cid, "candidate_ids": order})
                        for position, name in enumerate(order):
                            candidate = record["candidates"][name]
                            if not candidate["verification"]["passed"]:
                                phase_record["skipped"].append({"candidate_id": name, "case_id": cid, "reason": candidate["verification"]["category"]})
                                continue
                            ledger.candidate = name
                            before = len(ledger.events)
                            measured = measure_pairs(run_dir, name, size=n, seed=input_seed,
                                                     repeats=config.repeats, warmups=config.warmups,
                                                     timeout=config.timeout_seconds, run=ledger.run)
                            for sample, event in zip(measured["samples"], ledger.events[before:]):
                                event["sample_phase"] = sample["phase"]
                                event["case_id"] = cid
                                sample.update(program_sha256=event["program_sha256"], ledger_event_id=event["event_id"],
                                              candidate_order_position=position, experiment_phase=phase)
                            measured = summarize_measurement(measured, asdict(config.quality))
                            measured.update(phase=phase, case_id=cid, candidate_id=name,
                                            measurement_freeze_sha256=record["measurement_freeze_sha256"])
                            phase_record["measurements"].setdefault(name, {})[cid] = measured
                            write_json(phase_dir / f"{name}-{cid}.json", measured)
                    phase_record["completed_utc"] = datetime.now(timezone.utc).isoformat()
                    write_json(phase_dir / "phase.json", phase_record)
        with operation(record, "render_reports"):
            record["reports"] = write_reports(run_dir, record)
        verified = all(c["verification"]["passed"] for name, c in record["candidates"].items() if name != "deliberately_wrong")
        rejected = all(case["category"] == "value_mismatch" for case in record["candidates"]["deliberately_wrong"]["verification"]["cases"])
        rejected = rejected and bool(record["candidates"]["deliberately_wrong"]["verification"]["cases"])
        all_measured = all(record["phases"][phase]["measurements"].get(name, {}).get(case_id(n, s), {}).get("passed", False)
                           for phase in PHASES for name in record["candidates"] if name not in ("reference", "deliberately_wrong")
                           for n, s in config.measure_cases)
        record["status"] = "completed" if verified and rejected and all_measured else "failed"
        finalize(run_dir, record, ledger)
        errors = audit_diagnostic(run_dir)
        if errors:
            record["status"] = "failed"
            record["artifact_errors"] = errors
            write_json(run_dir / "experiment.json", record)
        return run_dir, json.loads((run_dir / "experiment.json").read_text())
    except BaseException as exc:
        record["status"] = "failed"
        record["failure"] = {"category": type(exc).__name__, "reason": str(exc)}
        finalize(run_dir, record, ledger)
        raise


def verify_frozen_inputs(run_dir, record):
    if digest(run_dir / "candidate-manifest.json") != record["manifest_sha256"]:
        raise RuntimeError("candidate manifest changed after freeze")
    if digest(run_dir / "measurement-freeze.json") != record["measurement_freeze_sha256"]:
        raise RuntimeError("measurement freeze changed")
    manifest = json.loads((run_dir / "candidate-manifest.json").read_text())
    frozen = json.loads((run_dir / "measurement-freeze.json").read_text())
    if digest(run_dir / "config.json") != manifest["config_sha256"]:
        raise RuntimeError("configuration changed after freeze")
    for candidate in manifest["candidates"]:
        directory = run_dir / "candidates" / candidate["candidate_id"]
        for name, expected in (("kernel.c", candidate["source_sha256"]), ("harness.c", manifest["driver_sha256"]), ("kernel.h", manifest["header_sha256"])):
            if digest(directory / name) != expected:
                raise RuntimeError(f"frozen source changed: {candidate['candidate_id']}/{name}")
        expected = record["candidates"][candidate["candidate_id"]].get("program_sha256")
        if expected and digest(directory / "program") != expected:
            raise RuntimeError(f"frozen executable changed: {candidate['candidate_id']}")
        if digest(directory / "verification.json") != frozen["verification"][candidate["candidate_id"]]["sha256"]:
            raise RuntimeError(f"frozen verification changed: {candidate['candidate_id']}")


def audit_diagnostic(run_dir):
    run_dir = Path(run_dir)
    try:
        record = json.loads((run_dir / "experiment.json").read_text())
        return _audit_diagnostic(run_dir, record)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:
        return [f"invalid or incomplete diagnostic artifacts: {exc}"]


def _audit_diagnostic(run_dir, record):
    errors = []
    if record["schema_version"] != DIAGNOSTIC_SCHEMA or record["status"] != "completed":
        errors.append("diagnostic run is not complete with supported schema")
    if record["environment_role"] != "development_smoke" or record["publishable_benchmark"] is not False or record["llm_api_called"] is not False:
        errors.append("invalid environment or generation classification")
    for key in ("host", "compiler", "git", "settings", "python", "tools", "execution_contract", "costs", "operations", "affinity"):
        if not record.get(key):
            errors.append(f"missing provenance: {key}")
    actual_files = artifact_manifest(run_dir)
    if actual_files != record["artifacts"]:
        errors.append("artifact manifest/file hash mismatch")
    required = {"candidate-manifest.json", "measurement-freeze.json", "config.json", "report.json", "report.csv", "report.md",
                "process-ledger.json", "operations.json", "phases/exploration/phase.json", "phases/confirmation/phase.json"}
    if not required.issubset(record["artifacts"]):
        errors.append("required diagnostic artifacts missing")
    verify_frozen_inputs(run_dir, record)
    manifest = json.loads((run_dir / "candidate-manifest.json").read_text())
    if [x["candidate_id"] for x in manifest["candidates"]] != list(record["candidates"]):
        # JSON serialization sorts mapping keys; the manifest is the order authority.
        if set(x["candidate_id"] for x in manifest["candidates"]) != set(record["candidates"]):
            errors.append("candidate set differs from preregistered manifest")
    expected_cases = {(n, s) for n in record["settings"]["verification_sizes"] for s in record["settings"]["verification_seeds"]}
    expected_cases.update(tuple(x) for x in record["settings"]["measure_cases"])
    events = json.loads((run_dir / "process-ledger.json").read_text())
    for name, candidate in record["candidates"].items():
        directory = run_dir / "candidates" / name
        for key, file in (("build", "build.json"), ("analysis", "analysis.json"), ("optimization", "optimization.json"), ("verification", "verification.json"), ("comparison", "comparison.json")):
            if candidate[key] != json.loads((directory / file).read_text()):
                errors.append(f"candidate {key} metadata mismatch: {name}")
        cases = candidate["verification"]["cases"]
        if {(x["size"], x["seed"]) for x in cases} != expected_cases:
            errors.append(f"verification cases missing: {name}")
        if candidate.get("program_sha256") != digest(directory / "program"):
            errors.append(f"executed program provenance mismatch: {name}")
        if candidate["analysis"].get("program_sha256") != candidate.get("program_sha256"):
            errors.append(f"analyzed program differs from executed program: {name}")
        for case in cases:
            p = case["process"]
            if p["program_sha256"] != candidate["program_sha256"] or events[p["ledger_event_id"]]["program_sha256"] != candidate["program_sha256"]:
                errors.append(f"verification executable changed: {name}")
        for phase in PHASES:
            measured = record["phases"][phase]["measurements"].get(name, {})
            if not candidate["verification"]["passed"] and measured:
                errors.append(f"unverified candidate measured: {name}")
            for cid, result in measured.items():
                if result != json.loads((run_dir / "phases" / phase / f"{name}-{cid}.json").read_text()):
                    errors.append(f"phase sample metadata mismatch: {name}/{phase}/{cid}")
                if result["phase"] != phase or result["measurement_freeze_sha256"] != record["measurement_freeze_sha256"]:
                    errors.append("phases do not use the same frozen inputs")
                for sample in result["samples"]:
                    expected = record["candidates"][sample["implementation"]]["program_sha256"]
                    if sample["program_sha256"] != expected or events[sample["ledger_event_id"]]["program_sha256"] != expected:
                        errors.append(f"measured executable provenance mismatch: {name}/{phase}/{cid}")
    for phase in PHASES:
        if record["phases"][phase] != json.loads((run_dir / "phases" / phase / "phase.json").read_text()):
            errors.append(f"phase record mismatch: {phase}")
    from .diagnostic_audit import audit_semantics
    errors.extend(audit_semantics(run_dir, record))
    return errors
