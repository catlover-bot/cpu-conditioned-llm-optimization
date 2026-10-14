#!/usr/bin/env python3
"""GPU004: common-prompt GPT/Claude/Qwen CUDA generation -> verification -> timing.

Cloud credentials stay in the WSL watcher. CUDA uses the pinned GPU002 core.
Only the six implemented development workloads are enabled; no 30-task claim.
No automatic generation retry, no provider/model fallback, no old-run overwrite.
"""
from __future__ import annotations

# PUBLIC ARCHIVAL COPY. Source hashes are recorded in publication-provenance.json.
# Only operational instance fields and dependency loading differ from the source.
# Offline analysis needs no allocation, provider account, CUDA build or GPU.
import importlib.util as _public_importlib
from pathlib import Path as _PublicPath
_public_path = _PublicPath(__file__).resolve().parent.parent / 'gpu004' / '_public.py'
_public_spec = _public_importlib.spec_from_file_location('_cpucond_public_dependencies', _public_path)
_public = _public_importlib.module_from_spec(_public_spec)
_public_spec.loader.exec_module(_public)
import argparse, base64, contextlib, copy, csv, ctypes as ct, datetime as dt
import decimal, getpass, gzip, hashlib, http.client, io, json, math, os, random
import re, shlex, shutil, signal, ssl, subprocess, sys, tarfile, tempfile, time
import traceback, types, unittest, uuid
from collections import Counter
from pathlib import Path
from unittest import mock

CORE_SHA = '378dffe7c0d185974450c29ce7d73cdccb179502e36a3771e57ee76071b6054b'
CORE_EMBED = _public.encoded_module('numeric_core.py')
SOURCE_SHA='54c87aa4795a520dc2601be7e13434abb1f415e23859f246ef8e6adccaac9778'
SOURCE_EMBED = _public.encoded_asset('source-bundle.json')
REGISTRY_SHA='76bfb5cd8c62efc5feada577bb01c45659c424e209519cbc7e45234ab6ca9054'
REGISTRY_EMBED = _public.encoded_asset('registry.json')


def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def load_embedded(name: str, encoded: str, pin: str):
    return _public.load_module('numeric_core.py', pin)

C = load_embedded('gpu004_numeric_core', CORE_EMBED, CORE_SHA)
P = C.P
Blocked, NumericFailure = P.Blocked, P.NumericFailure
need, require, canon, parse, read, save, jw, hfile, now = P.need, P.require, P.canon, P.parse, P.read, P.save, P.jw, P.hfile, P.now
ROOT = Path('/workspace/gpu004-multimodel-env-v1')
LOCAL_REL = Path('workspace/cpu-conditioned-llm-optimization/runs/gpu004-multimodel-env-v1')
VERSION = 'gpu004-three-provider-six-development-workloads-v1'
PROVIDERS = ('qwen', 'openai', 'anthropic')
RUN_SECONDS, ACK_SECONDS, REQUEST_SECONDS = 48*3600, 12*3600, 900
REPEATS = (1,2,3)
PLAN_SEED = 20261009041
TOTAL = 270
D = decimal.Decimal
API_HOSTS = {'openai':'api.openai.com','anthropic':'api.anthropic.com'}
PRICE_DATE = '2026-10-09'
PRICE_REFS = {
    'openai':'https://developers.openai.com/api/docs/models/gpt-5.6-terra',
    'anthropic':'https://platform.claude.com/docs/en/about-claude/pricing'}

# Explicitly reviewed presets, not an assertion about the user's CPU experiment.
# There is no default model choice and no automatic downgrade/substitution.
PRESETS = {
    'openai': {'id':'gpt-5.6-terra', 'input_usd_per_million':'2', 'output_usd_per_million':'12',
               'max_output_tokens':8192, 'reasoning_effort':'none', 'temperature':0.2,'top_p':0.9},
    'anthropic': {'id':'claude-sonnet-5', 'input_usd_per_million':'3','output_usd_per_million':'15',
                  'max_output_tokens':8192,'thinking':'disabled'},
    'qwen': {'id':P.MODEL,'max_output_tokens':8192,'seed_values':[69001,69002,69003],
             'temperature':0.2,'top_p':0.9,'top_k':40,'min_p':0.0}
}


def configure(root: Path | None = None) -> None:
    global ROOT
    if root is not None: ROOT = Path(root)
    C.__file__ = __file__; C.LOCAL_REL = LOCAL_REL; C.VERSION = VERSION
    C.RUN_SECONDS, C.ACK_SECONDS, C.REQUEST_SECONDS = RUN_SECONDS, ACK_SECONDS, REQUEST_SECONDS
    C.configure(ROOT)
    P.PORT = 11618; P.CAP = 8192; P.MAX_GENERATIONS = TOTAL
    P.STATE = {}; C.BASES.clear()
configure()


def source_files() -> dict[str, bytes]:
    raw = gzip.decompress(base64.b64decode(SOURCE_EMBED)); need(sha(raw)==SOURCE_SHA,'Source bundle changed')
    obj = parse(raw)
    return {k:base64.b64decode(v,validate=True) for k,v in obj.items()}


def registry() -> dict:
    raw = gzip.decompress(base64.b64decode(REGISTRY_EMBED)); need(sha(raw)==REGISTRY_SHA,'Registry changed')
    return parse(raw)


def original(task: str) -> str:
    need(task in C.TASKS,'Unknown task')
    return source_files()['sources/'+task+'.cu'].decode()


def install_sources() -> None:
    files = source_files()
    for task in C.TASKS:
        spec = C.SPECS[task]
        raw = files['upstream/'+spec['path']]
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        need(blob == spec['blob'],'Original Git blob changed')
        adapted, _ = C.extract_kernel(raw, task)
        need(adapted == original(task),'Adapted source differs from verified original')
    for name,b in files.items():
        path = Path(name); need(not path.is_absolute() and '..' not in path.parts,'Unsafe source entry')
        save(ROOT/'setup'/name,b)
    jw(ROOT/'setup/source-manifest.json', {'commit':C.COMMIT,'files':{n:sha(b) for n,b in files.items()},
        'source':'receipt-verified GPU002 upstream archive; old measurements are not imported',
        'core_sha256':CORE_SHA,'source_bundle_sha256':SOURCE_SHA})
    jw(ROOT/'setup/expansion-registry-reference.json',registry())


def validate_settings(cfg: dict) -> None:
    need(isinstance(cfg,dict) and set(cfg)=={'schema','models','model_provenance'},'Config schema mismatch')
    need(cfg['schema']==VERSION and set(cfg['models'])==set(PROVIDERS),'Config provider set differs')
    for p in PROVIDERS:
        m=cfg['models'][p]; base=PRESETS[p]
        need(set(m)==set(base),'Unknown model setting (credentials must never enter config)')
        # Restrict to reviewed API parameter contracts, but allow explicit dated snapshots.
        model=m['id']; family=base['id']
        need(isinstance(model,str) and (model==family or p=='openai' and
             re.fullmatch(re.escape(family)+r'-\d{4}-\d{2}-\d{2}',model)),
             'Unsupported model ID; no automatic substitution: '+str(model))
        need({k:v for k,v in m.items() if k!='id'}=={k:v for k,v in base.items() if k!='id'},
             'Reviewed settings changed; create a new protocol rather than mutate this run')
    need(cfg['model_provenance'] in ('user_entered_cpu_id_not_independently_verified','explicit_new_gpu_cohort_ids'),
         'Model provenance must be explicit')


def choose_settings() -> dict:
    print('CPUの実使用モデルIDは自動で推測しません。空欄なら送信せず終了します。')
    print('この版で確認したAPI契約: gpt-5.6-terra / claude-sonnet-5。別IDへ代替しません。')
    models=copy.deepcopy(PRESETS)
    for provider,var in [('openai','OPENAI_GPU_MODEL'),('anthropic','ANTHROPIC_GPU_MODEL')]:
        value=os.environ.get(var) or input(provider+' の正式モデルID: ').strip()
        need(bool(value),'Model not specified; no generation sent')
        models[provider]['id']=value
    tag=input('CPUの保存要求で同じIDを確認済みなら CPU、新しいGPU比較の指定なら NEW: ').strip()
    need(tag in ('CPU','NEW'),'Choose CPU or NEW explicitly')
    cfg={'schema':VERSION,'models':models,'model_provenance':
         'user_entered_cpu_id_not_independently_verified' if tag=='CPU' else 'explicit_new_gpu_cohort_ids'}
    validate_settings(cfg); return cfg


def gpu_profiles(info: dict) -> dict[str,str]:
    fields=('name','compute_capability','warp_size','static_shared_memory_per_block',
            'registers_per_block','max_threads_per_multiprocessor','shared_memory_per_multiprocessor',
            'multiprocessors','l2_bytes','max_threads_per_block','memory_bytes')
    actual={k:info[k] for k in fields}
    wrong={'name':'NVIDIA Tesla V100-SXM2-32GB','compute_capability':[7,0],'warp_size':32,
           'static_shared_memory_per_block':49152,'registers_per_block':65536,
           'max_threads_per_multiprocessor':2048,'shared_memory_per_multiprocessor':98304,
           'multiprocessors':80,'l2_bytes':6291456,'max_threads_per_block':1024,'memory_bytes':34359738368}
    return {'P0':'No GPU model name or hardware performance profile is supplied.',
            'S1':'Target GPU: NVIDIA A40.',
            'S2':'Target GPU profile (byte quantities are in bytes):\n'+json.dumps(actual,sort_keys=True),
            'W1':'Target GPU: NVIDIA Tesla V100-SXM2-32GB.',
            'W2':'Target GPU profile (byte quantities are in bytes):\n'+json.dumps(wrong,sort_keys=True)}


def messages_for(task: str, arm: str, env: dict) -> list[dict]:
    spec=C.SPECS[task]
    # Same content strings for all providers. Software version is common;
    # target architecture, device UUID, observed timings and paths never leak into P0.
    headers='\n'.join(json.dumps({'block':list(b)},separators=(',',':')) for b in C.allowed_blocks(task))
    software={'compiler':'NVRTC','version':env['nvrtc_version'],'device_language':'CUDA C++17',
              'floating_point_options':{'fmad':False,'ftz':False,'prec_div':True,'prec_sqrt':True}}
    prompt=f'''Optimize this existing CUDA device kernel under the exact contract below.
<gpu_information>
{gpu_profiles(env['gpu'])[arm]}
</gpu_information>

COMMON SOFTWARE AND WORKLOAD (identical in every hardware-information arm):
{json.dumps(software,sort_keys=True)}
Workload: {task}. {C.TASK_CONTRACT[task]}
Performance shapes, in (NI,NJ,NK) order (for gesummv, N is the first entry): {json.dumps(spec['perf'])}.
Use ONE kernel and ONE block shape for BOTH performance shapes. The objective is to maximize the equal-weight geometric mean of original-kernel time divided by candidate-kernel time over these two shapes, subject to exact correctness. Shape-dependent arithmetic/index bounds are allowed, but do not hard-code outputs, input values, seeds, repeat counts or special cases for the test harness.
The measurement is GPU CUDA-event time with warm/hot buffers. The trusted host restores in/out arrays before every timed invocation, outside its timed interval. PCIe transfer, compilation, CPU reference, sanitizers and LLM inference are excluded. For convolution-3d the original complete i-slice launch sequence is timed, not just a single slice. There is no timing or compiler feedback to the model.

EXACT CORRECTNESS CONTRACT:
DATA_TYPE is float. NI,NJ,NK,N are compile-time allocation strides; runtime extents equal the corresponding allocation dimensions. _PB_NI=ni, _PB_NJ=nj, _PB_NK=nk, _PB_N=n. A trusted prefix defines them; do not redefine them.
Preserve the supplied CUDA's FP32 operation grouping and order and sequential accumulations. Preserve all declared outputs and live scratch arrays and unchanged boundary bytes. Inputs are disjoint, finite FP32; signed zero and subnormal cases matter. All positive dimensions, including ragged and unit dimensions, must remain valid. No error tolerance, reassociation, FMA contraction, TF32, FP16 or Tensor Cores. Round-to-nearest is the arithmetic rule, not a callable function named RN32. __fmul_rn, __fadd_rn and __fsub_rn are permitted but need not replace already-correct operators.
Allowed: scalar variables, arrays, static shared memory up to 48 KiB, ordinary arithmetic/control flow, min/max, __syncthreads, __syncwarp and synchronized shuffle intrinsics. Every barrier must be safe on ragged dimensions.
Forbidden: includes, preprocessor directives, helper functions, extra kernels/top-level declarations, inline PTX, arbitrary host code, external libraries, dynamic allocation/launch, atomics and function pointers. Keep exactly the supplied function signature. The trusted host constructs a covering grid and keeps the convolution-3d slice loop unchanged.

OUTPUT FORMAT (two parts, no explanatory prose):
First line: exactly ONE of the following JSON metadata lines. It contains integer values, not X/Y placeholders. Do not print the whole list.
{headers}
Second line onward: the COMPLETE CUDA kernel, with the exact supplied signature. Do not wrap the whole answer in JSON, escape the CUDA as a JSON string, or add a // BLOCK comment. No Markdown fences are requested. If no safe improvement is found, output the original block metadata and original kernel.
The original block shape is {json.dumps(spec['base'])}.

----- BEGIN ORIGINAL CUDA -----
{original(task)}----- END ORIGINAL CUDA -----'''
    return [{'role':'system','content':'Optimize CUDA numerical code under the exact contract. Return one JSON metadata line followed by the complete device kernel. No tools, explanations or timing feedback.'},
            {'role':'user','content':prompt}]


def parse_candidate(text: str,task: str) -> tuple[str,list[int]]:
    require(isinstance(text,str) and 0<len(text.encode())<=65536,'Empty or oversized candidate')
    text=text.strip()
    # A single outer fence is normalized consistently for ALL providers, before parsing.
    if text.startswith('```'):
        m=re.fullmatch(r'```(?:cuda|cpp|c\+\+|c)?\s*\n(.*?)\n```',text,re.S|re.I)
        require(m is not None and '```' not in m[1],'Invalid outer fence'); text=m[1].strip()
    first,sep,body=text.partition('\n'); require(bool(sep),'Missing CUDA body')
    try: obj=parse(first)
    except (ValueError,Blocked) as exc: raise NumericFailure('Invalid JSON block header') from exc
    require(isinstance(obj,dict) and set(obj)=={'block'},'Header must contain only block')
    b=obj['block']
    require(isinstance(b,list) and len(b)==2 and all(type(x) is int for x in b),'Block requires two integers')
    require(tuple(b) in C.allowed_blocks(task),'Block outside fixed choices')
    # Use the frozen GPU002 signature and syntax policy; never infer or repair CUDA.
    source, parsed_block=C.candidate_source('// BLOCK %d %d\n'%(b[0],b[1])+body,task)
    require(parsed_block==b,'Parser disagreement')
    return source,b


def check_environment(env: dict) -> None:
    need(env['gpu']['name']=='NVIDIA A40' and env['gpu']['compute_capability']==[8,6],'Unexpected GPU')
    need(env['gpu_uuid']==P.EXPECTED_GPU,'Different A40 allocation; no silent target change')
    need(env['nvrtc_version']==[12,8],'CUDA/NVRTC version changed')
    need(env['core_sha256']==CORE_SHA,'Wrong numerical core')


def probe_environment() -> dict:
    P.remote_guard(); P.no_other_gpu()
    g=P.CUDA()
    try: info=copy.deepcopy(g.info)
    finally: g.close()
    cp=subprocess.run(['nvidia-smi','--query-gpu=uuid,driver_version','--format=csv,noheader'],
                      env=P.clean_env(),capture_output=True,text=True,timeout=30,check=True)
    rows=[x.strip().split(', ') for x in cp.stdout.splitlines() if x.strip()]
    need(len(rows)==1,'Expected one GPU')
    libpath=next((x.resolve() for x in (Path('/usr/local/cuda-12.8/lib64/libnvrtc.so'),Path('/usr/local/cuda/lib64/libnvrtc.so')) if x.exists()),None)
    need(libpath is not None,'NVRTC library missing')
    lib=ct.CDLL(str(libpath)); fn=lib.nvrtcVersion; fn.argtypes=[ct.POINTER(ct.c_int),ct.POINTER(ct.c_int)];fn.restype=ct.c_int
    a,b=ct.c_int(),ct.c_int();need(fn(ct.byref(a),ct.byref(b))==0,'NVRTC version query failed')
    sanitizer=Path(P.sanitizer_path()).resolve()
    cc=subprocess.run(['g++','--version'],env=P.clean_env(),capture_output=True,text=True,timeout=10,check=True)
    env={'gpu':info,'gpu_uuid':rows[0][0],'driver_version':rows[0][1],
         'nvrtc_version':[a.value,b.value],'nvrtc_sha256':hfile(libpath),'sanitizer_sha256':hfile(sanitizer),
         'host_compiler':cc.stdout.splitlines()[0],'core_sha256':CORE_SHA,
         'free_disk_bytes':shutil.disk_usage(ROOT).free,'observed_utc':now(),
         'os_release':Path('/etc/os-release').read_text(),'storage_persistence_verified':False}
    check_environment(env);return env


def environment_identity(env: dict) -> dict:
    return {k:env[k] for k in ('gpu_uuid','gpu','driver_version','nvrtc_version','nvrtc_sha256','sanitizer_sha256','host_compiler','core_sha256','os_release')}


def make_plan(cfg: dict,env: dict) -> dict:
    validate_settings(cfg); check_environment(env)
    groups=[]; rng=random.Random(PLAN_SEED)
    pairs=[(t,i) for t in C.TASKS for i in REPEATS];rng.shuffle(pairs)
    for task,trial in pairs:
        providers=list(PROVIDERS);rng.shuffle(providers)
        for provider in providers:
            arms=list(C.ARMS);rng.shuffle(arms)
            label=f'{provider}-{task}-r{trial:02d}'
            requests=[]
            for arm in arms:
                msgs=messages_for(task,arm,env)
                requests.append({'id':f'{provider}__{task}__{arm}__r{trial:02d}',
                   'provider':provider,'task':task,'condition':arm,'trial':trial,'seed':69000+trial,
                   'seed_sent_to_provider':69000+trial if provider=='qwen' else None,
                   'messages':msgs,'messages_sha256':sha(canon(msgs))})
            groups.append({'label':label,'provider':provider,'task':task,'trial':trial,'requests':requests})
    plan={'schema':VERSION,'config':cfg,'environment':env,'groups':groups,
          'candidate_slots':TOTAL,'source_bundle_sha256':SOURCE_SHA,'core_sha256':CORE_SHA,
          'task_count':6,'additional_24_tasks_enabled':False,'development_only':True,
          'common_prompt_revision':'environment-sizes-objective-json-header-v1',
          'code_track':'CUDA body plus enumerated block choice','input_archive_receipt':'GPU002 setup verified at packaging',
          'gpu_profiles':gpu_profiles(env['gpu']),
          'profile_provenance':{'S2':'transient CUDA driver inventory on the evaluation A40',
              'W2':'fixed V100-SXM2-32GB comparison profile; nominal capacity; not a V100 measurement',
              'memory_kind':'S2 device-visible memory; W2 fixed nominal 32 GiB; not treated as identically acquired observations',
              'references':['https://docs.nvidia.com/cuda/volta-tuning-guide/index.html','https://www.nvidia.com/en-gb/data-center/tesla-v100/']},
          'numeric_protocol':{k:C.PROTOCOL[k] for k in ('strict_semantics','baseline','host_adaptations','measurement','numerical_inputs','timing_input','timing_repetitions','sanitizers')},
          'no_feedback':True,'no_automatic_generation_retry':True,'no_provider_fallback':True,
          'formal_equivalence_proven':False,'old_results_overwritten':False}
    validate_plan(plan);return plan


def index_requests(plan: dict) -> dict[str,dict]:
    return {r['id']:r for g in plan['groups'] for r in g['requests']}


def validate_plan(plan: dict) -> None:
    validate_settings(plan['config']);check_environment(plan['environment'])
    rs=[r for g in plan['groups'] for r in g['requests']];idx=index_requests(plan)
    need(len(rs)==len(idx)==TOTAL,'270-slot plan differs')
    expect={(p,t,a,i) for p in PROVIDERS for t in C.TASKS for a in C.ARMS for i in REPEATS}
    need({(r['provider'],r['task'],r['condition'],r['trial']) for r in rs}==expect,'Unbalanced grid')
    for r in rs:
        need(r['messages']==messages_for(r['task'],r['condition'],plan['environment']),'Prompt altered')
        need(sha(canon(r['messages']))==r['messages_sha256'],'Prompt digest differs')
    for t in C.TASKS:
        for a in C.ARMS:
            need(len({r['messages_sha256'] for r in rs if r['task']==t and r['condition']==a})==1,'Cross-provider prompt differs')
        commons=[]
        for a in C.ARMS:
            txt=messages_for(t,a,plan['environment'])[1]['content']
            commons.append(re.sub(r'<gpu_information>.*?</gpu_information>','<gpu_information/>',txt,flags=re.S))
        need(len(set(commons))==1,'Nonhardware text changed between arms')
        p0=messages_for(t,'P0',plan['environment'])[1]['content']
        need(not any(x in p0 for x in ('A40','V100','sm_86',P.EXPECTED_GPU,'example.invalid')),'P0 hardware leak')


def api_payload(provider: str, r: dict,cfg: dict) -> dict:
    m=cfg['models'][provider];msgs=r['messages']
    if provider=='openai':
        return {'model':m['id'],'input':msgs,'max_output_tokens':m['max_output_tokens'],
                'reasoning':{'effort':m['reasoning_effort']},'temperature':m['temperature'],'top_p':m['top_p'],
                'tools':[],'tool_choice':'none','store':False,'stream':False,'truncation':'disabled','service_tier':'default'}
    need(provider=='anthropic','Not a cloud provider')
    return {'model':m['id'],'system':msgs[0]['content'],'messages':[msgs[1]],
            'max_tokens':m['max_output_tokens'],'thinking':{'type':'disabled'},'stream':False}


def count_payload(provider: str, body: dict) -> dict:
    keys=('model','input','tools','tool_choice','reasoning','truncation') if provider=='openai' else ('model','system','messages','thinking')
    return {k:body[k] for k in keys if k in body}


class Secrets:
    def __init__(self): self.values={}
    def get(self,provider: str) -> str:
        if provider not in self.values:
            var={'openai':'OPENAI_API_KEY','anthropic':'ANTHROPIC_API_KEY'}[provider]
            value=os.environ.pop(var,None)
            if not value:
                need(sys.stdin.isatty(),'API key missing; start interactively (never put keys in command arguments)')
                value=getpass.getpass(var+'（非表示、保存しません）: ')
            need(bool(value) and not any(c.isspace() for c in value),'Invalid/empty API key')
            self.values[provider]=value
        return self.values[provider]
    def redact(self,text: str) -> str:
        for val in self.values.values():text=text.replace(val,'[REDACTED]')
        return text


def api_http(provider: str,path: str,body: dict | None,secrets: Secrets,timeout: int=120) -> dict:
    need(provider in API_HOSTS,'Unapproved API provider')
    allowed=(path.startswith('/v1/models/') or path in ('/v1/responses','/v1/responses/input_tokens')) if provider=='openai' else (path.startswith('/v1/models/') or path in ('/v1/messages','/v1/messages/count_tokens'))
    need(allowed and re.fullmatch(r'/[A-Za-z0-9_/.-]+',path),'Unapproved API path')
    key=secrets.get(provider)
    headers={'Content-Type':'application/json','Accept':'application/json'}
    if provider=='openai':headers['Authorization']='Bearer '+key
    else:headers.update({'x-api-key':key,'anthropic-version':'2023-06-01'})
    # Direct TLS, no redirects, proxy variables, SDK retries or inherited API endpoints.
    conn=http.client.HTTPSConnection(API_HOSTS[provider],timeout=timeout,context=ssl.create_default_context())
    start=time.monotonic()
    try:
        conn.request('GET' if body is None else 'POST',path,body=None if body is None else canon(body),headers=headers)
        resp=conn.getresponse();raw=resp.read(32*1024**2+1)
        need(len(raw)<=32*1024**2,'Oversized API response')
        raw=secrets.redact(raw.decode('utf-8',errors='replace')).encode()
        # Only allowlisted response headers are recorded. No request Authorization headers.
        return {'http_status':resp.status,'raw_body_b64':base64.b64encode(raw).decode(),
                'headers':{k:v for k,v in resp.getheaders() if k.lower() in ('request-id','x-request-id','date','content-type')},
                'wall_seconds':time.monotonic()-start,'utc':now()}
    finally:conn.close()


def response_object(envelope: dict) -> dict:
    need(envelope.get('http_status')==200,'API HTTP status '+str(envelope.get('http_status')))
    raw=base64.b64decode(envelope['raw_body_b64'],validate=True)
    obj=parse(raw);need(isinstance(obj,dict),'API response is not an object');return obj


def model_lookup(provider: str,m: dict,secrets: Secrets) -> dict:
    env=api_http(provider,'/v1/models/'+m['id'],None,secrets)
    obj=response_object(env)
    need(obj.get('id')==m['id'],'Model metadata resolved a different ID; no silent substitution')
    return {'requested_model':m['id'],'response':obj,'envelope':env,
            'source':'provider model metadata; does not establish CPU historical usage'}


def cloud_text(provider: str,obj: dict,cfg: dict) -> str:
    need(obj.get('model')==cfg['models'][provider]['id'],'Returned model ID differs; preserve response, do not substitute')
    if provider=='openai':
        require(obj.get('status')=='completed' and not obj.get('error'),'OpenAI incomplete/refused/failed response')
        pieces=[]
        for item in obj.get('output',[]):
            if item.get('type')=='reasoning':continue
            require(item.get('type')=='message' and item.get('role')=='assistant','Unexpected OpenAI output item/tool')
            for content in item.get('content',[]):
                require(content.get('type')=='output_text','Refusal/nontext OpenAI output');pieces.append(content['text'])
        require(len(pieces)==1,'Expected one complete OpenAI text output')
        return pieces[0]
    require(obj.get('type')=='message' and obj.get('stop_reason')=='end_turn','Claude nonterminal/refusal/token cap')
    pieces=[]
    for content in obj.get('content',[]):
        require(content.get('type')=='text','Unexpected Claude tool/thinking/nontext block');pieces.append(content['text'])
    require(len(pieces)==1,'Expected one complete Claude text output');return pieces[0]


def usage_upper(provider: str,obj: dict,m: dict) -> str:
    u=obj.get('usage');need(isinstance(u,dict),'Missing API usage; spending cannot be reconciled')
    if provider=='openai':
        fields=[u.get('input_tokens'),u.get('output_tokens')]
        need(all(type(x) is int and x>=0 for x in fields),'Bad OpenAI usage')
        # Intentionally no cache discount: conservative estimate, not an invoice.
        input_n,output_n=fields
    else:
        keys=('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens')
        need(all(type(u.get(k,0)) is int and u.get(k,0)>=0 for k in keys),'Bad Claude usage')
        need('input_tokens' in u and 'output_tokens' in u,'Incomplete Claude usage')
        input_n=u['input_tokens']+u.get('cache_creation_input_tokens',0)+u.get('cache_read_input_tokens',0)
        output_n=u['output_tokens']
    # 2x input rate reserves also unrequested cache-write/input accounting overhead.
    return str((D(input_n)*D(m['input_usd_per_million'])*2+D(output_n)*D(m['output_usd_per_million']))/D(10**6))


def reserve_cost(count: int,m: dict) -> dict:
    need(type(count) is int and 0<count<100000,'Unexpected input-token count')
    limit=count+max(256,math.ceil(count*.10))
    usd=(D(limit)*D(m['input_usd_per_million'])*2+D(m['max_output_tokens'])*D(m['output_usd_per_million']))/D(10**6)
    return {'counted_input_tokens':count,'reserved_input_tokens':limit,'output_cap':m['max_output_tokens'],
            'reserved_usd':str(usd),'input_price_multiplier':2,
            'not_provider_billing_cap':True,'excludes_gpu_rental_taxes_fx':True}


def make_budget(plan: dict,secrets: Secrets,local_root: Path) -> dict:
    idx=index_requests(plan); cfg=plan['config']; prices={p:cfg['models'][p] for p in ('openai','anthropic')}
    cache={};records={};lookups={}
    for p in ('openai','anthropic'):
        lookups[p]=model_lookup(p,prices[p],secrets)
        jw(local_root/'api-preflight'/('model-'+p+'.json'),lookups[p])
    for cid,r in idx.items():
        p=r['provider']
        if p=='qwen':continue
        body=api_payload(p,r,cfg); cb=count_payload(p,body);key=p+':'+sha(canon(cb))
        if key not in cache:
            path='/v1/responses/input_tokens' if p=='openai' else '/v1/messages/count_tokens'
            env=api_http(p,path,cb,secrets); obj=response_object(env)
            count=obj.get('input_tokens'); need(type(count) is int and count>0,'Token counter missing input_tokens')
            cache[key]={'count':count,'response':env,'request':cb}
            jw(local_root/'api-preflight'/('count-'+sha(key.encode())+'.json'),cache[key])
            print('INPUT_TOKENS_COUNTED='+p+' '+r['task']+' '+r['condition']+' '+str(count),flush=True)
        records[cid]={**reserve_cost(cache[key]['count'],prices[p]),'provider':p,'request_sha256':sha(canon(body))}
    totals={p:sum((D(x['reserved_usd']) for x in records.values() if x['provider']==p),D(0)) for p in prices}
    return {'schema':VERSION,'plan_sha256':sha(canon(plan)),'per_request':records,
            'provider_reserved_usd':{k:str(v) for k,v in totals.items()},
            'full_cohort_reserved_usd':str(sum(totals.values(),D(0))),
            'prices_verified_in_documentation_on':PRICE_DATE,'price_sources':PRICE_REFS,
            'sequential_standard_api_not_batch':True,'new_generation_calls_so_far':0,
            'is_conservative_token_cost_estimate_not_invoice_or_provider_hard_cap':True}


def validate_budget(plan: dict,budget: dict,auth: dict | None = None) -> None:
    need(budget['plan_sha256']==sha(canon(plan)), 'Budget/plan mismatch')
    idx=index_requests(plan)
    expected={cid for cid,r in idx.items() if r['provider'] in API_HOSTS}
    need(set(budget['per_request'])==expected, 'Cloud budget coverage differs')
    totals={p:D(0) for p in API_HOSTS}
    for cid,rule in budget['per_request'].items():
        r=idx[cid];provider=r['provider']
        reconstructed={**reserve_cost(rule['counted_input_tokens'],plan['config']['models'][provider]),
                       'provider':provider,'request_sha256':sha(canon(api_payload(provider,r,plan['config'])))}
        need(rule==reconstructed, 'Request budget or payload changed: '+cid)
        totals[provider]+=D(rule['reserved_usd'])
    need(budget['provider_reserved_usd']=={p:str(x) for p,x in totals.items()},'Provider subtotal differs')
    need(D(budget['full_cohort_reserved_usd'])==sum(totals.values(),D(0)),'Cohort budget sum differs')
    if auth is not None:
        need(auth['approved'] is True and auth['plan_sha256']==sha(canon(plan)) and
             auth['budget_sha256']==sha(canon(budget)),'Authorization seal differs')
        need(D(auth['max_api_usd'])>=D(budget['full_cohort_reserved_usd']),'Approval below full reservation')


def plan_path(local: bool=False) -> Path:
    return Path.home()/LOCAL_REL/'plan.json' if local else ROOT/'control/plan.json'


def remote_status() -> dict:
    d=P.remote_status()
    pp=ROOT/'pending-cloud.json'
    if pp.exists() and d['state']=='RUNNING':d['pending_cloud']=parse(read(pp))
    if plan_path().exists():d['plan_sha256']=hfile(plan_path())
    return d


def wait_cloud(r: dict) -> dict:
    pending={'id':r['id'],'request_sha256':sha(canon(r)),'provider':r['provider'],'utc':now()}
    P.atomic(ROOT/'pending-cloud.json',pending)
    P.update(phase='WAITING_WSL_API_GATEWAY',current_id=r['id'])
    dest=ROOT/'inbox'/(r['id']+'.json');end=min(P.WORK_DEADLINE,time.monotonic()+ACK_SECONDS)
    while not dest.exists():
        need(time.monotonic()<end,'WSL API gateway absent before deadline; no request resent');time.sleep(2)
    package=parse(read(dest));need(package['request_sha256']==pending['request_sha256'],'Inbox request digest differs')
    (ROOT/'pending-cloud.json').unlink()
    return package


def generate_group(plan: dict,g: dict,A,assets) -> list[dict]:
    provider=g['provider'];d=ROOT/'groups'/g['label'];P.public_dirs(d)
    records=[];proc=None
    try:
        for r in g['requests']:
            rd=d/'generation'/r['condition'];P.public_dirs(rd)
            rec={k:r[k] for k in ('id','provider','task','condition','trial','seed','seed_sent_to_provider','messages_sha256')}
            rec.update(model=plan['config']['models'][provider]['id'],generation_status='invalid_generation',error=None)
            jw(rd/'request.json',r);P.update(phase='GENERATING_'+provider.upper(),current_id=r['id'])
            start=time.monotonic()
            try:
                if provider=='qwen':
                    if proc is None:proc=P.start_model(A,assets,d/('inference-'+r['condition']))
                    rendered=A.api('/apply-template',{'messages':r['messages']})['prompt']
                    need(all(x['content'] in rendered for x in r['messages']),'Template omitted common prompt')
                    save(rd/'rendered.txt',rendered.encode())
                    ids=A.api('/tokenize',{'content':rendered,'add_special':True,'parse_special':True})['tokens']
                    need(ids and all(type(x) is int and x>=0 for x in ids),'Invalid Qwen input token IDs')
                    cap=plan['config']['models']['qwen']['max_output_tokens']
                    need(len(ids)+cap+16<=32768,'Qwen context budget; no truncation')
                    body=dict(A.SAMPLING,seed=r['seed'],prompt=ids,n_predict=cap,stream=False,return_tokens=True,id_slot=0)
                    jw(rd/'wire-request.json',body);jw(rd/'intent.json',{'id':r['id'],'attempt':1,'utc':now()})
                    P.update(generation_calls=P.STATE.get('generation_calls',0)+1)
                    obj=A.api('/completion',body,timeout=min(REQUEST_SECONDS,max(1,P.WORK_DEADLINE-time.monotonic())))
                    jw(rd/'response.json',obj)
                    need(obj.get('tokens_evaluated')==len(ids),'Native input-token count mismatch')
                    require(obj.get('truncated') is False and obj.get('stop_type') in ('eos','word'),'Qwen incomplete output')
                    require(type(obj.get('timings',{}).get('predicted_n')) is int and 0<obj['timings']['predicted_n']<=cap+8,'Invalid Qwen token count')
                    text=obj.get('content');rec['usage']=obj.get('timings',{})
                else:
                    package=wait_cloud(r);jw(rd/'api-package.json',package)
                    P.update(generation_calls=P.STATE.get('generation_calls',0)+1)
                    need(package.get('provider')==provider,'Wrong cloud provider')
                    if package.get('fatal_error'):raise Blocked('Cloud API configuration/budget error; see local ledger: '+r['id'])
                    if package.get('transport_uncertain'):
                        rec.update(generation_status='transport_uncertain',error=package['error'],wall_seconds=time.monotonic()-start);records.append(rec);jw(rd/'record.json',rec);continue
                    obj=response_object(package['envelope']);jw(rd/'response.json',obj)
                    rec['usage']=obj.get('usage',{});rec['token_cost_upper_usd']=package['usage_upper_usd']
                    text=cloud_text(provider,obj,plan['config'])
                source,b=parse_candidate(text,r['task']);save(rd/'candidate.cu',source.encode())
                rec.update(generation_status='saved',source_sha256=sha(source.encode()),source_equals_original=source==original(r['task']),block=b)
            except NumericFailure as exc:rec.update(generation_status='invalid_generation',error=str(exc))
            except (OSError,http.client.HTTPException,TimeoutError) as exc:
                rec.update(generation_status='transport_uncertain',error=type(exc).__name__)
                P.close_child(proc);proc=None
            rec['wall_seconds']=time.monotonic()-start;jw(rd/'record.json',rec);records.append(rec)
            print('GPU004_GENERATION_TERMINAL '+r['id']+' '+rec['generation_status'],flush=True)
    finally:
        P.close_child(proc);jw(d/'model-stopped.json',{'owned_model_stopped':True,'utc':now()})
    P.no_other_gpu();return records


def summarize(outcomes: list[dict],plan: dict) -> dict:
    need(len(outcomes)==TOTAL and {o['id'] for o in outcomes}==set(index_requests(plan)),'270-slot accounting gap')
    rows=[];by_provider={}
    for provider in PROVIDERS:
        sub=[o for o in outcomes if o['provider']==provider]
        valid=[m for o in sub for m in o['measurements'] if m['measurement_valid']]
        by_provider[provider]={'model':plan['config']['models'][provider]['id'],'candidate_slots':len(sub),
             'generation_status_counts':dict(Counter(o['generation_status'] for o in sub)),
             'correctness_passed':sum(o['correctness_passed'] for o in sub),'valid_size_measurements':len(valid),
             'size_speedups_gt_1_02':sum(m['speedup_gt_1_02'] for m in valid),
             'same_source_saved':sum(o.get('source_equals_original',False) for o in sub)}
    for o in outcomes:
        for m in o['measurements'] or [{}]:
            rows.append({k:o.get(k) for k in ('id','provider','model','task','condition','trial','seed_sent_to_provider','generation_status','stage','correctness_passed','source_equals_original','block','error')}|m)
    summary={'state':'GPU004_MULTIMODEL_270_COMPLETE','candidate_slots':TOTAL,'providers':by_provider,
             'generation_intents_accounted':TOTAL,'independent_workloads':6,'development_only':True,'large_30_task_generation_started':False,
             'shared_prompt_content':True,'numerical_core_sha256':CORE_SHA,'source_bundle_sha256':SOURCE_SHA,
             'no_best_of_selection':True,'no_error_tolerance_changes':True,'original_results_overwritten':False,
             'formal_equivalence_proven':False,'whole_GPU_study_complete':False,'utc':now()}
    d=ROOT/'final';jw(d/'summary.json',summary);jw(d/'outcomes.json',outcomes);jw(d/'protocol.json',plan)
    save(d/'outcomes.csv',csv_bytes(rows))
    # Paired within this cohort and within model; do not combine historical timings.
    idx={(o['provider'],o['task'],o['trial'],o['condition']):o for o in outcomes};pairs=[]
    for p in PROVIDERS:
        for t in C.TASKS:
            for trial in REPEATS:
                for a,b in [('S1','P0'),('S2','P0'),('S1','W1'),('S2','W2')]:
                    x,y=idx[p,t,trial,a],idx[p,t,trial,b]
                    ys={tuple(m['shape']):m for m in y['measurements']}
                    for m in x['measurements']:
                        n=ys.get(tuple(m['shape']))
                        if n and m['measurement_valid'] and n['measurement_valid']:
                            pairs.append({'provider':p,'task':t,'trial':trial,'contrast':a+'_over_'+b,
                               'shape':m['shape'],'speedup_ratio':m['speedup']/n['speedup'],
                               'same_block':x['block']==y['block'],'same_source':x.get('source_sha256')==y.get('source_sha256')})
    save(d/'matched_pairs_descriptive.csv',csv_bytes(pairs))
    return summary


def csv_bytes(rows: list[dict]) -> bytes:
    if not rows:return b''
    out=io.StringIO();keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(out,keys);w.writeheader();w.writerows(rows);return out.getvalue().encode()


def worker(allow: bool) -> None:
    P.remote_guard();need(allow,'Explicit ephemeral/local-backup authorization required')
    plan=parse(read(plan_path()));validate_plan(plan)
    authorization=parse(read(ROOT/'control/authorization.json'))
    need(authorization['plan_sha256']==sha(canon(plan)) and authorization['approved'] is True,'Missing budget/prompt authorization')
    P.WORK_DEADLINE=time.monotonic()+RUN_SECONDS;os.umask(0o022);P.public_dirs(ROOT);P.public_dirs(ROOT/'control')
    (ROOT/'control/runner.py').chmod(0o444)
    def stop(*_):raise Blocked('Worker stopped; previous attempts retained, no automatic retry')
    signal.signal(signal.SIGTERM,stop)
    try:
        with P.lock('/workspace/gpu-code-pilot-exclusive.lock'):
            P.update(phase='ENVIRONMENT_AND_SOURCE_CHECK',generation_calls=0,evaluation_terminal=0,started_utc=now())
            observed=probe_environment()
            need(environment_identity(observed)==environment_identity(plan['environment']),'Environment changed since quote/plan; no generation started')
            need(observed['free_disk_bytes']>=4*1024**3,'Need 4GiB free; no old files deleted')
            install_sources();jw(ROOT/'setup/protocol.json',plan);jw(ROOT/'setup/environment.json',observed)
            save(ROOT/'setup/runner.py',read(__file__));jw(ROOT/'setup/authorization.json',authorization)
            helper=C.build_helper();jw(ROOT/'setup/host-helper-identity.json',{'sha256':hfile(helper)})
            A=P.module_a();A.ROOT=ROOT
            with contextlib.redirect_stdout(sys.stderr):assets=A.cached_assets();gi=A.gpu_info()
            need(gi['uuid']==P.EXPECTED_GPU,'Wrong inference GPU');jw(ROOT/'setup/inference-assets.json',assets[3])
            C.checkpoint(ROOT/'setup','setup')
            C.baseline_preflight(helper);C.checkpoint(ROOT/'preflight','original-controls')
            outcomes=[]
            for g in plan['groups']:
                need(time.monotonic()<P.WORK_DEADLINE,'Run deadline')
                records=generate_group(plan,g,A,assets)
                C.checkpoint(ROOT/'groups'/g['label']/'generation','generation-'+g['label'])
                result=C.evaluate_group(g,records,helper);outcomes.extend(result)
                C.checkpoint(ROOT/'groups'/g['label'],'evaluated-'+g['label'])
                with contextlib.redirect_stdout(sys.stderr):A.verify_cached_unchanged(assets[5])
                P.update(completed_groups=len(outcomes)//5,evaluation_terminal=len(outcomes))
            summary=summarize(outcomes,plan);rec=P.archive_dir(ROOT/'final','summary');C.wait_ack(rec)
            jw(ROOT/'completion.json',{'summary_sha256':hfile(ROOT/'final/summary.json'),'summary_checkpoint':rec,'utc':now()})
            P.update(phase='COMPLETE');print(summary['state'],flush=True)
    except BaseException as exc:
        P.atomic(ROOT/'failure.json',{'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'utc':now()})
        P.update(phase='BLOCKED',error=str(exc));raise


def immutable_json(path: Path,obj: dict) -> None:
    if path.exists():need(read(path)==canon(obj),'Existing immutable file differs: '+str(path))
    else:jw(path,obj)


def api_pending_package(r: dict,plan: dict,budget: dict,root: Path,secrets: Secrets) -> dict:
    provider=r['provider'];need(provider in ('openai','anthropic'),'Not a cloud slot')
    d=root/'api-ledger'/r['id'];d.mkdir(parents=True,exist_ok=True);P.safe(d)
    package_path=d/'package.json';intent_path=d/'intent.json'
    body=api_payload(provider,r,plan['config']);pin=sha(canon(body));rule=budget['per_request'][r['id']]
    need(pin==rule['request_sha256'],'Quoted API payload changed')
    if package_path.exists():
        package=parse(read(package_path));need(package['request_sha256']==sha(canon(r)),'Cached package mismatch');return package
    need(not intent_path.exists(),'Indeterminate API attempt retained, never resending: '+r['id']+'; use --abandon-uncertain only after reviewing provider usage')
    immutable_json(d/'request.json',body)
    # Fsync the attempt intent BEFORE any network submission. A crash cannot trigger a free retry.
    jw(intent_path,{'id':r['id'],'attempt':1,'request_sha256':pin,'reserved_usd':rule['reserved_usd'],'utc':now()})
    package={'id':r['id'],'provider':provider,'request_sha256':sha(canon(r)),'attempt':1,'utc':now()}
    try:
        endpoint='/v1/responses' if provider=='openai' else '/v1/messages'
        env=api_http(provider,endpoint,body,secrets,REQUEST_SECONDS);package['envelope']=env
        if env['http_status']!=200:
            package.update(fatal_error=True,error='API HTTP '+str(env['http_status']),charge_unknown=True)
        else:
            obj=response_object(env)
            need(obj.get('model')==plan['config']['models'][provider]['id'],'Provider returned a different model ID')
            cost=usage_upper(provider,obj,plan['config']['models'][provider]);package['usage_upper_usd']=cost
            if D(cost)>D(rule['reserved_usd']):package.update(fatal_error=True,error='Usage exceeded reservation; stop before another call')
    except BaseException as exc:
        package.update(transport_uncertain=True,error=type(exc).__name__+': '+secrets.redact(str(exc)),
                       charge_unknown=True,retained_reservation_usd=rule['reserved_usd'])
        if isinstance(exc,Blocked):package['fatal_error']=True
        jw(package_path,package)
        if isinstance(exc,(KeyboardInterrupt,SystemExit)):raise
        return package
    jw(package_path,package);return package


def ledger_report(root: Path,budget: dict) -> dict:
    attempts=[];total=D(0);unknown=0
    for p in sorted((root/'api-ledger').glob('*/intent.json')):
        intent=parse(read(p));need(intent['id'] in budget['per_request'],'Unquoted API intent')
        pkg=p.with_name('package.json');rec=parse(read(pkg)) if pkg.exists() else {}
        if rec.get('usage_upper_usd') is not None:amount=D(rec['usage_upper_usd'])
        else:amount=D(intent['reserved_usd']);unknown+=1
        total+=amount;attempts.append({'id':intent['id'],'accounted_upper_usd':str(amount),'response_saved':pkg.exists(),
                                     'usage_known':rec.get('usage_upper_usd') is not None})
    return {'attempts':attempts,'attempt_count':len(attempts),'token_cost_upper_usd_at_configured_rates':str(total),
            'unknown_usage_attempts':unknown,'not_an_invoice':True,'gpu_rental_excluded':True,'utc':now()}


def local_root() -> Path:
    root=P.safe(Path.home()/LOCAL_REL);root.mkdir(parents=True,exist_ok=True);root.chmod(0o700);return root


def prepare_local(con,secrets: Secrets) -> tuple[dict,dict]:
    root=local_root();pp=root/'plan.json'
    if pp.exists():
        plan=parse(read(pp));validate_plan(plan)
    else:
        cfgpath=root/'models.json'
        if cfgpath.exists():cfg=parse(read(cfgpath));validate_settings(cfg)
        else:cfg=choose_settings();jw(cfgpath,cfg)
        env=parse(con.run(remote_cmd('--_probe')));plan=make_plan(cfg,env)
        jw(pp,plan)
    # Cost preflight output uses a dedicated directory, retained on any failure.
    bp=root/'budget.json'
    if bp.exists():budget=parse(read(bp));need(budget['plan_sha256']==sha(canon(plan)),'Budget for another plan')
    else:
        attempt_dir=root/('preflight-'+uuid.uuid4().hex);attempt_dir.mkdir(mode=0o700)
        budget=make_budget(plan,secrets,attempt_dir);jw(bp,budget)
    validate_budget(plan,budget)
    ap=root/'authorization.json'
    if ap.exists():
        auth=parse(read(ap));need(auth['plan_sha256']==sha(canon(plan)) and auth['budget_sha256']==sha(canon(budget)) and auth['approved'] is True,'Authorization mismatch')
    else:
        print('\n=== FROZEN PLAN / CONFIGURED PRICE RESERVATION ===')
        print(json.dumps({'models':plan['config']['models'],'candidate_slots':TOTAL,'cloud_requests':180,
                          'provider_reserved_usd':budget['provider_reserved_usd'],
                          'full_cohort_reserved_usd':budget['full_cohort_reserved_usd'],
                          'excluded':'GPU rental, tax, exchange rates; not an invoice'},ensure_ascii=False,indent=2))
        print('プロンプトと実験環境: '+str(pp))
        limit=input('この新規コホートに許可するAPI上限（USD数値。空欄は中止）: ').strip()
        need(bool(re.fullmatch(r'\d+(?:\.\d{1,4})?',limit)) and D(limit)>0,'Explicit positive dollar limit required')
        need(D(limit)>=D(budget['full_cohort_reserved_usd']),'Budget below full-cohort reservation; no generation sent')
        consent=input('料金・モデル・プロンプトを確認して開始する場合だけ START 270 と入力: ').strip()
        need(consent=='START 270','No authorization; no model generation sent')
        auth={'approved':True,'plan_sha256':sha(canon(plan)),'budget_sha256':sha(canon(budget)),
              'max_api_usd':limit,'full_cohort_reserved_usd':budget['full_cohort_reserved_usd'],
              'price_date':PRICE_DATE,'not_a_provider_billing_cap':True,'utc':now()}
        jw(ap,auth)
    con.run(remote_cmd('--_put-plan'),data=canon({'plan':plan,'authorization':auth}))
    return plan,budget


def remote_cmd(*args) -> list[str]:
    return ['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),*args]


def local(mode: str,allow: bool=False) -> None:
    need(os.geteuid()!=0,'Run from WSL as regular user, without sudo')
    secrets=Secrets()
    # Remove API credentials from the inherited environment before creating SSH subprocesses.
    for p,var in [('openai','OPENAI_API_KEY'),('anthropic','ANTHROPIC_API_KEY')]:
        value=os.environ.pop(var,None)
        if value:secrets.values[p]=value
    A=P.module_a();A.fingerprint_check(Path.home()/'.ssh/id_ed25519');con=A.Connection();root=local_root()
    try:
        if mode=='run':
            need(allow,'Use --allow-ephemeral-with-local-checkpoints')
            raw=read(__file__);print(con.run(['/usr/bin/python3','-I','-S','-B','-c',P.install_text(sha(raw))],data=raw).decode())
            plan,budget=prepare_local(con,secrets)
            doc=parse(con.run(remote_cmd('--_launch','--allow-ephemeral-with-local-checkpoints')))
            print('GPU004_MULTIMODEL_STARTED; 270 slots; cloud keys remain in WSL',flush=True)
        else:
            if mode=='stop':print(con.run(remote_cmd('--_stop')).decode());return
            plan=parse(read(root/'plan.json'));validate_plan(plan);budget=parse(read(root/'budget.json'))
            doc=parse(con.run(remote_cmd('--_status')))
        validate_budget(plan,budget,parse(read(root/'authorization.json')))
        expected=sha(canon(plan));seen=set();idx=index_requests(plan)
        while True:
            need(doc.get('plan_sha256')==expected,'Remote plan differs from locally approved plan')
            if mode=='status':print(json.dumps(doc,ensure_ascii=False,indent=2));return
            for rec in doc['receipts']:
                if rec['label'] not in seen:
                    P.checkpoint_collect(con,rec);seen.add(rec['label'])
                    print('GPU004_LOCAL_CHECKPOINT_VERIFIED '+rec['label'],flush=True)
            public={'state':doc['state'],**doc.get('progress',{})}
            print(json.dumps(public,ensure_ascii=False),flush=True)
            if doc['state'] in ('BLOCKED','INTERRUPTED'):
                P.atomic(root/'last-status.json',doc);print(json.dumps(doc.get('failure',{}),ensure_ascii=False,indent=2))
                raise Blocked('Remote stopped; no automatic generation/numerical retry')
            if doc['state']=='COMPLETE':
                P.atomic(root/'final-status.json',doc);P.atomic(root/'api-usage-upper.json',ledger_report(root,budget))
                print(json.dumps(doc['summary'],ensure_ascii=False,indent=2));print('GPU004_MULTIMODEL_LOCAL_COPY_VERIFIED',flush=True);return
            need(doc['state']=='RUNNING','Worker not running')
            if mode=='collect':return
            pending=doc.get('pending_cloud')
            if pending:
                r=idx.get(pending['id']);need(r is not None and r['provider'] in API_HOSTS,'Unknown remote API request')
                need(pending['request_sha256']==sha(canon(r)),'Pending request changed')
                if not (root/'api-ledger'/r['id']/'package.json').exists():secrets.get(r['provider'])
                prior=ledger_report(root,budget)
                approval=parse(read(root/'authorization.json'))
                if not (root/'api-ledger'/r['id']/'intent.json').exists():
                    need(D(prior['token_cost_upper_usd_at_configured_rates'])+D(budget['per_request'][r['id']]['reserved_usd'])<=D(approval['max_api_usd']), 'API budget exhausted before submission')
                package=api_pending_package(r,plan,budget,root,secrets)
                report=ledger_report(root,budget);P.atomic(root/'api-usage-upper.json',report)
                auth=parse(read(root/'authorization.json'))
                if D(report['token_cost_upper_usd_at_configured_rates'])>D(auth['max_api_usd']):
                    package.update(fatal_error=True,error='Global API budget exceeded; no additional submissions')
                con.run(remote_cmd('--_supply',r['id']),data=canon(package))
            time.sleep(5);doc=parse(con.run(remote_cmd('--_status')))
    except KeyboardInterrupt:
        print('WSL_WATCH_CLOSED; worker waits for API/checkpoint. --watch resumes without replaying completed calls. Pod remains billed.')
    finally:con.close()


def abandon_uncertain(cid: str) -> None:
    root=local_root();plan=parse(read(root/'plan.json'));r=index_requests(plan).get(cid)
    need(r is not None and r['provider'] in API_HOSTS,'Unknown cloud request ID')
    d=root/'api-ledger'/cid;intent=parse(read(d/'intent.json'));need(not(d/'package.json').exists(),'Response already recorded')
    need(input('失われた応答を再送せず失敗として残す場合だけ '+cid+' と入力: ').strip()==cid,'Not confirmed')
    jw(d/'package.json',{'id':cid,'provider':r['provider'],'request_sha256':sha(canon(r)),'attempt':1,
       'transport_uncertain':True,'error':'User abandoned an indeterminate attempt without resubmission',
       'charge_unknown':True,'retained_reservation_usd':intent['reserved_usd'],'utc':now()})
    print('UNCERTAIN_ATTEMPT_RECORDED_WITHOUT_RESUBMISSION; resume --watch')


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True)
    for arg in ('run','watch','status','collect','stop','self-test','numeric-core-self-test','_probe','_put-plan','_worker','_launch','_status','_stop'):
        g.add_argument('--'+arg,action='store_true')
    g.add_argument('--_numeric');g.add_argument('--_send');g.add_argument('--_ack',nargs=2)
    g.add_argument('--_supply');g.add_argument('--abandon-uncertain')
    ap.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true');a=ap.parse_args()
    if a.self_test:self_test();return
    if a.numeric_core_self_test:C.self_test();return
    if a._numeric:sys.exit(C.numeric_job(a._numeric))
    if a.abandon_uncertain:abandon_uncertain(a.abandon_uncertain);return
    if a._probe:print(json.dumps(probe_environment()));return
    if a._put_plan:
        P.remote_guard();raw=sys.stdin.buffer.read(4*1024**2+1);need(len(raw)<=4*1024**2,'Oversized plan')
        doc=parse(raw);validate_plan(doc['plan']);auth=doc['authorization']
        need(auth['approved'] is True and auth['plan_sha256']==sha(canon(doc['plan'])),'Plan not authorized')
        immutable_json(plan_path(),doc['plan']);immutable_json(ROOT/'control/authorization.json',auth)
        print('PLAN_AND_AUTHORIZATION_PINNED');return
    if a._worker:worker(a.allow_ephemeral_with_local_checkpoints);return
    if a._launch:
        P.remote_guard();need(plan_path().exists() and (ROOT/'control/authorization.json').exists(),'Missing frozen plan')
        P.remote_launch(a.allow_ephemeral_with_local_checkpoints);print(json.dumps(remote_status()));return
    if a._status:print(json.dumps(remote_status()));return
    if a._supply:
        P.remote_guard();plan=parse(read(plan_path()));idx=index_requests(plan);r=idx.get(a._supply)
        need(r is not None and r['provider'] in API_HOSTS,'Unplanned API response')
        raw=sys.stdin.buffer.read(40*1024**2+1);need(len(raw)<=40*1024**2,'Oversized API envelope');pkg=parse(raw)
        need(pkg['id']==r['id'] and pkg['provider']==r['provider'] and pkg['request_sha256']==sha(canon(r)),'Wrong response assignment')
        immutable_json(ROOT/'inbox'/(r['id']+'.json'),pkg);print('API_RESULT_STORED');return
    if a._send or a._ack:
        P.remote_guard();label=a._send or a._ack[0];need(re.fullmatch(r'[a-z0-9-]+',label),'Invalid archive label')
        rec=parse(read(ROOT/'receipts'/(label+'.json')))
        if a._send:
            f=ROOT/'archives'/(label+'.tar.gz');need(hfile(f)==rec['sha256'],'Archive changed')
            with f.open('rb') as handle:shutil.copyfileobj(handle,sys.stdout.buffer,1024**2)
        else:
            need(a._ack[1]==rec['sha256'],'ACK digest mismatch');immutable_json(ROOT/'acks'/(label+'.json'),{'sha256':rec['sha256']});print('ACK_STORED')
        return
    if a._stop:
        P.remote_guard();rec=parse(read(ROOT/'launch.json'))
        if P.alive(rec):os.kill(rec['pid'],signal.SIGTERM)
        print('OWNED_GPU004_WORKER_STOP_REQUESTED; NO_POD_TERMINATION');return
    local(next(s for s in ('run','watch','status','collect','stop') if getattr(a,s)),a.allow_ephemeral_with_local_checkpoints)

def self_test() -> None:
    class T(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.cfg={'schema':VERSION,'models':copy.deepcopy(PRESETS),'model_provenance':'explicit_new_gpu_cohort_ids'}
            cls.env={'gpu':{'name':'NVIDIA A40','compute_capability':[8,6],'warp_size':32,
                           'static_shared_memory_per_block':49152,'registers_per_block':65536,
                           'max_threads_per_multiprocessor':1536,'shared_memory_per_multiprocessor':102400,
                           'multiprocessors':84,'l2_bytes':6291456,'max_threads_per_block':1024,'memory_bytes':48305799168},
                     'gpu_uuid':P.EXPECTED_GPU,'driver_version':'570.195.03','nvrtc_version':[12,8],
                     'nvrtc_sha256':'a'*64,'sanitizer_sha256':'b'*64,'host_compiler':'fixture-g++',
                     'core_sha256':CORE_SHA,'os_release':'fixture-linux','observed_utc':'fixture',
                     'free_disk_bytes':10*1024**3,'storage_persistence_verified':False}
            cls.plan=make_plan(cls.cfg,cls.env)
        def setUp(self):
            self.tmp=tempfile.TemporaryDirectory(prefix='gpu004-tests-');self.old=ROOT
            configure(Path(self.tmp.name)/'remote');ROOT.mkdir()
            self.local=Path(self.tmp.name)/'local';self.local.mkdir()
            self.plan=copy.deepcopy(self.__class__.plan)
            self.idx=index_requests(self.plan)
            self.r=next(r for r in self.idx.values() if r['provider']=='openai')
            self.a=next(r for r in self.idx.values() if r['provider']=='anthropic')
            self.budget={'plan_sha256':sha(canon(self.plan)),'per_request':{r['id']:{**reserve_cost(4500,self.cfg['models'][r['provider']]),
                    'provider':r['provider'],'request_sha256':sha(canon(api_payload(r['provider'],r,self.cfg)))}
                    for r in self.idx.values() if r['provider'] in API_HOSTS}}
            sums={p:sum((D(x['reserved_usd']) for x in self.budget['per_request'].values() if x['provider']==p),D(0)) for p in API_HOSTS}
            self.budget.update(provider_reserved_usd={p:str(x) for p,x in sums.items()},full_cohort_reserved_usd=str(sum(sums.values(),D(0))))
        def tearDown(self):
            configure(self.old);P.WORK_DEADLINE=None;self.tmp.cleanup()
        def text(self,r=None):
            r=r or self.r
            return json.dumps({'block':C.SPECS[r['task']]['base']})+'\n'+original(r['task'])
        def response(self,p='openai',r=None):
            r=r or (self.r if p=='openai' else self.a)
            common={'model':self.cfg['models'][p]['id'],'usage':{'input_tokens':4000,'output_tokens':300}}
            if p=='openai':return common|{'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':self.text(r)}]}]}
            return common|{'type':'message','stop_reason':'end_turn','content':[{'type':'text','text':self.text(r)}]}
        def envelope(self,obj=None,status=200):
            return {'http_status':status,'raw_body_b64':base64.b64encode(canon(obj or self.response())).decode(),'headers':{},'utc':'fixture'}
        def test_core_pin(self):self.assertEqual(sha(gzip.decompress(base64.b64decode(CORE_EMBED))),CORE_SHA)
        def test_source_manifest(self):
            files=source_files();self.assertEqual(len(files),22);self.assertIn(b'OHIO STATE',files['LICENSE'])
        def test_source_intake_original_unchanged(self):
            install_sources()
            for t in C.TASKS:self.assertEqual(read(ROOT/'setup/sources'/(t+'.cu')).decode(),original(t))
        def test_source_intake_no_repeat(self):
            install_sources()
            with self.assertRaises(FileExistsError):install_sources()
        def test_registry_not_30_enabled(self):
            self.assertFalse(self.plan['additional_24_tasks_enabled']);self.assertTrue(bool(registry()))
        def test_270_unique_ids(self):self.assertEqual(len(self.idx),270)
        def test_54_groups(self):self.assertEqual(len(self.plan['groups']),54)
        def test_90_per_provider(self):self.assertEqual(Counter(r['provider'] for r in self.idx.values()),dict.fromkeys(PROVIDERS,90))
        def test_shared_strings_all_providers(self):validate_plan(self.plan)
        def test_only_gpu_block_varies(self):
            for t in C.TASKS:
                strs={re.sub(r'<gpu_information>.*?</gpu_information>','',messages_for(t,a,self.env)[1]['content'],flags=re.S) for a in C.ARMS}
                self.assertEqual(len(strs),1)
        def test_p0_does_not_name_actual_gpu(self):
            for t in C.TASKS:self.assertNotIn('A40',messages_for(t,'P0',self.env)[1]['content'])
        def test_p0_no_architecture_flag(self):self.assertNotIn('sm_86',messages_for('gemm','P0',self.env)[1]['content'])
        def test_hardware_fields_equal_sets(self):
            x=gpu_profiles(self.env['gpu']);self.assertEqual(set(json.loads(x['S2'].split('\n',1)[1])),set(json.loads(x['W2'].split('\n',1)[1])))
        def test_11_hardware_fields(self):self.assertEqual(len(json.loads(gpu_profiles(self.env['gpu'])['S2'].split('\n',1)[1])),11)
        def test_software_version_in_prompt(self):self.assertIn('"version": [12, 8]',messages_for('gemm','P0',self.env)[1]['content'])
        def test_evaluation_sizes_in_prompt(self):self.assertIn('[[128, 128, 128], [256, 256, 256]]',messages_for('gemm','P0',self.env)[1]['content'])
        def test_objective_in_prompt(self):self.assertIn('equal-weight geometric mean',messages_for('gemm','S1',self.env)[1]['content'])
        def test_prompt_mutation_refused(self):
            self.plan['groups'][0]['requests'][0]['messages'][1]['content']+='boost'
            with self.assertRaises(Blocked):validate_plan(self.plan)
        def test_unsupported_model_no_fallback(self):
            cfg=copy.deepcopy(self.cfg);cfg['models']['openai']['id']='latest'
            with self.assertRaises(Blocked):validate_settings(cfg)
        def test_no_credentials_in_config(self):
            cfg=copy.deepcopy(self.cfg);cfg['models']['openai']['api_key']='fake'
            with self.assertRaises(Blocked):validate_settings(cfg)
        def test_empty_model_rejected(self):
            cfg=copy.deepcopy(self.cfg);cfg['models']['anthropic']['id']=''
            with self.assertRaises(Blocked):validate_settings(cfg)
        def test_changed_api_cap_refused(self):
            cfg=copy.deepcopy(self.cfg);cfg['models']['openai']['max_output_tokens']=999
            with self.assertRaises(Blocked):validate_settings(cfg)
        def test_claude_price_after_september(self):
            self.assertEqual(PRESETS['anthropic']['input_usd_per_million'],'3');self.assertEqual(PRESETS['anthropic']['output_usd_per_million'],'15')
        def test_changed_gpu_uuid(self):
            e=copy.deepcopy(self.env);e['gpu_uuid']='wrong'
            with self.assertRaises(Blocked):check_environment(e)
        def test_changed_nvrtc(self):
            e=copy.deepcopy(self.env);e['nvrtc_version']=[13,1]
            with self.assertRaises(Blocked):check_environment(e)
        def test_launch_header_all_valid(self):
            for t in C.TASKS:
                for b in C.allowed_blocks(t):
                    src,block=parse_candidate(json.dumps({'block':list(b)})+'\n'+original(t),t)
                    self.assertEqual(src,original(t));self.assertEqual(block,list(b))
        def test_old_placeholder_rejected(self):
            with self.assertRaises(NumericFailure):parse_candidate('// BLOCK X Y, (64, 4)\n'+original('gemm'),'gemm')
        def test_metadata_duplicate_key(self):
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[32,8],"block":[64,4]}\n'+original('gemm'),'gemm')
        def test_metadata_extra_key(self):
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[32,8],"host":"run"}\n'+original('gemm'),'gemm')
        def test_metadata_bool(self):
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[true,8]}\n'+original('gemm'),'gemm')
        def test_metadata_float(self):
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[32.0,8]}\n'+original('gemm'),'gemm')
        def test_block_outside_choices(self):
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[1024,8]}\n'+original('gemm'),'gemm')
        def test_single_outer_fence_consistent(self):
            s='```cuda\n'+self.text()+'\n```';self.assertEqual(parse_candidate(s,self.r['task'])[0],original(self.r['task']))
        def test_multiple_fences_rejected(self):
            with self.assertRaises(NumericFailure):parse_candidate('```cuda\n'+self.text()+'\n```\n```cuda\nmore\n```',self.r['task'])
        def test_host_code_rejected(self):
            with self.assertRaises(NumericFailure):parse_candidate(self.text()+'int main(){return 0;}\n',self.r['task'])
        def test_unknown_callable_still_rejected(self):
            src=C.signature('gemm')+' { RN32(1); }'
            with self.assertRaises(NumericFailure):parse_candidate('{"block":[32,8]}\n'+src,'gemm')
        def test_openai_same_content(self):self.assertEqual(api_payload('openai',self.r,self.cfg)['input'],self.r['messages'])
        def test_anthropic_same_content(self):
            b=api_payload('anthropic',self.a,self.cfg);self.assertEqual(b['system'],self.a['messages'][0]['content']);self.assertEqual(b['messages'],[self.a['messages'][1]])
        def test_claude_no_unsupported_sampling(self):
            b=api_payload('anthropic',self.a,self.cfg)
            self.assertTrue(all(k not in b for k in ('temperature','top_p','seed')));self.assertEqual(b['thinking'],{'type':'disabled'})
        def test_openai_no_tools_storage_truncation(self):
            b=api_payload('openai',self.r,self.cfg);self.assertFalse(b['store']);self.assertEqual(b['tools'],[]);self.assertEqual(b['truncation'],'disabled')
        def test_count_payload_no_generation_options(self):
            b=count_payload('openai',api_payload('openai',self.r,self.cfg));self.assertNotIn('max_output_tokens',b);self.assertNotIn('stream',b)
        def test_counting_not_character_estimate(self):
            for p,r in [('openai',self.r),('anthropic',self.a)]:
                self.assertIn('model',count_payload(p,api_payload(p,r,self.cfg)))
        def test_completed_openai_extraction(self):self.assertEqual(cloud_text('openai',self.response(),self.cfg),self.text())
        def test_completed_claude_extraction(self):self.assertEqual(cloud_text('anthropic',self.response('anthropic'),self.cfg),self.text(self.a))
        def test_openai_incomplete_not_candidate(self):
            o=self.response();o['status']='incomplete'
            with self.assertRaises(NumericFailure):cloud_text('openai',o,self.cfg)
        def test_claude_cap_not_candidate(self):
            o=self.response('anthropic');o['stop_reason']='max_tokens'
            with self.assertRaises(NumericFailure):cloud_text('anthropic',o,self.cfg)
        def test_returned_model_change_blocks(self):
            o=self.response();o['model']='unexpected'
            with self.assertRaises(Blocked):cloud_text('openai',o,self.cfg)
        def test_tool_output_rejected(self):
            o=self.response();o['output']=[{'type':'function_call'}]
            with self.assertRaises(NumericFailure):cloud_text('openai',o,self.cfg)
        def test_refusal_rejected(self):
            o=self.response();o['output'][0]['content']=[{'type':'refusal','refusal':'no'}]
            with self.assertRaises(NumericFailure):cloud_text('openai',o,self.cfg)
        def test_missing_usage_blocks(self):
            with self.assertRaises(Blocked):usage_upper('openai',{},PRESETS['openai'])
        def test_negative_usage_blocks(self):
            o=self.response();o['usage']['input_tokens']=-1
            with self.assertRaises(Blocked):usage_upper('openai',o,PRESETS['openai'])
        def test_cost_reserve_decimal(self):
            r=reserve_cost(1000,PRESETS['openai']);self.assertEqual(r['reserved_input_tokens'],1256);self.assertEqual(D(r['reserved_usd']),D('0.103328'))
        def test_noninteger_counter_rejected(self):
            with self.assertRaises(Blocked):reserve_cost(True,PRESETS['openai'])
        def test_usage_includes_all_output_tokens(self):
            o=self.response();o['usage'].update(output_tokens=10000,output_tokens_details={'reasoning_tokens':9500})
            self.assertEqual(D(usage_upper('openai',o,PRESETS['openai'])),D('0.136'))
        def test_claude_cached_tokens_included(self):
            o=self.response('anthropic');o['usage'].update(cache_creation_input_tokens=100,cache_read_input_tokens=1000)
            self.assertEqual(D(usage_upper('anthropic',o,PRESETS['anthropic'])),D('0.0351'))
        def test_request_cache_no_resubmission(self):
            with mock.patch(__name__+'.api_http',return_value=self.envelope()) as f:
                a=api_pending_package(self.r,self.plan,self.budget,self.local,Secrets());b=api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())
                self.assertEqual(a,b);self.assertEqual(f.call_count,1)
        def test_intent_before_submission(self):
            def send(*args,**kwargs):
                self.assertTrue((self.local/'api-ledger'/self.r['id']/'intent.json').exists());return self.envelope()
            with mock.patch(__name__+'.api_http',side_effect=send):api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())
        def test_indeterminate_intent_not_retried(self):
            d=self.local/'api-ledger'/self.r['id'];jw(d/'intent.json',{'id':self.r['id'],'reserved_usd':'1'})
            with mock.patch(__name__+'.api_http') as f:
                with self.assertRaises(Blocked):api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())
                f.assert_not_called()
        def test_timeout_retains_reservation(self):
            with mock.patch(__name__+'.api_http',side_effect=TimeoutError('fixture')) as f:
                p=api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())
                self.assertTrue(p['transport_uncertain']);self.assertEqual(f.call_count,1)
                api_pending_package(self.r,self.plan,self.budget,self.local,Secrets());self.assertEqual(f.call_count,1)
            self.assertEqual(ledger_report(self.local,self.budget)['unknown_usage_attempts'],1)
        def test_http_401_is_fatal(self):
            with mock.patch(__name__+'.api_http',return_value=self.envelope({'error':'denied'},401)):
                self.assertTrue(api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())['fatal_error'])
        def test_http_429_not_automatically_retried(self):
            with mock.patch(__name__+'.api_http',return_value=self.envelope({'error':'limited'},429)) as f:
                api_pending_package(self.r,self.plan,self.budget,self.local,Secrets());api_pending_package(self.r,self.plan,self.budget,self.local,Secrets());self.assertEqual(f.call_count,1)
        def test_billed_over_reservation_stops(self):
            o=self.response();o['usage']['output_tokens']=100000
            with mock.patch(__name__+'.api_http',return_value=self.envelope(o)):
                self.assertTrue(api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())['fatal_error'])
        def test_quote_payload_tamper_refused(self):
            self.budget['per_request'][self.r['id']]['request_sha256']='bad'
            with mock.patch(__name__+'.api_http') as f:
                with self.assertRaises(Blocked):api_pending_package(self.r,self.plan,self.budget,self.local,Secrets())
                f.assert_not_called()
        def test_secrets_removed_from_environment(self):
            with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'fixture-secret'}):
                s=Secrets();self.assertEqual(s.get('openai'),'fixture-secret');self.assertNotIn('OPENAI_API_KEY',os.environ);self.assertEqual(s.redact('fixture-secret'), '[REDACTED]')
        def test_no_unapproved_endpoint(self):
            with self.assertRaises(Blocked):api_http('openai','https://elsewhere',{},Secrets())
        def test_no_unapproved_provider(self):
            with self.assertRaises(Blocked):api_http('elsewhere','/v1/responses',{},Secrets())
        def test_budget_all_180(self):
            validate_budget(self.plan,self.budget);self.assertEqual(len(self.budget['per_request']),180)
        def test_budget_mutated_count(self):
            self.budget['per_request'][self.r['id']]['counted_input_tokens']+=1
            with self.assertRaises(Blocked):validate_budget(self.plan,self.budget)
        def test_budget_missing_slot(self):
            del self.budget['per_request'][self.r['id']]
            with self.assertRaises(Blocked):validate_budget(self.plan,self.budget)
        def test_budget_low_authorization(self):
            auth={'approved':True,'plan_sha256':sha(canon(self.plan)),'budget_sha256':sha(canon(self.budget)),'max_api_usd':'0.001'}
            with self.assertRaises(Blocked):validate_budget(self.plan,self.budget,auth)
        def test_budget_valid_authorization(self):
            auth={'approved':True,'plan_sha256':sha(canon(self.plan)),'budget_sha256':sha(canon(self.budget)),'max_api_usd':self.budget['full_cohort_reserved_usd']}
            validate_budget(self.plan,self.budget,auth)
        def test_https_fixed_host_no_redirect_no_retry(self):
            class Response:
                status=302
                def read(self,n):return b'{}'
                def getheaders(self):return [('Location','https://evil.invalid'),('Set-Cookie','private'),('request-id','safe-id')]
            fake=mock.Mock();fake.getresponse.return_value=Response()
            sec=Secrets();sec.values['openai']='FAKE-SECRET'
            with mock.patch.object(http.client,'HTTPSConnection',return_value=fake) as constructor:
                res=api_http('openai','/v1/responses',{'x':1},sec)
                self.assertEqual(constructor.call_args.args[0],'api.openai.com')
                self.assertEqual(fake.request.call_count,1)
                self.assertEqual(res['http_status'],302)
                self.assertEqual(res['headers'],{'request-id':'safe-id'})
                self.assertNotIn('FAKE-SECRET',json.dumps(res))
        def test_api_get_metadata_not_generation(self):
            with mock.patch(__name__+'.api_http',return_value=self.envelope({'id':PRESETS['openai']['id']})) as f:
                model_lookup('openai',PRESETS['openai'],Secrets())
                self.assertEqual(f.call_args.args[1],'/v1/models/gpt-5.6-terra')
                self.assertIsNone(f.call_args.args[2])
        def test_model_metadata_alias_not_silently_accepted(self):
            with mock.patch(__name__+'.api_http',return_value=self.envelope({'id':'another-model'})):
                with self.assertRaises(Blocked):model_lookup('openai',PRESETS['openai'],Secrets())
        def test_full_budget_counter_60_requests(self):
            paths=[]
            def send(p,path,body,secrets,timeout=120):
                paths.append(path)
                return self.envelope({'id':self.cfg['models'][p]['id']}) if body is None else self.envelope({'input_tokens':4500})
            with mock.patch(__name__+'.api_http',side_effect=send),contextlib.redirect_stdout(io.StringIO()):
                budget=make_budget(self.plan,Secrets(),self.local)
            validate_budget(self.plan,budget)
            self.assertEqual(sum(p.endswith('input_tokens') or p.endswith('count_tokens') for p in paths),60)
            self.assertNotIn('/v1/responses',paths);self.assertNotIn('/v1/messages',paths)
        def test_archive_roundtrip(self):
            src=ROOT/'data';jw(src/'a.json',{'ok':True});rec=P.archive_dir(src,'test');self.assertEqual(P.verify_archive(ROOT/'archives/test.tar.gz',rec)['verified_files'],1)
        def test_archive_tamper_rejected(self):
            src=ROOT/'data';jw(src/'a.json',{'ok':True});rec=P.archive_dir(src,'test');p=ROOT/'archives/test.tar.gz';p.write_bytes(p.read_bytes()+b'broken')
            with self.assertRaises(Blocked):P.verify_archive(p,rec)
        def test_immutable_plan_not_overwritten(self):
            p=ROOT/'p.json';immutable_json(p,{'a':1});immutable_json(p,{'a':1})
            with self.assertRaises(Blocked):immutable_json(p,{'a':2})
        def test_symlink_rejected(self):
            p=ROOT/'link';p.symlink_to(self.local)
            with self.assertRaises(Blocked):P.safe(p/'file')
        def test_summary_requires_all_270(self):
            with self.assertRaises(Blocked):summarize([],self.plan)
        def test_complete_mock_orchestration_270(self):
            jw(plan_path(),self.plan);jw(ROOT/'control/runner.py',{'fixture':True})
            jw(ROOT/'control/authorization.json',{'approved':True,'plan_sha256':sha(canon(self.plan))})
            def build():
                p=ROOT/'setup/mock-helper.so';save(p,b'not a shared library; orchestration fixture');return p
            def bases(helper):jw(ROOT/'preflight/mock.json',{'not_real_numeric_validation':True})
            class FakeModel:
                SAMPLING=P.module_a().SAMPLING
                def cached_assets(self):return [Path('/fake/binary'),Path('/fake/model'),{}, {'fixture':True},{},{}]
                def gpu_info(self):return {'uuid':P.EXPECTED_GPU}
                def verify_cached_unchanged(self,x):pass
                def api(fake,path,body=None,timeout=None):
                    if path=='/apply-template':
                        fake.messages=body['messages'];return {'prompt':'\n'.join(x['content'] for x in body['messages'])}
                    if path=='/tokenize':return {'tokens':[1,2,3]}
                    if path=='/completion':
                        task=next(t for t in C.TASKS if 'Workload: '+t+'.' in fake.messages[1]['content'])
                        return {'tokens_evaluated':3,'truncated':False,'stop_type':'eos','timings':{'predicted_n':200},
                                'content':json.dumps({'block':C.SPECS[task]['base']})+'\n'+original(task)}
                    raise AssertionError(path)
            class Proc:
                def poll(self):return 0
            def cloud(r):
                obj=self.response(r['provider'],r)
                return {'id':r['id'],'request_sha256':sha(canon(r)),'provider':r['provider'],
                        'envelope':self.envelope(obj),'usage_upper_usd':'0.03'}
            def evaluate(group,records,helper):
                # Numerical execution mocked. Real common parsers and response generation ran above.
                out=[]
                for r in records:
                    self.assertEqual(r['generation_status'],'saved')
                    ms=[{'shape':list(s),'measurement_valid':True,'speedup':1.0,'speedup_gt_1_02':False,
                         'same_cubin':True,'same_launch_as_original':True} for s in C.SPECS[group['task']]['perf']]
                    out.append(r|{'correctness_passed':True,'stage':'measured','measurements':ms})
                jw(ROOT/'groups'/group['label']/'outcomes.json',out);return out
            def ack(rec):
                P.verify_archive(ROOT/'archives'/(rec['label']+'.tar.gz'),rec)
                jw(ROOT/'acks'/(rec['label']+'.json'),{'sha256':rec['sha256']})
            original_lock = P.lock
            def fixture_lock(path):
                self.assertEqual(path, '/workspace/gpu-code-pilot-exclusive.lock')
                return original_lock(ROOT/'isolated-test-exclusive.lock')
            with contextlib.ExitStack() as stack:
                for obj,name,value in [(P,'lock',fixture_lock),(P,'remote_guard',lambda:None),(P,'no_other_gpu',lambda:None),
                        (sys.modules[__name__],'probe_environment',lambda:copy.deepcopy(self.env)),
                        (C,'build_helper',build),(C,'baseline_preflight',bases),(C,'evaluate_group',evaluate),(C,'wait_ack',ack),
                        (P,'module_a',lambda:FakeModel()),(P,'start_model',lambda *a:Proc()),
                        (sys.modules[__name__],'wait_cloud',cloud)]:
                    stack.enter_context(mock.patch.object(obj,name,value))
                with contextlib.redirect_stdout(io.StringIO()):worker(True)
            summary=parse(read(ROOT/'final/summary.json'))
            self.assertEqual(sum(x['candidate_slots'] for x in summary['providers'].values()),270)
            self.assertEqual(sum(x['valid_size_measurements'] for x in summary['providers'].values()),540)
            self.assertEqual(P.STATE['generation_calls'],270)
            self.assertEqual(len(list((ROOT/'receipts').glob('*.json'))),111)
            self.assertTrue((ROOT/'completion.json').exists())
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    need(result.wasSuccessful(),'GPU004 self tests failed')
    print('GPU004_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=COMMON_PROMPT_GRID_PARSERS_API_FIXTURES_COST_LEDGER_NO_RETRY_ARCHIVES_270_MOCK_ORCHESTRATION; NO_REAL_SSH_PAID_API_OR_CUDA_EXECUTION')


if __name__=='__main__':
    try:main()
    except (Blocked,NumericFailure,ValueError,OSError) as exc:
        print('GPU004_BLOCKED: '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        print('Prior results retained; no model fallback, automatic request retry or Pod termination.',file=sys.stderr)
        sys.exit(2)
