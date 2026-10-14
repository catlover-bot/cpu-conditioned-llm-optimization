#!/usr/bin/env python3
"""既存Qwenのローカル生成試験。gemm MINIのCとLLVM IRを各1回直接生成する。
外部のモデルAPI、ダウンロード、生成コードのコンパイル/実行は行わない。
Goal0064の入力照合/プロンプト関数と、既存Ollamaの実プロセス検査を再利用。
既存の実験出力は変更しない。途中失敗や打切りも保存し、自動再生成しない。
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

REVISION = 'server-open-codegen-32b-development-v1'
MODEL = 'qwen2.5-coder:32b-instruct-q4_K_M'
DIGEST = None  # 取得後・生成前に固定した完全なモデルハッシュを読み込む。
RUNTIME_SHA = '7deaad14177b824d8fcff7136d4418c0111d2db35fa872a5071fa8db5b8db527'
GATE_SHA = '809819e965bb7ec80487d4fb65c5313e1b00e4378ced059fd36d9e1bef22ee8e'
MAX_TEXT = 256*1024
MAX_RESPONSE = 16*1024*1024
ENDPOINT = 'http://127.0.0.1:11434'
CTX = 32768
CAPS = {'C':4096,'IR':8192}
SYSTEM = 'You optimize numerical code under the supplied exact correctness contract. Return only the complete requested code, without explanations or tool use.'
CHAT = '<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n'


class Problem(RuntimeError):
    pass

def need(ok, message):
    if not ok:
        raise Problem(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def unique(pairs):
    result = {}
    for k, v in pairs:
        need(k not in result, 'JSONキー重複: ' + k)
        result[k] = v
    return result

def loads(data):
    def bad(v):
        raise Problem('JSONの非有限数: ' + v)
    return json.loads(data, object_pairs_hook=unique, parse_constant=bad)

def load(path):
    path = Path(path)
    need(path.is_file() and path.stat().st_size <= MAX_RESPONSE, 'ファイル欠落/過大: ' + str(path))
    return loads(path.read_text(encoding='utf-8'))

def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    # 書き換えず、既存なら停止する。
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def jwrite(path, obj):
    write(path, encoded(obj))

def safe(root, rel):
    q = PurePosixPath(rel)
    need(bool(q.parts) and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,
         '不正な相対パス: ' + rel)
    root = Path(root).resolve()
    p = root / Path(*q.parts)
    need(p.is_file() and root in p.resolve().parents, 'ファイル欠落/範囲外: ' + str(p))
    cur = p
    while cur != root:
        need(not cur.is_symlink(), 'リンクは許可しません: ' + str(cur))
        cur = cur.parent
    return p

def manifest(root):
    d = {}
    for line in (Path(root) / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        h, sep, rel = line.partition('  ')
        if rel.startswith('./'):
            rel = rel[2:]
        need(sep and re.fullmatch(r'[0-9a-f]{64}', h) and rel not in d, 'ハッシュ一覧が不正')
        d[rel] = h
    return d

def hashes(root, target='SHA256SUMS'):
    entries = []
    for p in sorted(Path(root).rglob('*')):
        need(not p.is_symlink(), 'リンクを含む結果です')
        if p.is_file() and p.name != target:
            entries.append(f'{file_sha(p)}  {p.relative_to(root).as_posix()}\n')
    write(Path(root)/target, ''.join(entries))

def gate_evidence(repo, gate_dir):
    gate_dir = Path(gate_dir).resolve()
    hm = manifest(gate_dir)
    for name in ('summary.json', 'provenance.json'):
        need(file_sha(safe(gate_dir, name)) == hm.get(name), 'サーバー検証記録が一致しません: ' + name)
    s = load(gate_dir/'summary.json')
    p = load(gate_dir/'provenance.json')
    expected = {'completion': 'CODEGEN_DEV_GATE_COMPLETE', 'instances_planned': 18,
                'instances_completed': 18, 'instances_passed': 18, 'positive_checks': 1512,
                'positive_passed': 1512, 'negative_checks': 132, 'negative_detected': 132,
                'api_calls': 0, 'performance_measurements': 0}
    for k, v in expected.items():
        need(type(s.get(k)) is type(v) and s.get(k) == v, '検証要約が想定と異なります: ' + k)
    need(s.get('errors') == [], '検証にエラーがあります')
    need(p.get('tool_sha256') == GATE_SHA, 'サーバー検証器の版が違います')
    need(p.get('executions_are_known_reference_and_controls_only') is True, '検証の実行対象が違います')
    need('AMD EPYC 7402' in p.get('host', {}).get('cpu_model', ''), '検証の対象CPUが違います')
    need('clang version 18.1.3' in p.get('compiler', ''), '検証のコンパイラが違います')
    locator = Path(repo)/'runs/goal0063-latest-package.txt'
    prep = Path(locator.read_text(encoding='utf-8').strip()).resolve()
    need(Path(repo).resolve() in prep.parents, 'ローカルパッケージがリポジトリ外です')
    pkg = prep/'package'
    need(file_sha(pkg/'package.json') == p.get('package_manifest_sha256'),
         'ローカル入力とサーバー検証が別のパッケージです')
    pi = load(pkg/'package.json')
    need(pi.get('tool_sha256') == GATE_SHA and pi.get('revision') == 'codegen-development-gate-v1',
         'パッケージ版が違います')
    pm = manifest(pkg)
    need(pm.get('package.json') == file_sha(pkg/'package.json'), 'パッケージ記録のハッシュ不一致')
    matches = [x for x in pi['items'] if (x['task'], x['size']) == ('gemm', 'MINI')]
    need(len(matches) == 1, '開発用GEMM MINIが一意ではありません')
    inputs = {}
    for form in ('C', 'IR'):
        spec = matches[0]['sources'][form]
        src = safe(pkg, spec['path'])
        data = src.read_bytes()
        need(len(data) <= MAX_TEXT and spec['sha256'] == sha(data) == pm.get(spec['path']), '検証済み入力の不一致')
        inputs[form] = data.decode('utf-8')
        need('CPUCOND_LOOP_' not in inputs[form], '旧入力の位置表示が残っています')
        need('kernel_gemm' in inputs[form], '計算関数がありません')
    return inputs, {'gate_summary_sha256': file_sha(gate_dir/'summary.json'),
                    'gate_provenance_sha256': file_sha(gate_dir/'provenance.json'),
                    'gate_hash_list_sha256': file_sha(gate_dir/'SHA256SUMS'),
                    'package_sha256': file_sha(pkg/'package.json'),
                    'gate_source_directory': str(gate_dir), 'package_directory': str(pkg)}

def prompt(source, form):
    spec = ('Cの完全なコンパイル単位。kernel_gemmの関数名・引数型と宣言を維持し、本文を改良する。'
            if form == 'C' else
            'LLVM 18の完全なテキストモジュール。kernel_gemmの型、引数順、呼出規約を維持し、本文を改良する。'
            '既存の必要な宣言・属性・メタデータ定義を残す。')
    return f'''これは本番成績には使わない、数値計算のコード生成経路の開発試験です。
与えられた計算関数を直接改良し、計算結果を厳密に維持しつつ高速化してください。
候補IDの選択ではありません。変換後のコード全体だけを返してください。

対象: kernel_gemm（行列積）。CPU固有の型番や性能情報は与えません。
コンパイラ: Clang 18.1.3。後段は単一スレッド、-O3 -march=native
-fno-fast-math -ffp-contract=off -fno-lto。検証では汎用x86-64のビルドも使用します。
入力・数値の契約:
- ni, nj, nk は実行時の正の寸法で、開発検証の範囲は1〜512。ソースのMINIという名前や定数から固定してはいけません。
- Cはni×nj、Aはni×nk、Bはnk×nj。3配列は互いに重なりません。
- A, Bは読み取り専用。Cの全要素を含む観測値を参照とバイト単位で一致させます。
- binary64、最近接偶数丸め。符号付きゼロと非正規化数を保持。NaN・無限大を入力にしません。
- 引数alpha, betaを参照どおり使い、入力値や正解を埋め込まないでください。
- 積の括り方、各要素の加算順序を変えないでください。FMA、fast-math、近似計算、型の縮小は禁止。
- ループの展開・アクセス処理の工夫など、計算結果を変えない本文の改良は可能です。
- 入出力、時計、検証処理、グローバルな実行フック、外部プロセス・ファイル・ネットワーク操作を追加しないでください。
- 外部ライブラリへの計算の置換、CPU識別処理、インラインアセンブリ、対象CPU属性の追加は行わないでください。
出力形式: {spec}
理由説明、Markdownのコードフェンス、JSONを含めず、コードのみ出力してください。
正しさを維持できる改良がないと判断した場合は、未変更コードを返してください。

----- 元コード -----
{source.rstrip()}
----- 元コード終わり -----
'''

def extract_code(text, form):
    # 正規化は外側のコードフェンスだけ。自動修正/穴埋めはしない。
    s = text.strip()
    fence = re.fullmatch(r'```(?:c|C|llvm|LLVM|ir|IR)?[ \t]*\n(.*?)\n```', s, re.S)
    normalization = 'none'
    if fence:
        s = fence[1]; normalization = 'outer_markdown_fence_removed'
    need('```' not in s and '\x00' not in s, '出力に余分なフェンス/不正文字があります')
    if form == 'C':
        need(re.search(r'\bkernel_gemm\s*\(', s) is not None and 'define ' not in s, 'C出力の簡易形式検査に不合格')
    else:
        need(re.search(r'^define\b[^\n]*@kernel_gemm\(', s, re.M) is not None, '中間表現出力の簡易形式検査に不合格')
    return s.rstrip()+'\n', normalization

def _now():
    return datetime.now(timezone.utc).isoformat()

def _sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _endpoint(value):
    parsed = urlsplit(value)
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Ollama endpoint must use a numeric loopback address") from exc
    if (parsed.scheme != "http" or not address.is_loopback or not port or
            parsed.username or parsed.password or parsed.path not in ("", "/") or
            parsed.query or parsed.fragment):
        raise ValueError("Ollama endpoint must be an HTTP loopback origin with explicit port")
    return value.rstrip("/")

def server_evidence(endpoint, pid):
    """Inspect the actual serving process, its environment and owned listener."""
    endpoint = _endpoint(endpoint)
    parsed = urlsplit(endpoint)
    process = Path("/proc") / str(int(pid))
    if int(pid) <= 0:
        raise ValueError("invalid server PID")
    environment = {}
    for item in (process / "environ").read_bytes().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            if key in (b"OLLAMA_NO_CLOUD", b"OLLAMA_HOST", b"OLLAMA_NUM_PARALLEL", b"OLLAMA_MAX_LOADED_MODELS"):
                environment[key.decode()] = value.decode("utf-8", errors="strict")
    if environment.get("OLLAMA_NO_CLOUD") != "1":
        raise ValueError("serving process does not have OLLAMA_NO_CLOUD=1")
    if environment.get("OLLAMA_NUM_PARALLEL") != "1":
        raise ValueError("serving process must fix OLLAMA_NUM_PARALLEL=1")
    cmdline = (process / "cmdline").read_bytes().split(b"\0")
    if b"serve" not in cmdline:
        raise ValueError("PID is not an Ollama serve process")
    executable = str((process / "exe").resolve(strict=True))
    if not Path(executable).name.startswith("ollama"):
        raise ValueError("server executable is not Ollama")
    inodes = set()
    for fd in (process / "fd").iterdir():
        try:
            target = os.readlink(fd)
        except (FileNotFoundError, PermissionError):
            continue
        if target.startswith("socket:["):
            inodes.add(target[8:-1])
    listeners = []
    for filename, family in (("tcp", socket.AF_INET), ("tcp6", socket.AF_INET6)):
        for line in (process / "net" / filename).read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] != "0A" or fields[9] not in inodes:
                continue
            host_hex, port_hex = fields[1].split(":")
            raw = bytes.fromhex(host_hex)
            raw = raw[::-1] if family == socket.AF_INET else b"".join(raw[i:i + 4][::-1] for i in range(0, 16, 4))
            host = socket.inet_ntop(family, raw)
            if not ipaddress.ip_address(host).is_loopback:
                raise ValueError("Ollama process owns a non-loopback listener")
            listeners.append({"address": host, "port": int(port_hex, 16)})
    if {"address": parsed.hostname, "port": parsed.port} not in listeners:
        raise ValueError("endpoint is not an owned loopback listener of the inspected process")
    return {"checked_utc": _now(), "pid": int(pid), "executable": executable,
            "executable_sha256": _sha(Path(executable).read_bytes()),
            "environment": environment, "listeners": listeners,
            "verification": "actual /proc serving-process environment and owned listening socket"}

def local_api(path: str, payload=None, timeout=15):
    """固定ループバックへのみ接続。プロキシ、転送、認証キーは使わない。"""
    allowed={'/api/version','/api/tags','/api/show','/api/ps','/api/generate'}
    need(path in allowed,'未対応のAPI経路')
    conn=http.client.HTTPConnection('127.0.0.1',11434,timeout=timeout)
    try:
        data=None if payload is None else encoded(payload)
        conn.request('GET' if data is None else 'POST',path,body=data,
                     headers={'Content-Type':'application/json'})
        response=conn.getresponse()
        raw=response.read(MAX_RESPONSE+1)
        need(len(raw)<=MAX_RESPONSE,'応答が上限サイズを超えました')
        need(response.status==200,f'ローカル推論HTTPエラー: {response.status}: '+raw[:300].decode(errors='replace'))
        obj=loads(raw)
        need(isinstance(obj,dict),'応答がJSONオブジェクトではありません')
        need(not obj.get('error'),'ローカル推論エラー: '+str(obj.get('error','')))
        return raw,obj
    finally:
        conn.close()


def owned_server():
    errors=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            if p.stat().st_uid!=os.getuid():continue
            cmd=(p/'cmdline').read_bytes().split(b'\0')
            if b'serve' not in cmd or not cmd or b'ollama' not in cmd[0]:continue
            record=server_evidence(ENDPOINT,int(p.name))
            need(record['executable_sha256']==RUNTIME_SHA,'既存Ollamaの実行ファイル版が以前と異なります')
            return record
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        except (ValueError,Problem) as e:errors.append(str(e))
    raise Problem('同一ユーザーの安全なOllamaサービスを確認できません: '+'; '.join(errors[:3]))


def verify_local_weights(models):
    mf=models/'manifests/registry.ollama.ai/library/qwen2.5-coder/32b-instruct-q4_K_M'
    need(mf.is_file(),'以前のモデルが見つかりません。新規ダウンロードはしません: '+str(mf))
    need(file_sha(mf)==DIGEST,'以前のモデルとmanifestのハッシュが違います')
    rec=load(mf); blobs={}
    for b in [rec['config'],*rec['layers']]:
        d=b['digest']
        need(re.fullmatch('sha256:[0-9a-f]{64}',d) is not None,'不正なモデルblob')
        path=models/'blobs'/d.replace(':','-')
        need(path.is_file(),'モデルblobが欠けています: '+d)
        need(path.stat().st_size==b['size'],'モデルblobのサイズ不一致')
        if d not in blobs:
            need(file_sha(path)==d[7:],'モデルblobのハッシュ不一致: '+d)
            blobs[d]={'bytes':b['size'],'path':str(path)}
    return {'manifest_sha256':DIGEST,'verified_blobs':blobs}


def ensure_server(out, models):
    try:
        _,version=local_api('/api/version')
    except (OSError,http.client.HTTPException,Problem):
        # 既存の別サーバーやWindows側サービスを変更せず、ポート競合なら停止。
        with socket.socket() as sock:
            sock.settimeout(1)
            need(sock.connect_ex(('127.0.0.1',11434))!=0,
                 '11434番ポートが使用中ですがOllamaを確認できません。既存プロセスは変更しません')
        binary=Path.home()/'.local/opt/ollama-0.33.3/bin/ollama'
        need(binary.is_file(),'以前のOllama実行ファイルがありません: '+str(binary))
        need(file_sha(binary)==RUNTIME_SHA,'Ollama実行ファイルのハッシュが違います')
        env={k:v for k,v in os.environ.items() if k not in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY')}
        env.update({'OLLAMA_NO_CLOUD':'1','OLLAMA_HOST':'127.0.0.1:11434',
                    'OLLAMA_MODELS':str(models),'OLLAMA_NUM_PARALLEL':'1',
                    'OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_CONTEXT_LENGTH':str(CTX)})
        with (out/'ollama-service.log').open('xb') as log:
            child=subprocess.Popen([str(binary),'serve'],env=env,stdin=subprocess.DEVNULL,
                                   stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        jwrite(out/'started-local-service.json',{'pid':child.pid,'environment':{k:v for k,v in env.items() if k.startswith('OLLAMA_') and k in ('OLLAMA_NO_CLOUD','OLLAMA_HOST','OLLAMA_MODELS','OLLAMA_NUM_PARALLEL','OLLAMA_MAX_LOADED_MODELS','OLLAMA_CONTEXT_LENGTH')}})
        for _ in range(60):
            if child.poll() is not None:raise Problem('Ollama起動失敗。ollama-service.logを確認してください')
            time.sleep(.5)
            try:_,version=local_api('/api/version',timeout=2);break
            except (OSError,http.client.HTTPException,Problem):pass
        else:raise Problem('Ollama起動を30秒以内に確認できません')
    need(version.get('version')=='0.33.3','Ollamaの版が以前と異なります: '+str(version))
    record=owned_server()
    raw,ps=local_api('/api/ps');write(out/'models-already-loaded.json',raw)
    # 既存の大モデルに重ねて読み込まない。
    for m in ps.get('models',[]):
        need(m.get('name',m.get('model'))==MODEL,'別のモデルが読み込み中です。新しいモデルのロードはしません')
    return record


def check_model():
    _,tags=local_api('/api/tags')
    xs=[m for m in tags.get('models',[]) if m.get('name',m.get('model'))==MODEL]
    need(len(xs)==1,'指定したローカルQwenがAPI一覧にありません。pullは実行しません')
    need(xs[0].get('digest','').removeprefix('sha256:')==DIGEST,'API上のモデルdigestが異なります')
    raw,show=local_api('/api/show',{'model':MODEL})
    need(not show.get('remote_host') and not show.get('remote_model'),'クラウドモデルは使えません')
    need(show.get('model_info',{}).get('general.architecture')=='qwen2','モデルの系列が異なります')
    need(show['model_info'].get('qwen2.context_length',0)>=CTX,'モデルの文脈長が不足しています')
    details=show.get('details',{})
    need(details.get('quantization_level')=='Q4_K_M','量子化方式が異なります')
    pc=show.get('model_info',{}).get('general.parameter_count',0)
    need(isinstance(pc,(int,float)) and 30_000_000_000<=pc<=35_000_000_000,'32Bモデルではありません')
    return raw,show


def request(source, form):
    text=CHAT.format(system=SYSTEM,prompt=prompt(source,form))
    need('<|im_start|>' not in source and '<|im_end|>' not in source,'入力コード中に予約トークンがあります')
    upper=len(text.encode('utf-8'))+32
    need(upper+CAPS[form]<=CTX,
         f'{form}: 入力の保守的上界{upper}+出力上限{CAPS[form]}が文脈長{CTX}を超えます。切り詰めず停止します')
    body={'model':MODEL,'prompt':text,'raw':True,'stream':False,
          'keep_alive':'5m' if form=='C' else 0,
          'options':{'num_ctx':CTX,'num_predict':CAPS[form],'num_gpu':0,
              'num_thread':16,'num_batch':512,'temperature':0.2,'seed':65001,
              'top_k':40,'top_p':0.9,'min_p':0.0,'repeat_penalty':1.0,
              'repeat_last_n':64,'num_keep':4,'stop':['<|im_end|>','<|endoftext|>']}}
    return body,upper


def parse_generation(obj,form,upper):
    need(obj.get('model')==MODEL,'応答のモデル名が異なります')
    need(obj.get('done') is True,'生成が完了していません')
    need(obj.get('done_reason')=='stop','出力打切りまたは不明な終了理由: '+str(obj.get('done_reason')))
    ti,to=obj.get('prompt_eval_count'),obj.get('eval_count')
    need(type(ti) is int and 0<ti<=upper,'入力トークン数が不明または上界を超えました')
    need(type(to) is int and 0<to<CAPS[form],'出力上限到達または出力トークン数が不明')
    need(ti+to<=CTX,'入出力が文脈長を超えました')
    need(not obj.get('thinking'),'想定外の推論出力があります')
    text=obj.get('response')
    need(isinstance(text,str) and text.strip(),'空の生成結果です')
    code,norm=extract_code(text,form)
    duration=obj.get('eval_duration')
    rate=(to*1e9/duration if isinstance(duration,(int,float)) and duration>0 else None)
    return code,{'input_tokens':ti,'output_tokens':to,'normalization':norm,
                 'eval_duration_ns':duration,'output_tokens_per_second':rate,
                 'load_duration_ns':obj.get('load_duration'),
                 'prompt_eval_duration_ns':obj.get('prompt_eval_duration'),
                 'correctness_validated':False,'code_execution':False}


def generate(repo,gate):
    need(os.geteuid()!=0,'専用の一般ユーザーで実行してください。root実行はしません')
    repo=Path(repo).resolve()
    need(repo.is_dir(),'リポジトリがありません')
    inputs,evidence=gate_evidence(repo,gate)
    requests={f:request(inputs[f],f) for f in ('C','IR')}
    out=repo/'runs/goal0067-server-open-codegen/gemm-mini-qwen32b-v1'
    if out.exists():
        if (out/'summary.json').is_file():
            print('既存の実行記録があります。自動再生成はしません。')
            old=load(out/'summary.json');print(json.dumps(old,ensure_ascii=False,indent=2));print('保存先:',out)
            return 0 if old.get('completion')=='QWEN32_CODEGEN_SMOKE_COMPLETE' else 1
        raise Problem('途中の実行記録があります。自動再送せず停止します: '+str(out))
    out.mkdir(parents=True);os.chmod(out,0o700)
    write(out/'tool-source.py',Path(__file__).read_bytes())
    summary={'revision':REVISION,'model':MODEL,'model_digest':DIGEST,
      'requests_planned':2,'local_generation_attempts':0,'text_candidates_saved':0,
      'external_model_api_calls':0,'model_downloads':0,'automatic_retries':0,
      'code_compilations':0,'code_executions':0,'correctness_validated':False,
      'performance_measurements':0,'scope':'development only / gemm MINI / C and LLVM IR / P0',
      'evidence':evidence,'errors':[],'run_directory':str(out)}
    started=False
    try:
        print('32Bモデルのファイルと取得時ハッシュを確認中...',flush=True)
        models=Path.home()/'.local/share/cpucond-ollama/models'
        weights=verify_local_weights(models);jwrite(out/'local-weights.json',weights)
        srv=ensure_server(out,models);jwrite(out/'server-evidence.json',srv)
        raw,show=check_model();write(out/'model-show.json',raw)
        jwrite(out/'generation-settings.json',{'context_length':CTX,'output_caps':CAPS,
           'context_bound':'UTF8 byte bound for fixed byte-level Qwen tokenizer plus 32 reserved tokens',
           'input_bounds':{f:requests[f][1] for f in requests},'seed':65001,
           'seed_is_not_a_cross_runtime_reproducibility_guarantee':True,
           'tool_sha256':file_sha(Path(__file__))})
        for form in ('C','IR'):
            d=out/form;d.mkdir()
            body,upper=requests[form]
            jwrite(d/'request.json',body);write(d/'input-source.txt',inputs[form])
            check_model()
            jwrite(d/'started.json',{'utc':now(),'request_sha256':file_sha(d/'request.json')})
            summary['local_generation_attempts']+=1;started=True
            print(f'{form}: コードを生成中（サーバーCPU、上限{CAPS[form]}トークン）...',flush=True)
            raw,obj=local_api('/api/generate',body,timeout=1800)
            write(d/'response.raw.json',raw)
            if isinstance(obj.get('response'),str):write(d/'response.txt',obj['response'])
            check_model()
            code,receipt=parse_generation(obj,form,upper)
            write(d/('candidate.c' if form=='C' else 'candidate.ll'),code)
            jwrite(d/'receipt.json',receipt)
            summary['text_candidates_saved']+=1
            summary.setdefault('generation_statistics',{})[form]=receipt
            print(f'{form}: 保存完了 入力={receipt["input_tokens"]} 出力={receipt["output_tokens"]}（未検証）',flush=True)
        summary['completion']='QWEN32_CODEGEN_SMOKE_COMPLETE'
    except Exception as e:
        summary['completion']='QWEN32_CODEGEN_STOPPED'
        summary['errors'].append(type(e).__name__+': '+str(e))
    finally:
        if started:
            try:
                raw,_=local_api('/api/generate',{'model':MODEL,'keep_alive':0},timeout=60)
                write(out/'unload-response.json',raw)
            except Exception as e:
                summary['unload_warning']=type(e).__name__+': '+str(e)
        summary['finished_utc']=now();jwrite(out/'summary.json',summary);hashes(out)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print(summary['completion']);print('保存先:',out)
    return 0 if not summary['errors'] else 1


class Tests(unittest.TestCase):
    C='void kernel_gemm(int n) { }\n'
    IR='define void @kernel_gemm(i32 %n) {\n ret void\n}\n'
    def fixture(self, root):
        repo = root/'repo'; prep = repo/'runs/goal0063-codegen-gate-prep/fixture'; pkg = prep/'package'
        item = {'task':'gemm','size':'MINI','sources':{}}
        for form, ext, text in [('C','c',self.C),('IR','ll',self.IR)]:
            rel='inputs/gemm/MINI/kernel.'+ext
            write(pkg/rel,text)
            item['sources'][form]={'path':rel,'sha256':sha(text.encode())}
        pi={'tool_sha256':GATE_SHA,'revision':'codegen-development-gate-v1','items':[item]}
        jwrite(pkg/'package.json',pi); hashes(pkg)
        write(repo/'runs/goal0063-latest-package.txt',str(prep)+'\n')
        evidence = root/'gate-records'
        sm={'completion':'CODEGEN_DEV_GATE_COMPLETE','instances_planned':18,'instances_completed':18,
            'instances_passed':18,'positive_checks':1512,'positive_passed':1512,
            'negative_checks':132,'negative_detected':132,'api_calls':0,'performance_measurements':0,'errors':[]}
        pr={'tool_sha256':GATE_SHA,'executions_are_known_reference_and_controls_only':True,
            'host':{'cpu_model':'AMD EPYC 7402 24-Core Processor'},'compiler':'Ubuntu clang version 18.1.3',
            'package_manifest_sha256':file_sha(pkg/'package.json')}
        jwrite(evidence/'summary.json',sm);jwrite(evidence/'provenance.json',pr);hashes(evidence)
        return repo,evidence
    def test_two_local_generations_end_to_end(self):
        import io
        from contextlib import redirect_stdout
        calls=[]
        def fake_api(path,payload=None,timeout=15):
            calls.append((path,payload))
            code=self.IR if 'LLVM 18' in payload.get('prompt','') else self.C
            obj=self.response(code) if payload.get('prompt') else {'done':True}
            return encoded(obj),obj
        with tempfile.TemporaryDirectory() as t,redirect_stdout(io.StringIO()):
            repo,gate=self.fixture(Path(t))
            with patch('os.geteuid',return_value=1000),patch(__name__+'.verify_local_weights',return_value={}),patch(__name__+'.ensure_server',return_value={}),patch(__name__+'.check_model',return_value=(b'{}',{})),patch(__name__+'.local_api',side_effect=fake_api):
                self.assertEqual(generate(repo,gate),0)
                self.assertEqual(generate(repo,gate),0)
            self.assertEqual(len([p for _,p in calls if p.get('prompt')]),2)
            out=repo/'runs/goal0067-server-open-codegen/gemm-mini-qwen32b-v1'
            self.assertEqual(load(out/'summary.json')['text_candidates_saved'],2)
            self.assertTrue((out/'IR/candidate.ll').is_file())
            self.assertEqual(file_sha(out/'C/candidate.c'),manifest(out)['C/candidate.c'])
    def test_timeout_not_resent(self):
        import io
        from contextlib import redirect_stdout
        calls=[]
        def fake_api(path,payload=None,timeout=15):
            if payload.get('prompt'):
                calls.append(payload)
                raise TimeoutError('synthetic timeout')
            return b'{"done":true}',{'done':True}
        with tempfile.TemporaryDirectory() as t,redirect_stdout(io.StringIO()):
            repo,gate=self.fixture(Path(t))
            with patch('os.geteuid',return_value=1000),patch(__name__+'.verify_local_weights',return_value={}),patch(__name__+'.ensure_server',return_value={}),patch(__name__+'.check_model',return_value=(b'{}',{})),patch(__name__+'.local_api',side_effect=fake_api):
                self.assertEqual(generate(repo,gate),1)
                self.assertEqual(generate(repo,gate),1)
            self.assertEqual(len(calls),1)
            summary=load(repo/'runs/goal0067-server-open-codegen/gemm-mini-qwen32b-v1/summary.json')
            self.assertEqual(summary['text_candidates_saved'],0)
    def test_tampered_verified_input_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            repo,gate=self.fixture(Path(t))
            pkg=Path((repo/'runs/goal0063-latest-package.txt').read_text().strip())/'package'
            (pkg/'inputs/gemm/MINI/kernel.c').write_text('tampered')
            with self.assertRaises(Problem):gate_evidence(repo,gate)
    def response(self,code):
        return {'model':MODEL,'done':True,'done_reason':'stop','prompt_eval_count':100,'eval_count':50,'response':code}
    def test_duplicate_json(self):
        with self.assertRaises(Problem):loads('{"x":1,"x":2}')
    def test_nan_json(self):
        with self.assertRaises(Problem):loads('{"x":NaN}')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'x';write(p,'x')
            with self.assertRaises(FileExistsError):write(p,'y')
    def test_loopback_only(self):
        with self.assertRaises(ValueError):_endpoint('https://example.org:443')
    def test_cloud_endpoint_rejected(self):
        with self.assertRaises(ValueError):_endpoint('http://192.0.2.1:11434')
    def test_bad_path(self):
        with self.assertRaises(Problem):safe('/tmp','../x')
    def test_request_is_generation(self):
        b,u=request(self.C,'C');self.assertNotIn('format',b);self.assertNotIn('tools',b)
        self.assertNotIn('candidate_id',b['prompt']);self.assertEqual(b['options']['num_gpu'],0)
        self.assertEqual(b['options']['num_ctx'],32768);self.assertLess(u+CAPS['C'],CTX)
    def test_long_input_stops(self):
        with self.assertRaises(Problem):request('x'*50000,'IR')
    def test_special_tokens_stop(self):
        with self.assertRaises(Problem):request('<|im_start|>','C')
    def test_parse_c(self):
        self.assertEqual(parse_generation(self.response(self.C),'C',200)[0],self.C)
    def test_parse_ir(self):
        self.assertEqual(parse_generation(self.response('```llvm\n'+self.IR+'```'),'IR',200)[0],self.IR)
    def test_truncation(self):
        x=self.response(self.C);x['done_reason']='length'
        with self.assertRaises(Problem):parse_generation(x,'C',200)
    def test_model_mismatch(self):
        x=self.response(self.C);x['model']='other'
        with self.assertRaises(Problem):parse_generation(x,'C',200)
    def test_no_usage(self):
        x=self.response(self.C);del x['prompt_eval_count']
        with self.assertRaises(Problem):parse_generation(x,'C',200)
    def test_candidate_id_not_code(self):
        with self.assertRaises(Problem):extract_code('{"candidate_id":"identity"}','C')
    def test_local_api_path_allowlist(self):
        with self.assertRaises(Problem):local_api('/api/pull',{})
    def test_no_generation_on_existing_result(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as t,redirect_stdout(io.StringIO()):
            p=Path(t);out=p/'runs/goal0067-server-open-codegen/gemm-mini-qwen32b-v1'
            jwrite(out/'summary.json',{'completion':'QWEN32_CODEGEN_SMOKE_COMPLETE'})
            with patch(__name__+'.gate_evidence',return_value=({'C':self.C,'IR':self.IR},{})),patch('os.geteuid',return_value=1000),patch(__name__+'.local_api') as net:
                self.assertEqual(generate(p,p),0);net.assert_not_called()
    def test_hash_manifest(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);write(p/'x','x');hashes(p);self.assertEqual(manifest(p)['x'],sha(b'x'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test',action='store_true')
    group.add_argument('--generate',action='store_true')
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--gate-records',type=Path)
    ap.add_argument('--model-freeze',type=Path)
    args=ap.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    gate=args.gate_records or args.repo/'external-results/zen2-2x-epyc-7402/goal0063-dev-gate'
    try:
        global DIGEST
        need(args.model_freeze is not None,'--model-freezeが必要です')
        lock=load(args.model_freeze)
        need(lock.get('model')==MODEL,'取得記録のモデルが異なります')
        digest=lock.get('manifest_sha256','')
        need(re.fullmatch(r'[0-9a-f]{64}',digest) is not None,'取得記録のハッシュが不正です')
        need(digest.startswith('b92d6a0bd47e'),'公式タグで確認したハッシュ接頭辞と異なります')
        need(lock.get('phase')=='after_download_before_generation','モデル固定の段階が不正です')
        DIGEST=digest
        return generate(args.repo,gate)
    except Exception as e:
        print('停止:',type(e).__name__+': '+str(e),file=sys.stderr);return 1

if __name__=='__main__':
    raise SystemExit(main())
