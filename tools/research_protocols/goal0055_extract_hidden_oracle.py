#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

ANALYSIS_ID = "cpu-conditioned-final-analysis-v1"
HOST_ID = "haswell-e3-1241v3"

SIZE_ORDER = {
    "MINI": 0,
    "SMALL": 1,
    "MEDIUM": 2,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )


def geometric_mean(values: list[float]) -> float:
    if not values or any(x <= 0 for x in values):
        raise ValueError("geometric mean requires positive values")

    return math.exp(
        sum(math.log(x) for x in values)
        / len(values)
    )


def parse_candidate(candidate_id: str):
    if candidate_id == "identity":
        return {
            "loop_index": None,
            "hint_kind": "identity",
            "hint_value": None,
        }

    m = re.fullmatch(
        r"loop_([0-9]{2})_"
        r"(unroll_count|interleave_count|vectorize_width)_"
        r"([0-9]+)",
        candidate_id,
    )

    if not m:
        raise ValueError(
            f"unexpected candidate id: {candidate_id}"
        )

    return {
        "loop_index": int(m.group(1)),
        "hint_kind": m.group(2),
        "hint_value": int(m.group(3)),
    }


def representative_status(
    rep: str,
    summaries: dict,
    invalid_reps: set[str],
):
    if rep == "identity":
        return True, 1.0, ""

    if rep in invalid_reps:
        return (
            False,
            None,
            "candidate_invalid_no_selective_rerun",
        )

    sessions = summaries.get(rep)

    if not isinstance(sessions, list):
        return False, None, "missing_measurement_summary"

    if len(sessions) != 2:
        return (
            False,
            None,
            f"unexpected_session_count_{len(sessions)}",
        )

    medians = []

    for i, session in enumerate(sessions):
        if not session.get("measurement_valid", False):
            return (
                False,
                None,
                f"session_{i}_measurement_invalid",
            )

        warnings = session.get(
            "quality_warnings",
            [],
        )

        if warnings:
            return (
                False,
                None,
                "quality_warning:"
                + ",".join(sorted(warnings)),
            )

        x = session.get(
            "median_paired_speedup"
        )

        if (
            not isinstance(x, (int, float))
            or not math.isfinite(x)
            or x <= 0
        ):
            return (
                False,
                None,
                f"session_{i}_invalid_speedup",
            )

        medians.append(float(x))

    return (
        True,
        geometric_mean(medians),
        "",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(
            f"refusing empty CSV: {path}"
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--bundle",
        type=Path,
        default=Path(
            "external-results/"
            "haswell-e3-1241v3/"
            "final-atlas/"
            "analysis-bundle"
        ),
    )

    ap.add_argument(
        "--contract",
        type=Path,
        default=Path(
            "configs/"
            "final-analysis-contract-v1.json"
        ),
    )

    ap.add_argument(
        "--out",
        type=Path,
        default=Path(
            "external-results/"
            "haswell-e3-1241v3/"
            "hidden-oracle-v1"
        ),
    )

    args = ap.parse_args()

    bundle = args.bundle.resolve()
    contract_path = args.contract.resolve()
    out = args.out.resolve()

    contract = load(contract_path)

    assert (
        contract["analysis_id"]
        == ANALYSIS_ID
    )

    assert (
        contract["status"]
        == "FROZEN_BEFORE_INSPECTING_FINAL_CANDIDATE_SPEEDUPS"
    )

    assert (
        contract["source_protocol"]
        == "cpu-conditioned-final-v1.3"
    )

    assert (
        contract["performance_estimator"][
            "sessions"
        ]
        == 2
    )

    assert (
        contract["performance_estimator"][
            "pairs_per_session"
        ]
        == 8
    )

    instance_paths = sorted(
        bundle.rglob(
            "instance-summary.json"
        ),
        key=lambda p: (
            p.parent.parent.name,
            SIZE_ORDER[
                load(p)["size_label"]
            ],
        ),
    )

    assert len(instance_paths) == 90, (
        len(instance_paths)
    )

    candidate_rows = []
    oracle_rows = []

    for instance_path in instance_paths:
        instance_dir = instance_path.parent

        inst = load(instance_path)
        gate = load(
            instance_dir / "gate.json"
        )
        aliases = load(
            instance_dir / "alias-map.json"
        )

        kernel = inst["kernel_id"]
        size = inst["size_label"]

        assert inst["instance_valid"] is True

        gate_rows = (
            gate.get("candidate_rows")
            or gate.get("rows")
        )

        if not isinstance(gate_rows, list):
            raise RuntimeError(
                f"{kernel}/{size}: "
                "gate rows missing"
            )

        summaries = (
            inst.get(
                "final_measurement_summaries"
            )
            or inst.get(
                "measurement_summaries"
            )
        )

        if not isinstance(summaries, dict):
            raise RuntimeError(
                f"{kernel}/{size}: "
                "final measurement summaries missing"
            )

        invalid_reps = set(
            inst.get(
                "candidate_representatives_invalid_no_rerun",
                [],
            )
        )

        rep_cache = {}

        def status(rep: str):
            if rep not in rep_cache:
                rep_cache[rep] = (
                    representative_status(
                        rep,
                        summaries,
                        invalid_reps,
                    )
                )
            return rep_cache[rep]

        rows_this_instance = []

        for g in gate_rows:
            cid = g["candidate_id"]
            parsed = parse_candidate(cid)

            admitted = bool(
                g.get("admitted", False)
            )

            rep = (
                aliases.get(cid)
                if admitted
                else None
            )

            function_hash = None

            if admitted:
                function_hash = (
                    g.get("function", {})
                    .get("bytes_sha256")
                )

                if rep is None:
                    raise RuntimeError(
                        f"{kernel}/{size}/{cid}: "
                        "admitted candidate "
                        "missing alias"
                    )

                measurement_valid, speedup, reason = (
                    status(rep)
                )
            else:
                measurement_valid = False
                speedup = None
                reason = "correctness_rejected"

            oracle_eligible = (
                admitted
                and measurement_valid
                and speedup is not None
            )

            machine_code_noop = (
                admitted
                and cid != "identity"
                and rep == "identity"
            )

            row = {
                "host_id": HOST_ID,
                "kernel": kernel,
                "size": size,
                "candidate_id": cid,
                "loop_index":
                    parsed["loop_index"],
                "hint_kind":
                    parsed["hint_kind"],
                "hint_value":
                    parsed["hint_value"],
                "correctness_admitted":
                    admitted,
                "machine_code_representative":
                    rep,
                "machine_code_sha256":
                    function_hash,
                "machine_code_noop":
                    machine_code_noop,
                "measurement_valid":
                    measurement_valid,
                "measurement_invalid_reason":
                    reason,
                "oracle_eligible":
                    oracle_eligible,
                "speedup":
                    speedup,
            }

            rows_this_instance.append(
                row
            )

        assert (
            len(rows_this_instance)
            == inst[
                "candidate_ids_requested"
            ]
        )

        eligible = [
            r
            for r in rows_this_instance
            if r["oracle_eligible"]
        ]

        if not eligible:
            raise RuntimeError(
                f"{kernel}/{size}: "
                "no oracle-eligible candidate"
            )

        oracle_speedup = max(
            r["speedup"]
            for r in eligible
        )

        oracle_set = sorted(
            r["candidate_id"]
            for r in eligible
            if r["speedup"]
            == oracle_speedup
        )

        canonical = oracle_set[0]

        near_threshold = (
            oracle_speedup / 1.01
        )

        near_set = sorted(
            r["candidate_id"]
            for r in eligible
            if r["speedup"]
            >= near_threshold
        )

        for row in rows_this_instance:
            valid = row[
                "oracle_eligible"
            ]

            speedup = row["speedup"]

            row["is_oracle"] = (
                valid
                and speedup == oracle_speedup
            )

            row["near_oracle"] = (
                valid
                and speedup >= near_threshold
            )

            row["faster_than_reference"] = (
                valid
                and speedup > 1.0
            )

            if valid:
                row["oracle_regret"] = (
                    1.0
                    - speedup
                    / oracle_speedup
                )
            else:
                row["oracle_regret"] = 1.0

        candidate_rows.extend(
            rows_this_instance
        )

        oracle_rows.append({
            "host_id": HOST_ID,
            "kernel": kernel,
            "size": size,

            "oracle_speedup":
                oracle_speedup,

            "canonical_oracle_candidate":
                canonical,

            "oracle_candidate_count":
                len(oracle_set),

            "oracle_candidates_json":
                json.dumps(
                    oracle_set,
                    separators=(",", ":"),
                ),

            "near_oracle_threshold":
                near_threshold,

            "near_oracle_candidate_count":
                len(near_set),

            "near_oracle_candidates_json":
                json.dumps(
                    near_set,
                    separators=(",", ":"),
                ),

            "candidate_count":
                len(rows_this_instance),

            "correctness_admitted":
                sum(
                    r["correctness_admitted"]
                    for r in rows_this_instance
                ),

            "correctness_rejected":
                sum(
                    not r["correctness_admitted"]
                    for r in rows_this_instance
                ),

            "measurement_valid":
                sum(
                    r["measurement_valid"]
                    for r in rows_this_instance
                ),

            "measurement_invalid":
                sum(
                    r["correctness_admitted"]
                    and not r["measurement_valid"]
                    for r in rows_this_instance
                ),

            "machine_code_noop_nonidentity":
                sum(
                    r["machine_code_noop"]
                    for r in rows_this_instance
                ),

            "oracle_includes_identity":
                "identity" in oracle_set,

            "near_oracle_includes_identity":
                "identity" in near_set,
        })

    assert len(candidate_rows) == 4740
    assert len(oracle_rows) == 90

    old_summary_path = (
        bundle / "analysis-summary.json"
    )

    if old_summary_path.exists():
        old = load(old_summary_path)

        assert (
            sum(
                r["correctness_admitted"]
                for r in candidate_rows
            )
            == old[
                "candidate_instance_admitted"
            ]
        )

        assert (
            sum(
                not r["correctness_admitted"]
                for r in candidate_rows
            )
            == old[
                "candidate_instance_correctness_rejected"
            ]
        )

    out.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_csv(
        out / "candidate-scores.csv",
        candidate_rows,
    )

    write_csv(
        out / "hidden-oracle.csv",
        oracle_rows,
    )

    oracle_speedups = [
        r["oracle_speedup"]
        for r in oracle_rows
    ]

    valid_rows = [
        r for r in candidate_rows
        if r["oracle_eligible"]
    ]

    measurement_invalid = [
        r for r in candidate_rows
        if r["correctness_admitted"]
        and not r["measurement_valid"]
    ]

    nonidentity_noops = [
        r for r in candidate_rows
        if r["machine_code_noop"]
    ]

    summary = {
        "analysis_id": ANALYSIS_ID,
        "host_id": HOST_ID,

        "instances": len(oracle_rows),
        "candidate_rows": len(candidate_rows),

        "correctness_admitted": sum(
            r["correctness_admitted"]
            for r in candidate_rows
        ),

        "correctness_rejected": sum(
            not r["correctness_admitted"]
            for r in candidate_rows
        ),

        "oracle_eligible_candidates":
            len(valid_rows),

        "measurement_invalid_candidates":
            len(measurement_invalid),

        "nonidentity_machine_code_noops":
            len(nonidentity_noops),

        "instances_oracle_faster_than_reference":
            sum(
                r["oracle_speedup"] > 1.0
                for r in oracle_rows
            ),

        "instances_oracle_includes_identity":
            sum(
                r["oracle_includes_identity"]
                for r in oracle_rows
            ),

        "instances_near_oracle_includes_identity":
            sum(
                r["near_oracle_includes_identity"]
                for r in oracle_rows
            ),

        "oracle_speedup_mean":
            statistics.fmean(
                oracle_speedups
            ),

        "oracle_speedup_median":
            statistics.median(
                oracle_speedups
            ),

        "oracle_speedup_min":
            min(oracle_speedups),

        "oracle_speedup_max":
            max(oracle_speedups),

        "near_oracle_candidate_count_mean":
            statistics.fmean(
                r[
                    "near_oracle_candidate_count"
                ]
                for r in oracle_rows
            ),

        "analysis_contract_sha256":
            sha256(contract_path),

        "bundle_SHA256SUMS_sha256":
            (
                sha256(
                    bundle
                    / "SHA256SUMS"
                )
                if (
                    bundle
                    / "SHA256SUMS"
                ).exists()
                else None
            ),

        "formal_equivalence_proven":
            False,
    }

    dump(
        out / "summary.json",
        summary,
    )

    # Aggregate by hint family.
    family_rows = []

    families = [
        "identity",
        "unroll_count",
        "interleave_count",
        "vectorize_width",
    ]

    for family in families:
        xs = [
            r for r in candidate_rows
            if r["hint_kind"] == family
        ]

        valid = [
            r for r in xs
            if r["oracle_eligible"]
        ]

        family_rows.append({
            "hint_kind": family,
            "candidate_rows": len(xs),
            "correctness_admitted": sum(
                r["correctness_admitted"]
                for r in xs
            ),
            "measurement_valid": len(valid),
            "machine_code_noop": sum(
                r["machine_code_noop"]
                for r in xs
            ),
            "faster_than_reference": sum(
                r["faster_than_reference"]
                for r in xs
            ),
            "oracle_memberships": sum(
                r["is_oracle"]
                for r in xs
            ),
            "near_oracle_memberships": sum(
                r["near_oracle"]
                for r in xs
            ),
            "valid_speedup_mean":
                (
                    statistics.fmean(
                        r["speedup"]
                        for r in valid
                    )
                    if valid
                    else None
                ),
            "valid_speedup_median":
                (
                    statistics.median(
                        r["speedup"]
                        for r in valid
                    )
                    if valid
                    else None
                ),
        })

    write_csv(
        out / "hint-family-summary.csv",
        family_rows,
    )

    metadata = {
        "analysis_id": ANALYSIS_ID,
        "host_id": HOST_ID,
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip(),
        "contract_path":
            str(contract_path),
        "contract_sha256":
            sha256(contract_path),
        "source_bundle":
            str(bundle),
    }

    dump(
        out / "metadata.json",
        metadata,
    )

    print(
        "HASWELL_HIDDEN_ORACLE_EXTRACTION_COMPLETE"
    )

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "candidate_scores =",
        out / "candidate-scores.csv",
    )

    print(
        "hidden_oracle =",
        out / "hidden-oracle.csv",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
