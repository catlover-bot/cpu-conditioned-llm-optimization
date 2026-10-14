"""Conservative evidence from the exact linked executable used by diagnostics.

Equality here means only identical bytes in the extracted ELF function range.
It never establishes semantic equivalence or equality of external dependencies.
"""

import hashlib
import json
from pathlib import Path
import re

from .process import run_process


class AnalysisError(ValueError):
    """The available evidence does not support extracting the requested range."""


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def extract_symbol_range(program_bytes, metadata, symbol="kernel"):
    """Extract an ELF x86-64 STT_FUNC range using saved llvm-readobj JSON.

    A section's virtual address is not assumed to equal its file offset.
    Ambiguous/zero-sized symbols and unsupported layouts fail conservatively.
    """
    try:
        if not isinstance(metadata, list) or len(metadata) != 1:
            raise AnalysisError("expected exactly one ELF file in symbol metadata")
        item = metadata[0]
        summary = item["FileSummary"]
        if summary["Format"] != "elf64-x86-64":
            raise AnalysisError("only ELF x86-64 extraction has been validated")
        symbols = [s["Symbol"] for s in item["Symbols"] if s["Symbol"]["Name"]["Name"] == symbol]
        if len(symbols) != 1:
            raise AnalysisError(f"expected one {symbol} symbol; found {len(symbols)}")
        entry = symbols[0]
        if entry["Type"]["Name"] != "Function":
            raise AnalysisError("target symbol is not a function")
        start, size = entry["Value"], entry["Size"]
        if type(start) is not int or type(size) is not int or start < 0 or size <= 0:
            raise AnalysisError("invalid or zero-sized function range")
        sections = [s["Section"] for s in item["Sections"] if s["Section"]["Index"] == entry["Section"]["Value"]]
        if len(sections) != 1:
            raise AnalysisError("function section is missing or ambiguous")
        section = sections[0]
        if section["Type"]["Name"] != "SHT_PROGBITS" or not section["Flags"]["Value"] & 4:
            raise AnalysisError("function is not in a file-backed executable section")
        address, offset, section_size = section["Address"], section["Offset"], section["Size"]
        if any(type(v) is not int or v < 0 for v in (address, offset, section_size)):
            raise AnalysisError("invalid section bounds")
        delta = start - address
        file_offset = offset + delta
        if delta < 0 or delta + size > section_size or offset + section_size > len(program_bytes):
            raise AnalysisError("function or section range exceeds executable bounds")
        extracted = program_bytes[file_offset:file_offset + size]
        if len(extracted) != size:
            raise AnalysisError("truncated function bytes")
        return {"name": symbol, "start_address": start, "end_address_exclusive": start + size,
                "size_bytes": size, "section": section["Name"]["Name"], "file_offset": file_offset}, extracted
    except (KeyError, TypeError, IndexError) as exc:
        raise AnalysisError(f"malformed symbol metadata: {exc}") from exc


_INSTRUCTION = re.compile(r"^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2}\s+)+)(\S.*)$")


def verify_disassembly(text, symbol, extracted):
    """Require complete, contiguous instruction-byte coverage of the ELF range."""
    instructions = []
    offset = 0
    for line in text.splitlines():
        match = _INSTRUCTION.match(line)
        if not match:
            continue
        address = int(match[1], 16)
        if not symbol["start_address"] <= address < symbol["end_address_exclusive"]:
            continue
        raw = bytes.fromhex(match[2])
        if address != symbol["start_address"] + offset:
            raise AnalysisError("disassembly coverage is not contiguous")
        if raw != extracted[offset:offset + len(raw)]:
            raise AnalysisError("disassembly bytes differ from the executable range")
        if "<unknown>" in match[3]:
            raise AnalysisError("disassembler could not decode an instruction")
        instructions.append({"offset": offset, "bytes_hex": raw.hex(), "instruction": match[3].strip()})
        offset += len(raw)
    if offset != len(extracted) or not instructions:
        raise AnalysisError("disassembly does not cover the complete function range")
    return instructions


def normalize_disassembly(instructions):
    """Display only: replace leading addresses by offsets, preserve byte/operand text.

    This is never used for the comparison decision. In particular, immediates,
    RIP-relative displacements and branch destination operands are retained.
    """
    return "".join(f"+0x{x['offset']:x}: {x['bytes_hex']} {x['instruction']}\n" for x in instructions)


def _dependencies(instructions):
    symbols, references, indirect = set(), [], []
    for item in instructions:
        text = item["instruction"]
        for name in re.findall(r"<([^>]+)>", text):
            if name != "kernel" and not name.startswith("kernel+"):
                symbols.add(name)
        if "%rip" in text:
            references.append(item)
        if re.match(r"(?:callq?|jmpq?)\s+\*", text):
            indirect.append(item)
    return {"observed_external_symbols": sorted(symbols), "rip_relative_references": references,
            "indirect_control_transfers": indirect, "closure_proven": False,
            "reason": "External helper/data dependencies are not recursively resolved; whole-program equivalence is not claimed.",
            "object_relocations_path": "kernel.relocations.txt"}


def _driver_calls(full_disassembly, target):
    match = re.search(r"^[0-9a-fA-F]+ <main>:\s*\n(.*?)(?=^[0-9a-fA-F]+ <|\Z)",
                      full_disassembly, re.MULTILINE | re.DOTALL)
    if not match:
        raise AnalysisError("main function unavailable in executed-program disassembly")
    lines = match[1].splitlines()
    calls = [i for i, line in enumerate(lines)
             if re.search(r"\bcallq?\s+0x" + format(target, "x") + r"\s+<kernel>", line)]
    clocks = [i for i, line in enumerate(lines) if re.search(r"\bcallq?\s+.*<clock_gettime(?:@[^>]*)?>", line)]
    bracketed = [i for i in calls if any(a < i < b for a, b in zip(clocks, clocks[1:]))]
    if not bracketed:
        raise AnalysisError("direct kernel call between clock_gettime calls not found in main")
    return {"status": "direct_call_between_clock_calls_observed", "path": "program.disasm",
            "target_address": target, "call_site_lines": [lines[i].strip() for i in bracketed],
            "scope": "Static main disassembly plus the saved common harness source; not a dynamic execution trace."}


def parse_optimization_record(path):
    """Index LLVM's YAML documents without claiming to be a general YAML parser.

    Scalar fields remain raw YAML, and every remark retains the original lines.
    Unknown tags are retained; AnalysisFPCommute/AnalysisAliasing count as Analysis.
    """
    path = Path(path)
    result = {"status": "unavailable", "reason": None, "source_path": path.name, "source_sha256": None,
              "counts": {"Passed": 0, "Missed": 0, "Analysis": 0, "Other": 0}, "remarks": [],
              "parser": "conservative LLVM YAML document index; scalar fields preserved verbatim",
              "interpretation": "Missing or empty remarks do not prove that an optimization did not occur."}
    if not path.is_file():
        result["reason"] = "optimization record file missing"
        return result
    raw = path.read_bytes()
    result["source_sha256"] = _sha(raw)
    text = raw.decode("utf-8", errors="replace")
    if not text.strip():
        result.update(status="no_remarks_emitted", reason="compiler emitted an empty optimization record")
        return result
    lines = text.splitlines()
    starts = [(i, re.fullmatch(r"---\s+!([A-Za-z][A-Za-z0-9_]*)\s*", line)) for i, line in enumerate(lines)]
    starts = [(i, match[1]) for i, match in starts if match]
    if not starts:
        result.update(status="unparsed", reason="no supported LLVM YAML document markers found")
        return result
    for index, (start, tag) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(lines)
        block = lines[start:end]
        kind = "Analysis" if tag.startswith("Analysis") else tag if tag in ("Passed", "Missed") else "Other"
        remark = {"kind": kind, "exact_tag": tag, "start_line": start + 1, "end_line": end,
                  "raw_excerpt": "\n".join(block) + "\n"}
        for field in ("Pass", "Name", "Function", "DebugLoc"):
            value = next((line.split(":", 1)[1].strip() for line in block if line.startswith(field + ":")), None)
            remark[field.lower() + "_raw"] = value
        result["remarks"].append(remark)
        result["counts"][kind] += 1
    result["status"] = "available"
    return result


def compare_kernels(left, right):
    """Compare only exact extracted executable-range bytes, represented by SHA-256."""
    result = {"status": "analysis_unavailable", "reason": None,
              "scope": "exact bytes of the linked executable ELF kernel function range",
              "full_equivalence_claim": False, "intended_transformation_status": "unknown",
              "limitations": ["External helpers/constants are outside the compared range.",
                              "A byte difference does not prove that the intended source transformation survived.",
                              "Instruction count and code size do not predict performance."],
              "left": {k: left.get(k) for k in ("status", "program_sha256", "symbol", "extracted_bytes")},
              "right": {k: right.get(k) for k in ("status", "program_sha256", "symbol", "extracted_bytes")}}
    if left.get("status") != "available" or right.get("status") != "available":
        result["reason"] = "one or both kernel extractions are unavailable"
        return result
    try:
        a, b = left["extracted_bytes"]["sha256"], right["extracted_bytes"]["sha256"]
        if not all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{64}", x) for x in (a, b)):
            raise ValueError("missing or invalid extracted-byte hash")
        sizes = []
        for item in (left, right):
            size = item["extracted_bytes"]["size_bytes"]
            if type(size) is not int or size <= 0 or item["symbol"]["size_bytes"] != size:
                raise ValueError("missing or inconsistent extracted range size")
            sizes.append(size)
        result["status"] = "same_in_extracted_scope" if a == b and sizes[0] == sizes[1] else "different_in_extracted_scope"
    except (KeyError, TypeError, ValueError) as exc:
        result["reason"] = str(exc)
    return result


def build_and_analyze(directory, target, tool_paths, timeout=30.0, run=run_process):
    """Build, retain compiler diagnostics, and inspect the exact executable.

    Every child process goes through ``run`` so the caller can maintain a ledger.
    All artifact paths are directory-local. No candidate execution happens here.
    """
    directory = Path(directory)
    commands = []

    def execute(stage, args, output=None):
        result = run(args, cwd=directory, timeout=timeout)
        commands.append({"stage": stage, "cwd": str(directory), **result.to_dict()})
        if output is not None:
            (directory / output).write_text(result.stdout, encoding="utf-8")
        return result

    common = [target.compiler, "-std=c11", *target.compile_flags, "-fno-lto"]
    stages = [
        ("kernel_object", [*common, "-fsave-optimization-record", "-foptimization-record-file=kernel.opt.yaml", "-c", "kernel.c", "-o", "kernel.o"]),
        ("harness_object", [*common, "-c", "harness.c", "-o", "harness.o"]),
        ("link", [target.compiler, *target.target_flags, "kernel.o", "harness.o", *target.link_flags, "-fno-lto", "-o", "program"]),
        ("llvm_ir", [*common, "-S", "-emit-llvm", "kernel.c", "-o", "kernel.ll"]),
        ("assembly", [*common, "-S", "kernel.c", "-o", "kernel.s"]),
    ]
    build = {"passed": True, "category": "ok", "commands": commands, "lto": False,
             "analysis_role": "linked executable is authoritative; IR and Assembly are auxiliary emissions",
             "source_hashes": {}, "source_fp_related_lines": {},
             "fp_source_scan_scope": "lines containing FP/floating-point/optimization pragmas or fast-math attributes; originals retained"}
    for filename in ("kernel.c", "kernel.h", "harness.c"):
        source = (directory / filename).read_bytes()
        build["source_hashes"][filename] = _sha(source)
        build["source_fp_related_lines"][filename] = [
            {"line": i, "text": line} for i, line in enumerate(source.decode("utf-8").splitlines(), 1)
            if re.search(r"(?:#\s*pragma.*(?:FP|fp|float|optimize)|__attribute__.*(?:optimize|fast.math))", line)]
    for stage, args in stages:
        result = execute(stage, args)
        if result.category != "ok":
            build.update(passed=False, category="timeout" if result.category == "timeout" else "compile_failure")
            break
    analysis = {"status": "analysis_unavailable", "reason": "build did not succeed",
                "program_sha256": None, "object_sha256": None, "symbol": None, "extracted_bytes": None,
                "disassembly": None, "dependencies": {"closure_proven": False},
                "intended_transformation_status": "unknown", "full_equivalence_claim": False}
    if build["passed"]:
        program_bytes = (directory / "program").read_bytes()
        analysis.update(program_sha256=_sha(program_bytes), object_sha256=_sha((directory / "kernel.o").read_bytes()))
        analysis["harness_object_sha256"] = _sha((directory / "harness.o").read_bytes())
        try:
            objdump, readobj = tool_paths["objdump"], tool_paths["readobj"]
            meta = execute("symbol_metadata", [readobj, "--elf-output-style=JSON", "--sections", "--symbols", "program"], "program.symbols.json")
            full = execute("executed_program_disassembly", [objdump, "--disassemble", "--disassemble-zeroes", "program"], "program.disasm")
            reloc = execute("object_relocations", [objdump, "--reloc", "kernel.o"], "kernel.relocations.txt")
            if any(x.category != "ok" for x in (meta, full, reloc)):
                raise AnalysisError("a required executable-analysis command failed")
            symbol, extracted = extract_symbol_range(program_bytes, json.loads(meta.stdout))
            dis = execute("kernel_disassembly", [objdump, "--disassemble-symbols=kernel", "--disassemble-zeroes",
                          f"--start-address={symbol['start_address']}", f"--stop-address={symbol['end_address_exclusive']}", "program"], "kernel.disasm")
            if dis.category != "ok":
                raise AnalysisError("kernel disassembly command failed")
            instructions = verify_disassembly(dis.stdout, symbol, extracted)
            driver = _driver_calls(full.stdout, symbol["start_address"])
            if (directory / "program").read_bytes() != program_bytes:
                raise AnalysisError("executable changed while gathering analysis evidence")
            (directory / "kernel.bytes").write_bytes(extracted)
            (directory / "kernel.normalized.txt").write_text(normalize_disassembly(instructions), encoding="utf-8")
            analysis.update(status="available", reason=None, symbol=symbol,
                            extracted_bytes={"path": "kernel.bytes", "sha256": _sha(extracted), "size_bytes": len(extracted)},
                            disassembly={"path": "kernel.disasm", "sha256": _sha(dis.stdout.encode("utf-8")),
                                         "program_path": "program.disasm", "normalization_path": "kernel.normalized.txt",
                                         "instruction_count": len(instructions), "coverage_verified_against_executable": True},
                            dependencies=_dependencies(instructions), driver_call_evidence=driver,
                            extraction_method="llvm-readobj JSON function symbol size and section file-offset mapping; cross-checked against llvm-objdump instruction bytes",
                            symbol_metadata_path="program.symbols.json",
                            normalization="Display-only function-relative address prefixes; bytes and operands retained verbatim; comparison uses original extracted-byte SHA-256.")
        except (AnalysisError, OSError, ValueError, KeyError, TypeError) as exc:
            analysis["reason"] = str(exc)
    optimization = parse_optimization_record(directory / "kernel.opt.yaml")
    optimization["object_sha256"] = analysis["object_sha256"]
    optimization["emission_stage"] = "kernel_object"
    _save(directory / "build.json", build)
    _save(directory / "analysis.json", analysis)
    _save(directory / "optimization.json", optimization)
    return {"build": build, "analysis": analysis, "optimization": optimization}
