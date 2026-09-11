#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

REPO = Path.cwd()

INTAKE = (
    REPO
    / "runs/goal0041-dataset-intake"
    / "20260910T132522.441454Z-69857bdb"
)

PB = INTAKE / "upstream/polybench-c-4.2.1-beta"

CATALOG = json.loads(
    (INTAKE / "polybench-catalog.json").read_text(
        encoding="utf-8"
    )
)

MANIFEST = json.loads(
    (REPO / "configs/final-candidate-manifest-v1.json")
    .read_text(encoding="utf-8")
)

PROTOCOL = json.loads(
    (REPO / "configs/final-experiment-v1.2.json")
    .read_text(encoding="utf-8")
)

SIZES = (
    "MINI_DATASET",
    "SMALL_DATASET",
    "MEDIUM_DATASET",
)

PROFILES = {
    "oracle_O0": ["-O0"],
    "generic_O3": ["-O3"],
    "native_O3": ["-O3", "-march=native"],
    "sanitized": [
        "-O1",
        "-fsanitize=address,undefined",
        "-fno-sanitize-recover=all",
        "-fno-omit-frame-pointer",
    ],
}

COMMON = [
    "-std=gnu11",
    "-fno-fast-math",
    "-ffp-contract=off",
    "-fno-lto",
]


def sha_bytes(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_json(p: Path, x) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(
            x,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ) + "\n",
        encoding="utf-8",
    )


def mask_noncode(text: str) -> str:
    out = list(text)
    i = 0
    n = len(text)
    state = "code"
    quote = None

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "line":
            if c == "\n":
                state = "code"
            else:
                out[i] = " "
            i += 1
            continue

        if state == "block":
            out[i] = " "
            if c == "*" and nxt == "/":
                out[i + 1] = " "
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "literal":
            out[i] = " "
            if c == "\\":
                if i + 1 < n:
                    out[i + 1] = " "
                i += 2
                continue
            if c == quote:
                state = "code"
                quote = None
            i += 1
            continue

        if c == "/" and nxt == "/":
            out[i] = out[i + 1] = " "
            state = "line"
            i += 2
            continue

        if c == "/" and nxt == "*":
            out[i] = out[i + 1] = " "
            state = "block"
            i += 2
            continue

        if c in ("'", '"'):
            out[i] = " "
            state = "literal"
            quote = c
            i += 1
            continue

        i += 1

    return "".join(out)


def matching(
    masked: str,
    opening: int,
    left: str,
    right: str,
) -> int:
    depth = 0

    for i in range(opening, len(masked)):
        c = masked[i]

        if c == left:
            depth += 1
        elif c == right:
            depth -= 1

            if depth == 0:
                return i

    raise RuntimeError("unbalanced delimiter")


def function_span(
    text: str,
    name: str,
    return_type: str,
) -> tuple[int, int]:
    masked = mask_noncode(text)

    pat = re.compile(
        r"\b(?:static\s+)?"
        + re.escape(return_type)
        + r"\s+"
        + re.escape(name)
        + r"\s*\("
    )

    found = []

    for m in pat.finditer(masked):
        opening = masked.find("{", m.end())

        if opening < 0:
            continue

        semicolon = masked.find(
            ";",
            m.end(),
            opening,
        )

        if semicolon >= 0:
            continue

        end = matching(
            masked,
            opening,
            "{",
            "}",
        ) + 1

        found.append((m.start(), end))

    if len(found) != 1:
        raise RuntimeError(
            f"{name}: expected one definition, "
            f"got {len(found)}"
        )

    return found[0]


def split_args(text: str) -> list[str]:
    masked = mask_noncode(text)

    paren = 0
    bracket = 0
    brace = 0
    start = 0
    out = []

    for i, c in enumerate(masked):
        if c == "(":
            paren += 1
        elif c == ")":
            paren -= 1
        elif c == "[":
            bracket += 1
        elif c == "]":
            bracket -= 1
        elif c == "{":
            brace += 1
        elif c == "}":
            brace -= 1
        elif (
            c == ","
            and paren == 0
            and bracket == 0
            and brace == 0
        ):
            out.append(text[start:i].strip())
            start = i + 1

    out.append(text[start:].strip())

    return out


def raw_instrument_print_array(
    source: str,
) -> tuple[str, int]:
    ps, pe = function_span(
        source,
        "print_array",
        "void",
    )

    fn = source[ps:pe]
    masked = mask_noncode(fn)

    calls = []

    for m in re.finditer(
        r"\bfprintf\s*\(",
        masked,
    ):
        opening = masked.find("(", m.start())

        closing = matching(
            masked,
            opening,
            "(",
            ")",
        )

        j = closing + 1

        while (
            j < len(masked)
            and masked[j].isspace()
        ):
            j += 1

        if (
            j >= len(masked)
            or masked[j] != ";"
        ):
            raise RuntimeError(
                "fprintf statement malformed"
            )

        args = split_args(
            fn[opening + 1:closing]
        )

        if len(args) != 3:
            continue

        a0 = re.sub(r"\s+", "", args[0])
        a1 = re.sub(r"\s+", "", args[1])

        if (
            a0 == "POLYBENCH_DUMP_TARGET"
            and a1 == "DATA_PRINTF_MODIFIER"
        ):
            calls.append(
                (
                    m.start(),
                    j + 1,
                    args[2],
                )
            )

    if not calls:
        raise RuntimeError(
            "no DATA_PRINTF_MODIFIER emission"
        )

    for start, end, expr in reversed(calls):
        replacement = (
            "do { "
            "__typeof__(" + expr + ") "
            "cpucond_raw_value = (" + expr + "); "
            "cpucond_emit_value("
            "&cpucond_raw_value, "
            "sizeof(cpucond_raw_value)); "
            "} while (0);"
        )

        fn = (
            fn[:start]
            + replacement
            + fn[end:]
        )

    helper = r'''
#include <stdio.h>
#include <stdlib.h>

static void cpucond_emit_value(
    const void *p,
    size_t n
) {
    if (fwrite(p, 1, n, stdout) != n) {
        fputs(
            "cpucond raw write failed\n",
            stderr
        );
        exit(91);
    }
}
'''

    source = (
        helper
        + "\n"
        + source[:ps]
        + fn
        + source[pe:]
    )

    return source, len(calls)


def add_noinline(
    source: str,
    kernel: str,
) -> str:
    ks, ke = function_span(
        source,
        kernel,
        "void",
    )

    fn = source[ks:ke]
    masked = mask_noncode(fn)

    m = re.search(
        r"\bvoid\s+"
        + re.escape(kernel)
        + r"\s*\(",
        masked,
    )

    if m is None:
        raise RuntimeError(
            "kernel header not found"
        )

    at = ks + m.start()

    return (
        source[:at]
        + "__attribute__((noinline)) "
        + source[at:]
    )


def transformed_identity(
    source: str,
    kernel: str,
) -> tuple[str, int]:
    source = add_noinline(
        source,
        kernel,
    )

    return raw_instrument_print_array(
        source
    )


def run(
    argv: list[str],
    timeout: int = 60,
) -> tuple[int | None, bytes, bytes]:
    env = {
        **os.environ,
        "LC_ALL": "C",
        "ASAN_OPTIONS":
            "detect_leaks=0:halt_on_error=1",
        "UBSAN_OPTIONS":
            "halt_on_error=1:"
            "print_stacktrace=1",
    }

    try:
        p = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env=env,
        )

        return (
            p.returncode,
            p.stdout,
            p.stderr,
        )

    except subprocess.TimeoutExpired as e:
        return (
            None,
            e.stdout or b"",
            e.stderr or b"",
        )


def compile_program(
    clang: str,
    source_dir: Path,
    source: str,
    size: str,
    profile: str,
    out: Path,
) -> Path:
    out.mkdir(parents=True)

    src = out / "program.c"
    binary = out / "program"

    src.write_text(
        source,
        encoding="utf-8",
    )

    flags = [
        *COMMON,
        *PROFILES[profile],
        f"-D{size}",
        "-DPOLYBENCH_USE_C99_PROTO",
        "-DPOLYBENCH_DUMP_ARRAYS",
        "-I",
        str(PB / "utilities"),
        "-I",
        str(source_dir),
        str(src),
        str(PB / "utilities/polybench.c"),
        "-lm",
        "-o",
        str(binary),
    ]

    rc, stdout, stderr = run(
        [clang, *flags],
        timeout=120,
    )

    (out / "compile.stdout").write_bytes(
        stdout
    )
    (out / "compile.stderr").write_bytes(
        stderr
    )

    if rc != 0:
        raise RuntimeError(
            f"compile failed {profile}: "
            + stderr.decode(
                errors="replace"
            )[:2000]
        )

    return binary


def main() -> int:
    if (
        PROTOCOL["protocol_id"]
        != "cpu-conditioned-final-v1.2"
    ):
        raise RuntimeError(
            "wrong frozen protocol"
        )

    if (
        MANIFEST[
            "total_candidates_across_30_kernels"
        ]
        != 1580
    ):
        raise RuntimeError(
            "candidate manifest changed"
        )

    clang = shutil.which("clang")

    if clang is None:
        raise RuntimeError("clang missing")

    by_catalog = {
        x["id"]: x
        for x in CATALOG
    }

    rid = (
        datetime.now(timezone.utc)
        .strftime("%Y%m%dT%H%M%S.%fZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )

    out = (
        REPO
        / "runs/goal0054-identity-liveout-smoke"
        / rid
    )

    out.mkdir(parents=True)

    rows = []

    print(
        "=== FINAL 30x3 IDENTITY "
        "RAW LIVE-OUT SMOKE ==="
    )

    for entry in MANIFEST["kernels"]:
        kid = entry["kernel_id"]
        cat = by_catalog[kid]

        source_path = PB / cat["source"]

        if (
            sha_file(source_path)
            != cat["source_sha256"]
        ):
            raise RuntimeError(
                f"{kid}: source hash changed"
            )

        original = source_path.read_text(
            encoding="utf-8"
        )

        kernel = (
            "kernel_"
            + kid.replace("-", "_")
        )

        transformed, value_calls = (
            transformed_identity(
                original,
                kernel,
            )
        )

        for size in SIZES:
            d = out / kid / size

            oracle_binary = compile_program(
                clang,
                source_path.parent,
                transformed,
                size,
                "oracle_O0",
                d / "oracle_O0",
            )

            rc, oracle, err = run(
                [str(oracle_binary)]
            )

            if rc != 0:
                raise RuntimeError(
                    f"{kid}/{size}: "
                    "oracle failed: "
                    + err.decode(
                        errors="replace"
                    )[:1000]
                )

            if not oracle:
                raise RuntimeError(
                    f"{kid}/{size}: "
                    "empty raw oracle"
                )

            negative = bytearray(oracle)
            negative[len(negative) // 2] ^= 1

            if bytes(negative) == oracle:
                raise RuntimeError(
                    "negative control failed"
                )

            profile_rows = []

            for profile in (
                "generic_O3",
                "native_O3",
                "sanitized",
            ):
                binary = compile_program(
                    clang,
                    source_path.parent,
                    transformed,
                    size,
                    profile,
                    d / profile,
                )

                rc, raw, err = run(
                    [str(binary)]
                )

                passed = (
                    rc == 0
                    and raw == oracle
                )

                profile_rows.append(
                    {
                        "profile": profile,
                        "passed": passed,
                        "returncode": rc,
                        "stdout_bytes":
                            len(raw),
                        "stdout_sha256":
                            sha_bytes(raw),
                    }
                )

                if not passed:
                    raise RuntimeError(
                        f"{kid}/{size}/"
                        f"{profile}: "
                        "live-out mismatch or "
                        "runtime failure; "
                        + err.decode(
                            errors="replace"
                        )[:1000]
                    )

            row = {
                "kernel_id": kid,
                "size": size,
                "raw_value_emission_sites":
                    value_calls,
                "oracle_bytes": len(oracle),
                "oracle_sha256":
                    sha_bytes(oracle),
                "negative_control_rejected":
                    bytes(negative)
                    != oracle,
                "profiles": profile_rows,
                "passed": True,
            }

            rows.append(row)

            print(
                f"{kid:16s} "
                f"{size:14s} "
                f"raw={len(oracle):9d} "
                f"valuesites={value_calls:2d} "
                "gate=PASS"
            )

    passed = (
        len(rows) == 90
        and all(x["passed"] for x in rows)
    )

    summary = {
        "completion":
            "FINAL_IDENTITY_LIVEOUT_SMOKE_COMPLETE"
            if passed
            else
            "FINAL_IDENTITY_LIVEOUT_SMOKE_BLOCKED",
        "passed": passed,
        "instances": len(rows),
        "expected_instances": 90,
        "oracle_profile": "O0",
        "candidate_profiles": [
            "generic_O3",
            "native_O3",
            "sanitized",
        ],
        "comparison":
            "exact_raw_live_out_bytes",
        "candidate_hint_compilations": 0,
        "performance_measurements": 0,
        "llm_requests": 0,
        "formal_equivalence_proven": False,
        "rows": rows,
        "run_directory": str(out),
    }

    write_json(
        out / "summary.json",
        summary,
    )

    print()
    print(
        summary["completion"]
    )
    print("instances =", len(rows))
    print("passed =", passed)
    print("run =", out)

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
