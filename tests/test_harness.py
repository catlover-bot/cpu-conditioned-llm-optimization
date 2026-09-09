"""Real C builds check the fixture ABI, exact outputs and timing protocol."""

import json
from pathlib import Path
import re
import shutil
import struct
import subprocess

import pytest


FIXTURES = Path(__file__).resolve().parents[1] / "src" / "cpucond" / "fixtures"
CANDIDATES = ("reference", "identity", "equivalent", "deliberately_wrong")
COMPILERS = [name for name in ("clang", "gcc") if shutil.which(name)]


@pytest.fixture(scope="module", params=COMPILERS or [None])
def executables(request, tmp_path_factory):
    compiler = request.param
    if compiler is None:
        pytest.skip("the C fixture integration tests require Clang or GCC")
    directory = tmp_path_factory.mktemp(f"harness-{compiler}")
    flags = ["-std=c11", "-O3", "-fno-fast-math", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror"]
    harness = directory / "harness.o"
    subprocess.run(
        [compiler, *flags, "-c", str(FIXTURES / "harness.c"), "-o", str(harness)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    result = {}
    for candidate in CANDIDATES:
        source = FIXTURES / f"{candidate}.c"
        obj = directory / f"{candidate}.o"
        executable = directory / candidate
        subprocess.run(
            [compiler, *flags, "-c", str(source), "-o", str(obj)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        subprocess.run(
            [compiler, str(harness), str(obj), "-o", str(executable)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        result[candidate] = executable
    return result


def run_fixture(executable, *args):
    return subprocess.run(
        [str(executable), *map(str, args)], capture_output=True, text=True, timeout=10,
    )


def expected_output(n, seed):
    """Independent binary64 computation also checks the runtime PRNG contract."""
    state = seed
    a, b = [], []
    for _ in range(n * n):
        for matrix in (a, b):
            state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
            matrix.append((state >> 15) / 65536.0 - 1.0)
    output = []
    for i in range(n):
        for j in range(n):
            value = 0.0
            for k in range(n):
                value += a[i * n + k] * b[k * n + j]
            output.append(struct.pack(">d", value).hex())
    return f"CPUCOND_F64 {n * n}\n" + "\n".join(output) + "\n"


@pytest.mark.parametrize("n,seed", [(1, 0), (2, 1), (5, 42), (9, 0xFFFFFFFF)])
def test_fixtures_match_independent_binary64_reference(executables, n, seed):
    expected = expected_output(n, seed)
    for candidate in ("reference", "identity", "equivalent"):
        completed = run_fixture(executables[candidate], "verify", n, seed)
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == expected
        assert completed.stderr == ""
    wrong = run_fixture(executables["deliberately_wrong"], "verify", n, seed)
    assert wrong.returncode == 0, wrong.stderr
    assert wrong.stdout != expected
    assert wrong.stdout.splitlines()[0] == f"CPUCOND_F64 {n * n}"
    assert len(wrong.stdout.splitlines()) == n * n + 1


def test_identity_is_byte_identical_to_reference():
    assert (FIXTURES / "identity.c").read_bytes() == (FIXTURES / "reference.c").read_bytes()


def test_measurement_reports_only_kernel_nanoseconds_and_consumes_all_output(executables):
    verification = run_fixture(executables["reference"], "verify", 16, 101)
    assert verification.returncode == 0
    expected_checksum = 14695981039346656037
    for element in verification.stdout.splitlines()[1:]:
        expected_checksum ^= int(element, 16)
        expected_checksum = (expected_checksum * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    for candidate in ("reference", "identity", "equivalent"):
        for _ in range(2):
            measured = run_fixture(executables[candidate], "measure", 16, 101)
            assert measured.returncode == 0, measured.stderr
            assert len(measured.stdout.splitlines()) == 1
            data = json.loads(measured.stdout)
            assert set(data) == {"elapsed_ns", "checksum_bits"}
            assert type(data["elapsed_ns"]) is int
            assert data["elapsed_ns"] > 0
            assert re.fullmatch(r"[0-9a-f]{16}", data["checksum_bits"])
            assert data["checksum_bits"] == f"{expected_checksum:016x}"


@pytest.mark.parametrize("args", [
    (), ("unknown", "2", "0"), ("verify", "0", "0"), ("verify", "1025", "0"),
    ("verify", "-1", "0"), ("verify", "+1", "0"), ("verify", "1x", "0"),
    ("verify", " 1", "0"), ("verify", "1", "-1"),
    ("verify", "1", "4294967296"), ("verify", "1", "999999999999999999999999"),
])
def test_harness_rejects_invalid_arguments(executables, args):
    completed = run_fixture(executables["reference"], *args)
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage:" in completed.stderr
