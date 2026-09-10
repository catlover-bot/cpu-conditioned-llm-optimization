"""Clock ordering is independent of UTC adjustments and kernel timing values."""

from copy import deepcopy
from datetime import datetime, timezone

import pytest

from cpucond import clock_provenance as clocks
from cpucond.selection_scoring import score_selection
from test_diagnostic_audit import synthetic_measurements
from test_selection_scoring import inputs


BOOT_A = "00000000-0000-0000-0000-000000000001"
BOOT_B = "00000000-0000-0000-0000-000000000002"


def event(prefix, utc, monotonic_ns=None, boot_id=BOOT_A):
    value = {prefix + "_utc": utc}
    if monotonic_ns is not None:
        value[prefix + "_clock"] = {"boot_id": boot_id, "monotonic_ns": monotonic_ns}
    return value


def ordered_events():
    return (event("frozen", "2026-09-10T00:00:10+00:00", 100),
            event("started", "2026-09-10T00:00:11+00:00", 200))


def test_event_capture_records_actual_boot_and_monotonic_with_observed_utc(monkeypatch):
    class BootFile:
        def read_text(self, encoding):
            assert encoding == "ascii"
            return BOOT_A + "\n"
    def boot_path(path):
        assert str(path) == "/proc/sys/kernel/random/boot_id"
        return BootFile()
    class Clock:
        @staticmethod
        def now(tz):
            assert tz is timezone.utc
            return datetime(2026, 9, 10, 1, 2, 3, tzinfo=timezone.utc)
    monkeypatch.setattr(clocks, "Path", boot_path)
    monkeypatch.setattr(clocks.time, "monotonic_ns", lambda: 987654321)
    monkeypatch.setattr(clocks, "datetime", Clock)
    assert clocks.event_fields("frozen") == {
        "frozen_utc": "2026-09-10T01:02:03+00:00",
        "frozen_clock": {"boot_id": BOOT_A, "monotonic_ns": 987654321},
    }


def test_same_boot_monotonic_order_retains_utc_regression_as_warning():
    first, second = ordered_events()
    second["started_utc"] = "2026-09-10T00:00:08.700000+00:00"
    original = deepcopy((first, second))
    warnings = clocks.check_order(first, "frozen", second, "started", "freeze to score")
    assert (first, second) == original
    assert len(warnings) == 1
    assert warnings[0]["code"] == "wall_clock_regression"
    assert warnings[0]["order_basis"] == "linux_boot_id_and_monotonic_ns"
    assert warnings[0]["wall_delta_seconds"] == pytest.approx(-1.3)
    assert warnings[0]["earlier_utc"] == first["frozen_utc"]
    assert warnings[0]["later_utc"] == second["started_utc"]


def test_correct_utc_never_overrides_reversed_monotonic_order():
    first, second = ordered_events()
    second["started_clock"]["monotonic_ns"] = 99
    with pytest.raises(ValueError, match="monotonic event order is reversed"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


def test_different_boots_cannot_compare_monotonic_values_even_with_ordered_utc():
    first, second = ordered_events()
    second["started_clock"]["boot_id"] = BOOT_B
    with pytest.raises(ValueError, match="different Linux boots"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


@pytest.mark.parametrize("bad_value", [-1, True, 1.5, "200", None])
def test_noninteger_or_negative_monotonic_evidence_is_rejected(bad_value):
    first, second = ordered_events()
    second["started_clock"]["monotonic_ns"] = bad_value
    with pytest.raises(ValueError, match="invalid Linux monotonic"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


@pytest.mark.parametrize("bad_value", ["", "unknown-boot", 123, None])
def test_missing_or_malformed_boot_identity_is_not_assumed_comparable(bad_value):
    first, second = ordered_events()
    second["started_clock"]["boot_id"] = bad_value
    with pytest.raises(ValueError, match="invalid Linux monotonic"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


@pytest.mark.parametrize("missing_side", ["first", "second"])
def test_one_missing_clock_cannot_enable_the_legacy_fallback(missing_side):
    first, second = ordered_events()
    if missing_side == "first":
        del first["frozen_clock"]
    else:
        del second["started_clock"]
    with pytest.raises(ValueError, match="incomplete monotonic"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


@pytest.mark.parametrize("utc", ["2026-09-10T00:00:11", "2026-09-10T09:00:11+09:00", "unknown", None])
def test_monotonic_evidence_does_not_relax_explicit_utc_validation(utc):
    first, second = ordered_events()
    second["started_utc"] = utc
    with pytest.raises(ValueError, match="explicit UTC"):
        clocks.check_order(first, "frozen", second, "started", "freeze to score")


def test_legacy_records_still_require_utc_order_and_are_never_repaired():
    first = event("frozen", "2026-09-10T00:00:10Z")
    second = event("started", "2026-09-10T00:00:11+00:00")
    assert clocks.check_order(first, "frozen", second, "started", "legacy") == []
    second["started_utc"] = "2026-09-10T00:00:09Z"
    original = deepcopy((first, second))
    with pytest.raises(ValueError, match="legacy UTC event order is reversed"):
        clocks.check_order(first, "frozen", second, "started", "legacy")
    assert (first, second) == original


def phases_with_clocks():
    return {
        "exploration": {**event("started", "2026-09-10T00:00:10Z", 100),
                        **event("completed", "2026-09-10T00:00:09Z", 200)},
        "confirmation": {**event("started", "2026-09-10T00:00:08Z", 300),
                         **event("completed", "2026-09-10T00:00:07Z", 400)},
    }


def test_phase_internal_and_cross_phase_regressions_are_all_preserved():
    phases = phases_with_clocks()
    original = deepcopy(phases)
    warnings = clocks.phase_clock_warnings(phases)
    assert phases == original
    assert len(warnings["exploration"]) == 1
    assert len(warnings["confirmation"]) == 2
    assert {w["code"] for group in warnings.values() for w in group} == {"wall_clock_regression"}


@pytest.mark.parametrize("mutation", ["internal_order", "overlapping_phases", "boot_change", "partial_clock"])
def test_phase_order_does_not_accept_monotonic_overlap_or_missing_provenance(mutation):
    phases = phases_with_clocks()
    if mutation == "internal_order":
        phases["exploration"]["completed_clock"]["monotonic_ns"] = 99
    elif mutation == "overlapping_phases":
        phases["confirmation"]["started_clock"]["monotonic_ns"] = 199
    elif mutation == "boot_change":
        for prefix in ("started", "completed"):
            phases["confirmation"][prefix + "_clock"]["boot_id"] = BOOT_B
    else:
        del phases["confirmation"]["started_clock"]
    with pytest.raises(ValueError):
        clocks.phase_clock_warnings(phases)


def test_diagnostic_audit_accepts_real_order_but_requires_saved_clock_warnings(synthetic_measurements):
    audit = synthetic_measurements
    for name, fields in phases_with_clocks().items():
        audit.record["phases"][name].update(fields)
    warnings = clocks.phase_clock_warnings(audit.record["phases"])
    for name, values in warnings.items():
        audit.record["phases"][name]["clock_warnings"] = values
    original = deepcopy(audit.record)
    audit.measurements()
    assert audit.errors == []
    assert audit.record == original


def test_diagnostic_audit_detects_omitted_regression_warning(synthetic_measurements):
    audit = synthetic_measurements
    for name, fields in phases_with_clocks().items():
        audit.record["phases"][name].update(fields)
        audit.record["phases"][name]["clock_warnings"] = []
    audit.measurements()
    assert audit.errors


def timed_selection_inputs():
    protocol, freeze, measurement = inputs()
    freeze.update(event("frozen", "2026-09-10T00:00:10Z", 100))
    for phase, start, end, time_start, time_end in (
        ("exploration", 110, 150, "00:00:11", "00:00:12"),
        ("confirmation", 200, 250, "00:00:13", "00:00:14"),
    ):
        measurement["phases"][phase].update(
            event("started", "2026-09-10T" + time_start + "Z", start))
        measurement["phases"][phase].update(
            event("completed", "2026-09-10T" + time_end + "Z", end))
        measurement["phases"][phase]["clock_warnings"] = []
    return protocol, freeze, measurement


def test_scoring_uses_confirmation_values_unchanged_when_utc_regresses():
    protocol, freeze, measurement = timed_selection_inputs()
    baseline = score_selection(protocol, freeze, measurement)
    measurement["phases"]["confirmation"]["started_utc"] = "2026-09-10T00:00:08.700000Z"
    warnings = clocks.phase_clock_warnings(measurement["phases"])
    for phase, values in warnings.items():
        measurement["phases"][phase]["clock_warnings"] = values
    original = deepcopy((protocol, freeze, measurement))
    report = score_selection(protocol, freeze, measurement)
    assert (protocol, freeze, measurement) == original
    assert report["counts"] == baseline["counts"]
    assert report["selection_frequencies"] == baseline["selection_frequencies"]
    assert any(w["code"] == "wall_clock_regression" for w in report["warnings"])
    for before, after in zip(baseline["requests"], report["requests"]):
        for metric in ("observed_time_ns", "reference_ratio", "loss_to_observed_best_fraction"):
            assert after[metric] == before[metric]
        assert after["judgment_status"] == "deferred"
        assert any(w["code"] == "wall_clock_regression" for w in after["warnings"])
    for before, after in zip(baseline["policies"], report["policies"]):
        assert after["mean_observed_time_ns"] == before["mean_observed_time_ns"]
        assert after["judgment_status"] == "deferred"


@pytest.mark.parametrize("mutation", ["before_freeze", "different_boot", "partial_clock"])
def test_confirmation_cannot_bypass_freeze_with_false_monotonic_evidence(mutation):
    protocol, freeze, measurement = timed_selection_inputs()
    confirmation = measurement["phases"]["confirmation"]
    if mutation == "before_freeze":
        confirmation["started_clock"]["monotonic_ns"] = 99
    elif mutation == "different_boot":
        confirmation["started_clock"]["boot_id"] = BOOT_B
    else:
        del confirmation["started_clock"]
    with pytest.raises(ValueError):
        score_selection(protocol, freeze, measurement)


def test_legacy_selection_utc_order_remains_strict_without_new_clock_evidence():
    protocol, freeze, measurement = inputs()
    assert score_selection(protocol, freeze, measurement)["counts"]["valid"] == 20
    measurement["phases"]["confirmation"]["started_utc"] = "2026-09-09T23:59:59Z"
    with pytest.raises(ValueError, match="before responses|legacy UTC"):
        score_selection(protocol, freeze, measurement)
