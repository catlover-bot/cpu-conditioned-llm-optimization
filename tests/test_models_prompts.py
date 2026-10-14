"""The prompt treatment must not change observations, code, or build settings."""

from dataclasses import FrozenInstanceError, asdict, replace
import hashlib
import inspect
import json

import pytest

from cpucond import host
from cpucond.models import (
    CompilerTarget, ExecutionContract, ExperimentRecord, HostObservation,
    PromptCPUContext, SCHEMA_VERSION,
)
from cpucond.prompts import CPU_SECTION_HEADER, prompt_hash, render_prompt


SOURCE = "#include <stddef.h>\nvoid kernel(size_t n, const double*a, const double*b, double*c) {}\n"
CPU_SENTINEL = "CPU_SENTINEL_MODEL_123, L3 cache: CACHE_SENTINEL_456 MiB"


def test_models_are_separate_and_prompt_switch_leaves_other_settings_unchanged():
    observation = HostObservation(cpu_model=CPU_SENTINEL, caches={"L3 cache": "456 MiB"})
    target = CompilerTarget(
        compiler="/LOCAL_PATH_SENTINEL/clang", version="COMPILER_VERSION_SENTINEL",
        target_flags=("-march=TARGET_CPU_SENTINEL",),
    )
    snapshot = asdict(observation), asdict(target)
    contract = ExecutionContract()
    baseline = render_prompt(SOURCE, PromptCPUContext(), contract)
    treatment = render_prompt(SOURCE, PromptCPUContext("spec", CPU_SENTINEL), contract)
    assert treatment == baseline + CPU_SECTION_HEADER + CPU_SENTINEL + "\n"
    assert CPU_SENTINEL not in baseline
    assert "CACHE_SENTINEL_456" not in baseline
    assert "LOCAL_PATH_SENTINEL" not in baseline + treatment
    assert "COMPILER_VERSION_SENTINEL" not in baseline + treatment
    assert "TARGET_CPU_SENTINEL" not in baseline + treatment
    assert (asdict(observation), asdict(target)) == snapshot
    assert SOURCE in baseline and SOURCE in treatment
    assert all(getattr(contract, field) in baseline for field in ("abi", "correctness", "output_format"))
    assert target.compile_flags == ("-march=TARGET_CPU_SENTINEL", "-O3", "-fno-fast-math", "-ffp-contract=off")


def test_prompt_allowlist_does_not_inspect_runtime_state(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("prompt renderer inspected runtime state")
    monkeypatch.setattr(host, "observe_host", forbidden)
    monkeypatch.setattr(host, "discover_compiler", forbidden)
    monkeypatch.setenv("HOSTNAME", "HOSTNAME_SENTINEL")
    monkeypatch.setenv("CPU_MODEL", CPU_SENTINEL)
    assert list(inspect.signature(render_prompt).parameters) == ["source", "context", "contract"]
    rendered = render_prompt(SOURCE, PromptCPUContext())
    assert "HOSTNAME_SENTINEL" not in rendered
    assert CPU_SENTINEL not in rendered
    with pytest.raises(TypeError):
        render_prompt(SOURCE, HostObservation(cpu_model=CPU_SENTINEL))


def test_source_is_verbatim_even_when_source_explicitly_contains_cpu_text():
    source = "/* explicit source information: " + CPU_SENTINEL + " */\r\n" + SOURCE
    prompt = render_prompt(source, PromptCPUContext())
    assert "<source>\n" + source + "\n</source>" in prompt
    # 'none' is an extra-description treatment, not a claim of complete blindness.
    assert CPU_SENTINEL in prompt


@pytest.mark.parametrize("context", [PromptCPUContext(), PromptCPUContext("spec", CPU_SENTINEL)])
def test_render_and_sha256_are_deterministic(context):
    first = render_prompt(SOURCE, context)
    second = render_prompt(SOURCE, context)
    assert first == second
    assert prompt_hash(first) == prompt_hash(second)
    assert prompt_hash(first) == hashlib.sha256(first.encode("utf-8")).hexdigest()
    assert len(prompt_hash(first)) == 64


@pytest.mark.parametrize("mode,specification", [
    ("auto", None), ("none", CPU_SENTINEL), ("none", ""),
    ("spec", None), ("spec", " "), ("spec", 123),
])
def test_cpu_context_rejects_ambiguous_or_unsupported_values(mode, specification):
    with pytest.raises(ValueError):
        PromptCPUContext(mode, specification)


def test_top_level_dataclasses_are_frozen():
    for item, field, value in [
        (HostObservation(), "cpu_model", "other"),
        (PromptCPUContext(), "mode", "spec"),
        (CompilerTarget("clang", "observed"), "target_flags", ("-march=native",)),
        (ExecutionContract(), "abi", "other"),
        (ExperimentRecord(), "run_id", "other"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(item, field, value)


@pytest.mark.parametrize("field", ["target_flags", "optimization_flags", "floating_point_flags", "link_flags"])
@pytest.mark.parametrize("flag", [
    "-ffast-math", "-Ofast", "-fassociative-math", "-ffp-contract=fast",
    "-ffp-model=fast", "-funsafe-math-optimizations", "-ffinite-math-only",
    "-fno-signed-zeros", "-freciprocal-math", "-Xclang", "-mllvm",
    "-Xclang=-ffast-math", "-mllvm=-enable-unsafe-fp-math",
    "@unreviewed-options", "-fdenormal-fp-math=positive-zero",
])
def test_unsafe_flags_cannot_weaken_strict_contract_in_any_group(field, flag):
    target = CompilerTarget("clang", "observed")
    with pytest.raises(ValueError, match="strict smoke"):
        replace(target, **{field: getattr(target, field) + (flag,)})


def test_strict_floating_point_controls_are_required_and_flags_are_immutable_tuples():
    with pytest.raises(ValueError, match="strict smoke"):
        CompilerTarget("clang", "observed", floating_point_flags=())
    with pytest.raises(ValueError, match="tuples"):
        CompilerTarget("clang", "observed", target_flags=["-march=native"])


def test_record_encodes_input_kind_without_silently_coercing():
    assert ExperimentRecord().schema_version == SCHEMA_VERSION
    assert ExperimentRecord(input_kind="llvm_ir").input_kind == "llvm_ir"
    assert ExperimentRecord(input_kind="asm").input_kind == "asm"
    with pytest.raises(ValueError, match="input_kind"):
        ExperimentRecord(input_kind="bitcode")


def test_missing_host_fields_are_null_with_reasons_and_no_cpu_inference(monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda name: None)
    monkeypatch.setattr(host.platform, "release", lambda: "test-microsoft-WSL2")
    monkeypatch.setattr(host.platform, "version", lambda: "mock")
    observed = host.observe_host()
    assert observed.wsl is True
    assert "WSL guest-visible" in observed.scope
    for field in ("cpu_model", "isa_flags", "caches", "topology"):
        assert getattr(observed, field) is None
        assert observed.missing[field]
    assert all(value is None for value in observed.virtualization.values())


def test_lscpu_observation_has_scope_and_allowlisted_fields_only(monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda name: "/usr/bin/lscpu")
    data = {"lscpu": [
        {"field": "Model name:", "data": CPU_SENTINEL},
        {"field": "Flags:", "data": "feature_b feature_a"},
        {"field": "L3 cache:", "data": "123 MiB (2 instances)"},
        {"field": "Core(s) per socket:", "data": "8"},
        {"field": "Hypervisor vendor:", "data": "test-hypervisor"},
        {"field": "Hostname:", "data": "HOSTNAME_SENTINEL"},
        {"field": "Secret:", "data": "SECRET_SENTINEL"},
    ]}
    def fake_run(argv, **kwargs):
        assert argv == ["/usr/bin/lscpu", "--json"]
        assert kwargs["env"]["LC_ALL"] == "C"
        return host.subprocess.CompletedProcess(argv, 0, json.dumps(data), "")
    monkeypatch.setattr(host.subprocess, "run", fake_run)
    observed = host.observe_host()
    assert observed.cpu_model == CPU_SENTINEL
    assert observed.isa_flags == ("feature_a", "feature_b")
    assert observed.caches == {"L3 cache": "123 MiB (2 instances)"}
    assert "guest-visible" in observed.methods["caches"]
    assert "physical host cores" in observed.methods["topology"]
    assert observed.virtualization["hypervisor_vendor"] == "test-hypervisor"
    serialized = json.dumps(asdict(observed))
    assert "HOSTNAME_SENTINEL" not in serialized
    assert "SECRET_SENTINEL" not in serialized


def test_compiler_discovery_queries_resolved_executable(monkeypatch, tmp_path):
    executable = tmp_path / "clang-real"
    executable.write_text("fixture")
    alias = tmp_path / "clang"
    alias.symlink_to(executable)
    monkeypatch.setattr(host.shutil, "which", lambda name: str(alias))
    calls = []
    def capture(argv):
        calls.append(argv)
        return ("clang OBSERVED VERSION" if argv[-1] == "--version" else "observed-target-triple", None)
    monkeypatch.setattr(host, "_capture", capture)
    target = host.discover_compiler()
    assert target.compiler == str(executable.resolve())
    assert target.version == "clang OBSERVED VERSION"
    assert target.target_triple == "observed-target-triple"
    assert calls == [[str(executable.resolve()), "--version"], [str(executable.resolve()), "-dumpmachine"]]


def test_compiler_discovery_failure_is_explicit(monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda name: None)
    with pytest.raises(FileNotFoundError, match="not found"):
        host.discover_compiler()


def test_compiler_discovery_rejects_gcc_before_attempting_llvm_ir(monkeypatch):
    monkeypatch.setattr(host.shutil, "which", lambda name: "/usr/bin/gcc")
    monkeypatch.setattr(host, "_capture", lambda args: ("gcc observed version", None))
    with pytest.raises(ValueError, match="requires Clang"):
        host.discover_compiler("gcc")
