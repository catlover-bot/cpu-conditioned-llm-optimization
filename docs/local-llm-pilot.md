# Goal 003.1: Ollamaによるローカル回答取得

Goal 003の未回答manual cohortとsynthetic cohortを保全し、同じ20課題を
`runs/goal0031/local/<pilot-id>` の独立した実回答コホートへコピーする。
既存schemaの `cohort=real` に `acquisition_backend=ollama_local` を加え、
手動回答やsynthetic回答と混ぜない。実験の用途は常に
`environment_role=development_smoke` / `publishable_benchmark=false`。

## 事前に固定する条件

- サイズ128/256、none/spec各5試行。候補、提示位置の均等化、共通契約、
  Clang 18.1.3 generic条件、測定品質方針は元pilotと同じ。
- 入力とpromptをバイト単位でコピーし、元pilotのprotocol、manifest、
  入力・promptのSHA-256を新protocolに保存する。元回答・旧測定表はコピーしない。
- モデルは `qwen2.5-coder:7b-instruct-q4_K_M` 1本。
  初期のWSL利用可能メモリ約13 GiBに対し重みは4,683,074,048 bytes。
  16,384 contextのf16 KV cache概算896 MiBに加え、計算バッファとOS用の余裕を見込む。
  概算は実測メモリではなく、実際のロード後のAPI・プロセス観測で確認する。
- temperature 0.2、seeds 31001/31002/31003/31004/31005。
  同じ試行番号のnone/specに同じseedを使う。完全な再現性は保証しない。
- context 16,384、回答上限512、CPU (`num_gpu=0`)、8 threads、batch 512。
  その他の全オプション、共通system、raw ChatMLテンプレート、JSON出力モードは
  `protocol.json` の `local_llm` に固定する。回答を見て変更しない。

Ollamaは公式リリースv0.33.3、MIT。モデルは公式Ollama registry配布、Apache-2.0。
release archive、実行バイナリ、モデルmanifest、モデルblobのdigestとライセンス原本を保存する。
モデル重みはリポジトリ外に置く。公式資料:
[local only設定](https://docs.ollama.com/faq#how-do-i-disable-ollama-cloud-features)、
[API](https://docs.ollama.com/api/generate)、
[Ollama配布](https://github.com/ollama/ollama/releases/tag/v0.33.3)、
[モデル](https://ollama.com/library/qwen2.5-coder:7b-instruct-q4_K_M)、
[Qwen構成](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/blob/main/config.json)。

## コンテキストと独立性

`/api/generate` に `raw=true` で明示したChatMLを送る。内容は固定systemと
そのリクエストの `prompt.txt` だけ。過去の回答、会話context、測定結果、toolsは送らない。
Ollama既定テンプレートと使用テンプレートを両方記録する。

QwenのGPT-2 byte-level BPEでは、UTF-8 bytesからのmergeはtoken数を増やさない。
全文renderのUTF-8 byte数に特殊token用32と回答用512を加えた保守上界が
context内に収まることを全20件で先に検査する。文字数から厳密なtoken数を算出したとは扱わない。
全20件に回答上限1の技術的preflightを実行し、API入力token数、実ロードcontext、CPU配置も検査する。
preflight回答は本試行に取り込まない。全文が入らなければ生成前に拒否する。

接続先は数字のループバックHTTP originだけ。proxy・redirectは無効。
実際のOllama server PIDの `/proc/<pid>/environ` にある `OLLAMA_NO_CLOUD=1`、
`OLLAMA_NUM_PARALLEL=1` と、そのPIDが所有するloopback listenerを確認する。
モデルtagのdigest、Ollama版、show metadataを固定値と照合する。

## 実行・再開

WSL内で既存venvを使用する。設定の生成例と実行済みの正確なrunパスは
`runs/goal0031-setup/` と完了報告を参照。

```bash
cd /home/mhirotaka/workspace/cpu-conditioned-llm-optimization
.venv/bin/python -m cpucond pilot prepare-local \
  --source-pilot runs/goal003/real/20260909T172539.164336Z-2374beee \
  --local-config runs/goal0031-setup/local-config.json \
  --output runs/goal0031
# 表示された一意のpilot_directoryを指定する。
pilot_dir=runs/goal0031/local/<pilot-id>
.venv/bin/python -m cpucond pilot local-preflight "$pilot_dir"
.venv/bin/python -m cpucond pilot local-run "$pilot_dir" --limit 2
.venv/bin/python -m cpucond pilot local-check "$pilot_dir"
.venv/bin/python -m cpucond pilot local-run "$pilot_dir"
.venv/bin/python -m cpucond pilot local-unload "$pilot_dir"
.venv/bin/python -m cpucond pilot status "$pilot_dir"
.venv/bin/python -m cpucond pilot freeze "$pilot_dir"
.venv/bin/python -m cpucond pilot score "$pilot_dir"
.venv/bin/python -m cpucond pilot check "$pilot_dir"
```

`local-run` を再実行すると保存済み回答を保持し、未処理のみ順番に取得する。
通信失敗はattemptとして残り、明示的な再開時に再試行できる。
server PIDも固定するため、再開は同じOllama serverプロセスの稼働中に行う。
serverを再起動した後の同一pilot再開は現実装では拒否される。モデルのunloadはserver終了ではない。
保存されたAPI原本からのimport復旧は再生成を伴わない。
不正JSON・候補ID不正・出力打ち切りも最初の回答として保持する。
回答が正しくなるまでの再生成は禁止。固定後に回答を追加するには別pilotが必要。

モデルをアンロードし `/api/ps` とrunnerプロセス停止を確認してからfreeze/scoreする。
共有file lockでこの実装の推論と性能測定を排他にする。
他ソフトの負荷を防げるとは主張せず、従来のwarmup・負荷観測・品質警告を維持する。
新しいconfirmationだけで全LLM回答・固定5方策・一様ランダムの期待値を採点する。
API生成時間とC kernel実行時間は別の記録・単位のまま比較する。

## 保存と検査

`local-acquisition/technical-preflight/` に技術試行、`local-acquisition/` 内の取得記録に
request ID/hash、送信payload、API応答原本、回答原文、hash、生成設定、取得時刻、
APIが返したtoken数/時間、終了理由、失敗、import結果を保存する。
回答原文を既存 `responses/<key>/attempt-0001/` にそのままimportする。
`freeze.json` と `scoring-attempts/` が固定回答、新confirmation、選択頻度、方策比較を結び付ける。
`pilot check` は元の回答検査・測定成果物検査にlocal取得の整合性検査を加える。

コード変更後は旧runを変更せず、新commitから新pilotを作る。
最終コードのテストは `.venv/bin/python -m pytest -q`、差分検査は `git diff --check`。
CPU説明ありの勝利はソフトウェアの合格条件に含まれない。
