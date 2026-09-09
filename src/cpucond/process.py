"""Recorded, shell-free local process execution with process-group timeouts."""

from dataclasses import asdict, dataclass
import os
import signal
import subprocess
import time


@dataclass(frozen=True)
class ProcessResult:
    args: list[str]
    category: str
    returncode: int | None
    stdout: str
    stderr: str
    wall_seconds: float  # Process overhead, NEVER a kernel measurement.

    def to_dict(self):
        return asdict(self)


def run_process(args, *, timeout=30.0, cwd=None):
    args = [str(arg) for arg in args]
    start = time.monotonic()
    # Deliberate, reproducible allowlist: no credentials, CFLAGS, CPATH, or
    # LD_PRELOAD inherited into the experiment. No environment enumeration.
    env = {"PATH": os.defpath, "LANG": "C", "LC_ALL": "C"}
    try:
        process = subprocess.Popen(
            args, cwd=cwd, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )
    except OSError as exc:
        return ProcessResult(args, "launch_failure", None, "", str(exc), time.monotonic() - start)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        category = "ok" if process.returncode == 0 else "abnormal_exit"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        category = "timeout"
    return ProcessResult(
        args, category, process.returncode, stdout.decode("utf-8", "replace"),
        stderr.decode("utf-8", "replace"), time.monotonic() - start,
    )
