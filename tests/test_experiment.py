import json
import os
import shutil

import pytest

from cpucond import experiment as exp
from cpucond.host import discover_compiler
from cpucond.process import ProcessResult


@pytest.fixture(scope="module")
def completed_run(tmp_path_factory):
    # Missing required compilers fails this integration suite, not a silent skip.
    assert shutil.which("clang") and shutil.which("llvm-objdump")
    return exp.run_smoke(tmp_path_factory.mktemp("runs"), sizes=(1, 3, 8), seeds=(0, 17, 42),
                         measure_size=32, repeats=4, warmups=1)


@pytest.mark.integration
def test_real_smoke_gate_artifacts_and_paired_measurements(completed_run):
    path, record = completed_run
    assert record["status"] == "completed"
    assert record["environment_role"] == "development_smoke"
    assert record["publishable_benchmark"] is False
    assert record["llm_api_called"] is False
    assert exp.audit_artifacts(path) == []
    assert json.loads((path / "experiment.json").read_text()) == record
    assert record["sources"]["input_sha256"] == record["candidates"]["reference"]["source_sha256"]
    for name in exp.CANDIDATES:
        candidate = record["candidates"][name]
        directory = path / "candidates" / name
        assert candidate["origin"] == "handwritten_fixture"
        assert candidate["build"]["passed"]
        assert all((directory / f).stat().st_size for f in ("kernel.ll", "kernel.s", "kernel.disasm", "program"))
        assert "kernel" in (directory / "kernel.disasm").read_text()
        assert candidate["build"] == json.loads((directory / "build.json").read_text())
        assert candidate["verification"] == json.loads((directory / "verification.json").read_text())
    assert record["candidates"]["reference"]["verification"]["passed"]
    wrong = record["candidates"]["deliberately_wrong"]
    assert wrong["verification"]["category"] == "value_mismatch"
    assert all(case["category"] == "value_mismatch" for case in wrong["verification"]["cases"])
    assert wrong["measurement"] is None
    assert not (path / "candidates/deliberately_wrong/measurements.json").exists()
    for name in ("identity", "equivalent"):
        candidate = record["candidates"][name]
        assert candidate["verification"]["passed"]
        measurement = candidate["measurement"]
        assert measurement["passed"]
        assert len(measurement["samples"]) == 10  # 1 warmup pair + 4 measured pairs
        assert all(x["elapsed_ns"] > 0 for x in measurement["samples"])
        assert len([x for x in measurement["samples"] if x["phase"] == "measurement"]) == 8
        assert measurement["samples"][2]["order"] == ["reference", name]
        assert measurement["samples"][4]["order"] == [name, "reference"]
        assert measurement["summary"]["candidate"]["count"] == 4
        assert measurement["summary"]["candidate"]["mad_ns"] >= 0
    commands = [x["args"] for x in record["candidates"]["reference"]["build"]["commands"]]
    assert "-ffp-contract=off" in commands[0]
    assert "-fno-fast-math" in commands[0]
    assert record["compiler"]["version"]
    assert record["git"]["commit"]


@pytest.mark.integration
def test_artifact_tampering_is_detected(completed_run, tmp_path):
    source, _ = completed_run
    target = tmp_path / "copied"
    shutil.copytree(source, target)
    with (target / "candidates/equivalent/kernel.c").open("a") as stream:
        stream.write("\n/* tampered */\n")
    assert any("hash mismatch" in x for x in exp.audit_artifacts(target))


@pytest.mark.parametrize("kind", ["llvm_ir", "asm"])
def test_unsupported_input_kind_rejected_before_creating_run(tmp_path, kind):
    with pytest.raises(NotImplementedError, match=kind):
        exp.run_smoke(tmp_path / "unused", input_kind=kind)
    assert not (tmp_path / "unused").exists()


@pytest.mark.integration
def test_compilation_failure_has_own_category(tmp_path):
    (tmp_path / "kernel.c").write_text("this is deliberately invalid C\n")
    result = exp.build_candidate(tmp_path, discover_compiler(), shutil.which("llvm-objdump"), 10)
    assert not result["passed"]
    assert result["category"] == "compile_failure"
    assert result["commands"][0]["stderr"]
    assert not (tmp_path / "program").exists()


@pytest.mark.integration
@pytest.mark.parametrize("failure", ["compile_failure", "empty_output", "abnormal_exit", "timeout"])
def test_reference_failure_blocks_all_measurement(tmp_path, monkeypatch, failure):
    fixtures = tmp_path / "fixtures"
    shutil.copytree(exp.FIXTURES, fixtures)
    code = {
        "compile_failure": "not C syntax",
        "empty_output": '#include <stdlib.h>\n#include "kernel.h"\nvoid kernel(size_t n,const double*a,const double*b,double*c){exit(0);}',
        "abnormal_exit": '#include <stdlib.h>\n#include "kernel.h"\nvoid kernel(size_t n,const double*a,const double*b,double*c){abort();}',
        "timeout": '#include "kernel.h"\nvoid kernel(size_t n,const double*a,const double*b,double*c){for(;;){__asm__ volatile("" ::: "memory");}}',
    }[failure]
    (fixtures / "reference.c").write_text(code)
    monkeypatch.setattr(exp, "FIXTURES", fixtures)
    def forbidden(*args, **kwargs):
        pytest.fail("measurement called after reference failure")
    monkeypatch.setattr(exp, "measure_pairs", forbidden)
    real_process = exp.run_process
    def short_verify(args, **kwargs):
        if "verify" in args:
            kwargs["timeout"] = 0.15
        return real_process(args, **kwargs)
    monkeypatch.setattr(exp, "run_process", short_verify)
    _, record = exp.run_smoke(tmp_path / "runs", sizes=(1,), seeds=(1,), measure_size=1, measure_seed=1, repeats=2, warmups=0)
    assert record["status"] == "failed"
    reference = record["candidates"]["reference"]
    assert not reference["verification"]["passed"]
    assert all(x["measurement"] is None for x in record["candidates"].values())
    assert record["candidates"]["identity"]["verification"]["category"] == "reference_failure"


def test_measurement_failure_keeps_raw_evidence_without_aggregate(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "run_process", lambda *a, **kw: ProcessResult([], "timeout", -9, "", "", 0.1))
    result = exp.measure_pairs(tmp_path, "identity", size=1, seed=1, repeats=2, warmups=0, timeout=0.1)
    assert result["passed"] is False
    assert result["summary"] is None
    assert "elapsed_ns" not in result["samples"][0]


def test_affinity_rejects_unavailable_cpu_and_restores_original():
    available = os.sched_getaffinity(0)
    with pytest.raises(ValueError, match="outside"):
        with exp.cpu_affinity(max(available) + 100):
            pytest.fail("invalid affinity was allowed")
    assert os.sched_getaffinity(0) == available
    with exp.cpu_affinity() as record:
        assert record["pinned"]
        assert record["effective"] == [min(available)]
    assert record["restored"]
    assert os.sched_getaffinity(0) == available


def test_affinity_unavailable_is_recorded(monkeypatch):
    def denied(*args):
        raise OSError("affinity denied by test")
    monkeypatch.setattr(exp.os, "sched_setaffinity", denied)
    with exp.cpu_affinity() as record:
        assert not record["pinned"]
        assert "denied" in record["reason"]


def test_empty_manifest_cannot_claim_complete(tmp_path):
    exp.write_json(tmp_path / "experiment.json", {"artifacts": {}, "candidates": {}, "prompts": {}, "status": "running"})
    assert exp.audit_artifacts(tmp_path)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["omit_required_entry", "metadata", "delete_file", "missing_provenance", "missing_compiler_version"])
def test_incomplete_or_inconsistent_artifacts_rejected(completed_run, tmp_path, mutation):
    original, _ = completed_run
    copy = tmp_path / "run"
    shutil.copytree(original, copy)
    record = json.loads((copy / "experiment.json").read_text())
    if mutation == "omit_required_entry":
        del record["artifacts"]["candidates/equivalent/kernel.ll"]
    elif mutation == "metadata":
        record["candidates"]["identity"]["verification"]["cases"][0]["seed"] = 999
    elif mutation == "missing_provenance":
        for key in ("host", "compiler", "settings", "git", "toolchain"):
            del record[key]
    elif mutation == "missing_compiler_version":
        del record["compiler"]["version"]
    else:
        (copy / "candidates/identity/kernel.disasm").unlink()
    exp.write_json(copy / "experiment.json", record)
    assert exp.audit_artifacts(copy)


@pytest.mark.integration
def test_unexpected_error_records_failure(tmp_path, monkeypatch):
    def interrupted(*args, **kwargs):
        raise RuntimeError("simulated interrupted build")
    monkeypatch.setattr(exp, "build_candidate", interrupted)
    with pytest.raises(RuntimeError, match="simulated"):
        exp.run_smoke(tmp_path)
    records = list(tmp_path.glob("*/experiment.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record["status"] == "failed"
    assert record["failure"]["category"] == "RuntimeError"
    assert "simulated" in record["failure"]["reason"]


@pytest.mark.integration
def test_unique_runs_and_prompt_switch_preserve_build_conditions(tmp_path, monkeypatch):
    first_path, first = exp.run_smoke(tmp_path, specification="CPU ALPHA with cache A", sizes=(1,), seeds=(1,),
                                     measure_size=2, repeats=2, warmups=0)
    original_bytes = (first_path / "experiment.json").read_bytes()
    monkeypatch.chdir(tmp_path)
    second_path, second = exp.run_smoke(tmp_path, specification="CPU BETA with cache B", sizes=(1,), seeds=(1,),
                                       measure_size=2, repeats=2, warmups=0)
    assert first_path != second_path
    assert (first_path / "experiment.json").read_bytes() == original_bytes
    assert first["compiler"] == second["compiler"]
    assert first["git"] == second["git"]
    assert second["git"]["commit"] is not None
    assert first["sources"] == second["sources"]
    assert first["prompts"]["none"] == second["prompts"]["none"]
    assert first["prompts"]["spec"]["sha256"] != second["prompts"]["spec"]["sha256"]
    assert first["settings"]["execution_contract"] == second["settings"]["execution_contract"]
    for name in exp.CANDIDATES:
        first_commands = [c["args"] for c in first["candidates"][name]["build"]["commands"]]
        second_commands = [c["args"] for c in second["candidates"][name]["build"]["commands"]]
        assert first_commands == second_commands
