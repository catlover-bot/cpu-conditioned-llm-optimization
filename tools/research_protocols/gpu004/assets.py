#!/usr/bin/env python3
"""Runpod A40 cached-only recheck: verbosity 4, full GPU offload, one smoke.
WSL: --self-test / --run --allow-ephemeral-preparation / --watch / --status.
Reuses the verified V2 executable, shared libraries and GGUF in place.
No rebuild, download, install, old-file rewrite or benchmark request is allowed.
New records are written only in the V3 namespace. No Cherry connection.
The ephemeral acknowledgement still does not establish durable storage.
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
import argparse
import contextlib
import base64
import csv
import fcntl
import hashlib
import http.client
import io
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

VERSION = 'a40-prepare-3.0.0-cached-recheck'
ROOT = Path('/workspace/cpucond-runpod-a40-prepare-v3')
CACHE_ROOT = Path('/workspace/cpucond-runpod-a40-prepare-v2')
V2_RUNNER_SHA = 'd8849737d165a83900d3f5aada80e4a4821d57f0cb695d5e8625dac74f5123b0'
CACHED_BINARY_SHA = '67090bf56f3deb8349bd744a27c252effe910944489fd04900b0c7a744f86780'
LOG_SOURCE_BLOBS = {
    'common/log.cpp': '0a9a4eb9ea496acb5e5d6f94c5adbbdd57b9164f',
    'common/log.h': 'e36b09463e60bccb2a72c5ca5a8c178691a3bcd4',
}
LOG_VERBOSITY = 4
SERVER = 'root@example.invalid'
SSH_PORT = 22
HOST_FINGERPRINT = 'SHA256:REPLACE_WITH_VERIFIED_HOST_KEY'
POD = 'PUBLIC_ALLOCATION_ID'
MODEL = 'qwen2.5-coder:14b-instruct-q4_K_M'
MODEL_SHA = 'ac9bc7a69dab38da1c790838955f1293420b55ab555ef6b4615efa1c1507b1ed'
MODEL_SIZE = 8988110784
COMMIT = 'b29c606e28a01b1bc8c1351026a0fa6e616bf6c4'
TAG = 'b10964'
REPO = 'https://github.com/ggml-org/llama.cpp.git'
BLOB_URL = 'https://registry.ollama.ai/v2/library/qwen2.5-coder/blobs/sha256:' + MODEL_SHA
MANIFEST_URL = 'https://registry.ollama.ai/v2/library/qwen2.5-coder/manifests/14b-instruct-q4_K_M'
PORT, CTX, SMOKE_CAP = 11528, 32768, 256
GIB = 1024**3
LOCAL_REL = 'workspace/cpu-conditioned-llm-optimization/runs/runpod-a40-prepare-v3'
PUBLIC_FILES = ('report.json', 'receipt.json', 'worker.log', 'llama-server.log',
    'failure.json', 'progress.json', 'environment.json', 'storage.json',
    'cuda-compiler.json', 'model-manifest.json', 'native-props.json',
    'smoke-request.json', 'smoke-response.json', 'gpu-loaded.json',
    'control/build-command.json', 'control/runtime-identity.json',
    'control/cache-verification.json', 'control/cache-verification-after.json',
    'control/device-list.json', 'control/logging-source-cpp.txt', 'control/logging-source-h.txt',
    'control/logging-contract.json', 'control/model-log-evidence.json',
    'control/server-command.json', 'control/model-stopped.json', 'control/smoke-intent.json')
LIVE_FILES = {'worker.log', 'llama-server.log', 'failure.json', 'progress.json'}
MIN_PREPARE_FREE = 2 * 1024**3  # cached-only: no model/build copy
SAMPLING = dict(seed=69001, temperature=0.2, top_k=40, top_p=0.9, min_p=0.0,
    typical_p=1.0, repeat_penalty=1.0, repeat_last_n=64,
    presence_penalty=0.0, frequency_penalty=0.0, dry_multiplier=0.0,
    xtc_probability=0.0, mirostat=0, dynatemp_range=0.0,
    samplers=['top_k','top_p','min_p','temperature'], cache_prompt=False,
    n_keep=-1, ignore_eos=False, n_cmpl=1, stop=['<|im_end|>','<|im_start|>'])

class Blocked(RuntimeError): pass

def need(value, message):
    if not value: raise Blocked(message)

def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(d): return (json.dumps(d, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()

def parse(b):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out, 'Duplicate JSON key: '+k);out[k]=v
        return out
    def bad(x): raise Blocked('Nonfinite JSON')
    return json.loads(b, object_pairs_hook=pairs, parse_constant=bad)

def safe(p):
    p=Path(p).absolute()
    need('..' not in p.parts, 'Path traversal')
    for q in (p,*p.parents): need(not q.is_symlink(), 'Symlink refused: '+str(q))
    return p

def digest(p):
    p=safe(p);h=hashlib.sha256()
    with p.open('rb') as f:
        s=os.fstat(f.fileno());need(stat.S_ISREG(s.st_mode),'Regular file required')
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
        e=os.fstat(f.fileno())
    need((s.st_ino,s.st_size,s.st_mtime_ns)==(e.st_ino,e.st_size,e.st_mtime_ns),'File changed while hashing')
    return h.hexdigest()

def write(p,b):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())

def jw(p,d):write(p,canon(d))

def atomic(p,d):
    p=safe(p);t=p.with_name(p.name+'.tmp-'+str(os.getpid()))
    write(t,canon(d));os.replace(t,p)

def note(phase,**kw):
    data=dict(version=VERSION,phase=phase,updated_utc=now(),benchmark_generation_calls=0,
              cherry_modified=False,**kw)
    atomic(ROOT/'progress.json',data)
    print('PHASE='+phase,flush=True)

def env():
    # Do not propagate account API keys or an SSH agent to build/inference tools.
    out={'PATH':'/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
         'HOME':'/root','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1',
         'GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
    out['TMPDIR']=str(ROOT/'tmp')
    return out

def cmd(argv,timeout=120,capture=False,extra=None):
    e=env();e.update(extra or {})
    print('COMMAND '+shlex.join([str(x) for x in argv]),flush=True)
    cp=subprocess.run([str(x) for x in argv],env=e,stdin=subprocess.DEVNULL,
         stdout=subprocess.PIPE if capture else None,
         stderr=subprocess.PIPE if capture else None,text=True,timeout=timeout)
    need(cp.returncode==0,'Command failed ('+str(cp.returncode)+'): '+str(argv[0])+
         (': '+cp.stderr[-2000:] if capture else '; inspect worker.log'))
    return cp.stdout if capture else ''

def gpu_info():
    raw=cmd(['nvidia-smi','--query-gpu=index,name,uuid,driver_version,memory.total,memory.free',
             '--format=csv,noheader,nounits'],capture=True)
    rows=list(csv.reader(io.StringIO(raw)));need(len(rows)==1 and len(rows[0])==6,'Exactly one visible A40 required')
    r=[x.strip() for x in rows[0]]
    need(r[1]=='NVIDIA A40','Unexpected GPU: '+r[1])
    return dict(index=int(r[0]),name=r[1],uuid=r[2],driver=r[3],total_mib=int(r[4]),free_mib=int(r[5]))

def mount_layout(text, workspace='/workspace'):
    """Identify the containing mount; no claim about provider durability/quota."""
    def unescape(value):
        return re.sub(r'\\([0-7]{3})',lambda m:chr(int(m.group(1),8)),value)
    target=Path(workspace)
    need(target.is_absolute(),'Storage target must be absolute')
    mounts=[]
    for line in text.splitlines():
        if not line.strip():continue
        left,sep,right=line.partition(' - ')
        a,b=left.split(),right.split()
        need(sep and len(a)>=6 and len(b)>=3,'Malformed mountinfo record')
        point=unescape(a[4])
        if target==Path(point) or target.is_relative_to(Path(point)):
            mounts.append(dict(mount_target=point,fstype=b[0],source=unescape(b[1]),
                mount_options=a[5],super_options=b[2]))
    need(mounts,'No containing mount found')
    chosen=max(mounts,key=lambda r:len(Path(r['mount_target']).parts))
    need('ro' not in chosen['mount_options'].split(','),'Storage mount is read-only')
    need(chosen['fstype'] not in ('tmpfs','ramfs'),'RAM-backed storage is not allowed for model preparation')
    separate=chosen['mount_target']!='/' and chosen['fstype'] not in ('overlay','aufs')
    return dict(workspace=str(target),**chosen,separate_disk_mount_observed=separate,
        storage_mode='separate_mount_unverified_lifetime' if separate else 'ephemeral_or_unverified_root_disk',
        persistence_verified=False,provider_quota_verified=False)

def storage_policy(layout, free_bytes, allow_ephemeral=False):
    need(layout['separate_disk_mount_observed'] or allow_ephemeral,
        'No separate disk mount: use --allow-ephemeral-preparation ONLY for rebuildable assets and one smoke; not benchmark output storage')
    need(free_bytes>=MIN_PREPARE_FREE,'Less than 2 GiB free for cached-only recheck logs and scratch')
    return dict(layout,allow_ephemeral_preparation=bool(allow_ephemeral),
        observed_free_bytes=free_bytes,minimum_free_bytes=MIN_PREPARE_FREE,
        allowed_scope='read-only cached assets, log-level correction, one non-benchmark smoke',
        benchmark_generation_authorized=False,pod_stop_or_edit_may_erase_files=True,
        off_pod_report_copy_verified=False)

def local_mount_check(allow_ephemeral=False):
    workspace=safe('/workspace')
    need(workspace.is_dir(),'/workspace is absent')
    layout=mount_layout(Path('/proc/self/mountinfo').read_text(),str(workspace))
    usage=shutil.disk_usage(workspace)
    report=storage_policy(layout,usage.free,allow_ephemeral)
    report.update(observed_total_bytes=usage.total,observed_utc=now())
    print('STORAGE_MODE='+report['storage_mode'],flush=True)
    if not layout['separate_disk_mount_observed']:
        print('EPHEMERAL_PREPARATION_ACKNOWLEDGED; no benchmark requests; copy reports off Pod before stopping/editing',flush=True)
    return report












def verify_model_file(path, expected_sha=None, expected_size=None):
    path=safe(path)
    pin=MODEL_SHA if expected_sha is None else expected_sha
    size=MODEL_SIZE if expected_size is None else expected_size
    need(path.is_file() and path.stat().st_size==size,'Cached GGUF size/file mismatch')
    need(digest(path)==pin,'Cached GGUF digest mismatch')
    with path.open('rb') as stream:
        need(stream.read(4)==b'GGUF','Cached model has no GGUF header')
    return dict(path=str(path),sha256=pin,bytes=size)

def verify_runtime_files(directory, table):
    directory=safe(directory)
    need(directory.is_dir() and isinstance(table,dict) and table,'Missing runtime directory/table')
    actual={p.name for p in directory.iterdir() if not p.is_symlink() and p.is_file()}
    need(actual==set(table),'Cached runtime regular-file set changed')
    for name,pin in table.items():
        need(isinstance(name,str) and re.fullmatch(r'[A-Za-z0-9_.+-]+',name) and name not in ('.','..'),
             'Unsafe runtime member name')
        need(isinstance(pin,str) and re.fullmatch(r'[0-9a-f]{64}',pin),'Invalid runtime hash')
        need(digest(directory/name)==pin,'Cached runtime file changed: '+name)
    links={}
    for p in directory.iterdir():
        if p.is_symlink():
            resolved=p.resolve(strict=True)
            need(resolved.parent==directory and resolved.name in table,'Cached runtime symlink escaped table')
            links[p.name]=dict(link=os.readlink(p),resolved=resolved.name)
        else:
            need(p.is_file(),'Unexpected runtime directory/special file')
    need(any(name.startswith('libggml-cuda.so') for name in table),'CUDA library absent from pinned runtime')
    return dict(files=table,links=links)

def logging_contract(rawcpp, rawh):
    # Git blob SHA identifies the precise files of the already pinned source.
    def gitblob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    for name,raw in (('common/log.cpp',rawcpp),('common/log.h',rawh)):
        need(gitblob(raw)==LOG_SOURCE_BLOBS[name],'Pinned logging source changed: '+name)
    cpp=rawcpp.decode();hdr=rawh.decode()
    need(re.search(r'case\s+GGML_LOG_LEVEL_INFO:\s+return\s+LOG_LEVEL_TRACE\s*;',cpp),
         'GGML INFO mapping not confirmed')
    need(re.search(r'#define\s+LOG_LEVEL_TRACE\s+4\b',hdr) and
         re.search(r'#define\s+LOG_DEFAULT_LLAMA\s+LOG_LEVEL_INFO\b',hdr) and
         re.search(r'#define\s+LOG_LEVEL_INFO\s+3\b',hdr),'Pinned verbosity levels differ')
    return dict(commit=COMMIT,source_blobs=LOG_SOURCE_BLOBS,default_verbosity=3,
        ggml_info_required_verbosity=4,recheck_verbosity=LOG_VERBOSITY,
        inference_success_not_inferred_from_logging=True)

def cached_assets():
    cache=safe(CACHE_ROOT)
    need(cache!=ROOT and cache.is_dir(),'V2 cache absent or aliases V3 result root')
    need(digest(cache/'control/runner.py')==V2_RUNNER_SHA,'V2 runner differs')
    for name in ('control/smoke-intent.json','smoke-response.json','receipt.json'):
        need(not safe(cache/name).exists(),'V2 already entered/completed smoke; do not auto-repeat: '+name)
    oldfailure=parse((cache/'failure.json').read_bytes())
    need(oldfailure.get('error')=='Blocked: No GPU layer-offload evidence in model log',
         'V2 failure is not the confirmed pre-generation log-evidence failure')
    stopped=parse((cache/'control/model-stopped.json').read_bytes())
    need(stopped.get('returncode')==0,'V2 model process exit was not clean')
    launchrec=parse((cache/'launch.json').read_bytes())
    need(not worker_alive(launchrec),'V2 preparation worker is still active')
    ident=parse((cache/'control/runtime-identity.json').read_bytes())
    binary=cache/'build/bin/llama-server';model=cache/'models'/(MODEL_SHA+'.gguf')
    need(ident.get('commit')==COMMIT and ident.get('tag')==TAG,'Wrong cached runtime commit/tag')
    need(ident.get('binary')==str(binary) and ident.get('binary_sha256')==CACHED_BINARY_SHA,
         'Cached runtime identity does not match provided executable hash')
    need(digest(binary)==CACHED_BINARY_SHA,'Cached executable modified')
    runtimes=verify_runtime_files(binary.parent,ident.get('runtime_files'))
    need(digest(cache/'build/CMakeCache.txt')==ident.get('build_cache_sha256'),'CMake cache changed')
    cmaketext=(cache/'build/CMakeCache.txt').read_text()
    need(re.search(r'^GGML_CUDA:BOOL=ON$',cmaketext,re.M),'Cached build has no CUDA')
    modelrec=verify_model_file(model)
    nvmeta=parse((cache/'cuda-compiler.json').read_bytes());nv=Path(nvmeta['cuda_compiler'])
    need(nv.is_absolute() and nv.is_relative_to('/usr/local') and nv.is_file(),'Cached CUDA compiler location invalid')
    nv=nv.resolve();nvroot=nv.parent.parent
    cudaenv={'PATH':str(nv.parent)+':'+env()['PATH'],
        'LD_LIBRARY_PATH':str(binary.parent)+':'+str(nvroot/'lib64')+':/usr/local/nvidia/lib:/usr/local/nvidia/lib64'}
    rawcpp=safe(cache/'source/common/log.cpp').read_bytes()
    rawh=safe(cache/'source/common/log.h').read_bytes()
    contract=logging_contract(rawcpp,rawh)
    metadata_names=('control/runner.py','control/runtime-identity.json','control/build-command.json',
        'control/model-stopped.json','cuda-compiler.json','model-manifest.json','failure.json',
        'native-props.json','launch.json','source/common/log.cpp','source/common/log.h')
    before={name:digest(cache/name) for name in metadata_names}
    report=dict(model=modelrec,executable_sha256=CACHED_BINARY_SHA,runtime=runtimes,
        build_cache_sha256=ident['build_cache_sha256'],metadata_hashes=before,
        source_cache=str(cache),model_copied=False,runtime_copied=False,downloads=0,builds=0,
        old_cache_modified=False,logging_contract=contract)
    return binary,model,cudaenv,ident,nvmeta,report,rawcpp,rawh

def verify_cached_unchanged(before):
    need(verify_model_file(CACHE_ROOT/'models'/(MODEL_SHA+'.gguf'))==before['model'],'Cached model changed')
    after=verify_runtime_files(CACHE_ROOT/'build/bin',before['runtime']['files'])
    need(after==before['runtime'],'Runtime symlink map changed')
    need(digest(CACHE_ROOT/'build/CMakeCache.txt')==before['build_cache_sha256'],'Build cache changed')
    for name,pin in before['metadata_hashes'].items():
        need(digest(CACHE_ROOT/name)==pin,'V2 metadata changed: '+name)
    return dict(old_cache_unchanged=True,model_sha256=MODEL_SHA,
        executable_sha256=CACHED_BINARY_SHA,checked_utc=now())

def device_check(binary,model,cudaenv,gpu):
    # Use exactly the same unprivileged identity and CUDA visibility as inference.
    args=server_argv(binary,model);prefix=args[:args.index(str(binary))+1]
    e=env();e.update(cudaenv);e.update(CUDA_VISIBLE_DEVICES=gpu['uuid'],CUDA_CACHE_DISABLE='1',TMPDIR='/tmp')
    cp=subprocess.run([*prefix,'--list-devices','--log-verbosity','4'],env=e,
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=60,cwd=ROOT)
    text=cp.stdout+'\n'+cp.stderr
    jw(ROOT/'control/device-list.json',dict(argv=[*prefix,'--list-devices','--log-verbosity','4'],
        returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,utc=now()))
    need(cp.returncode==0,'Unprivileged CUDA device listing failed; inspect device-list.json')
    need(re.search(r'CUDA\d+:\s*NVIDIA A40\b',text),'A40 CUDA device not visible to inference identity')
    print('A40_CUDA_DEVICE_VISIBLE_UNPRIVILEGED',flush=True)

def wait_for_offload(path,proc,timeout=5):
    deadline=time.monotonic()+timeout
    text=''
    while time.monotonic()<deadline:
        need(proc.poll() is None,'Model exited before offload check')
        text=path.read_text(errors='replace')
        if re.search(r'offloaded\s+\d+\s*/\s*\d+\s+layers\s+to\s+GPU',text,re.I):
            return offload_record(text)
        time.sleep(0.1)
    raise Blocked('No GPU layer-offload evidence even at verbosity 4; inspect saved log and gpu-loaded.json')

def api(path,body=None,timeout=60):
    need(path in ('/health','/props','/apply-template','/tokenize','/completion'),'Unexpected API path')
    conn=http.client.HTTPConnection('127.0.0.1',PORT,timeout=timeout)
    try:
        conn.request('POST' if body is not None else 'GET',path,
            body=canon(body) if body is not None else None,headers={'Content-Type':'application/json'})
        r=conn.getresponse();b=r.read(4*1024**2+1)
        need(r.status==200 and len(b)<=4*1024**2,'Local model API failed: '+path+' status='+str(r.status))
        return parse(b)
    finally:conn.close()

def offload_record(text):
    m=re.findall(r'offloaded\s+(\d+)\s*/\s*(\d+)\s+layers\s+to\s+GPU',text,re.I)
    need(m,'No GPU layer-offload evidence in model log')
    a,b=map(int,m[-1]);need(a==b and a>0,'Not all model layers offloaded; CPU fallback refused')
    return dict(offloaded_layers=a,total_layers=b,full_offload=True)

def stop_process(proc):
    if proc is None:return
    if proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=30)
    need(proc.poll() is not None,'Model subprocess still active')

def server_argv(binary,model):
    return ['setpriv','--reuid=65534','--regid=65534','--clear-groups','--bounding-set=-all',
       '--inh-caps=-all','--ambient-caps=-all','--no-new-privs',str(binary),
       '--model',str(model),'--host','127.0.0.1','--port',str(PORT),
       '--ctx-size',str(CTX),'--parallel','1','--threads','4','--threads-batch','4',
       '--batch-size','512','--ubatch-size','512','--n-gpu-layers','999',
       '--cache-type-k','f16','--cache-type-v','f16','--no-context-shift',
       '--alias',MODEL,'--jinja','--fit','off','--no-op-offload','--no-repack','--offline',
       '--log-verbosity',str(LOG_VERBOSITY),'--log-colors','off']


def permissions_for_inference():
    # Only NEW V3 output-directory traversal permissions are changed.
    # V2 cached model, binary, libraries and their modes are left untouched.
    ROOT.chmod(0o755)
    home=ROOT/'infer-home';home.mkdir(mode=0o755);home.chmod(0o755)

def smoke(binary,model,cudaenv,gpu):
    permissions_for_inference()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',PORT))
    e=env();e.update(cudaenv);e.update(HOME=str(ROOT/'infer-home'),CUDA_VISIBLE_DEVICES=gpu['uuid'],
                                    OMP_NUM_THREADS='4',TMPDIR='/tmp',CUDA_CACHE_DISABLE='1')
    argv=server_argv(binary,model);jw(ROOT/'control/server-command.json',dict(argv=argv,utc=now()))
    proc=None
    try:
        with (ROOT/'llama-server.log').open('xb') as log:
            proc=subprocess.Popen(argv,env=e,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                                  cwd=ROOT,start_new_session=True)
        note('LOADING_A40_MODEL',model_pid=proc.pid)
        deadline=time.monotonic()+1200
        while time.monotonic()<deadline:
            need(proc.poll() is None,'GPU model load failed; inspect llama-server.log')
            try:
                if api('/health',timeout=5).get('status')=='ok':break
            except (OSError,Blocked,http.client.HTTPException):pass
            time.sleep(2)
        else:raise Blocked('Model load timed out')
        props=api('/props');jw(ROOT/'native-props.json',props)
        need(props.get('total_slots')==1,'Parallel slot count mismatch')
        need(props['default_generation_settings']['n_ctx']==CTX,'Context length was reduced')
        need(Path(props['model_path']).resolve()==model.resolve(),'Wrong model file loaded')
        loaded=gpu_info();jw(ROOT/'gpu-loaded.json',loaded)
        offload=wait_for_offload(ROOT/'llama-server.log',proc)
        need(loaded['uuid']==gpu['uuid'],'Visible GPU changed during model load')
        delta=gpu['free_mib']-loaded['free_mib']
        need(delta>7000,'GPU memory increase inconsistent with full 14B loading')
        jw(ROOT/'control/model-log-evidence.json',dict(**offload,log_verbosity=LOG_VERBOSITY,
            gpu_memory_increase_mib=delta,gpu_uuid=gpu['uuid'],utc=now()))
        print('FULL_GPU_OFFLOAD_CONFIRMED='+str(offload['offloaded_layers'])+'/'+str(offload['total_layers']),flush=True)
        messages=[{'role':'system','content':'Follow the user instruction. Do not use tools.'},
                  {'role':'user','content':'Write the integers from 1 to 300, one per line, in order. Do not explain.'}]
        rendered=api('/apply-template',{'messages':messages})['prompt']
        need(isinstance(rendered,str) and all(m['content'] in rendered for m in messages),'Native template dropped content')
        need(rendered.endswith('<|im_start|>assistant\n'),'Unexpected native assistant prefix')
        tokens=api('/tokenize',dict(content=rendered,add_special=True,parse_special=True))['tokens']
        need(isinstance(tokens,list) and tokens and all(type(x) is int and x>=0 for x in tokens),'Invalid native tokens')
        body=dict(SAMPLING,prompt=tokens,n_predict=SMOKE_CAP,stream=False,return_tokens=True,id_slot=0)
        jw(ROOT/'smoke-request.json',body)
        jw(ROOT/'control/smoke-intent.json',dict(utc=now(),benchmark_slot=False,max_output_tokens=SMOKE_CAP,
            note='One non-benchmark smoke only; no automatic inference retry.'))
        note('GPU_SMOKE_GENERATING',max_output_tokens=SMOKE_CAP)
        begin=time.monotonic();result=api('/completion',body,timeout=600);elapsed=time.monotonic()-begin
        jw(ROOT/'smoke-response.json',result)
        need(result.get('truncated') is False,'Smoke context truncated')
        need(result.get('stop_type') in ('limit','eos','word'),'Smoke did not end normally')
        need(isinstance(result.get('content'),str) and result['content'],'Empty smoke output')
        rate=result.get('timings',{}).get('predicted_per_second')
        need(type(rate) in (int,float) and math.isfinite(rate) and rate>0,'Smoke token rate absent')
        count=result.get('timings',{}).get('predicted_n')
        need(type(count) is int and 0<count<=SMOKE_CAP+8,'Smoke token count absent/out of range')
        print(f'GPU_SMOKE_TOKENS_PER_SECOND={rate:.3f}',flush=True)
        return dict(native_context=CTX,parallel_slots=1,**offload,gpu_memory_increase_mib=delta,
            log_verbosity=LOG_VERBOSITY,smoke_tokens=count,
            smoke_tokens_per_second=rate,smoke_wall_seconds=elapsed,smoke_calls=1,
            smoke_is_benchmark=False,long_IR_throughput_established=False,
            prompt_template_sha256=sha(props['chat_template'].encode()))
    finally:
        stop_process(proc)
        if proc is not None:jw(ROOT/'control/model-stopped.json',dict(pid=proc.pid,returncode=proc.returncode,utc=now()))

def remote_guard():
    need(os.geteuid()==0,'Run the worker in the Runpod root account')
    need(socket.gethostname().split('.')[0]!='cpucond-skylake-01','Refusing to run on Cherry')
    if os.environ.get('RUNPOD_POD_ID'):need(os.environ['RUNPOD_POD_ID']==POD,'Wrong Runpod Pod ID')
    need(Path('/workspace').is_dir(),'/workspace missing')


def worker(allow_ephemeral=False):
    remote_guard();os.umask(0o077)
    with (ROOT/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        (ROOT/'tmp').mkdir(exist_ok=True)
        def interrupt(signum,frame):raise Blocked('Received signal '+str(signum))
        signal.signal(signal.SIGTERM,interrupt)
        try:
            note('VERIFYING_CACHED_ASSETS')
            mount=local_mount_check(allow_ephemeral);jw(ROOT/'storage.json',mount);gpu=gpu_info()
            need(gpu['total_mib']>=44000 and gpu['free_mib']>=40000,'A40 VRAM unavailable; no process will be stopped')
            for p in Path('/proc').iterdir():
                if not p.name.isdigit():continue
                try:name=(p/'comm').read_text().strip()
                except (FileNotFoundError,ProcessLookupError):continue
                need(name not in ('llama-server','ollama'),'Another inference engine is active; leave it untouched')
            jw(ROOT/'environment.json',dict(gpu=gpu,os_release=Path('/etc/os-release').read_text(),mount=mount,utc=now()))
            binary,model,cudaenv,ident,nvmeta,cache,cpp,hdr=cached_assets()
            jw(ROOT/'control/cache-verification.json',cache)
            jw(ROOT/'control/runtime-identity.json',ident)
            jw(ROOT/'control/build-command.json',parse((CACHE_ROOT/'control/build-command.json').read_bytes()))
            jw(ROOT/'cuda-compiler.json',nvmeta)
            write(ROOT/'model-manifest.json',(CACHE_ROOT/'model-manifest.json').read_bytes())
            write(ROOT/'control/logging-source-cpp.txt',cpp);write(ROOT/'control/logging-source-h.txt',hdr)
            jw(ROOT/'control/logging-contract.json',cache['logging_contract'])
            print('CACHED_MODEL_AND_CUDA_RUNTIME_VERIFIED; NO_DOWNLOAD_NO_REBUILD',flush=True)
            note('CHECKING_UNPRIVILEGED_CUDA_DEVICE')
            device_check(binary,model,cudaenv,gpu)
            smoke_report=smoke(binary,model,cudaenv,gpu)
            note('VERIFYING_CACHED_ASSETS_UNCHANGED')
            jw(ROOT/'control/cache-verification-after.json',verify_cached_unchanged(cache))
            report=dict(schema=VERSION,state='A40_PREPARATION_COMPLETE',model=MODEL,model_sha256=MODEL_SHA,
                model_bytes=MODEL_SIZE,model_file=str(model),llama_commit=COMMIT,llama_tag=TAG,
                runtime_binary=str(binary),runtime_binary_sha256=CACHED_BINARY_SHA,runtime_banner=ident['banner'],
                cuda_compiler=nvmeta['cuda_compiler'],cuda_version=nvmeta['cuda_version'],tool_packages_installed=[],
                gpu=gpu,storage=mount,**smoke_report,model_process_stopped=True,benchmark_generation_calls=0,
                cherry_modified=False,unattempted_slots_assigned=False,all_experiments_complete=False,
                source_cache=str(CACHE_ROOT),cached_assets_unchanged=True,model_downloads=0,runtime_builds=0,
                change_scope='Only model logging verbosity 4 and colors disabled; cached model/binary/sampling unchanged.',
                performance_measurement_host='unchanged: Cherry Skylake',
                migration_note='GPU generation is a distinct backend stratum; CPU/GPU outputs are not assumed identical.',
                completed_utc=now())
            jw(ROOT/'report.json',report)
            table={name:digest(ROOT/name) for name in PUBLIC_FILES
                   if name not in LIVE_FILES and name!='receipt.json' and (ROOT/name).is_file()}
            jw(ROOT/'receipt.json',dict(report_sha256=digest(ROOT/'report.json'),files=table,utc=now()))
            note('COMPLETE',smoke_tokens_per_second=smoke_report['smoke_tokens_per_second'])
            print('RUNPOD_A40_MODEL_LOAD_AND_SMOKE_COMPLETE',flush=True)
            print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
        except BaseException as exc:
            atomic(ROOT/'failure.json',dict(error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),utc=now()))
            note('BLOCKED',error=type(exc).__name__+': '+str(exc))
            raise

def process_start(pid):
    try:
        s=Path('/proc',str(pid),'stat').read_text();tail=s[s.rfind(')')+2:].split()
        if tail[0]=='Z':return None
        return tail[19]
    except (OSError,IndexError):return None

def worker_alive(rec):return type(rec.get('pid')) is int and process_start(rec['pid'])==rec.get('process_start') and rec.get('process_start') is not None

def remote_status():
    remote_guard();d=dict(state='NOT_STARTED')
    for name in ('launch','progress','failure','report','receipt'):
        p=ROOT/(name+'.json')
        if p.exists():d[name]=parse(p.read_bytes())
    if 'report' in d and 'receipt' in d:
        need(digest(ROOT/'report.json')==d['receipt']['report_sha256'],'Report hash changed')
        d['state']='COMPLETE'
    elif 'failure' in d:d['state']='BLOCKED'
    elif 'launch' in d:d['state']='RUNNING' if worker_alive(d['launch']) else 'INTERRUPTED'
    return d

def launch(allow_ephemeral=False):
    remote_guard()
    with (ROOT/'launch.lock').open('a') as lk:
        fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (ROOT/'launch.json').exists():
            d=remote_status();need(d['state'] in ('RUNNING','COMPLETE'),'Previous attempt retained; inspect logs, no automatic rerun')
            return d
        log=(ROOT/'worker.log').open('xb')
        e=env()
        for k in ('RUNPOD_POD_ID',):
            if k in os.environ:e[k]=os.environ[k]
        proc=subprocess.Popen(worker_command(allow_ephemeral),
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=e,cwd=ROOT,start_new_session=True)
        log.close()
        start=process_start(proc.pid);need(start is not None,'Detached worker did not start')
        jw(ROOT/'launch.json',dict(pid=proc.pid,process_start=start,runner_sha256=digest(ROOT/'control/runner.py'),
            allow_ephemeral_preparation=bool(allow_ephemeral),benchmark_generation_authorized=False,utc=now()))
        return remote_status()

def worker_command(allow_ephemeral=False):
    argv=[sys.executable,'-I','-S','-B','-u',str(ROOT/'control/runner.py'),'--_worker']
    if allow_ephemeral:argv.append('--allow-ephemeral-preparation')
    return argv

def fingerprint_check(keyfile):
    known=Path.home()/'.ssh/known_hosts'
    need(known.is_file(),'Known-hosts file is missing; do not disable host verification')
    cp=subprocess.run(['ssh-keygen','-F',f'[example.invalid]:{SSH_PORT}','-f',str(known)],capture_output=True,text=True,check=False)
    fingerprints=[]
    for line in cp.stdout.splitlines():
        fields=line.split()
        if len(fields)>=3 and not line.startswith('#') and fields[1]=='ssh-ed25519':
            try:fingerprints.append('SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(fields[2],validate=True)).digest()).decode().rstrip('='))
            except ValueError:pass
    need(HOST_FINGERPRINT in fingerprints,'Known Runpod direct-SSH fingerprint mismatch; do not clear known_hosts')
    need(keyfile.is_file() and not keyfile.is_symlink(),'Existing WSL SSH private key missing')

def install_code(pin):
    # Only the new /workspace namespace is written; no private keys are uploaded.
    return """import os,sys,hashlib
from pathlib import Path
p=Path(%r)
assert os.geteuid()==0 and Path('/workspace').is_dir(), 'Wrong host or missing workspace'
assert os.environ.get('RUNPOD_POD_ID',%r)==%r, 'Wrong Pod'
for q in (p,*p.parents): assert not q.is_symlink(), 'Symlink refused'
b=sys.stdin.buffer.read(1024*1024+1)
assert len(b)<=1024*1024 and hashlib.sha256(b).hexdigest()==%r, 'Upload hash mismatch'
p.parent.mkdir(parents=True,exist_ok=True)
if p.exists(): assert p.is_file() and p.read_bytes()==b, 'Runner conflict; no overwrite'
else:
 with p.open('xb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
print('A40_SETUP_RUNNER_HASH_VERIFIED')
""" % (str(ROOT/'control/runner.py'),POD,POD,pin)

class Connection:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cpucond-a40-ssh-');os.chmod(self.tmp.name,0o700)
        self.opts=['-F','/dev/null','-p',str(SSH_PORT),'-i',str(Path.home()/'.ssh/id_ed25519'),
            '-o','IdentitiesOnly=yes','-o','PreferredAuthentications=publickey',
            '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no',
            '-o','StrictHostKeyChecking=yes','-o','HostKeyAlgorithms=ssh-ed25519','-o','ForwardAgent=no',
            '-o','ConnectTimeout=30','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=4',
            '-o','ControlMaster=auto','-o','ControlPersist=600','-o','ControlPath='+self.tmp.name+'/master']
    def run(self,args,data=None):
        cp=subprocess.run(['ssh','-T',*self.opts,SERVER,shlex.join([str(x) for x in args])],
            input=data,stdout=subprocess.PIPE,check=False)
        need(cp.returncode==0,'SSH command failed; the detached GPU preparation is not automatically stopped')
        return cp.stdout
    def remote(self,action,*args):return parse(self.run(['python3','-I','-S','-B',str(ROOT/'control/runner.py'),action,*args]))
    def close(self):
        subprocess.run(['ssh',*self.opts,'-O','exit',SERVER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        self.tmp.cleanup()

def verify_local_collection(dest, receipt):
    need(isinstance(receipt.get('files'),dict) and receipt['files'],'Missing receipt file table')
    need(receipt['files'].get('report.json')==receipt.get('report_sha256'),'Receipt report pins conflict')
    verified={}
    for name,pin in receipt['files'].items():
        need(name in PUBLIC_FILES and name not in LIVE_FILES and name!='receipt.json','Unexpected receipt item')
        path=safe(dest/name)
        need(path.is_file(),'Missing local report artifact: '+name)
        need(digest(path)==pin,'Local artifact does not match remote receipt: '+name)
        verified[name]=pin
    return verified

def collect(con,doc):
    dest=safe(Path.home()/LOCAL_REL);dest.mkdir(parents=True,exist_ok=True)
    for name in PUBLIC_FILES:
        if name=='failure.json' and 'failure' not in doc:continue
        if name in ('report.json','receipt.json') and doc['state']!='COMPLETE':continue
        reply=parse(con.run(['python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_read',name]))
        if reply.get('missing'):continue
        raw=base64.b64decode(reply['data'],validate=True);need(sha(raw)==reply['sha256'],'Transfer hash mismatch')
        if doc['state']=='COMPLETE' and name in doc['receipt'].get('files',{}):
            need(sha(raw)==doc['receipt']['files'][name],'Remote receipt mismatch: '+name)
        if name=='receipt.json' and doc['state']=='COMPLETE':
            need(parse(raw)==doc['receipt'],'Receipt changed during collection')
        p=safe(dest/name)
        if name not in LIVE_FILES and p.exists():need(p.read_bytes()==raw,'Existing local result differs: '+name)
        elif p.exists():
            t=p.with_name(p.name+'.tmp-'+str(os.getpid()));write(t,raw);os.replace(t,p)
        else:write(p,raw)
    print('LOCAL_DIRECTORY='+str(dest),flush=True)
    if doc['state']=='COMPLETE':
        verified=verify_local_collection(dest,doc['receipt'])
        atomic(dest/'local-verification.json',dict(utc=now(),receipt_sha256=digest(dest/'receipt.json'),
            verified=verified,report_copy_verified=True,model_or_runtime_copied=False,
            benchmark_results_copied=False,whole_study_backup_verified=False))
        print('RUNPOD_A40_PREPARATION_LOCAL_REPORT_VERIFIED',flush=True)

def local(mode,allow_ephemeral=False):
    need(os.geteuid()!=0,'Run local commands as mhirotaka in WSL, not inside Runpod')
    fingerprint_check(Path.home()/'.ssh/id_ed25519')
    con=Connection()
    try:
        if mode=='run':
            raw=Path(__file__).read_bytes();pin=sha(raw)
            print(con.run(['python3','-I','-S','-B','-c',install_code(pin)],data=raw).decode(),flush=True)
            doc=con.remote('--_launch',*(['--allow-ephemeral-preparation'] if allow_ephemeral else []))
            print('RUNPOD_A40_PREPARATION_STARTED; no Cherry modification and no benchmark requests',flush=True)
        else:doc=con.remote('--_status')
        if mode=='status':
            print(json.dumps(doc,ensure_ascii=False,indent=2));return
        while True:
            print(json.dumps(dict(state=doc['state'],phase=doc.get('progress',{}).get('phase'),
                  updated_utc=doc.get('progress',{}).get('updated_utc'))),flush=True)
            if doc['state'] in ('COMPLETE','BLOCKED','INTERRUPTED'):
                collect(con,doc)
                if doc['state']!='COMPLETE':raise Blocked(doc.get('failure',{}).get('error','Worker interrupted; inspect local logs'))
                print(json.dumps(doc['report'],ensure_ascii=False,indent=2),flush=True);return
            need(doc['state']=='RUNNING','Preparation was not started')
            time.sleep(15);doc=con.remote('--_status')
    except KeyboardInterrupt:
        print('LOCAL_WATCH_STOPPED; detached Runpod preparation continues. Use --watch to reconnect.',flush=True)
    finally:con.close()

def self_test():
    class T(unittest.TestCase):
        def test_model_pin(self):self.assertEqual(len(MODEL_SHA),64);self.assertEqual(MODEL_SIZE,8988110784)
        def test_commit_pin(self):self.assertEqual(len(COMMIT),40)
        def test_context(self):self.assertEqual(CTX,32768)
        def test_cap(self):self.assertEqual(SMOKE_CAP,256)
        def test_gpu_all_layers(self):self.assertIn('999',server_argv(Path('/bin/s'),Path('/m')))
        def test_loopback_only(self):
            a=server_argv(Path('/bin/s'),Path('/m'));self.assertEqual(a[a.index('--host')+1],'127.0.0.1')
        def test_no_silent_fit(self):
            a=server_argv(Path('/bin/s'),Path('/m'));self.assertEqual(a[a.index('--fit')+1],'off')
        def test_one_slot(self):
            a=server_argv(Path('/bin/s'),Path('/m'));self.assertEqual(a[a.index('--parallel')+1],'1')
        def test_no_privileged_model(self):self.assertIn('--reuid=65534',server_argv(Path('/bin/s'),Path('/m')))
        def test_float_contract(self):self.assertEqual(SAMPLING['temperature'],0.2);self.assertFalse(SAMPLING['cache_prompt'])
        def test_no_credentials_in_env(self):
            with patch.dict(os.environ,{'OPENAI_API_KEY':'x','SSH_AUTH_SOCK':'x'}):
                self.assertNotIn('OPENAI_API_KEY',env());self.assertNotIn('SSH_AUTH_SOCK',env())
        def test_duplicate_json(self):self.assertRaises(Blocked,parse,b'{"a":1,"a":2}')
        def test_nonfinite_json(self):self.assertRaises(Blocked,parse,b'{"a":NaN}')
        def test_full_gpu(self):self.assertTrue(offload_record('load_tensors: offloaded 49/49 layers to GPU')['full_offload'])
        def test_partial_gpu_refused(self):self.assertRaises(Blocked,offload_record,'offloaded 20/49 layers to GPU')
        def test_no_offload_refused(self):self.assertRaises(Blocked,offload_record,'CPU model loaded')
        def test_empty_offload_refused(self):self.assertRaises(Blocked,offload_record,'offloaded 0/0 layers to GPU')
        def test_symlink(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'x').write_text('x');(p/'y').symlink_to(p/'x');self.assertRaises(Blocked,digest,p/'y')
        def test_no_overwrite(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'x';write(p,b'x');self.assertRaises(FileExistsError,write,p,b'y')
        def test_atomic(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'x';atomic(p,{'a':1});atomic(p,{'a':2});self.assertEqual(parse(p.read_bytes()),{'a':2})
        def test_hash(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'x';write(p,b'x');self.assertEqual(digest(p),sha(b'x'))
        def test_dead_pid(self):self.assertIsNone(process_start(999999999))
        def test_alive_identity(self):
            pid=os.getpid();self.assertTrue(worker_alive(dict(pid=pid,process_start=process_start(pid))))
        def test_wrong_pid_identity(self):self.assertFalse(worker_alive(dict(pid=os.getpid(),process_start='wrong')))
        def test_unknown_state_not_complete(self):
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)),patch(__name__+'.remote_guard'):
                self.assertEqual(remote_status()['state'],'NOT_STARTED')
        def test_summary_without_receipt_not_complete(self):
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)),patch(__name__+'.remote_guard'):
                jw(Path(d)/'report.json',{'state':'COMPLETE'});self.assertNotEqual(remote_status()['state'],'COMPLETE')
        def test_report_digest_checked(self):
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)),patch(__name__+'.remote_guard'):
                jw(Path(d)/'report.json',{'x':1});jw(Path(d)/'receipt.json',{'report_sha256':'0'*64})
                self.assertRaises(Blocked,remote_status)
        def test_stop_owned_child(self):
            p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
            stop_process(p);self.assertIsNotNone(p.poll())
        def test_upload_code_syntax(self):compile(install_code('0'*64),'<install>','exec')
        def test_no_cherry_destination(self):self.assertNotIn('example.invalid',SERVER);self.assertTrue(str(ROOT).startswith('/workspace/'))
        def test_cached_bad_model_refused(self):
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)):
                p=Path(d)/'models'/(MODEL_SHA+'.gguf');p.parent.mkdir();p.write_bytes(b'wrong')
                self.assertRaises(Blocked,verify_model_file,p)
        def test_token_settings_same_as_cpu(self):
            self.assertEqual(SAMPLING['seed'],69001)
            self.assertEqual(SAMPLING['samplers'],['top_k','top_p','min_p','temperature'])
            self.assertEqual(SAMPLING['n_keep'],-1)
        def test_smoke_mock_api_and_real_child_cleanup(self):
            # Tests orchestration/cleanup only, not a real model, GPU, or API server.
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)):
                root=Path(d);(root/'tmp').mkdir();model=root/'m.gguf';model.write_bytes(b'fixture')
                props={'total_slots':1,'default_generation_settings':{'n_ctx':CTX},
                       'model_path':str(model),'chat_template':'fixture-template'}
                calls=[]
                def fakeapi(path,body=None,timeout=60):
                    calls.append(path)
                    if path=='/health':
                        deadline=time.monotonic()+5
                        while time.monotonic()<deadline:
                            if 'offloaded 49/49' in (root/'llama-server.log').read_text():break
                            time.sleep(0.02)
                        else:raise AssertionError('Fixture child did not become ready: '+(root/'llama-server.log').read_text())
                        return {'status':'ok'}
                    if path=='/props':return props
                    if path=='/apply-template':return {'prompt':''.join(m['content'] for m in body['messages'])+'<|im_start|>assistant\n'}
                    if path=='/tokenize':return {'tokens':[1,2,3]}
                    if path=='/completion':return {'truncated':False,'stop_type':'limit','content':'1\n2',
                                                   'timings':{'predicted_per_second':20.0,'predicted_n':256}}
                    raise AssertionError(path)
                childcmd=[sys.executable,'-u','-c',"import time;print('offloaded 49/49 layers to GPU',flush=True);time.sleep(30)"]
                with patch(__name__+'.permissions_for_inference'),patch(__name__+'.server_argv',return_value=childcmd), \
                     patch(__name__+'.api',side_effect=fakeapi),patch(__name__+'.gpu_info',return_value={'uuid':'GPU-fixture','total_mib':46068,'free_mib':30000}), \
                     contextlib.redirect_stdout(io.StringIO()):
                    got=smoke(Path('/fake/bin'),model,{}, {'uuid':'GPU-fixture','free_mib':46000})
                self.assertEqual(calls.count('/completion'),1)
                self.assertEqual(got['smoke_tokens'],256)
                self.assertTrue(got['full_offload'])
                self.assertFalse(got['smoke_is_benchmark'])
                rec=parse((root/'control/model-stopped.json').read_bytes())
                self.assertIsNotNone(rec['returncode'])
                self.assertIsNone(process_start(rec['pid']))
        def test_smoke_failure_cleanup(self):
            with tempfile.TemporaryDirectory() as d,patch(__name__+'.ROOT',Path(d)):
                root=Path(d);(root/'tmp').mkdir();model=root/'m.gguf';model.write_bytes(b'fixture')
                childcmd=[sys.executable,'-u','-c',"import time;time.sleep(30)"]
                def failapi(path,body=None,timeout=60):
                    if path=='/health':return {'status':'ok'}
                    return {'total_slots':2}
                with patch(__name__+'.permissions_for_inference'),patch(__name__+'.server_argv',return_value=childcmd), \
                     patch(__name__+'.api',side_effect=failapi),contextlib.redirect_stdout(io.StringIO()):
                    self.assertRaises(Blocked,smoke,Path('/fake/bin'),model,{}, {'uuid':'GPU-fixture'})
                self.assertTrue((root/'control/model-stopped.json').exists())
                self.assertFalse((root/'control/smoke-intent.json').exists())
        def test_remote_read_allowlist(self):
            self.assertNotIn('/root/.ssh/id_ed25519',PUBLIC_FILES)
            self.assertNotIn('../secret',PUBLIC_FILES)
        def test_storage_overlay_requires_ack(self):
            layout=mount_layout('1 0 0:1 / / rw - overlay overlay rw\n')
            self.assertFalse(layout['separate_disk_mount_observed'])
            self.assertRaises(Blocked,storage_policy,layout,30*GIB,False)
        def test_storage_overlay_ack_no_durability_claim(self):
            layout=mount_layout('1 0 0:1 / / rw - overlay overlay rw\n')
            r=storage_policy(layout,30*GIB,True)
            self.assertFalse(r['persistence_verified'])
            self.assertFalse(r['benchmark_generation_authorized'])
            self.assertFalse(r['off_pod_report_copy_verified'])
        def test_storage_separate_mount(self):
            text='1 0 0:1 / / rw - overlay overlay rw\n2 1 8:1 / /workspace rw - xfs /dev/data rw\n'
            r=storage_policy(mount_layout(text),30*GIB)
            self.assertTrue(r['separate_disk_mount_observed'])
            self.assertFalse(r['persistence_verified'])
        def test_storage_nested_path(self):
            text='1 0 0:1 / / rw - overlay overlay rw\n2 1 8:1 / /data rw - xfs /dev/data rw\n'
            r=mount_layout(text,'/data/workspace')
            self.assertEqual(r['mount_target'],'/data')
        def test_storage_prefix_not_mount(self):
            text='1 0 0:1 / / rw - overlay overlay rw\n2 1 8:1 / /work rw - xfs /dev/data rw\n'
            self.assertEqual(mount_layout(text)['mount_target'],'/')
        def test_storage_tmpfs_refused(self):
            self.assertRaises(Blocked,mount_layout,'1 0 0:1 / / rw - overlay overlay rw\n2 1 0:2 / /workspace rw - tmpfs tmpfs rw\n')
        def test_storage_readonly_refused(self):
            self.assertRaises(Blocked,mount_layout,'1 0 0:1 / / ro - overlay overlay ro\n')
        def test_storage_insufficient_even_with_ack(self):
            r=mount_layout('1 0 0:1 / / rw - overlay overlay rw\n')
            self.assertRaises(Blocked,storage_policy,r,1*GIB,True)
        def test_storage_exact_free_boundary(self):
            r=mount_layout('1 0 0:1 / / rw - overlay overlay rw\n')
            self.assertEqual(storage_policy(r,MIN_PREPARE_FREE,True)['minimum_free_bytes'],MIN_PREPARE_FREE)
        def test_storage_bad_mountinfo(self):
            self.assertRaises(Blocked,mount_layout,'not mountinfo')
        def test_storage_empty_mountinfo(self):self.assertRaises(Blocked,mount_layout,'')
        def test_storage_escape(self):
            r=mount_layout(r'1 0 8:1 / /work\040space rw - xfs /dev/data rw','/work space')
            self.assertEqual(r['mount_target'],'/work space')
        def test_ephemeral_flag_propagated(self):
            self.assertIn('--allow-ephemeral-preparation',worker_command(True))
            self.assertNotIn('--allow-ephemeral-preparation',worker_command(False))
        def test_no_benchmark_argv(self):
            self.assertIn('--_worker',worker_command(True))
            self.assertNotIn('--generate',worker_command(True))
        def test_v1_preserved_namespace(self):
            self.assertEqual(ROOT,Path('/workspace/cpucond-runpod-a40-prepare-v3'))
            self.assertTrue(LOCAL_REL.endswith('runpod-a40-prepare-v3'))
        def test_receipt_missing_local_artifact_not_success(self):
            with tempfile.TemporaryDirectory() as d:
                self.assertRaises(Blocked,verify_local_collection,Path(d),{'report_sha256':'a','files':{'report.json':'a'}})
        def test_receipt_bad_local_artifact_not_success(self):
            with tempfile.TemporaryDirectory() as d:
                write(Path(d)/'report.json',b'bad')
                self.assertRaises(Blocked,verify_local_collection,Path(d),{'report_sha256':'a','files':{'report.json':'a'}})
        def test_receipt_copy_fullset(self):
            with tempfile.TemporaryDirectory() as d:
                dest=Path(d);raw=b'{}\n';write(dest/'report.json',raw);write(dest/'storage.json',raw)
                r={'report_sha256':sha(raw),'files':{'report.json':sha(raw),'storage.json':sha(raw)}}
                self.assertEqual(len(verify_local_collection(dest,r)),2)
        def test_receipt_unsafe_path(self):
            with tempfile.TemporaryDirectory() as d:
                self.assertRaises(Blocked,verify_local_collection,Path(d),
                    {'report_sha256':'a','files':{'report.json':'a','../no':'b'}})
        def test_receipt_disagreeing_report_pin(self):
            with tempfile.TemporaryDirectory() as d:
                self.assertRaises(Blocked,verify_local_collection,Path(d),{'report_sha256':'a','files':{'report.json':'b'}})


        def test_logging_level_is_trace4(self):
            args=server_argv(Path('/bin/s'),Path('/m'))
            self.assertEqual(args[args.index('--log-verbosity')+1],'4')
            self.assertEqual(args[args.index('--log-colors')+1],'off')
        def test_cached_source_namespace(self):
            self.assertEqual(CACHE_ROOT,Path('/workspace/cpucond-runpod-a40-prepare-v2'))
            self.assertNotEqual(CACHE_ROOT,ROOT)
        def test_no_download_install_or_build_functions(self):
            for name in ('download_model','build_runtime','ensure_build_tools','public_bytes'):
                self.assertNotIn(name,globals())
        def test_runtime_table_valid(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);files={'llama-server':b'bin','libggml-cuda.so.1':b'lib'}
                for name,b in files.items():write(p/name,b)
                (p/'libggml-cuda.so').symlink_to('libggml-cuda.so.1')
                r=verify_runtime_files(p,{n:sha(b) for n,b in files.items()})
                self.assertEqual(r['links']['libggml-cuda.so']['resolved'],'libggml-cuda.so.1')
        def test_runtime_table_tamper(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);write(p/'libggml-cuda.so.1',b'bad')
                self.assertRaises(Blocked,verify_runtime_files,p,{'libggml-cuda.so.1':sha(b'good')})
        def test_runtime_table_escaped_symlink(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'bin';p.mkdir();write(p/'libggml-cuda.so.1',b'lib')
                write(Path(d)/'outside',b'lib');(p/'libggml-cuda.so').symlink_to('../outside')
                self.assertRaises(Blocked,verify_runtime_files,p,{'libggml-cuda.so.1':sha(b'lib')})
        def test_runtime_missing_cuda(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);write(p/'llama-server',b'bin')
                self.assertRaises(Blocked,verify_runtime_files,p,{'llama-server':sha(b'bin')})
        def test_cached_model_no_write(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'m';b=b'GGUFfixture';write(p,b);p.chmod(0o444)
                old=p.stat().st_mtime_ns
                try:
                    verify_model_file(p,sha(b),len(b))
                    self.assertEqual(p.stat().st_mtime_ns,old)
                    self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o444)
                finally:p.chmod(0o600)
        def test_cached_model_header(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'m';b=b'BAD!fixture';write(p,b)
                self.assertRaises(Blocked,verify_model_file,p,sha(b),len(b))
        def test_logging_source_unpinned_refused(self):
            self.assertRaises(Blocked,logging_contract,b'wrong source',b'wrong header')
        def test_offload_wait_missing_rejected(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'log';p.write_text('model loaded\n')
                proc=unittest.mock.Mock();proc.poll.return_value=None
                self.assertRaises(Blocked,wait_for_offload,p,proc,0.01)
        def test_verbosity_gated_real_child_log(self):
            # A synthetic child simulates default suppression and level-4 output.
            for level in (3,4):
                with tempfile.TemporaryDirectory() as d:
                    p=Path(d)/'log'
                    code="import sys,time;v=int(sys.argv[1]);print('offloaded 49/49 layers to GPU' if v>=4 else 'model loaded',flush=True);time.sleep(30)"
                    with p.open('wb') as log:
                        child=subprocess.Popen([sys.executable,'-u','-c',code,str(level)],stdout=log,stderr=log,start_new_session=True)
                    try:
                        if level==4:self.assertTrue(wait_for_offload(p,child,3)['full_offload'])
                        else:self.assertRaises(Blocked,wait_for_offload,p,child,0.1)
                    finally:stop_process(child)
        def test_permissions_do_not_touch_old_cache(self):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);new=p/'new';new.mkdir();cache=p/'old';cache.mkdir();f=cache/'m';write(f,b'fixture');f.chmod(0o444)
                try:
                    with patch(__name__+'.ROOT',new),patch(__name__+'.CACHE_ROOT',cache):permissions_for_inference()
                    self.assertEqual(stat.S_IMODE(f.stat().st_mode),0o444)
                    self.assertEqual(f.read_bytes(),b'fixture')
                    self.assertEqual(sorted(x.name for x in new.iterdir()),['infer-home'])
                finally:f.chmod(0o600)

    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    need(result.wasSuccessful(),'Self tests failed')
    print('A40_PREPARE_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=LOCAL_SYNTHETIC_CACHE_LOGGING_AND_REAL_CHILD_CLEANUP; NO_REAL_SSH_OR_GPU_INFERENCE')

def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('run','watch','status','self-test','_launch','_status','_worker'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--_read',choices=PUBLIC_FILES)
    p.add_argument('--allow-ephemeral-preparation',action='store_true',
        help='Explicitly permit rebuildable model/build assets and ONE smoke on ephemeral disk; NOT benchmark generation')
    a=p.parse_args()
    need(not a.allow_ephemeral_preparation or a.run or a._launch or a._worker,
         '--allow-ephemeral-preparation is only used to authorize preparation start')
    if a.self_test:self_test();return
    if a._worker:worker(a.allow_ephemeral_preparation);return
    if a._launch:print(json.dumps(launch(a.allow_ephemeral_preparation)));return
    if a._status:print(json.dumps(remote_status()));return
    if a._read:
        remote_guard();path=safe(ROOT/a._read)
        if not path.exists():print(json.dumps({'missing':True}));return
        need(path.is_file() and path.stat().st_size<=16*1024**2,'Metadata/log too large')
        b=path.read_bytes();print(json.dumps({'data':base64.b64encode(b).decode(),'sha256':sha(b)}));return
    local('run' if a.run else 'watch' if a.watch else 'status',a.allow_ephemeral_preparation)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('A40_PREPARATION_BLOCKED: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        raise SystemExit(2)
