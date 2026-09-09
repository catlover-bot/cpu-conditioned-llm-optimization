import sys

import pytest

from cpucond.process import ProcessResult, run_process
from cpucond.verification import OutputError, parse_measurement, parse_output, validate_result


def output(bits):
    return f"CPUCOND_F64 {len(bits)}\n" + "".join(f"{x:016x}\n" for x in bits)


@pytest.mark.parametrize("text,count,reason", [
    ("", 1, "empty_output"),
    ("\n", 1, "invalid_header"),
    ("0.0\n", 1, "invalid_header"),
    ("CPUCOND_F64 " + "9" * 5000 + "\n0000000000000000\n", 1, "invalid_header"),
    ("CPUCOND_F64 2\n0000000000000000\n", 2, "element_count_mismatch"),
    (output([0]), 2, "element_count_mismatch"),
    (output([0, 0]), 1, "element_count_mismatch"),
    (output([0x7FF0000000000000]), 1, "non_finite_output"),
    (output([0xFFF0000000000000]), 1, "non_finite_output"),
    (output([0x7FF8000000000000]), 1, "non_finite_output"),
    ("CPUCOND_F64 1\n0.000000\n", 1, "invalid_float64_bits"),
])
def test_rejects_invalid_full_output(text, count, reason):
    with pytest.raises(OutputError, match=reason):
        parse_output(text, count)


def test_compares_every_bit_including_signed_zero_and_last_element():
    result = ProcessResult([], "ok", 0, output([0, 0x8000000000000000]), "", 0.0)
    verdict, _ = validate_result(result, 2, [0, 0])
    assert verdict["category"] == "value_mismatch"
    assert verdict["first_index"] == 1
    assert verdict["mismatch_count"] == 1


@pytest.mark.parametrize("text", ["", "{}", "[]", '{"elapsed_ns":0,"checksum_bits":"0000000000000000"}',
                                  '{"elapsed_ns":true,"checksum_bits":"0000000000000000"}',
                                  '{"elapsed_ns":NaN,"checksum_bits":"0000000000000000"}',
                                  '{"elapsed_ns":-1,"checksum_bits":"0000000000000000"}'])
def test_invalid_measurement_has_no_fabricated_time(text):
    with pytest.raises(OutputError):
        parse_measurement(text)


@pytest.mark.parametrize("program,category", [
    ("import sys; sys.exit(9)", "abnormal_exit"),
    ("import os, signal; os.kill(os.getpid(), signal.SIGTERM)", "abnormal_exit"),
    ("import time; time.sleep(10)", "timeout"),
])
def test_real_process_failure_classification(program, category):
    result = run_process([sys.executable, "-c", program], timeout=0.15)
    assert result.category == category
    assert validate_result(result, 1)[0]["category"] == category


def test_process_environment_allowlist(monkeypatch):
    monkeypatch.setenv("CPUCOND_TEST_SECRET", "must-never-be-copied")
    result = run_process([sys.executable, "-c", "import os; print('CPUCOND_TEST_SECRET' in os.environ)"])
    assert result.category == "ok"
    assert result.stdout.strip() == "False"


def test_launch_failure():
    assert run_process(["/definitely/missing/cpucond-program"]).category == "launch_failure"
