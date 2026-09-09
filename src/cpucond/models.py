"""Separate observations, prompt disclosures, build settings, and run records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SCHEMA_VERSION = "1.0"
FIXTURE_PROVENANCE = "handwritten_fixture"


@dataclass(frozen=True)
class HostObservation:
    """Runtime observations; no field is automatically disclosed in a prompt."""

    os_name: str | None = None
    os_release: str | None = None
    kernel: str | None = None
    architecture: str | None = None
    cpu_model: str | None = None
    available_cpus: tuple[int, ...] | None = None
    logical_cpus: int | None = None
    isa_flags: tuple[str, ...] | None = None
    wsl: bool | None = None
    virtualization: dict[str, str | None] = field(default_factory=dict)
    caches: dict[str, str] | None = None
    topology: dict[str, str] | None = None
    scope: str = "Information visible to this process; physical host properties are not inferred."
    methods: dict[str, str] = field(default_factory=dict)
    missing: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptCPUContext:
    """The explicit extra CPU description; independent of the executing host."""

    mode: Literal["none", "spec"] = "none"
    specification: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("none", "spec"):
            raise ValueError("CPU prompt mode must be 'none' or 'spec'")
        if self.mode == "none" and self.specification is not None:
            raise ValueError("mode='none' cannot contain a CPU specification")
        if self.mode == "spec" and (
            not isinstance(self.specification, str) or not self.specification.strip()
        ):
            raise ValueError("mode='spec' requires an explicit nonempty CPU specification")


@dataclass(frozen=True)
class CompilerTarget:
    """An observed compiler and independently selected strict smoke build flags."""

    compiler: str
    version: str
    target_flags: tuple[str, ...] = ()
    optimization_flags: tuple[str, ...] = ("-O3",)
    floating_point_flags: tuple[str, ...] = ("-fno-fast-math", "-ffp-contract=off")
    link_flags: tuple[str, ...] = ()
    target_triple: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.compiler, str) or not self.compiler:
            raise ValueError("compiler must identify the actual compiler executable")
        if not isinstance(self.version, str) or not self.version:
            raise ValueError("the observed compiler version is required")
        groups = (
            self.target_flags,
            self.optimization_flags,
            self.floating_point_flags,
            self.link_flags,
        )
        if any(
            not isinstance(group, tuple)
            or any(not isinstance(flag, str) or not flag or "\x00" in flag for flag in group)
            for group in groups
        ):
            raise ValueError("compiler flag groups must be tuples of nonempty strings")
        required = {"-fno-fast-math", "-ffp-contract=off"}
        if not required.issubset(self.floating_point_flags):
            raise ValueError("strict smoke requires -fno-fast-math and -ffp-contract=off")
        unsafe = {
            "-ffast-math", "-Ofast", "-fassociative-math",
            "-funsafe-math-optimizations", "-ffinite-math-only", "-fno-signed-zeros",
            "-freciprocal-math", "-fapprox-func", "-menable-unsafe-fp-math",
            "-fno-honor-infinities", "-fno-honor-nans", "-fno-trapping-math",
            "-fno-rounding-math", "-Xclang", "-mllvm",
        }
        for group in groups:
            for flag in group:
                if (
                    flag in unsafe
                    or flag.startswith("@")
                    or flag.startswith(("-Xclang=", "-mllvm="))
                    or flag.startswith("-Ofast=")
                    or (flag.startswith("-ffp-contract=") and flag != "-ffp-contract=off")
                    or (flag.startswith("-ffp-model=") and flag != "-ffp-model=strict")
                    or flag.startswith("-fdenormal-fp-math")
                ):
                    raise ValueError(f"flag incompatible with the strict smoke contract: {flag}")

    @property
    def compile_flags(self) -> tuple[str, ...]:
        return self.target_flags + self.optimization_flags + self.floating_point_flags


@dataclass(frozen=True)
class ExecutionContract:
    """Explicit common prompt inputs, including any required ABI or ISA contract."""

    abi: str = (
        "C11; export void kernel(size_t n, const double *a, const double *b, double *c). "
        "Arrays a, b, and c are disjoint row-major n-by-n arrays of IEEE-754 binary64 "
        "values. Include <stddef.h> for size_t. Preserve the function signature."
    )
    correctness: str = (
        "Overwrite every c element with the row-major matrix product a*b, accumulating "
        "in increasing k order as in the reference. The smoke domain is n=1..1024, "
        "32-bit unsigned seeds, and finite binary64 inputs from -1 through 1-2^-16 "
        "on a 2^-16 grid; c initially contains positive zero. "
        "Preserve the reference result for all initialized finite smoke inputs. "
        "Every output element must be finite and match the reference binary64 bits. "
        "Missing, empty, or incorrectly sized output fails. Preserve each output's "
        "floating-point operation order; do not reassociate operations or contract "
        "multiplication and addition into FMA. Tests check selected sizes and seeds "
        "and are not a proof of equivalence."
    )
    output_format: str = (
        "Return only a complete C source file defining kernel, with no main function, "
        "Markdown fences, external dependencies, or explanatory text."
    )

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in (
            self.abi, self.correctness, self.output_format
        )):
            raise ValueError("every execution contract field must be a nonempty string")


@dataclass(frozen=True)
class ExperimentRecord:
    """JSON-serializable run envelope; payloads hold build and execution evidence."""

    schema_version: str = SCHEMA_VERSION
    run_id: str = ""
    input_kind: Literal["c", "llvm_ir", "asm"] = "c"
    kernel: str = "gemm_smoke"
    environment_role: str = "development_smoke"
    publishable_benchmark: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    host: dict[str, Any] = field(default_factory=dict)
    compiler: dict[str, Any] = field(default_factory=dict)
    git: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    prompts: dict[str, Any] = field(default_factory=dict)
    candidates: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    status: str = "incomplete"

    def __post_init__(self) -> None:
        if self.input_kind not in ("c", "llvm_ir", "asm"):
            raise ValueError("input_kind must explicitly be c, llvm_ir, or asm")
