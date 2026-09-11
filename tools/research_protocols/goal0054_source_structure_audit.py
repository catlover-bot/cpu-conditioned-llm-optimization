#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path.cwd()

INTAKE = (
    REPO
    / "runs/goal0041-dataset-intake"
    / "20260910T132522.441454Z-69857bdb"
)

PB = INTAKE / "upstream/polybench-c-4.2.1-beta"

CATALOG = json.loads(
    (INTAKE / "polybench-catalog.json").read_text(encoding="utf-8")
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


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def mask_noncode(text: str) -> str:
    """Preserve offsets, replacing comments and literals with spaces."""
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


def matching_body(text: str, opening: int) -> int:
    masked = mask_noncode(text)
    depth = 0

    for i in range(opening, len(masked)):
        c = masked[i]

        if c == "{":
            depth += 1

        elif c == "}":
            depth -= 1

            if depth == 0:
                return i + 1

            if depth < 0:
                raise RuntimeError("negative_brace_depth")

    raise RuntimeError("unbalanced_function_body")


def extract_function(text: str, name: str, return_type: str) -> str:
    masked = mask_noncode(text)

    pattern = re.compile(
        r"\b(?:static\s+)?"
        + re.escape(return_type)
        + r"\s+"
        + re.escape(name)
        + r"\s*\("
    )

    definitions = []

    for m in pattern.finditer(masked):
        opening = masked.find("{", m.end())

        if opening < 0:
            continue

        semicolon = masked.find(";", m.end(), opening)

        if semicolon >= 0:
            continue

        end = matching_body(text, opening)
        definitions.append(text[m.start():end])

    if len(definitions) != 1:
        raise RuntimeError(
            f"{name}: expected exactly one definition, "
            f"found {len(definitions)}"
        )

    return definitions[0]


def count_for_loops(function: str) -> int:
    masked = mask_noncode(function)

    return len(
        re.findall(
            r"\bfor\s*\(",
            masked,
        )
    )


def token_positions(function: str, tokens: list[str]) -> dict[str, list[int]]:
    masked = mask_noncode(function)
    result = {}

    for token in tokens:
        result[token] = [
            m.start()
            for m in re.finditer(
                r"\b" + re.escape(token) + r"\b",
                masked,
            )
        ]

    return result


def require_single_call_position(
    positions: dict[str, list[int]],
    token: str,
) -> int:
    xs = positions[token]

    if len(xs) != 1:
        raise RuntimeError(
            f"{token}: expected one occurrence in main, got {len(xs)}"
        )

    return xs[0]


def syntax_check(
    clang: str,
    source: Path,
    size: str,
) -> dict:
    cmd = [
        clang,
        "-std=gnu11",
        "-fsyntax-only",
        "-fno-fast-math",
        "-ffp-contract=off",
        f"-D{size}",
        "-DPOLYBENCH_USE_C99_PROTO",
        "-I", str(PB / "utilities"),
        "-I", str(source.parent),
        str(source),
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )

    return {
        "size": size,
        "passed": p.returncode == 0,
        "returncode": p.returncode,
        "stderr": p.stderr.decode(
            encoding="utf-8",
            errors="replace",
        )[:4000],
        "argv": cmd,
    }


def main() -> int:
    clang = shutil.which("clang")

    if clang is None:
        raise RuntimeError("clang_missing")

    if PROTOCOL["protocol_id"] != "cpu-conditioned-final-v1.2":
        raise RuntimeError("unexpected_protocol")

    if PROTOCOL["dataset"]["performance_sizes"] != [
        "MINI",
        "SMALL",
        "MEDIUM",
    ]:
        raise RuntimeError("unexpected_final_sizes")

    if MANIFEST["kernel_count"] != 30:
        raise RuntimeError("unexpected_manifest_kernel_count")

    catalog = {x["id"]: x for x in CATALOG}
    manifest = {x["kernel_id"]: x for x in MANIFEST["kernels"]}

    if set(catalog) != set(manifest):
        raise RuntimeError("catalog_manifest_kernel_set_mismatch")

    rid = (
        datetime.now(timezone.utc)
        .strftime("%Y%m%dT%H%M%S.%fZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )

    out = (
        REPO
        / "runs/goal0054-source-structure-audit"
        / rid
    )

    out.mkdir(parents=True)

    rows = []
    syntax_total = 0
    syntax_passed = 0

    print("=== FINAL POLYBENCH SOURCE STRUCTURE AUDIT ===")

    for kid in [x["kernel_id"] for x in MANIFEST["kernels"]]:
        cat = catalog[kid]
        man = manifest[kid]

        source = PB / cat["source"]

        if sha(source) != cat["source_sha256"]:
            raise RuntimeError(f"{kid}: source hash mismatch")

        text = source.read_text(encoding="utf-8")

        kernel_name = "kernel_" + kid.replace("-", "_")

        init_fn = extract_function(
            text,
            "init_array",
            "void",
        )

        kernel_fn = extract_function(
            text,
            kernel_name,
            "void",
        )

        print_fn = extract_function(
            text,
            "print_array",
            "void",
        )

        main_fn = extract_function(
            text,
            "main",
            "int",
        )

        observed_loops = count_for_loops(kernel_fn)
        expected_loops = man["syntactic_loop_count"]

        if observed_loops != expected_loops:
            raise RuntimeError(
                f"{kid}: loop count mismatch "
                f"{observed_loops} != {expected_loops}"
            )

        tokens = [
            "init_array",
            "polybench_start_instruments",
            kernel_name,
            "polybench_stop_instruments",
            "polybench_print_instruments",
            "print_array",
        ]

        pos = token_positions(main_fn, tokens)

        p_init = require_single_call_position(pos, "init_array")
        p_start = require_single_call_position(
            pos,
            "polybench_start_instruments",
        )
        p_kernel = require_single_call_position(pos, kernel_name)
        p_stop = require_single_call_position(
            pos,
            "polybench_stop_instruments",
        )
        p_print_time = require_single_call_position(
            pos,
            "polybench_print_instruments",
        )
        p_print_array = require_single_call_position(
            pos,
            "print_array",
        )

        if not (
            p_init
            < p_start
            < p_kernel
            < p_stop
            < p_print_time
            < p_print_array
        ):
            raise RuntimeError(
                f"{kid}: unexpected main call order"
            )

        syntax = []

        for size in SIZES:
            result = syntax_check(
                clang,
                source,
                size,
            )

            syntax.append(result)
            syntax_total += 1

            if result["passed"]:
                syntax_passed += 1
            else:
                raise RuntimeError(
                    f"{kid}/{size}: syntax failed:\n"
                    + result["stderr"]
                )

        row = {
            "kernel_id": kid,
            "source": cat["source"],
            "source_sha256": cat["source_sha256"],
            "kernel_function": kernel_name,
            "syntactic_loop_count": observed_loops,
            "candidate_count":
                man["candidate_count_including_identity"],
            "function_bytes": {
                "init_array": len(init_fn.encode()),
                "kernel": len(kernel_fn.encode()),
                "print_array": len(print_fn.encode()),
                "main": len(main_fn.encode()),
            },
            "main_order_verified": True,
            "syntax": syntax,
        }

        rows.append(row)

        print(
            f"{kid:16s} "
            f"loops={observed_loops:2d} "
            f"candidates="
            f"{man['candidate_count_including_identity']:3d} "
            f"syntax=3/3 "
            f"main_order=OK"
        )

    total_loops = sum(
        x["syntactic_loop_count"]
        for x in rows
    )

    total_candidates = sum(
        x["candidate_count"]
        for x in rows
    )

    if total_loops != 155:
        raise RuntimeError(
            f"expected 155 loops, got {total_loops}"
        )

    if total_candidates != 1580:
        raise RuntimeError(
            f"expected 1580 candidates, got {total_candidates}"
        )

    if syntax_total != 90 or syntax_passed != 90:
        raise RuntimeError(
            f"expected 90/90 syntax checks, "
            f"got {syntax_passed}/{syntax_total}"
        )

    summary = {
        "completion":
            "FINAL_SOURCE_STRUCTURE_AUDIT_COMPLETE",
        "passed": True,
        "protocol":
            "cpu-conditioned-final-v1.2",
        "kernel_count": len(rows),
        "size_count": len(SIZES),
        "syntax_checks": syntax_total,
        "syntax_checks_passed": syntax_passed,
        "total_syntactic_loops": total_loops,
        "total_candidates": total_candidates,
        "main_instances": 30 * len(SIZES),
        "candidate_instances":
            total_candidates * len(SIZES),
        "all_main_call_orders_verified": True,
        "performance_measurements": 0,
        "candidate_compilations": 0,
        "llm_requests": 0,
        "rows": rows,
    }

    (out / "summary.json").write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print()
    print("FINAL_SOURCE_STRUCTURE_AUDIT_COMPLETE")
    print("kernels = 30")
    print("syntax_checks = 90/90")
    print("syntactic_loops =", total_loops)
    print("candidates =", total_candidates)
    print(
        "candidate_instances =",
        total_candidates * len(SIZES),
    )
    print("run =", out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
