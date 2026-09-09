"""Compiler evidence tests; this module never times or executes a candidate."""

import copy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from cpucond.code_analysis import (
    AnalysisError, build_and_analyze, compare_kernels, extract_symbol_range,
    normalize_disassembly, parse_optimization_record, verify_disassembly,
)
from cpucond.host import discover_compiler
from cpucond.process import ProcessResult, run_process


def metadata(size=3):
    return [{"FileSummary": {"Format": "elf64-x86-64"},
             "Symbols": [{"Symbol": {"Name": {"Name": "kernel"}, "Type": {"Name": "Function"},
                                      "Value": 0x1002, "Size": size, "Section": {"Value": 4}}}],
             "Sections": [{"Section": {"Index": 4, "Name": {"Name": ".text"},
                                         "Type": {"Name": "SHT_PROGBITS"}, "Flags": {"Value": 6},
                                         "Address": 0x1000, "Offset": 8, "Size": 8}}]}]


def test_symbol_range_maps_virtual_address_to_file_offset():
    image = b"header!!" + b"abcdefgh"
    symbol, raw = extract_symbol_range(image, metadata())
    assert symbol["file_offset"] == 10
    assert symbol["start_address"] == 0x1002
    assert symbol["end_address_exclusive"] == 0x1005
    assert raw == b"cde"


@pytest.mark.parametrize("mutation", ["missing", "ambiguous", "zero", "not_function", "outside",
                                       "nonexecuting", "nobits", "truncated", "unsupported", "malformed"])
def test_unavailable_or_ambiguous_function_ranges_fail_closed(mutation):
    data = metadata()
    image = b"0" * 16
    symbol = data[0]["Symbols"][0]["Symbol"]
    section = data[0]["Sections"][0]["Section"]
    if mutation == "missing":
        data[0]["Symbols"] = []
    elif mutation == "ambiguous":
        data[0]["Symbols"] *= 2
    elif mutation == "zero":
        symbol["Size"] = 0
    elif mutation == "not_function":
        symbol["Type"]["Name"] = "Object"
    elif mutation == "outside":
        symbol["Size"] = 99
    elif mutation == "nonexecuting":
        section["Flags"]["Value"] = 2
    elif mutation == "nobits":
        section["Type"]["Name"] = "SHT_NOBITS"
    elif mutation == "truncated":
        image = image[:12]
    elif mutation == "unsupported":
        data[0]["FileSummary"]["Format"] = "elf64-aarch64"
    else:
        del symbol["Section"]
    with pytest.raises(AnalysisError):
        extract_symbol_range(image, data)


def test_disassembly_requires_exact_complete_executable_byte_coverage():
    symbol, raw = extract_symbol_range(b"header!!xx\x90\x90\xc3xxx", metadata())
    text = "0000000000001002 <kernel>:\n 1002: 90 nop\n 1003: 90 nop\n 1004: c3 retq\n"
    instructions = verify_disassembly(text, symbol, raw)
    assert len(instructions) == 3
    for damaged in (text.replace("1003: 90", "1003: 91"), text.replace("1003: 90 nop\n", ""),
                    text.replace("1003:", "1004:"), text.replace("nop", "<unknown>", 1)):
        with pytest.raises(AnalysisError):
            verify_disassembly(damaged, symbol, raw)


def analysis_for(raw):
    return {"status": "available", "program_sha256": "f" * 64,
            "symbol": {"name": "kernel", "size_bytes": len(raw)},
            "extracted_bytes": {"path": "kernel.bytes", "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}}


@pytest.mark.parametrize("before,after,operands", [
    (b"\x83\xc0\x01", b"\x83\xc0\x02", ("addl $0x1, %eax", "addl $0x2, %eax")),
    (b"\x8b\x40\x08", b"\x8b\x40\x10", ("movl 0x8(%rax), %eax", "movl 0x10(%rax), %eax")),
    (b"\x75\x04", b"\x75\x08", ("jne 0x1008 <kernel+0x8>", "jne 0x100c <kernel+0xc>")),
])
def test_immediates_memory_offsets_and_branches_are_preserved(before, after, operands):
    left = normalize_disassembly([{"offset": 0, "bytes_hex": before.hex(), "instruction": operands[0]}])
    right = normalize_disassembly([{"offset": 0, "bytes_hex": after.hex(), "instruction": operands[1]}])
    assert operands[0] in left and operands[1] in right
    assert left != right
    assert compare_kernels(analysis_for(before), analysis_for(after))["status"] == "different_in_extracted_scope"


def test_same_range_is_scoped_and_never_claims_full_equivalence():
    left = analysis_for(b"\xc3")
    right = copy.deepcopy(left)
    right["program_sha256"] = "a" * 64  # Whole-program bytes are outside the comparison.
    result = compare_kernels(left, right)
    assert result["status"] == "same_in_extracted_scope"
    assert result["full_equivalence_claim"] is False
    assert result["intended_transformation_status"] == "unknown"
    assert compare_kernels(left, {"status": "analysis_unavailable"})["status"] == "analysis_unavailable"
    right["extracted_bytes"]["sha256"] = "invalid"
    assert compare_kernels(left, right)["status"] == "analysis_unavailable"


def test_optimization_index_preserves_analysis_subtypes_and_evidence(tmp_path):
    path = tmp_path / "kernel.opt.yaml"
    raw = ("--- !Passed\nPass: loop-unroll\nName: PartialUnrolled\nFunction: kernel\nArgs:\n"
           "  - UnrollCount: '4'\n...\n--- !Missed\nPass: loop-vectorize\nName: MissedDetails\n...\n"
           "--- !AnalysisFPCommute\nPass: loop-vectorize\nName: CantReorderFPOps\n...\n"
           "--- !Analysis\nPass: prologepilog\nName: StackSize\n...\n--- !Failure\nName: Example\n...\n")
    path.write_text(raw)
    result = parse_optimization_record(path)
    assert result["status"] == "available"
    assert result["counts"] == {"Passed": 1, "Missed": 1, "Analysis": 2, "Other": 1}
    assert result["remarks"][2]["exact_tag"] == "AnalysisFPCommute"
    assert result["remarks"][0]["pass_raw"] == "loop-unroll"
    assert "UnrollCount: '4'" in result["remarks"][0]["raw_excerpt"]
    assert "".join(x["raw_excerpt"] for x in result["remarks"]) == raw
    assert result["source_sha256"] == hashlib.sha256(raw.encode()).hexdigest()


def test_missing_empty_and_unsupported_reports_are_distinguished(tmp_path):
    path = tmp_path / "kernel.opt.yaml"
    assert parse_optimization_record(path)["status"] == "unavailable"
    path.write_text("")
    assert parse_optimization_record(path)["status"] == "no_remarks_emitted"
    path.write_text("unrecognized text\n")
    assert parse_optimization_record(path)["status"] == "unparsed"


@pytest.fixture(scope="module")
def built_analysis(tmp_path_factory):
    directory = tmp_path_factory.mktemp("compiled-analysis")
    fixtures = Path(__file__).resolve().parents[1] / "src/cpucond/fixtures"
    for source, dest in (("identity.c", "kernel.c"), ("harness.c", "harness.c"), ("kernel.h", "kernel.h")):
        shutil.copyfile(fixtures / source, directory / dest)
    calls = []
    def recording_run(args, **kwargs):
        calls.append([str(x) for x in args])
        assert "measure" not in args and "verify" not in args
        return run_process(args, **kwargs)
    result = build_and_analyze(directory, discover_compiler(),
                               {"objdump": shutil.which("llvm-objdump"), "readobj": shutil.which("llvm-readobj")},
                               run=recording_run)
    return directory, result, calls


@pytest.mark.integration
def test_real_linked_kernel_bytes_match_executable_and_actual_driver_call(built_analysis):
    directory, result, calls = built_analysis
    assert result["build"]["passed"], result
    analysis = result["analysis"]
    assert analysis["status"] == "available", analysis
    symbol = analysis["symbol"]
    raw = (directory / "program").read_bytes()
    start = symbol["file_offset"]
    assert raw[start:start + symbol["size_bytes"]] == (directory / "kernel.bytes").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == analysis["program_sha256"]
    assert analysis["disassembly"]["coverage_verified_against_executable"]
    assert analysis["driver_call_evidence"]["status"] == "direct_call_between_clock_calls_observed"
    assert analysis["dependencies"]["closure_proven"] is False
    assert len(calls) == len(result["build"]["commands"]) == 9
    for filename, item in (("build.json", "build"), ("analysis.json", "analysis"), ("optimization.json", "optimization")):
        assert json.loads((directory / filename).read_text()) == result[item]
    for args in calls[:5]:
        assert "-fno-lto" in args
    assert "-foptimization-record-file=kernel.opt.yaml" in calls[0]
    assert all(not any(x.startswith("-foptimization-record-file") for x in args) for args in calls[1:])
    assert result["optimization"]["status"] == "available"
    assert result["optimization"]["counts"]["Analysis"] > 0


@pytest.mark.integration
def test_analysis_failure_preserves_successful_build_and_explicit_unavailable(tmp_path):
    fixtures = Path(__file__).resolve().parents[1] / "src/cpucond/fixtures"
    for source, dest in (("identity.c", "kernel.c"), ("harness.c", "harness.c"), ("kernel.h", "kernel.h")):
        shutil.copyfile(fixtures / source, tmp_path / dest)
    def missing_symbols(args, **kwargs):
        if "--symbols" in args:
            return ProcessResult(list(args), "ok", 0, "[]", "", 0)
        return run_process(args, **kwargs)
    result = build_and_analyze(tmp_path, discover_compiler(),
                               {"objdump": shutil.which("llvm-objdump"), "readobj": shutil.which("llvm-readobj")},
                               run=missing_symbols)
    assert result["build"]["passed"]
    assert result["analysis"]["status"] == "analysis_unavailable"
    assert result["analysis"]["reason"]
    assert result["analysis"]["program_sha256"]
    assert not (tmp_path / "kernel.bytes").exists()
