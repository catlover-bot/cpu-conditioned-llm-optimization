# 旧資産の読み取り専用監査

Goal 001 の実装判断のため、旧リポジトリの GitHub 上のソースを確認した。
旧コードのコピー・関数移植は行わず、新しい `cpucond` は独立して実装する。
以下の判断は、記載したコミットのソースに限る。大学サーバーの最新状態や、
旧実験の正しさ・性能を確認したという意味ではない。

## 出所と取得方法

- 監査日: 2026-09-10
- リポジトリ: <https://github.com/catlover-bot/Profile-Guided-Verified-LLM-Optimization>
- ブランチ: `main`
- 正確なコミット SHA: `787326c988a8be0104eab7b886d7487723080bcd`
- 参照コピー: `/tmp/cpucond-legacy-audit-20260910`
- `/home/mhirotaka/workspace` の直下を確認したが、旧リポジトリはなかった。
- 公開 HTTPS URL から `git clone --depth 1 --branch main` で取得した。
  新リポジトリの中には配置していない。認証情報を指定・表示していない。
- `git ls-remote --symref ... HEAD` と取得後の `git rev-parse HEAD` で SHA を照合した。
  取得直後および監査後の `git status --porcelain` は空だった。
- 旧リポジトリのスクリプト、テスト、候補、API 呼び出し、ジョブは実行していない。
  ソースの読み取り、追跡ファイル一覧とパスの存在確認だけを行った。

以降の旧ファイル名はすべて上記 SHA に対応する。
[固定コミットのツリー](https://github.com/catlover-bot/Profile-Guided-Verified-LLM-Optimization/tree/787326c988a8be0104eab7b886d7487723080bcd)
から参照できる。

## 実装を確認した項目と判断

| 項目 | ソースから確認できたこと | Goal 001 での判断 |
| --- | --- | --- |
| カーネル読み込み | `src/vallmopt/datasets/polybench.py` は外部 PolyBench ルート、既知カーネル名、ソースパターン、サイズ定義、include を設定から解決する。`scripts/run_polybench_one.py:78` 以降で発見した C ファイルを読む。 | 入力の出所とビルド条件を明示する考え方は参考にする。外部データセット探索器は移植しない。Goal 001 は同梱の独自 float64 スモーク fixture を使う。 |
| ビルド | `src/vallmopt/build/cbuild.py` は引数リストを構築する。`build/polybench.py:28` の既定値は `-std=c99 -O3 -march=native -Wall -Wextra`、リンクは `-lm`。検証と計測のビルドで `POLYBENCH_DUMP_ARRAYS` / `POLYBENCH_TIME` を切り替える。 | 構造化されたビルド引数は参考にする。旧既定フラグと PolyBench アダプターは採用しない。CPU 提示条件から独立したビルド設定と、明示した FP フラグを新たに用意する。 |
| サブプロセス | `src/vallmopt/utils/subprocess.py` は終了コード、stdout/stderr、timeout、壁時計時間を記録する。`verify/runtime.py` は timeout と非ゼロ終了に別の理由を付ける。 | 失敗理由と診断を残す設計は参考にする。旧ラッパーは移植しない。プロセス経過時間をカーネル時間と混同しない記録にする。 |
| 正しさと浮動小数点 | `src/vallmopt/verify/output.py:22` は stdout の文字列一致、同 `:74` は正規化したストリームの文字列一致を判定する。float64 の全要素、ビット列、要素数、有限性を扱う比較器ではない。両出力が空なら一致として通る。 | この比較方式は採用しない。全要素の float64 ビット比較、空出力・欠落・要素数不一致・非有限値の拒否を独立実装する。旧 PolyBench utility の実体を取得していないため、旧出力の表示精度は確認していない。 |
| 検証から計測への遷移 | `src/vallmopt/verify/pipeline.py` は失敗後の後続ゲートを skipped にする。一方 `scripts/run_polybench_one.py:203` は「失敗ゲートがない」を計測の条件とし、同 `:318` では verify モード外の出力比較を skipped にする。 | 失敗で後続を止める考え方は参考にする。ただし「失敗がない」だけの条件は採用しない。Goal 001 は正しさが明示的に成功した候補だけを計測対象にする。これはソース上の分岐の確認であり、旧実験を再実行した結果ではない。 |
| 反復計測 | `src/vallmopt/benchmark/runner.py:13` は shell コマンドを起動する前後の `perf_counter` 差を測る。同 `:73` は baseline 全反復の後に candidate 全反復を実行する。 | 起動・初期化・出力まで含む壁時計計測と、順序を交互にしない計測は移植しない。カーネル内タイマー、初期状態の復元、ウォームアップの区別、順序を入れ替えるペア計測を新規実装する。 |
| 集計 | `src/vallmopt/benchmark/stats.py` は中央値、線形補間 percentile による IQR、baseline 中央値 / candidate 中央値を計算する。`benchmark/hyperfine.py` は warmup を含むコマンド構築器であり、実行はしない。 | 中央値とばらつきを生データとともに保存する考え方は参考にする。旧関数はコピーしない。ゼロ・不正な測定値や架空の速度比を成功値として補わない。 |
| CPU 設定 | `src/vallmopt/arch.py` の `Architecture` は `tag`, `isa`, `description`, `cflags_extra` を一つに持つ。`configs/architectures.yaml` の各 CPU クラスは `-march=native` を設定し、`scripts/run_polybench_one.py:151` がフラグを取り込む。 | 提示用 CPU 情報とビルド設定を同じレコードで扱う構造は採用しない。`HostObservation`、`PromptCPUContext`、`CompilerTarget` の分離が必要。旧 CPU 名・仕様を現在の WSL の観測値として使わない。 |
| プロンプト | `scripts/generate_prompts.py` と `tests/test_prompt_builder.py` は `vallmopt.prompts.PromptBuilder` を import している。呼び出し側と設定には参照 C、変換制約、CPU/ISA タグ、出力制約がある。だが取得したツリーに `src/vallmopt/prompts` も対応するモジュールもない。 | 呼び出し側の存在をもってビルダー実装の確認済みとはしない。新しい none/spec プロンプトを明示的な許可リストから独立実装する。旧ビルダー内部で CPU 情報がどう入るかは未確認。 |
| ログ | `src/vallmopt/logging/schema.py` は候補・検証・計測別 dataclass とハッシュ、Git commit、診断、生のタイミングを持つ。`logging/jsonl.py` は追記と上書きの両方を提供する。`utils/hashing.py` は SHA-256。 | 出所をハッシュ・設定・診断で結び付ける考え方は参考にする。旧スキーマと上書き規則は移植しない。新スキーマでは Git dirty、実際のツール情報、ビルド引数、成果物、環境上の限界をまとめ、既存 run を上書きしない。 |

## README と取得したソースとの差

README だけで実装状況を判定していない。具体的には次の違いがある。

- README は実 LLM API 呼び出しを未対応と記載しているが、
  `scripts/generate_llm_candidate_once.py` には OpenAI、Anthropic、Gemini の
  呼び出しコードと応答・候補・メタデータ保存処理がある。
  実装の存在を確認しただけで、動作や旧実験の実施を検証してはいない。
  Goal 001 には移植せず、API も呼ばない。
- README とテストが参照する `PromptBuilder` の実装ファイルは取得したツリーにない。
  `.gitignore:8` の `prompts/` は、`git check-ignore -v
  src/vallmopt/prompts/__init__.py` でも一致した。
  無視規則がそのパスに一致することは確認したが、それが欠落の原因だったか、
  大学サーバーに未追跡実装があるかは未確認。
- `runs/artifact_manifest.txt` には 113 件のパスが列挙されていたが、
  この参照コピーでは列挙されたファイルは 0 件だった。
  一覧の名前から測定成功・性能改善・候補の正しさを推定しない。

## 確認したファイル

全文を読んだ主なファイル:

- `src/vallmopt/datasets/polybench.py`
- `src/vallmopt/build/cbuild.py`, `src/vallmopt/build/polybench.py`
- `src/vallmopt/utils/subprocess.py`, `src/vallmopt/utils/hashing.py`
- `src/vallmopt/verify/output.py`, `src/vallmopt/verify/pipeline.py`,
  `src/vallmopt/verify/runtime.py`
- `src/vallmopt/benchmark/runner.py`, `src/vallmopt/benchmark/stats.py`,
  `src/vallmopt/benchmark/hyperfine.py`
- `src/vallmopt/arch.py`, `src/vallmopt/generation/base.py`,
  `src/vallmopt/generation/mock.py`
- `src/vallmopt/logging/schema.py`, `src/vallmopt/logging/jsonl.py`,
  `src/vallmopt/analysis/summarize.py`
- `configs/architectures.yaml`, `configs/prompts.default.yaml`,
  `configs/experiments.default.yaml`, `configs/verify.default.yaml`
- `scripts/generate_prompts.py`, `scripts/generate_llm_candidate_once.py`
- `tests/test_prompt_builder.py`, `tests/test_verify_pipeline.py`, `tests/test_stats.py`
- `examples/kernels/dot_product/reference.c`, `.gitignore`

該当箇所を読んだファイル・一覧:

- `scripts/run_polybench_one.py`: import、入力読込、プロンプト呼び出し、
  ビルド設定、記録、比較、計測への分岐、全体 status の判定。
- `README.md`: 機能説明、未対応項目、プロンプト・検証・計測の説明。
- `runs/artifact_manifest.txt`: 先頭の記載と、全 113 パスの存在確認。
- `git ls-files`: 追跡ファイル一覧。ジョブ名やファイル名の存在確認は、
  当該ジョブの内容確認・実行確認とは区別した。

## 再利用と未確認部分の境界

再利用したのは、検証を段階に分けること、引数を構造化して記録すること、
コード・プロンプトの SHA-256、生の計測値と中央値・ばらつきを保存すること、
mock と実生成を区別することという設計上の考え方である。
**旧ソースからの移植は 0 件**で、移植元ファイルと変更差分の対応表は該当しない。
新しい fixture を旧候補や正式な PolyBench カーネルとは呼ばない。

以下は今回確認していない。

- 大学サーバーのブランチ、最新 commit、未追跡ファイル、環境、ジョブの実行状況。
- 旧 `PromptBuilder` の実装、旧環境でのビルドとテストの成否。
- 外部 PolyBench checkout、utility ソース、旧候補の実体と全要素の正しさ。
- manifest に列挙された測定ファイル、プロンプト、IR、Assembly、逆アセンブルの内容。
- 全旧ジョブ・全スクリプトの網羅的な監査、旧論文結果の再現。

旧結果は新しい実験条件の結果として取り込まない。参照コピーはソース監査の
ためだけに取得しており、旧リポジトリ・旧実験結果は変更していない。
