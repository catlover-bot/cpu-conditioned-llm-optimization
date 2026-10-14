"""One per-user machine gate for local inference and CPU measurement.

The lock coordinates this runner's entry points; it does not claim to prevent
unrelated software, users, or an external Ollama client from generating load.
"""

from contextlib import contextmanager
import fcntl
from functools import wraps
import os
from pathlib import Path
import tempfile
import threading


_state = threading.local()


@contextmanager
def execution_gate(activity):
    if activity not in ("inference", "measurement"):
        raise ValueError("unsupported execution activity")
    active = getattr(_state, "active", None)
    if active is not None:
        if active["activity"] != activity:
            raise RuntimeError("local inference and kernel measurement cannot overlap")
        yield active
        return
    path = Path(tempfile.gettempdir()) / f"cpucond-execution-{os.getuid()}.lock"
    with path.open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another local inference or kernel measurement is active") from exc
        evidence = {"activity": activity, "lock_path": str(path), "pid": os.getpid(),
                    "scope": "Cooperating cpucond processes for this OS user; unrelated load remains possible."}
        _state.active = evidence
        try:
            yield evidence
        finally:
            del _state.active
            fcntl.flock(stream, fcntl.LOCK_UN)


def gated(activity):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with execution_gate(activity):
                return function(*args, **kwargs)
        return wrapped
    return decorate
