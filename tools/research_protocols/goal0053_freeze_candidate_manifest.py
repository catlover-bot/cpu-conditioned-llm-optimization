#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path.cwd()

INTAKE = (
    REPO
    / "runs/goal0041-dataset-intake"
    / "20260910T132522.441454Z-69857bdb"
)

PB = INTAKE / "upstream/polybench-c-4.2.1-beta"
CATALOG = INTAKE / "polybench-catalog.json"

OUT = REPO / "configs/final-candidate-manifest-v1.json"

SIZES = (
    "MINI_DATASET",
    "SMALL_DATASET",
    "MEDIUM_DATASET",
    "LARGE_DATASET",
    "EXTRALARGE_DATASET",
)

HINTS = {
    "unroll_count": (2, 4, 8, 16),
    "interleave_count": (2, 4, 8),
    "vectorize_width": (2, 4, 8),
}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def extract_function(text: str, name: str) -> str:
    """Lexically extract one C function definition.

    This is source navigation only, not a C semantic parser.
    Braces inside strings, character literals, // comments, and /* comments */
    are ignored.
    """
    pattern = (
        r"\b(?:static\s+)?void\s+"
        + re.escape(name)
        + r"\s*\("
    )
    matches = list(re.finditer(pattern, text))

    if len(matches) != 1:
        raise RuntimeError(
            f"{name}: expected one definition, got {len(matches)}"
        )

    start = matches[0].start()

    i = matches[0].end()
    n = len(text)
    state = "code"
    quote = None

    # Find the opening brace of the definition while ignoring comments/strings.
    opening = None

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "line_comment":
            if c == "\n":
                state = "code"
            i += 1
            continue

        if state == "block_comment":
            if c == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "string":
            if c == "\\":
                i += 2
                continue
            if c == quote:
                state = "code"
                quote = None
            i += 1
            continue

        if c == "/" and nxt == "/":
            state = "line_comment"
            i += 2
            continue

        if c == "/" and nxt == "*":
            state = "block_comment"
            i += 2
            continue

        if c in ("'", '"'):
            state = "string"
            quote = c
            i += 1
            continue

        if c == ";":
            raise RuntimeError(
                f"{name}: matched declaration/prototype, not definition"
            )

        if c == "{":
            opening = i
            break

        i += 1

    if opening is None:
        raise RuntimeError(f"{name}: opening brace not found")

    # Match the compound statement.
    depth = 0
    i = opening
    state = "code"
    quote = None

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "line_comment":
            if c == "\n":
                state = "code"
            i += 1
            continue

        if state == "block_comment":
            if c == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "string":
            if c == "\\":
                i += 2
                continue
            if c == quote:
                state = "code"
                quote = None
            i += 1
            continue

        if c == "/" and nxt == "/":
            state = "line_comment"
            i += 2
            continue

        if c == "/" and nxt == "*":
            state = "block_comment"
            i += 2
            continue

        if c in ("'", '"'):
            state = "string"
            quote = c
            i += 1
            continue

        if c == "{":
            depth += 1

        elif c == "}":
            depth -= 1

            if depth < 0:
                raise RuntimeError(
                    f"{name}: negative brace depth"
                )

            if depth == 0:
                return text[start:i + 1]

        i += 1

    raise RuntimeError(
        f"{name}: unbalanced braces after lexical scan"
    )


def for_positions(text: str) -> list[int]:
    positions = []
    i = 0
    n = len(text)
    state = "code"
    quote = None

    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "line-comment":
            if c == "\n":
                state = "code"
            i += 1
            continue

        if state == "block-comment":
            if c == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "string":
            if c == "\\":
                i += 2
                continue
            if c == quote:
                state = "code"
            i += 1
            continue

        if c == "/" and nxt == "/":
            state = "line-comment"
            i += 2
            continue

        if c == "/" and nxt == "*":
            state = "block-comment"
            i += 2
            continue

        if c in ("'", '"'):
            state = "string"
            quote = c
            i += 1
            continue

        if text.startswith("for", i):
            prev = text[i - 1] if i else ""
            after = text[i + 3] if i + 3 < n else ""

            if (
                not (prev.isalnum() or prev == "_")
                and not (after.isalnum() or after == "_")
            ):
                j = i + 3
                while j < n and text[j].isspace():
                    j += 1

                if j < n and text[j] == "(":
                    positions.append(i)
                    i += 3
                    continue

        i += 1

    return positions


def loop_header(text: str, pos: int) -> str:
    opening = text.find("(", pos)
    if opening < 0:
        raise RuntimeError("missing loop opening parenthesis")

    depth = 0
    quote = None
    escape = False

    for i in range(opening, len(text)):
        c = text[i]

        if quote is not None:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            continue

        if c in ("'", '"'):
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return " ".join(text[pos:i + 1].split())

    raise RuntimeError("unterminated loop header")


def preprocess(
    clang: str,
    source: Path,
    size_macro: str,
) -> str:
    cmd = [
        clang,
        "-std=c11",
        "-E",
        "-P",
        f"-D{size_macro}",
        "-DPOLYBENCH_USE_C99_PROTO",
        "-I", str(PB / "utilities"),
        "-I", str(source.parent),
        str(source),
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if p.returncode != 0:
        raise RuntimeError(
            f"preprocess failed: {source}\n"
            + p.stderr.decode(errors="replace")[:3000]
        )

    return p.stdout.decode("utf-8", errors="strict")


def main() -> None:
    if OUT.exists():
        raise RuntimeError(
            f"{OUT} already exists; refusing to overwrite frozen manifest"
        )

    clang = shutil.which("clang")
    if clang is None:
        raise RuntimeError("clang not found")

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if len(catalog) != 30:
        raise RuntimeError(
            f"expected 30 PolyBench kernels, got {len(catalog)}"
        )

    kernels = []
    grand_candidates = 0

    for row in catalog:
        kid = row["id"]
        source = PB / row["source"]

        if sha_file(source) != row["source_sha256"]:
            raise RuntimeError(f"{kid}: source digest mismatch")

        function_name = "kernel_" + kid.replace("-", "_")

        # Candidate IDs are defined ONLY from the original PolyBench
        # source text. Dataset-size macros may legitimately change the
        # preprocessed function text (e.g. local array extents in durbin).
        #
        # Therefore preprocessed byte identity across MINI..EXTRALARGE
        # is provenance only, not an admission requirement.
        original_text = source.read_text(encoding="utf-8")
        function = extract_function(original_text, function_name)
        positions = for_positions(function)

        if not positions:
            raise RuntimeError(f"{kid}: no loops found in original kernel")

        extracted_by_size = {}

        for size_macro in SIZES:
            pp = preprocess(clang, source, size_macro)
            fn = extract_function(pp, function_name)
            extracted_by_size[size_macro] = fn

        hashes = {
            k: sha_bytes(v.encode())
            for k, v in extracted_by_size.items()
        }

        preprocessed_loop_counts = {
            k: len(for_positions(v))
            for k, v in extracted_by_size.items()
        }

        if not positions:
            raise RuntimeError(f"{kid}: no loops found")

        loops = []

        for idx, pos in enumerate(positions):
            candidates = []

            for hint_name, values in HINTS.items():
                for value in values:
                    candidates.append(
                        {
                            "candidate_id":
                                f"loop_{idx:02d}_{hint_name}_{value}",
                            "hint": hint_name,
                            "value": value,
                        }
                    )

            loops.append(
                {
                    "loop_index": idx,
                    "line_in_preprocessed_kernel":
                        function.count("\n", 0, pos) + 1,
                    "header": loop_header(function, pos),
                    "candidates": candidates,
                }
            )

        candidate_count = (
            1
            + sum(
                len(loop["candidates"])
                for loop in loops
            )
        )

        grand_candidates += candidate_count

        kernels.append(
            {
                "kernel_id": kid,
                "source": row["source"],
                "source_sha256": row["source_sha256"],
                "function_name": function_name,
                "candidate_addressing":
                    "original_source_syntactic_loop_index",
                "original_kernel_sha256":
                    sha_bytes(function.encode()),
                "preprocessed_kernel_sha256_by_size":
                    hashes,
                "preprocessed_kernel_identical_across_all_five_sizes":
                    len(set(hashes.values())) == 1,
                "preprocessed_loop_count_by_size":
                    preprocessed_loop_counts,
                "syntactic_loop_count": len(loops),
                "candidate_count_including_identity":
                    candidate_count,
                "identity_candidate_id": "identity",
                "loops": loops,
            }
        )

        print(
            f"{kid:16s} "
            f"loops={len(loops):2d} "
            f"candidates={candidate_count:3d}"
        )

    manifest = {
        "schema": "cpucond-final-candidate-manifest-v1",
        "generation_role":
            "candidate-space-freeze-before-final-performance-timing",
        "polybench_release": "PolyBench/C 4.2.1-beta",
        "kernel_count": len(kernels),
        "dataset_sizes": list(SIZES),
        "candidate_policy":
            "identity_or_exactly_one_Clang_loop_hint_on_one_syntactic_loop",
        "hint_space": {
            k: list(v)
            for k, v in HINTS.items()
        },
        "candidate_ids_depend_on_performance_results": False,
        "candidate_ids_depend_on_target_CPU": False,
        "same_candidate_ids_required_on_all_hosts": True,
        "total_candidates_across_30_kernels":
            grand_candidates,
        "total_candidate_instance_pairs_for_five_sizes":
            grand_candidates * 5,
        "kernels": kernels,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)

    with OUT.open("x", encoding="utf-8") as f:
        json.dump(
            manifest,
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")

    print()
    print("FINAL_CANDIDATE_MANIFEST_FROZEN")
    print("kernel_count:", len(kernels))
    print(
        "total_candidates_across_30_kernels:",
        grand_candidates,
    )
    print(
        "total_candidate_instance_pairs_for_five_sizes:",
        grand_candidates * 5,
    )
    print(
        "manifest_sha256:",
        sha_file(OUT),
    )


if __name__ == "__main__":
    main()
