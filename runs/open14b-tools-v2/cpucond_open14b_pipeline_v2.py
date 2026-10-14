#!/usr/bin/env python3
"""Explicit NEW Qwen2.5-Coder-14B Q4_K_M campaign on the existing Skylake host.

WSL: --self-test; --run (start, watch, collect); --watch; --status; --collect; --stop.
This is NOT a Qwen3-Coder-Next/Stage26 continuation. Existing experiments are
read-only. API keys, cloud inference, rentals, package upgrades and automatic
candidate retries are not used. Numeric validation/timing are delegated to
SHA-pinned existing Stage25C helpers. A finite test is not a proof of equivalence.
"""
from __future__ import annotations

import argparse
import contextlib
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import http.client
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import types
import unittest
from unittest.mock import patch
import urllib.request
import urllib.parse
import uuid

VERSION = '1.0.1'
HOST = 'cpucond-skylake-01'
SERVER = 'root@192.0.2.1'
ROOT = Path('/srv/research/cpucond-open14b-skylake-five-arm-v2')
ASSETS = Path('/var/lib/cpucond-open14b-skylake-v1')
OLD = Path('/srv/research/cpucond-stage25c-gpt-skylake-autopipeline-v1_2')
UNIT = 'cpucond69-open14b-skylake-v2.service'
MODEL = 'qwen2.5-coder:14b-instruct-q4_K_M'
MODEL_MANIFEST_PREFIX = '9ec8897f747e'
MODEL_URL = 'https://registry.ollama.ai/v2/library/qwen2.5-coder/manifests/14b-instruct-q4_K_M'
LLAMA_TAG = 'b10964'
LLAMA_COMMIT = 'b29c606e28a01b1bc8c1351026a0fa6e616bf6c4'
LLAMA_ASSET = 'llama-b10964-bin-ubuntu-x64.tar.gz'
LLAMA_ARCHIVE_SHA = '9abf88aea48a55d0f80edb1ee20220b186848cca0b4e919d71518cfd7ca67443'
LLAMA_ARCHIVE_BYTES = 16825086
LLAMA_RELEASE = 'https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/' + LLAMA_TAG
COHORT = 'qwen25coder14b-q4km-llamacpp-skylake-five-arm-v1'
COMPLETE = 'OPEN14B_900_GENERATION_VALIDATION_TIMING_ARCHIVE_COMPLETE'
CORE_SHA = '976d2b5295674283ee723ececd1a3a6750cc4b245fbfaff0446ec9241141bfe2'
POLICY_SHA = 'e10fe4a3a9d1cfed6633147d7546b70b1e03e3d1c8fc29d4bf0ed18b471963ba'
CLANG_SHA = '8ef402d453d1ba4902e4ee0f0f847f6cfa01400c95aa43c24e97818b9c0e3f45'
ENGINE_SHA = 'c0f16b48924a81320aee74f16b6b136503667d648a0dc2ee61e2c807c53fc47c'
BATCH_SHA = '8980a24f238df7b8285508c6a319a5f5835774b49ff17a82037aa158a0b9d427'
ORDER_SHA = 'abfd125741e68f95e5e86dd033478672b776736b005b0fec96a5f12338f06d9a'
OLD_ANALYSIS_SHA = '43789ffef47422aad912c7d2270fd99e1e7adc9065d4085641eb99ef5020fbf7'
PINS = {
    'host.py': '9005ac8eda4b6ed5d869cca9b0b7a535067984adb7b90e6a1b405be7055d3b23',
    'performance.py': 'cfecdb283ed6ac5c5fa44f9370b6e451dfd0fd323216dd78ec19a33dd8875b0b',
    'statistics.py': 'a5545ff53b0bfce371e66b01d157dc193f47b9de69010873f41a6910162827bb',
}
KERNELS = tuple('2mm 3mm adi atax bicg cholesky correlation covariance deriche doitgen durbin fdtd-2d floyd-warshall gemm gemver gesummv gramschmidt heat-3d jacobi-1d jacobi-2d lu ludcmp mvt nussinov seidel-2d symm syr2k syrk trisolv trmm'.split())
SIZES = ('MINI', 'SMALL', 'MEDIUM')
FORMS = ('C', 'IR')
ARMS = ('P0', 'S1', 'S2', 'W1', 'W2')
LABELS = {'P0':'P0', 'S1':'P1', 'S2':'P2', 'W1':'P1', 'W2':'P2'}
CAPS = {'C':4096, 'IR':16384}
SYSTEM = 'You optimize numerical code under the supplied exact correctness contract. Return only the complete requested code, without explanations or tool use.'
BEGIN = '----- BEGIN ORIGINAL CODE -----\n'
END = '----- END ORIGINAL CODE -----'
CPU, NODE, PORT, CTX = 2, 0, 11527, 32768
RESERVE, GIB, TOTAL = 32, 1024**3, 900
MAX_META, MAX_STREAM = 256*1024**2, 16*1024**2
CID = re.compile(r'q27__([a-z0-9-]+)__(MINI|SMALL|MEDIUM)__(C|IR)__(P0|S1|S2|W1|W2)__s0')
HEX = re.compile(r'[0-9a-f]{64}')
LOCKS = (
    '/run/lock/cpucond-skylake-experiment.lock',
    '/run/lock/cpucond-benchmark-exclusive.lock',
    '/run/lock/cpucond-revalidation079.lock',
)
# These are frozen settings for this NEW backend, not an equivalence claim with Ollama.
SAMPLING = dict(seed=69001, temperature=0.2, top_k=40, top_p=0.9, min_p=0.0,
                typical_p=1.0, repeat_penalty=1.0, repeat_last_n=64,
                presence_penalty=0.0, frequency_penalty=0.0,
                dry_multiplier=0.0, xtc_probability=0.0, mirostat=0,
                dynatemp_range=0.0, samplers=['top_k','top_p','min_p','temperature'],
                cache_prompt=False, n_keep=-1, ignore_eos=False, n_cmpl=1,
                stop=['<|im_end|>', '<|im_start|>'])

class Blocked(RuntimeError):
    pass

def need(ok, message):
    if not ok:
        raise Blocked(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def canon(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False)+'\n').encode()

def sha(b):
    return hashlib.sha256(b).hexdigest()

def parse(b):
    def pairs(xs):
        out = {}
        for k, v in xs:
            need(k not in out, 'Duplicate JSON key: '+k)
            out[k] = v
        return out
    def bad(x):
        raise Blocked('Nonfinite JSON number')
    def floating(x):
        v = float(x)
        need(math.isfinite(v), 'Nonfinite JSON number')
        return v
    return json.loads(b, object_pairs_hook=pairs, parse_constant=bad, parse_float=floating)

def rel(n):
    need(isinstance(n,str) and n and '\\' not in n and
         not any(ord(c)<32 or ord(c)==127 for c in n), 'Invalid relative path')
    p = PurePosixPath(n)
    need(not p.is_absolute() and '..' not in p.parts and str(p)==n and n!='.', 'Unsafe relative path: '+repr(n))
    return n

def checked(p):
    p = Path(p).absolute()
    need('..' not in p.parts, 'Parent traversal')
    for q in (p,*p.parents):
        need(not q.is_symlink(), 'Symlink refused: '+str(q))
    return p

def sig(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def regular(p):
    p = checked(p)
    fd = os.open(p, os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    f = os.fdopen(fd,'rb')
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        f.close()
        raise Blocked('Nonregular file: '+str(p))
    return f

def read(p, limit=MAX_META):
    with regular(p) as f:
        before = os.fstat(f.fileno())
        need(before.st_size<=limit, 'Oversize metadata: '+str(p))
        b = f.read(limit+1)
        need(len(b)==before.st_size and sig(before)==sig(os.fstat(f.fileno())), 'File changed: '+str(p))
    return b

def hfile(p):
    with regular(p) as f:
        before = os.fstat(f.fileno()); h=hashlib.sha256(); n=0
        for b in iter(lambda:f.read(4*1024**2),b''):
            h.update(b); n+=len(b)
        need(n==before.st_size and sig(before)==sig(os.fstat(f.fileno())), 'File changed while hashing: '+str(p))
    return h.hexdigest()

def save(p,b):
    p=checked(p); p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:
        f.write(b); f.flush(); os.fsync(f.fileno())

def jw(p,x):
    save(p,canon(x))

def atomic(p,x):
    p=checked(p); tmp=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex)
    jw(tmp,x); os.replace(tmp,p)

def loadmod(p,pin,name):
    raw=read(p); need(sha(raw)==pin,'Pinned module changed: '+str(p))
    m=types.ModuleType(name+'_'+uuid.uuid4().hex); m.__file__=str(p)
    sys.modules[m.__name__]=m
    exec(compile(raw,str(p),'exec'),m.__dict__)
    return m

def identity(cid):
    m=CID.fullmatch(cid) if isinstance(cid,str) else None
    need(m is not None and m[1] in KERNELS, 'Invalid NEW campaign ID: '+repr(cid))
    return dict(id=cid,task=m[1],size=m[2],form=m[3],condition=m[4])

def grid():
    return {'q27__'+'__'.join((k,z,f,a,'s0')) for k in KERNELS for z in SIZES for f in FORMS for a in ARMS}

def controls_env():
    return {'PATH':'/usr/sbin:/usr/bin:/sbin:/bin', 'HOME':'/root',
            'LANG':'C.UTF-8', 'LC_ALL':'C.UTF-8', 'PYTHONDONTWRITEBYTECODE':'1'}

def command(argv, **kw):
    return subprocess.run(argv,check=True,env=controls_env(),**kw)

@contextlib.contextmanager
def locks():
    with contextlib.ExitStack() as es:
        for path in LOCKS:
            fd=os.open(checked(path),os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
            f=es.enter_context(os.fdopen(fd,'a'))
            try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Blocked('Existing experiment/backup is using '+path+'; nothing is stopped') from exc
        yield

def meminfo():
    d={}
    for line in Path('/proc/meminfo').read_text().splitlines():
        k,_,v=line.partition(':')
        if k in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):
            d[k]=int(v.split()[0])*1024
    return d

def host_basic():
    need(sys.version_info >= (3,12),'Python 3.12 or newer is required; no package upgrade is attempted')
    need(sys.platform=='linux' and os.geteuid()==0 and socket.gethostname().split('.')[0]==HOST,'Wrong server/user')
    need(os.uname().machine=='x86_64','x86_64 required')

def unit_state():
    p=subprocess.run(['systemctl','show',UNIT,'-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus'],
                     capture_output=True,text=True,timeout=20)
    return dict(l.split('=',1) for l in p.stdout.splitlines() if '=' in l)

def cgroup_guard(private=False):
    host_basic()
    need(os.environ.get('CPUCOND_BATCH_UNIT')==UNIT,'Must run in the owned systemd service')
    cg=[l.split(':',2)[2] for l in Path('/proc/self/cgroup').read_text().splitlines() if l.startswith('0::')]
    need(len(cg)==1 and UNIT in PurePosixPath(cg[0]).parts, 'Wrong cgroup')
    base=Path('/sys/fs/cgroup')/cg[0].lstrip('/')
    vals={n:(base/n).read_text().strip() for n in ('memory.max','memory.swap.max','pids.max')}
    need(vals['memory.max'].isdigit() and int(vals['memory.max'])<=24*GIB,'24GiB memory cap absent')
    need(vals['memory.swap.max']=='0' and vals['pids.max'].isdigit() and int(vals['pids.max'])<=256,'Swap/task cap absent')
    if private:
        need(os.readlink('/proc/self/ns/net')!=os.readlink('/proc/1/ns/net'),'Private network missing')
    return vals

def update(**kw):
    p=ROOT/'progress.json'
    s=parse(read(p)) if p.exists() else dict(version=VERSION,model=MODEL,requests_total=TOTAL,started_utc=now())
    s.update(kw); s['updated_utc']=now(); atomic(p,s)
    if 'phase' in kw:
        print('PHASE='+kw['phase'],flush=True)

# Input and numeric pipeline recovery reads only the already-snapshotted Stage25C
# inputs. No old generated candidates, timing values, or provider API code are used.
def prepare_inputs():
    old=OLD/'inputs/static'
    launch=parse(read(OLD/'control/launch.json'))
    raw=read(old/'snapshot-manifest.json')
    need(sha(raw)==launch['static_manifest_sha256'],'Original static manifest changed')
    table=parse(raw)
    def get(n):
        rel(n); e=table[n]; b=read(old/n)
        need(len(b)==e['bytes'] and sha(b)==e['sha256'],'Original input changed: '+n)
        return b
    core=read(OLD/'control/runner.py'); need(sha(core)==CORE_SHA,'Stage25C runner mismatch')
    payload={'runtime/core.py':core}
    for n in sorted(table):
        if n.startswith(('package/','references/','policy/')) or n in tuple('runtime/'+x for x in PINS)+('runtime/measurement-library.py',):
            payload[n]=get(n)
    for n,pin in PINS.items():
        need(sha(payload['runtime/'+n])==pin,'Wrong numeric helper: '+n)
    need(sha(payload['policy/validator-v1_2.py'])==POLICY_SHA,'Wrong numerical validator')
    br=get('bundle/openai_batch_requests.jsonl'); need(sha(br)==BATCH_SHA,'Wrong role request batch')
    orderraw=get('bundle/order.json'); need(sha(orderraw)==ORDER_SHA,'Wrong input order')
    ar=get('bundle/analysis-plan.json'); need(sha(ar)==OLD_ANALYSIS_SHA,'Wrong analysis design')
    reqs=[parse(b) for b in br.splitlines()]; metas=[parse(b) for b in get('bundle/requests_meta.jsonl').splitlines()]
    order=parse(orderraw)['order']; blocks={a:get('bundle/prompts/cpu-'+a+'.txt').decode() for a in ARMS}
    need(len(reqs)==len(metas)==len(order)==TOTAL,'Wrong request cardinality')
    seen=set(); neutral={}; rows=[]; positions={a:Counter() for a in ARMS}
    for i,(r,mt) in enumerate(zip(reqs,metas)):
        oldid=r['custom_id']; need(oldid==order[i]==mt['id']==mt['custom_id'] and oldid.startswith('g25__'),'Input ordering mismatch')
        cid='q27__'+oldid[len('g25__'):]; ident=identity(cid)
        need(cid not in seen,'Duplicate ID'); seen.add(cid)
        for k in ('task','size','form','condition'): need(mt[k]==ident[k],'Input identity mismatch')
        messages=r['body']['input']; need(len(messages)==2 and messages[0]=={'role':'system','content':SYSTEM},'System prompt changed')
        need(set(messages[1])=={'role','content'} and messages[1]['role']=='user','Wrong roles')
        u=messages[1]['content']; a=ident['condition']; f=ident['form']; k=ident['task']; z=ident['size']
        need(u.count(BEGIN)==u.count(END)==1 and u[:u.index(BEGIN)].isascii(),'Source boundaries/language')
        start=u.index(BEGIN)+len(BEGIN); end=u.index(END); code=u[start:end]
        ref=f'references/{k}/{z}/kernel.'+('c' if f=='C' else 'll')
        need(code==payload[ref].decode().rstrip()+'\n','Original code embedding changed')
        need(mt['source_sha256']==sha(payload[ref]),'Original code digest changed')
        need(r['body']['max_output_tokens']==CAPS[f],'Original output cap changed')
        block=blocks[a]; need(u.count(block)==1 and u.index(block)+len(block)<u.index(BEGIN),'CPU block not unique')
        zero=u.replace(block,blocks['P0'],1); key=(k,z,f)
        need(key not in neutral or neutral[key]==zero,'Non-CPU prompt difference'); neutral[key]=zero
        req={'messages':messages,'form':f,'output_token_cap':CAPS[f]}
        payload['requests/'+cid+'.json']=canon(req)
        rows.append({**ident,'cohort':COHORT,'prompt_condition_label':LABELS[a], 'sample':0,
                     'request':'requests/'+cid+'.json','request_sha256':sha(canon(req)),
                     'source_reference':ref,'original_source_sha256':sha(payload[ref]),
                     'origin_role_id':oldid,'old_answers_reused':False})
        positions[a][i%5]+=1
    need(seen==grid(),'Grid incomplete')
    for i in range(0,TOTAL,5):
        rs=rows[i:i+5]
        need(len({(r['task'],r['size'],r['form']) for r in rs})==1 and {r['condition'] for r in rs}==set(ARMS),'Five-arm block broken')
    need(all(len(c)==5 and set(c.values())=={36} for c in positions.values()),'Position balance differs')
    analysis=parse(ar); analysis.update(cohort=COHORT,model=MODEL,
        timing='Frozen for this separate 14B/backend campaign after earlier experiments; not whole-study preregistration.',
        backend='llama.cpp '+LLAMA_TAG, previous_analysis_plan_sha256=OLD_ANALYSIS_SHA,
        generation_execution_host_differs_from_evaluation_host=False,
        generation_settings=SAMPLING,normalization='strip whitespace; unwrap at most one code fence; no code repair')
    payload['analysis-plan.json']=canon(analysis)
    payload['rows.json']=canon(rows)
    payload['role-source.jsonl']=br
    payload['origin-static-manifest.json']=raw
    payload['plan.json']=canon(dict(schema='open14b-new-campaign-v1',model=MODEL,cohort=COHORT,requests_total=TOTAL,
        forms=FORMS,conditions=ARMS,generations_per_slot=1,context_length=CTX,output_caps=CAPS,
        sampling=SAMPLING,backend_tag=LLAMA_TAG,backend_commit=LLAMA_COMMIT,
        prior_qwen3next_replaced=False,prior_qwen3next_results_combined=False,
        generation_and_measurement_overlap=False,generation_threads=4,measurement_cpu=CPU,
        finite_validation_not_formal_proof=True,old_results_modified=False))
    out=ROOT/'inputs'; need(not out.exists(),'Inputs already exist; no blind restart')
    manifest={}
    for n,b in sorted(payload.items()):
        save(out/rel(n),b); os.chmod(out/n,0o444); manifest[n]={'sha256':sha(b),'bytes':len(b)}
    jw(out/'snapshot-manifest.json',manifest)
    jw(ROOT/'input-receipt.json',{'sha256':hfile(out/'snapshot-manifest.json'),'files':len(manifest),'utc':now()})
    print('INPUTS_READY=900; old candidate and timing data not imported',flush=True)

def verify_inputs():
    out=ROOT/'inputs'; rr=parse(read(ROOT/'input-receipt.json')); raw=read(out/'snapshot-manifest.json')
    need(sha(raw)==rr['sha256'],'Input manifest changed')
    table=parse(raw)
    for n,d in table.items():
        b=read(out/rel(n)); need(len(b)==d['bytes'] and sha(b)==d['sha256'],'New snapshot changed: '+n)
    return table

def modules():
    p=ROOT/'inputs'; core=loadmod(p/'runtime/core.py',CORE_SHA,'core27')
    ms={n:loadmod(p/'runtime'/n,pin,'open14b_'+n.replace('.','_')) for n,pin in PINS.items()}
    c,e,f=ms['host.py'],ms['performance.py'],ms['statistics.py']; m,raw=e.helper()
    need(raw==read(p/'runtime/measurement-library.py'),'Measurement library differs')
    need(c.POLICY_SHA==POLICY_SHA and c.CLANG_SHA==CLANG_SHA and c.HOST==HOST,'Host helper lineage')
    need(e.ENGINE_SHA==ENGINE_SHA and e.DEFAULTS==core.DEFAULTS,'Timer protocol changed')
    # Explicit namespace/config adaptation only; source bytes and numeric funcs
    # remain pinned. The old core main(), arm(), API replay and run() are NOT used.
    core.CID=CID; core.grid=grid; core.MODEL=MODEL; core.COHORT=COHORT
    core.COMPLETE=COMPLETE; core.VCOMPLETE='OPEN14B_FINITE_VALIDATION_COMPLETE'
    core.PCOMPLETE='OPEN14B_STOCK_TIMING_COMPLETE'; core.ACOMPLETE='OPEN14B_ANALYSIS_COMPLETE'
    core.ANALYSIS_SHA=hfile(p/'analysis-plan.json')
    core.check_analysis_plan(parse(read(p/'analysis-plan.json')))
    return core,c,e,f,m

# Downloads are public fixed-runtime/model assets only. Requests carry no
# provider credentials and do not transmit prompts or experiment files.
class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        need(urllib.parse.urlparse(newurl).scheme=='https','HTTPS redirect required')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),HTTPSRedirect())

def public_get(url):
    need(urllib.parse.urlparse(url).scheme=='https','HTTPS required')
    req=urllib.request.Request(url,headers={'User-Agent':'cpucond-open14b/1.0','Accept':'application/json'})
    with opener().open(req,timeout=120) as r:
        b=r.read(8*1024**2+1)
        need(r.status==200 and len(b)<=8*1024**2,'Metadata download failed/too large')
    return b

def download(url,path,pin,size):
    need(HEX.fullmatch(pin) is not None and type(size) is int and 0<size<=12*GIB,'Download contract invalid')
    path=checked(path); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        need(path.stat().st_size==size and hfile(path)==pin,'Cached asset mismatch')
        return
    part=path.with_name(path.name+'.partial'); contract=part.with_name(part.name+'.json')
    want=dict(url=url,sha256=pin,bytes=size)
    if part.exists(): need(contract.exists() and parse(read(contract))==want,'Unrecognized partial download')
    elif not contract.exists(): jw(contract,want)
    else: need(parse(read(contract))==want,'Partial download metadata conflict')
    for attempt in range(4):
        offset=part.stat().st_size if part.exists() else 0
        need(offset<=size,'Oversize partial')
        if offset==size: break
        headers={'User-Agent':'cpucond-open14b/1.0'}
        if offset: headers['Range']='bytes='+str(offset)+'-'
        try:
            with opener().open(urllib.request.Request(url,headers=headers),timeout=120) as r:
                if offset:
                    need(r.status==206 and r.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-'), 'Download resume not supported; partial retained')
                else: need(r.status==200,'Unexpected download status')
                last=offset
                with part.open('ab' if offset else 'xb') as f:
                    count=offset
                    while True:
                        b=r.read(4*1024**2)
                        if not b: break
                        count+=len(b); need(count<=size,'Download exceeds pinned size'); f.write(b)
                        if count-last>=256*1024**2:
                            print('DOWNLOAD '+path.name+' '+str(count)+'/'+str(size),flush=True); last=count
                    f.flush(); os.fsync(f.fileno())
            if count==size: break
        except (OSError, http.client.HTTPException) as exc:
            if attempt==3: raise
            print('PUBLIC_ASSET_DOWNLOAD_RETRY '+type(exc).__name__+'; no model generation',flush=True)
            time.sleep(5)
    need(part.is_file() and part.stat().st_size==size and hfile(part)==pin,'Downloaded asset integrity failed')
    os.rename(part,path); os.chmod(path,0o444)

def extract_runtime(archive,dest):
    need(not dest.exists(),'Runtime destination already exists')
    dest.mkdir(mode=0o755)
    dest.chmod(0o755)  # Explicit: the coordinator umask is 0077.
    with tarfile.open(archive,'r:gz') as tf:
        members=tf.getmembers(); need(len(members)<20000,'Runtime archive too many files')
        need(sum(t.size for t in members)<=2*GIB,'Runtime archive too large')
        for t in members:
            n=t.name.removeprefix('./').rstrip('/')
            if n in ('','.') and t.isdir(): continue
            rel(n)
            need(t.isfile() or t.isdir() or t.issym() or t.islnk(),'Runtime archive special file')
            if t.issym() or t.islnk():
                need(not PurePosixPath(t.linkname).is_absolute(),'Absolute runtime link')
        tf.extractall(dest,filter='data')
    servers=[]
    for p in dest.rglob('*'):
        if p.is_symlink():
            need(p.resolve().is_relative_to(dest.resolve()),'Runtime symlink escapes')
            continue
        if p.is_dir(): p.chmod(0o755)
        elif p.is_file():
            p.chmod(0o755 if p.stat().st_mode&0o111 else 0o644)
            if p.name=='llama-server': servers.append(p)
    need(len(servers)==1,'Expected exactly one llama-server executable')
    return servers[0]

def acquire_assets():
    checked(ASSETS); ASSETS.mkdir(mode=0o755,parents=True,exist_ok=True)
    ASSETS.chmod(0o755)  # Nobody must traverse the public, root-owned asset directory.
    raw=public_get(LLAMA_RELEASE); rr=parse(raw)
    need(rr['tag_name']==LLAMA_TAG and rr['target_commitish']==LLAMA_COMMIT and not rr['draft'],'Runtime release changed')
    aa=[a for a in rr['assets'] if a['name']==LLAMA_ASSET]
    need(len(aa)==1,'Official CPU runtime asset missing')
    a=aa[0]; dg=a.get('digest',''); need(dg.startswith('sha256:') and HEX.fullmatch(dg[7:]),'Official runtime digest absent')
    need(a['browser_download_url']=='https://github.com/ggml-org/llama.cpp/releases/download/'+LLAMA_TAG+'/'+LLAMA_ASSET,'Unexpected runtime URL')
    need(a['size']==LLAMA_ARCHIVE_BYTES and dg[7:]==LLAMA_ARCHIVE_SHA,
         'Official pinned CPU runtime archive changed; no backend fallback')
    jw(ROOT/'acquisition/runtime-release.json',rr)
    archive=ASSETS/LLAMA_ASSET; download(a['browser_download_url'],archive,dg[7:],a['size'])
    runtime_dest=ASSETS/'runtime'
    if runtime_dest.exists():
        need(runtime_dest.is_dir() and not runtime_dest.is_symlink(),'Cached runtime directory invalid')
        # Reconstruct the pinned 16MB runtime archive in a temporary directory and
        # compare every regular file and symlink. This proves that reuse of the
        # already-downloaded runtime is byte-identical to the pinned public asset.
        with tempfile.TemporaryDirectory(prefix='open14b-runtime-verify-',dir=str(ASSETS)) as td:
            fresh=Path(td)/'runtime'
            fresh_binary=extract_runtime(archive,fresh)
            def inventory(root):
                out={}
                for p in sorted(root.rglob('*')):
                    n=p.relative_to(root).as_posix()
                    if p.is_symlink():
                        out[n]=('symlink',os.readlink(p))
                    elif p.is_file():
                        out[n]=('file',hfile(p))
                    elif p.is_dir():
                        out[n]=('dir',None)
                    else:
                        raise Blocked('Unexpected runtime filesystem entry: '+str(p))
                return out
            need(inventory(runtime_dest)==inventory(fresh),'Cached runtime differs from pinned archive')
            relbin=fresh_binary.relative_to(fresh)
        binary=runtime_dest/relbin
        need(binary.is_file() and os.access(binary,os.X_OK),'Cached llama-server executable missing')
        print('PINNED_RUNTIME_CACHE_VERIFIED; no runtime redownload/execution change',flush=True)
    else:
        binary=extract_runtime(archive,runtime_dest)
    raw=public_get(MODEL_URL); md=sha(raw); manifest=parse(raw)
    need(md.startswith(MODEL_MANIFEST_PREFIX),'Published model manifest changed; no automatic model switch')
    need(manifest.get('schemaVersion')==2,'Unexpected model manifest schema')
    layers=[x for x in manifest['layers'] if x.get('mediaType')=='application/vnd.ollama.image.model']
    need(len(layers)==1,'Expected one GGUF model layer')
    layer=layers[0]; digest=layer['digest']; size=layer['size']
    need(digest.startswith('sha256:') and HEX.fullmatch(digest[7:]) and 8*GIB<=size<=11*GIB,'Wrong 14B Q4 model layer')
    save(ROOT/'acquisition/ollama-manifest.json',raw)
    # Retain public small metadata/license layers without executing any template
    # supplied by the registry. Actual rendering uses the GGUF's native template.
    aux=[]
    for desc in [manifest['config'], *manifest['layers']]:
        if desc.get('mediaType')=='application/vnd.ollama.image.model': continue
        dh=desc['digest']; dn=desc['size']
        need(dh.startswith('sha256:') and HEX.fullmatch(dh[7:]) and 0<dn<=1024**2,
             'Unexpected nonweight model metadata')
        path=ROOT/'acquisition/model-metadata'/dh[7:]
        download('https://registry.ollama.ai/v2/library/qwen2.5-coder/blobs/'+dh,path,dh[7:],dn)
        aux.append(dict(desc,path=path.relative_to(ROOT).as_posix()))
    jw(ROOT/'acquisition/model-metadata/index.json',aux)
    model=ASSETS/(digest[7:]+'.gguf')
    download('https://registry.ollama.ai/v2/library/qwen2.5-coder/blobs/'+digest,model,digest[7:],size)
    with regular(model) as fp: need(fp.read(4)==b'GGUF','Model is not GGUF')
    files={}
    for p in (ASSETS/'runtime').rglob('*'):
        if p.is_file() and not p.is_symlink(): files[str(p.relative_to(ASSETS))]=hfile(p)
    rec=dict(model=MODEL,model_manifest_sha256=md,model_sha256=digest[7:],model_bytes=size,model_file=str(model),
             backend_tag=LLAMA_TAG,backend_commit=LLAMA_COMMIT,backend_archive_sha256=dg[7:],binary=str(binary),
             runtime_files=files,assets_outside_result_archive=True,utc=now())
    jw(ROOT/'acquisition/assets.json',rec)
    return rec

def verify_assets():
    rec=parse(read(ROOT/'acquisition/assets.json'))
    need(rec['model']==MODEL and rec['backend_tag']==LLAMA_TAG and rec['backend_commit']==LLAMA_COMMIT,'Asset identity changed')
    model=checked(rec['model_file']); need(model.parent==ASSETS and hfile(model)==rec['model_sha256'],'Model changed')
    for n,pin in rec['runtime_files'].items(): need(hfile(ASSETS/rel(n))==pin,'Runtime file changed: '+n)
    need(checked(rec['binary']).is_relative_to(ASSETS/'runtime'),'Wrong runtime binary')
    return rec

def loopback(path,payload=None,timeout=120):
    need(path in ('/health','/props','/apply-template','/tokenize'), 'Unexpected native API endpoint')
    con=http.client.HTTPConnection('127.0.0.1',PORT,timeout=timeout)
    try:
        con.request('GET' if payload is None else 'POST',path,body=None if payload is None else canon(payload),headers={'Content-Type':'application/json'})
        r=con.getresponse(); b=r.read(8*1024**2+1)
        need(r.status==200 and len(b)<=8*1024**2,'Native API '+path+' returned '+str(r.status))
        return parse(b)
    finally: con.close()

def llama_command(rec):
    return ['/usr/bin/setpriv','--reuid=65534','--regid=65534','--clear-groups',
        '--bounding-set=-all','--inh-caps=-all','--ambient-caps=-all','--no-new-privs',
        rec['binary'],'--model',rec['model_file'],'--host','127.0.0.1','--port',str(PORT),
        '--ctx-size',str(CTX),'--parallel','1','--threads','4','--threads-batch','4',
        '--cpu-range','0-3','--cpu-strict','1','--cpu-range-batch','0-3','--cpu-strict-batch','1',
        '--batch-size','512','--ubatch-size','512','--n-gpu-layers','0',
        '--cache-type-k','f16','--cache-type-v','f16','--no-context-shift',
        '--alias',MODEL,'--jinja','--device','none','--fit','off','--no-op-offload','--no-repack','--offline']

def start_llama(rec):
    need(set(range(4)) <= os.sched_getaffinity(0),'Generation needs the observed four CPUs 0-3')
    mem=meminfo(); need(mem['MemAvailable']>=21*GIB,'Less than 21GiB available for this 14B generation; no swap fallback')
    log=(ROOT/'llama-server.log').open('xb')
    env=controls_env(); env.update(HOME=str(ASSETS),LD_LIBRARY_PATH=str(Path(rec['binary']).parent),
                                  OMP_NUM_THREADS='4',CUDA_VISIBLE_DEVICES='',HIP_VISIBLE_DEVICES='')
    proc=subprocess.Popen(llama_command(rec),stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                          env=env,cwd=ASSETS,start_new_session=True)
    log.close(); jw(ROOT/'control/llama-process.json',{'pid':proc.pid,'argv':llama_command(rec),'utc':now()})
    try:
        deadline=time.monotonic()+1200
        while time.monotonic()<deadline:
            need(proc.poll() is None,'llama-server exited; inspect llama-server.log')
            try:
                if loopback('/health',timeout=5).get('status')=='ok': break
            except (OSError,Blocked,http.client.HTTPException): pass
            time.sleep(2)
        else: raise Blocked('llama-server health deadline exceeded')
        props=loopback('/props'); need(props['total_slots']==1,'Unexpected parallel slot count')
        settings=props['default_generation_settings']; need(settings['n_ctx']==CTX,'Native context differs')
        need(Path(props['model_path']).resolve()==Path(rec['model_file']).resolve(),'Native server loaded wrong model')
        need(isinstance(props.get('chat_template'),str) and props['chat_template'],'Native chat template missing')
        jw(ROOT/'acquisition/native-props.json',props)
        return proc
    except BaseException:
        stop_llama(proc)
        raise

def stop_llama(proc):
    if proc is None: return
    if proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try: proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL); proc.wait(timeout=20)
    need(proc.poll() is not None,'Inference process still alive')

def token_budget(count,form):
    need(type(count) is int and count>0 and form in CAPS,'Invalid token count')
    return count+CAPS[form]+RESERVE<=CTX

def native_inputs():
    rows=parse(read(ROOT/'inputs/rows.json')); recs=[]
    for i,row in enumerate(rows,1):
        q=parse(read(ROOT/'inputs'/row['request']))
        need(hfile(ROOT/'inputs'/row['request'])==row['request_sha256'],'Role request changed')
        rendered=loopback('/apply-template',{'messages':q['messages']})['prompt']
        need(isinstance(rendered,str) and all(m['content'] in rendered for m in q['messages']),'Native template dropped message content')
        need(rendered.endswith('<|im_start|>assistant\n'),'Unexpected native assistant prefix; no guessed template fallback')
        tokens=loopback('/tokenize',{'content':rendered,'add_special':True,'parse_special':True})['tokens']
        need(isinstance(tokens,list) and tokens and all(type(x) is int and x>=0 for x in tokens),'Native tokenizer schema')
        cid=row['id']; doc=dict(id=cid,prompt=rendered,tokens=tokens,native_input_tokens=len(tokens),
            output_cap=CAPS[row['form']],context_budget_ok=token_budget(len(tokens),row['form']),
            tokenizer='same loaded GGUF and native runtime used for generation')
        jw(ROOT/'native-inputs'/(cid+'.json'),doc)
        recs.append(dict(id=cid,native_input_tokens=len(tokens),context_budget_ok=doc['context_budget_ok'],sha256=hfile(ROOT/'native-inputs'/(cid+'.json'))))
        if i%50==0: print('NATIVE_TOKEN_AUDIT='+str(i)+'/900',flush=True)
    jw(ROOT/'native-input-receipt.json',dict(rows=recs,all_roles_preserved=True,no_truncation=True,utc=now()))
    return rows,{x['id']:x for x in recs}

def completion_body(tokens,form):
    need(token_budget(len(tokens),form),'Context budget exceeded')
    return dict(SAMPLING,prompt=tokens,n_predict=CAPS[form],stream=True,return_tokens=True,
                return_progress=True,sse_ping_interval=15,id_slot=0)

def parse_sse(lines):
    """Replay the exact native server stream; no model calls and no code repair."""
    text=[]; final=None; events=0
    for line in lines:
        line=line.strip()
        if not line or line.startswith(b':'): continue
        need(line.startswith(b'data: '),'Unexpected SSE framing')
        data=line[6:]
        if data==b'[DONE]': continue
        msg=parse(data); need(isinstance(msg,dict) and 'error' not in msg,'Native generation protocol error')
        need(final is None,'Data arrived after terminal response')
        content=msg.get('content',''); need(isinstance(content,str),'Non-text output')
        text.append(content); events+=1
        if msg.get('stop') is True: final=msg
    need(final is not None and events>0,'Incomplete native stream; no automatic resubmission')
    return ''.join(text),final

def normalize_code(text,form):
    if not isinstance(text,str) or not text.strip(): return None,'empty_output'
    if '\x00' in text or '<think>' in text or '</think>' in text: return None,'invalid_response_format'
    text=text.strip()
    if '```' in text:
        m=re.fullmatch(r'```([^\n`]*)\n([\s\S]*?)\n```',text)
        if not m or '```' in m[2]: return None,'invalid_response_format'
        label=m[1].strip().lower()
        allowed={'','c'} if form=='C' else {'','llvm','llvm ir','llvm_ir','ir'}
        if label not in allowed: return None,'invalid_response_format'
        text=m[2].strip()
    if not text: return None,'empty_output'
    return text+'\n',None

def classify(text,final,form,native_count):
    if final.get('truncated') is not False: return None,'native_context_truncation_or_unknown'
    if final.get('tokens_evaluated')!=native_count: return None,'native_input_token_count_mismatch'
    if final.get('stop_type') not in ('eos','word'): return None,'output_cap_or_abnormal_stop'
    n=final.get('tokens_predicted',final.get('timings',{}).get('predicted_n'))
    if type(n) is not int or not 0<n<=CAPS[form]+4: return None,'output_count_invalid'
    return normalize_code(text,form)

def stream_once(body,path):
    need(not path.exists(),'Generation already attempted; no overwrite')
    con=http.client.HTTPConnection('127.0.0.1',PORT,timeout=1800)
    start=time.monotonic(); count=0
    try:
        con.request('POST','/completion',body=canon(body),headers={'Content-Type':'application/json'})
        response=con.getresponse()
        need(response.status==200,'Native completion HTTP '+str(response.status))
        with path.open('xb') as f:
            while True:
                need(time.monotonic()-start<6*3600,'Per-request wall limit reached; attempt retained')
                line=response.readline(1024**2+1)
                if not line: break
                count+=len(line); need(len(line)<=1024**2 and count<=MAX_STREAM,'Oversize native stream')
                f.write(line)
            f.flush(); os.fsync(f.fileno())
    finally: con.close()
    return parse_sse(read(path,MAX_STREAM).splitlines())

def generate(rows,tokens,proc):
    results=[]
    for i,row in enumerate(rows,1):
        need(proc.poll() is None,'Inference server stopped unexpectedly')
        cid=row['id']; update(phase='GENERATING',current_id=cid,generation_terminal=i-1)
        raw=read(ROOT/'native-inputs'/(cid+'.json')); need(sha(raw)==tokens[cid]['sha256'],'Native input changed')
        native=parse(raw); error=None; code=None; fp=None
        if not native['context_budget_ok']:
            error='context_budget_exceeded_without_generation'
        else:
            body=completion_body(native['tokens'],row['form'])
            dest=ROOT/'generation'/cid; dest.mkdir(parents=True,exist_ok=False)
            jw(dest/'request.json',body)
            jw(dest/'intent.json',dict(id=cid,attempt=1,utc=now(),request_sha256=sha(canon(body))))
            text,final=stream_once(body,dest/'response.sse')
            save(dest/'response.txt',text.encode()); jw(dest/'terminal.json',final)
            code,error=classify(text,final,row['form'],len(native['tokens']))
            if error in ('native_input_token_count_mismatch','native_context_truncation_or_unknown'):
                jw(dest/'protocol-failure.json',dict(reason=error,id=cid))
                raise Blocked(error+'; native request retained, no retry')
        if code is not None:
            fp='candidates/'+cid+('.c' if row['form']=='C' else '.ll')
            save(ROOT/'evaluation'/fp,code.encode())
            os.chmod(ROOT/'evaluation'/fp,0o444)
        rr={**identity(cid),'cohort':COHORT,'prompt_condition_label':LABELS[row['condition']],
            'generation_status':'saved' if code is not None else 'invalid_generation',
            'generation_errors':[error] if error else [], 'provider_result_type':'native_llama_cpp',
            'source_path':fp,'source_sha256':sha(code.encode()) if code is not None else None,'old_native_object':None}
        jw(ROOT/'generation-records'/(cid+'.json'),rr); results.append(rr)
        print('GENERATION '+str(i)+'/900 '+cid+' '+rr['generation_status'],flush=True)
        update(generation_terminal=i,generation_saved=sum(x['generation_status']=='saved' for x in results))
    need(len(results)==TOTAL and {r['id'] for r in results}==grid(),'Generation slots incomplete')
    jw(ROOT/'generation-rows.json',results)
    return results

def replay_generation():
    rows=parse(read(ROOT/'generation-rows.json')); native={r['id']:r for r in parse(read(ROOT/'native-input-receipt.json'))['rows']}
    need(len(rows)==TOTAL and {r['id'] for r in rows}==grid(),'Generation ledger missing slots')
    for row in rows:
        cid=row['id']; ndraw=read(ROOT/'native-inputs'/(cid+'.json')); need(sha(ndraw)==native[cid]['sha256'],'Native input changed')
        nd=parse(ndraw)
        if nd['context_budget_ok']:
            dest=ROOT/'generation'/cid
            need(parse(read(dest/'request.json'))==completion_body(nd['tokens'],row['form']),'Generation request changed')
            text,final=parse_sse(read(dest/'response.sse',MAX_STREAM).splitlines())
            code,error=classify(text,final,row['form'],len(nd['tokens']))
            need(read(dest/'response.txt')==text.encode() and parse(read(dest/'terminal.json'))==final,'Response snapshot differs')
        else: code,error=None,'context_budget_exceeded_without_generation'
        need(row['generation_status']==('saved' if code is not None else 'invalid_generation'),'Generation classification differs')
        need(row['generation_errors']==([error] if error else []),'Generation error classification differs')
        if code is not None: need(read(ROOT/'evaluation'/rel(row['source_path']))==code.encode() and row['source_sha256']==sha(code.encode()),'Candidate source differs')
        need(parse(read(ROOT/'generation-records'/(cid+'.json')))==row,'Generation ledger differs')
    return rows

def assert_inference_stopped():
    receipt=parse(read(ROOT/'control/inference-stopped.json'))
    need(receipt['stopped'] is True,'Inference stop receipt missing')
    # In the private namespace no unrelated process should own the port.
    con=socket.socket(); con.settimeout(1)
    try: need(con.connect_ex(('127.0.0.1',PORT))!=0,'Inference port is still listening')
    finally: con.close()


def run_evaluation(core,c,e,f,m,rows):
    assert_inference_stopped(); verify_inputs(); evalroot=ROOT/'evaluation'
    table=parse(read(ROOT/'inputs/snapshot-manifest.json'))
    for n in table:
        if n.startswith(('references/','package/','policy/')):
            save(evalroot/n,read(ROOT/'inputs'/n)); os.chmod(evalroot/n,0o444)
    eval_manifest={p.relative_to(evalroot).as_posix():hfile(p) for p in evalroot.rglob('*') if p.is_file()}
    jw(ROOT/'control/evaluation-inputs.json',eval_manifest)
    def verify_evaluation():
        for n,d in eval_manifest.items(): need(hfile(evalroot/rel(n))==d,'Evaluation input changed: '+n)
    verify_evaluation()
    boot=parse(read(ROOT/'control/start.json'))['boot_id']
    def check():
        need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'Host rebooted')
        c.controls()
    check(); c.host_check(check_processes=False); e.no_other_jobs()
    v=c.import_validator(evalroot/'policy/validator-v1_2.py'); clang,banner=c.compiler(v)
    need(hfile(Path(clang).resolve())==CLANG_SHA,'Compiler changed')
    prior=os.umask(0o022)
    try: vrecs=core.validation_loop(c,v,clang,rows,evalroot,ROOT/'validation',update,check)
    finally: os.umask(prior)
    verify_evaluation()
    vs=core.validation_summary(vrecs); jw(ROOT/'validation/result-index.json',vrecs); jw(ROOT/'validation/summary.json',vs)
    core.seal_phase(ROOT/'validation',core.VCOMPLETE)
    by={r['id']:r for r in vrecs}
    prows=[dict(r,correctness_passed=by[r['id']]['passed'],validation_status=by[r['id']]['status']) for r in rows]
    eligible=sum(r['correctness_passed'] for r in prows)
    update(phase='MEASURING',correctness_pass_eligible=eligible,measurement_pending=eligible)
    eng=m.pinned_engine(evalroot/'package'); tclang,tbanner=eng.clang_path()
    need(tbanner==banner and hfile(Path(tclang).resolve())==CLANG_SHA,'Timing compiler changed')
    box=None; prior=os.umask(0o022)
    try:
        if eligible:
            box=eng.Sandbox(ROOT/'performance/sandbox'); box.preflight()
        outcomes,bases=core.measurement_loop(m,eng,box,tclang,prows,evalroot,ROOT/'performance',update,check)
    finally:
        os.umask(prior)
        if box: box.close()
    verify_evaluation()
    pm=core.metric(outcomes); need(pm['measurement_terminal']==eligible and pm['measurement_pending']==0,'Pending measurement slots')
    ps=dict(pm,completion=core.PCOMPLETE,by_form_condition={fo:{a:core.metric([r for r in outcomes if r['form']==fo and r['condition']==a]) for a in ARMS} for fo in FORMS},
        baseline_policy=core.BASELINE,protocol=core.DEFAULTS,cpu=CPU,numa_node=NODE,
        timing_retries=0,historical_timing_used=False,compiler=banner,compiler_sha256=CLANG_SHA)
    save(ROOT/'performance/outcomes.jsonl',b''.join(canon(r) for r in outcomes)); jw(ROOT/'performance/summary.json',ps)
    core.seal_phase(ROOT/'performance',core.PCOMPLETE)
    update(phase='ANALYZING'); audit=core.audit_measured(m,f,eng,outcomes,ROOT/'performance')
    ar,tables=core.analysis_results(f,outcomes,parse(read(ROOT/'inputs/analysis-plan.json')))
    ar['measurement_audit']=audit; jw(ROOT/'analysis/summary.json',ar)
    save(ROOT/'analysis/outcomes.csv',core.table_csv(outcomes))
    for n,rs in tables.items(): save(ROOT/'analysis/tables'/rel(n+'.csv'),core.table_csv(rs))
    core.seal_phase(ROOT/'analysis',core.ACOMPLETE); check(); verify_inputs(); replay_generation()
    summary=dict(schema='open14b-900-generation-and-evaluation-v1',completion=COMPLETE,cohort=COHORT,model=MODEL,
        backend='llama.cpp '+LLAMA_TAG,backend_commit=LLAMA_COMMIT,requests_total=TOTAL,
        generation_status_counts=dict(Counter(r['generation_status'] for r in rows)),
        generation_calls=sum((ROOT/'generation'/r['id']/'intent.json').exists() for r in rows),
        validation=vs,performance=ps,primary_contrasts=ar['primary_contrasts'],
        formal_equivalence_proven=False,old_results_modified=False,old_timing_reused=False,
        automatic_generation_retries=0,timing_retries=0,cloud_inference_calls=0,
        previous_qwen3next_campaign_completed_by_this_run=False,condition_labels=ARMS,
        local_copy_verified=False,completed_utc=now(),out=str(ROOT))
    jw(ROOT/'summary.json',summary)
    update(phase='ARCHIVING'); arch,sealdigest,n=core.archive_all(ROOT,update)
    receipt=dict(completion=COMPLETE,model=MODEL,summary_sha256=hfile(ROOT/'summary.json'),seal_sha256=sealdigest,
                 sealed_files=n,archive=arch,completed_utc=now())
    jw(ROOT/'completion-receipt.json',receipt); update(phase='COMPLETE',pipeline_complete=True,current_id=None,archive=arch)
    print(COMPLETE,flush=True)
    print(json.dumps({'generation':summary['generation_status_counts'],'validation_passed':vs['passed'],
                      'measurement_valid':pm['measurement_valid'],'archive':arch},indent=2),flush=True)


def numeric_preflight(core,c,m):
    """Exercise the real C/IR handoff BEFORE generation, using reference sources.

    These two reference-only checks are not LLM candidates, are stored separately,
    and their timing samples are never imported into the 900-slot experiment.
    A noisy identity timing is recorded, not used for performance conclusions.
    """
    out=ROOT/'preflight/identity-pipeline'; inp=out/'inputs'
    table=parse(read(ROOT/'inputs/snapshot-manifest.json'))
    for n in table:
        if n.startswith(('references/','package/','policy/')):
            save(inp/n,read(ROOT/'inputs'/n)); os.chmod(inp/n,0o444)
    rows=[]
    for form,ext in (('C','c'),('IR','ll')):
        cid='q27__gemm__MINI__'+form+'__P0__s0'
        path='references/gemm/MINI/kernel.'+ext
        rows.append(dict(identity(cid),cohort=COHORT,prompt_condition_label='P0',
             generation_status='saved',generation_errors=[],provider_result_type='UNCHANGED_REFERENCE_PREFLIGHT',
             source_path=path,source_sha256=hfile(inp/path),old_native_object=None))
    def check(): c.controls()
    def progress(**kw):
        kw['preflight_only']=True
        update(**kw)
    old=(core.TOTAL,core.KERNELS,core.SIZES)
    prior=os.umask(0o022); box=None
    try:
        core.TOTAL=2; core.KERNELS=('gemm',); core.SIZES=('MINI',)
        v=c.import_validator(inp/'policy/validator-v1_2.py'); clang,banner=c.compiler(v)
        records=core.validation_loop(c,v,clang,rows,inp,out/'validation',progress,check)
        need(len(records)==2 and all(r['passed'] is True for r in records),
             'Unchanged C/IR finite-validation preflight failed; no generation started')
        prows=[dict(row,correctness_passed=True,validation_status=r['status']) for row,r in zip(rows,records)]
        eng=m.pinned_engine(inp/'package'); tc,tbanner=eng.clang_path()
        need(tbanner==banner and hfile(Path(tc).resolve())==CLANG_SHA,'Preflight compiler changed')
        box=eng.Sandbox(out/'performance/sandbox'); box.preflight()
        outcomes,_=core.measurement_loop(m,eng,box,tc,prows,inp,out/'performance',progress,check)
        need(len(outcomes)==2 and all(r.get('native_stock_check_passed') is True for r in outcomes),
             'Unchanged C/IR stock-output preflight failed; no generation started')
        need(all(r.get('stage') in ('measurement_valid','timing_quality_failed') for r in outcomes),
             'Unchanged C/IR timing did not execute successfully; no generation started')
        jw(out/'receipt.json',dict(reference_only=True,LLM_calls=0,
            fullstate_passed=2,stock_passed=2,measurement_outcomes=outcomes,
            scientific_samples_reused=False,utc=now()))
    finally:
        if box: box.close()
        os.umask(prior)
        core.TOTAL,core.KERNELS,core.SIZES=old
    update(phase='REFERENCE_HANDOFF_PREFLIGHT_PASSED',preflight_only=False,
           validation_slots_terminal=0,measurement_terminal=0,measurement_pending=None)
    print('UNCHANGED_C_AND_IR_HANDOFF_PASSED; no LLM candidate yet',flush=True)


def offline_run():
    cgroup_guard(private=True)
    ip=shutil.which('ip'); need(ip is not None,'iproute2 ip missing')
    command([ip,'link','set','lo','up'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=20)
    proc=None
    with locks():
        verify_inputs(); core,c,e,f,m=modules(); e.no_other_jobs(); c.host_check(check_processes=False)
        numeric_preflight(core,c,m)
        update(phase='LOADING_MODEL'); rec=verify_assets()
        try:
            proc=start_llama(rec)
            update(phase='NATIVE_TOKEN_AUDIT'); rows,tokens=native_inputs()
            update(phase='GENERATING'); generate(rows,tokens,proc)
        finally:
            stop_llama(proc)
        jw(ROOT/'control/inference-stopped.json',dict(stopped=True,utc=now(),generation_measurement_overlap=False))
        update(phase='INFERENCE_STOPPED_COOLDOWN')
        time.sleep(30)
        assert_inference_stopped()
        rows=replay_generation(); run_evaluation(core,c,e,f,m,rows)


def coordinator():
    cgroup_guard()
    try:
        update(phase='PREPARING_INPUTS')
        with locks():
            need(shutil.disk_usage('/root').free>=40*GIB,'Need at least 40GiB free before acquisition')
            need(meminfo()['MemTotal']>=28*GIB,'Host memory below expected 32GB class')
            prepare_inputs(); core,c,e,f,m=modules()
            c.host_check(check_processes=False); e.no_other_jobs()
            need(shutil.which('setpriv') and shutil.which('unshare') and shutil.which('ip'),'Required namespace tools missing; no apt upgrade attempted')
            v=c.import_validator(ROOT/'inputs/policy/validator-v1_2.py'); c.compiler(v)
            update(phase='DOWNLOADING_PUBLIC_MODEL_AND_RUNTIME'); acquire_assets()
        # Execute the rest in a new network namespace. No external API can be
        # reached there, and the model is killed before any candidate execution.
        argv=['/usr/bin/unshare','--net','--','/usr/bin/python3','-I','-S','-B','-u',str(ROOT/'control/runner.py'),'--_offline']
        env=controls_env(); env['CPUCOND_BATCH_UNIT']=UNIT
        os.execve(argv[0],argv,env)
    except BaseException:
        raise


def start_remote():
    host_basic(); os.umask(0o077)
    with locks():
        if ROOT.exists():
            print(json.dumps(status_remote(),indent=2),flush=True)
            need((ROOT/'completion-receipt.json').exists() or unit_state().get('ActiveState') in ('active','activating'),
                 'Existing partial campaign retained; use --status. No automatic generation or measurement retry.')
            return
        ROOT.mkdir(mode=0o700)
        raw=read(__file__); save(ROOT/'control/runner.py',raw)
        start=dict(version=VERSION,model=MODEL,cohort=COHORT,runner_sha256=sha(raw),
                   boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),utc=now())
        jw(ROOT/'control/start.json',start)
        cmd=['systemd-run','--unit='+UNIT,'--property=Type=exec','--property=Restart=no',
             '--property=MemoryMax=24G','--property=MemorySwapMax=0','--property=TasksMax=256',
             '--property=RuntimeMaxSec=7d','--property=TimeoutStopSec=60','--property=KillMode=control-group',
             '--property=UMask=0077','--property=LimitCORE=0',
             '--property=UnsetEnvironment=ANTHROPIC_API_KEY OPENAI_API_KEY CLAUDE_API_KEY HF_TOKEN HUGGING_FACE_HUB_TOKEN',
             '--property=StandardOutput=append:'+str(ROOT/'run.log'),
             '--property=StandardError=append:'+str(ROOT/'run.log'),
             '--setenv=CPUCOND_BATCH_UNIT='+UNIT,'--setenv=PYTHONDONTWRITEBYTECODE=1','--working-directory=/root','--',
             '/usr/bin/python3','-I','-S','-B','-u',str(ROOT/'control/runner.py'),'--_coordinator']
        jw(ROOT/'control/launch.json',dict(argv=cmd,unit=UNIT,utc=now()))
    cp=subprocess.run(cmd,capture_output=True,text=True,timeout=60,env=controls_env())
    atomic(ROOT/'control/launch-submission.json',dict(returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,utc=now()))
    need(cp.returncode==0,'Systemd start not confirmed; no resubmission')
    print('OPEN14B_PIPELINE_STARTED; new model, generation -> validation -> timing -> archive',flush=True)


def status_remote():
    host_basic()
    if not ROOT.exists(): return {'state':'NOT_STARTED','model':MODEL}
    out={'state':'RUNNING_OR_INCOMPLETE','model':MODEL,'systemd':unit_state()}
    for n in ('progress.json','failure.json'):
        if (ROOT/n).is_file(): out[n[:-5]]=parse(read(ROOT/n))
    p=ROOT/'completion-receipt.json'
    if p.is_file():
        r=parse(read(p)); need(r['completion']==COMPLETE and r['model']==MODEL,'Unexpected completion receipt')
        need(hfile(ROOT/'summary.json')==r['summary_sha256'] and hfile(ROOT/'SHA256SUMS')==r['seal_sha256'],'Final metadata changed')
        need(r['archive']['path']==str(ROOT)+'.tar.gz','Archive path differs')
        out.update(state='COMPLETE',receipt=r)
    if out.get('failure'):
        out['state']='BLOCKED'
    elif out['state']!='COMPLETE' and out['systemd'].get('ActiveState') not in ('active','activating'):
        out['state']='STOPPED_OR_BLOCKED'
    if out['state'] in ('BLOCKED','STOPPED_OR_BLOCKED'):
        for name in ('run.log','llama-server.log'):
            p=ROOT/name
            if p.is_file():
                with regular(p) as fp:
                    fp.seek(0,2); fp.seek(max(0,fp.tell()-5000))
                    out[name+'_tail']=fp.read().decode('utf-8',errors='replace')
    return out


def verify_archive(path,expected_hash,expected_size):
    need(path.stat().st_size==expected_size and hfile(path)==expected_hash,'Local archive hash/size mismatch')
    entries={}; manifest=None
    with tarfile.open(path,'r:gz') as tf:
        for t in tf:
            n=rel(t.name); need(t.isfile() and not t.islnk() and n not in entries,'Unsafe/duplicate archive member')
            src=tf.extractfile(t); need(src is not None,'Missing archive member payload')
            h=hashlib.sha256(); count=0; pieces=[]
            for b in iter(lambda:src.read(1024**2),b''):
                h.update(b); count+=len(b)
                if n=='SHA256SUMS':
                    need(count<=MAX_META,'Oversize archive manifest'); pieces.append(b)
            need(count==t.size,'Truncated archive member')
            entries[n]=h.hexdigest()
            if n=='SHA256SUMS': manifest=b''.join(pieces)
    need(manifest is not None,'Archive seal absent')
    table={}
    for line in manifest.decode().splitlines():
        pin,sep,n=line.partition('  '); need(sep and HEX.fullmatch(pin) and n not in table,'Invalid archive seal'); rel(n); table[n]=pin
    need(set(entries)==set(table)|{'SHA256SUMS'},'Archive content set mismatch')
    need(all(entries[n]==pin for n,pin in table.items()),'Archive member hash mismatch')
    # Read gzip through EOF too, so truncated trailers are not ignored by tar.
    with gzip.open(path,'rb') as f:
        for _ in iter(lambda:f.read(4*1024**2),b''): pass
    return dict(archive_sha256=expected_hash,bytes=expected_size,members_verified=len(entries))


class SSH:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cpucond27-ssh-')
        self.sock=str(Path(self.tmp.name)/'c')
        key=Path.home()/'.ssh/id_ed25519'; need(key.is_file(),'SSH key missing: '+str(key))
        self.opts=['-T','-i',str(key),'-o','StrictHostKeyChecking=yes','-o','IdentitiesOnly=yes',
            '-o','PreferredAuthentications=publickey','-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no',
            '-o','ForwardAgent=no','-o','ConnectTimeout=30','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=4',
            '-o','ControlMaster=auto','-o','ControlPath='+self.sock,'-o','ControlPersist=600']
        self.script=None
    def exec(self,argv,input=None,capture=False):
        return subprocess.run(['ssh',*self.opts,SERVER,shlex.join(argv)],input=input,
             stdout=subprocess.PIPE if capture else None,check=True)
    def upload(self):
        raw=read(__file__); digest=sha(raw); self.script='/srv/research/cpucond-open14b-entry-'+digest[:16]+'.py'
        code="""import os,sys,hashlib,socket
from pathlib import Path
assert os.geteuid()==0 and socket.gethostname().split('.')[0]=='cpucond-skylake-01'
p=Path(sys.argv[1]); h=sys.argv[2]; b=sys.stdin.buffer.read(1024*1024)
assert hashlib.sha256(b).hexdigest()==h and not p.is_symlink()
os.umask(0o077)
if p.exists(): assert p.read_bytes()==b
else:
 with p.open('xb') as f: f.write(b);f.flush();os.fsync(f.fileno())
"""
        self.exec(['/usr/bin/python3','-I','-S','-B','-c',code,self.script,digest],input=raw)
    def run(self,flag,capture=False):
        need(self.script is not None,'SSH script not installed')
        return self.exec(['/usr/bin/python3','-I','-S','-B','-u',self.script,flag],capture=capture)
    def status(self):
        return parse(self.run('--_status',capture=True).stdout)
    def close(self):
        subprocess.run(['ssh','-S',self.sock,'-O','exit',SERVER],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.tmp.cleanup()


def collect(conn,doc=None):
    doc=doc or conn.status(); need(doc['state']=='COMPLETE','Server pipeline is not complete; no successful backup is claimed')
    r=doc['receipt']; ar=r['archive']; need(ar['path']==str(ROOT)+'.tar.gz' and HEX.fullmatch(ar['sha256']),'Invalid archive receipt')
    dest=Path.home()/'workspace/cpu-conditioned-llm-optimization/runs/open14b-skylake-five-arm-v2'
    checked(dest); dest.mkdir(parents=True,exist_ok=True)
    file=dest/(ROOT.name+'.tar.gz'); part=file.with_name(file.name+'.partial')
    jwpath=dest/'server-completion-receipt.json'
    if jwpath.exists(): need(parse(read(jwpath))==r,'Saved server receipt differs')
    else: jw(jwpath,r)
    if not file.exists():
        need(shutil.disk_usage(dest).free>=ar['bytes']+GIB,'Insufficient local disk')
        # scp only touches this script-owned partial, never a verified final copy.
        opts=[x for x in conn.opts if x!='-T']
        subprocess.run(['scp',*opts,SERVER+':'+ar['path'],str(part)],check=True)
        verification=verify_archive(part,ar['sha256'],ar['bytes']); os.rename(part,file)
    else: verification=verify_archive(file,ar['sha256'],ar['bytes'])
    rec=dict(schema='open14b-local-copy-receipt-v1',local_path=str(file),server_receipt_sha256=sha(canon(r)),
             **verification,local_copy_verified=True,utc=now())
    atomic(dest/'local-copy-receipt.json',rec)
    print('OPEN14B_LOCAL_COPY_VERIFIED',flush=True); print(json.dumps(rec,indent=2),flush=True)


def local(mode):
    need(socket.gethostname().split('.')[0]!=HOST,'Run user-facing modes in local WSL, not the server')
    conn=SSH()
    try:
        conn.upload()
        if mode=='run':
            print('NEW_MODEL='+MODEL+'; NOT a Stage26/Qwen3-Coder-Next continuation.',flush=True)
            conn.run('--_start')
        if mode=='stop':
            conn.exec(['/usr/bin/systemctl','stop',UNIT])
            print('OWNED_OPEN14B_JOB_STOPPED; evidence preserved; server rental not terminated')
            return
        if mode=='status':
            print(json.dumps(conn.status(),indent=2,ensure_ascii=False)); return
        if mode=='collect': collect(conn); return
        last=None
        while True:
            doc=conn.status(); p=doc.get('progress',{})
            line=json.dumps({'state':doc['state'],'phase':p.get('phase'),'generation_terminal':p.get('generation_terminal'),
                'validation_slots_terminal':p.get('validation_slots_terminal'),'measurement_terminal':p.get('measurement_terminal'),
                'measurement_pending':p.get('measurement_pending'),'current_id':p.get('current_id')},ensure_ascii=False)
            if line!=last: print(line,flush=True); last=line
            if doc['state']=='COMPLETE': collect(conn,doc); return
            if doc['state'] in ('BLOCKED','STOPPED_OR_BLOCKED','NOT_STARTED'):
                print(json.dumps(doc,indent=2,ensure_ascii=False)); raise Blocked('Remote job not running. Evidence retained; no automatic retry.')
            time.sleep(30)
    except KeyboardInterrupt:
        print('\nLocal watch stopped. The independent systemd job is not killed. Reattach with --watch.',flush=True)
    finally: conn.close()


def self_test():
    class Tests(unittest.TestCase):
        def test_full_grid(self): self.assertEqual(len(grid()),900)
        def test_90_per_form_arm(self):
            counts=Counter((identity(x)['form'],identity(x)['condition']) for x in grid())
            self.assertEqual(len(counts),10); self.assertEqual(set(counts.values()),{90})
        def test_old_namespace_refused(self):
            for p in ('g25__','q26__','wc24__'):
                self.assertRaises(Blocked,identity,p+'gemm__MINI__C__P0__s0')
        def test_new_namespace(self): self.assertEqual(identity('q27__gemm__MINI__IR__W2__s0')['form'],'IR')
        def test_not_same_model(self): self.assertNotEqual(MODEL,'qwen3-coder-next:q8_0')
        def test_three_sizes(self): self.assertEqual(SIZES,('MINI','SMALL','MEDIUM'))
        def test_json_duplicate(self): self.assertRaises(Blocked,parse,b'{"a":1,"a":2}')
        def test_json_nan(self): self.assertRaises(Blocked,parse,b'{"a":NaN}')
        def test_json_inf(self): self.assertRaises(Blocked,parse,b'{"a":1e999}')
        def test_paths(self):
            for p in ('../x','/x','x/../y','x\\y','x\n','./x',''):
                self.assertRaises(Blocked,rel,p)
        def test_symlink(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t); save(p/'x',b'x'); (p/'y').symlink_to(p/'x'); self.assertRaises(Blocked,read,p/'y')
        def test_no_overwrite(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x'; save(p,b'x'); self.assertRaises(FileExistsError,save,p,b'y'); self.assertEqual(read(p),b'x')
        def test_budget(self): self.assertTrue(token_budget(15000,'IR'))
        def test_budget_no_truncation(self): self.assertFalse(token_budget(17000,'IR'))
        def test_budget_exact_boundary(self):
            self.assertTrue(token_budget(CTX-CAPS['IR']-RESERVE,'IR'))
            self.assertFalse(token_budget(CTX-CAPS['IR']-RESERVE+1,'IR'))
        def test_token_ids_direct(self):
            b=completion_body([1,2,3],'C'); self.assertEqual(b['prompt'],[1,2,3]); self.assertFalse(b['cache_prompt'])
        def test_caps(self): self.assertEqual(completion_body([1],'IR')['n_predict'],16384)
        def test_samplers(self): self.assertEqual(completion_body([1],'C')['temperature'],0.2)
        def test_no_cloud_credentials(self): self.assertFalse(any('KEY' in k or 'TOKEN' in k for k in controls_env()))
        def test_code_plain(self): self.assertEqual(normalize_code(' void x(){} ','C'),('void x(){}\n',None))
        def test_code_outer_fence(self): self.assertEqual(normalize_code('```llvm\ndefine void @x(){ ret void }\n```','IR')[1],None)
        def test_code_bad_fence(self): self.assertIsNone(normalize_code('text\n```c\nx\n```','C')[0])
        def test_code_multi_fence(self): self.assertIsNone(normalize_code('```c\nx\n```\n```c\ny\n```','C')[0])
        def test_wrong_language(self): self.assertIsNone(normalize_code('```python\nx\n```','C')[0])
        def test_empty(self): self.assertIsNone(normalize_code('','IR')[0])
        def test_no_thinking(self): self.assertIsNone(normalize_code('<think>x</think>void f(){}','C')[0])
        def test_sse_replay(self):
            ls=[b': ping',b'data: {"content":"void ","stop":false}',b'data: {"content":"x(){}","stop":true}',b'data: [DONE]']
            self.assertEqual(parse_sse(ls)[0],'void x(){}')
        def test_sse_missing_terminal(self): self.assertRaises(Blocked,parse_sse,[b'data: {"content":"x","stop":false}'])
        def test_sse_two_terminals(self): self.assertRaises(Blocked,parse_sse,[b'data: {"stop":true}',b'data: {"stop":true}'])
        def test_sse_error(self): self.assertRaises(Blocked,parse_sse,[b'data: {"error":"x"}'])
        def terminal(self,**kw): return dict(dict(truncated=False,tokens_evaluated=12,tokens_predicted=7,stop_type='eos'),**kw)
        def test_classification_ok(self): self.assertIsNotNone(classify('void f(){}',self.terminal(),'C',12)[0])
        def test_truncation(self): self.assertIsNone(classify('void f(){}',self.terminal(truncated=True),'C',12)[0])
        def test_wrong_tokens(self): self.assertEqual(classify('void f(){}',self.terminal(),'C',13)[1],'native_input_token_count_mismatch')
        def test_limit(self): self.assertIsNone(classify('void f(){}',self.terminal(stop_type='limit'),'C',12)[0])
        def test_cpu_only(self):
            a=llama_command({'binary':'/x/llama-server','model_file':'/x/model.gguf'})
            self.assertEqual(a[a.index('--n-gpu-layers')+1],'0'); self.assertEqual(a[a.index('--threads')+1],'4')
        def test_unprivileged_inference(self): self.assertIn('--reuid=65534',llama_command({'binary':'x','model_file':'y'}))
        def test_single_slot(self): self.assertIn('--no-context-shift',llama_command({'binary':'x','model_file':'y'}))
        def test_cached_asset_hash(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x'; save(p,b'x'); download('https://example.invalid/x',p,sha(b'x'),1)
                self.assertRaises(Blocked,download,'https://example.invalid/x',p,sha(b'y'),1)
        def make_archive(self,p,files):
            with tarfile.open(p,'w:gz') as tf:
                for n,b in files.items():
                    ti=tarfile.TarInfo(n); ti.size=len(b); tf.addfile(ti,io.BytesIO(b))
        def test_archive_roundtrip(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x.tar.gz'; self.make_archive(p,{'x':b'hello','SHA256SUMS':(sha(b'hello')+'  x\n').encode()})
                self.assertEqual(verify_archive(p,hfile(p),p.stat().st_size)['members_verified'],2)
        def test_archive_bad_pin(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x.tar.gz'; self.make_archive(p,{'x':b'hello','SHA256SUMS':(sha(b'wrong')+'  x\n').encode()})
                self.assertRaises(Blocked,verify_archive,p,hfile(p),p.stat().st_size)
        def test_archive_missing_entry(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x.tar.gz'; self.make_archive(p,{'SHA256SUMS':(sha(b'hello')+'  absent\n').encode()})
                self.assertRaises(Blocked,verify_archive,p,hfile(p),p.stat().st_size)
        def test_archive_path_attack(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t)/'x.tar.gz'; self.make_archive(p,{'../bad':b'x'})
                self.assertRaises(Blocked,verify_archive,p,hfile(p),p.stat().st_size)
        def test_existing_experiments_not_destinations(self):
            self.assertNotEqual(ROOT,OLD); self.assertNotIn('stage26',str(ROOT)); self.assertNotIn('stage26',str(ASSETS))
        def test_numeric_sandbox_unit_contract(self):
            self.assertIsNotNone(re.fullmatch(r'cpucond69-[A-Za-z0-9-]+\.service',UNIT))
        def test_v2_result_namespace(self):
            self.assertTrue(str(ROOT).endswith('-v2'))
            self.assertIn('open14b-skylake-five-arm-v2',str(Path.home()/'workspace/cpu-conditioned-llm-optimization/runs/open14b-skylake-five-arm-v2'))
        def test_output_caps_total(self): self.assertEqual(sum(CAPS[identity(x)['form']] for x in grid()),9216000)
        def test_no_external_native_endpoint(self): self.assertRaises(Blocked,loopback,'https://example.com')
        def test_runtime_archive_pin_is_full(self):
            self.assertTrue(HEX.fullmatch(LLAMA_ARCHIVE_SHA))
            self.assertEqual(LLAMA_ARCHIVE_BYTES,16825086)
        def test_runtime_directory_umask(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t); archive=p/'cpu.tar.gz'
                with tarfile.open(archive,'w:gz') as tf:
                    ti=tarfile.TarInfo('build/bin/llama-server'); ti.size=1; ti.mode=0o755
                    tf.addfile(ti,io.BytesIO(b'x'))
                old=os.umask(0o077)
                try: binary=extract_runtime(archive,p/'runtime')
                finally: os.umask(old)
                self.assertEqual((p/'runtime').stat().st_mode&0o777,0o755)
                self.assertEqual(binary.parent.stat().st_mode&0o777,0o755)
                self.assertTrue(binary.stat().st_mode&0o001)
        def test_runtime_symlink_escape(self):
            with tempfile.TemporaryDirectory() as t:
                p=Path(t); ar=p/'x.tgz'
                with tarfile.open(ar,'w:gz') as tf:
                    ti=tarfile.TarInfo('bad'); ti.type=tarfile.SYMTYPE; ti.linkname='../../bad'
                    tf.addfile(ti)
                with self.assertRaises((Blocked,tarfile.FilterError)):
                    extract_runtime(ar,p/'runtime')
        def test_disable_backend_auto_fit_and_gpu(self):
            cmd=llama_command({'binary':'/x','model_file':'/y'})
            self.assertEqual(cmd[cmd.index('--fit')+1],'off')
            self.assertEqual(cmd[cmd.index('--device')+1],'none')
            self.assertIn('--offline',cmd)
        def test_generation_failure_preserves_attempt(self):
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t)):
                cid='q27__gemm__MINI__C__P0__s0'
                nd=dict(tokens=[1,2],context_budget_ok=True)
                jw(ROOT/'native-inputs'/(cid+'.json'),nd)
                row=dict(identity(cid))
                proc=types.SimpleNamespace(poll=lambda:None)
                with patch.dict(globals(),stream_once=lambda *a: (_ for _ in ()).throw(Blocked('synthetic disconnect'))):
                    with self.assertRaises(Blocked):
                        generate([row],{cid:{'sha256':hfile(ROOT/'native-inputs'/(cid+'.json'))}},proc)
                self.assertTrue((ROOT/'generation'/cid/'intent.json').exists())
                with self.assertRaises(FileExistsError):
                    generate([row],{cid:{'sha256':hfile(ROOT/'native-inputs'/(cid+'.json'))}},proc)
        def test_full_900_native_generate_replay(self):
            # Fake API responses only. No weights, network, compiler or CPU timings
            # are used. Real filesystem writes, token budget, ledgers and replay.
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t)):
                rows=[]
                for cid in sorted(grid()):
                    r=dict(identity(cid)); body={'messages':[{'role':'system','content':SYSTEM},
                        {'role':'user','content':'EXPERIMENT '+cid}], 'form':r['form']}
                    path='requests/'+cid+'.json'; jw(ROOT/'inputs'/path,body)
                    r.update(request=path,request_sha256=hfile(ROOT/'inputs'/path))
                    rows.append(r)
                jw(ROOT/'inputs/rows.json',rows)
                def api(path,payload):
                    if path=='/apply-template':
                        return {'prompt':''.join('<|im_start|>'+m['role']+'\n'+m['content']+'<|im_end|>\n' for m in payload['messages'])+'<|im_start|>assistant\n'}
                    if path=='/tokenize': return {'tokens':[1,2,3,4]}
                    raise AssertionError(path)
                calls=[]
                def stream(body,path):
                    calls.append(body)
                    code='void kernel_test(){}' if body['n_predict']==CAPS['C'] else 'define void @kernel_test() { ret void }'
                    final=dict(content='',stop=True,truncated=False,tokens_evaluated=4,tokens_predicted=10,stop_type='eos')
                    data=b'data: '+canon(dict(content=code,stop=False))+b'\ndata: '+canon(final)+b'\n'
                    save(path,data)
                    return parse_sse(data.splitlines())
                with patch.dict(globals(),loopback=api,stream_once=stream):
                    rr,nd=native_inputs()
                    generated=generate(rr,nd,types.SimpleNamespace(poll=lambda:None))
                    self.assertEqual(len(calls),900)
                    self.assertEqual(replay_generation(),generated)
                    self.assertEqual(len(generated),900)
                    self.assertEqual({r['id'] for r in generated},grid())
                    for r in generated:
                        self.assertEqual((ROOT/'evaluation'/r['source_path']).stat().st_mode&0o777,0o444)
                    bad=ROOT/'evaluation'/generated[0]['source_path']
                    bad.chmod(0o600); bad.write_text('tampered')
                    self.assertRaises(Blocked,replay_generation)
        def test_numeric_preflight_restores_core_on_error(self):
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t)):
                table={}
                for form,ext in (('C','c'),('IR','ll')):
                    n='references/gemm/MINI/kernel.'+ext; save(ROOT/'inputs'/n,b'x'); table[n]={}
                jw(ROOT/'inputs/snapshot-manifest.json',table)
                c=types.SimpleNamespace(import_validator=lambda *a:None,compiler=lambda *a:('/not-used','banner'),controls=lambda:None)
                core=types.SimpleNamespace(TOTAL=900,KERNELS=KERNELS,SIZES=SIZES,
                    validation_loop=lambda *a: (_ for _ in ()).throw(Blocked('synthetic preflight error')))
                with self.assertRaises(Blocked): numeric_preflight(core,c,None)
                self.assertEqual((core.TOTAL,core.KERNELS,core.SIZES),(900,KERNELS,SIZES))
        def test_generation_stopped_before_evaluation(self):
            events=[]
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t)):
                rec={'x':1}; c=types.SimpleNamespace(host_check=lambda **k:None)
                e=types.SimpleNamespace(no_other_jobs=lambda:None)
                @contextlib.contextmanager
                def lk(): yield
                proc=types.SimpleNamespace(poll=lambda:None)
                def gen(*a): events.append('generate')
                def stop(*a): events.append('stop')
                def ev(*a): events.append('evaluate')
                with contextlib.ExitStack() as es:
                    es.enter_context(patch.dict(globals(),cgroup_guard=lambda **k:None,command=lambda *a,**k:None,
                        locks=lk,verify_inputs=lambda:None,modules=lambda:(None,c,e,None,None),
                        numeric_preflight=lambda *a:events.append('preflight'), verify_assets=lambda:rec,
                        start_llama=lambda *a:proc,native_inputs=lambda:([],{}),generate=gen,
                        stop_llama=stop,assert_inference_stopped=lambda:None,replay_generation=lambda:[],run_evaluation=ev))
                    es.enter_context(patch.object(time,'sleep',lambda *a:None))
                    es.enter_context(patch.object(shutil,'which',lambda *a:'/not-executed/ip'))
                    offline_run()
                self.assertEqual(events,['preflight','generate','stop','evaluate'])
                self.assertTrue(parse(read(ROOT/'control/inference-stopped.json'))['stopped'])
        def test_generation_exception_does_not_start_measurement(self):
            events=[]
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t)):
                c=types.SimpleNamespace(host_check=lambda **k:None); e=types.SimpleNamespace(no_other_jobs=lambda:None)
                @contextlib.contextmanager
                def lk(): yield
                with contextlib.ExitStack() as es:
                    es.enter_context(patch.dict(globals(),cgroup_guard=lambda **k:None,command=lambda *a,**k:None,
                        locks=lk,verify_inputs=lambda:None,modules=lambda:(None,c,e,None,None),
                        numeric_preflight=lambda *a:None,verify_assets=lambda:{},start_llama=lambda *a:object(),
                        native_inputs=lambda:([],{}),generate=lambda *a: (_ for _ in ()).throw(Blocked('disconnect')),
                        stop_llama=lambda *a:events.append('stop'),run_evaluation=lambda *a:events.append('evaluate')))
                    es.enter_context(patch.object(shutil,'which',lambda *a:'/not-executed/ip'))
                    with self.assertRaises(Blocked): offline_run()
                self.assertEqual(events,['stop'])
                self.assertFalse((ROOT/'completion-receipt.json').exists())
        def test_status_inactive_without_failure_is_not_running(self):
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t),
                    host_basic=lambda:None,unit_state=lambda:{'ActiveState':'inactive'}):
                self.assertEqual(status_remote()['state'],'STOPPED_OR_BLOCKED')
        def test_status_active(self):
            with tempfile.TemporaryDirectory() as t, patch.dict(globals(),ROOT=Path(t),
                    host_basic=lambda:None,unit_state=lambda:{'ActiveState':'active'}):
                self.assertEqual(status_remote()['state'],'RUNNING_OR_INCOMPLETE')
        def test_archive_no_result_claim_without_receipt(self):
            with self.assertRaises(Blocked): collect(None,{'state':'RUNNING'})

    with contextlib.redirect_stdout(io.StringIO()):
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    need(result.wasSuccessful(),'Self-tests failed'); print('OPEN14B_SELF_TEST=PASS tests='+str(result.testsRun))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for n in ('self-test','run','watch','status','collect','stop','_start','_status','_coordinator','_offline'):
        g.add_argument('--'+n,action='store_true',help=argparse.SUPPRESS if n.startswith('_') else None)
    a=p.parse_args(); sys.dont_write_bytecode=True
    if a.self_test: self_test(); return
    if a._start: start_remote(); return
    if a._status: print(json.dumps(status_remote())); return
    if a._coordinator or a._offline:
        os.umask(0o077)
        def stop(sig,frame): raise Blocked('Signal '+str(sig)+'; partial artifacts retained, no automatic retry')
        signal.signal(signal.SIGTERM,stop)
        try:
            need(hfile(ROOT/'control/runner.py')==parse(read(ROOT/'control/start.json'))['runner_sha256'],'Deployed runner changed')
            if a._coordinator: coordinator()
            else: offline_run()
        except BaseException as exc:
            atomic(ROOT/'failure.json',dict(error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc(),utc=now(),automatic_retry=False))
            update(phase='BLOCKED',error=str(exc)); raise
        return
    mode='run' if a.run else 'watch' if a.watch else 'status' if a.status else 'stop' if a.stop else 'collect'
    local(mode)

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: raise SystemExit(130)
    except Exception as exc:
        print('OPEN14B_BLOCKED: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        print('No existing experiment is overwritten; no automatic candidate retry.',file=sys.stderr)
        raise SystemExit(2)
