"""Read-only semantic checks beyond self-consistent artifact hashes.

Saved verification output, executable ranges, raw measurements and process
events are replayed. No compiler or candidate is executed by this checker.
"""

import csv
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import random

from .code_analysis import (compare_kernels, extract_symbol_range, normalize_disassembly,
                            parse_optimization_record, verify_disassembly, _dependencies, _driver_calls)
from .diagnostic_config import load_config
from .diagnostic_prompts import _common_payload
from .diagnostic_reporting import build_report, render_markdown, summarize_measurement, _csv_rows
from .models import CompilerTarget, ExecutionContract
from .process import ProcessResult
from .prompts import CPU_SECTION_HEADER
from .transformations import make_candidates
from .verification import parse_measurement, validate_result


PHASES = ("exploration", "confirmation")
CANDIDATE_IDS = ("reference", "identity", "unroll_1", "unroll_2", "unroll_4", "unroll_8", "unroll_16", "deliberately_wrong")


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _case_id(size, seed):
    return f"n{size}_seed{seed}"


def _canonical_warnings(value, key=None):
    """Ignore warning presentation order, preserving all meaningful list order."""
    if isinstance(value, dict):
        return {k: _canonical_warnings(v, k) for k, v in value.items()}
    if isinstance(value, list):
        items = [_canonical_warnings(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True)) if key == "warnings" else items
    return value


def _cost_totals(events):
    stages = {}
    for event in events:
        label = event["stage"] + ("/" + event["sample_phase"] if event.get("sample_phase") else "")
        row = stages.setdefault(label, {"attempts": 0, "executions": 0, "process_failures": 0,
                                        "verification_failures": 0, "wall_seconds": 0.0})
        row["attempts"] += 1
        row["executions"] += int(event["process_attempted"])
        row["process_failures"] += int(event["category"] != "ok")
        row["verification_failures"] += int(event.get("verification_passed") is False)
        row["wall_seconds"] += event["wall_seconds"]
    return stages, sum(event["process_attempted"] for event in events)


def _planned_samples(candidate, warmups, repeats):
    for phase, count in (("warmup", warmups), ("measurement", repeats)):
        for repetition in range(count):
            order = ["reference", candidate] if repetition % 2 == 0 else [candidate, "reference"]
            for position, implementation in enumerate(order):
                yield {"phase": phase, "repetition": repetition, "position": position,
                       "implementation": implementation, "order": order}


class _Audit:
    def __init__(self, run_dir, record):
        self.root, self.record = Path(run_dir), record
        self.errors, self.cursor, self.reference_outputs = [], 0, {}

    def check(self, condition, reason):
        if not condition:
            self.errors.append(reason)

    def event(self, process, stage, candidate, args, cwd=None, program=None, **extra):
        """Correlate a saved process with its unique position in the full ledger."""
        event = self.events[self.cursor]
        expected = {"event_id": self.cursor, "stage": stage, "candidate_id": candidate,
                    "args": args, "cwd": cwd, "category": process["category"],
                    "returncode": process["returncode"], "wall_seconds": process["wall_seconds"],
                    "program_sha256": program, "expected_program_sha256": program, **extra}
        self.check(all(event.get(k) == v for k, v in expected.items()),
                   f"process ledger mismatch at event {self.cursor}: {stage}/{candidate}")
        self.check(process["args"] == args, f"saved process arguments mismatch: {stage}/{candidate}")
        if "ledger_event_id" in process:
            self.check(process["ledger_event_id"] == self.cursor, f"reused or reordered process event: {stage}/{candidate}")
        self.cursor += 1

    def config_and_manifest(self):
        self.config = load_config(self.root / "config.json")
        self.events = _read(self.root / "process-ledger.json")
        self.manifest = _read(self.root / "candidate-manifest.json")
        self.frozen = _read(self.root / "measurement-freeze.json")
        r, m, f = self.record, self.manifest, self.frozen
        self.check(r["settings"] == self.config.to_dict(), "settings differ from saved validated configuration")
        self.check(r["execution_contract"] == asdict(ExecutionContract()), "common execution contract was changed")
        self.check(set(r["candidates"]) == set(CANDIDATE_IDS), "required diagnostic candidate set is incomplete or changed")
        self.check([c["candidate_id"] for c in m["candidates"]] == list(CANDIDATE_IDS), "manifest candidate order/set is not the predeclared family")
        self.check(m["factors"] == [1, 2, 4, 8, 16] and m["family"] == "independent_output_j_unrolling"
                   and m["series_baseline"] == "unroll_1" and m["measurement_baseline"] == "reference"
                   and m["fixed_before_measurement"] is True and bool(m["baseline_change"]), "invalid transformation-family manifest")
        self.check(m["compiler"] == r["compiler"], "CompilerTarget differs from frozen manifest")
        compiler = dict(r["compiler"])
        for key in ("target_flags", "optimization_flags", "floating_point_flags", "link_flags"):
            compiler[key] = tuple(compiler[key])
        self.target = CompilerTarget(**compiler)
        self.check(m["config_sha256"] == _hash(self.root / "config.json") == f["config_sha256"], "frozen configuration hash mismatch")
        self.check(r["manifest_sha256"] == _hash(self.root / "candidate-manifest.json") == f["manifest_sha256"], "frozen candidate manifest hash mismatch")
        self.check(r["measurement_freeze_sha256"] == _hash(self.root / "measurement-freeze.json"), "measurement freeze hash mismatch")
        self.check(m["generator_sha256"] == _hash(self.root / "runner_source/transformations.py"), "generator snapshot hash mismatch")
        self.check(m["source_fp_directives"]["kernel_fp_pragmas"] == [], "unexpected source FP directives in manifest")
        self.check(set(f["programs"]) == set(CANDIDATE_IDS) == set(f["verification"]), "frozen program/verification set is incomplete")
        self.check(r["operations"] == _read(self.root / "operations.json"), "operation duration records differ")
        expected_operations = [("setup_observations", None), ("generate_and_freeze_candidate_manifest", None)]
        expected_operations += [("build_and_analyze", name) for name in CANDIDATE_IDS]
        expected_operations += [("verify", name) for name in CANDIDATE_IDS]
        expected_operations += [(phase, None) for phase in PHASES] + [("render_reports", None)]
        self.check([(x["operation"], x["candidate_id"]) for x in r["operations"]] == expected_operations,
                   "required operation duration records missing or reordered")
        self.check(all(x["completed"] is True and math.isfinite(x["wall_seconds"]) and x["wall_seconds"] >= 0 for x in r["operations"]),
                   "invalid or incomplete operation durations")

    def builds(self):
        r, m = self.record, self.manifest
        for key in ("objdump", "readobj"):
            tool = r["tools"][key]
            self.event(tool["version"], "setup", None, [tool["path"], "--version"])
        expected_candidates = {c.candidate_id: c for c in make_candidates()}
        self.runtime_dirs = {}
        for name, item in zip(CANDIDATE_IDS, m["candidates"]):
            c, directory = r["candidates"][name], self.root / "candidates" / name
            expected = asdict(expected_candidates[name])
            source = expected.pop("source")
            self.check(all(c.get(k) == v == item.get(k) for k, v in expected.items()), f"candidate metadata/template mismatch: {name}")
            self.check((directory / "kernel.c").read_text(encoding="utf-8") == source, f"candidate source differs from the deterministic template/control: {name}")
            self.check(c["source_sha256"] == item["source_sha256"] == _hash(directory / "kernel.c"), f"candidate source hash mismatch: {name}")
            self.check(c["source_path"] == item["source_path"] == f"candidates/{name}/kernel.c", f"candidate source path mismatch: {name}")
            for file, key in (("harness.c", "driver_sha256"), ("kernel.h", "header_sha256")):
                self.check(_hash(directory / file) == m[key], f"common driver/header changed: {name}/{file}")
            self.check(c["build"]["passed"] is True and c["build"]["category"] == "ok", f"required candidate build failed: {name}")
            for filename, sha in c["build"]["source_hashes"].items():
                self.check(_hash(directory / filename) == sha, f"build source provenance mismatch: {name}/{filename}")
            self.check(set(c["build"]["source_hashes"]) == {"kernel.c", "kernel.h", "harness.c"}, f"build source hashes incomplete: {name}")
            self.check(c["build"]["source_fp_related_lines"] == {file: [] for file in ("kernel.c", "kernel.h", "harness.c")}, f"unexpected source FP policy: {name}")
            program, obj = _hash(directory / "program"), _hash(directory / "kernel.o")
            self.check(c["program_sha256"] == program == c["analysis"]["program_sha256"] == self.frozen["programs"][name], f"program hash disagreement: {name}")
            self.check(c["object_sha256"] == obj == c["analysis"]["object_sha256"], f"kernel object hash disagreement: {name}")
            self.check(c["analysis"]["harness_object_sha256"] == _hash(directory / "harness.o"), f"driver object hash disagreement: {name}")
            commands = c["build"]["commands"]
            runtime_dir = commands[0]["cwd"]
            self.runtime_dirs[name] = runtime_dir
            self.check(Path(runtime_dir).name == name and Path(runtime_dir).parent.name == "candidates", f"build working directory mismatch: {name}")
            common = [self.target.compiler, "-std=c11", *self.target.compile_flags, "-fno-lto"]
            expected_build = [
                ("kernel_object", [*common, "-fsave-optimization-record", "-foptimization-record-file=kernel.opt.yaml", "-c", "kernel.c", "-o", "kernel.o"]),
                ("harness_object", [*common, "-c", "harness.c", "-o", "harness.o"]),
                ("link", [self.target.compiler, *self.target.target_flags, "kernel.o", "harness.o", *self.target.link_flags, "-fno-lto", "-o", "program"]),
                ("llvm_ir", [*common, "-S", "-emit-llvm", "kernel.c", "-o", "kernel.ll"]),
                ("assembly", [*common, "-S", "kernel.c", "-o", "kernel.s"]),
            ]
            self.check([(x["stage"], x["args"]) for x in commands[:5]] == expected_build, f"build flags or translation units differ: {name}")
            objdump, readobj = r["tools"]["objdump"]["path"], r["tools"]["readobj"]["path"]
            expected_analysis = [
                ("symbol_metadata", [readobj, "--elf-output-style=JSON", "--sections", "--symbols", "program"], "program.symbols.json"),
                ("executed_program_disassembly", [objdump, "--disassemble", "--disassemble-zeroes", "program"], "program.disasm"),
                ("object_relocations", [objdump, "--reloc", "kernel.o"], "kernel.relocations.txt"),
            ]
            if len(commands) == 9:
                symbol, _ = extract_symbol_range((directory / "program").read_bytes(), _read(directory / "program.symbols.json"))
                expected_analysis.append(("kernel_disassembly", [objdump, "--disassemble-symbols=kernel", "--disassemble-zeroes",
                    f"--start-address={symbol['start_address']}", f"--stop-address={symbol['end_address_exclusive']}", "program"], "kernel.disasm"))
            self.check(len(commands) in (8, 9) and [(x["stage"], x["args"]) for x in commands[5:]] == [(stage, args) for stage, args, _ in expected_analysis], f"analysis commands did not inspect the linked executable: {name}")
            for command, (_, _, output) in zip(commands[5:], expected_analysis):
                self.check(command["stdout"] == (directory / output).read_text(), f"saved analysis output differs from recorded command: {name}/{output}")
            self.check(c["build"]["lto"] is False, f"LTO policy changed: {name}")
            for command in commands:
                self.check(command["cwd"] == runtime_dir, f"build working directory changed: {name}")
                self.event(command, "build_analysis", name, command["args"], runtime_dir)
            self._analysis(directory, c, name)

    def prompts(self):
        """Reconstruct the source/contract allowlist; CPU text remains explicit input."""
        directory = self.root / "prompts"
        payload, mapping = _common_payload(make_candidates(), ExecutionContract())
        common = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
        cpu = (directory / "cpu_spec.txt").read_text(encoding="utf-8")
        contents = {"common_payload.json": common, "cpu_spec.txt": cpu, "none.txt": common,
                    "spec.txt": common + CPU_SECTION_HEADER + cpu + "\n"}
        self.check(bool(cpu.strip()), "diagnostic CPU description is empty")
        for filename, expected in contents.items():
            self.check((directory / filename).read_text(encoding="utf-8") == expected,
                       f"prompt source/contract/CPU allowlist mismatch: {filename}")
        sha = lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
        expected_meta = {
            "purpose": "offline_diagnostic_selection_preparation", "llm_calls": 0,
            "option_mapping": mapping,
            "common_payload": {"path": "common_payload.json", "sha256": sha(common)},
            "cpu_spec": {"path": "cpu_spec.txt", "sha256": sha(cpu)},
        }
        for mode in ("none", "spec"):
            expected_meta[mode] = {"path": f"{mode}.txt", "sha256": sha(contents[f"{mode}.txt"]),
                                   "common_payload_sha256": sha(common), "cpu_spec_sha256": sha(cpu) if mode == "spec" else None}
        self.check(self.record["prompts"] == expected_meta, "diagnostic prompt hash/option provenance mismatch")

    def _analysis(self, directory, candidate, name):
        analysis = candidate["analysis"]
        self.check(analysis["intended_transformation_status"] == "unknown" and analysis["full_equivalence_claim"] is False,
                   f"unsupported transformation/equivalence claim: {name}")
        self.check(analysis["dependencies"]["closure_proven"] is False, f"unsupported external-dependency closure claim: {name}")
        if analysis["status"] == "available":
            symbol, raw = extract_symbol_range((directory / "program").read_bytes(), _read(directory / "program.symbols.json"))
            self.check(symbol == analysis["symbol"], f"saved kernel symbol bounds differ: {name}")
            self.check(raw == (directory / "kernel.bytes").read_bytes(), f"kernel bytes differ from measured executable: {name}")
            self.check(analysis["extracted_bytes"] == {"path": "kernel.bytes", "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}, f"kernel range hash mismatch: {name}")
            text = (directory / "kernel.disasm").read_text()
            instructions = verify_disassembly(text, symbol, raw)
            full = (directory / "program.disasm").read_text()
            main_symbol, main_raw = extract_symbol_range((directory / "program").read_bytes(), _read(directory / "program.symbols.json"), "main")
            verify_disassembly(full, main_symbol, main_raw)
            self.check(analysis["driver_call_evidence"] == _driver_calls(full, symbol["start_address"]), f"analyzed kernel is not the timed driver target: {name}")
            self.check(analysis["dependencies"] == _dependencies(instructions), f"external-dependency observations differ: {name}")
            self.check((directory / "kernel.normalized.txt").read_text() == normalize_disassembly(instructions), f"normalized code removed or altered an operand: {name}")
            self.check(analysis["disassembly"]["sha256"] == _hash(directory / "kernel.disasm"), f"disassembly provenance mismatch: {name}")
            self.check(analysis["disassembly"]["instruction_count"] == len(instructions) and analysis["disassembly"]["coverage_verified_against_executable"] is True, f"incomplete instruction coverage: {name}")
        else:
            self.check(analysis["status"] == "analysis_unavailable" and bool(analysis["reason"]), f"analysis missing without a reason: {name}")
        optimization = parse_optimization_record(directory / "kernel.opt.yaml")
        optimization.update(object_sha256=analysis["object_sha256"], emission_stage="kernel_object")
        self.check(optimization == candidate["optimization"], f"optimization summary differs from raw compiler evidence: {name}")

    def verification(self):
        for name in CANDIDATE_IDS:
            c = self.record["candidates"][name]
            directory = self.root / "candidates" / name
            validations = c["verification"]["cases"]
            self.check([(x["size"], x["seed"]) for x in validations] == self.config.cases(), f"required ordered verification cases missing/duplicated: {name}")
            verdicts = []
            for case in validations:
                n, seed, p = case["size"], case["seed"], case["process"]
                stdout_path, stderr_path = directory / p["stdout_path"], directory / p["stderr_path"]
                self.check(stdout_path.resolve().is_relative_to(directory.resolve()) and stderr_path.resolve().is_relative_to(directory.resolve()), f"verification output path escapes candidate: {name}")
                self.check(_hash(stdout_path) == p["stdout_sha256"] and _hash(stderr_path) == p["stderr_sha256"], f"verification output hash mismatch: {name}")
                process = ProcessResult(p["args"], p["category"], p["returncode"], stdout_path.read_text(), stderr_path.read_text(), p["wall_seconds"])
                verdict, values = validate_result(process, n * n, None if name == "reference" else self.reference_outputs[(n, seed)])
                saved = {k: v for k, v in case.items() if k not in ("size", "seed", "process")}
                self.check(verdict == saved, f"verification verdict does not match saved output bits: {name}/{n}/{seed}")
                verdicts.append(verdict)
                if name == "reference" and verdict["passed"]:
                    self.reference_outputs[(n, seed)] = values
                self.check(p["program_sha256"] == c["program_sha256"], f"verification binary hash mismatch: {name}")
                args = [str(Path(self.runtime_dirs[name]) / "program"), "verify", str(n), str(seed)]
                self.event(p, "verification", name, args, program=c["program_sha256"],
                           verification_passed=verdict["passed"], verification_category=verdict["category"])
            failures = [x for x in verdicts if not x["passed"]]
            self.check(c["verification"]["passed"] == (not failures) and c["verification"]["category"] == (failures[0]["category"] if failures else "ok"), f"verification aggregate mismatch: {name}")
            self.check(bool(verdicts) and (all(v["category"] == "value_mismatch" for v in verdicts) if name == "deliberately_wrong" else all(v["passed"] for v in verdicts)), f"required control correctness outcome failed: {name}")
            frozen = self.frozen["verification"][name]
            self.check(frozen == {"passed": c["verification"]["passed"], "path": f"candidates/{name}/verification.json", "sha256": _hash(directory / "verification.json")}, f"frozen verification mismatch: {name}")
            base = self.record["candidates"][c["comparison_baseline"]]
            comparison = compare_kernels(base["analysis"], c["analysis"])
            comparison.update(baseline_candidate_id=c["comparison_baseline"], evidence_paths=[base["evidence"]["analysis_path"], c["evidence"]["analysis_path"]])
            self.check(c["comparison"] == comparison, f"kernel comparison not derived from extracted ranges: {name}")

    def measurements(self):
        self.check(set(self.record["phases"]) == set(PHASES), "exploration/confirmation phase missing or unexpected")
        eligible = {name for name in CANDIDATE_IDS if name != "reference" and self.record["candidates"][name]["verification"]["passed"]}
        from .clock_provenance import phase_clock_warnings
        clock_warnings = phase_clock_warnings(self.record["phases"])
        for phase in PHASES:
            row = self.record["phases"][phase]
            seed = getattr(self.config, phase + "_order_seed")
            rng, orders, skipped = random.Random(seed), [], []
            self.check(row["phase"] == phase and row["order_seed"] == seed and row["measurement_freeze_sha256"] == self.record["measurement_freeze_sha256"], f"phase configuration/freeze mismatch: {phase}")
            if "started_clock" in row or "completed_clock" in row:
                self.check(row.get("clock_warnings") == clock_warnings[phase], f"measurement phase clock warnings differ: {phase}")
            self.check(set(row["measurements"]) == eligible, f"verified candidate measurement set missing/changed: {phase}")
            required_cases = {_case_id(n, s) for n, s in self.config.measure_cases}
            for name in eligible:
                self.check(set(row["measurements"][name]) == required_cases, f"measurement condition missing/changed: {phase}/{name}")
            for n, input_seed in self.config.measure_cases:
                cid = _case_id(n, input_seed)
                order = list(CANDIDATE_IDS[1:])
                rng.shuffle(order)
                orders.append({"case_id": cid, "candidate_ids": order})
                for position, name in enumerate(order):
                    if name not in eligible:
                        skipped.append({"candidate_id": name, "case_id": cid, "reason": self.record["candidates"][name]["verification"]["category"]})
                        self.check(not (self.root / "phases" / phase / f"{name}-{cid}.json").exists(), f"rejected candidate has a timing artifact: {phase}/{name}")
                        continue
                    measured = row["measurements"][name][cid]
                    context = {"phase": phase, "case_id": cid, "candidate_id": name, "measurement_freeze_sha256": self.record["measurement_freeze_sha256"]}
                    self.check(all(measured.get(k) == v for k, v in context.items()), f"measurement identity mismatch: {phase}/{name}/{cid}")
                    planned = list(_planned_samples(name, self.config.warmups, self.config.repeats))
                    self.check(len(measured["samples"]) == len(planned), f"warmup/repeat sample count differs from preregistration: {phase}/{name}/{cid}")
                    for sample, expected in zip(measured["samples"], planned):
                        expected.update(size=n, seed=input_seed, pair_candidate=name, candidate_order_position=position, experiment_phase=phase)
                        self.check(all(sample.get(k) == v for k, v in expected.items()), f"paired order/input/phase mismatch: {phase}/{name}/{cid}")
                        implementation = expected["implementation"]
                        program = self.record["candidates"][implementation]["program_sha256"]
                        p = sample["process"]
                        parsed = parse_measurement(p["stdout"]) if p["category"] == "ok" else {}
                        self.check(p["category"] == sample["category"] == "ok" and all(sample.get(k) == v for k, v in parsed.items()), f"raw measurement output/status mismatch: {phase}/{name}/{cid}")
                        self.check(sample["program_sha256"] == program, f"measurement binary mismatch: {phase}/{name}/{cid}")
                        args = [str(Path(self.runtime_dirs[implementation]) / "program"), "measure", str(n), str(input_seed)]
                        self.check(sample["ledger_event_id"] == self.cursor, f"measurement reused a ledger event: {phase}/{name}/{cid}")
                        self.event(p, phase, name, args, program=program, sample_phase=sample["phase"], case_id=cid)
                    rebuilt = summarize_measurement(measured, asdict(self.config.quality))
                    self.check(measured["passed"] is True and all(measured[k] == rebuilt[k] for k in ("passed", "summary", "warnings")), f"measurement summary/quality warnings differ from raw samples: {phase}/{name}/{cid}")
            self.check(row["candidate_order_by_case"] == orders, f"candidate order does not match seeded shuffle: {phase}")
            self.check(row["skipped"] == skipped, f"rejected candidate skip records mismatch: {phase}")

    def costs_and_reports(self):
        self.check(self.cursor == len(self.events), "unmatched or missing process ledger events")
        self.check([x["event_id"] for x in self.events] == list(range(len(self.events))), "process event IDs are duplicated/reordered")
        for event in self.events:
            elapsed = event["wall_seconds"]
            self.check(type(event["process_attempted"]) is bool and isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool) and math.isfinite(elapsed) and elapsed >= 0, "invalid process execution/duration ledger field")
            if event["category"] == "ok":
                self.check(event["process_attempted"] is True and event["returncode"] == 0, "successful ledger event was not executed successfully")
            if not event["process_attempted"]:
                self.check(event["category"] == "artifact_changed" and event["returncode"] is None, "unattempted process lacks recorded artifact-change failure")
        stages, count = _cost_totals(self.events)
        self.check(self.record["costs"]["stages"] == stages and self.record["costs"]["execution_count"] == count, "cost totals exclude or miscount process/verification failures or phases")
        source = dict(self.record)
        source["candidates"] = {name: self.record["candidates"][name] for name in CANDIDATE_IDS}
        report = build_report(source)
        self.check(_canonical_warnings(report) == _canonical_warnings(_read(self.root / "report.json")), "JSON report statuses/ranks/warnings are not derived from the raw phase data")
        expected_rows = [{k: "" if v is None else str(v) for k, v in row.items()} for row in _csv_rows(report)]
        with (self.root / "report.csv").open(newline="", encoding="utf-8") as stream:
            saved_rows = list(csv.DictReader(stream))
        sort_rows = lambda rows: sorted(rows, key=lambda x: (x["candidate_id"], x["phase"], x["case_id"]))
        self.check(sort_rows(expected_rows) == sort_rows(saved_rows), "CSV report statuses/ranks/warnings differ from the reconstructed report")
        self.check((self.root / "report.md").read_text(encoding="utf-8") == render_markdown(report), "Markdown report differs from the reconstructed report")


def audit_semantics(run_dir, record):
    """Return semantic artifact errors without executing any saved code or process."""
    audit = _Audit(run_dir, record)
    for stage in (audit.config_and_manifest, audit.prompts, audit.builds, audit.verification, audit.measurements, audit.costs_and_reports):
        try:
            stage()
        except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
            audit.errors.append(f"incomplete or invalid {stage.__name__} evidence: {exc}")
    return audit.errors
