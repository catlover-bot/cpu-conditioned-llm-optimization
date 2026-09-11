#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

EXPECTED_ARCHIVE_SHA256 = (
    "753965e5ffd4856a9e218b2d02ef293b"
    "9d469096eeb3eacbef354064775acc34"
)

ARCHIVE = Path(
    "external-results/"
    "haswell-e3-1241v3/"
    "final-atlas/"
    "cpucond-haswell02-final-atlas-90of90.tgz"
)

BUNDLE = Path(
    "external-results/"
    "haswell-e3-1241v3/"
    "final-atlas/"
    "analysis-bundle"
)

MARKER = "runs/goal0054-final-atlas/"

WANTED = (
    "final-timing.json",
    "final-timing-summary.json",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(block)

    return h.hexdigest()


def main() -> int:
    actual = sha256(ARCHIVE)

    if actual != EXPECTED_ARCHIVE_SHA256:
        raise RuntimeError(
            f"archive SHA mismatch: {actual}"
        )

    counts = {
        name: 0
        for name in WANTED
    }

    extracted = []

    bundle_root = BUNDLE.resolve()
    bundle_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tarfile.open(
        ARCHIVE,
        "r:gz",
    ) as tf:
        selected = []

        for member in tf.getmembers():
            if not member.isfile():
                continue

            name = member.name

            matched = None

            for wanted in WANTED:
                if name.endswith(
                    "/" + wanted
                ):
                    matched = wanted
                    break

            if matched is None:
                continue

            if MARKER not in name:
                raise RuntimeError(
                    f"unexpected timing member: {name}"
                )

            selected.append(
                (member, matched)
            )

        for _, kind in selected:
            counts[kind] += 1

        if counts != {
            "final-timing.json": 90,
            "final-timing-summary.json": 90,
        }:
            raise RuntimeError(
                f"unexpected counts: {counts}"
            )

        for member, kind in selected:
            raw = tf.extractfile(member)

            if raw is None:
                raise RuntimeError(
                    f"cannot extract {member.name}"
                )

            data = raw.read()

            rel = member.name.split(
                MARKER,
                1,
            )[1]

            parts = Path(rel).parts

            # First component is unique run ID.
            if len(parts) < 3:
                raise RuntimeError(
                    f"unexpected path: {member.name}"
                )

            rel2 = Path(*parts[1:])

            dest = (
                bundle_root / rel2
            ).resolve()

            if (
                dest != bundle_root
                and bundle_root
                not in dest.parents
            ):
                raise RuntimeError(
                    "path traversal rejected"
                )

            dest.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            dest.write_bytes(data)

            extracted.append({
                "source_member":
                    member.name,
                "bundle_path":
                    str(rel2),
                "kind":
                    kind,
                "bytes":
                    len(data),
                "sha256":
                    hashlib.sha256(
                        data
                    ).hexdigest(),
            })

    metadata = {
        "completion":
            "ANALYSIS_BUNDLE_TIMING_COMPLETION_COMPLETE",

        "source_archive":
            str(ARCHIVE),

        "source_archive_sha256":
            EXPECTED_ARCHIVE_SHA256,

        "counts":
            counts,

        "files_added":
            len(extracted),

        "performance_values_inspected_by_this_script":
            False,

        "files":
            extracted,
    }

    (
        BUNDLE
        / "bundle-timing-completion-v1.json"
    ).write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        "ANALYSIS_BUNDLE_TIMING_COMPLETION_COMPLETE"
    )

    print(
        "final-timing.json =",
        counts["final-timing.json"],
    )

    print(
        "final-timing-summary.json =",
        counts[
            "final-timing-summary.json"
        ],
    )

    print(
        "files_added =",
        len(extracted),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
