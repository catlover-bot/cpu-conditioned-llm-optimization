# Goal 003: blind candidate-selection pilot

Goal 002の生成器・検証器・計測器を使い、課題固定、独立セッションの回答取り込み、
回答固定、新しいconfirmationによる採点を接続する。API SDKやAPI呼び出しはない。
実装担当エージェントも、過去の会話を引き継ぐsubagentも、評価回答を作らない。
実回答がない状態では `software_ready=true` / `awaiting_real_responses` である。
syntheticによる動作確認を実LLM実験と呼ばない。

## 引き継いだ基盤の確認

元コードは `75c1e8b388666566c2843adf0ccb6846a239ce95`、確認対象runは
`runs/goal002/20260909T165623.261899Z-ee785286`。実装開始時の成果物検査は合格した。
元runを変更せず、ソースと条件の出所に使う。古い測定値を新しい採点には使わない。

| 確認項目 | 保存資料と確認内容 |
| --- | --- |
| CompilerTarget | `experiment.json`。Clang 18.1.3、`x86_64-pc-linux-gnu`、target flagsなし。native指定なし |
| 既定ターゲットの補助証拠 | `candidates/reference/kernel.ll` の `target-cpu="x86-64"`、`tune-cpu="generic"`、SSE2を含む既定features |
| 全ビルド引数 | 各候補の `build.json`。共通 `-std=c11 -O3 -fno-fast-math -ffp-contract=off -fno-lto`、driverとkernelを別翻訳単位でコンパイル |
| ソースと実行バイナリ | `kernel.c`、`harness.c`、`kernel.h`、オブジェクト・programのハッシュ。process ledgerの実行時ハッシュと分析対象が一致 |
| タイマー | `CLOCK_MONOTONIC` の単一kernel呼び出し時間、単位ns。初期化と結果利用・出力は区間外 |
| 集計 | warmupを除くペア測定。時間の中央値・線形補間IQR、ペアごとのreference/candidate速度比の中央値 |
| 品質 | 中央値100000ns未満、相対IQR 0.20超、順位変動許容1、近接速度比0.03という事前設定 |
| 実行コード比較 | リンクしたELF x86-64のkernel関数の命令バイト範囲。即値・オフセット・分岐を保持。外部依存全体の同値性は未証明 |
| 最適化資料 | 実オブジェクト生成時の `kernel.opt.yaml` とPassed/Missed/Analysis索引。欠損は最適化不在の証明にならない |

reference、identity、unroll_1の抽出バイトは一致し、他の展開率は系列基準と相違した。
コード差だけから変換残存や性能差の原因は断定せずunknownとする。
既報の速度比は再現目標にも、ソフトウェアの合格条件にも使わない。

## 固定するprotocol

既定計画はサイズ128・256、入力seed17、none/spec各5リクエスト、計20件。
5択はunroll_1・2・4・8・16だけで、identityとdeliberately_wrongは新しい診断でもcontrolとして保持する。
各サイズでseed付き初期順を作り、5回循環させる。各候補は各提示位置に一度ずつ現れ、
対応するnone/specの候補順と共通payloadは一致する。

`protocol.json` は候補本文・ハッシュ、入力・ABI・メモリ・数値契約、CompilerTarget、
CPU説明の出所、試行順、全測定設定、無効・欠損・僅差・品質の扱いを保存する。
`pilot.json` がprotocolとstatic manifestのSHA-256を保持する。
`runner_source/` と `provenance.json` に実装ソースとGit/ホスト観測を保存する。
プロンプト、候補、雛形は固定後に編集しない。設定を変える場合は別pilotを作る。

この課題は開発中に性能を見ており、unseen benchmarkやheld-out taskではない。
noneにも共通のISA・ABI・コンパイラ条件を提示するため、ハードウェア情報を完全には隠していない。
specにだけ追加するのは、出所を記録したHostObservationの許可項目である。
WSLのCPUモデル・キャッシュ・ISA広告・トポロジーはguest-visibleとして記述し、
物理CPUの同一性、物理キャッシュ、周波数の独立確認はunknownとする。
ホスト名・ローカルパス・測定値・順位・コンパイラの実行後レポートはpromptへ渡さない。

`configs/selection-pilot.json` で提示順seed、CPU情報の観測元、測定CPUなどを指定する。
現在の測定先は同じ観測ホスト上のローカル実行だけで、CompilerTargetは元runの既定generic条件を維持する。
native/明示ターゲット、外部仕様の任意登録、リモート実行は現在未対応として拒否する。
この制約を黙って回避したり、未測定CPUを実測済みとして扱ったりしない。

## 手動export/import

WSLのリポジトリ直下で実行する。

```bash
.venv/bin/python -m cpucond pilot prepare \
  --source-run runs/goal002/20260909T165623.261899Z-ee785286 \
  --config configs/selection-pilot.json --output runs/goal003
pilot_dir=$(find runs/goal003/real -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
.venv/bin/python -m cpucond pilot check "$pilot_dir"
.venv/bin/python -m cpucond pilot status "$pilot_dir"
```

最初の2件は以下。各prompt全文だけを、測定値を見ていない別々の新規セッションへ渡す。
この文書、実装の会話、Goal 002レポート、他試行の回答は渡さない。
検索・コード実行・関数呼び出し等のツールを使用しない。各20リクエストの履歴を分離する。

- `$pilot_dir/requests/n128-t01-none/prompt.txt`
- `$pilot_dir/requests/n128-t01-spec/prompt.txt`

CPU説明以外のprompt差を避けるため、回答用 `request_id` はペア内共通の `n128-t01`。
取り込みには一意の `request_key`（`n128-t01-none` または `n128-t01-spec`）も使う。
各requestにはprompt hash、対応表、回答・metadata保存先、正確なimport引数列をprotocol内に記録する。
回答形式はJSONオブジェクト1個のみ。`request_id` と `selected_option_id` は必須、
`rationale_short` は任意の500文字以内。長い内部推論は求めない。

まずメタデータ雛形を編集用の場所へコピーする。

```bash
cp "$pilot_dir/requests/n128-t01-none/metadata-template.json" "$pilot_dir/incoming/n128-t01-none/metadata.json"
cp "$pilot_dir/requests/n128-t01-spec/metadata-template.json" "$pilot_dir/incoming/n128-t01-spec/metadata.json"
```

それぞれの**生回答を変更せず** `incoming/<request_key>/response.txt` に保存する。
metadata.jsonには実際の取得元・方式・確認できたモデル識別情報・日時を入力する。
生成設定・使用量が取れなければnullと理由を残し、推測しない。
`prompt_hash` は雛形の値を保持する。モデル識別・盲検条件は手動申告であり独立検証済みではない。
`blinding` の独立セッション・ツール不使用・過去結果未閲覧を保証できなければnull/falseと制限を残す。

```bash
.venv/bin/python -m cpucond pilot import "$pilot_dir" \
  --request-key n128-t01-none \
  --response "$pilot_dir/incoming/n128-t01-none/response.txt" \
  --metadata "$pilot_dir/incoming/n128-t01-none/metadata.json"
.venv/bin/python -m cpucond pilot import "$pilot_dir" \
  --request-key n128-t01-spec \
  --response "$pilot_dir/incoming/n128-t01-spec/response.txt" \
  --metadata "$pilot_dir/incoming/n128-t01-spec/metadata.json"
.venv/bin/python -m cpucond pilot status "$pilot_dir"
```

任意コードやshellとして回答を評価しない。未知ID、複数選択、不正JSON、ID不一致はinvalidとして原本とともに保存する。
同じrequestへの同じ原文の再importは拒否する。修正・再回答は別attemptに保存するが、
**主採点は常に最初のattempt**。最初がinvalidなら後の有効回答で置き換えない。
原文と解析結果は `responses/<request_key>/attempt-NNNN/` に別ファイルで保存する。

## 回答固定と独立採点

残りの回答も同じ経路で取り込む。20件を待たず1組で動作させることもできるが、
freeze時点の残りは未回答として固定する。固定後の追加回答には別pilotが必要になる。
0件のcollectionはfreezeできない。

```bash
.venv/bin/python -m cpucond pilot freeze "$pilot_dir"
.venv/bin/python -m cpucond pilot score "$pilot_dir"
.venv/bin/python -m cpucond pilot check "$pilot_dir"
```

`score` は旧runを指定する引数を持たず、固定後に新規診断runを作る。
同じ候補・driver・CompilerTarget・観測ホストを照合し、全controlと5候補を検証する。
既存器によるexplorationも保存するが、採点値には新しいconfirmationだけを使う。
フェーズ間の順位不安定は品質診断として引き継ぐ。
成功済み採点を上書きしない。失敗した試行も `scoring-attempts/` に残す。

全LLM回答と固定5方策・一様ランダム方策は、1個のconfirmation測定表を共有する。
回答20件は独立性能測定20件ではない。固定・ランダムの比較はoffline policy scoringであり、
全候補の参照測定をLLMの探索として数えない。一様ランダムは各候補確率1/5の厳密な期待値である。

採点は選択頻度、none/spec対応ペアの変化、候補時間、対reference比、
5候補内の観測最小時間からの損失、全固定方策・ランダム方策を保存する。
損失は `候補中央値 / 5候補内の最小中央値 - 1`。
既定の損失0.03以内は実用上の僅差であり、正解・不正解や統計的同等性に変換しない。
品質や盲検条件が不十分なら判定保留とし、数値・警告を残す。
invalid/missingは計画母数20に残し、測定値のない選択はnullにする。

`score.json` が新規runと回答freeze、報告書の場所・ハッシュを結び付ける。
各採点attemptに `selection-report.json` / `.csv` / `.md` と測定原本を保存する。
`pilot check` は原回答の再解析、固定値、実行順・測定原本の検査、報告書の再構成を行う。

## syntheticによる動作確認

実回答の取得とは別に実行する。このコマンドはrealコホートを拒否する。

```bash
.venv/bin/python -m cpucond pilot prepare \
  --source-run runs/goal002/20260909T165623.261899Z-ee785286 \
  --config configs/selection-pilot.json --output runs/goal003 --cohort synthetic
fixture_dir=$(find runs/goal003/synthetic -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
.venv/bin/python -m cpucond pilot synthetic "$fixture_dir"
.venv/bin/python -m cpucond pilot freeze "$fixture_dir"
.venv/bin/python -m cpucond pilot score "$fixture_dir"
.venv/bin/python -m cpucond pilot check "$fixture_dir"
.venv/bin/python -m pytest -q
git diff --check
```

real/syntheticは別ディレクトリ・別集計であり、メタデータの混入を拒否する。
syntheticは `software_ready`、実回答0件は `awaiting_real_responses`、
一部回答やinvalid/missingありは `real_pilot_partial`、全20件が有効で採点済みなら `real_pilot_complete`。
completeという状態は、統計的有意性・盲検の独立証明・CPU理解を意味しない。

## 次の実機へ持ち込むとき

2種類のレンタルCPUそれぞれで環境・利用可能ISA・コンパイラを観測し、
同じ候補と正しさ契約による新しい診断runを作ってから、そのホストのprotocolを別々に固定する。
必要なtarget変更、測定品質・負荷統制、モデル取得条件、探索予算、統計計画も事前に決める。
現時点で契約・接続・リモート実行は行っていない。物理仕様と仮想化による観測制限を確認する作業も残る。
複数CPUで評価するまではCPU間の適応を確認したと報告しない。
自由なC生成・最適化、IR/Assembly入力の最適化は未実施である。
すべてのWSL出力は `development_smoke`、`publishable_benchmark=false` を維持する。
