"""Small C-only experiment pipeline with a verification gate and provenance."""

from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import uuid

from .host import discover_compiler, observe_host
from .models import SCHEMA_VERSION, ExperimentRecord, ExecutionContract, PromptCPUContext
from .process import run_process
from .prompts import prompt_hash, render_prompt
from .verification import OutputError, parse_measurement, validate_result
from .execution_gate import gated

FIXTURES = Path(__file__).parent / "fixtures"
CANDIDATES = ("reference", "identity", "equivalent", "deliberately_wrong")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    if is_dataclass(value):
        value = asdict(value)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def git_state(cwd):
    commit = run_process(["git", "rev-parse", "HEAD"], cwd=cwd)
    status = run_process(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=cwd)
    branch = run_process(["git", "branch", "--show-current"], cwd=cwd)
    return {"commit": commit.stdout.strip() if commit.category == "ok" else None,
            "branch": branch.stdout.strip() if branch.category == "ok" else None,
            "dirty": bool(status.stdout) if status.category == "ok" else None,
            "status_porcelain": status.stdout if status.category == "ok" else None,
            "missing_reason": None if commit.category == status.category == "ok" else "Git metadata unavailable"}


@contextmanager
def cpu_affinity(requested=None):
    record = {"requested_cpu": requested, "available_before": None, "effective": None,
              "pinned": False, "reason": None, "restored": None}
    previous = None
    try:
        previous = os.sched_getaffinity(0)
        record["available_before"] = sorted(previous)
        chosen = min(previous) if requested is None else requested
        record["requested_cpu"] = chosen
        if chosen not in previous:
            raise ValueError(f"CPU {chosen} is outside the available affinity set")
        os.sched_setaffinity(0, {chosen})
        record["effective"] = sorted(os.sched_getaffinity(0))
        record["pinned"] = record["effective"] == [chosen]
        if not record["pinned"]:
            record["reason"] = "affinity readback did not confirm the requested CPU"
    except (AttributeError, OSError) as exc:
        record["reason"] = f"{type(exc).__name__}: {exc}"
    try:
        yield record
    finally:
        if previous is not None:
            try:
                os.sched_setaffinity(0, previous)
                record["restored"] = os.sched_getaffinity(0) == previous
            except OSError as exc:
                record["restored"] = False
                record["restore_reason"] = str(exc)


def build_candidate(directory, target, objdump, timeout):
    """Build separate translation units; all C analysis uses the same flags."""
    common = [target.compiler, "-std=c11", *target.compile_flags]
    commands = [
        ("kernel_object", [*common, "-c", "kernel.c", "-o", "kernel.o"]),
        ("harness_object", [*common, "-c", "harness.c", "-o", "harness.o"]),
        ("link", [target.compiler, *target.target_flags, "kernel.o", "harness.o", *target.link_flags, "-o", "program"]),
        ("llvm_ir", [*common, "-S", "-emit-llvm", "kernel.c", "-o", "kernel.ll"]),
        ("assembly", [*common, "-S", "kernel.c", "-o", "kernel.s"]),
        ("disassembly", [objdump, "--disassemble-symbols=kernel", "program"]),
    ]
    results = []
    category = "ok"
    for stage, args in commands:
        result = run_process(args, cwd=directory, timeout=timeout)
        item = {"stage": stage, "cwd": str(directory), **result.to_dict()}
        if result.category != "ok":
            item["category"] = result.category if result.category == "timeout" else "compile_failure"
            category = item["category"]
        results.append(item)
        if category != "ok":
            break
        if stage == "disassembly":
            (directory / "kernel.disasm").write_text(result.stdout, encoding="utf-8")
    record = {"passed": category == "ok", "category": category, "commands": results,
              "analysis_role": "compiled_C_artifacts_not_IR_or_assembly_input_experiments"}
    write_json(directory / "build.json", record)
    return record


def summarize(values):
    median = statistics.median(values)
    return {"count": len(values), "median_ns": median, "min_ns": min(values), "max_ns": max(values),
            "mad_ns": statistics.median(abs(x - median) for x in values),
            "population_stdev_ns": statistics.pstdev(values)}


@gated("measurement")
def measure_pairs(run_dir, candidate, *, size, seed, repeats, warmups, timeout, run=None):
    run = run or run_process
    samples = []
    passed = True
    for phase, count in (("warmup", warmups), ("measurement", repeats)):
        for repetition in range(count):
            order = ["reference", candidate] if repetition % 2 == 0 else [candidate, "reference"]
            for position, name in enumerate(order):
                result = run([run_dir / "candidates" / name / "program", "measure", size, seed], timeout=timeout)
                item = {"phase": phase, "pair_candidate": candidate, "repetition": repetition,
                        "position": position, "order": order, "implementation": name,
                        "size": size, "seed": seed, "process": result.to_dict(),
                        "category": result.category}
                if result.category == "ok":
                    try:
                        item.update(parse_measurement(result.stdout))
                    except OutputError as exc:
                        item.update(category="output_format_error", reason=exc.reason)
                samples.append(item)
                if item["category"] != "ok":
                    passed = False
                    break
            if not passed:
                break
        if not passed:
            break
    if not passed:
        return {"passed": False, "samples": samples, "summary": None}
    measured = [x for x in samples if x["phase"] == "measurement"]
    baseline = [x["elapsed_ns"] for x in measured if x["implementation"] == "reference"]
    candidate_times = [x["elapsed_ns"] for x in measured if x["implementation"] == candidate]
    ratios = [b / c for b, c in zip(baseline, candidate_times)]
    return {"passed": True, "samples": samples,
            "summary": {"baseline": summarize(baseline), "candidate": summarize(candidate_times),
                        "median_paired_ratio": statistics.median(ratios), "paired_ratios": ratios,
                        "interpretation": "development_smoke_only; no CPU specialization claim"}}


def audit_artifacts(run_dir):
    """Read back the saved manifest and verify every referenced artifact."""
    run_dir = Path(run_dir)
    try:
        record = json.loads((run_dir / "experiment.json").read_text(encoding="utf-8"))
        if record.get("experiment_type") == "controlled_diagnostics":
            from .diagnostics import audit_diagnostic
            return audit_diagnostic(run_dir)
        return _audit_record(run_dir, record)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"invalid or incomplete experiment record: {exc}"]


def _audit_record(run_dir, record):
    errors = []
    required_metadata = {"schema_version", "run_id", "input_kind", "kernel", "environment_role",
                         "publishable_benchmark", "status", "settings", "host", "compiler", "git",
                         "sources", "prompts", "candidates", "summary", "artifacts", "toolchain",
                         "candidate_origin", "llm_api_called"}
    if not required_metadata.issubset(record):
        return ["required experiment metadata missing: " + ", ".join(sorted(required_metadata - set(record)))]
    critical_fields = {
        "host": {"os_name", "kernel", "cpu_model", "available_cpus", "isa_flags", "wsl", "scope", "methods", "missing"},
        "compiler": {"compiler", "version", "target_triple", "target_flags", "optimization_flags", "floating_point_flags", "link_flags"},
        "settings": {"execution_contract", "prompt_cpu_contexts", "verification_cases", "affinity", "python", "repeats", "warmups"},
        "git": {"commit", "branch", "dirty", "status_porcelain", "missing_reason"},
        "toolchain": {"objdump", "objdump_version"},
    }
    for section, fields in critical_fields.items():
        if not isinstance(record[section], dict) or not fields.issubset(record[section]):
            errors.append(f"required provenance fields missing: {section}")
    if record["environment_role"] != "development_smoke" or record["publishable_benchmark"] is not False:
        errors.append("invalid development smoke environment classification")
    if record["input_kind"] != "c" or record["candidate_origin"] != "handwritten_fixture" or record["llm_api_called"] is not False:
        errors.append("unexpected input kind or candidate provenance")
    if record.get("status") != "completed" or record.get("schema_version") != SCHEMA_VERSION:
        errors.append("run is not completed with the supported schema")
    if set(record["candidates"]) != set(CANDIDATES) or set(record["prompts"]) != {"none", "spec"}:
        errors.append("required candidates or prompt variants missing")
    required = {"summary.json", "prompts/none.txt", "prompts/spec.txt"}
    required.update(f"runner_source/{name}.py" for name in (
        "__init__", "__main__", "experiment", "host", "models", "process", "prompts", "verification"))
    for name in CANDIDATES:
        required.update(f"candidates/{name}/{file}" for file in (
            "kernel.c", "kernel.h", "harness.c", "kernel.o", "harness.o", "program",
            "kernel.ll", "kernel.s", "kernel.disasm", "build.json", "verification.json"))
    required.update(f"candidates/{name}/measurements.json" for name in ("identity", "equivalent"))
    if not required.issubset(record["artifacts"]):
        errors.append("required artifact manifest entries missing")
    actual_files = {str(p.relative_to(run_dir)) for p in run_dir.rglob("*") if p.is_file() and p.name != "experiment.json"}
    if actual_files != set(record["artifacts"]):
        errors.append("artifact manifest does not match saved file set")
    for relative, expected in record["artifacts"].items():
        path = (run_dir / relative).resolve()
        if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
            errors.append(f"missing or invalid artifact: {relative}")
        elif digest(path) != expected:
            errors.append(f"hash mismatch: {relative}")
        elif path.stat().st_size == 0:
            errors.append(f"empty artifact: {relative}")
    for name, candidate in record["candidates"].items():
        if not candidate["verification"]["passed"] and candidate["measurement"] is not None:
            errors.append(f"unverified candidate was measured: {name}")
        if candidate["source_sha256"] != record["artifacts"].get(f"candidates/{name}/kernel.c"):
            errors.append(f"source hash mismatch: {name}")
        for key, filename in (("build", "build.json"), ("verification", "verification.json"), ("measurement", "measurements.json")):
            if candidate[key] is not None:
                snapshot = json.loads((run_dir / "candidates" / name / filename).read_text())
                if candidate[key] != snapshot:
                    errors.append(f"metadata differs from saved {key}: {name}")
        if not candidate["build"]["passed"]:
            errors.append(f"required build did not pass: {name}")
    if record["sources"]["input_sha256"] != record["candidates"]["reference"]["source_sha256"]:
        errors.append("input source differs from reference source")
    for mode, prompt in record["prompts"].items():
        if prompt["sha256"] != record["artifacts"].get(prompt["path"]):
            errors.append(f"prompt hash mismatch: {mode}")
    if record["summary"] != json.loads((run_dir / "summary.json").read_text()):
        errors.append("summary differs from saved summary")
    if not record["summary"]["expected_fixture_outcomes_passed"]:
        errors.append("expected fixture outcomes did not pass")
    return errors


@gated("measurement")
def run_smoke(output, **kwargs):
    """Preserve failure evidence if an unexpected error interrupts a created run."""
    state = {}
    try:
        return _run_smoke(output, _state=state, **kwargs)
    except BaseException as exc:
        if state:
            run_dir, data = state["run_dir"], state["data"]
            data["status"] = "failed"
            data["failure"] = {"category": type(exc).__name__, "reason": str(exc)}
            data["artifacts"] = {str(path.relative_to(run_dir)): digest(path) for path in sorted(run_dir.rglob("*"))
                                 if path.is_file() and path.name != "experiment.json"}
            write_json(run_dir / "experiment.json", data)
        raise


def _run_smoke(output, *, _state, specification=None, compiler="clang", input_kind="c", sizes=(1, 3, 8),
              seeds=(1, 17, 42), measure_size=64, measure_seed=17, repeats=6, warmups=2,
              timeout=30.0, cpu=None):
    if input_kind not in ("c", "llvm_ir", "asm"):
        raise ValueError(f"unknown input_kind: {input_kind}")
    if input_kind != "c":
        raise NotImplementedError(f"input_kind={input_kind} candidate evaluation is not implemented; C only")
    if not sizes or not seeds or any(type(n) is not int or not 1 <= n <= 1024 for n in (*sizes, measure_size)):
        raise ValueError("sizes must be integers between 1 and 1024")
    if any(type(s) is not int or not 0 <= s <= 0xFFFFFFFF for s in (*seeds, measure_seed)):
        raise ValueError("seeds must be uint32 integers")
    if repeats < 2 or warmups < 0 or timeout <= 0:
        raise ValueError("need repeats >= 2, warmups >= 0 and timeout > 0")
    host = observe_host()
    target = discover_compiler(compiler)
    objdump_path = shutil.which("llvm-objdump") or shutil.which("llvm-objdump-18")
    if objdump_path is None:
        raise RuntimeError("llvm-objdump is required for the C analysis artifacts")
    objdump = str(Path(objdump_path).resolve())
    objdump_version = run_process([objdump, "--version"])
    if objdump_version.category != "ok":
        raise RuntimeError("llvm-objdump version probe failed")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = Path(output).resolve() / run_id
    contract = ExecutionContract()
    # This example is a user-visible synthetic specification, never inferred
    # from the host. Both prompt variants share the exact source and contract.
    specification = specification if specification is not None else "Synthetic prompt fixture: Example CPU; 32 KiB L1 data cache, 512 KiB L2 cache. Not an observed host specification."
    contexts = {"none": PromptCPUContext(), "spec": PromptCPUContext("spec", specification)}
    run_dir.mkdir(parents=True, exist_ok=False)
    settings = {"sizes": list(sizes), "seeds": list(seeds), "measure_size": measure_size,
                "measure_seed": measure_seed, "repeats": repeats, "warmups": warmups, "timeout_seconds": timeout,
                "execution_contract": asdict(contract), "prompt_cpu_contexts": {k: asdict(v) for k, v in contexts.items()},
                "input_domain": "uint32 LCG runtime inputs: [-1, 1 - 2^-16] in exact multiples of 2^-16; C starts at +0",
                "process_environment_policy": "only PATH=os.defpath, LANG=C, LC_ALL=C",
                "python": {"version": sys.version, "executable": sys.executable},
                "timing": "CLOCK_MONOTONIC inside harness; one kernel invocation per process; separately recorded warmup processes",
                "perf": {"used": False, "reason": "optional counters are outside Goal 001"}}
    # Include the measured input in validation before allowing any timing.
    cases = [(n, s) for n in sizes for s in seeds]
    if (measure_size, measure_seed) not in cases:
        cases.append((measure_size, measure_seed))
    settings["verification_cases"] = [{"size": n, "seed": s} for n, s in cases]
    record = ExperimentRecord()
    data = asdict(record)
    data.update(schema_version=SCHEMA_VERSION, run_id=run_id, input_kind=input_kind, kernel="gemm_smoke",
                status="running", environment_role="development_smoke", publishable_benchmark=False,
                settings=settings, host=asdict(host), compiler=asdict(target), git=git_state(Path(__file__).resolve().parent),
                sources={}, prompts={}, candidates={}, summary={}, artifacts={},
                toolchain={"objdump": objdump, "objdump_version": objdump_version.to_dict()},
                candidate_origin="handwritten_fixture", llm_api_called=False)
    data["git"]["source_directory"] = str(Path(__file__).resolve().parent)
    _state.update(run_dir=run_dir, data=data)
    write_json(run_dir / "experiment.json", data)
    (run_dir / "runner_source").mkdir()
    for module in sorted(Path(__file__).parent.glob("*.py")):
        shutil.copyfile(module, run_dir / "runner_source" / module.name)
    project_config = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if project_config.is_file():
        shutil.copyfile(project_config, run_dir / "runner_source" / "pyproject.toml")
    source = (FIXTURES / "reference.c").read_text(encoding="utf-8")
    (run_dir / "prompts").mkdir()
    for mode, context in contexts.items():
        prompt = render_prompt(source, context, contract)
        relative = f"prompts/{mode}.txt"
        (run_dir / relative).write_text(prompt, encoding="utf-8")
        data["prompts"][mode] = {"path": relative, "sha256": prompt_hash(prompt), "sent_to_llm": False}
    data["sources"]["input_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    reference_values = {}
    with cpu_affinity(cpu) as affinity:
        data["settings"]["affinity"] = affinity
        for name in CANDIDATES:
            directory = run_dir / "candidates" / name
            directory.mkdir(parents=True)
            for original, snapshot in ((f"{name}.c", "kernel.c"), ("harness.c", "harness.c"), ("kernel.h", "kernel.h")):
                shutil.copyfile(FIXTURES / original, directory / snapshot)
            build = build_candidate(directory, target, objdump, timeout)
            candidate = {"origin": "handwritten_fixture", "source_sha256": digest(directory / "kernel.c"),
                         "build": build, "verification": {"passed": False, "category": "not_run", "cases": []},
                         "measurement": None}
            data["candidates"][name] = candidate
            if not build["passed"]:
                candidate["verification"]["category"] = build["category"]
            elif name != "reference" and not data["candidates"]["reference"]["verification"]["passed"]:
                candidate["verification"]["category"] = "reference_failure"
            else:
                validations = []
                for n, seed in cases:
                    result = run_process([directory / "program", "verify", n, seed], timeout=timeout)
                    verdict, values = validate_result(result, n * n, None if name == "reference" else reference_values[(n, seed)])
                    validations.append({"size": n, "seed": seed, **verdict, "process": result.to_dict()})
                    if name == "reference" and verdict["passed"]:
                        reference_values[(n, seed)] = values
                failures = [x for x in validations if not x["passed"]]
                candidate["verification"] = {"passed": not failures, "category": failures[0]["category"] if failures else "ok", "cases": validations}
            write_json(directory / "verification.json", candidate["verification"])
        for name in CANDIDATES[1:]:
            candidate = data["candidates"][name]
            if not candidate["verification"]["passed"]:
                continue
            candidate["measurement"] = measure_pairs(run_dir, name, size=measure_size, seed=measure_seed,
                                                     repeats=repeats, warmups=warmups, timeout=timeout)
            write_json(run_dir / "candidates" / name / "measurements.json", candidate["measurement"])
    expected_outcomes = (
        all(data["candidates"][name]["verification"]["passed"] for name in ("reference", "identity", "equivalent"))
        and all(data["candidates"][name]["measurement"] is not None and data["candidates"][name]["measurement"]["passed"] for name in ("identity", "equivalent"))
        and data["candidates"]["deliberately_wrong"]["verification"]["category"] == "value_mismatch"
        and data["candidates"]["deliberately_wrong"]["measurement"] is None
        and all(x["build"]["passed"] for x in data["candidates"].values())
    )
    data["summary"] = {"expected_fixture_outcomes_passed": expected_outcomes,
                       "candidates": {name: x["measurement"]["summary"] if x["measurement"] else None for name, x in data["candidates"].items()},
                       "limitations": ["test-based validation, not formal equivalence", "WSL development smoke, not publishable performance",
                                       "handwritten fixtures, no LLM optimization", "warmups are separate processes; short kernels include timer overhead",
                                       "code hashes do not prove semantic equivalence or explain performance"]}
    write_json(run_dir / "summary.json", data["summary"])
    data["artifacts"] = {str(path.relative_to(run_dir)): digest(path) for path in sorted(run_dir.rglob("*")) if path.is_file() and path.name != "experiment.json"}
    data["status"] = "completed" if expected_outcomes else "failed"
    write_json(run_dir / "experiment.json", data)
    errors = audit_artifacts(run_dir)
    if errors:
        data["status"] = "failed"
        data["artifact_errors"] = errors
        write_json(run_dir / "experiment.json", data)
    return run_dir, json.loads((run_dir / "experiment.json").read_text(encoding="utf-8"))
