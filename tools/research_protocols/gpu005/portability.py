#!/usr/bin/env python3
"""GPU005: offline export of the recorded 85 CUDA candidates; A40/L4 evaluation.
No LLM/API call or server purchase. Existing experiment records are read-only.
Prepare locally first; --probe pins an explicitly configured SSH target;
--run executes fresh compilation/validation/controls/timing only after approval.
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
import argparse, ast, base64, contextlib, copy, csv, ctypes as ct, gzip, hashlib
import io, json, math, os, random, re, shlex, shutil, signal, stat, subprocess
import sys, tarfile, tempfile, textwrap, time, traceback, types, unittest
from pathlib import Path, PurePosixPath
from collections import Counter
from unittest import mock
CORE_SHA = '378dffe7c0d185974450c29ce7d73cdccb179502e36a3771e57ee76071b6054b'
CORE_EMBED = _public.encoded_module('numeric_core.py')
SOURCE_SHA = '54c87aa4795a520dc2601be7e13434abb1f415e23859f246ef8e6adccaac9778'
SOURCE_EMBED = _public.encoded_asset('source-bundle.json')
PRIMARY_SUMMARY_B64 = _public.encoded_asset('primary-summary.tar.gz')
PRIMARY_RECEIPT = {'bytes': 103651, 'files': 4, 'label': 'summary', 'manifest_sha256': '4b78ad68ad209bdd492ee905824c199430b757682fafb0b621e2deced29ad3a5', 'sha256': 'c236d106e37528f1316cd57685b4d8d3fce35862ebc445425d0560def3a8b0d6', 'utc': '2026-10-08T20:13:32.790856+00:00'}

ORIGINAL_NUMERIC_CORE_SHA = 'afe6858e7d510084a40e97aa81c14fa9da907fc80bc23f4a8b76f1eccf14e90a'
VERSION = 'gpu005-85-source-portability-v1'
PRIMARY_PLAN_SHA = '00e6369e8a52314e2b1cd4e322df75ee8ba1f78ed2098f4cf85f57d6f4de2960'
SOURCE_REL = Path('workspace/cpu-conditioned-llm-optimization/runs/gpu004-batch-budget-v1')
PREP_REL = Path('workspace/cpu-conditioned-llm-optimization/runs/gpu005-portability-prepared-v1')
ROOT = Path('/workspace/gpu005-portability-v1')
RUN_SECONDS, ACK_SECONDS = 24 * 3600, 12 * 3600
MIB = 1024**2
PROFILES = {'A40': {'name':'NVIDIA A40','cc':[8,6]}, 'L4': {'name':'NVIDIA L4','cc':[8,9]}}
A40_ENDPOINT = {'profile':'A40','host':'example.invalid','port':22065,'user':'root',
 'host_fingerprint':'SHA256:REPLACE_WITH_VERIFIED_HOST_KEY',
 'expected_gpu_uuid':'GPU-REPLACE-WITH-VERIFIED-UUID'}


def sha(b): return hashlib.sha256(b).hexdigest()
def need(ok, message):
    if not ok: raise RuntimeError(message)
def canon(obj): return (json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()
def parse(raw):
    def unique(items):
        result={}
        for k,v in items:
            need(k not in result,'Duplicate JSON key')
            result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda v: (_ for _ in ()).throw(RuntimeError('Nonfinite JSON')))
def safe(path):
    p=Path(path).absolute()
    need('..' not in p.parts,'Path traversal')
    for q in (p,*p.parents): need(not q.is_symlink(),'Symlink refused: '+str(q))
    return p
def read(path, cap=64*MIB):
    p=safe(path)
    with p.open('rb') as f:
        st=os.fstat(f.fileno());need(stat.S_ISREG(st.st_mode) and st.st_size<=cap,'Nonregular/oversized file: '+str(p))
        b=f.read(cap+1);en=os.fstat(f.fileno())
    need(len(b)==st.st_size and (st.st_ino,st.st_mtime_ns,st.st_size)==(en.st_ino,en.st_mtime_ns,en.st_size),'File changed while reading')
    return b
def hfile(path):
    p=safe(path);h=hashlib.sha256()
    with p.open('rb') as f:
        a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode),'Nonregular file')
        for b in iter(lambda:f.read(4*MIB),b''):h.update(b)
        z=os.fstat(f.fileno())
    need((a.st_ino,a.st_mtime_ns,a.st_size)==(z.st_ino,z.st_mtime_ns,z.st_size),'File changed while hashing')
    return h.hexdigest()
def save(path,b):
    p=safe(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def jw(path,obj):save(path,canon(obj))
def atomic(path,obj):
    p=safe(path);q=p.with_name(p.name+'.tmp-'+os.urandom(6).hex());save(q,canon(obj));os.replace(q,p)
def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def pathname(n):
    p=PurePosixPath(n)
    need(isinstance(n,str) and n and str(p)==n and not p.is_absolute() and '..' not in p.parts
         and '\\' not in n and '\x00' not in n,'Unsafe archive path')
    return p

def load_core():
    return _public.load_module('numeric_core.py', CORE_SHA)
C=load_core();P=C.P
FROZEN_NUMERIC=C.numeric
FROZEN_NUMERIC_JOB=C.numeric_job
FROZEN_OPTIONS=list(P.NVRTC_OPTIONS)
NUMERIC_NAMES=('definitions','dimensions','scalar_args','grids','paired','cpu_emulator_source',
               'compile_checked','validate_object','baseline_preflight','evaluate_group')


def read_archive(raw, receipt, cap=256*MIB):
    need(isinstance(receipt,dict),'Missing receipt')
    need(len(raw)==receipt.get('bytes') and sha(raw)==receipt.get('sha256'),'Archive hash/size differs')
    total=0
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
        while True:
            b=f.read(MIB)
            if not b:break
            total+=len(b);need(total<=cap,'Gzip expansion exceeds bound')
    files={};manifest=None;used=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
        for m in tf:
            pathname(m.name)
            need(m.isfile() and not m.issym() and not m.islnk() and m.size<=64*MIB,'Nonregular/oversized tar member')
            need(m.name not in files,'Duplicate tar member')
            used+=m.size;need(used<=cap and len(files)<20000,'Archive limits exceeded')
            b=tf.extractfile(m).read(m.size+1);need(len(b)==m.size,'Truncated tar member')
            files[m.name]=b
    mb=files.pop('CHECKPOINT_SHA256.json',None)
    need(mb is not None and sha(mb)==receipt.get('manifest_sha256'),'Manifest hash differs')
    manifest=parse(mb)
    need(manifest=={n:sha(b) for n,b in files.items()} and len(files)==receipt.get('files'),'Internal archive hashes differ')
    return files

def make_archive(files,label):
    need(files and 'CHECKPOINT_SHA256.json' not in files,'Invalid payload set')
    for n in files:pathname(n)
    mb=canon({n:sha(b) for n,b in files.items()});buf=io.BytesIO()
    with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0,compresslevel=6) as gz:
        with tarfile.open(fileobj=gz,mode='w') as tf:
            for n,b in sorted({**files,'CHECKPOINT_SHA256.json':mb}.items()):
                t=tarfile.TarInfo(n);t.size=len(b);t.mode=0o444;tf.addfile(t,io.BytesIO(b))
    raw=buf.getvalue();r={'bytes':len(raw),'files':len(files),'label':label,'sha256':sha(raw),'manifest_sha256':sha(mb),'utc':now()}
    read_archive(raw,r);return raw,r

def source_files():
    raw=gzip.decompress(base64.b64decode(SOURCE_EMBED,validate=True));need(sha(raw)==SOURCE_SHA,'Source bundle changed')
    obj=parse(raw);files={n:base64.b64decode(b,validate=True) for n,b in obj.items()}
    for n in files:pathname(n)
    for t in C.TASKS:
        b=files['upstream/'+C.SPECS[t]['path']]
        need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==C.SPECS[t]['blob'],'Upstream blob changed')
        adapted,_=C.extract_kernel(b,t)
        need(adapted.encode()==files['sources/'+t+'.cu'],'Adaptation changed')
    return files

# This is the ORIGINAL GPU004 parse contract, not a permissive repair.
def parse_candidate(text,task,original):
    P.require(isinstance(text,str) and 0<len(text.encode())<=65536,'Empty or oversized candidate')
    text=text.strip()
    if text.startswith('```'):
        m=re.fullmatch(r'```(?:cuda|cpp|c\+\+|c)?\s*\n(.*?)\n```',text,re.S|re.I)
        P.require(m is not None and '```' not in m[1],'Invalid outer fence');text=m[1].strip()
    first,sep,body=text.partition('\n');P.require(bool(sep),'Missing CUDA body')
    try:obj=P.parse(first)
    except (ValueError,P.Blocked) as e:raise P.NumericFailure('Invalid JSON block header') from e
    P.require(isinstance(obj,dict) and set(obj)=={'block'},'Header must contain only block')
    b=obj['block'];P.require(isinstance(b,list) and len(b)==2 and all(type(x) is int for x in b),'Block requires two integers')
    P.require(tuple(b) in C.allowed_blocks(task),'Block outside fixed choices')
    # Freeze exact original signature, not the fallback token-formatted copy.
    old=C.baseline_source
    try:
        C.baseline_source=lambda t:original[t]
        s,pb=C.candidate_source('// BLOCK %d %d\n'%(b[0],b[1])+body,task)
    finally:C.baseline_source=old
    P.require(pb==b,'Parser disagreement');return s,b

def response_text(provider,obj,cfg):
    if provider=='qwen':
        P.require(obj.get('truncated') is False and obj.get('stop_type') in ('eos','word'),'Qwen incomplete output')
        n=obj.get('timings',{}).get('predicted_n');cap=cfg['models']['qwen']['max_output_tokens']
        P.require(type(n) is int and 0<n<=cap+8,'Invalid Qwen token count');return obj.get('content')
    need(obj.get('model')==cfg['models'][provider]['id'],'Recorded model differs')
    if provider=='openai':
        P.require(obj.get('status')=='completed' and not obj.get('error'),'OpenAI incomplete/refused/failed response')
        pieces=[]
        for item in obj.get('output',[]):
            if item.get('type')=='reasoning':continue
            P.require(item.get('type')=='message' and item.get('role')=='assistant','Unexpected OpenAI output item/tool')
            for part in item.get('content',[]):
                P.require(part.get('type')=='output_text','Refusal/nontext OpenAI output');pieces.append(part['text'])
        P.require(len(pieces)==1,'Expected one complete OpenAI text output');return pieces[0]
    P.require(provider=='anthropic' and obj.get('type')=='message' and obj.get('stop_reason')=='end_turn','Claude nonterminal/refusal/token cap')
    pieces=[]
    for part in obj.get('content',[]):
        P.require(part.get('type')=='text','Unexpected Claude tool/thinking/nontext block');pieces.append(part['text'])
    P.require(len(pieces)==1,'Expected one complete Claude text output');return pieces[0]


def primary_data(raw,receipt):
    need(receipt['sha256']==PRIMARY_RECEIPT['sha256'],'Not the audited GPU004B first trial')
    f=read_archive(raw,receipt);plan=parse(f['protocol.json']);outcomes=parse(f['outcomes.json']);summary=parse(f['summary.json'])
    need(sha(canon(plan))==PRIMARY_PLAN_SHA,'Different source plan')
    need(plan['core_sha256']==ORIGINAL_NUMERIC_CORE_SHA and plan['source_bundle_sha256']==SOURCE_SHA,'Source/core identity differs')
    rs=[r for g in plan['groups'] for r in g['requests']]
    expected={(p,t,a,1) for p in ('qwen','openai','anthropic') for t in C.TASKS for a in C.ARMS}
    need(len(rs)==90 and len({r['id'] for r in rs})==90,'Source plan is not 90 unique slots')
    need({(r['provider'],r['task'],r['condition'],r['trial']) for r in rs}==expected,'Unbalanced source plan')
    need(len(outcomes)==90 and {o['id'] for o in outcomes}=={r['id'] for r in rs},'Outcome/plan ID mismatch')
    need(len({o['id'] for o in outcomes})==90,'Duplicate outcomes')
    need(Counter(o['generation_status'] for o in outcomes)=={'saved':85,'invalid_generation':5},'Unexpected source status counts')
    need(all(o['correctness_passed'] for o in outcomes if o['generation_status']=='saved'),'Source accepted set differs')
    orig={t:source_files()['sources/'+t+'.cu'].decode() for t in C.TASKS}
    for r in rs:
        need(sha(canon(r['messages']))==r['messages_sha256'],'Prompt hash mismatch')
        need(any(orig[r['task']] in m['content'] for m in r['messages']),'Original source missing from saved prompt')
    return plan,outcomes,orig


def validate_generation(plan,outcomes,orig,archives):
    by={o['id']:o for o in outcomes};entries=[];candidate_files={};seen=set()
    # Every input group is included, including Claude SYRK with five failures.
    for group in plan['groups']:
        label='generation-'+group['label'];f=archives[label]
        for r in group['requests']:
            arm=r['condition'];rd=arm+'/';cid=r['id'];need(cid not in seen,'Duplicate candidate');seen.add(cid)
            req=parse(f[rd+'request.json']);rec=parse(f[rd+'record.json']);obj=parse(f[rd+'response.json']);o=by[cid]
            need(req==r,'Recorded request differs from primary plan: '+cid)
            for k in ('id','provider','task','condition','trial','generation_status','model','error'):
                need(rec.get(k)==o.get(k),'Record/outcome mismatch '+cid+' '+k)
            need(rec.get('messages_sha256')==r['messages_sha256'],'Prompt identity changed')
            error=None;s=b=None
            try:s,b=parse_candidate(response_text(r['provider'],obj,plan['config']),r['task'],orig)
            except P.NumericFailure as e:error=str(e)
            entry={k:r[k] for k in ('id','provider','task','condition','trial')}
            entry.update(group=group['label'],model=o['model'],primary_generation_status=o['generation_status'],
              primary_error=o.get('error'),response_sha256=sha(f[rd+'response.json']),request_sha256=sha(f[rd+'request.json']),
              original_source_sha256=sha(orig[r['task']].encode()),messages_sha256=r['messages_sha256'])
            if o['generation_status']=='saved':
                need(error is None,'Saved candidate now fails original parser: '+cid)
                raw=f.get(rd+'candidate.cu');need(raw is not None and raw==s.encode(),'Candidate bytes/parser differ: '+cid)
                need(sha(raw)==o['source_sha256']==rec['source_sha256'] and b==o['block']==rec['block'],'Candidate hash/block differs: '+cid)
                need((s==orig[r['task']])==o['source_equals_original'],'Source identity flag differs')
                entry.update(eligible=True,source_sha256=sha(raw),source_equals_original=s==orig[r['task']],block=b,path='candidates/'+cid+'.cu')
                candidate_files[entry['path']]=raw
            else:
                need(error==o.get('error') and rd+'candidate.cu' not in f,'Failure replay differs; no repairs: '+cid)
                entry.update(eligible=False,path=None,block=None,replayed_error=error)
            if r['provider']=='qwen':
                wr=parse(f[rd+'wire-request.json'])
                need(obj.get('tokens_evaluated')==len(wr['prompt']),'Qwen token count differs')
            else:
                package=parse(f[rd+'api-package.json'])
                need(package['provider']==r['provider'] and package.get('batch_only') is True,'Not a recorded batch result')
                env=package['envelope'];need(env['http_status']==200,'Source API result failed')
                need(parse(base64.b64decode(env['raw_body_b64'],validate=True))==obj,'Raw provider response differs')
            entries.append(entry)
    need(len(entries)==90 and sum(e['eligible'] for e in entries)==85,'85/5 coverage changed')
    return entries,candidate_files


def build_payload(raw_summary,receipt,raw_archives):
    plan,outs,orig=primary_data(raw_summary,receipt)
    sources=source_files();verified={};payload={'evidence/summary.tar.gz':raw_summary,'evidence/summary-receipt.json':canon(receipt)}
    labels=['generation-'+g['label'] for g in plan['groups']]
    need(set(raw_archives)==set(labels),'Missing or unexpected generation archive')
    for label in labels:
        raw,rec=raw_archives[label];need(rec.get('label')==label,'Receipt label mismatch')
        verified[label]=read_archive(raw,rec,cap=128*MIB)
        payload['evidence/'+label+'.tar.gz']=raw;payload['evidence/'+label+'-receipt.json']=canon(rec)
    entries,candidates=validate_generation(plan,outs,orig,verified)
    payload.update(candidates)
    for n,b in sources.items():payload['original/'+n]=b
    man={'schema':VERSION,'source_plan_sha256':PRIMARY_PLAN_SHA,'primary_summary_sha256':receipt['sha256'],
      'numerical_core_sha256':CORE_SHA,'source_bundle_sha256':SOURCE_SHA,'source_slots':90,'eligible_candidates':85,
      'primary_invalid_preserved':5,'new_generation_calls':0,'source_namespaces_modified':False,
      'full_primary_raw_timing_backup':False,'cuda_sources_are_actual_saved_outputs':True,'entries':entries,
      'groups':[ {k:v for k,v in g.items() if k!='requests'} for g in plan['groups']],
      'original_environment':plan['environment'],'upstream_commit':C.COMMIT,
      'original_prompt_labels':'P0/S1/S2/W1/W2 retain their original A40/V100 meaning; they are not relabeled for L4',
      'scope':'Portability of all primary accepted candidates; no post-hoc JSON repairs; six development workloads'}
    payload['input-manifest.json']=canon(man)
    return payload,man


def bundle_data(raw,receipt,replay=True):
    f=read_archive(raw,receipt);man=parse(f['input-manifest.json'])
    need(man['schema']==VERSION and man['eligible_candidates']==85 and man['source_slots']==90,'Not this portability cohort')
    if replay:
        archives={}
        for g in man['groups']:
            lab='generation-'+g['label'];archives[lab]=(f['evidence/'+lab+'.tar.gz'],parse(f['evidence/'+lab+'-receipt.json']))
        rebuilt,m=build_payload(f['evidence/summary.tar.gz'],parse(f['evidence/summary-receipt.json']),archives)
        need(rebuilt==f and m==man,'Bundle did not reproduce from pinned original evidence')
    return f,man


def prepare(source_dir,out_dir):
    source=safe(source_dir);out=safe(out_dir)
    raw=read(source/'summary.tar.gz');receipt=parse(read(source/'summary-receipt.json'))
    plan,_,_=primary_data(raw,receipt);archives={}
    for group in plan['groups']:
        lab='generation-'+group['label']
        archives[lab]=(read(source/(lab+'.tar.gz')),parse(read(source/(lab+'-receipt.json'))))
    payload,man=build_payload(raw,receipt,archives)
    packed,rec=make_archive(payload,'portable-inputs');bundle_data(packed,rec)
    if out.exists():
        need(out.is_dir(),'Output is not a directory')
        existing=parse(read(out/'portable-inputs-receipt.json'));b=read(out/'portable-inputs.tar.gz')
        f,m=bundle_data(b,existing);need(f==payload,'Existing preparation is different; do not overwrite')
        print('GPU005_PREPARED_INPUTS_REVERIFIED',flush=True)
    else:
        out.parent.mkdir(parents=True,exist_ok=True)
        stage=Path(tempfile.mkdtemp(prefix=out.name+'.partial-',dir=out.parent))
        save(stage/'portable-inputs.tar.gz',packed);jw(stage/'portable-inputs-receipt.json',rec)
        save(stage/'runner.py',read(__file__,2*MIB));jw(stage/'target-a40.json',{'schema':VERSION,**A40_ENDPOINT})
        report={'state':'GPU005_PORTABILITY_INPUTS_PREPARED','eligible_saved_candidates':85,'original_invalid_preserved':5,
         'source_slots':90,'generation_archives_verified':18,'source_summary_verified':True,
         'new_generation_calls':0,'provider_http_calls':0,'ssh_connections':0,'new_gpu_jobs_started':0,
         'bundle_sha256':rec['sha256'],'bundle_bytes':rec['bytes'],'runtime_gpu_tests_performed_here':False,
         'primary_experiment_files_modified':False,'whole_pod_backup':False,'full_original_evaluation_archives_included':False}
        jw(stage/'preparation.json',report)
        need(not out.exists(),'Preparation destination appeared during build');os.rename(stage,out)
    report=parse(read(out/'preparation.json'));print(json.dumps(report,ensure_ascii=False,indent=2))
    print('GPU005_PORTABILITY_BUNDLE_LOCAL_VERIFIED='+str(out/'portable-inputs.tar.gz'),flush=True)
    print('NO_API_NO_SSH_NO_GENERATION_NO_GPU_EXECUTION')


def configure_target(profile,dest,host=None,port=None,fingerprint=None,gpu_uuid=None):
    need(profile in PROFILES,'Only A40 and L4 are implemented')
    if profile=='A40' and host is None:
        cfg={'schema':VERSION,**A40_ENDPOINT}
    else:
        host=host or input('Target direct SSH hostname/IP: ').strip()
        port=port or int(input('Direct SSH port: ').strip())
        fingerprint=fingerprint or input('Verified ED25519 host fingerprint (SHA256:...): ').strip()
        cfg={'schema':VERSION,'profile':profile,'host':host,'port':port,'user':'root',
             'host_fingerprint':fingerprint,'expected_gpu_uuid':gpu_uuid}
    validate_target(cfg,False);jw(dest,cfg)
    print('TARGET_ENDPOINT_SAVED='+str(Path(dest).absolute())+'; NO_CONNECTION_OR_DEPLOYMENT')


def validate_target(t,pinned=False):
    need(t.get('schema')==VERSION and t.get('profile') in PROFILES,'Invalid target profile')
    need(isinstance(t.get('host'),str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,252}',t['host']),'Invalid SSH hostname')
    need(type(t.get('port')) is int and 1<=t['port']<=65535 and t.get('user')=='root','Invalid SSH port/user')
    need(re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}',t.get('host_fingerprint','')),'Verified ED25519 fingerprint required')
    if t.get('expected_gpu_uuid') is not None:
        need(re.fullmatch(r'GPU-[0-9a-fA-F-]{36}',t['expected_gpu_uuid']),'Invalid GPU UUID')
    if pinned:
        need(isinstance(t.get('runtime_identity'),dict) and t.get('expected_gpu_uuid'),'Run --probe first')
        need(t['runtime_identity']['gpu_uuid']==t['expected_gpu_uuid'],'Pinned GPU differs')


class Connection:
    def __init__(self,t,key=None):
        validate_target(t);self.t=t;self.key=safe(key or Path.home()/'.ssh/id_ed25519')
        need(self.key.is_file(),'Private SSH key missing; do not upload keys')
        self.tmp=tempfile.TemporaryDirectory(prefix='gpu005-ssh-');self.dir=Path(self.tmp.name);self.endpoint='root@'+t['host']
        scan=subprocess.run(['ssh-keyscan','-T','10','-p',str(t['port']),'-t','ed25519',t['host']],capture_output=True,timeout=20)
        matches=[]
        for line in scan.stdout.decode(errors='replace').splitlines():
            a=line.split()
            if len(a)!=3 or a[1]!='ssh-ed25519':continue
            fp='SHA256:'+base64.b64encode(hashlib.sha256(base64.b64decode(a[2],validate=True)).digest()).decode().rstrip('=')
            if fp==t['host_fingerprint']:matches.append(line)
        need(matches,'SSH host fingerprint mismatch/unavailable; known_hosts not changed')
        kh=self.dir/'known_hosts';save(kh,('\n'.join(sorted(set(matches)))+'\n').encode())
        self.opts=['-F','/dev/null','-p',str(t['port']),'-i',str(self.key),'-o','IdentitiesOnly=yes',
          '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(kh),'-o','GlobalKnownHostsFile=/dev/null',
          '-o','HostKeyAlgorithms=ssh-ed25519','-o','PreferredAuthentications=publickey',
          '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','-o','ForwardAgent=no',
          '-o','ConnectTimeout=30','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=4',
          '-o','ControlMaster=auto','-o','ControlPath='+str(self.dir/'control'),'-o','ControlPersist=600']
    def run(self,args,data=None,timeout=300):
        cp=subprocess.run(['ssh','-T',*self.opts,self.endpoint,shlex.join([str(x) for x in args])],
                          input=data,stdout=subprocess.PIPE,timeout=timeout)
        need(cp.returncode==0,'SSH operation failed; no automatic execution retry')
        need(len(cp.stdout)<=256*MIB,'Oversized SSH response');return cp.stdout
    def close(self):
        with contextlib.suppress(Exception):
            subprocess.run(['ssh',*self.opts,'-O','exit',self.endpoint],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        self.tmp.cleanup()


# Standalone read-only inventory function; the same function is used in SSH and clean worker environments.
def inventory(profile,expected_uuid=None,preferred_sanitizer_sha=None,sanitizer_absolute=None):
    import ctypes as ct, hashlib, json, os, pathlib, shutil, subprocess, re
    Path=pathlib.Path
    def check(ok,msg):
        if not ok:raise RuntimeError(msg)
    def hf(p):
        h=hashlib.sha256()
        with open(p,'rb') as f:
            for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
        return h.hexdigest()
    env={'PATH':'/usr/local/cuda-12.8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
         'HOME':'/tmp','LANG':'C','LC_ALL':'C','CUDA_CACHE_DISABLE':'1','CUDA_MODULE_LOADING':'EAGER'}
    def command(args):
        p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=30)
        check(p.returncode==0,'Inventory command failed: '+args[0]+' '+p.stderr[-1000:]);return p.stdout.strip()
    query=command(['nvidia-smi','--query-gpu=uuid,name,driver_version','--format=csv,noheader'])
    rows=[[x.strip() for x in line.split(',')] for line in query.splitlines() if line.strip()]
    check(len(rows)==1 and len(rows[0])==3,'Exactly one visible GPU required')
    uid,name,driver=rows[0];check(expected_uuid is None or uid==expected_uuid,'GPU UUID changed')
    check(re.fullmatch(r'GPU-[0-9a-fA-F-]{36}',uid),'Invalid GPU UUID')
    check(name==profile['name'],'GPU model differs from explicitly selected profile')
    apps=command(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'])
    check(not apps,'Another GPU compute process is active; it will not be stopped')
    os.environ['CUDA_VISIBLE_DEVICES']=uid
    lib=ct.CDLL('libcuda.so.1');I=ct.c_int;S=ct.c_size_t
    def call(n,args,*vals):
        f=getattr(lib,n);f.argtypes=args;f.restype=I
        check(f(*vals)==0,'CUDA inventory call failed: '+n)
    call('cuInit',[ct.c_uint],0);dev=I();call('cuDeviceGet',[ct.POINTER(I),I],ct.byref(dev),0)
    a,b=I(),I();call('cuDeviceComputeCapability',[ct.POINTER(I),ct.POINTER(I),I],ct.byref(a),ct.byref(b),dev.value)
    check([a.value,b.value]==profile['cc'],'Compute capability differs')
    mem=S();call('cuDeviceTotalMem_v2',[ct.POINTER(S),I],ct.byref(mem),dev.value)
    gpu={'name':name,'compute_capability':[a.value,b.value],'memory_bytes':mem.value}
    for label,n in [('max_threads_per_block',1),('static_shared_memory_per_block',8),('warp_size',10),
                    ('registers_per_block',12),('multiprocessors',16),('l2_bytes',38),
                    ('max_threads_per_multiprocessor',39),('shared_memory_per_multiprocessor',81)]:
        v=I();call('cuDeviceGetAttribute',[ct.POINTER(I),I,I],ct.byref(v),n,dev.value);gpu[label]=v.value
    root=Path('/usr/local/cuda-12.8');nv=(root/'lib64/libnvrtc.so').resolve()
    check(nv.is_file(),'NVRTC 12.8 installation not found; no package/driver change is made')
    nl=ct.CDLL(str(nv));vfn=nl.nvrtcVersion;vfn.argtypes=[ct.POINTER(I),ct.POINTER(I)];vfn.restype=I
    major,minor=I(),I();check(vfn(ct.byref(major),ct.byref(minor))==0,'NVRTC version query failed')
    check([major.value,minor.value]==[12,8],'This protocol requires NVRTC 12.8')
    n=I();nl.nvrtcGetNumSupportedArchs.argtypes=[ct.POINTER(I)];nl.nvrtcGetNumSupportedArchs.restype=I
    check(nl.nvrtcGetNumSupportedArchs(ct.byref(n))==0 and 0<n.value<100,'Cannot query NVRTC architectures')
    archs=(I*n.value)();nl.nvrtcGetSupportedArchs.argtypes=[ct.POINTER(I)];nl.nvrtcGetSupportedArchs.restype=I
    check(nl.nvrtcGetSupportedArchs(archs)==0 and a.value*10+b.value in archs,'Compiler lacks selected architecture')
    paths=[root/'compute-sanitizer/compute-sanitizer',root/'bin/compute-sanitizer',
           Path('/usr/local/cuda/compute-sanitizer/compute-sanitizer'),Path('/usr/local/cuda/bin/compute-sanitizer')]
    for d in os.environ.get('PATH','').split(':')+env['PATH'].split(':'):
        if d and Path(d).is_absolute():paths.append(Path(d)/'compute-sanitizer')
    uniq=[]
    for p in paths:
        if p.is_file():
            p=p.resolve()
            if p not in uniq:uniq.append(p)
    matches=[p for p in uniq if hf(p)==preferred_sanitizer_sha] if preferred_sanitizer_sha else []
    sanitizer=matches[0] if matches else (uniq[0] if uniq else None)
    if sanitizer_absolute is not None:
        pinned=Path(sanitizer_absolute)
        check(pinned.is_absolute() and pinned.is_file() and str(pinned.resolve())==str(pinned), 'Pinned Sanitizer path changed')
        check(hf(pinned)==preferred_sanitizer_sha,'Pinned Sanitizer hash changed')
        sanitizer=pinned
    check(sanitizer is not None,'Compute Sanitizer unavailable')
    sanver=command([str(sanitizer),'--version'])
    compiler=shutil.which('g++',path=env['PATH']);check(compiler is not None,'g++ missing')
    compiler=str(Path(compiler).resolve());ccver=command([compiler,'--version']).splitlines()[0]
    for tool in ('python3','setpriv','nvidia-smi'):
        check(shutil.which(tool,path=env['PATH']) is not None,'Missing tool '+tool)
    libs={str(nv):hf(nv)}
    for p in sorted((root/'lib64').glob('libnvrtc-builtins.so*')):
        if p.is_file():libs[str(p.resolve())]=hf(p.resolve())
    check(len(libs)>=2,'NVRTC builtins library missing')
    identity={'gpu':gpu,'gpu_uuid':uid,'driver_version':driver,'nvrtc_version':[major.value,minor.value],
      'nvrtc_sha256':hf(nv),'nvrtc_path':str(nv),'nvrtc_libraries':libs,
      'sanitizer_path':str(sanitizer),'sanitizer_sha256':hf(sanitizer),'sanitizer_version':sanver,
      'host_compiler_path':compiler,'host_compiler':ccver,'host_compiler_sha256':hf(compiler),
      'os_release':Path('/etc/os-release').read_text()}
    return {'identity':identity,'free_disk_bytes':shutil.disk_usage('/workspace').free,
            'storage_persistence_verified':False,'provider_http_calls':0,'model_generation_calls':0}


def function_source(fn):
    # Our source file is under 1 MiB; use AST so embedded long literals cannot be mistaken for definitions.
    text=read(__file__,2*MIB).decode();tree=ast.parse(text)
    for n in tree.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==fn.__name__:
            return ast.get_source_segment(text,n)
    raise RuntimeError('Function source not found')


def probe_target(path,out_path=None):
    t=parse(read(path));validate_target(t)
    preferred=None
    if t['profile']=='A40':preferred=primary_data(base64.b64decode(PRIMARY_SUMMARY_B64),PRIMARY_RECEIPT)[0]['environment']['sanitizer_sha256']
    code=function_source(inventory)+'\nimport json\nprint(json.dumps(inventory('+repr(PROFILES[t['profile']])+','+repr(t.get('expected_gpu_uuid'))+','+repr(preferred)+')))\n'
    con=Connection(t)
    try:report=parse(con.run(['/usr/bin/python3','-I','-S','-B','-c',code],timeout=180))
    finally:con.close()
    t=copy.deepcopy(t);t['expected_gpu_uuid']=report['identity']['gpu_uuid'];t['runtime_identity']=report['identity']
    validate_target(t,True)
    out=safe(out_path or Path(path).with_name(Path(path).stem+'-pinned.json'))
    if out.exists():need(parse(read(out))==t,'Pinned target differs; do not overwrite')
    else:jw(out,t)
    old=primary_data(base64.b64decode(PRIMARY_SUMMARY_B64),PRIMARY_RECEIPT)[0]['environment']
    print(json.dumps({'state':'GPU005_TARGET_PROBE_COMPLETE','target':t['profile'],
      'gpu_uuid':t['expected_gpu_uuid'],'runtime_identity':t['runtime_identity'],
      'matches_origin_nvrtc_binary':t['runtime_identity']['nvrtc_sha256']==old['nvrtc_sha256'],
      'matches_origin_sanitizer_binary':t['runtime_identity']['sanitizer_sha256']==old['sanitizer_sha256'],
      'free_disk_bytes':report['free_disk_bytes'],'candidate_execution_started':False},indent=2,ensure_ascii=False))
    print('GPU005_PINNED_TARGET='+str(out))


def forbid_generation(*args,**kwargs):
    raise RuntimeError('GPU005 has no generation, provider API, model download or model-start path')


def patch_cuda_guard(profile):
    raw=gzip.decompress(base64.b64decode(C.PILOT_EMBED)).decode();tree=ast.parse(raw)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CUDA')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    text=textwrap.dedent(ast.get_source_segment(raw,method))
    old="require(self.info['name']=='NVIDIA A40' and [major.value,minor.value]==[8,6],'Unexpected evaluation GPU')"
    new="require(self.info['name']==GPU005_EXPECTED_NAME and [major.value,minor.value]==GPU005_EXPECTED_CC,'Unexpected evaluation GPU')"
    need(text.count(old)==1,'Pinned CUDA guard shape differs')
    patched=text.replace(old,new)
    P.GPU005_EXPECTED_NAME=profile['name'];P.GPU005_EXPECTED_CC=profile['cc']
    namespace={};exec(compile(patched,'<gpu005-target-bound-cuda-init>','exec'),P.__dict__,namespace)
    P.CUDA.__init__=namespace['__init__']
    return {'original_method_sha256':sha(text.encode()),'target_bound_method_sha256':sha(patched.encode()),
            'change':'Only explicit GPU name/compute capability guard parameterized; no kernel arithmetic modified'}


def configure_runtime(target,root=None):
    global ROOT
    validate_target(target,True)
    if root is not None:ROOT=safe(root)
    C.__file__=__file__;C.LOCAL_REL=Path('unused-gpu005-local-helper')
    C.RUN_SECONDS,C.ACK_SECONDS=RUN_SECONDS,ACK_SECONDS;C.configure(ROOT)
    P.EXPECTED_GPU=target['expected_gpu_uuid'];P.MAX_GENERATIONS=0
    original_clean=P.clean_env
    def clean_env():
        return {'PATH':'/usr/local/cuda-12.8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
          'HOME':'/tmp','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
          'CUDA_VISIBLE_DEVICES':target['expected_gpu_uuid'],'CUDA_CACHE_DISABLE':'1',
          'CUDA_MODULE_LOADING':'EAGER','OMP_NUM_THREADS':'4'}
    P.clean_env=clean_env
    identity=target['runtime_identity'];san=Path(identity['sanitizer_path'])
    def sanitizer():
        need(san.is_absolute() and hfile(san)==identity['sanitizer_sha256'],'Pinned Sanitizer changed')
        return str(san)
    P.sanitizer_path=sanitizer
    major,minor=PROFILES[target['profile']]['cc']
    P.NVRTC_OPTIONS=['--gpu-architecture=sm_'+str(major)+str(minor)]+FROZEN_OPTIONS[1:]
    patch=patch_cuda_guard(PROFILES[target['profile']])
    C.numeric=numeric;P.remote_guard=remote_guard
    P.module_a=P.start_model=P.generate_group=C.generate_group=forbid_generation
    return patch


def remote_target():
    p=Path(__file__).absolute()
    need(p==ROOT/'control/runner.py','Remote runner must be installed in its own GPU005 namespace')
    t=parse(read(ROOT/'control/target.json'));validate_target(t,True);return t


def remote_guard():
    need(os.geteuid()==0 and Path('/workspace').is_dir(),'Remote coordinator requires the authorized root Pod shell')
    need(Path(__file__).absolute()==ROOT/'control/runner.py','Unexpected runner location')


def check_runtime(target):
    inv=inventory(PROFILES[target['profile']],target['expected_gpu_uuid'],target['runtime_identity']['sanitizer_sha256'],
                  target['runtime_identity']['sanitizer_path'])
    # Excludes observation time/free memory; pins stable compiler/device/tool identities.
    need(inv['identity']==target['runtime_identity'],'Pinned target environment differs; re-probe, do not delete existing run')
    need(inv['free_disk_bytes']>=4*1024**3,'Need 4GiB free; no files are removed automatically')
    return inv


# Numerical process orchestration from GPU002, extended only with an explicit reference BLOCK.
def numeric(task,sh,dest,mode,*,source=None,cubin=None,helper=None,block=None,baseline=None,sanitizer=None,baseline_block=None):
    dest=P.safe(dest);dest.mkdir(parents=True,exist_ok=False);P.public_dirs(dest);os.chown(dest,65534,65534)
    j=dict(task=task,shape=list(sh),mode=mode,output=str(dest/'numeric-result.json'))
    if source is not None:
        C.save(dest/'kernel.cu',source.encode());(dest/'kernel.cu').chmod(0o444);j.update(source=str(dest/'kernel.cu'),source_sha256=C.sha(source.encode()))
    if cubin is not None:j.update(cubin=str(cubin),cubin_sha256=C.hfile(cubin),block=list(block),helper=str(helper),helper_sha256=C.hfile(helper))
    if baseline is not None:j.update(baseline=str(baseline),baseline_sha256=C.hfile(baseline))
    if baseline_block is not None:
        need(mode=='time' and tuple(baseline_block) in C.allowed_blocks(task),'Invalid reference block')
        j['reference_block']=list(baseline_block)
    jp=dest/'job.json';C.jw(jp,j);jp.chmod(0o444)
    argv=P.unpriv_prefix()
    if sanitizer:argv+=[P.sanitizer_path(),'--tool',sanitizer,'--error-exitcode','86','--target-processes','all']
    argv+=['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_numeric',str(jp)]
    rc=P.command(argv,dest/'process.log',600 if sanitizer else 300)
    res=C.parse(C.read(dest/'numeric-result.json')) if (dest/'numeric-result.json').exists() else {'ok':False,'error':'NO_RESULT'}
    res['process_returncode']=rc;res['ok']=res.get('ok') is True and rc==0
    if sanitizer:
        text=C.read(dest/'process.log',32*MIB).decode(errors='replace')
        clean=bool(re.search(r'ERROR SUMMARY:\s+0 errors',text)) or sanitizer=='racecheck' and bool(re.search(r'RACECHECK SUMMARY:\s+0 hazards',text))
        res['sanitizer_clean']=bool(clean and rc==0);res['ok']=res['ok'] and res['sanitizer_clean']
    if mode=='compile' and res['ok']:
        for ext in ('ptx','cubin'):
            p=dest/('kernel.'+ext);p.chmod(0o444);res[ext+'_sha256']=C.hfile(p)
    C.jw(dest/'parent-result.json',res)
    error=res.get('error','');fatal_driver=('CUDA_DRIVER_ERROR' in error and not re.search(r'cuLaunchKernel (?:1|701)\b',error))
    if not res['ok'] and (fatal_driver or rc in (124,-9)):
        raise P.Blocked('GPU execution infrastructure failure; retained: '+str(dest)+' '+error)
    return res


def numeric_job(path):
    j=parse(read(path));old=None;task=j.get('task')
    if 'reference_block' in j:
        need(j['mode']=='time' and task in C.TASKS,'Reference launch can change only timing')
        block=j['reference_block'];need(isinstance(block,list) and all(type(x) is int for x in block)
             and tuple(block) in C.allowed_blocks(task),'Unknown reference launch')
        selection=parse(read(ROOT/'selection/selection.json'))
        need(block==selection[task]['selected_block'],'Reference block is not exploration-selected')
        old=C.SPECS[task]['base'];C.SPECS[task]['base']=block
    try:return FROZEN_NUMERIC_JOB(path)
    finally:
        if old is not None:C.SPECS[task]['base']=old


def schedule(man):
    rng=random.Random(20261009051);tasks=list(C.TASKS);rng.shuffle(tasks);passes=[]
    randoms={t:list(random.Random(20261009052+i).choice(C.allowed_blocks(t))) for i,t in enumerate(C.TASKS)}
    for i,phase in enumerate(('exploration','confirmation')):
        for t in (tasks if not i else list(reversed(tasks))):
            blocks=[list(x) for x in C.allowed_blocks(t)];random.Random(20261009053+i*100+list(C.TASKS).index(t)).shuffle(blocks)
            passes.append({'phase':phase,'task':t,'blocks':blocks,'shapes':[list(s) for s in C.SPECS[t]['perf']]})
    return {'schema':VERSION,'source_plan_sha256':PRIMARY_PLAN_SHA,'new_generation_calls':0,'source_slots':90,
      'eligible_candidates':85,'primary_invalid_preserved':5,'profiles_supported':['A40','L4'],
      'passes':passes,'random_choices':randoms,'candidate_groups':man['groups'],
      'controls_planned_cells':176,'candidate_original_baseline_cells_max':170,'candidate_tuned_baseline_cells_max':170,
      'selection_rule':'EXPLORATION only; maximize geometric mean of both valid sizes; ties in original allowed-block order',
      'confirmation_rule':'Fresh pass over all blocks; frozen selection is not replaced by confirmation maximum',
      'candidate_rule':'Saved source and saved BLOCK fixed; no re-generation or code/metadata repairs',
      'tuned_baseline_rule':'Same-host paired measurement vs original CUDA at the frozen exploration-selected block',
      'source_recompilation':'Per target sm_86 or sm_89; same numerical flags and NVRTC 12.8 requirement',
      'scope':'Six already-developed workloads; not a new large dataset or GPU-specific re-generation study',
      'numeric_protocol':{k:C.PROTOCOL[k] for k in ('strict_semantics','baseline','host_adaptations','measurement',
                          'numerical_inputs','timing_input','timing_repetitions','sanitizers')},
      'formal_equivalence_proven':False}


def wait_ack(rec):
    P.update(phase='WAITING_LOCAL_BACKUP',checkpoint=rec['label'])
    end=min(P.WORK_DEADLINE,time.monotonic()+ACK_SECONDS);path=ROOT/'acks'/(rec['label']+'.json')
    while not path.exists():
        need(time.monotonic()<end,'Local ACK/run deadline exceeded; evidence retained');time.sleep(2)
    need(parse(read(path)).get('sha256')==rec['sha256'],'Wrong local backup ACK')

def checkpoint(src,label):
    rec=P.archive_dir(src,label);wait_ack(rec);print('GPU005_CHECKPOINT_ACKED '+label,flush=True)


def metric_pair(task,sh,block,cubin,base,twin,helper,dest,reference_block=None):
    result={'shape':list(sh),'block':list(block),'reference_block':list(reference_block or C.SPECS[task]['base']),
      'measurement_valid':False,'speedup':None,'quality_reasons':[]}
    r=C.numeric(task,sh,dest/'timing','time',cubin=cubin,baseline=base,helper=helper,block=block,baseline_block=reference_block)
    if r['ok']:
        result.update(P.timing_metric(r['rows']))
        ib=reference_block or C.SPECS[task]['base']
        control=C.numeric(task,sh,dest/'identity-timing','time',cubin=twin,baseline=base,helper=helper,block=ib,baseline_block=reference_block)
        if control['ok']:
            im=P.timing_metric(control['rows']);result['identity']=im
            if not im['measurement_valid'] or abs(math.log(im['speedup']))>math.log(1.02):
                result['measurement_valid']=False;result['quality_reasons'].append('identity_control_shift')
        else:result['measurement_valid']=False;result['quality_reasons'].append('identity_execution_failed')
    else:result['error']=r.get('error','timing_failed')
    result['speedup_gt_1_02']=bool(result['measurement_valid'] and result['speedup']>1.02)
    return result


def validate_blocks(helper):
    eligible={}
    for task in C.TASKS:
        for block in C.allowed_blocks(task):
            rows=[]
            for sh in C.shapes(task):
                P.no_other_gpu();base,_=C.BASES[task,sh]
                d=ROOT/'block-validation'/task/('b%dx%d'%block)/C.shape_id(sh)
                r=C.validate_object(task,sh,base,d,helper,block,sanit=sh==C.small_shapes(task)[-1]);rows.append({'shape':list(sh),**r})
                if not r['passed']:break
            ok=len(rows)==len(C.shapes(task)) and all(r['passed'] for r in rows)
            eligible[task,tuple(block)]=ok;jw(ROOT/'block-validation'/task/('b%dx%d'%block)/'summary.json',{'passed':ok,'checks':rows})
    return eligible


def control_pass(entry,helper,eligible):
    task,phase=entry['task'],entry['phase'];rows=[]
    jw(ROOT/phase/task/'telemetry-before.json',P.telemetry())
    for block in entry['blocks']:
        for shape in entry['shapes']:
            sh=tuple(shape);P.no_other_gpu();d=ROOT/phase/task/('b%dx%d'%tuple(block))/C.shape_id(sh)
            P.update(phase='CONTROL_'+phase.upper(),task=task,block=block,shape=shape)
            base,twin=C.BASES[task,sh]
            r={'task':task,'phase':phase,'block':block,'shape':shape,'source_changed':False,'same_cubin':True,
               'source_sha256':sha(C.baseline_source(task).encode()),'cubin_sha256':hfile(base),
               'measurement_valid':False,'speedup':None,'speedup_gt_1_02':False,'stage':'validation_failed'}
            if eligible[task,tuple(block)]:
                r.update(metric_pair(task,sh,block,base,base,twin,helper,d));r['stage']='measured'
            jw(d/'outcome.json',r);rows.append(r)
    jw(ROOT/phase/task/'outcomes.json',rows);jw(ROOT/phase/task/'telemetry-after.json',P.telemetry());return rows


def select_exploration(rows,plan):
    need(rows and all(r['phase']=='exploration' for r in rows),'Selection requires exploration-only data')
    result={}
    for task in C.TASKS:
        scores=[]
        for b in C.allowed_blocks(task):
            ss=[r for r in rows if r['task']==task and tuple(r['block'])==b]
            need(len(ss)==2 and {tuple(r['shape']) for r in ss}=={tuple(s) for s in C.SPECS[task]['perf']},'Exploration coverage gap')
            if all(r['measurement_valid'] for r in ss):
                scores.append({'block':list(b),'score':math.exp(sum(math.log(r['speedup']) for r in ss)/2)})
        best=max(scores,key=lambda r:r['score']) if scores else None
        result[task]={'selected_block':best['block'] if best else None,'exploration_score':best['score'] if best else None,
                      'random_block':plan['random_choices'][task],'eligible_scores':scores,'no_confirmation_data_used':True}
    return result


def evaluate_saved_group(g,man,payload,helper,selection):
    selected=[e for e in man['entries'] if e['group']==g['label']];records=[]
    for e in selected:
        r={k:e[k] for k in ('id','provider','model','task','condition','trial')}
        r.update(generation_status=e['primary_generation_status'],error=e['primary_error'],
          primary_source_status=e['primary_generation_status'],new_generation_calls=0,source_preserved=True)
        if e['eligible']:
            b=payload[e['path']];need(sha(b)==e['source_sha256'],'Saved source changed')
            C.save(ROOT/'groups'/g['label']/'generation'/e['condition']/'candidate.cu',b)
            r.update(source_sha256=e['source_sha256'],source_equals_original=e['source_equals_original'],block=e['block'])
        else:r['target_not_evaluated_original_invalid']=True
        records.append(r)
    outputs=C.evaluate_group(g,records,helper)
    for o in outputs:
        o['tuned_measurements']=[]
        if not o['correctness_passed']:continue
        task=o['task'];block=selection[task]['selected_block']
        for sh in [tuple(s) for s in C.SPECS[task]['perf']]:
            d=ROOT/'groups'/g['label']/'evaluation'/o['condition']/C.shape_id(sh)
            if block is None:
                o['tuned_measurements'].append({'shape':list(sh),'measurement_valid':False,'speedup':None,'error':'NO_VALID_EXPLORATION_SELECTION'})
                continue
            base,twin=C.BASES[task,sh];cubin=d/'compiled/kernel.cubin';P.no_other_gpu()
            mm=metric_pair(task,sh,o['block'],cubin,base,twin,helper,d/'selected-reference',reference_block=block)
            mm.update(reference_kind='exploration_selected_original_CUDA',same_source_as_original=o['source_equals_original'])
            o['tuned_measurements'].append(mm)
        # Do not overwrite the numeric core's outcome; extended portability result has a new name.
        jw(ROOT/'groups'/g['label']/'evaluation'/o['condition']/'portability-outcome.json',o)
    jw(ROOT/'groups'/g['label']/'portability-outcomes.json',outputs);return outputs


def csv_bytes(rows):
    out=io.StringIO();fields=list(dict.fromkeys(k for row in rows for k in row))
    w=csv.DictWriter(out,fields);w.writeheader();w.writerows(rows);return out.getvalue().encode()


def final_results(outcomes,controls,selection,plan,target,man):
    expected={e['id'] for e in man['entries']};need(len(outcomes)==len({o['id'] for o in outcomes})==90 and {o['id'] for o in outcomes}==expected,'90-source-slot coverage failed')
    grid={(p,t,tuple(b),tuple(s)) for p in ('exploration','confirmation') for t in C.TASKS for b in C.allowed_blocks(t) for s in C.SPECS[t]['perf']}
    actual=[(r['phase'],r['task'],tuple(r['block']),tuple(r['shape'])) for r in controls]
    need(len(actual)==176 and len(set(actual))==176 and set(actual)==grid,'Control grid differs')
    by={};rows=[]
    for provider in ('qwen','openai','anthropic'):
        ss=[o for o in outcomes if o['provider']==provider]
        valid=[m for o in ss for m in o['measurements'] if m['measurement_valid']]
        tuned=[m for o in ss for m in o['tuned_measurements'] if m['measurement_valid']]
        by[provider]={'source_slots':len(ss),'target_correctness_passed':sum(o['correctness_passed'] for o in ss),
          'valid_size_measurements':len(valid),'speedups_gt_1_02_vs_original':sum(m['speedup_gt_1_02'] for m in valid),
          'valid_tuned_comparisons':len(tuned),'speedups_gt_1_02_vs_tuned':sum(m.get('speedup_gt_1_02',False) for m in tuned)}
    for o in outcomes:
        for kind in ('measurements','tuned_measurements'):
            for m in o[kind]:
                rows.append({k:o.get(k) for k in ('id','provider','model','task','condition','trial','stage','generation_status','correctness_passed','source_sha256','block')}|{'comparison':kind}|m)
    summary={'state':'GPU005_PORTABILITY_85_COMPLETE','scope':'85 fixed saved CUDA candidates, same BLOCK; six development tasks',
      'target_gpu':target['runtime_identity']['gpu'],'gpu_uuid':target['expected_gpu_uuid'],'new_generation_calls':0,
      'source_slots':90,'target_candidate_slots':85,'primary_invalid_preserved':5,'control_cells':len(controls),
      'valid_control_cells':sum(r['measurement_valid'] for r in controls),'providers':by,
      'old_results_overwritten':False,'selection_used_confirmation':False,'formal_equivalence_proven':False,
      'not_gpu_conditioned_regeneration':True,'prompt_labels_retain_original_A40_V100_meaning':True,
      'whole_GPU_study_complete':False,'utc':now()}
    d=ROOT/'final';jw(d/'summary.json',summary);jw(d/'outcomes.json',outcomes);jw(d/'controls.json',controls)
    jw(d/'selection.json',selection);jw(d/'protocol.json',plan);jw(d/'target.json',target)
    jw(d/'input-manifest.json',man);C.save(d/'outcomes.csv',csv_bytes(rows))
    C.save(d/'coverage_90.csv',csv_bytes([{'id':o['id'],'provider':o['provider'],'task':o['task'],
        'original_status':o['generation_status'],'target_stage':o['stage'],'correctness_passed':o['correctness_passed']} for o in outcomes]))
    return summary


def worker(target,allow):
    remote_guard();need(allow,'Explicit ephemeral/checkpoint permission is required')
    P.WORK_DEADLINE=time.monotonic()+RUN_SECONDS;P.STATE={};C.BASES.clear();os.umask(0o022)
    def terminate(*_):raise RuntimeError('Worker stop requested; no automatic repetition')
    signal.signal(signal.SIGTERM,terminate)
    try:
        with P.lock('/workspace/gpu-code-pilot-exclusive.lock'):
            P.public_dirs(ROOT);P.update(phase='VERIFYING_PORTABILITY_INPUTS',new_generation_calls=0,evaluation_terminal=0)
            inv=check_runtime(target)
            b=read(ROOT/'inputs/portable-inputs.tar.gz');rec=parse(read(ROOT/'inputs/portable-inputs-receipt.json'))
            payload,man=bundle_data(b,rec)
            plan=schedule(man);jw(ROOT/'setup/protocol.json',plan);jw(ROOT/'setup/environment-before.json',inv)
            jw(ROOT/'setup/target.json',target);jw(ROOT/'setup/input-manifest.json',man)
            jw(ROOT/'setup/input-receipt.json',rec);save(ROOT/'setup/runner.py',read(__file__,2*MIB))
            for n,raw in source_files().items():C.save(ROOT/'setup'/n,raw)
            helper=C.build_helper();jw(ROOT/'setup/host-helper-identity.json',{'sha256':hfile(helper)})
            checkpoint(ROOT/'setup','setup')
            C.baseline_preflight(helper);checkpoint(ROOT/'preflight','original-controls')
            eligibility=validate_blocks(helper);checkpoint(ROOT/'block-validation','all-block-validation')
            controls=[];selection=None
            for entry in plan['passes']:
                if entry['phase']=='confirmation' and selection is None:
                    selection=select_exploration(controls,plan)
                    jw(ROOT/'selection/selection.json',selection);jw(ROOT/'selection/exploration-rows.json',controls)
                    checkpoint(ROOT/'selection','frozen-selection')
                controls.extend(control_pass(entry,helper,eligibility))
                checkpoint(ROOT/entry['phase']/entry['task'],entry['phase']+'-'+entry['task'])
            outcomes=[]
            for group in man['groups']:
                need(time.monotonic()<P.WORK_DEADLINE,'Run deadline exceeded')
                P.no_other_gpu();outcomes.extend(evaluate_saved_group(group,man,payload,helper,selection))
                checkpoint(ROOT/'groups'/group['label'],'evaluated-'+group['label'])
                P.update(evaluation_terminal=len(outcomes),new_generation_calls=0)
            after=check_runtime(target);need(hfile(ROOT/'inputs/portable-inputs.tar.gz')==rec['sha256'],'Input bundle changed')
            summary=final_results(outcomes,controls,selection,plan,target,man);jw(ROOT/'final/environment-after.json',after)
            r=P.archive_dir(ROOT/'final','summary');wait_ack(r)
            jw(ROOT/'completion.json',{'summary_sha256':hfile(ROOT/'final/summary.json'),'summary_checkpoint':r,'utc':now()})
            P.update(phase='COMPLETE');print(summary['state'],flush=True)
    except BaseException as e:
        tails={}
        with contextlib.suppress(Exception):
            logs=sorted(ROOT.rglob('process.log'),key=lambda p:p.stat().st_mtime)[-3:]
            for p in logs:
                with p.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-4000));tails[str(p.relative_to(ROOT))]=f.read().decode(errors='replace')
        P.atomic(ROOT/'failure.json',{'error':type(e).__name__+': '+str(e),'traceback':traceback.format_exc(),'logs':tails,'utc':now()})
        P.update(phase='BLOCKED',error=str(e));raise


def installation_code(pin):
    # Upload only this evaluation runner, target pin and fixed-source bundle; no shell expansion or extraction of arbitrary paths.
    return '''import io,tarfile,gzip,hashlib,json,pathlib,os,sys
root=pathlib.Path(%r)
assert os.geteuid()==0 and pathlib.Path('/workspace').is_dir(), 'Not an authorized root GPU container'
for p in (root,*root.parents): assert not p.is_symlink(), 'Symlink in destination'
b=sys.stdin.buffer.read(64*1024**2+1)
assert len(b)<=64*1024**2 and hashlib.sha256(b).hexdigest()==%r, 'Upload digest mismatch'
allowed={'control/runner.py','control/target.json','inputs/portable-inputs.tar.gz','inputs/portable-inputs-receipt.json'}
items={}
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 for m in t:
  assert m.name in allowed and m.name not in items and m.isfile() and m.size<32*1024**2, 'Invalid uploaded member'
  items[m.name]=t.extractfile(m).read()
assert set(items)==allowed, 'Missing uploaded input'
for name,raw in items.items():
 p=root/name
 for q in (p,*p.parents): assert not q.is_symlink(), 'Symlink refused'
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists(): assert p.is_file() and p.read_bytes()==raw, 'Existing run/input conflict'
 else:
  with p.open('xb') as f: f.write(raw);f.flush();os.fsync(f.fileno())
 p.chmod(0o444)
print('GPU005_RUNNER_AND_INPUTS_UPLOADED')
'''%(str(ROOT),pin)


def installation_archive(files):
    b=io.BytesIO()
    with tarfile.open(fileobj=b,mode='w:gz') as tf:
        for n,raw in sorted(files.items()):
            ti=tarfile.TarInfo(n);ti.size=len(raw);ti.mode=0o444;tf.addfile(ti,io.BytesIO(raw))
    return b.getvalue()


def remote_command(*args):return ['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),*args]

def collect_checkpoint(con,rec,out):
    label=rec['label'];need(re.fullmatch(r'[a-z0-9-]+',label),'Invalid checkpoint label')
    p=out/(label+'.tar.gz');rp=out/(label+'-receipt.json')
    if p.exists():read_archive(read(p,256*MIB),rec)
    else:
        need(shutil.disk_usage(out).free>rec['bytes']+128*MIB,'Not enough local backup space')
        temp=out/(label+'.partial-'+os.urandom(6).hex())
        with temp.open('xb') as f:
            cp=subprocess.run(['ssh','-T',*con.opts,con.endpoint,shlex.join(remote_command('--_send',label))],stdout=f)
            need(cp.returncode==0,'Backup transfer failed; .partial retained');f.flush();os.fsync(f.fileno())
        read_archive(read(temp,256*MIB),rec);os.rename(temp,p)
    if rp.exists():need(parse(read(rp))==rec,'Local receipt conflict')
    else:jw(rp,rec)
    con.run(remote_command('--_ack',label,rec['sha256']))
    print('GPU005_LOCAL_CHECKPOINT_VERIFIED '+label,flush=True)


def local_run(mode,target_path,prepared,allow):
    need(os.geteuid()!=0,'Run SSH controller from WSL without sudo')
    target=parse(read(target_path));validate_target(target,True);prep=safe(prepared)
    raw=read(prep/'portable-inputs.tar.gz');rec=parse(read(prep/'portable-inputs-receipt.json'));_,man=bundle_data(raw,rec)
    out=safe(prep/'results'/target['profile'].lower());out.mkdir(parents=True,exist_ok=True)
    if (out/'target.json').exists():need(parse(read(out/'target.json'))==target,'Result destination belongs to another GPU/pin')
    else:jw(out/'target.json',target)
    con=Connection(target)
    try:
        with P.lock(out/'controller.lock'):
            if mode=='run':
                need(allow,'Explicit ephemeral/local checkpoint permission required')
                upload=installation_archive({'control/runner.py':read(__file__,2*MIB),'control/target.json':canon(target),
                  'inputs/portable-inputs.tar.gz':raw,'inputs/portable-inputs-receipt.json':canon(rec)})
                print(con.run(['/usr/bin/python3','-I','-S','-B','-c',installation_code(sha(upload))],data=upload).decode().strip())
                if not (out/'authorization.json').exists():
                    print('Target: '+target['profile']+' '+target['expected_gpu_uuid'])
                    print('No new LLM generation. Fresh 176 launch-control cells + up to170 original-baseline and170 tuned-baseline candidate comparisons.')
                    phrase='RUN 85 ON '+target['profile']
                    need(input('Start GPU execution only by entering '+phrase+': ').strip()==phrase,'GPU execution not authorized')
                    jw(out/'authorization.json',{'approved':True,'target_sha256':sha(canon(target)),'bundle_sha256':rec['sha256'],'utc':now()})
                auth=parse(read(out/'authorization.json'));need(auth['target_sha256']==sha(canon(target)) and auth['bundle_sha256']==rec['sha256'],'Authorization mismatch')
                doc=parse(con.run(remote_command('--_launch','--allow-ephemeral-with-local-checkpoints')))
                print('GPU005_PORTABILITY_STARTED; NO_NEW_GENERATION',flush=True)
            elif mode=='stop':print(con.run(remote_command('--_stop')).decode());return
            else:doc=parse(con.run(remote_command('--_status')))
            seen=set()
            while True:
                if mode=='status':print(json.dumps(doc,ensure_ascii=False,indent=2));return
                for rr in doc.get('receipts',[]):
                    if rr['label'] not in seen:collect_checkpoint(con,rr,out);seen.add(rr['label'])
                print(json.dumps({'state':doc['state'],**doc.get('progress',{})},ensure_ascii=False),flush=True)
                if doc['state']=='COMPLETE':
                    need('summary' in seen,'Summary not backed up')
                    atomic(out/'final-status.json',doc);print(json.dumps(doc['summary'],ensure_ascii=False,indent=2))
                    print('GPU005_PORTABILITY_LOCAL_COPY_VERIFIED target='+target['profile']);return
                if doc['state'] in ('BLOCKED','INTERRUPTED'):
                    atomic(out/'last-status.json',doc);print(json.dumps(doc.get('failure',{}),ensure_ascii=False,indent=2))
                    raise RuntimeError('GPU worker stopped; no automatic candidate/measurement retry')
                need(doc['state']=='RUNNING','Worker is not running')
                if mode=='collect':return
                time.sleep(10);doc=parse(con.run(remote_command('--_status')))
    except KeyboardInterrupt:print('WATCH_CLOSED; reconnect --watch before ACK12h/run24h; Pod billing is separate')
    finally:con.close()


def remote_mode(args):
    target=remote_target();configure_runtime(target)
    if args._numeric:
        need('GPU001_TEST_NVRTC' not in os.environ,'Test override is not permitted remotely')
        return numeric_job(args._numeric)
    if args._worker:worker(target,args.allow_ephemeral_with_local_checkpoints);return 0
    remote_guard()
    if args._launch:
        need(args.allow_ephemeral_with_local_checkpoints,'Missing explicit execution permission')
        print(json.dumps(P.remote_launch(True)));return 0
    if args._status:print(json.dumps(P.remote_status()));return 0
    if args._stop:
        r=parse(read(ROOT/'launch.json'))
        if P.alive(r):os.kill(r['pid'],signal.SIGTERM)
        print('GPU005_OWNED_WORKER_STOP_REQUESTED; NO_FILE_OR_POD_DELETION');return 0
    label=args._send or args._ack[0];need(re.fullmatch(r'[a-z0-9-]+',label),'Invalid checkpoint label')
    rec=parse(read(ROOT/'receipts'/(label+'.json')))
    if args._send:
        p=ROOT/'archives'/(label+'.tar.gz');need(hfile(p)==rec['sha256'],'Remote checkpoint changed')
        with p.open('rb') as f:shutil.copyfileobj(f,sys.stdout.buffer,MIB)
    else:
        need(args._ack[1]==rec['sha256'],'ACK hash differs');p=ROOT/'acks'/(label+'.json');obj={'sha256':rec['sha256']}
        if p.exists():need(parse(read(p))==obj,'ACK conflict')
        else:jw(p,obj)
        print('ACK_STORED')
    return 0


# Synthetic fixtures are used only by --self-test; no synthetic measurements enter an exported experiment.
def _fixture():
    real=read_archive(base64.b64decode(PRIMARY_SUMMARY_B64),PRIMARY_RECEIPT)
    plan=parse(real['protocol.json']);orig={t:source_files()['sources/'+t+'.cu'].decode() for t in C.TASKS}
    all_out=[];raws={}
    for g in plan['groups']:
        files={}
        for r in g['requests']:
            failed=r['provider']=='anthropic' and r['task']=='syrk'
            block=C.SPECS[r['task']]['base'];text='INVALID JSON\n'+orig[r['task']] if failed else json.dumps({'block':block})+'\n'+orig[r['task']]
            rec={k:r[k] for k in ('id','provider','task','condition','trial','seed','seed_sent_to_provider','messages_sha256')}
            rec.update(model=plan['config']['models'][r['provider']]['id'],generation_status='invalid_generation' if failed else 'saved',
                       error='Invalid JSON block header' if failed else None)
            if not failed:rec.update(source_sha256=sha(orig[r['task']].encode()),source_equals_original=True,block=block)
            o={**rec,'correctness_passed':not failed,'stage':'generation_failed' if failed else 'measured','measurements':[]}
            all_out.append(o);p=r['condition']+'/'
            if r['provider']=='qwen':
                response={'truncated':False,'stop_type':'eos','content':text,'tokens_evaluated':2,'timings':{'predicted_n':25}}
                files[p+'wire-request.json']=canon({'prompt':[1,2]})
            elif r['provider']=='openai':
                response={'model':rec['model'],'status':'completed','output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':text}]}]}
            else:response={'model':rec['model'],'type':'message','stop_reason':'end_turn','content':[{'type':'text','text':text}]}
            files[p+'request.json']=canon(r);files[p+'record.json']=canon(rec);files[p+'response.json']=canon(response)
            if r['provider']!='qwen':
                files[p+'api-package.json']=canon({'provider':r['provider'],'batch_only':True,'envelope':{'http_status':200,'raw_body_b64':base64.b64encode(canon(response)).decode()}})
            if not failed:files[p+'candidate.cu']=orig[r['task']].encode()
        lab='generation-'+g['label'];raws[lab]=make_archive(files,lab)
    summary,rec=make_archive({'protocol.json':canon(plan),'outcomes.json':canon(all_out),'summary.json':canon({'fixture_only':True})},'summary')
    return summary,rec,raws


def self_test():
    class T(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.real_receipt=copy.deepcopy(PRIMARY_RECEIPT)
            cls.fixture_summary,cls.fixture_rec,cls.fixture_archives=_fixture()
        def setUp(self):
            self.tmp=tempfile.TemporaryDirectory(prefix='gpu005-tests-');self.base=Path(self.tmp.name)
        def tearDown(self):self.tmp.cleanup()
        def fixture_context(self):return mock.patch.dict(globals(),{'PRIMARY_RECEIPT':self.fixture_rec})
        def payload(self):
            with self.fixture_context():return build_payload(self.fixture_summary,self.fixture_rec,self.fixture_archives)
        def test_real_primary_archive_pin(self):
            f=read_archive(base64.b64decode(PRIMARY_SUMMARY_B64),self.real_receipt)
            self.assertEqual(len(parse(f['outcomes.json'])),90)
        def test_real_primary_85_5_split(self):
            plan,outs,orig=primary_data(base64.b64decode(PRIMARY_SUMMARY_B64),self.real_receipt)
            self.assertEqual(sum(o['generation_status']=='saved' for o in outs),85);self.assertEqual(len(orig),6)
        def test_source_original_blob_pins(self):self.assertEqual(len(source_files()),22)
        def test_core_sha(self):self.assertEqual(sha(gzip.decompress(base64.b64decode(CORE_EMBED))),CORE_SHA)
        def test_archive_roundtrip(self):
            b,r=make_archive({'a/b.json':b'{}'},'test');self.assertEqual(read_archive(b,r),{'a/b.json':b'{}'})
        def test_archive_bad_hash(self):
            b,r=make_archive({'a':b'x'},'test');r['sha256']='0'*64
            with self.assertRaises(RuntimeError):read_archive(b,r)
        def test_archive_bad_manifest(self):
            b,r=make_archive({'a':b'x'},'test');r['manifest_sha256']='0'*64
            with self.assertRaises(RuntimeError):read_archive(b,r)
        def test_archive_bad_count(self):
            b,r=make_archive({'a':b'x'},'test');r['files']=2
            with self.assertRaises(RuntimeError):read_archive(b,r)
        def test_gzip_trailer(self):
            b,r=make_archive({'a':b'x'},'test');b=b[:-8]+bytes([b[-8]^1])+b[-7:];r['sha256']=sha(b)
            with self.assertRaises((OSError,EOFError,RuntimeError)):read_archive(b,r)
        def test_traversal(self):
            for s in ('../x','/x','a//b','a/./b','a\\b'):
                with self.assertRaises(RuntimeError):pathname(s)
        def test_link_refused(self):
            b=io.BytesIO()
            with tarfile.open(fileobj=b,mode='w:gz') as tf:
                m=tarfile.TarInfo('link');m.type=tarfile.SYMTYPE;m.linkname='/etc/passwd';tf.addfile(m)
            raw=b.getvalue();r={'bytes':len(raw),'sha256':sha(raw)}
            with self.assertRaises(RuntimeError):read_archive(raw,r)
        def test_duplicate_tar_refused(self):
            b=io.BytesIO()
            with tarfile.open(fileobj=b,mode='w:gz') as tf:
                for _ in range(2):m=tarfile.TarInfo('a');m.size=1;tf.addfile(m,io.BytesIO(b'x'))
            raw=b.getvalue()
            with self.assertRaises(RuntimeError):read_archive(raw,{'bytes':len(raw),'sha256':sha(raw)})
        def test_duplicate_json_refused(self):
            with self.assertRaises(RuntimeError):parse('{"a":1,"a":2}')
        def test_nonfinite_json_refused(self):
            with self.assertRaises(RuntimeError):parse('{"a":NaN}')
        def test_no_overwrite(self):
            p=self.base/'file';save(p,b'a')
            with self.assertRaises(FileExistsError):save(p,b'b')
            self.assertEqual(read(p),b'a')
        def test_symlink_refused(self):
            p=self.base/'link';p.symlink_to(self.base/'other')
            with self.assertRaises(RuntimeError):read(p)
        def original(self):return {t:source_files()['sources/'+t+'.cu'].decode() for t in C.TASKS}
        def test_parser_valid_header(self):
            orig=self.original();s,b=parse_candidate('{"block":[64,4]}\n'+orig['gemm'],'gemm',orig)
            self.assertEqual(s,orig['gemm']);self.assertEqual(b,[64,4])
        def test_parser_boolean_block_refused(self):
            with self.assertRaises(P.NumericFailure):parse_candidate('{"block":[true,4]}\n'+self.original()['gemm'],'gemm',self.original())
        def test_parser_unknown_block(self):
            with self.assertRaises(P.NumericFailure):parse_candidate('{"block":[1,1]}\n'+self.original()['gemm'],'gemm',self.original())
        def test_parser_no_repair(self):
            for prefix in ('// BLOCK X Y, (64, 4)','{\n"block":[64,4]\n}'):
                with self.assertRaises(P.NumericFailure):parse_candidate(prefix+'\n'+self.original()['gemm'],'gemm',self.original())
        def test_parser_header_extra_field(self):
            with self.assertRaises(P.NumericFailure):parse_candidate('{"block":[64,4],"x":0}\n'+self.original()['gemm'],'gemm',self.original())
        def test_original_failure_record_stays_failure(self):
            payload,man=self.payload();bad=[e for e in man['entries'] if not e['eligible']]
            self.assertEqual(len(bad),5);self.assertTrue(all(e['replayed_error']=='Invalid JSON block header' for e in bad))
        def test_all_saved_85_included(self):
            payload,man=self.payload();self.assertEqual(sum(n.startswith('candidates/') for n in payload),85)
        def test_no_candidate_selection_on_speed(self):
            _,man=self.payload();self.assertEqual(Counter(e['provider'] for e in man['entries'] if e['eligible']),{'qwen':30,'openai':30,'anthropic':25})
        def test_full_bundle_replay(self):
            with self.fixture_context():
                f,m=build_payload(self.fixture_summary,self.fixture_rec,self.fixture_archives)
                b,r=make_archive(f,'portable-inputs');ff,mm=bundle_data(b,r);self.assertEqual(ff,f);self.assertEqual(mm,m)
        def test_candidate_tamper_blocks(self):
            with self.fixture_context():
                f,m=build_payload(self.fixture_summary,self.fixture_rec,self.fixture_archives)
                name=next(n for n in f if n.startswith('candidates/'));f[name]+=b'\n'
                b,r=make_archive(f,'portable-inputs')
                with self.assertRaises(RuntimeError):bundle_data(b,r)
        def test_response_tamper_blocks(self):
            a=copy.deepcopy(self.fixture_archives);label=next(iter(a));f=read_archive(*a[label]);name=next(n for n in f if n.endswith('/response.json'))
            o=parse(f[name]);o['tokens_evaluated']=0;f[name]=canon(o);a[label]=make_archive(f,label)
            with self.fixture_context(),self.assertRaises(RuntimeError):build_payload(self.fixture_summary,self.fixture_rec,a)
        def test_missing_generation_blocks(self):
            a=self.fixture_archives.copy();a.pop(next(iter(a)))
            with self.fixture_context(),self.assertRaises(RuntimeError):build_payload(self.fixture_summary,self.fixture_rec,a)
        def test_wrong_summary_refused(self):
            with self.assertRaises(RuntimeError):primary_data(self.fixture_summary,self.fixture_rec)
        def test_prepare_no_network_idempotent(self):
            src=self.base/'source';out=self.base/'prepared';src.mkdir()
            save(src/'summary.tar.gz',self.fixture_summary);jw(src/'summary-receipt.json',self.fixture_rec)
            for lab,(b,r) in self.fixture_archives.items():save(src/(lab+'.tar.gz'),b);jw(src/(lab+'-receipt.json'),r)
            before={p.name:hfile(p) for p in src.iterdir()}
            with self.fixture_context(),mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess permitted in prepare')),contextlib.redirect_stdout(io.StringIO()):
                prepare(src,out);prepare(src,out)
            self.assertEqual(before,{p.name:hfile(p) for p in src.iterdir()})
            self.assertEqual(parse(read(out/'preparation.json'))['ssh_connections'],0)
        def test_target_has_no_guessed_l4_endpoint(self):
            self.assertNotIn('L4',A40_ENDPOINT.values())
        def test_target_validation(self):validate_target({'schema':VERSION,**A40_ENDPOINT})
        def test_target_injection_refused(self):
            for h in ('root@host','host;touch/tmp/a','-oProxyCommand=x','a b',''):
                with self.assertRaises(RuntimeError):validate_target({'schema':VERSION,**A40_ENDPOINT,'host':h})
        def test_missing_fingerprint_refused(self):
            with self.assertRaises(RuntimeError):validate_target({'schema':VERSION,**A40_ENDPOINT,'host_fingerprint':''})
        def test_unpinned_run_refused(self):
            with self.assertRaises(RuntimeError):validate_target({'schema':VERSION,**A40_ENDPOINT},True)
        def test_target_architecture_options(self):
            for label,arch in [('A40','sm_86'),('L4','sm_89')]:
                t=self.target(label);configure_runtime(t,self.base/'run')
                self.assertEqual(P.NVRTC_OPTIONS[0],'--gpu-architecture='+arch)
                self.assertEqual(P.NVRTC_OPTIONS[1:],FROZEN_OPTIONS[1:])
        def target(self,label='A40'):
            return {'schema':VERSION,**A40_ENDPOINT,'profile':label,'runtime_identity':{'gpu_uuid':A40_ENDPOINT['expected_gpu_uuid'],
                'sanitizer_path':'/nonexistent/fake-sanitizer','sanitizer_sha256':'0'*64,'gpu':PROFILES[label]}}
        def test_guard_patch_is_one_assertion(self):
            p=patch_cuda_guard(PROFILES['L4']);self.assertNotEqual(p['original_method_sha256'],p['target_bound_method_sha256'])
            self.assertEqual(P.GPU005_EXPECTED_CC,[8,9]);self.assertEqual(P.GPU005_EXPECTED_NAME,'NVIDIA L4')
        def test_cuda_guard_accepts_only_selected_profile(self):
            for accepted in (True,False):
                label='NVIDIA L4' if accepted else 'NVIDIA A40';cc=[8,9] if accepted else [8,6]
                patch_cuda_guard(PROFILES['L4']);ctx=[]
                def fake_bind(lib,name,args,ret=ct.c_int):
                    def f(*a):
                        if name=='cuDeviceGetName':a[0].value=label.encode()
                        elif name=='cuDeviceComputeCapability':a[0]._obj.value=cc[0];a[1]._obj.value=cc[1]
                        elif name=='cuDeviceTotalMem_v2':a[0]._obj.value=24*1024**3
                        elif name=='cuDeviceGetAttribute':a[0]._obj.value=1024
                        elif name=='cuCtxCreate_v2':a[0]._obj.value=1;ctx.append(1)
                        return 0
                    return f
                with mock.patch.object(P,'bind',side_effect=fake_bind),mock.patch.object(P.ct,'CDLL',return_value=object()):
                    if accepted:self.assertEqual(P.CUDA().info['name'],label);self.assertEqual(ctx,[1])
                    else:
                        with self.assertRaises(P.NumericFailure):P.CUDA()
                        self.assertEqual(ctx,[])
        def test_generation_path_disabled(self):
            configure_runtime(self.target(),self.base/'run')
            for fn in (P.module_a,P.start_model,P.generate_group,C.generate_group):
                with self.assertRaises(RuntimeError):fn()
        def test_clean_env_does_not_forward_api_keys(self):
            configure_runtime(self.target(),self.base/'run')
            with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'secret','ANTHROPIC_API_KEY':'secret'}):
                self.assertNotIn('OPENAI_API_KEY',P.clean_env());self.assertNotIn('ANTHROPIC_API_KEY',P.clean_env())
        def test_sanitizer_pin_not_path_lookup(self):
            p=self.base/'san';save(p,b'fixture');t=self.target();t['runtime_identity'].update(sanitizer_path=str(p),sanitizer_sha256=sha(b'fixture'))
            configure_runtime(t,self.base/'run');self.assertEqual(P.sanitizer_path(),str(p))
            p.write_bytes(b'changed')
            with self.assertRaises(RuntimeError):P.sanitizer_path()
        def test_environment_recheck_uses_absolute_sanitizer(self):
            t=self.target();calls=[]
            def inv(*args):
                calls.append(args);return {'identity':t['runtime_identity'],'free_disk_bytes':8*1024**3}
            with mock.patch.dict(globals(),{'inventory':inv}):check_runtime(t)
            self.assertEqual(calls[0][3],t['runtime_identity']['sanitizer_path'])
        def test_inventory_explicit_sanitizer_precedes_path_fallback(self):
            text=function_source(inventory)
            self.assertIn('if sanitizer_absolute is not None:',text)
            self.assertIn('sanitizer=pinned',text)
            self.assertLess(text.index('sanitizer=pinned'),text.index('sanver=command'))
        def test_schedule_176(self):
            _,m=self.payload();p=schedule(m)
            self.assertEqual(sum(len(x['blocks'])*len(x['shapes']) for x in p['passes']),176)
            self.assertEqual(len(p['candidate_groups']),18)
        def rows(self):
            return [{'phase':'exploration','task':t,'block':list(b),'shape':list(s),'measurement_valid':True,'speedup':1+(i/100)}
              for t in C.TASKS for i,b in enumerate(C.allowed_blocks(t)) for s in C.SPECS[t]['perf']]
        def test_selection_exploration_only(self):
            _,m=self.payload();r=self.rows();r[0]['phase']='confirmation'
            with self.assertRaises(RuntimeError):select_exploration(r,schedule(m))
        def test_selection_tie_uses_original_order(self):
            _,m=self.payload();r=self.rows()
            for row in r:row['speedup']=1
            s=select_exploration(r,schedule(m))
            self.assertTrue(all(s[t]['selected_block']==list(C.allowed_blocks(t)[0]) for t in C.TASKS))
        def test_selection_invalid_excluded(self):
            _,m=self.payload();r=self.rows()
            for row in r:
                if tuple(row['block'])==C.allowed_blocks(row['task'])[-1]:row['measurement_valid']=False
            s=select_exploration(r,schedule(m))
            self.assertTrue(all(s[t]['selected_block']==list(C.allowed_blocks(t)[-2]) for t in C.TASKS))
        def test_no_selection_when_all_invalid(self):
            _,m=self.payload();r=self.rows()
            for row in r:row['measurement_valid']=False
            self.assertTrue(all(v['selected_block'] is None for v in select_exploration(r,schedule(m)).values()))
        def test_reference_block_time_only(self):
            configure_runtime(self.target(),self.base/'run');p=self.base/'job';jw(p,{'mode':'compile','task':'gemm','reference_block':[64,4]})
            with self.assertRaises(RuntimeError):numeric_job(p)
        def test_reference_block_selected_and_restored(self):
            configure_runtime(self.target(),self.base/'run');jw(ROOT/'selection/selection.json',{'gemm':{'selected_block':[64,4]}})
            p=self.base/'job';jw(p,{'mode':'time','task':'gemm','reference_block':[64,4]})
            old=C.SPECS['gemm']['base'];seen=[]
            with mock.patch.dict(globals(),{'FROZEN_NUMERIC_JOB':lambda path:seen.append(C.SPECS['gemm']['base']) or 0}):self.assertEqual(numeric_job(p),0)
            self.assertEqual(seen,[[64,4]]);self.assertEqual(C.SPECS['gemm']['base'],old)
        def test_reference_block_wrong_selection_refused(self):
            configure_runtime(self.target(),self.base/'run');jw(ROOT/'selection/selection.json',{'gemm':{'selected_block':[64,4]}})
            p=self.base/'job';jw(p,{'mode':'time','task':'gemm','reference_block':[16,16]})
            with self.assertRaises(RuntimeError):numeric_job(p)
        def test_numeric_wrapper_records_reference_launch(self):
            configure_runtime(self.target(),self.base/'run');base=self.base/'base.cubin';helper=self.base/'helper.so'
            save(base,b'object');save(helper,b'helper');dest=ROOT/'case'
            rows=[{'session':s,'pair':p,'ratio':1.0,'baseline_ms':1.,'candidate_ms':1.,'repeats':1,'order':[0,1]}
                  for s in range(2) for p in range(8)]
            def run_command(argv,log,timeout):
                j=parse(read(dest/'job.json'))
                self.assertEqual(j['reference_block'],[64,4]);self.assertEqual(j['block'],[32,8])
                self.assertEqual(j['baseline_sha256'],sha(b'object'))
                self.assertIn('--_numeric',argv)
                jw(dest/'numeric-result.json',{'ok':True,'rows':rows});save(log,b'fixture child log');return 0
            with mock.patch.object(P,'command',side_effect=run_command),mock.patch.object(os,'chown',return_value=None):
                res=numeric('gemm',(128,128,128),dest,'time',cubin=base,baseline=base,helper=helper,block=[32,8],baseline_block=[64,4])
            self.assertTrue(res['ok']);self.assertTrue((dest/'parent-result.json').is_file())
        def test_installation_whitelist(self):
            code=installation_code('0'*64);self.assertIn("'control/target.json'",code);self.assertNotIn('extractall',code);compile(code,'installer','exec')
        def test_inventory_standalone_compiles(self):
            code=function_source(inventory)+'\n';compile(code,'inventory','exec')
        def test_host_fingerprint_failure_never_authenticates(self):
            r=subprocess.CompletedProcess([],0,b'host ssh-ed25519 AAAA\n',b'')
            p=self.base/'key';save(p,b'not a key')
            with mock.patch.object(subprocess,'run',return_value=r) as fn:
                with self.assertRaises(RuntimeError):Connection({'schema':VERSION,**A40_ENDPOINT},p)
                self.assertEqual(fn.call_count,1);self.assertEqual(fn.call_args.args[0][0],'ssh-keyscan')
        def test_full_mock_worker_85_candidates_516_cells(self):
            target=self.target();configure_runtime(target,self.base/'run');P.STATE={};C.BASES.clear()
            f,m=self.payload();b,r=make_archive(f,'portable-inputs')
            save(ROOT/'inputs/portable-inputs.tar.gz',b);jw(ROOT/'inputs/portable-inputs-receipt.json',r)
            copied=self.base/'copied';copied.mkdir();checkpoint_labels=[];numeric_calls=[]
            def check_runtime_mock(t):return {'identity':t['runtime_identity'],'free_disk_bytes':10*1024**3}
            def build_helper_mock():
                p=ROOT/'setup/helper.so';save(p,b'fixture-helper');return p
            def numeric_mock(task,sh,dest,mode,**kw):
                d=Path(dest);d.mkdir(parents=True,exist_ok=False);numeric_calls.append((task,mode,kw.get('baseline_block')))
                if mode=='compile':
                    src=kw['source'].encode();save(d/'kernel.cubin',src);save(d/'kernel.ptx',src)
                    return {'ok':True,'cubin_sha256':sha(src),'ptx_sha256':sha(src)}
                value=1.0 if 'identity' in str(d) else 1.0+min(0.1,(kw['block'][0]/max(1,kw['block'][1]))*0.0001)
                rows=[{'session':s,'pair':p,'ratio':value,'baseline_ms':value,'candidate_ms':1,'repeats':1,'order':[0,1]}
                      for s in range(2) for p in range(8)]
                jw(d/'numeric-result.json',{'ok':True,'rows':rows});return {'ok':True,'rows':rows}
            def preflight_mock(helper):
                for t in C.TASKS:
                    for sh in C.shapes(t):
                        d=ROOT/'preflight'/t/C.shape_id(sh)
                        base=d/'baseline/kernel.cubin';twin=d/'identity/kernel.cubin'
                        for p in (base,twin):save(p,source_files()['sources/'+t+'.cu']);save(p.with_suffix('.ptx'),read(p))
                        C.BASES[t,sh]=(base,twin)
            def ack_mock(rec):
                lab=rec['label'];raw=read(ROOT/'archives'/(lab+'.tar.gz'));read_archive(raw,rec)
                save(copied/(lab+'.tar.gz'),raw);jw(ROOT/'acks'/(lab+'.json'),{'sha256':rec['sha256']});checkpoint_labels.append(lab)
            real_lock=P.lock
            with self.fixture_context(),mock.patch.dict(globals(),{'remote_guard':lambda:None,'check_runtime':check_runtime_mock,'wait_ack':ack_mock}),\
                 mock.patch.object(P,'lock',side_effect=lambda path:real_lock(self.base/'mock-exclusive.lock')),\
                 mock.patch.object(P,'no_other_gpu',lambda:None),mock.patch.object(P,'telemetry',return_value={'fixture_only':True}),\
                 mock.patch.object(C,'build_helper',side_effect=build_helper_mock),mock.patch.object(C,'baseline_preflight',side_effect=preflight_mock),\
                 mock.patch.object(C,'validate_object',return_value={'passed':True,'fixture_only':True}),mock.patch.object(C,'numeric',side_effect=numeric_mock),\
                 contextlib.redirect_stdout(io.StringIO()):
                worker(target,True)
            s=parse(read(ROOT/'final/summary.json'));out=parse(read(ROOT/'final/outcomes.json'));controls=parse(read(ROOT/'final/controls.json'))
            self.assertEqual(sum(o['correctness_passed'] for o in out),85)
            self.assertEqual(sum(len(o['measurements']) for o in out),170)
            self.assertEqual(sum(len(o['tuned_measurements']) for o in out),170)
            self.assertEqual(len(controls),176);self.assertEqual(s['new_generation_calls'],0)
            self.assertEqual(len(checkpoint_labels),35);self.assertEqual(checkpoint_labels[-1],'summary')
            self.assertEqual(hfile(ROOT/'inputs/portable-inputs.tar.gz'),r['sha256'])
            self.assertTrue((ROOT/'completion.json').is_file())
            self.assertEqual(sum(o.get('target_not_evaluated_original_invalid',False) for o in out),5)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    need(result.wasSuccessful(),'GPU005 self-test failed')
    print('GPU005_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=REAL_RECORDED_SUMMARY_AND_ORIGINAL_SOURCES; SYNTHETIC_90_RESPONSES; MOCK_A40_L4_AND_FULL_WORKER; NO_REAL_SSH_NVRTC_SANITIZER_GPU_OR_PROVIDER_API')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    a=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','configure-target','probe','run','watch','status','collect','stop','self-test','numeric-core-self-test',
              '_launch','_worker','_status','_stop'):a.add_argument('--'+n,action='store_true')
    a.add_argument('--_numeric');a.add_argument('--_send');a.add_argument('--_ack',nargs=2)
    p.add_argument('--source-dir',type=Path,default=Path.home()/SOURCE_REL)
    p.add_argument('--prepared-dir',type=Path,default=Path.home()/PREP_REL)
    p.add_argument('--target',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--profile',choices=tuple(PROFILES));p.add_argument('--host');p.add_argument('--port',type=int)
    p.add_argument('--host-fingerprint');p.add_argument('--gpu-uuid')
    p.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true')
    args=p.parse_args()
    if args.self_test:self_test();return 0
    if args.numeric_core_self_test:C.self_test();return 0
    if any((args._worker,args._launch,args._status,args._stop,args._numeric,args._send,args._ack)):return remote_mode(args)
    if args.prepare:prepare(args.source_dir,args.prepared_dir);return 0
    if args.configure_target:
        need(args.profile and args.output,'--profile and --output are required')
        configure_target(args.profile,args.output,args.host,args.port,args.host_fingerprint,args.gpu_uuid);return 0
    need(args.target,'An explicit --target JSON file is required')
    if args.probe:probe_target(args.target,args.output);return 0
    mode=next(n for n in ('run','watch','status','collect','stop') if getattr(args,n))
    local_run(mode,args.target,args.prepared_dir,args.allow_ephemeral_with_local_checkpoints);return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (Exception,KeyboardInterrupt) as e:
        print('GPU005_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr)
        print('NO_AUTOMATIC_GENERATION_RETRY; NO_PRIOR_RESULT_OVERWRITE; NO_POD_TERMINATION',file=sys.stderr)
        sys.exit(2)
