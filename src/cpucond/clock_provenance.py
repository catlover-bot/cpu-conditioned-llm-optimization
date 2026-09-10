"""Preserve UTC observations while proving same-boot order monotonically.

Wall clocks can move backwards in a WSL guest. Monotonic values are comparable
only within the same Linux boot; legacy records retain their strict UTC gate.
"""

from datetime import datetime, timezone
from pathlib import Path
import re
import time


_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


def event_fields(prefix):
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    if not _BOOT_ID.fullmatch(boot_id):
        raise ValueError("Linux boot identity is unavailable")
    monotonic_ns = time.monotonic_ns()
    return {prefix + "_utc": datetime.now(timezone.utc).isoformat(),
            prefix + "_clock": {"boot_id": boot_id, "monotonic_ns": monotonic_ns}}


def _utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("event time must be explicit UTC") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("event time must be explicit UTC")
    return parsed


def _clock(value):
    if (not isinstance(value, dict) or set(value) != {"boot_id", "monotonic_ns"}
            or not isinstance(value["boot_id"], str) or not _BOOT_ID.fullmatch(value["boot_id"])
            or type(value["monotonic_ns"]) is not int or value["monotonic_ns"] < 0):
        raise ValueError("invalid Linux monotonic clock provenance")
    return value


def check_order(first, first_prefix, second, second_prefix, label):
    """Require order and return UTC-regression warnings without changing times."""
    first_utc, second_utc = first[first_prefix + "_utc"], second[second_prefix + "_utc"]
    earlier, later = _utc(first_utc), _utc(second_utc)
    first_key, second_key = first_prefix + "_clock", second_prefix + "_clock"
    present = first_key in first, second_key in second
    if any(present) and not all(present):
        raise ValueError(f"{label}: incomplete monotonic clock provenance")
    if all(present):
        a, b = _clock(first[first_key]), _clock(second[second_key])
        if a["boot_id"] != b["boot_id"]:
            raise ValueError(f"{label}: monotonic events belong to different Linux boots")
        if a["monotonic_ns"] > b["monotonic_ns"]:
            raise ValueError(f"{label}: monotonic event order is reversed")
        if earlier > later:
            return [{"code": "wall_clock_regression", "scope": label,
                     "reason": "Observed UTC moved backwards; event order is established by the same Linux boot and monotonic clock.",
                     "earlier_utc": first_utc, "later_utc": second_utc,
                     "wall_delta_seconds": (later - earlier).total_seconds(),
                     "order_basis": "linux_boot_id_and_monotonic_ns"}]
        return []
    if earlier > later:
        raise ValueError(f"{label}: legacy UTC event order is reversed")
    return []


def phase_clock_warnings(phases):
    """Reconstruct clock warnings for saved exploration/confirmation phases."""
    previous = None
    result = {}
    for name in ("exploration", "confirmation"):
        row = phases[name]
        warnings = check_order(row, "started", row, "completed", f"{name} phase start to completion")
        if previous is not None:
            warnings += check_order(previous, "completed", row, "started", "exploration completion to confirmation start")
        result[name] = warnings
        previous = row
    return result
