"""Deterministic family generation and real-Clang, verify-only boundary checks."""

from dataclasses import FrozenInstanceError, asdict
import hashlib
from pathlib import Path
import shutil
import struct

import pytest

from cpucond.process import run_process
from cpucond.transformations import Candidate, FACTORS, FIXTURES, generate_unrolled, make_candidates
from cpucond.verification import parse_output


def test_candidate_set_is_predeclared_deterministic_and_preserves_controls():
    first = make_candidates()
    assert [asdict(item) for item in first] == [asdict(item) for item in make_candidates()]
    assert [item.candidate_id for item in first] == [
        "reference", "identity", "unroll_1", "unroll_2", "unroll_4", "unroll_8",
        "unroll_16", "deliberately_wrong",
    ]
    assert first[0].source == first[1].source == (FIXTURES / "reference.c").read_text()
    assert first[-1].source == (FIXTURES / "deliberately_wrong.c").read_text()
    generated = [item for item in first if item.origin == "deterministic_generator"]
    assert [item.unroll_factor for item in generated] == list(FACTORS)
    assert len({hashlib.sha256(item.source.encode()).hexdigest() for item in generated}) == 5
    assert generated[0].comparison_baseline == "reference"
    assert all(item.comparison_baseline == "unroll_1" for item in generated[1:])
    assert all(item.origin != "llm" for item in first)
    with pytest.raises(FrozenInstanceError):
        first[0].source = "changed"


@pytest.mark.parametrize("factor", FACTORS)
def test_generator_is_deterministic_across_calls_and_retains_shared_abi(factor):
    source = generate_unrolled(factor)
    assert source == generate_unrolled(factor)
    assert source.startswith('#include "kernel.h"\n')
    assert "CPUCOND_NOINLINE void kernel(size_t n, const double *a, const double *b, double *c)" in source
    assert not any(token in source for token in ("restrict", "pragma", "aligned", "fma("))


@pytest.mark.parametrize("factor", [0, -1, 3, 32, True, False, 1.0, "2", None])
def test_generator_rejects_unsupported_or_ambiguous_factor(factor):
    with pytest.raises(ValueError, match="unroll factor"):
        generate_unrolled(factor)


@pytest.fixture(scope="module")
def generated_executables(tmp_path_factory):
    compiler = shutil.which("clang")
    if compiler is None:
        pytest.skip("real-Clang integration requires an installed clang")
    directory = tmp_path_factory.mktemp("controlled-transformations")
    flags = ["-std=c11", "-O3", "-fno-fast-math", "-ffp-contract=off", "-fno-lto",
             "-Wall", "-Wextra", "-Werror", "-I", str(FIXTURES)]
    harness = directory / "harness.o"
    result = run_process([compiler, *flags, "-c", FIXTURES / "harness.c", "-o", harness])
    assert result.category == "ok", result.stderr
    binaries = {}
    for candidate in make_candidates():
        source = directory / f"{candidate.candidate_id}.c"
        source.write_text(candidate.source)
        obj = directory / f"{candidate.candidate_id}.o"
        binary = directory / candidate.candidate_id
        result = run_process([compiler, *flags, "-c", source, "-o", obj])
        assert result.category == "ok", result.stderr
        result = run_process([compiler, "-fno-lto", harness, obj, "-o", binary])
        assert result.category == "ok", result.stderr
        binaries[candidate.candidate_id] = binary
    return binaries


def _independent_expected(n, seed):
    a, b = [], []
    state = seed
    for _ in range(n * n):
        for destination in (a, b):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            destination.append((state >> 15) / 65536.0 - 1.0)
    expected = []
    for i in range(n):
        for j in range(n):
            total = 0.0
            for k in range(n):
                total += a[i * n + k] * b[k * n + j]
            expected.append(struct.unpack(">Q", struct.pack(">d", total))[0])
    return expected


@pytest.mark.integration
@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17])
@pytest.mark.parametrize("seed", [0, 42, 0xFFFFFFFF])
def test_every_factor_and_remainder_match_all_reference_bits(generated_executables, n, seed):
    expected = _independent_expected(n, seed)
    for name, executable in generated_executables.items():
        result = run_process([executable, "verify", n, seed])
        assert result.category == "ok", result.stderr
        actual = parse_output(result.stdout, n * n)
        if name == "deliberately_wrong":
            assert actual != expected
        else:
            assert actual == expected, (name, n, seed)


@pytest.mark.integration
def test_each_independent_output_retains_rounding_sensitive_k_order(generated_executables):
    """An extra finite-input sentinel catches splitting/reordering a reduction.

    Unlike the smoke PRNG's exact dyadic sums, this cancellation-sensitive input
    distinguishes (large + small) + negative_large from regrouped reductions.
    It checks a preservation property, not an expanded benchmark input domain.
    """
    directory = next(iter(generated_executables.values())).parent
    driver = directory / "rounding_order.c"
    driver.write_text('''#include "kernel.h"
#include <stdio.h>
int main(void) {
    const size_t n = 17;
    double a[17 * 17], b[17 * 17], c[17 * 17];
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            a[i * n + j] = j == 0 ? 1.0e16 : (j == 1 ? 1.0 : (j == 2 ? -1.0e16 : 0.0));
            b[i * n + j] = (double)(j % 3 + 1);
            c[i * n + j] = 23.0;
        }
    }
    kernel(n, a, b, c);
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            double multiplier = (double)(j % 3 + 1);
            double expected = 0.0;
            expected += 1.0e16 * multiplier;
            expected += 1.0 * multiplier;
            expected += -1.0e16 * multiplier;
            if (c[i * n + j] != expected) return 1;
        }
    }
    return 0;
}
''')
    compiler = shutil.which("clang")
    for name in ["reference", *(f"unroll_{factor}" for factor in FACTORS)]:
        binary = directory / f"{name}_rounding"
        result = run_process([
            compiler, "-std=c11", "-O3", "-fno-fast-math", "-ffp-contract=off",
            "-fno-lto", "-I", FIXTURES, driver, directory / f"{name}.o", "-o", binary,
        ])
        assert result.category == "ok", result.stderr
        result = run_process([binary])
        assert result.category == "ok", (name, result.stderr)
