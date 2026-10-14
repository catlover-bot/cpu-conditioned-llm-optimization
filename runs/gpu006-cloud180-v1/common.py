"""Immutable GPU006 inputs and crash-durable state primitives (stdlib only)."""
from __future__ import annotations
import contextlib, datetime as dt, fcntl, hashlib, json, os, secrets, stat, sys, types
from collections import Counter
from pathlib import Path

PLAN_SHA = "9f5570a6b8d87b90df9eee97fba56fb33311e8d52cb93e1d9f17248b37c64a83"
BASE_SHA = "427675e790429706ba7854b00229be07a26c67183ea4698c80baa5cff6866e2c"
REPO = Path(__file__).resolve().parents[2]
RUN = REPO / "runs/gpu006-cloud180-v1"
INPUT = "runs/gpu006-target-info-v1"
TARGET = "examples/target-l4.sample.json"

class Blocked(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise Blocked(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()

def parse(data):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "Duplicate JSON key")
            out[key] = value
        return out
    def bad(_):
        raise Blocked("Nonfinite JSON")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad)

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def safe(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "Symlink rejected")
    return path

def read(path, cap=32 * 1024**2):
    path = safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= cap, "Not a bounded regular file")
        data = stream.read(cap + 1)
    require(len(data) <= cap, "Read limit exceeded")
    return data

def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def write_once(path, data):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists():
        require(read(path, max(len(data), 1)) == data, "Conflicting existing artifact retained")
        return
    tmp = path.with_name(path.name + ".partial-" + secrets.token_hex(8))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    # Hard-link publish prevents overwriting a concurrently-created artifact.
    try:
        os.link(tmp, path)
    except FileExistsError:
        require(read(path, max(len(data), 1)) == data, "Conflicting artifact retained")
    finally:
        tmp.unlink()
    fsync_dir(path.parent)

def atomic_json(path, obj):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + ".partial-" + secrets.token_hex(8))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(obj))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    fsync_dir(path.parent)

@contextlib.contextmanager
def exclusive(run_dir):
    path = safe(run_dir)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path / "controller.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Blocked("Another cloud controller holds the lock")
        yield
    finally:
        os.close(fd)

def load_base(repo_root=REPO):
    raise Blocked("Private deployment validation is archived locally; use the public offline reanalysis command")

def validate_inputs(repo_root=REPO):
    raise Blocked("Private deployment validation is archived locally; use the public offline reanalysis command")
