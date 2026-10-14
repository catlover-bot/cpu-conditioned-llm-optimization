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

CATALOG = json.loads(
    (INTAKE / "polybench-catalog.json")
    .read_text(encoding="utf-8")
)

MANIFEST = json.loads(
    (REPO / "configs/final-candidate-manifest-v1.json")
    .read_text(encoding="utf-8")
)

OUT = (
    REPO
    / "generated/llm-input-corpus-v1"
)

SIZES = (
    "MINI_DATASET",
    "SMALL_DATASET",
    "MEDIUM_DATASET",
)

SIZE_LABEL = {
    "MINI_DATASET": "MINI",
    "SMALL_DATASET": "SMALL",
    "MEDIUM_DATASET": "MEDIUM",
}


def sha_bytes(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def mask_noncode(text: str) -> str:
    out = list(text)
    i = 0
    state = "code"
    quote = None

    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""

        if state == "line":
            if c == "\n":
                state = "code"
            else:
                out[i] = " "
            i += 1
            continue

        if state == "block":
            out[i] = " "
            if c == "*" and n == "/":
                out[i + 1] = " "
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "literal":
            out[i] = " "

            if c == "\\":
                if i + 1 < len(text):
                    out[i + 1] = " "
                i += 2
                continue

            if c == quote:
                state = "code"
                quote = None

            i += 1
            continue

        if c == "/" and n == "/":
            out[i] = out[i + 1] = " "
            state = "line"
            i += 2
            continue

        if c == "/" and n == "*":
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


def matching_brace(masked: str, opening: int) -> int:
    depth = 0

    for i in range(opening, len(masked)):
        if masked[i] == "{":
            depth += 1

        elif masked[i] == "}":
            depth -= 1

            if depth == 0:
                return i + 1

    raise RuntimeError("unbalanced braces")


def function_span(
    text: str,
    name: str,
    return_type: str,
) -> tuple[int, int]:
    masked = mask_noncode(text)

    pattern = re.compile(
        r"\b(?:static\s+)?"
        + re.escape(return_type)
        + r"\s+"
        + re.escape(name)
        + r"\s*\("
    )

    found = []

    for m in pattern.finditer(masked):
        opening = masked.find("{", m.end())

        if opening < 0:
            continue

        if masked.find(";", m.end(), opening) >= 0:
            continue

        found.append(
            (
                m.start(),
                matching_brace(masked, opening),
            )
        )

    if len(found) != 1:
        raise RuntimeError(
            f"{name}: expected 1 definition, got {len(found)}"
        )

    return found[0]


def loop_positions(function_text: str) -> list[int]:
    masked = mask_noncode(function_text)

    return [
        m.start()
        for m in re.finditer(
            r"\bfor\s*\(",
            masked,
        )
    ]


def inject_loop_markers(
    source: str,
    kernel: str,
    expected_loops: int,
    mode: str,
) -> str:
    a, b = function_span(
        source,
        kernel,
        "void",
    )

    fn = source[a:b]
    positions = loop_positions(fn)

    if len(positions) != expected_loops:
        raise RuntimeError(
            f"{kernel}: loop count "
            f"{len(positions)} != {expected_loops}"
        )

    for i, pos in reversed(
        list(enumerate(positions))
    ):
        if mode == "c":
            marker = (
                f"/* CPUCOND_LOOP_{i:02d} */\n"
            )

        elif mode == "ir":
            marker = (
                "__asm__ __volatile__("
                f"\"# CPUCOND_LOOP_{i:02d}\""
                ");\n"
            )

        else:
            raise ValueError(mode)

        fn = (
            fn[:pos]
            + marker
            + fn[pos:]
        )

    return source[:a] + fn + source[b:]


def extract_kernel_c(
    source: str,
    kernel: str,
) -> str:
    a, b = function_span(
        source,
        kernel,
        "void",
    )

    return source[a:b].strip() + "\n"


def header_macro_names(
    header: Path,
) -> set[str]:
    if not header.exists():
        return set()

    names = set()

    for line in header.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines():
        m = re.match(
            r"\s*#\s*define\s+([A-Z][A-Z0-9_]*)\b",
            line,
        )

        if m:
            names.add(m.group(1))

    return names


def numeric_dimensions(
    clang: str,
    source: Path,
    size: str,
) -> dict[str, int]:
    header = source.with_suffix(".h")
    names = header_macro_names(header)

    p = subprocess.run(
        [
            clang,
            "-std=gnu11",
            "-E",
            "-dM",
            f"-D{size}",
            "-DPOLYBENCH_USE_C99_PROTO",
            "-I",
            str(PB / "utilities"),
            "-I",
            str(source.parent),
            str(source),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=True,
    )

    macros = {}

    for line in p.stdout.decode(
        encoding="utf-8",
        errors="strict",
    ).splitlines():
        m = re.match(
            r"#define\s+([A-Z][A-Z0-9_]*)\s+([0-9]+)$",
            line,
        )

        if not m:
            continue

        name = m.group(1)

        if name in names:
            macros[name] = int(m.group(2))

    return dict(
        sorted(macros.items())
    )


def extract_llvm_function(
    ir: str,
    kernel: str,
) -> str:
    lines = ir.splitlines()

    start = None

    for i, line in enumerate(lines):
        if (
            line.startswith("define ")
            and f"@{kernel}(" in line
        ):
            start = i
            break

    if start is None:
        raise RuntimeError(
            f"LLVM function not found: {kernel}"
        )

    depth = 0
    body = []
    seen_open = False

    for line in lines[start:]:
        body.append(line)

        depth += line.count("{")
        depth -= line.count("}")

        if "{" in line:
            seen_open = True

        if seen_open and depth == 0:
            break

    if not seen_open or depth != 0:
        raise RuntimeError(
            f"LLVM function malformed: {kernel}"
        )

    cleaned = []

    for line in body:
        marker = re.search(
            r"CPUCOND_LOOP_([0-9]{2})",
            line,
        )

        if marker:
            indent = (
                line[:len(line) - len(line.lstrip())]
            )

            cleaned.append(
                indent
                + "; CPUCOND_LOOP_"
                + marker.group(1)
            )

            continue

        # CPU固有属性グループ参照を除去。
        if line.startswith("define "):
            line = re.sub(
                r"\s+#\d+\s*\{",
                " {",
                line,
            )

        # 不要なLLVMメタデータ参照を除去。
        line = re.sub(
            r",?\s*!dbg\s+!\d+",
            "",
            line,
        )

        line = re.sub(
            r",?\s*!llvm\.loop\s+!\d+",
            "",
            line,
        )

        cleaned.append(line)

    result = "\n".join(cleaned).strip() + "\n"

    banned = (
        "target-cpu",
        "target-features",
        "tune-cpu",
        "haswell",
        "znver",
        "epyc",
    )

    lowered = result.lower()

    for token in banned:
        if token in lowered:
            raise RuntimeError(
                f"CPU information leaked into IR: {token}"
            )

    return result


def build_ir(
    clang: str,
    source_path: Path,
    source_text: str,
    kernel: str,
    size: str,
    work: Path,
) -> str:
    work.mkdir(
        parents=True,
        exist_ok=True,
    )

    marked = work / "marked.c"
    module = work / "module.ll"

    marked.write_text(
        source_text,
        encoding="utf-8",
    )

    cmd = [
        clang,
        "-std=gnu11",
        "-O0",
        "-Xclang",
        "-disable-O0-optnone",
        "-fno-discard-value-names",
        "-fno-fast-math",
        "-ffp-contract=off",
        "-S",
        "-emit-llvm",
        f"-D{size}",
        "-DPOLYBENCH_USE_C99_PROTO",
        "-I",
        str(PB / "utilities"),
        "-I",
        str(source_path.parent),
        str(marked),
        "-o",
        str(module),
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )

    if p.returncode != 0:
        raise RuntimeError(
            p.stderr.decode(
                errors="replace"
            )[:4000]
        )

    return extract_llvm_function(
        module.read_text(
            encoding="utf-8",
        ),
        kernel,
    )


def main() -> int:
    clang = shutil.which("clang")

    if clang is None:
        raise RuntimeError(
            "clang not found"
        )

    catalog = {
        x["id"]: x
        for x in CATALOG
    }

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []

    c_count = 0
    ir_count = 0

    for entry in MANIFEST["kernels"]:
        kid = entry["kernel_id"]

        cat = catalog[kid]

        source_path = PB / cat["source"]

        original = source_path.read_text(
            encoding="utf-8",
        )

        kernel = (
            "kernel_"
            + kid.replace("-", "_")
        )

        expected_loops = entry[
            "syntactic_loop_count"
        ]

        c_marked = inject_loop_markers(
            original,
            kernel,
            expected_loops,
            "c",
        )

        c_kernel = extract_kernel_c(
            c_marked,
            kernel,
        )

        assert (
            c_kernel.count(
                "CPUCOND_LOOP_"
            )
            == expected_loops
        )

        for size in SIZES:
            label = SIZE_LABEL[size]

            dimensions = numeric_dimensions(
                clang,
                source_path,
                size,
            )

            c_dir = (
                OUT / "c" / kid
            )

            ir_dir = (
                OUT / "ir" / kid
            )

            work = (
                OUT
                / "_work"
                / kid
                / label
            )

            c_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            ir_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            c_path = (
                c_dir
                / f"{label}.txt"
            )

            c_document = (
                f"カーネル: {kid}\n"
                f"サイズ条件: {label}\n"
                "数値寸法: "
                + json.dumps(
                    dimensions,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n\n"
                + c_kernel
            )

            c_path.write_text(
                c_document,
                encoding="utf-8",
            )

            ir_source = inject_loop_markers(
                original,
                kernel,
                expected_loops,
                "ir",
            )

            ir_kernel = build_ir(
                clang,
                source_path,
                ir_source,
                kernel,
                size,
                work,
            )

            if (
                ir_kernel.count(
                    "CPUCOND_LOOP_"
                )
                != expected_loops
            ):
                raise RuntimeError(
                    f"{kid}/{label}: "
                    "IR loop marker mismatch"
                )

            ir_path = (
                ir_dir
                / f"{label}.txt"
            )

            ir_document = (
                f"カーネル: {kid}\n"
                f"サイズ条件: {label}\n"
                "数値寸法: "
                + json.dumps(
                    dimensions,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n\n"
                + ir_kernel
            )

            ir_path.write_text(
                ir_document,
                encoding="utf-8",
            )

            rows.append({
                "kernel": kid,
                "size": label,
                "loop_count":
                    expected_loops,
                "dimensions":
                    dimensions,
                "c_path":
                    str(
                        c_path.relative_to(REPO)
                    ),
                "ir_path":
                    str(
                        ir_path.relative_to(REPO)
                    ),
                "c_sha256":
                    sha_bytes(
                        c_document.encode()
                    ),
                "ir_sha256":
                    sha_bytes(
                        ir_document.encode()
                    ),
            })

            c_count += 1
            ir_count += 1

            print(
                f"{kid:16s} "
                f"{label:6s} "
                f"loops={expected_loops:2d} "
                "C=OK IR=OK"
            )

    assert len(rows) == 90
    assert c_count == 90
    assert ir_count == 90

    manifest = {
        "corpus_id":
            "llm-input-corpus-v1",

        "representation_conditions":
            ["C", "LLVM_IR"],

        "instances": 90,

        "c_documents": 90,

        "ir_documents": 90,

        "cpu_specific_information_in_documents":
            False,

        "llvm_generation": {
            "compiler":
                subprocess.check_output(
                    [clang, "--version"],
                    text=True,
                ).splitlines()[0],

            "optimization_level":
                "O0",

            "discard_value_names":
                False,

            "cpu_specific_attributes_removed":
                True,

            "loop_labels_preserved":
                True,
        },

        "rows": rows,
    }

    (
        OUT / "manifest.json"
    ).write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    # 一時生成物は最終コーパスから除外。
    shutil.rmtree(
        OUT / "_work"
    )

    print()
    print(
        "LLM_INPUT_CORPUS_COMPLETE"
    )
    print("instances = 90")
    print("C documents = 90")
    print("IR documents = 90")
    print("total = 180")
    print("out =", OUT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
