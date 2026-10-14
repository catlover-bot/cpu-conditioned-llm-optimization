#!/usr/bin/env python3
"""PolyBench 30x3 の直接C/LLVM IR生成・共通検証・暫定計測。

第1波=全90条件 x C/IR x P0 x 1試行 (180要求)。固定キューを再開可能。
固定候補選択/特定生成コードとの文字列照合にはしない。
公式入力の全出力比較は全30課題、追加の全状態14入力は既存6課題のみ。
24課題の追加検証を実装済みと偽らない。計測は常に provisional と記録。
LLM生成と検証/計測は時間的に分離する。未知コードはbwrap内のみで実行。
有料API、モデル取得、既存データの変更、サーバー契約の操作は行わない。
"""
from __future__ import annotations
import argparse, csv, fcntl, hashlib, http.client, importlib.util, json, math, os
from pathlib import Path, PurePosixPath
import pwd, random, re, resource, shutil, signal, socket, statistics, subprocess, sys
import tarfile, tempfile, time, unittest, uuid
from datetime import datetime, timezone

REV='polybench-direct-codegen-batch-wave1-v1'
MODEL='qwen2.5-coder:32b-instruct-q4_K_M'
RUNTIME_SHA='7deaad14177b824d8fcff7136d4418c0111d2db35fa872a5071fa8db5b8db527'
VENDORS={'roundtrip_support.py':'caae960ddf1c919eb24c14ab55b85e9b35d351b966c1acf485816c31a88ff886',
 'stress_support.py':'809819e965bb7ec80487d4fb65c5313e1b00e4378ced059fd36d9e1bef22ee8e',
 'model_support.py':'28e86abfaac3492690d11f3353983e94e13d3a83a1e08ca55bb2836d52904e23'}
CANDIDATE_SHA='a6c6423984aab7a26f90b86aab36ab3962fd208fb6f977ad068b80d4fc31c7a1'
INTAKE='runs/goal0041-dataset-intake/20260910T132522.441454Z-69857bdb'
SIZES=('MINI','SMALL','MEDIUM')
HOME=Path('/var/lib/cpucond-infer')
ACCOUNT='cpucond-infer'
SERVICE_PORT=11469
CTX=32768
CAPS={'C':4096,'IR':8192}
SEED=69001
STRICT=['-fno-fast-math','-ffp-contract=off','-fno-lto']
GENERIC=['--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic']
NATIVE=['--target=x86_64-unknown-linux-gnu','-march=native']
MAX_OUT=64*1024*1024
MAX_ITEM_SECONDS=1800

class Blocked(RuntimeError):pass
class CandidateFailure(RuntimeError):pass
class BudgetPause(RuntimeError):pass

def need(x,msg):
    if not x:raise Blocked(msg)
def now():return datetime.now(timezone.utc).isoformat()
def shab(b):return hashlib.sha256(b).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def pairs(xs):
    d={}
    for k,v in xs:
        need(k not in d,'JSONキー重複: '+k);d[k]=v
    return d
def loads(b):
    def bad(s):raise Blocked('不正なJSON数値: '+s)
    return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def load(p):
    p=Path(p);need(p.is_file() and not p.is_symlink() and p.stat().st_size<MAX_OUT,'ファイル欠落/過大/リンク: '+str(p))
    return loads(p.read_bytes())
def enc(x):return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def write(p,b):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(b,str):b=b.encode()
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def jw(p,x):write(p,enc(x))
def atomic(p,x):
    p=Path(p);q=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex);write(q,enc(x));q.replace(p)
def safe(root,rel):
    q=PurePosixPath(rel)
    need(q.parts and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,'不正パス: '+rel)
    root=Path(root).resolve();p=root/Path(*q.parts)
    need(root in p.resolve().parents,'パス範囲外')
    for ancestor in [p,*p.parents]:
        if ancestor==root:break
        need(not ancestor.is_symlink(),'シンボリックリンクを拒否')
    need(p.is_file(),'ファイル欠落: '+str(p));return p

def hm(root):
    d={}
    for ln in (Path(root)/'SHA256SUMS').read_text().splitlines():
        h,sep,n=ln.partition('  ');n=n.removeprefix('./')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and n not in d,'ハッシュ一覧不正');d[n]=h
    return d

def seal(root):
    xs=[]
    for p in sorted(Path(root).rglob('*')):
        need(not p.is_symlink(),'結果にリンクがあります')
        if p.is_file() and p.name!='SHA256SUMS':xs.append(f'{sha(p)}  {p.relative_to(root).as_posix()}\n')
    write(Path(root)/'SHA256SUMS',''.join(xs))

def vendor(name):
    p=Path(__file__).resolve().with_name(name)
    need(sha(p)==VENDORS[name],'同梱コードのハッシュ不一致: '+name)
    spec=importlib.util.spec_from_file_location('_batch_'+name.replace('.','_'),p)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m
    old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:spec.loader.exec_module(m)
    finally:sys.dont_write_bytecode=old
    return m


def prompt(source,form,task,size,stress_domain=None):
    domain=stress_domain or '元の計算が定義される入力を対象とし、元コードの型・寸法・式・依存順序・条件分岐を維持する。'
    return f'''数値計算関数を直接書き換え、結果を厳密に保って高速化してください。候補IDの選択ではありません。
対象関数: kernel_{task.replace('-', '_')}
出力: {'Cの完全なコンパイル単位' if form=='C' else 'LLVM 18の完全なテキストモジュール'}
CPU固有の型番・性能情報は追加しません。この条件はP0です。
ソースサイズの区分: {size}。実行時引数の寸法を区分名で固定しないでください。
コンパイラ: Clang 18.1.3。単一スレッド、-O3 -march=native -fno-fast-math -ffp-contract=off -fno-lto。
共通の契約:
- 計算関数の名前・引数の型/順序・呼出規約・既存の必要な型定義を保つ。
- 入力配列は元の別々の割当てどおり重ならない。元コードが変更しない配列を変更しない。
- 元コードで定義される出力・中間状態を保持。浮動小数点の式の括り方や加算順序を変えない。
- 最近接偶数丸め、符号付きゼロと非正規化数を保持。FMA、fast-math、近似、型の縮小は禁止。
- 境界/端数処理を保持。初期値・答えを埋め込まず、実行時の引数をそのまま使う。
- 入出力・ファイル・ネットワーク・時計・CPU識別・外部プロセス・グローバル実行フックを追加しない。
- インラインアセンブリ、CPU属性、別の外部計算ライブラリへの置換を追加しない。
- 対象関数の本文以外の実行フックやmainを作らない。内部の補助関数は外部依存を増やさない範囲に限る。
- LLVM中間表現の場合、必要な宣言・属性・メタデータを残す。C形式で回答しない。
追加契約: {domain}
理由・JSON・Markdownを付けず、完全なコードのみ返す。正しい改善が見つからない場合は未変更コードを返す。
----- 元コード -----
{source.rstrip()}
----- 元コード終わり -----
'''

def request_for(source,form,task,size,domain=None):
    m=vendor('model_support.py')
    text=m.CHAT.format(system=m.SYSTEM,prompt=prompt(source,form,task,size,domain))
    need('<|im_start|>' not in source and '<|im_end|>' not in source,'入力に予約トークン')
    upper=len(text.encode())+32
    payload={'model':MODEL,'prompt':text,'raw':True,'stream':False,'keep_alive':'30m',
      'options':{'num_ctx':CTX,'num_predict':CAPS[form],'num_gpu':0,'num_thread':16,
       'num_batch':512,'temperature':0.2,'seed':SEED,'top_k':40,'top_p':0.9,'min_p':0.0,
       'repeat_penalty':1.0,'repeat_last_n':64,'num_keep':4,'stop':['<|im_end|>','<|endoftext|>']}}
    return payload,upper

def extract_response(obj,item):
    need(obj.get('model')==MODEL and obj.get('done') is True,'生成応答が未完/別モデル')
    need(obj.get('done_reason')=='stop','出力打切り/異常終了: '+str(obj.get('done_reason')))
    ti,to=obj.get('prompt_eval_count'),obj.get('eval_count');form=item['form']
    need(type(ti) is int and 0<ti<=item['input_byte_upper'],'入力長の検査失敗')
    need(type(to) is int and 0<to<CAPS[form] and ti+to<=CTX,'出力上限/文脈長の検査失敗')
    raw=obj.get('response');need(isinstance(raw,str) and raw.strip(),'空の応答')
    s=raw.strip();normal='none'
    match=re.fullmatch(r'```(?:c|C|llvm|LLVM|ir|IR)?[ \t]*\n(.*?)\n```',s,re.S)
    if match:s=match[1];normal='outer_markdown_fence_removed'
    need('```' not in s and '\x00' not in s,'回答形式不正')
    name='kernel_'+item['task'].replace('-','_')
    need(re.search(r'\b'+re.escape(name)+r'\s*\(',s) if form=='C' else re.search(r'^define\b[^\n]*@'+re.escape(name)+r'\(',s,re.M),'対象関数がない')
    duration=obj.get('eval_duration',0)
    return s.rstrip()+'\n',{'input_tokens':ti,'output_tokens':to,'normalization':normal,
       'output_tokens_per_second':to*1e9/duration if isinstance(duration,(int,float)) and duration>0 else None,
       'correctness_validated':False,'performance_measured':False}


def make_task_id(task,size,form):return f'{task}__{size}__{form}__P0__s0'


def prepare(repo,rt):
    repo=Path(repo).resolve();rt=Path(rt).resolve();g=vendor('stress_support.py')
    hashes=hm(rt)
    for n in ('summary.json','manifest.json','provenance.json','tool-source.py','input-snapshots.json'):
        need(sha(safe(rt,n))==hashes.get(n),'往復確認ファイルのハッシュ不一致: '+n)
    summary=load(rt/'summary.json');man=load(rt/'manifest.json')
    need(summary.get('completion')=='CODEGEN_ROUNDTRIP_COMPLETE' and summary.get('instances_passed')==90,'90条件の往復確認が未完了')
    need(sha(rt/'tool-source.py')==VENDORS['roundtrip_support.py'],'往復確認器の版が違う')
    need(sha(repo/'configs/final-candidate-manifest-v1.json')==CANDIDATE_SHA,'元課題集合が変更されています')
    entries=load(repo/'configs/final-candidate-manifest-v1.json')['kernels']
    source_keys={(x['kernel'],x['size']) for x in man['rows']}
    need(source_keys=={(x['kernel_id'],s) for x in entries for s in SIZES} and len(man['rows'])==90,'90条件の組合せ不一致')
    rows={(x['kernel'],x['size']):x for x in man['rows']}
    pointer=repo/'runs/goal0069-latest-package.json'
    if pointer.exists():
        previous=load(pointer);old=Path(previous['directory'])
        need(repo in old.resolve().parents,'以前の準備場所が不正')
        need(sha(old/'cpucond-dataset-batch.tgz')==previous['sha256'],'保存済みパッケージが変更されています')
        oldplan=load(old/'package/plan.json')
        need(oldplan.get('revision')==REV and oldplan.get('source_roundtrip_manifest_sha256')==sha(rt/'manifest.json'),'別の入力/仕様のパッケージが既にあります')
        need(sha(old/'package/goal0069_batch_codegen.py')==sha(Path(__file__)),'準備済みコードと実行器が違います。自動置換しません')
        print('DATASET_BATCH_PACKAGE_REUSED');print('保存先:',old);return 0
    rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    out=repo/'runs/goal0069-batch-prep'/rid;pkg=out/'package';pkg.mkdir(parents=True,exist_ok=False)
    for name in ('goal0069_batch_codegen.py','server_launch.sh',*VENDORS):shutil.copyfile(Path(__file__).with_name(name),pkg/name)
    pb=repo/INTAKE/'upstream/polybench-c-4.2.1-beta'
    snaps=load(rt/'input-snapshots.json')['polybench']
    for n in ('utilities/polybench.c','utilities/polybench.h'):
        p=safe(pb,n);need(sha(p)==snaps[n],'元ユーティリティのハッシュ不一致');write(pkg/n,p.read_bytes())
    items=[];instances=[]
    # 入力の先行検査。以前のGEMM開発応答は本バッチに混ぜない。
    for size in SIZES:
        for e in sorted(entries,key=lambda x:x['kernel_id']):
            task=e['kernel_id'];row=rows[(task,size)]
            need(row.get('passed') is True,'未合格の元入力')
            inst={'task':task,'size':size,'function':e['function_name'],'sources':{},'loop_count':e['syntactic_loop_count']}
            for form,n,ext in [('C',row['c_input'],'c'),('IR',row['ir_input'],'ll')]:
                p=safe(rt,n);b=p.read_bytes();need(shab(b)==hashes.get(n),'元入力が変更されています')
                dest=f'inputs/{task}/{size}/kernel.{ext}';write(pkg/dest,b)
                inst['sources'][form]={'path':dest,'sha256':shab(b)}
            rel=f'cases/{task}/{size}/check/driver.c';p=safe(rt,rel)
            need(sha(p)==hashes.get(rel),'ドライバ不一致')
            dest=f'inputs/{task}/{size}/driver.c';write(pkg/dest,p.read_bytes());inst['driver']=dest
            rel=f'cases/{task}/{size}/check/run-reference-O0.stdout';p=safe(rt,rel)
            need(sha(p)==hashes.get(rel) and p.stat().st_size>0,'元の正解出力がない')
            dest=f'inputs/{task}/{size}/oracle.raw';write(pkg/dest,p.read_bytes());inst['oracle']=dest
            domain=g.contract(task)['domain'] if task in g.TASKS else None
            for form in ('C','IR'):
                tid=make_task_id(task,size,form);src=(pkg/inst['sources'][form]['path']).read_text()
                payload,upper=request_for(src,form,task,size,domain)
                path=f'requests/{tid}.json';jw(pkg/path,payload)
                items.append({'id':tid,'task':task,'size':size,'form':form,'condition':'P0','sample':0,'seed':SEED,
                   'request':path,'request_sha256':sha(pkg/path),'source':inst['sources'][form]['path'],
                   'input_byte_upper':upper,'context_budget_ok':upper+CAPS[form]<=CTX})
            instances.append(inst)
    plan={'revision':REV,'model':MODEL,'scope':'first dataset-wide direct-code-generation wave; not final multi-model multi-CPU-information factorial',
      'kernels':30,'instances':90,'requests':180,'representations':['C','IR'],'conditions':['P0'],'samples':1,
      'seed':SEED,'context_length':CTX,'output_caps':CAPS,'tasks':items,'instances_list':instances,
      'source_roundtrip_manifest_sha256':sha(rt/'manifest.json'),'source_compiler':load(rt/'provenance.json')['compiler'],
      'validation_scope':{'official_output':30,'additional_multiinput_fullstate':list(g.TASKS),
       'full_30_multinput_validator_complete':False,'formal_equivalence':False},
      'measurement_scope':'provisional single-host function time, fixed sources and flags; not final CPU-conditioning evidence',
      'queue_policy':'size-major, kernel name ascending, C then IR; fixed before batch outputs; failed attempts retained; no automatic model retry',
      'context_policy':'UTF8 conservative bound; over-budget requests are recorded not sent; never truncate input',
      'sampling_scope':'development for six previously used kernels; other kernels first-wave evaluation, not a held-out confirmatory claim',
      'performance_defaults':{'sessions':2,'pairs_per_session':8,'target_ms':5,'max_batch':16384,
         'ratio_rel_iqr':0.10,'identity_log_tolerance':math.log(1.02),'session_log_tolerance':math.log(1.03),
         'invalid':'keep all measurements; no selective timing retry'},
      'old_smoke_outputs_imported':False,'additional_calls_for_P1_P2':False,'paid_api_calls':0}
    jw(pkg/'plan.json',plan);seal(pkg)
    archive=out/'cpucond-dataset-batch.tgz'
    with tarfile.open(archive,'w:gz') as tf:
        for p in sorted(pkg.rglob('*')):
            if p.is_file():tf.add(p,arcname=p.relative_to(pkg).as_posix(),recursive=False)
    write(out/'cpucond-dataset-batch.tgz.sha256',sha(archive)+'  cpucond-dataset-batch.tgz\n')
    atomic(repo/'runs/goal0069-latest-package.json',{'directory':str(out),'sha256':sha(archive),'plan_sha256':sha(pkg/'plan.json')})
    print('DATASET_BATCH_PACKAGE_READY',flush=True)
    print('全30課題×3サイズ×C/IR×CPU情報なし×1試行 = 180要求')
    print('文脈長の保守判定で送信不可:',sum(not x['context_budget_ok'] for x in items),'件（欠落として記録。省略して合格にしません）')
    print('保存先:',out);print('転送容量:',archive.stat().st_size,'bytes');return 0


def api(path,payload=None,timeout=20):
    need(path in {'/api/version','/api/tags','/api/show','/api/generate','/api/ps'},'ローカルAPIパス不正')
    c=http.client.HTTPConnection('127.0.0.1',SERVICE_PORT,timeout=timeout)
    try:
        b=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
        c.request('GET' if b is None else 'POST',path,body=b,headers={'Content-Type':'application/json'})
        r=c.getresponse();raw=r.read(MAX_OUT+1);need(r.status==200 and len(raw)<=MAX_OUT,'ローカルAPIの応答失敗/過大')
        return raw,loads(raw)
    finally:c.close()

def env():return {'PATH':'/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','LC_ALL':'C.UTF-8','LANG':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}

def stop(p):
    if p is None:return
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=10)

def model_state():
    account=pwd.getpwnam(ACCOUNT);need(account.pw_uid!=0 and account.pw_dir==str(HOME),'専用推論ユーザー不一致')
    binary=HOME/'.local/opt/ollama-0.33.3/bin/ollama';need(sha(binary)==RUNTIME_SHA,'固定Ollamaがない/変更。ダウンロードはしません')
    freeze=load(HOME/'goal0067/repo/model-freeze.json')
    mf=HOME/'.local/share/cpucond-ollama/models/manifests/registry.ollama.ai/library/qwen2.5-coder/32b-instruct-q4_K_M'
    need(sha(mf)==freeze['manifest_sha256'] and freeze['model']==MODEL,'固定モデルmanifest不一致')
    m=vendor('model_support.py');m.DIGEST=freeze['manifest_sha256']
    print('既存32Bモデルのファイルを確認（再ダウンロードなし）...',flush=True)
    blobs=m.verify_local_weights(HOME/'.local/share/cpucond-ollama/models')
    return account,binary,freeze,blobs

def model_command(binary):
    return ['runuser','-u',ACCOUNT,'--','env','-i',f'HOME={HOME}','PATH=/usr/bin:/bin',
      'LC_ALL=C.UTF-8','OLLAMA_NO_CLOUD=1',f'OLLAMA_HOST=127.0.0.1:{SERVICE_PORT}',
      f'OLLAMA_MODELS={HOME}/.local/share/cpucond-ollama/models','OLLAMA_NUM_PARALLEL=1',
      'OLLAMA_MAX_LOADED_MODELS=1','OLLAMA_CONTEXT_LENGTH=32768',
      'numactl','--physcpubind=2-17','--membind=0',str(binary),'serve']

def check_busy():
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:args=(p/'cmdline').read_bytes().split(b'\0')
        except (OSError,PermissionError):continue
        names={Path(a.decode(errors='replace')).name for a in args if a}
        if names & {'goal0054_final_physical_atlas.py','goal0067_qwen32_generator.py','goal0068_verify_reviewed_qwen32_c.py'}:found.append(p.name)
        if any(n=='ollama' for n in names) and any(a in (b'serve',b'runner') for a in args):found.append(p.name)
    need(not found,'別の生成/計測/検証が実行中です。終了後に同じコマンドで再開: '+','.join(found))


def results_summary(plan,run):
    gs={};vs={};ms={}
    for t in plan['tasks']:
        d=run/'generation'/t['id']
        if (d/'result.json').exists():gs[t['id']]=load(d/'result.json')
        v=run/'validation'/t['id']/'result.json'
        if v.exists():vs[t['id']]=load(v)
        z=run/'measurement'/t['id']/'result.json'
        if z.exists():ms[t['id']]=load(z)
    return {'revision':REV,'planned_requests':180,'generation_terminal':len(gs),
       'generated_texts':sum(x.get('status')=='saved' for x in gs.values()),
       'generation_non_success':sum(x.get('status')!='saved' for x in gs.values()),
       'requests_pending':180-len(gs),'validation_terminal':len(vs),
       'official_gate_passed':sum(x.get('official_all_passed',False) for x in vs.values()),
       'additional_multiinput_passed':sum(x.get('multiinput_status')=='passed' for x in vs.values()),
       'additional_multiinput_not_implemented':sum(x.get('multiinput_status')=='not_implemented_for_task' for x in vs.values()),
       'measurement_eligible_provisional':sum(x.get('measurement_eligible_provisional',False) for x in vs.values()),
       'measurement_pending':sum(x.get('measurement_eligible_provisional',False) and k not in ms for k,x in vs.items()),
       'measurement_terminal':len(ms),'measurement_quality_passed':sum(x.get('measurement_valid',False) for x in ms.values()),
       'all_30_multinput_validation_complete':False,'final_research_conclusions_ready':False,
       'cpu_information_effect_measured':False,'scope':'P0, one model, one trial, first full-dataset wave, provisional',
       'paid_api_calls':0,'model_downloads':0,'automatic_model_retries':0,'formal_equivalence_proven':False,'updated_utc':now()}

def generation_phase(pkg,plan,run,deadline,freeze,binary):
    service=None
    try:
        with socket.socket() as s:need(s.connect_ex(('127.0.0.1',SERVICE_PORT))!=0,'一括生成ポートが使用中')
        log=(run/'sessions'/('ollama-'+uuid.uuid4().hex[:8]+'.log')).open('xb')
        service=subprocess.Popen(model_command(binary),env=env(),stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True);log.close()
        for _ in range(120):
            need(service.poll() is None,'Ollama起動失敗')
            try:
                _,o=api('/api/version',timeout=2)
                if o.get('version')=='0.33.3':break
                raise Blocked('Ollamaの版不一致')
            except (ConnectionError,TimeoutError,OSError):time.sleep(.5)
        else:raise Blocked('Ollamaに接続できません')
        _,tags=api('/api/tags');same=[x for x in tags.get('models',[]) if x.get('name',x.get('model'))==MODEL]
        need(len(same)==1 and same[0]['digest'].removeprefix('sha256:')==freeze['manifest_sha256'],'API上のモデルが固定値と異なる')
        _,show=api('/api/show',{'model':MODEL})
        need(not show.get('remote_host') and not show.get('remote_model'),'クラウドモデルは禁止')
        need(show.get('model_info',{}).get('qwen2.context_length',0)>=CTX,'文脈長未対応')
        for index,item in enumerate(plan['tasks'],1):
            d=run/'generation'/item['id']
            if (d/'result.json').is_file():continue
            d.mkdir(parents=True,exist_ok=True)
            if (d/'started.json').exists() and not (d/'response.raw.json').exists():
                jw(d/'result.json',{'status':'interrupted_unknown_response','automatic_retry':False,'utc':now()});continue
            if not item['context_budget_ok']:
                jw(d/'result.json',{'status':'input_budget_excluded','input_byte_upper':item['input_byte_upper'],'automatic_retry':False});continue
            response=d/'response.raw.json'
            if not response.exists():
                if time.monotonic()+MAX_ITEM_SECONDS+30>deadline:break
                payload=load(safe(pkg,item['request']));need(sha(pkg/item['request'])==item['request_sha256'],'要求ファイル改変')
                if not (d/'request.json').exists():jw(d/'request.json',payload)
                jw(d/'started.json',{'utc':now(),'request_sha256':item['request_sha256'],'model_digest':freeze['manifest_sha256']})
                print(f'生成 {index}/180 {item["task"]}/{item["size"]}/{item["form"]}',flush=True)
                try:
                    raw,obj=api('/api/generate',payload,timeout=MAX_ITEM_SECONDS)
                    write(response,raw)
                except Exception as exc:
                    jw(d/'result.json',{'status':'generation_transport_failure','error':type(exc).__name__+':'+str(exc),
                      'automatic_retry':False,'utc':now()})
                    atomic(run/'progress.json',results_summary(plan,run));break
            else:obj=load(response)
            try:
                code,receipt=extract_response(obj,item)
                dest=d/('candidate.c' if item['form']=='C' else 'candidate.ll')
                if dest.exists():need(dest.read_text()==code,'保存コードが応答と異なる')
                else:write(dest,code)
                jw(d/'result.json',{'status':'saved','code_sha256':sha(dest),'receipt':receipt,'utc':now()})
                print('  保存済み（未検証） 出力=',receipt['output_tokens'],flush=True)
            except Exception as exc:
                jw(d/'result.json',{'status':'invalid_generation','error':type(exc).__name__+':'+str(exc),'utc':now()})
            atomic(run/'progress.json',results_summary(plan,run))
    finally:
        # 自分が起動したサービスだけを終了。既存の他ジョブを停止しない。
        stop(service)
    print('推論サービス停止。ここから共通検証と暫定計測に移ります。',flush=True)


class Sandbox:
    """個々のコンパイル/実行を別のmount,pid,net名前空間で行う。
    出力比較・参照出力ファイルはホストのroot親のみが持つ。
    候補実行時はソース/正解/結果DBをマウントしない。
    """
    def __init__(self,root,deadline=None):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.counter=0
        self.deadline=deadline
        # 親systemd unitで96GiB・256tasksを強制。子を別cgroupへ移さない。
        # RuntimeMaxSecによる全子プロセス停止から逃れない配置にする。
        unit=os.environ.get('CPUCOND_BATCH_UNIT','')
        need(re.fullmatch(r'cpucond69-[A-Za-z0-9-]+\.service',unit) is not None,'systemdの管理下で起動してください')
        cgroup=Path('/proc/self/cgroup').read_text().strip().split('0::')[-1]
        need(unit in cgroup,'systemd unitのcgroupと実プロセスが異なります')
        cg=Path('/sys/fs/cgroup')/cgroup.lstrip('/')
        need((cg/'memory.max').read_text().strip()!='max','メモリ上限が設定されていません')
        need(int((cg/'memory.max').read_text())<=96*1024**3,'メモリ上限が96GiBを超えています')
        need(int((cg/'pids.max').read_text())<=256,'プロセス・スレッド数上限が256を超えています')
    def close(self):
        pass
    def argv(self,argv,inputs,scratch):
        a=['bwrap','--die-with-parent','--new-session','--unshare-pid','--unshare-net','--unshare-ipc','--unshare-uts',
           '--cap-drop','ALL','--cap-add','CAP_SETUID','--cap-add','CAP_SETGID','--clearenv',
           '--setenv','PATH','/usr/bin:/bin','--setenv','LC_ALL','C','--setenv','HOME','/tmp',
           '--setenv','TMPDIR','/tmp','--setenv','ASAN_OPTIONS','detect_leaks=0:halt_on_error=1',
           '--setenv','UBSAN_OPTIONS','halt_on_error=1:print_stacktrace=1',
           '--ro-bind','/usr','/usr']
        for p in ('/lib','/lib64','/bin','/sbin'):
            if Path(p).exists():a+=['--ro-bind',p,p]
        a+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/in','--dir','/out','--dir','/etc']
        for f in ('/etc/ld.so.cache','/etc/ld.so.conf'):
            if Path(f).is_file():a+=['--ro-bind',f,f]
        for name,p in inputs.items():
            need(re.fullmatch(r'[A-Za-z0-9_.-]+',name) is not None,'sandbox入力名不正')
            need(not Path(p).is_symlink() and Path(p).is_file(),'sandboxへ通常ファイル以外を渡せません')
            a+=['--ro-bind',str(Path(p).resolve()),'/in/'+name]
        if scratch:a+=['--bind',str(scratch.resolve()),'/out']
        # 名前空間とマウントの構築だけroot。固定の小さな起動片がuid/gidを
        # 落としてcapability=0を確認してから、コンパイラ/候補をexecする。
        # --uidはuser namespaceが必要なので、root bwrapでは使わない。
        drop=('import os,sys,ctypes;os.setgroups([]);os.setgid(65534);os.setuid(65534);'
              'libc=ctypes.CDLL(None);assert libc.prctl(38,1,0,0,0)==0;'
              'assert os.getuid()==65534;st=open("/proc/self/status").read();assert all(int(st.split(k+":")[1].split()[0],16)==0 for k in ("CapEff","CapPrm","CapInh","CapAmb"));'
              'os.execv(sys.argv[1],sys.argv[1:])')
        a+=['--chdir','/tmp','--','/usr/bin/python3','-I','-S','-c',drop,*map(str,argv)]
        return ['numactl','--physcpubind=2','--membind=0',*a]
    def call(self,argv,inputs,stem,timeout=60,output_names=()):
        if self.deadline is not None:
            remaining=self.deadline-time.monotonic()
            if remaining<5:raise BudgetPause('セッション時間上限')
            timeout=min(timeout,max(1,int(remaining)-2))
        stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
        self.counter+=1;scratch=None
        if output_names:
            scratch=self.root/('scratch-'+str(self.counter)+'-'+uuid.uuid4().hex[:8]);scratch.mkdir(mode=0o700)
            os.chown(scratch,65534,65534)
        a=self.argv(argv,inputs,scratch)
        def limit():
            os.sched_setaffinity(0,{2})
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            resource.setrlimit(resource.RLIMIT_CPU,(min(int(timeout)+5,300),min(int(timeout)+5,300)))
            resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_OUT,MAX_OUT))
            resource.setrlimit(resource.RLIMIT_NOFILE,(256,256))
            # cgroupはsystemd親unitを継承する。
        with stem.with_suffix('.stdout').open('xb') as so,stem.with_suffix('.stderr').open('xb') as se:
            proc=subprocess.Popen(a,env=env(),stdin=subprocess.DEVNULL,stdout=so,stderr=se,
                         start_new_session=True,preexec_fn=limit)
            try:rc=proc.wait(timeout=timeout);state='ok' if rc==0 else 'exit_nonzero'
            except subprocess.TimeoutExpired:stop(proc);rc=None;state='timeout'
        out={}
        if state=='ok' and scratch:
            for name in output_names:
                p=scratch/name
                if not p.is_file() or p.is_symlink() or p.stat().st_size>MAX_OUT:
                    state='invalid_compiler_output';break
                dest=stem.parent/(stem.name+'-'+name)
                fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
                with os.fdopen(fd,'rb') as f:write(dest,f.read(MAX_OUT+1))
                if name=='program':os.chmod(dest,0o755)
                out[name]=dest
        if scratch:
            shutil.rmtree(scratch)
        rec={'argv':list(map(str,argv)),'state':state,'returncode':rc,
             'network_isolated':True,'host_uid':65534,'scratch_only_writable':True,
             'cpu_affinity':[2],'memory_policy':'bind:0','session_memory_limit_bytes':96*1024**3,'timeout_s':timeout}
        jw(stem.with_suffix('.command.json'),rec)
        return rec,stem.with_suffix('.stdout').read_bytes(),out
    def preflight(self):
        script='import os,socket; assert os.getuid()==65534; assert not os.path.exists("/root"); assert not os.path.exists("/var/lib/cpucond-infer"); assert int(open("/proc/self/status").read().split("CapEff:")[1].split()[0],16)==0; print("SANDBOX_OK")'
        rec,raw,_=self.call(['/usr/bin/python3','-c',script],{},self.root/'sandbox-preflight',15)
        need(rec['state']=='ok' and raw.strip()==b'SANDBOX_OK','隔離の自己確認失敗。root実行にフォールバックしません')


def clang_path(strict=True):
    for name in ('clang-18','clang'):
        p=shutil.which(name)
        if p:
            v=subprocess.check_output([p,'--version'],text=True,timeout=10).splitlines()[0]
            if not strict or 'clang version 18.1.3' in v:
                return p,v
    raise Blocked('Clang 18.1.3が見つかりません')

def object_build(box,clang,src,stem,flags,sanitize_ir=False):
    src=Path(src)
    if sanitize_ir and src.suffix=='.ll':
        text=src.read_text()
        text,count=re.subn(r'^(define\b[^\n]*?)(\s*\{)\s*$',r'\1 sanitize_address\2',text,flags=re.M)
        if count<1:raise CandidateFailure('IRにサニタイザー対象関数を指定できません')
        patched=Path(stem).parent/(Path(stem).name+'-sanitized.ll');write(patched,text);src=patched
    inputs={'source.c' if src.suffix=='.c' else 'source.ll':src}
    name=next(iter(inputs))
    f=(['-std=gnu11'] if src.suffix=='.c' else [])+STRICT+flags
    rec,_,paths=box.call([clang,*f,'-c','/in/'+name,'-o','/out/result.o'],inputs,stem,120,('result.o',))
    if rec['state']!='ok':raise CandidateFailure('compile_'+rec['state'])
    return paths['result.o']

def link(box,clang,objects,stem,flags=()):
    inp={f'obj{i}.o':p for i,p in enumerate(objects)}
    rec,_,out=box.call([clang,*flags,*['/in/'+n for n in inp],'-lm','-o','/out/program'],inp,stem,120,('program',))
    if rec['state']!='ok':raise CandidateFailure('link_'+rec['state'])
    return out['program']

def execute_program(box,program,stem,args=(),extras=None,timeout=60):
    inputs={'program':program};inputs.update(extras or {})
    return box.call(['/in/program',*map(str,args)],inputs,stem,timeout)[:2]


def symbols_ok(box,obj,function,stem):
    rec,raw,_=box.call(['/usr/bin/nm','--extern-only','--defined-only','--format=posix','/in/kernel.o'],{'kernel.o':obj},stem,20)
    if rec['state']!='ok':raise CandidateFailure('symbol_scan_failed')
    symbols=[]
    for line in raw.decode('utf-8','strict').splitlines():
        parts=line.split()
        if len(parts)>=2:symbols.append(parts[0])
    if symbols!=[function]:raise CandidateFailure('unexpected_exported_symbols:'+','.join(symbols))


def statement_calls(s,name):
    r=vendor('roundtrip_support.py');m=r.mask_noncode(s);xs=[]
    for match in re.finditer(r'\b'+re.escape(name)+r'\s*\(',m):
        o=m.index('(',match.start());end=r.matching(m,o,'(',')');xs.append((match.start(),end+1,s[match.start():end+1]+';'))
    return xs

def main_bounds(s):
    r=vendor('roundtrip_support.py');m=r.mask_noncode(s);hits=[]
    for x in re.finditer(r'\bint\s+main\s*\(',m):
        o=m.index('(',x.start());e=r.matching(m,o,'(',')');b=e+1
        while b<len(m) and m[b].isspace():b+=1
        if b<len(m) and m[b]=='{':hits.append((x.start(),b,r.matching(m,b,'{','}')+1))
    need(len(hits)==1,'信頼済みドライバのmainが一意でない');return hits[0]

TIMER="""#include <time.h>
#include <stdlib.h>
unsigned long long cpucond69_clock(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC_RAW,&t))exit(92);return (unsigned long long)t.tv_sec*1000000000ULL+t.tv_nsec;}
"""


def timing_driver(driver,function):
    a,b,e=main_bounds(driver);main=driver[b+1:e-1]
    init=statement_calls(main,'init_array');kernel=statement_calls(main,function)
    need(len(init)==1 and len(kernel)==1,'初期化/対象関数呼出し不一致')
    prefix=main[:init[0][0]]
    free=statement_calls(main,'free')+statement_calls(main,'polybench_free_data')
    frees='\n'.join(x[2] for x in sorted(free))
    return 'extern unsigned long long cpucond69_clock(void);\n'+driver[:a]+'''int main(int argc,char **argv){
'''+prefix+'''
 if(argc!=2)return 64;char*ep=0;long K=strtol(argv[1],&ep,10);if(!ep||*ep||K<1||K>16384)return 65;
'''+init[0][2]+kernel[0][2]+'''
 unsigned long long cpucond69_total=0;
 for(long rr=0;rr<K;++rr){
'''+init[0][2]+'''
 __asm__ __volatile__("" ::: "memory");unsigned long long cpucond69_start=cpucond69_clock();
'''+kernel[0][2]+'''
 __asm__ __volatile__("" ::: "memory");unsigned long long cpucond69_finish=cpucond69_clock();if(cpucond69_finish<=cpucond69_start)return 66;cpucond69_total+=cpucond69_finish-cpucond69_start;
 }
 printf("CPUCOND_BATCH %ld %llu\\n",K,(unsigned long long)cpucond69_total);
'''+frees+'''\n return 0;\n}\n'''


def policy(source,form,function):
    # 不正な仕様追加を拒否する静的契約検査。安全性そのものは別の隔離で担保する。
    r=vendor('roundtrip_support.py')
    s=r.mask_noncode(source) if form=='C' else re.sub(r';[^\n]*','',source)
    forbidden=r'\b(?:system|popen|fork|vfork|execve|execvp|ptrace|syscall|dlopen|dlsym|fopen|freopen|printf|fprintf|fwrite|puts|socket|connect|clock_gettime|rdtsc|cpuid|fesetround|fesetenv|_mm_setcsr|__builtin_ia32_ldmxcsr|exit|_Exit|abort|fma|fmaf|fmal)\b'
    if re.search(forbidden,s):raise CandidateFailure('policy_forbidden_side_effect_or_intrinsic')
    if re.search(r'\b(?:asm|__asm__|__asm)\b|target-cpu|target-features|tune-cpu|llvm\.global_(?:ctors|dtors)|\bmain\s*\(',s):raise CandidateFailure('policy_hook_or_target_attribute')
    if 'cpucond69_' in s:raise CandidateFailure('policy_reserved_symbol')
    if form=='C':
        for line in s.splitlines():
            if line.lstrip().startswith('#include'):
                if not re.fullmatch(r'\s*#\s*include\s*<(math|stdint|stddef|stdbool|float|limits)\.h>\s*',line):raise CandidateFailure('policy_include')
        if re.search(r'__attribute__\s*\(\([^)]*(constructor|destructor|alias|ifunc|section|target)',s):raise CandidateFailure('policy_attribute')
        if re.search(r'pragma\s+(?:omp|GCC\s+optimize)|pragma\s+clang\s+fp\s+(?:reassociate|contract)\s*\(on',s):raise CandidateFailure('policy_fp_or_threading')
        r.function_span(source,function)
    else:
        if re.search(r'\b(?:fadd|fsub|fmul|fdiv|frem|fcmp|call)\s+(?:fast|reassoc|nnan|ninf|nsz|arcp|contract|afn)\b',s):raise CandidateFailure('policy_relaxed_fp')
        if re.search(r'@llvm\.(?:fma|fmuladd|x86.*fmadd)',s):raise CandidateFailure('policy_fma')
        if not re.search(r'^define\b[^\n]*@'+re.escape(function)+r'\(',s,re.M):raise CandidateFailure('policy_missing_function')


def abi_signature(fn):
    params=[x for x in fn.get('inner',[]) if x.get('kind')=='ParmVarDecl']
    result=[]
    mapping={p.get('name',''):f'arg{i}' for i,p in enumerate(params) if p.get('name')}
    for p in params:
        t=p['type'].get('desugaredQualType',p['type']['qualType'])
        for old,new in sorted(mapping.items(),key=lambda z:-len(z[0])):t=re.sub(r'\b'+re.escape(old)+r'\b',new,t)
        result.append(re.sub(r'\s+','',t))
    return result

def abi_c(box,clang,source,function,stem):
    rec,raw,_=box.call([clang,'-std=gnu11','-fsyntax-only','-Xclang','-ast-dump=json','-Xclang','-ast-dump-filter','-Xclang',function,'/in/source.c'],{'source.c':source},stem,60)
    if rec['state']!='ok':raise CandidateFailure('syntax_failed')
    fn=vendor('roundtrip_support.py').root_function(raw.decode(),function)
    if fn.get('storageClass')=='static' or not fn.get('type',{}).get('qualType','').startswith('void ('):raise CandidateFailure('function_linkage_or_return_changed')
    return abi_signature(fn)

def ir_abi(text,function):
    m=re.search(r'^define\b[^\n]*?\bvoid\s+@'+re.escape(function)+r'\((.*?)\)',text,re.M)
    if not m:raise CandidateFailure('ir_signature_not_found')
    args=vendor('roundtrip_support.py').split_args(m[1])
    return [a.strip().split()[0] for a in args if a.strip()]


def prepare_baseline(box,clang,pkg,inst,run):
    key=inst['task']+'__'+inst['size'];base=run/'baselines'/key
    if (base/'result.json').exists():return load(base/'result.json')
    if base.exists():base.rename(base.with_name(base.name+'.interrupted-'+uuid.uuid4().hex[:8]))
    base.mkdir(parents=True)
    src=pkg/inst['sources']['C']['path'];driver=pkg/inst['driver'];oracle=(pkg/inst['oracle']).read_bytes()
    # utilityを前処理して1ファイルにし、clangのinclude探索を隔離内に閉じる。
    u=base/'utility.i'
    rc,raw,_=box.call([clang,'-std=gnu11','-E','-P','-I/in','/in/polybench.c'],
       {'polybench.c':pkg/'utilities/polybench.c','polybench.h':pkg/'utilities/polybench.h'},base/'utility-preprocess',60)
    need(rc['state']=='ok','ユーティリティ前処理失敗');write(u,raw)
    # .c拡張子で明示し、通常のCコンパイルへ渡す。
    uc=base/'utility.c';write(uc,raw)
    util=object_build(box,clang,uc,base/'utility',['-O0',*GENERIC])
    archived_oracle=oracle
    objects={};checks=[]
    abi=abi_c(box,clang,src,inst['function'],base/'reference-abi')
    for label,flags in [('O0',['-O0',*GENERIC]),('generic',['-O3',*GENERIC]),('native',['-O3',*NATIVE]),
                         ('sanitized',['-O1',*GENERIC,'-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
        folder=base/label;folder.mkdir()
        obj=object_build(box,clang,src,folder/'kernel',flags)
        drv=object_build(box,clang,driver,folder/'driver',['-O0',*GENERIC]+(['-fsanitize=address,undefined'] if label=='sanitized' else []))
        exe=link(box,clang,[drv,obj,util],folder/'link',['-fsanitize=address,undefined'] if label=='sanitized' else [])
        rec,result=execute_program(box,exe,folder/'verify')
        if label=='O0':
            oracle=result
            checks.append(rec['state']=='ok' and bool(result) and len(result)==len(archived_oracle))
        else:
            checks.append(rec['state']=='ok' and bool(result) and result==oracle)
        objects[label]={'kernel':str(obj),'driver':str(drv),'flags':flags,'program':str(exe)}
    info={'passed':all(checks),'official_checks':checks,'abi':abi,'objects':objects,'utility':str(util),
          'reference_c':str(src),'expected_output_sha256':shab(oracle),'oracle_path':str(base/'O0/verify.stdout'),
          'archived_output_sha256':shab(archived_oracle),'cross_host_reference_byte_match':oracle==archived_oracle,'timing':None}
    if info['passed']:
        td=base/'timing-driver.c';write(td,timing_driver(driver.read_text(),inst['function']))
        tdo=object_build(box,clang,td,base/'timing-driver',['-O3',*NATIVE])
        clock=base/'clock.c';write(clock,TIMER)
        clock_o=object_build(box,clang,clock,base/'clock',['-O3',*GENERIC])
        exe=link(box,clang,[tdo,clock_o,Path(objects['native']['kernel']),util],base/'timing-baseline')
        info['timing']={'driver':str(tdo),'clock':str(clock_o),'program':str(exe)}
    jw(base/'result.json',info);return info


def stress_gate(box,clang,pkg,inst,item,candidate,run,out):
    g=vendor('stress_support.py');task=inst['task']
    if task not in g.TASKS:return 'not_implemented_for_task',[]
    out.mkdir(parents=True,exist_ok=True);h=out/'harness.c';write(h,g.harness(task));rows=[]
    src=pkg/inst['sources']['C']['path']
    data=g.cases(task);inputs={}
    for c in data:
        p=out/(c['case_id']+'.bin');write(p,g.checked_data(task,c));inputs[c['case_id']]=p
    ro=object_build(box,clang,src,out/'oracle-kernel',['-O0',*GENERIC])
    ho=object_build(box,clang,h,out/'oracle-driver',['-O0',*GENERIC])
    ref=link(box,clang,[ho,ro],out/'oracle-link');oracles={}
    for c in data:
        p=inputs[c['case_id']];rec,raw=execute_program(box,ref,out/('oracle-'+c['case_id']),
          [c['p'],c['q'],c['r'],c['t'],'/in/input.bin'],{'input.bin':p})
        need(rec['state']=='ok','追加検証の参照実行が失敗')
        g.validate_blob(task,c,raw)
        need(g.compare_result(task,c,p.read_bytes(),raw,raw,'ok')['passed'],'追加参照が契約違反')
        oracles[c['case_id']]=raw
    for label,flags in [('generic',['-O3',*GENERIC]),('native',['-O3',*NATIVE]),
                 ('sanitized',['-O1',*GENERIC,'-fsanitize=address,undefined','-fno-sanitize-recover=all'])]:
        co=object_build(box,clang,candidate,out/(label+'-kernel'),flags,label=='sanitized')
        ho=object_build(box,clang,h,out/(label+'-driver'),flags)
        ex=link(box,clang,[ho,co],out/(label+'-link'),['-fsanitize=address,undefined'] if label=='sanitized' else [])
        for c in data:
            p=inputs[c['case_id']];rec,raw=execute_program(box,ex,out/(label+'-'+c['case_id']),
              [c['p'],c['q'],c['r'],c['t'],'/in/input.bin'],{'input.bin':p})
            ans=g.compare_result(task,c,p.read_bytes(),oracles[c['case_id']],raw,rec['state'])
            rows.append({'case':c['case_id'],'profile':label,**ans})
    return ('passed' if all(x['passed'] for x in rows) else 'failed'),rows


def validate_candidate(box,clang,pkg,plan,run,item,inst,base):
    d=run/'validation'/item['id']
    if (d/'result.json').exists():return load(d/'result.json')
    if d.exists():d.rename(d.with_name(d.name+'.interrupted-'+uuid.uuid4().hex[:8]))
    d.mkdir(parents=True)
    gen=run/'generation'/item['id'];gr=load(gen/'result.json')
    result={'id':item['id'],'status':'not_verified','official_all_passed':False,'multiinput_status':'not_run',
       'official_profiles':[],'universal_equivalence_proven':False,'measurement_eligible_provisional':False,
       'not_final_correctness_claim':True,'native_object':None,'errors':[]}
    if gr['status']!='saved':
        result['status']='generation_failed';jw(d/'result.json',result);return result
    if not base['passed']:
        result['status']='baseline_failed';jw(d/'result.json',result);return result
    candidate=gen/('candidate.c' if item['form']=='C' else 'candidate.ll')
    need(sha(candidate)==gr['code_sha256'],'生成物の保存ハッシュ不一致')
    try:
        policy(candidate.read_text(),item['form'],inst['function'])
        if item['form']=='C':
            if abi_c(box,clang,candidate,inst['function'],d/'abi')!=base['abi']:raise CandidateFailure('signature_changed')
        else:
            if ir_abi(candidate.read_text(),inst['function'])!=ir_abi((pkg/inst['sources']['IR']['path']).read_text(),inst['function']):raise CandidateFailure('ir_signature_changed')
        oracle=Path(base['oracle_path']).read_bytes()
        for label in ('generic','native','sanitized'):
            bd=base['objects'][label]
            obj=object_build(box,clang,candidate,d/(label+'-kernel'),bd['flags'],label=='sanitized')
            if label!='sanitized':symbols_ok(box,obj,inst['function'],d/(label+'-symbols'))
            exe=link(box,clang,[Path(bd['driver']),obj,Path(base['utility'])],d/(label+'-link'),['-fsanitize=address,undefined'] if label=='sanitized' else [])
            rec,raw=execute_program(box,exe,d/(label+'-verify'))
            passed=rec['state']=='ok' and bool(raw) and raw==oracle
            result['official_profiles'].append({'profile':label,'passed':passed,'state':rec['state'],
                      'stdout_sha256':shab(raw),'expected_sha256':shab(oracle)})
            if label=='native':result['native_object']=str(obj)
        result['official_all_passed']=len(result['official_profiles'])==3 and all(x['passed'] for x in result['official_profiles'])
        if result['official_all_passed']:
            status,rows=stress_gate(box,clang,pkg,inst,item,candidate,run,d/'stress')
            result['multiinput_status']=status;result['multiinput_checks']=rows
        result['measurement_eligible_provisional']=result['official_all_passed'] and result['multiinput_status'] in {'passed','not_implemented_for_task'}
        result['status']='checked'
    except BudgetPause:raise
    except CandidateFailure as exc:result['status']='candidate_rejected';result['errors'].append(str(exc))
    except Exception as exc:result['status']='validation_error';result['errors'].append(type(exc).__name__+': '+str(exc))
    jw(d/'result.json',result);return result


def parse_batch(raw,k):
    m=re.fullmatch(rb'CPUCOND_BATCH ([0-9]+) ([0-9]+)\n',raw)
    need(m is not None,'計測応答の形式不正')
    kk,ns=map(int,m.groups());need(kk==k and ns>0,'計測値不正');return ns

def qsummary(rows,identity=False):
    ratios=[r['speedup'] for r in rows];refs=[r['reference_ns'] for r in rows];cands=[r['candidate_ns'] for r in rows]
    warnings=[]
    for n,x in [('ratio',ratios),('reference',refs),('candidate',cands)]:
        med=statistics.median(x);q=statistics.quantiles(x,n=4,method='inclusive')
        if (q[2]-q[0])/med>0.10:warnings.append(n+'_variable')
    m=statistics.median(ratios)
    if identity and abs(math.log(m))>math.log(1.02):warnings.append('identity_shift')
    return {'median_speedup':m,'warnings':warnings}


def timing(box,ref,cand,d,k,identity=False):
    rows=[];summaries=[]
    for session in range(2):
        order=[0,1]*4;random.Random(SEED+session).shuffle(order);rs=[]
        for trial,b in enumerate(order):
            vals={}
            for name,program in ([('candidate',cand),('reference',ref)] if b else [('reference',ref),('candidate',cand)]):
                stem=d/f's{session}-p{trial}-{name}';rec,raw=execute_program(box,program,stem,[k])
                need(rec['state']=='ok','計測プログラム実行失敗');vals[name]=parse_batch(raw,k)
            row={'session':session,'trial':trial,'reference_ns':vals['reference'],'candidate_ns':vals['candidate'],
                    'speedup':vals['reference']/vals['candidate'],'order':b,'batch':k};rs.append(row);rows.append(row)
        summaries.append(qsummary(rs,identity))
    if abs(math.log(summaries[0]['median_speedup']/summaries[1]['median_speedup']))>math.log(1.03):
        for s in summaries:s['warnings'].append('session_change')
    return rows,summaries


def baseline_timing(box,base,run,inst):
    d=run/'baseline-timing'/(inst['task']+'__'+inst['size'])
    if (d/'result.json').exists():return load(d/'result.json')
    if d.exists():d.rename(d.with_name(d.name+'.interrupted-'+uuid.uuid4().hex[:8]))
    d.mkdir(parents=True)
    ref=Path(base['timing']['program']);k=1;cal=[]
    while k<=16384:
        xs=[]
        for i in range(3):
            rec,raw=execute_program(box,ref,d/f'cal-k{k}-r{i}',[k]);need(rec['state']=='ok','基準校正失敗');xs.append(parse_batch(raw,k))
        cal.append({'k':k,'ns':xs})
        if statistics.median(xs)>=5_000_000:break
        k*=2
    need(k<=16384,'基準校正の時間未達')
    rows,summaries=timing(box,ref,ref,d/'identity',k,True)
    result={'k':k,'calibration':cal,'identity_rows':rows,'identity_sessions':summaries,
            'valid':not any(s['warnings'] for s in summaries)}
    jw(d/'result.json',result);return result


def measurement(box,clang,run,inst,item,base,v):
    d=run/'measurement'/item['id']
    if (d/'result.json').exists():return load(d/'result.json')
    if d.exists():d.rename(d.with_name(d.name+'.interrupted-'+uuid.uuid4().hex[:8]))
    d.mkdir(parents=True)
    result={'id':item['id'],'provisional':True,'measurement_valid':False,'speedup':None,
       'correctness_scope':v['multiinput_status'],'formal_equivalence_proven':False,'errors':[]}
    try:
        control=baseline_timing(box,base,run,inst)
        if not control['valid']:
            result['errors'].append('identity_quality_failed');jw(d/'result.json',result);return result
        exe=link(box,clang,[Path(base['timing']['driver']),Path(base['timing']['clock']),Path(v['native_object']),Path(base['utility'])],d/'candidate-timing')
        rows,summaries=timing(box,Path(base['timing']['program']),exe,d/'timings',control['k'])
        result['rows']=rows;result['session_summaries']=summaries
        result['measurement_valid']=not any(s['warnings'] for s in summaries)
        result['speedup']=math.exp(statistics.fmean(math.log(s['median_speedup']) for s in summaries))
        result['baseline_object_sha256']=sha(base['objects']['native']['kernel']);result['candidate_object_sha256']=sha(v['native_object'])
    except BudgetPause:raise
    except Exception as exc:result['errors'].append(type(exc).__name__+': '+str(exc))
    jw(d/'result.json',result);return result


def host_guard():
    need(os.geteuid()==0,'--run起動器のみ、サーバーのrootで実行します')
    need(Path('/proc/sys/kernel/hostname').read_text().strip()=='cpucond-zen2-01','対象ホストが違います')
    need('AMD EPYC 7402' in Path('/proc/cpuinfo').read_text(),'EPYC 7402ではありません')
    need(set(range(2,18))<=os.sched_getaffinity(0),'推論用CPUが利用不可')
    for cpu in range(2,18):need(Path(f'/sys/devices/system/cpu/cpu{cpu}/node0').exists(),'推論CPUがNUMA0ではありません')
    for p,x in [('/sys/devices/system/cpu/smt/active','0'),('/sys/devices/system/cpu/cpufreq/boost','0'),
                ('/sys/devices/system/cpu/cpu2/cpufreq/scaling_governor','performance')]:
        need(Path(p).read_text().strip()==x,'CPU設定が変わっています: '+p)
    for tool in ('bwrap','runuser','numactl'):need(shutil.which(tool),'必要ツールがありません: '+tool)
    check_busy()


def run_pipeline(pkg,max_hours,generation_hours):
    pkg=Path(pkg).resolve();host_guard();clang,version=clang_path()
    need(0.25<=max_hours<=24 and 0<=generation_hours<=max_hours-0.25,'時間上限が不正です')
    hashes=hm(pkg)
    for rel,h in hashes.items():need(sha(safe(pkg,rel))==h,'転送パッケージが改変されています: '+rel)
    plan=load(pkg/'plan.json');need(plan.get('revision')==REV and plan['requests']==180,'実行計画不一致')
    run=pkg.parent/'results';run.mkdir(exist_ok=True);(run/'sessions').mkdir(exist_ok=True)
    lock=open('/var/lock/cpucond-batch-codegen.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    start=time.monotonic();end=start+max_hours*3600;gen_end=start+generation_hours*3600
    def budget_signal(signum,frame):raise BudgetPause('管理側の時間上限')
    signal.signal(signal.SIGTERM,budget_signal)
    session=run/'sessions'/('session-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.json')
    record={'started_utc':now(),'phase':'preflight','max_hours':max_hours,'generation_hours':generation_hours,
       'plan_sha256':sha(pkg/'plan.json'),'compiler':version,'hostname':socket.gethostname(),'errors':[]}
    box=None
    try:
        with open(run/'frozen-plan-sha256','a+') as f:
            f.seek(0);old=f.read().strip()
            if old:need(old==sha(pkg/'plan.json'),'再開する計画が変更されています')
            else:f.write(sha(pkg/'plan.json')+'\n')
        box=Sandbox(run/'sandbox-records'/uuid.uuid4().hex[:8],end);box.preflight()
        account,binary,freeze,blobs=model_state();record['model_freeze']=freeze;record['model_blobs']=blobs
        if (run/'frozen-model.json').exists():need(load(run/'frozen-model.json')==freeze,'再開時モデルが変化')
        else:jw(run/'frozen-model.json',freeze)
        frozen_host={'machine_id':Path('/etc/machine-id').read_text().strip(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'kernel_release':os.uname().release,'compiler':version,'compiler_binary_sha256':sha(Path(clang).resolve())}
        if (run/'frozen-host.json').exists():need(load(run/'frozen-host.json')==frozen_host,'再開先の実機/OS/コンパイラが変化。自動で旧計測を混ぜません')
        else:jw(run/'frozen-host.json',frozen_host)
        atomic(run/'progress.json',results_summary(plan,run))
        if generation_hours>0 and results_summary(plan,run)['requests_pending']:
            record['phase']='generation';generation_phase(pkg,plan,run,gen_end,freeze,binary)
        # 他の推論サービスが残る場合は計測しない。
        check_busy();host_guard()
        record['phase']='validation_and_measurement'
        for item in plan['tasks']:
            gen=run/'generation'/item['id']/'result.json'
            if not gen.exists():continue
            if (run/'validation'/item['id']/'result.json').exists():
                v=load(run/'validation'/item['id']/'result.json')
                if (run/'measurement'/item['id']/'result.json').exists() or not v.get('measurement_eligible_provisional'):continue
            if time.monotonic()+300>end:break
            inst=next(x for x in plan['instances_list'] if (x['task'],x['size'])==(item['task'],item['size']))
            print('検証:',item['id'],flush=True)
            gr=load(gen)
            if gr['status']!='saved':
                vd=run/'validation'/item['id'];vd.mkdir(parents=True,exist_ok=True)
                if not (vd/'result.json').exists():jw(vd/'result.json',{'id':item['id'],'status':'generation_failed','official_all_passed':False,'multiinput_status':'not_run','measurement_eligible_provisional':False})
                continue
            base=prepare_baseline(box,clang,pkg,inst,run)
            v=validate_candidate(box,clang,pkg,plan,run,item,inst,base)
            print('  公式入力=',v['official_all_passed'],'追加検証=',v['multiinput_status'],flush=True)
            if v.get('measurement_eligible_provisional') and time.monotonic()+180<end:
                z=measurement(box,clang,run,inst,item,base,v)
                print('  暫定速度倍率=',z.get('speedup'),'計測品質=',z['measurement_valid'],flush=True)
            atomic(run/'progress.json',results_summary(plan,run))
        record['phase']='finished_or_budget_pause'
    except BudgetPause:
        record['phase']='budget_pause'
    except Exception as exc:
        record['phase']='blocked';record['errors'].append(type(exc).__name__+': '+str(exc))
    finally:
        if box:box.close()
        summary=results_summary(plan,run);summary['current_session']=record;summary['run_directory']=str(run)
        summary['completion']='DATASET_BATCH_COMPLETE' if summary['generation_terminal']==180 and summary['validation_terminal']==180 and summary['measurement_pending']==0 and record['phase']!='blocked' else ('DATASET_BATCH_BLOCKED' if record['phase']=='blocked' else 'DATASET_BATCH_PAUSED')
        summary['completion_means_all_requested_attempts_processed_not_all_correct']=True
        record['finished_utc']=now();record['elapsed_seconds']=time.monotonic()-start
        jw(session,record);atomic(run/'summary.json',summary);atomic(run/'progress.json',summary)
        # セッション単位の結果ハッシュ一覧。前の一覧を上書きしない。
        receipt=run/'sessions'/(session.stem+'-hashes.txt')
        write(receipt,''.join(f'{sha(p)}  {p.relative_to(run).as_posix()}\n' for p in sorted(run.rglob('*')) if p.is_file() and not p.is_symlink()))
        print('\n=== データセット一括実行結果 ===\n'+json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
        print(summary['completion'],flush=True)
        print('保存先:',run,flush=True)
    return 1 if record['errors'] else 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_mutually_exclusive_group(required=True);sub.add_argument('--prepare',action='store_true');sub.add_argument('--run',action='store_true');sub.add_argument('--self-test',action='store_true')
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--roundtrip',type=Path)
    p.add_argument('--package',type=Path,default=Path(__file__).parent)
    p.add_argument('--max-hours',type=float,default=4);p.add_argument('--generation-hours',type=float,default=3)
    args=p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    try:
        if args.prepare:
            need(args.roundtrip is not None,'--roundtripが必要です');return prepare(args.repo,args.roundtrip)
        return run_pipeline(args.package,args.max_hours,args.generation_hours)
    except Exception as exc:print('停止:',type(exc).__name__+': '+str(exc),file=sys.stderr);return 1


FIXTURE='''#include <stdio.h>\n#include <stdlib.h>\nvoid kernel_t(int n, double a[n]);\nstatic void init_array(int n,double a[n]){for(int i=0;i<n;i++)a[i]=i+1;}\nint main(int argc,char**argv){int n=3;double*a=malloc(sizeof(double)*n);init_array(n,a);kernel_t(n,a);fwrite(a,sizeof(double),n,stdout);free(a);return 0;}\n'''
class Tests(unittest.TestCase):
    def test_unique(self):
        with self.assertRaises(Blocked):loads('{"x":1,"x":2}')
    def test_nan(self):
        with self.assertRaises(Blocked):loads('{"x":NaN}')
    def test_safe(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Blocked):safe(Path(d),'../x')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';write(p,'x')
            with self.assertRaises(FileExistsError):write(p,'y')
    def test_vendor_hashes(self):
        for n in VENDORS:self.assertIsNotNone(vendor(n))
    def test_task_unique(self):
        xs=[make_task_id('k'+str(k),s,f) for s in SIZES for k in range(30) for f in ('C','IR')]
        self.assertEqual(len(set(xs)),180)
    def test_generation_is_not_selection(self):
        q,u=request_for('void kernel_gemm(int n){}','C','gemm','MINI')
        self.assertNotIn('format',q);self.assertIn('直接',q['prompt']);self.assertEqual(q['options']['seed'],SEED)
    def test_no_cpu_info(self):
        q,_=request_for('void kernel_t(){}','C','t','SMALL')
        for s in ('Haswell','EPYC','Zen 2','candidate_id'):self.assertNotIn(s,q['prompt'])
    def test_no_special(self):
        with self.assertRaises(Blocked):request_for('<|im_start|>','C','t','SMALL')
    def test_context_bound(self):
        _,upper=request_for('x'*40000,'IR','t','MINI');self.assertGreater(upper+CAPS['IR'],CTX)
    def test_candidate_error(self):
        with self.assertRaises(CandidateFailure):policy('void kernel_t(){system(0);}','C','kernel_t')
    def test_changed_candidate_allowed(self):
        policy('void kernel_t(int n,double a[n]){for(int i=0;i<n;i++){double x=a[i];a[i]=x*2;}}','C','kernel_t')
    def test_bad_include(self):
        with self.assertRaises(CandidateFailure):policy('#include </etc/shadow>\nvoid kernel_t(){}','C','kernel_t')
    def test_ir_fast(self):
        with self.assertRaises(CandidateFailure):policy('define void @kernel_t(){\n%a = fadd fast double 1.0, 2.0\nret void\n}','IR','kernel_t')
    def test_ir_abi(self):self.assertEqual(ir_abi('define void @kernel_t(i32 noundef %n, ptr %a) {','kernel_t'),['i32','ptr'])
    def test_abi_names(self):
        def f(name):return {'inner':[{'kind':'ParmVarDecl','name':name,'type':{'qualType':'int'}},{'kind':'ParmVarDecl','name':'A','type':{'qualType':'double (*)['+name+']'}}]}
        self.assertEqual(abi_signature(f('n')),abi_signature(f('m')))
    def test_timer(self):
        s=timing_driver(FIXTURE,'kernel_t');self.assertIn('CPUCOND_BATCH',s);self.assertNotIn('fwrite(a',s);self.assertIn('init_array(n,a);',s)
    def test_batch_parse(self):self.assertEqual(parse_batch(b'CPUCOND_BATCH 2 17\n',2),17)
    def test_bad_batch(self):
        with self.assertRaises(Blocked):parse_batch(b'CPUCOND_BATCH 3 17\n',2)
    def test_quality(self):
        rows=[{'speedup':1.0,'reference_ns':10,'candidate_ns':10}]*8
        self.assertEqual(qsummary(rows,True)['warnings'],[])
    def test_quality_identity(self):
        rows=[{'speedup':1.1,'reference_ns':11,'candidate_ns':10}]*8
        self.assertIn('identity_shift',qsummary(rows,True)['warnings'])
    def test_sandbox_paths(self):
        b=object.__new__(Sandbox)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidate.c';p.write_text('void k(){}')
            a=b.argv(['/usr/bin/true'],{'candidate.c':p},None)
            self.assertIn('--unshare-net',a);self.assertIn('--cap-drop',a);self.assertIn('65534',' '.join(a))
            self.assertNotIn('/root',a);self.assertNotIn('/var/lib/cpucond-infer',a)
    def test_runtime_has_no_oracle(self):
        b=object.__new__(Sandbox)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'program';p.write_text('x')
            a=b.argv(['/in/program'],{'program':p},None)
            self.assertNotIn('oracle.raw',' '.join(a));self.assertNotIn('--bind',a)
    def test_nodata_summary(self):
        with tempfile.TemporaryDirectory() as d:
            x=results_summary({'tasks':[]},Path(d));self.assertFalse(x['all_30_multinput_validation_complete'])
    def test_parse_response(self):
        item={'task':'t','form':'C','input_byte_upper':999}
        obj={'model':MODEL,'done':True,'done_reason':'stop','prompt_eval_count':10,'eval_count':10,'response':'void kernel_t(){}'}
        s,r=extract_response(obj,item);self.assertIn('kernel_t',s);self.assertFalse(r['correctness_validated'])
    def test_truncated_response(self):
        with self.assertRaises(Blocked):extract_response({'model':MODEL,'done':True,'done_reason':'length'},{'task':'t','form':'C','input_byte_upper':999})
    def test_real_timing_driver_compile(self):
        c,v=clang_path(False)
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);driver=d/'driver.c';driver.write_text(timing_driver(FIXTURE,'kernel_t'))
            kernel=d/'kernel.c';kernel.write_text('void kernel_t(int n,double a[n]){for(int i=0;i<n;i++)a[i]*=2;}')
            clock=d/'clock.c';clock.write_text(TIMER)
            p=subprocess.run([c,'-std=gnu11',driver,kernel,clock,'-o',d/'program'],capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr.decode())
            p=subprocess.run([d/'program','2'],capture_output=True)
            self.assertEqual(p.returncode,0);self.assertGreater(parse_batch(p.stdout,2),0)

if __name__=='__main__':raise SystemExit(main())
