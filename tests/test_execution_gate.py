"""Check process/thread exclusion without running inference or C benchmarks."""

from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import pytest

from cpucond.execution_gate import execution_gate


def test_same_thread_reentry_is_allowed_only_for_the_same_activity():
    with execution_gate("inference") as outer:
        with execution_gate("inference") as inner:
            assert inner == outer
        with pytest.raises(RuntimeError, match="cannot overlap"):
            with execution_gate("measurement"):
                pytest.fail("measurement overlapped inference")
    with execution_gate("measurement"):
        pass


@pytest.mark.parametrize("other", ["measurement", "inference"])
def test_other_thread_cannot_overlap_even_if_it_has_the_same_activity(other):
    def attempt():
        with execution_gate(other):
            return "acquired"

    with ThreadPoolExecutor(max_workers=1) as executor:
        with execution_gate("inference"):
            with pytest.raises(RuntimeError, match="active"):
                executor.submit(attempt).result(timeout=5)
        assert executor.submit(attempt).result(timeout=5) == "acquired"


def test_other_process_cannot_measure_during_inference():
    script = "from cpucond.execution_gate import execution_gate\nwith execution_gate('measurement'): pass"
    with execution_gate("inference"):
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=5)
    assert result.returncode != 0
    assert "another local inference or kernel measurement is active" in result.stderr


def test_gate_is_released_after_failure():
    with pytest.raises(ValueError, match="failure"):
        with execution_gate("inference"):
            raise ValueError("deliberate failure")
    with execution_gate("measurement"):
        pass


def test_diagnostic_and_smoke_entry_points_refuse_to_measure_under_inference(tmp_path):
    from cpucond.diagnostics import run_diagnostics
    from cpucond.experiment import run_smoke

    with execution_gate("inference"):
        for runner in (run_diagnostics, run_smoke):
            with pytest.raises(RuntimeError, match="cannot overlap"):
                runner(tmp_path / runner.__name__)
    assert not list(tmp_path.iterdir())
