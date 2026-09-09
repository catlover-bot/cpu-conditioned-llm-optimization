# cpu-conditioned-llm-optimization
Studying and improving CPU-conditioned LLM optimization through controlled experiments and executable-code analysis.

Goal 001 は、CPU情報の提示条件、実際のビルド条件、実行環境の観測を分離した最小実験基盤です。
小さな独自の `gemm_smoke` と手書きC候補を使い、正しさ検証、検証後の反復計測、実行コードと来歴の保存までを確認します。
LLMへの送信・生成、CPU特化の有効性検証、正式なPolyBench評価は実施しません。

## WSLでのセットアップと実行

Ubuntu / Linux、Python 3.12以上、Clang、LLVMの `llvm-objdump` が必要です。
テストはGCCでもCハーネスを確認するためGCCも必要です。ツールのバージョンは実行時に観測します。
既存の `.venv` を使用してください。まだない場合だけ `python3 -m venv .venv` で作成します。

```bash
cd /home/mhirotaka/workspace/cpu-conditioned-llm-optimization
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m cpucond doctor
python -m pytest -q
python -m cpucond smoke --output runs/goal001
```

`doctor` はホスト観測、利用可能CPU、WSL判定、ツールの実体とバージョン、欠測理由をJSONで表示します。
必須ツールが見つからない場合は非ゼロ終了します。テストは実際のClang/GCCビルドと実行を含み、必要なコンパイラの不在を黙ってスキップしません。
Pythonの依存関係は `.venv` 内にインストールします。実行コード自体はPython標準ライブラリだけを使います。

`smoke` は指定先を親として、時刻とUUIDを含む新しいrunディレクトリを作ります。既存runは上書きしません。
最後に `run_directory`、`status`、各候補の検証結果を表示します。
期待したfixture結果と成果物の検査が通った場合に限り `status: completed`、終了コード0になります。
正しい候補の失敗、誤候補の誤受理、計測失敗、成果物不備は実行全体の失敗です。

## 保存した成果物の確認

次のコマンドは、直近のrunを選び、その成果物のハッシュと記録間の整合性を確認します。

```bash
run_dir=$(find runs/goal001 -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1)
python -m cpucond check-artifacts "$run_dir"
python -m json.tool "$run_dir/summary.json"
```

| 保存先（run内） | 内容 |
| --- | --- |
| `experiment.json` | スキーマ1.0、設定、ホスト、Python・Clang・objdump、Gitコミットとdirty状態、入力・候補・プロンプトのハッシュ、結果、成果物一覧 |
| `prompts/none.txt`, `prompts/spec.txt` | 同一入力・同一共通契約で作ったローカルのプロンプト |
| `candidates/<name>/kernel.c`, `kernel.h`, `harness.c` | ビルドに使ったソースのコピー |
| `candidates/<name>/build.json` | 全コマンド引数、作業場所、成否、標準出力・診断 |
| `candidates/<name>/verification.json` | 各サイズ・seedの全要素出力と検証判定 |
| `candidates/<name>/measurements.json` | 検証成功候補のウォームアップ、ペア順序、反復番号、生のナノ秒値、集計 |
| `candidates/<name>/kernel.ll`, `kernel.s`, `kernel.disasm` | Cから生成したLLVM IR、Assembly、実行ファイル中のkernelの逆アセンブル |
| `candidates/<name>/program`, `*.o` | 実際に使用した実行ファイルとオブジェクト |
| `runner_source/` | 実行時のPythonモジュールと、取得できる場合はパッケージ設定のコピー |
| `summary.json` | 中央値、MAD、標準偏差、ペアごとの速度比、制約 |

ハッシュ一覧は `experiment.json` 自身を除く成果物を対象とします。第三者による改ざんへの署名ではありません。
`runs/`、`.venv/`、Pythonの生成物はGit管理対象外です。fixture・設定・テストは管理対象にできます。
ユーザー作成の `.gitignore` の既存ルールは保持しています。

## 検証と計測の契約

4候補はすべて `handwritten_fixture` です。`reference` と `identity` は同一ソース、`equivalent` は各出力のk方向の加算順を保ったループ変更、`deliberately_wrong` は意図的な値変更です。
独立したPythonオラクルとの一致もCハーネスのテストで確認します。

入力は実行時にuint32のseedから初期化する有限float64で、値域は `[-1, 1 - 2^-16]`、間隔は `2^-16` です。
出力行列は毎回 `+0` から開始します。標準の検証はサイズ1・3・8、seed 1・17・42の9組と、計測対象（サイズ64、seed 17）の計10組です。
すべての出力を16桁16進のbinary64ビット列として比較します。空出力、要素数の不一致、非有限値、形式不正は拒否します。
これは有限個のテストによる検証で、形式的な同値性証明ではありません。

Clangは `-std=c11 -O3 -fno-fast-math -ffp-contract=off` を使い、カーネルとハーネスを別々にコンパイルします。LTOは使用しません。
コンパイル失敗、異常終了、timeout、出力形式不正、値の不一致を区別します。
referenceの検証失敗時には全候補の計測を止め、誤候補には計測値を付けません。

検証を通過したidentity／equivalentについて、それぞれreferenceとのペアを計測します。
標準では2ウォームアップペアと6本計測ペアです。反復ごとにreference先行／candidate先行を交互に切り替えます。
C内の `CLOCK_MONOTONIC` でkernel呼び出しだけを計測し、初期化・プロセス起動・出力は区間外です。
実行時入力、別コンパイル、計測後の全出力利用によって計算の消去を防ぎます。checksumは結果利用のためだけで、正しさ判定には使いません。
各試行は新しいプロセスで、ウォームアップも別プロセスです。短いカーネルでは時計呼び出しの影響があり、安定したキャッシュ状態を保証しません。

利用可能CPU集合の先頭CPUへのaffinity固定を試し、結果と復元状態を記録します。`--cpu N` で集合内のCPUを指定できます。
固定できない場合は理由を残します。root設定変更やperfは必要ありません。
出力は常に `environment_role="development_smoke"`、`publishable_benchmark=false` であり、速度比をCPU特化の効果や論文の主結果として解釈しません。

## CPU提示条件と対応範囲

`HostObservation`、`PromptCPUContext`、`CompilerTarget` は独立しています。ホスト情報やビルドフラグをプロンプトに自動挿入しません。
プロンプトは入力コード、明示した共通契約、追加CPU説明だけから構築します。
`none` は追加のCPU仕様説明なしという意味です。共通のABI／ISA契約や入力コードの情報まで隠した条件ではありません。

標準の `spec` は架空のCPU／キャッシュ説明と明記したテスト用文面で、実測したホスト仕様ではありません。
実際に比較する仕様はUTF-8ファイルで明示できます。

```bash
python -m cpucond smoke --output runs/goal001 --spec-file configs/example-cpu-spec.txt
```

どちらの場合もnone／spec両方を保存し、ビルド条件は変わりません。プロンプトは送信せず、APIは呼びません。
入力形式は `c` / `llvm_ir` / `asm` を区別し、現在の評価対象はCだけです。
`--input-kind llvm_ir` と `--input-kind asm` は明示的に拒否します。保存したIR／AssemblyはCの分析成果物です。
任意の外部候補コードを安全に実行する隔離環境は提供していません。CLIが評価する対象は同梱の手書きfixtureです。

研究の比較計画と未実装部分は [研究設計](docs/research-design.md)、旧資産の根拠と未確認部分は [旧資産監査](docs/legacy-audit.md) を参照してください。
