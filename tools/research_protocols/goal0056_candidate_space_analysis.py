#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(
    "external-results/"
    "haswell-e3-1241v3/"
    "hidden-oracle-v1"
)

OUT = Path(
    "external-results/"
    "haswell-e3-1241v3/"
    "candidate-space-analysis-v1"
)

FAMILIES = (
    "identity",
    "unroll_count",
    "interleave_count",
    "vectorize_width",
)


def as_bool(x: str) -> bool:
    return x.lower() == "true"


def load_rows():
    with (ROOT / "candidate-scores.csv").open(
        newline="",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r["oracle_eligible"] = as_bool(
            r["oracle_eligible"]
        )
        r["machine_code_noop"] = as_bool(
            r["machine_code_noop"]
        )
        r["speedup"] = (
            float(r["speedup"])
            if r["speedup"]
            else None
        )

    return rows


def best(rows, families):
    xs = [
        r["speedup"]
        for r in rows
        if (
            r["oracle_eligible"]
            and r["hint_kind"] in families
            and r["speedup"] is not None
        )
    ]

    if not xs:
        raise RuntimeError(
            f"no valid candidate for {families}"
        )

    return max(xs)


def main():
    rows = load_rows()

    groups = defaultdict(list)

    for r in rows:
        groups[
            (r["kernel"], r["size"])
        ].append(r)

    assert len(groups) == 90

    instance_rows = []

    for (kernel, size), xs in sorted(groups.items()):
        full = best(xs, FAMILIES)

        identity = best(
            xs,
            {"identity"},
        )

        unroll = best(
            xs,
            {
                "identity",
                "unroll_count",
            },
        )

        interleave = best(
            xs,
            {
                "identity",
                "interleave_count",
            },
        )

        vectorize = best(
            xs,
            {
                "identity",
                "vectorize_width",
            },
        )

        no_unroll = best(
            xs,
            {
                "identity",
                "interleave_count",
                "vectorize_width",
            },
        )

        no_interleave = best(
            xs,
            {
                "identity",
                "unroll_count",
                "vectorize_width",
            },
        )

        no_vectorize = best(
            xs,
            {
                "identity",
                "unroll_count",
                "interleave_count",
            },
        )

        valid = [
            r
            for r in xs
            if r["oracle_eligible"]
        ]

        candidate_uniform_mean = statistics.fmean(
            r["speedup"]
            for r in valid
        )

        # 同じ機械語を多数の候補IDが持つことによる
        # 重複バイアスを避けた無作為基準。
        reps = {}

        for r in valid:
            rep = r[
                "machine_code_representative"
            ]

            if rep not in reps:
                reps[rep] = r["speedup"]
            else:
                assert abs(
                    reps[rep] - r["speedup"]
                ) < 1e-12

        machine_uniform_mean = (
            statistics.fmean(
                reps.values()
            )
        )

        instance_rows.append({
            "kernel": kernel,
            "size": size,

            "full_oracle": full,

            "identity": identity,

            "unroll_only_oracle": unroll,
            "interleave_only_oracle": interleave,
            "vectorize_only_oracle": vectorize,

            "without_unroll_oracle": no_unroll,
            "without_interleave_oracle": no_interleave,
            "without_vectorize_oracle": no_vectorize,

            "unroll_only_regret":
                1 - unroll / full,

            "interleave_only_regret":
                1 - interleave / full,

            "vectorize_only_regret":
                1 - vectorize / full,

            "remove_unroll_regret":
                1 - no_unroll / full,

            "remove_interleave_regret":
                1 - no_interleave / full,

            "remove_vectorize_regret":
                1 - no_vectorize / full,

            "candidate_uniform_mean_speedup":
                candidate_uniform_mean,

            "machine_code_uniform_mean_speedup":
                machine_uniform_mean,

            "valid_candidate_count":
                len(valid),

            "unique_machine_code_count":
                len(reps),
        })

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = OUT / "instances.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                instance_rows[0].keys()
            ),
        )
        writer.writeheader()
        writer.writerows(instance_rows)

    def mean(key):
        return statistics.fmean(
            x[key]
            for x in instance_rows
        )

    def median(key):
        return statistics.median(
            x[key]
            for x in instance_rows
        )

    summary = {
        "instances": 90,

        "full_oracle_speedup_mean":
            mean("full_oracle"),

        "full_oracle_speedup_median":
            median("full_oracle"),

        "unroll_only_oracle_mean":
            mean("unroll_only_oracle"),

        "interleave_only_oracle_mean":
            mean("interleave_only_oracle"),

        "vectorize_only_oracle_mean":
            mean("vectorize_only_oracle"),

        "unroll_only_regret_mean":
            mean("unroll_only_regret"),

        "interleave_only_regret_mean":
            mean("interleave_only_regret"),

        "vectorize_only_regret_mean":
            mean("vectorize_only_regret"),

        "remove_unroll_regret_mean":
            mean("remove_unroll_regret"),

        "remove_interleave_regret_mean":
            mean("remove_interleave_regret"),

        "remove_vectorize_regret_mean":
            mean("remove_vectorize_regret"),

        "instances_unroll_required_for_exact_oracle":
            sum(
                x["remove_unroll_regret"] > 1e-15
                for x in instance_rows
            ),

        "instances_interleave_required_for_exact_oracle":
            sum(
                x["remove_interleave_regret"] > 1e-15
                for x in instance_rows
            ),

        "instances_vectorize_required_for_exact_oracle":
            sum(
                x["remove_vectorize_regret"] > 1e-15
                for x in instance_rows
            ),

        "candidate_uniform_mean_speedup":
            mean(
                "candidate_uniform_mean_speedup"
            ),

        "machine_code_uniform_mean_speedup":
            mean(
                "machine_code_uniform_mean_speedup"
            ),

        "valid_candidate_count_mean":
            mean("valid_candidate_count"),

        "unique_machine_code_count_mean":
            mean("unique_machine_code_count"),
    }

    (OUT / "summary.json").write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        "CANDIDATE_SPACE_ANALYSIS_COMPLETE"
    )

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
