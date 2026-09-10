#!/usr/bin/env python3
"""Pin official benchmark inputs; do NOT evaluate optimization candidates.

Python 3.10+, standard library only. Default: verify the completed local
semantics-audit receipts, fetch immutable/release sources into a cache, inventory
PolyBench/C and TSVC2, and compile (but NEVER execute) six unmodified PolyBench
translation units. Existing cpucond modules and runs are not edited.

The first PolyBench digest is OBSERVED from the downloaded release, not a claimed
publisher signature. Supply --polybench-sha256 to independently require a digest.
TSVC2 files are checked against Git blob IDs read from the pinned upstream tree.

--self-test runs only local tests, including a tiny synthetic Clang build.
--check RUN checks this tool's saved intake artifacts without network/builds.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import urllib.request
import urllib.parse
import uuid
from datetime import datetime, timezone

REVISION = "dataset-intake-v1"
AUDIT_REL = "runs/goal004-semantics-audit/20260910T125416.576724Z-04c3e93f"
TSVC_COMMIT = "badf9adb2974867ac0937718d85a44dec6dec95a"
TSVC_TREE = "a009ccf980a04e17c07aaf388983935d40cde038"
TSVC_BLOBS = {
    ".gitignore": "6acd24d07c0b836e8ae6d96ed1448d099c942dd6",
    "Makefile": "b37dec1df86f24bfb588ad145a203f7e970cfbd7",
    "README.md": "667a367b3034a091a255b239f8467582fbfe7966",
    "license.txt": "782154d4adf742bb8bbf0c199ec9c3ff7723d4b8",
    "makefiles/Makefile.GNU": "d416d4db921d5c0b467b5c915914e50d27776f10",
    "makefiles/Makefile.PGI": "7e1ecac504d94a53de567fe096b0a1c5e720af85",
    "makefiles/Makefile.clang": "cefe725531c25980ebe44bd3e0dbc0640c517dda",
    "makefiles/Makefile.cray": "3212f36a868123680e6ad28f929548772c0f2de4",
    "makefiles/Makefile.defs": "76f6b5929508afab783ae221e6e261f028da70fa",
    "makefiles/Makefile.intel": "3a46fbf87765f041c0fdb5bbc5cd2f767fce5675",
    "src/Makefile": "9a9fc37ffa433f183f48e658738f0cc4ed8b45b8",
    "src/array_defs.h": "5b754cea451ca0878cbcff20275733e08248f00b",
    "src/common.c": "4fafab5e01dae3de720501f59c4ab5a97f567d88",
    "src/common.h": "f862ffd625bce719e151906179e9dda108070962",
    "src/dummy.c": "0dd9207830f2e9478de6c1e4649f642901b3a3ac",
    "src/tsvc.c": "48d7ef33485c696fd45c5fad5d456aee58addca1",
}
PB_IDS = set("2mm 3mm adi atax bicg cholesky correlation covariance deriche doitgen durbin fdtd-2d gemm gemver gesummv gramschmidt heat-3d jacobi-1d jacobi-2d lu ludcmp mvt nussinov seidel-2d symm syr2k syrk trisolv trmm floyd-warshall".split())
PILOT_IDS = ("gemm", "atax", "jacobi-2d", "trisolv", "nussinov", "correlation")
PB_URL = "https://downloads.sourceforge.net/project/polybench/polybench-c-4.2.1-beta.tar.gz"
TSVC_URL = f"https://codeload.github.com/UoB-HPC/TSVC_2/tar.gz/{TSVC_COMMIT}"
MAX_ARCHIVE_BYTES = 30 * 1024 * 1024
MAX_TREE_BYTES = 150 * 1024 * 1024
FLAGS = ["-std=gnu11", "-O3", "-fno-fast-math", "-ffp-contract=off", "-DMINI_DATASET", "-DPOLYBENCH_DUMP_ARRAYS"]


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def relative_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("invalid_relative_path")
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or str(p) == ".":
        raise ValueError("unsafe_relative_path")
    return str(p)


def safe_file(root: Path, name: str) -> Path:
    rel = relative_name(name)
    p = root / rel
    if any(parent.is_symlink() for parent in [p, *p.parents] if parent != root.parent):
        raise ValueError("symlink_not_allowed")
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("path_outside_root")
    return p


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise RuntimeError(f"symlink_in_tree: {p}")
        if p.is_file():
            result[str(p.relative_to(root))] = digest(p)
    return result


def verify_manifest(root: Path, manifest: dict, manifest_name: str = "artifacts.json") -> int:
    if not isinstance(manifest, dict) or not manifest:
        raise RuntimeError("empty_or_invalid_manifest")
    found = set(inventory(root)) - {manifest_name}
    if found != set(manifest):
        raise RuntimeError("artifact_file_set_changed")
    for name, expected in manifest.items():
        p = safe_file(root, name)
        if not re.fullmatch(r"[0-9a-f]{64}", str(expected)) or digest(p) != expected:
            raise RuntimeError(f"artifact_changed: {name}")
    return len(manifest)


def check_run(root: Path) -> int:
    return verify_manifest(root, json.loads((root / "artifacts.json").read_text(encoding="utf-8")))


def audit_receipt(root: Path, repo: Path) -> dict:
    count = check_run(root)
    summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
    if summary.get("completion") != "SEMANTICS_AUDIT_COMPLETE" or summary.get("passed") is not True:
        raise RuntimeError("preceding_semantics_audit_not_passed")
    if summary.get("case_count") != 120 or summary.get("build_profiles") != ["generic", "native", "sanitized"]:
        raise RuntimeError("unexpected_semantics_audit_scope")
    package = json.loads((root / "audit_tool/package-manifest.json").read_text(encoding="utf-8"))
    hashes = package["expected_local_sources"]
    for name, expected in hashes.items():
        if digest(safe_file(repo, name)) != expected:
            raise RuntimeError(f"source_changed_since_semantics_audit: {name}")
    return {
        "run": str(root), "summary_sha256": digest(root / "summary.json"),
        "artifacts_manifest_sha256": digest(root / "artifacts.json"), "artifacts_checked": count,
        "source_sha256": hashes, "source_files_match": True,
        "accepted_for": "dataset_intake_prerequisite_only",
        "equivalence_proven": False, "main_evaluation_gate_integrated": False,
    }


def git_read(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError("git_read_failed: " + p.stderr.decode(errors="replace")[:1000])
    return p.stdout.decode("utf-8", errors="strict")


def tracked_snapshot(repo: Path) -> dict[str, str]:
    return {name: digest(safe_file(repo, name)) for name in git_read(repo, "ls-files", "-z").split("\x00") if name}


class HTTPSOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme != "https":
            raise RuntimeError("non_https_redirect_refused")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_archive(url: str, target: Path, expected: str | None = None) -> dict:
    record_path = target.with_suffix(target.suffix + ".receipt.json")
    if target.exists():
        if not record_path.is_file():
            raise RuntimeError(f"cache_without_receipt: {target}; original file retained")
        receipt = json.loads(record_path.read_text(encoding="utf-8"))
        observed = digest(target)
        if receipt.get("requested_url") != url or observed != receipt.get("sha256") or (expected and observed != expected):
            raise RuntimeError("cached_archive_digest_or_origin_mismatch")
        return {**receipt, "cache_reused": True}
    if record_path.exists():
        raise RuntimeError("receipt_without_cache; no overwrite attempted")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / (target.name + ".partial-" + uuid.uuid4().hex[:8])
    opener = urllib.request.build_opener(HTTPSOnly())
    req = urllib.request.Request(url, headers={"User-Agent": "cpucond-research-intake/1"})
    with opener.open(req, timeout=60) as response, tmp.open("xb") as f:
        total = 0
        while True:
            data = response.read(1024 * 1024)
            if not data:
                break
            total += len(data)
            if total > MAX_ARCHIVE_BYTES:
                raise RuntimeError("download_size_limit")
            f.write(data)
        final_url = response.geturl()
    if total == 0 or tmp.read_bytes()[:2] != b"\x1f\x8b":
        raise RuntimeError(f"not_a_gzip_archive: {tmp}; error/HTML download retained")
    observed = digest(tmp)
    if expected and observed != expected:
        raise RuntimeError(f"download_digest_mismatch: {tmp}")
    receipt = {"requested_url": url, "final_url": final_url, "bytes": total,
               "sha256": observed, "downloaded_utc": datetime.now(timezone.utc).isoformat(),
               "publisher_signature_verified": False,
               "digest_basis": "caller_supplied" if expected else "first_observation_over_https"}
    # Same-process lock protects our cache; never overwrite another valid acquisition.
    if target.exists() or record_path.exists():
        raise RuntimeError("cache_was_created_concurrently")
    tmp.rename(target)
    write_json(record_path, receipt)
    return {**receipt, "cache_reused": False}


def extract_archive(archive: Path, destination: Path, expected_top: str) -> None:
    if destination.exists():
        raise RuntimeError("extraction_destination_already_exists")
    planned = []
    names = set()
    total = 0
    with tarfile.open(archive, "r:gz") as t:
        for item in t:
            if len(planned) > 20000:
                raise RuntimeError("archive_member_limit")
            full = PurePosixPath(relative_name(item.name))
            if full.parts[0] != expected_top:
                raise RuntimeError("unexpected_archive_root")
            if item.isdir():
                continue
            if not item.isfile() or item.islnk() or item.issym():
                raise RuntimeError("archive_links_and_special_files_refused")
            rel = relative_name(str(PurePosixPath(*full.parts[1:])))
            if rel in names:
                raise RuntimeError("duplicate_archive_member")
            names.add(rel)
            total += item.size
            if item.size < 0 or total > MAX_TREE_BYTES:
                raise RuntimeError("extracted_size_limit")
            planned.append((item, rel))
        destination.mkdir(parents=True)
        for item, rel in planned:
            stream = t.extractfile(item)
            if stream is None:
                raise RuntimeError("missing_archive_member_body")
            p = safe_file(destination, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("xb") as f:
                shutil.copyfileobj(stream, f)
            if p.stat().st_size != item.size:
                raise RuntimeError("archive_member_size_mismatch")
    if not planned:
        raise RuntimeError("empty_archive")


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def check_tsvc(root: Path, expected: dict = TSVC_BLOBS) -> None:
    found = inventory(root)
    if set(found) != set(expected):
        raise RuntimeError("TSVC_pinned_file_set_mismatch")
    for name, blob in expected.items():
        if git_blob_id(safe_file(root, name).read_bytes()) != blob:
            raise RuntimeError(f"TSVC_blob_mismatch: {name}")


def polybench_catalog(root: Path, required: set[str] = PB_IDS) -> list[dict]:
    readme = (root / "README").read_text(encoding="utf-8")
    if "4.2.1" not in readme or "beta" not in readme.lower():
        raise RuntimeError("unexpected_PolyBench_release")
    if not (root / "LICENSE.txt").is_file():
        raise RuntimeError("PolyBench_license_missing")
    rows = []
    for line in (root / "utilities/benchmark_list").read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if not name or name.startswith("#"):
            continue
        p = safe_file(root, name)
        if not p.is_file() or p.suffix != ".c" or not p.with_suffix(".h").is_file():
            raise RuntimeError(f"invalid_PolyBench_source_entry: {name}")
        rows.append({"id": p.stem, "source": str(p.relative_to(root)), "source_sha256": digest(p),
                     "header": str(p.with_suffix(".h").relative_to(root)), "header_sha256": digest(p.with_suffix(".h")),
                     "pilot_compile_selection": p.stem in PILOT_IDS,
                     "correctness_status": "contract_and_adapter_pending", "optimization_admitted": False})
    if len({r["id"] for r in rows}) != len(rows) or {r["id"] for r in rows} != required:
        raise RuntimeError("PolyBench_kernel_set_mismatch")
    return rows


def tsvc_catalog(root: Path) -> list[dict]:
    text = (root / "src/tsvc.c").read_text(encoding="utf-8")
    # Lexical navigation index only. Never use regex output as a semantic certificate.
    pat = r"(?m)^real_t\s+([A-Za-z_]\w*)\s*\(\s*struct\s+args_t\s*\*\s*\w+\s*\)\s*\{"
    rows = [{"id": m.group(1), "line": text.count("\n", 0, m.start()) + 1,
             "source": "src/tsvc.c", "index_method": "lexical_declaration_index_not_AST",
             "correctness_status": "per_loop_contract_and_full_output_adapter_pending",
             "optimization_admitted": False} for m in re.finditer(pat, text)]
    if not rows or len({r['id'] for r in rows}) != len(rows):
        raise RuntimeError("TSVC_index_missing_or_duplicate")
    return rows


def run_cmd(args: list[str], cwd: Path, evidence: Path, timeout: int = 120) -> dict:
    evidence.mkdir(parents=True, exist_ok=False)
    start = time.monotonic_ns()
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout,
                           env={**os.environ, "LC_ALL": "C"})
        code, out, err = p.returncode, p.stdout, p.stderr
        state = "ok" if code == 0 else "process_failed"
    except subprocess.TimeoutExpired as e:
        code, out, err, state = None, e.stdout or b"", e.stderr or b"", "timeout"
    (evidence / "stdout.raw").write_bytes(out)
    (evidence / "stderr.raw").write_bytes(err)
    rec = {"args": args, "returncode": code, "state": state,
           "process_duration_ns": time.monotonic_ns() - start,
           "duration_is_kernel_benchmark": False}
    write_json(evidence / "command.json", rec)
    return rec


def compile_polybench(root: Path, rows: list[dict], compiler: str, out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=False)
    util = root / "utilities"
    common = [compiler, *FLAGS, "-I", str(util)]
    util_record = run_cmd([*common, "-c", str(util / "polybench.c"), "-o", str(out / "polybench.o")], out, out / "utility-command")
    if util_record["state"] != "ok":
        raise RuntimeError(f"utility_compile_failed: {out / 'utility-command/stderr.raw'}")
    by_id = {r["id"]: r for r in rows}
    result = []
    for kernel_id in PILOT_IDS:
        src = root / by_id[kernel_id]["source"]
        d = out / kernel_id
        d.mkdir()
        base = [*common, "-I", str(src.parent)]
        commands = [
            [*base, "-c", str(src), "-o", str(d / "kernel.o")],
            [compiler, *FLAGS, str(d / "kernel.o"), str(out / "polybench.o"), "-lm", "-o", str(d / "program")],
            [*base, "-S", "-emit-llvm", str(src), "-o", str(d / "translation-unit.ll")],
            [*base, "-S", str(src), "-o", str(d / "translation-unit.s")],
            [*base, "-E", "-dM", str(src)],
        ]
        records = []
        for n, cmd in enumerate(commands):
            rec = run_cmd(cmd, d, d / f"command-{n:02d}")
            records.append(rec)
            if rec["state"] != "ok":
                break
        passed = len(records) == len(commands) and all(r["state"] == "ok" for r in records)
        macros = d / "command-04/stdout.raw"
        type_info = None
        if macros.is_file():
            text = macros.read_text(encoding="utf-8", errors="strict")
            m = re.search(r"(?m)^#define DATA_TYPE (.+)$", text)
            type_info = m.group(1) if m else None
        row = {"kernel_id": kernel_id, "compile_passed": passed, "executed": False,
               "observed_DATA_TYPE_macro": type_info, "commands": records,
               "source_sha256": digest(src), "correctness_proven": False,
               "IR_Assembly_role": "derived_whole_translation_unit_not_input_optimization",
               "artifact_directory": str(d)}
        result.append(row)
        print(f"PolyBench/{kernel_id}: compile={passed}, DATA_TYPE={type_info}, executed=False", flush=True)
    return result


def report_text(summary: dict, pb: list[dict], tv: list[dict], builds: list[dict]) -> str:
    lines = ["# データセット原本の固定とビルド準備", "", f"状態: {summary['completion']}",
             "このrunは原本取得・課題索引・コンパイル確認のみ。候補の正しさ／速度／CPU情報の効果は未評価。",
             "既存の検証器・採点経路へストレス入力を組み込む変更は行っていない。", "",
             f"PolyBench/C: 4.2.1-beta、{len(pb)}課題を索引化。",
             f"TSVC2: {TSVC_COMMIT}、{len(tv)}個の宣言を字句的に索引化（適格課題数ではない）。",
             "TSVC2のchecksumは全出力のビット比較の代わりにしない。", "",
             "| 課題 | コンパイル | 元のDATA_TYPE | 実行・候補採用 |", "|---|---|---|---|"]
    for b in builds:
        lines.append(f"| {b['kernel_id']} | {b['compile_passed']} | {b['observed_DATA_TYPE_macro']} | 未実施 |")
    lines += ["", "## 原本の来歴", json.dumps(summary['datasets'], ensure_ascii=False, indent=2),
              "", "## 次に必要な課題別契約", "入力領域、出力配列の全要素、型、算術順序、境界条件、別名参照を確定する。",
              "PolyBenchの表示用dumpを丸めたまま厳密な同値性検証に使用しない。",
              "GEMMスモークに対する監査結果をPolyBenchやTSVCの正しさ証拠に流用しない。",
              "手書き変換もLLM提案も同じ採用条件を満たすまで本評価には入れない。",
              "CPU情報P0/P1/P2、コンパイラ、生成予算は別々に固定する。",
              "", "## 実行状態", json.dumps(summary, ensure_ascii=False, indent=2)]
    return "\n".join(lines) + "\n"


@contextlib.contextmanager
def shared_lock():
    p = Path(tempfile.gettempdir()) / f"cpucond-execution-{os.getuid()}.lock"
    with p.open("a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def execute(args) -> int:
    repo = args.repo.resolve()
    if not (repo / "src/cpucond").is_dir():
        raise RuntimeError("wrong_repository")
    compiler = shutil.which("clang")
    if not compiler:
        raise RuntimeError("clang_missing; no install attempted")
    compiler = str(Path(compiler).resolve())
    audit = (args.audit or repo / AUDIT_REL).resolve()
    receipt = audit_receipt(audit, repo)
    print(f"Existing semantics receipt: {receipt['artifacts_checked']} artifact hashes checked; no kernels rerun", flush=True)
    before = tracked_snapshot(repo)
    head_before = git_read(repo, "rev-parse", "HEAD").strip()
    rid = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid.uuid4().hex[:8]
    out = repo / "runs/goal0041-dataset-intake" / rid
    out.mkdir(parents=True, exist_ok=False)
    print(f"Run: {out}", flush=True)
    write_json(out / "audit-receipt.json", receipt)
    shutil.copyfile(Path(__file__).resolve(), out / "dataset-intake-tool.py")
    write_json(out / "provenance.json", {"revision": REVISION, "git_head": head_before,
             "tracked_file_sha256": before, "git_status": git_read(repo, "status", "--short", "--branch"),
             "compiler": compiler, "compiler_sha256": digest(Path(compiler)), "flags": FLAGS,
             "target": "compiler_default_no_explicit_march_or_mtune", "benchmark_input_executed": False})
    try:
        v = run_cmd([compiler, "--version"], out, out / "compiler-version")
        if v['state'] != 'ok':
            raise RuntimeError('compiler_version_failed')
        cache = Path.home() / ".cache/cpucond-datasets-intake-v1"
        print("Fetch/verify fixed PolyBench release and pinned TSVC2 sources (no upstream build scripts)", flush=True)
        pb_archive = cache / "polybench-c-4.2.1-beta.tar.gz"
        tsvc_archive = cache / f"TSVC_2-{TSVC_COMMIT}.tar.gz"
        pb_download = fetch_archive(PB_URL, pb_archive, args.polybench_sha256)
        tv_download = fetch_archive(TSVC_URL, tsvc_archive)
        src = out / "upstream"
        src.mkdir()
        pb_root, tv_root = src / "polybench-c-4.2.1-beta", src / "TSVC_2"
        extract_archive(pb_archive, pb_root, "polybench-c-4.2.1-beta")
        extract_archive(tsvc_archive, tv_root, "TSVC_2-" + TSVC_COMMIT)
        check_tsvc(tv_root)
        pb, tv = polybench_catalog(pb_root), tsvc_catalog(tv_root)
        upstream_before = inventory(src)
        datasets = {"polybench": {"release": "4.2.1-beta", "acquisition": pb_download, "license_file": "LICENSE.txt", "task_count": len(pb)},
                    "tsvc2": {"repository": "UoB-HPC/TSVC_2", "commit": TSVC_COMMIT, "tree": TSVC_TREE,
                              "acquisition": tv_download, "verified_git_blobs": len(TSVC_BLOBS), "license_file": "license.txt"}}
        write_json(out / "dataset-lock.json", {"revision": REVISION, "datasets": datasets, "upstream_file_sha256": upstream_before})
        write_json(out / "polybench-catalog.json", pb)
        write_json(out / "tsvc-declaration-index.json", tv)
        write_json(out / "admission-contracts-pending.json", {
            "status": "NOT_ADMITTED_FOR_OPTIMIZATION", "all_candidates_require_result_preservation": True,
            "inherited_smoke_equivalence": False, "datasets": datasets,
            "requirements": ["per-kernel valid input domain", "all observable outputs and numeric types",
                             "aliasing and size preconditions", "strict FP policy and exception scope",
                             "exact-output adapter and negative controls", "legal transformation preconditions",
                             "reference compiler/toolchain trust boundary", "independent final measurement policy"],
            "no_automatic_relaxation_of_tolerance": True,
        })
        builds = compile_polybench(pb_root, pb, compiler, out / "build")
        write_json(out / "build-results.json", builds)
        unchanged = before == tracked_snapshot(repo) and head_before == git_read(repo, "rev-parse", "HEAD").strip()
        if not unchanged or inventory(src) != upstream_before:
            raise RuntimeError("sources_changed_during_intake")
        passed = all(b["compile_passed"] for b in builds)
        summary = {"completion": "DATASET_INTAKE_COMPLETE" if passed else "DATASET_INTAKE_PARTIAL", "passed": passed,
                   "run_directory": str(out), "datasets": datasets,
                   "polybench_catalog_count": len(pb), "tsvc_declaration_index_count": len(tv),
                   "polybench_compiled": sum(b['compile_passed'] for b in builds),
                   "source_files_unchanged": True, "upstream_sources_unchanged": True,
                   "llm_requests": 0, "benchmark_executions": 0, "performance_measurements": 0,
                   "equivalence_proven": False, "main_benchmark_admissible": False,
                   "main_evaluation_gate_integrated": False, "publishable_benchmark": False,
                   "environment_role": "dataset_intake_and_compile_only"}
        write_json(out / "summary.json", summary)
        text = report_text(summary, pb, tv, builds)
        (out / "report.md").write_text(text, encoding="utf-8")
        write_json(out / "artifacts.json", inventory(out))
        checked = check_run(out)
        downloads = Path("/mnt/c/Users/m.hirotaka/Downloads")
        if downloads.is_dir():
            share = downloads / f"cpucond-dataset-intake-{rid}.txt"
            with share.open("x", encoding="utf-8") as f:
                f.write(text)
            print(f"Shareable report: {share}", flush=True)
        print(summary["completion"])
        print(json.dumps({k: v for k, v in summary.items() if k != "datasets"}, indent=2, ensure_ascii=False))
        print(f"Artifacts checked: {checked}")
        return 0 if passed else 2
    except Exception as e:
        write_json(out / "failure.json", {"type": type(e).__name__, "message": str(e), "completion": "DATASET_INTAKE_FAILED"})
        if not (out / "artifacts.json").exists():
            write_json(out / "artifacts.json", inventory(out))
        print(f"DATASET_INTAKE_FAILED; evidence preserved: {out}", file=sys.stderr)
        raise


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def archive(self, members):
        p = self.root / 'test.tar.gz'
        with tarfile.open(p, 'w:gz') as t:
            for name, data, kind in members:
                i = tarfile.TarInfo(name)
                i.type = kind
                i.size = len(data) if kind == tarfile.REGTYPE else 0
                t.addfile(i, io.BytesIO(data) if i.isfile() else None)
        return p
    def test_safe_relative(self):
        self.assertEqual(relative_name('./a/b.c'), 'a/b.c')
    def test_traversal_refused(self):
        for s in ['../a', '/a', 'a/../../b', 'a\\b', '.']:
            with self.assertRaises(ValueError): relative_name(s)
    def test_symlink_refused(self):
        (self.root/'a').symlink_to('/tmp')
        with self.assertRaises(ValueError): safe_file(self.root,'a/file')
    def test_extract_normal(self):
        p=self.archive([('top/a.c',b'int x;',tarfile.REGTYPE)])
        extract_archive(p,self.root/'out','top')
        self.assertEqual((self.root/'out/a.c').read_bytes(),b'int x;')
    def test_extract_traversal(self):
        p=self.archive([('top/../outside',b'x',tarfile.REGTYPE)])
        with self.assertRaises(ValueError): extract_archive(p,self.root/'out','top')
        self.assertFalse((self.root/'outside').exists())
    def test_extract_duplicate(self):
        p=self.archive([('top/a',b'x',tarfile.REGTYPE),('top/a',b'y',tarfile.REGTYPE)])
        with self.assertRaises(RuntimeError): extract_archive(p,self.root/'out','top')
    def test_extract_link(self):
        p=self.archive([('top/a',b'',tarfile.SYMTYPE)])
        with self.assertRaises(RuntimeError): extract_archive(p,self.root/'out','top')
    def test_extract_wrong_root(self):
        p=self.archive([('other/a',b'x',tarfile.REGTYPE)])
        with self.assertRaises(RuntimeError): extract_archive(p,self.root/'out','top')
    def test_extract_no_overwrite(self):
        p=self.archive([('top/a',b'x',tarfile.REGTYPE)])
        (self.root/'out').mkdir()
        with self.assertRaises(RuntimeError): extract_archive(p,self.root/'out','top')
    def test_json_no_overwrite(self):
        p=self.root/'x.json'; write_json(p,{'x':1})
        with self.assertRaises(FileExistsError): write_json(p,{'x':2})
    def test_manifest_ok(self):
        (self.root/'x').write_bytes(b'abc')
        write_json(self.root/'artifacts.json',inventory(self.root))
        self.assertEqual(check_run(self.root),1)
    def test_manifest_changed(self):
        (self.root/'x').write_bytes(b'abc')
        write_json(self.root/'artifacts.json',inventory(self.root))
        (self.root/'x').write_bytes(b'abd')
        with self.assertRaises(RuntimeError): check_run(self.root)
    def test_manifest_added(self):
        (self.root/'x').write_bytes(b'abc')
        write_json(self.root/'artifacts.json',inventory(self.root))
        (self.root/'extra').write_text('x')
        with self.assertRaises(RuntimeError): check_run(self.root)
    def test_git_blob(self):
        self.assertEqual(git_blob_id(b'hello\n'),'ce013625030ba8dba906f756967f9e9ca394464a')
    def test_blob_verification(self):
        (self.root/'x').write_bytes(b'hello\n')
        check_tsvc(self.root,{'x':git_blob_id(b'hello\n')})
        (self.root/'x').write_bytes(b'changed')
        with self.assertRaises(RuntimeError): check_tsvc(self.root,{'x':git_blob_id(b'hello\n')})
    def test_bad_cache_not_refetched(self):
        p=self.root/'x.tgz';p.write_bytes(b'x')
        with self.assertRaises(RuntimeError): fetch_archive('https://unused.invalid/x',p)
    def test_cached_digest(self):
        p=self.root/'x.tgz';p.write_bytes(b'x')
        write_json(p.with_suffix('.tgz.receipt.json'),{'requested_url':'https://unused.invalid/x','sha256':digest(p)})
        self.assertTrue(fetch_archive('https://unused.invalid/x',p)['cache_reused'])
        with self.assertRaises(RuntimeError): fetch_archive('https://unused.invalid/x',p,'0'*64)
    def make_pb_fixture(self):
        (self.root/'utilities').mkdir()
        (self.root/'README').write_text('PolyBench/C 4.2.1 (beta) - SYNTHETIC TEST ONLY')
        (self.root/'LICENSE.txt').write_text('SYNTHETIC TEST DATA')
        entries=[]
        for name in sorted(PB_IDS):
            directory=self.root/'test-kernels'/name
            directory.mkdir(parents=True)
            (directory/(name+'.c')).write_text('int main(void){return 0;}\n')
            (directory/(name+'.h')).write_text('/* SYNTHETIC TEST */\n')
            entries.append('test-kernels/'+name+'/'+name+'.c')
        (self.root/'utilities/benchmark_list').write_text('\n'.join(entries)+'\n')
    def test_polybench_catalog(self):
        self.make_pb_fixture()
        rows=polybench_catalog(self.root)
        self.assertEqual(len(rows),30)
        self.assertEqual(sum(r['pilot_compile_selection'] for r in rows),6)
        self.assertTrue(all(not r['optimization_admitted'] for r in rows))
    def test_polybench_release_mismatch(self):
        self.make_pb_fixture()
        (self.root/'README').write_text('PolyBench/C 3.2')
        with self.assertRaises(RuntimeError): polybench_catalog(self.root)
    def test_polybench_missing_header(self):
        self.make_pb_fixture()
        (self.root/'test-kernels/gemm/gemm.h').unlink()
        with self.assertRaises(RuntimeError): polybench_catalog(self.root)
    def test_polybench_duplicate_entry(self):
        self.make_pb_fixture()
        with (self.root/'utilities/benchmark_list').open('a') as f:
            f.write('test-kernels/gemm/gemm.c\n')
        with self.assertRaises(RuntimeError): polybench_catalog(self.root)
    def test_TSV_index(self):
        (self.root/'src').mkdir()
        (self.root/'src/tsvc.c').write_text('real_t s000(struct args_t * func_args)\n{ return 0; }\n')
        rows=tsvc_catalog(self.root)
        self.assertEqual(rows[0]['id'],'s000');self.assertFalse(rows[0]['optimization_admitted'])
    def test_command_failure_is_not_pass(self):
        r=run_cmd([sys.executable,'-c','raise SystemExit(3)'],self.root,self.root/'cmd')
        self.assertEqual(r['state'],'process_failed')
    def test_real_compiler_fixture_compile_only(self):
        cc=shutil.which('clang')
        if not cc: self.skipTest('Clang unavailable: compiler fixture not tested')
        src=self.root/'fixture.c';src.write_text('int main(void){return 0;}\n')
        r=run_cmd([cc,*FLAGS,str(src),'-o',str(self.root/'program')],self.root,self.root/'compile')
        self.assertEqual(r['state'],'ok')
        self.assertTrue((self.root/'program').is_file())


def self_test() -> bool:
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IntakeTests)
    return unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--audit',type=Path)
    ap.add_argument('--polybench-sha256',help='Optional independently known PolyBench archive SHA-256')
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--check',type=Path)
    args=ap.parse_args()
    if args.self_test: return 0 if self_test() else 1
    if args.check:
        print('DATASET_ARTIFACT_CHECK_OK',check_run(args.check.resolve()));return 0
    if args.polybench_sha256 and not re.fullmatch('[0-9a-f]{64}',args.polybench_sha256):
        ap.error('--polybench-sha256 must be 64 lowercase hex characters')
    if not self_test(): return 1
    os.umask(0o077)
    try:
        with shared_lock(): return execute(args)
    except Exception as e:
        print(type(e).__name__+': '+str(e),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
