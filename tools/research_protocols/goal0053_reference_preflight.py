#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone

SIZES = (
    "MINI_DATASET",
    "SMALL_DATASET",
    "MEDIUM_DATASET",
    "LARGE_DATASET",
    "EXTRALARGE_DATASET",
)

TARGET_BATCH_S = 0.005
SESSIONS = 2
PAIRS_PER_SESSION = 8


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, x) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(x, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def parse_polybench_time(raw: bytes):
    text = raw.decode(errors="replace")
    vals = []

    for line in text.splitlines():
        line = line.strip()

        if re.fullmatch(
            r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)"
            r"(?:[eE][+-]?[0-9]+)?",
            line,
        ):
            try:
                x = float(line)
            except ValueError:
                continue

            if x > 0:
                vals.append(x)

    return vals[-1] if vals else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--cpu", type=int, default=2)
    args = ap.parse_args()

    repo = args.repo.resolve()

    manifest_path = repo / "configs/final-candidate-manifest-v1.json"

    intake = (
        repo
        / "runs/goal0041-dataset-intake"
        / "20260910T132522.441454Z-69857bdb"
    )

    pb = intake / "upstream/polybench-c-4.2.1-beta"
    catalog_path = intake / "polybench-catalog.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    if manifest["kernel_count"] != 30:
        raise RuntimeError("unexpected manifest kernel count")

    by_id = {x["id"]: x for x in catalog}

    clang = shutil.which("clang")
    if clang is None:
        raise RuntimeError("clang missing")

    rid = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )

    out = repo / "runs/goal0053-reference-preflight" / rid
    out.mkdir(parents=True)

    rows = []

    flags = [
        "-std=gnu11",
        "-O3",
        "-march=native",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-fno-lto",
        "-DPOLYBENCH_TIME",
    ]

    print("=== REFERENCE-ONLY FINAL-ATLAS PREFLIGHT ===")
    print("timeout_per_instance_s =", args.timeout)
    print()

    for kernel in manifest["kernels"]:
        kid = kernel["kernel_id"]
        candidates = kernel["candidate_count_including_identity"]

        source = pb / by_id[kid]["source"]

        if sha(source) != by_id[kid]["source_sha256"]:
            raise RuntimeError(f"{kid}: source digest changed")

        kernel_rows = []

        for size in SIZES:
            d = out / kid / size
            d.mkdir(parents=True)

            program = d / "program"

            cmd = [
                clang,
                *flags,
                f"-D{size}",
                "-I", str(pb / "utilities"),
                "-I", str(source.parent),
                str(source),
                str(pb / "utilities/polybench.c"),
                "-lm",
                "-o", str(program),
            ]

            cp = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                env={**os.environ, "LC_ALL": "C"},
            )

            (d / "compile.stdout").write_bytes(cp.stdout)
            (d / "compile.stderr").write_bytes(cp.stderr)

            if cp.returncode != 0:
                row = {
                    "kernel": kid,
                    "size": size,
                    "candidate_count": candidates,
                    "state": "compile_failed",
                    "returncode": cp.returncode,
                }
                rows.append(row)
                kernel_rows.append(row)
                print(f"{kid:16s} {size:18s} COMPILE_FAILED")
                continue

            start = time.monotonic()

            try:
                rp = subprocess.run(
                    [
                        "taskset",
                        "-c", str(args.cpu),
                        str(program),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=args.timeout,
                    env={**os.environ, "LC_ALL": "C"},
                )

                wall = time.monotonic() - start

                (d / "run.stdout").write_bytes(rp.stdout)
                (d / "run.stderr").write_bytes(rp.stderr)

                pb_time = parse_polybench_time(rp.stdout)

                if rp.returncode == 0 and pb_time is not None:
                    state = "ok"
                    effective = max(TARGET_BATCH_S, pb_time)
                else:
                    state = "run_failed"
                    effective = None

                row = {
                    "kernel": kid,
                    "size": size,
                    "candidate_count": candidates,
                    "state": state,
                    "polybench_reference_seconds": pb_time,
                    "wall_seconds": wall,
                    "effective_min_batch_seconds": effective,
                    "returncode": rp.returncode,
                }

            except subprocess.TimeoutExpired as e:
                wall = time.monotonic() - start

                (d / "run.stdout").write_bytes(e.stdout or b"")
                (d / "run.stderr").write_bytes(e.stderr or b"")

                row = {
                    "kernel": kid,
                    "size": size,
                    "candidate_count": candidates,
                    "state": "timeout",
                    "polybench_reference_seconds": None,
                    "wall_seconds": wall,
                    "effective_min_batch_seconds": args.timeout,
                    "timeout_lower_bound_seconds": args.timeout,
                }

            rows.append(row)
            kernel_rows.append(row)

            display = (
                f"{row['polybench_reference_seconds']:.6f}s"
                if row.get("polybench_reference_seconds") is not None
                else row["state"]
            )

            print(
                f"{kid:16s} "
                f"{size:18s} "
                f"{display}"
            )

        # Lower bound assuming candidate cost ~= reference and no warmup/process overhead.
        floor = 0.0

        for row in kernel_rows:
            effective = row.get("effective_min_batch_seconds")

            if effective is None:
                continue

            # 2 sessions × 8 pairs × (reference + candidate)
            observations = SESSIONS * PAIRS_PER_SESSION * 2

            floor += candidates * observations * effective

        print(
            f"  -> candidates={candidates}, "
            f"timed-kernel floor≈{floor/3600:.3f} h"
        )
        print()

    ok = [x for x in rows if x["state"] == "ok"]
    timeouts = [x for x in rows if x["state"] == "timeout"]
    failures = [
        x for x in rows
        if x["state"] not in ("ok", "timeout")
    ]

    total_floor = 0.0

    for row in rows:
        effective = row.get("effective_min_batch_seconds")

        if effective is None:
            continue

        observations = SESSIONS * PAIRS_PER_SESSION * 2

        total_floor += (
            row["candidate_count"]
            * observations
            * effective
        )

    summary = {
        "completion": "REFERENCE_PREFLIGHT_COMPLETE",
        "run_directory": str(out),
        "manifest_sha256": sha(manifest_path),
        "instances_planned": 150,
        "instances_ok": len(ok),
        "instances_timeout": len(timeouts),
        "instances_failed": len(failures),
        "timeout_seconds": args.timeout,
        "initial_target_batch_seconds": TARGET_BATCH_S,
        "candidate_instance_pairs": 7900,
        "reference_equivalent_timed_kernel_floor_seconds":
            total_floor,
        "reference_equivalent_timed_kernel_floor_hours":
            total_floor / 3600,
        "important": (
            "This is a feasibility floor, not a final-runtime prediction. "
            "It excludes compilation, validation, process overhead, "
            "warmups, escalation, and candidate slowdowns."
        ),
        "rows": rows,
    }

    write_json(out / "summary.json", summary)

    print("REFERENCE_PREFLIGHT_COMPLETE")
    print("instances_ok =", len(ok))
    print("instances_timeout =", len(timeouts))
    print("instances_failed =", len(failures))
    print(
        "reference_equivalent_timed_kernel_floor_hours =",
        round(total_floor / 3600, 3),
    )
    print("run =", out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
