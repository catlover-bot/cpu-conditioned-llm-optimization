#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path.cwd()

CORPUS = REPO / "generated/llm-input-corpus-v1"

CORPUS_MANIFEST = json.loads(
    (CORPUS / "manifest.json").read_text(
        encoding="utf-8"
    )
)

CANDIDATE_MANIFEST = json.loads(
    (
        REPO
        / "configs/final-candidate-manifest-v1.json"
    ).read_text(encoding="utf-8")
)

CONTRACT = json.loads(
    (
        REPO
        / "configs/final-llm-prompt-contract-v1.json"
    ).read_text(encoding="utf-8")
)

OUT = REPO / "generated/final-llm-prompts-v1"

REPRESENTATIONS = {
    "C": "c",
    "LLVM_IR": "ir",
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def load_json(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def hardware_text(
    condition: str,
    profile: dict,
) -> str:
    if condition == "P0":
        return (
            "対象CPUに固有の情報は与えられていません。"
        )

    if condition == "P1":
        return (
            "対象CPU情報:\n"
            f"- 製品名: {profile['product_name']}\n"
            f"- マイクロアーキテクチャ: "
            f"{profile['microarchitecture']}"
        )

    if condition != "P2":
        raise ValueError(condition)

    d = profile["static_details"]

    isa = ", ".join(d["isa"])

    return f"""対象CPU情報:
- 製品名: {profile["product_name"]}
- マイクロアーキテクチャ: {profile["microarchitecture"]}
- ベース周波数: {d["base_frequency_ghz"]} GHz
- 物理コア数: {d["physical_cores"]}
- ハードウェアスレッド数: {d["hardware_threads"]}
- 1コアあたりスレッド数: {d["threads_per_core"]}
- ソケット数: {d["sockets"]}
- NUMAノード数: {d["numa_nodes"]}
- L1データキャッシュ: {d["l1d_per_core_kib"]} KiB / core
- L1命令キャッシュ: {d["l1i_per_core_kib"]} KiB / core
- L2キャッシュ: {d["l2_per_core_kib"]} KiB / core
- 共有L3キャッシュ: {d["l3_shared_mib"]} MiB
- キャッシュライン: {d["cache_line_bytes"]} bytes
- 関連ISA: {isa}"""


def build_prompt(
    document: str,
    representation: str,
    condition: str,
    profile: dict,
    loop_count: int,
) -> str:
    loop_ids = ", ".join(
        f"{i:02d}"
        for i in range(loop_count)
    )

    hw = hardware_text(
        condition,
        profile,
    )

    return f"""あなたはコンパイラ最適化候補を1つ選択します。

目的:
対象CPU上で、提示されたカーネルの実行時間が最も短くなる可能性が高い候補IDを1つ選んでください。

重要:
- コードを書き換えてはいけません。
- 候補IDを1つだけ選んでください。
- 実測性能、過去の候補順位、過去のモデル回答は与えられていません。
- 候補はClang 18.1.3でコンパイルされます。
- コンパイル条件は -O3 -march=native -fno-fast-math -ffp-contract=off -fno-lto です。
- 性能評価は単一スレッドです。
- 測定時はSMTとTurbo/Boostを無効化します。
- 出力に理由説明を含めないでください。

コード表現:
{representation}

{hw}

選択可能なループ番号:
{loop_ids}

候補ID規則:
- identity
- loop_XX_unroll_count_2
- loop_XX_unroll_count_4
- loop_XX_unroll_count_8
- loop_XX_unroll_count_16
- loop_XX_interleave_count_2
- loop_XX_interleave_count_4
- loop_XX_interleave_count_8
- loop_XX_vectorize_width_2
- loop_XX_vectorize_width_4
- loop_XX_vectorize_width_8

ここでXXには上記の存在するループ番号のみ使用できます。

候補IDの意味:
- identity: 追加のループヒントを指定しない
- unroll_count_N: 対象ループ直前にClangのunroll_count(N)ヒントを指定
- interleave_count_N: 対象ループ直前にClangのinterleave_count(N)ヒントを指定
- vectorize_width_N: 対象ループ直前にClangのvectorize_width(N)ヒントを指定

入力:
----- BEGIN INPUT -----
{document.rstrip()}
----- END INPUT -----

次のJSONだけを返してください。
{{"candidate_id":"..."}}
"""


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--hardware-profile",
        type=Path,
        required=True,
    )

    args = ap.parse_args()

    profile = load_json(
        args.hardware_profile
    )

    assert (
        CONTRACT["contract_id"]
        == "final-llm-prompt-contract-v1"
    )

    assert (
        CONTRACT["status"]
        == "FROZEN_BEFORE_FINAL_LLM_API_CALLS"
    )

    assert (
        CORPUS_MANIFEST["instances"]
        == 90
    )

    kernels = {
        x["kernel_id"]: x
        for x in CANDIDATE_MANIFEST["kernels"]
    }

    rows = []

    totals = defaultdict(
        lambda: {
            "documents": 0,
            "characters": 0,
            "utf8_bytes": 0,
        }
    )

    # P0はCPU共通。
    # 2台目で再生成しても同一内容になることを保証する。
    conditions = (
        "P0",
        "P1",
        "P2",
    )

    for corpus_row in CORPUS_MANIFEST["rows"]:
        kernel = corpus_row["kernel"]
        size = corpus_row["size"]

        loop_count = kernels[
            kernel
        ]["syntactic_loop_count"]

        for rep_name, rep_dir in REPRESENTATIONS.items():
            source = (
                CORPUS
                / rep_dir
                / kernel
                / f"{size}.txt"
            )

            document = source.read_text(
                encoding="utf-8"
            )

            for condition in conditions:
                if condition == "P0":
                    target_dir = (
                        OUT
                        / "P0"
                        / "common"
                        / rep_dir
                        / kernel
                    )
                else:
                    target_dir = (
                        OUT
                        / condition
                        / profile["profile_id"]
                        / rep_dir
                        / kernel
                    )

                target_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                target = (
                    target_dir
                    / f"{size}.txt"
                )

                prompt = build_prompt(
                    document=document,
                    representation=rep_name,
                    condition=condition,
                    profile=profile,
                    loop_count=loop_count,
                )

                if (
                    condition == "P0"
                    and target.exists()
                ):
                    previous = target.read_text(
                        encoding="utf-8"
                    )

                    if previous != prompt:
                        raise RuntimeError(
                            "P0 changed between hardware profiles"
                        )

                target.write_text(
                    prompt,
                    encoding="utf-8",
                )

                key = (
                    f"{condition}:"
                    f"{profile['profile_id'] if condition != 'P0' else 'common'}:"
                    f"{rep_name}"
                )

                totals[key]["documents"] += 1
                totals[key]["characters"] += len(
                    prompt
                )
                totals[key]["utf8_bytes"] += len(
                    prompt.encode("utf-8")
                )

                rows.append({
                    "condition": condition,
                    "hardware_profile": (
                        "common"
                        if condition == "P0"
                        else profile["profile_id"]
                    ),
                    "representation": rep_name,
                    "kernel": kernel,
                    "size": size,
                    "loop_count": loop_count,
                    "path": str(
                        target.relative_to(REPO)
                    ),
                    "sha256": sha256_text(prompt),
                    "characters": len(prompt),
                    "utf8_bytes": len(
                        prompt.encode("utf-8")
                    ),
                })

    # 同じhardware profileで P0/P1/P2 x C/IR x 90
    assert len(rows) == 540

    manifest = {
        "prompt_corpus_id":
            "final-llm-prompts-v1",

        "prompt_contract":
            CONTRACT["contract_id"],

        "hardware_profile":
            profile["profile_id"],

        "logical_prompts_generated":
            len(rows),

        "independent_samples_per_condition":
            CONTRACT["sampling"][
                "independent_samples_per_condition"
            ],

        "rows":
            rows,

        "totals":
            dict(totals),

        "final_two_cpu_plan": {
            "P0_per_representation": 90,
            "P1_per_cpu_per_representation": 90,
            "P2_per_cpu_per_representation": 90,
            "cpu_count": 2,
            "representation_count": 2,
            "logical_prompts_per_model": 900,
            "samples_per_logical_prompt": 3,
            "requests_per_model": 2700,
            "paid_provider_count": 3,
            "paid_requests_total": 8100
        }
    }

    manifest_path = (
        OUT
        / f"manifest-{profile['profile_id']}.json"
    )

    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        "FINAL_LLM_PROMPTS_COMPLETE"
    )
    print(
        "hardware_profile =",
        profile["profile_id"],
    )
    print(
        "logical_prompts_generated =",
        len(rows),
    )

    print()
    print("=== 入力量 ===")

    for key in sorted(totals):
        x = totals[key]

        print(
            f"{key:40s} "
            f"docs={x['documents']:3d} "
            f"chars={x['characters']:9d} "
            f"bytes={x['utf8_bytes']:9d}"
        )

    print()
    print(
        "最終計画 requests/model = 2700"
    )
    print(
        "有料3モデル合計 requests = 8100"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
