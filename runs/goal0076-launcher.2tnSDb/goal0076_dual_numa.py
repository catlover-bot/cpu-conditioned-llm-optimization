#!/usr/bin/env python3
"""Phase-boundary dual-NUMA generation for the existing P0 -> P1 -> P2 campaign.
P0 and in-flight requests are never interrupted. Only the WAITING_FOR_P0 chain
manager is replaced. After P0 evaluation finishes, two independent inference
workers produce disjoint, paired P1/P2 tasks. Original validators are reused.
No downloads, no prompt edits, no model resubmission, no aggregate deadline.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import fcntl
import functools
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import pwd
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path('/srv/research/cpucond-p012-zen2-v1')
P0 = Path('/srv/research/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent')
CONTROL = ROOT / 'dual-numa-v1'
HOME = Path('/var/lib/cpucond-infer')
MODEL_STORE = HOME / '.local/share/cpucond-ollama/models'
SECOND_STORE = HOME / 'goal0076-node1-models'
ORIGINAL_CHAIN_SHA = '695886fbba299782ad3b8eb603950ddc7f6297283ca45aeca9fbf53f1535d675'
PIPELINE_SHA = 'f3f5162024bd914383efc152d16e80719930ccf3663c295bcc9589ad2e4af20b'
MODEL_DIGEST = 'b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41'
MANIFEST_REL = 'manifests/registry.ollama.ai/library/qwen2.5-coder/32b-instruct-q4_K_M'
LIVE = {'active', 'activating', 'deactivating', 'reloading'}

class Refuse(RuntimeError): pass

def need(ok, message):
    if not ok: raise Refuse(message)

def utc(): return datetime.now(timezone.utc).isoformat()
def enc(x): return (json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
def decode(raw):
    def pairs(items):
        out = {}
        for k,v in items:
            need(k not in out, 'duplicate JSON key'); out[k] = v
        return out
    def bad(x): raise Refuse('nonfinite JSON: '+x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)
def read(p):
    p=Path(p); need(p.is_file() and not p.is_symlink(), 'not a regular file: '+str(p))
    need(p.stat().st_size < 64*1024**2, 'oversize metadata')
    return p.read_bytes()
def load(p): return decode(read(p))
def sha(p):
    p=Path(p); need(p.is_file() and not p.is_symlink(), 'not a regular file: '+str(p))
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()
def atomic(p,x,exclusive=False,raw=False):
    """Publish a complete record atomically; exclusive publication never overwrites."""
    p=Path(p); need(not p.is_symlink(), 'symlink output')
    p.parent.mkdir(parents=True,exist_ok=True)
    data=x if raw else enc(x)
    if isinstance(data,str): data=data.encode()
    tmp=p.with_name(p.name+'.tmp76-'+uuid.uuid4().hex)
    try:
        with tmp.open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        if exclusive: os.link(tmp,p)
        else: os.replace(tmp,p)
    finally:
        tmp.unlink(missing_ok=True)
def record(p,x): atomic(p,x,exclusive=True)
def cmd(argv,timeout=60,**kw):
    return subprocess.run(list(map(str,argv)),check=True,timeout=timeout,**kw)
def unit_props(unit,keys=('ActiveState','SubState','MainPID','ControlGroup','PartOf')):
    need(re.fullmatch(r'cpucond\d+-[A-Za-z0-9-]+\.service',unit), 'unsafe unit')
    r=subprocess.run(['systemctl','show',unit,*sum((['-p',k] for k in keys),[])],
                     capture_output=True,text=True,timeout=15)
    if r.returncode:
        need('not found' in r.stderr.lower() or 'could not be found' in r.stderr.lower(),r.stderr[:500])
        return {'ActiveState':'inactive','MainPID':'0'}
    return dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
def import_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module)
    return module

def load_chain():
    path=ROOT/'control/goal0075_p012_chain.py'
    need(sha(path)==ORIGINAL_CHAIN_SHA,'existing chain differs')
    need(sha(ROOT/'control/finish74/until_complete_pipeline.py')==PIPELINE_SHA,'existing pipeline differs')
    return import_file('cpucond76_unchanged_chain',path)

def cpu_list(value):
    out=set()
    for part in value.strip().split(','):
        need(re.fullmatch(r'\d+(?:-\d+)?',part),'invalid CPU list')
        x=list(map(int,part.split('-'))); a,b=x[0],x[-1]
        need(0<=a<=b<65536,'invalid CPU range'); out.update(range(a,b+1))
    return sorted(out)

def topology(syscpu=Path('/sys/devices/system/cpu')):
    online=cpu_list((syscpu/'online').read_text()); workers=[]
    for i,cpus in enumerate((list(range(2,18)), list(range(26,42)))):
        rows=[]
        for n in cpus:
            need(n in online,'required inference CPU is offline')
            p=syscpu/f'cpu{n}'
            s=int((p/'topology/physical_package_id').read_text())
            core=int((p/'topology/core_id').read_text())
            nodes=[int(v.name[4:]) for v in p.glob('node[0-9]*') if re.fullmatch(r'node\d+',v.name)]
            need(s==i and nodes==[i],'CPU/socket/NUMA mapping differs')
            rows.append((s,core))
        need(len(set(rows))==16,'not 16 different physical cores')
        workers.append({'worker':i,'cpus':cpus,'node':i,'socket':i,
                        'threads_per_request':16,'port':11480+i,
                        'models':str(MODEL_STORE if i==0 else SECOND_STORE)})
    need(not set(workers[0]['cpus']) & set(workers[1]['cpus']),'worker CPU overlap')
    return workers

def assignments(plan):
    need(len(plan['tasks'])==180,'expected 180 condition requests')
    keys=sorted({(t['task'],t['size']) for t in plan['tasks']})
    need(len(keys)==90,'expected 90 instances')
    pos={key:i%2 for i,key in enumerate(keys)}
    out={0:[],1:[]}; seen=set()
    for t in plan['tasks']:
        need(t['id'] not in seen,'duplicate task'); seen.add(t['id'])
        need(t['form'] in ('C','IR'),'unknown form')
        out[pos[(t['task'],t['size'])]].append(t['id'])
    need(len(out[0])==90 and len(out[1])==90,'unbalanced fixed partition')
    return out

def host():
    need(os.geteuid()==0,'server administrator required')
    need(socket.gethostname()=='cpucond-zen2-01','wrong server')
    need('AMD EPYC 7402' in Path('/proc/cpuinfo').read_text(),'wrong CPU')

def new_status(phase,**kw):
    atomic(CONTROL/'status.json',{'phase':phase,'utc':utc(),
          'aggregate_time_limit_seconds':None,**kw})

def validate_config(c):
    campaign=c.verify_installed(ROOT)
    cfg=load(CONTROL/'config.json')
    need(cfg['workers']==topology(),'topology changed')
    for con in ('P1','P2'):
        work=ROOT/con/'work'; plan=load(work/'plan.json')
        need(sha(work/'plan.json')==cfg['plan_hashes'][con]==campaign['plans_sha256'][con],'plan changed')
        need({str(k):v for k,v in assignments(plan).items()}==cfg['assignments'][con],'assignments changed')
    need(sha(CONTROL/'goal0076_dual_numa.py')==cfg['adapter_sha256'],'adapter changed')
    return cfg

def has_generation(job):
    g=job/'results/generation'
    return g.exists() and any(p.is_file() for p in g.rglob('*'))

def stage_unstarted(c):
    for con in ('P1','P2'):
        job=ROOT/con; marker=job/'active-unit.txt'
        if marker.exists():
            need(unit_props(read(marker).decode().strip())['ActiveState'] not in LIVE, con+' already active')
        need(not has_generation(job),con+' already has request records; do not migrate automatically')

def wait_stopped(pid, seconds=3):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        text=(Path('/proc')/str(pid)/'status').read_text()
        state=next(x for x in text.splitlines() if x.startswith('State:')).split()[1]
        if state in ('T','t'): return
        time.sleep(.02)
    raise Refuse('waiting chain did not suspend for handover')

def enable():
    host(); c=load_chain(); campaign=c.verify_installed(ROOT)
    CONTROL.mkdir(exist_ok=True)
    with open('/var/lock/cpucond-dual76-install.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        marker=CONTROL/'active-unit.txt'
        if marker.exists() and unit_props(read(marker).decode().strip())['ActiveState'] in LIVE:
            need((CONTROL/'approved.json').exists(),'handover incomplete; inspect status before repeating')
            print('DUAL_NUMA_ALREADY_RUNNING',flush=True);return
        if (CONTROL/'approved.json').exists():
            raise Refuse('a previous dual controller ended; inspect errors before restarting')
        stage_unstarted(c)
        observed=topology(); c.capture_hardware()
        cfg={'revision':'dual-numa-p12-v1','workers':observed,
             'plan_hashes':campaign['plans_sha256'],
             'assignments':{con:{str(k):v for k,v in assignments(load(ROOT/con/'work/plan.json')).items()} for con in ('P1','P2')},
             'p0_execution_unchanged':True,'p0_interrupted':False,'model_prompt_options_unchanged':True,
             'evaluation_original_single_cpu_2':True,'generated_output_identity_not_guaranteed_by_seed':True,
             'generation_runtime_mode_differs_from_p0':True,
             'adapter_sha256':sha(Path(__file__)),
             'additional_model_storage_bytes_approx':20_000_000_000,
             'installation_utc':utc()}
        if not (CONTROL/'config.json').exists():
            atomic(CONTROL/'goal0076_dual_numa.py',read(Path(__file__)),exclusive=True,raw=True)
            record(CONTROL/'config.json',cfg)
        else:
            old=load(CONTROL/'config.json');cfg['installation_utc']=old['installation_utc']
            need(old==cfg,'previous configuration differs')
        # The new manager starts in a wait-only state. It cannot issue model calls
        # until approved.json exists. This makes a partial installation fail closed.
        unit='cpucond75-p012-dual76-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.service'
        atomic(marker,unit+'\n',raw=True)
        cmd(['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
             '--property=RuntimeMaxSec=infinity','--property=MemoryMax=512M','--property=TasksMax=32',
             '--property=CPUAffinity=24','--property=Nice=19',
             '--property=TimeoutStopSec=20','--property=KillMode=control-group',
             '--property=StandardOutput=append:'+str(CONTROL/'manager.log'),
             '--property=StandardError=append:'+str(CONTROL/'manager.log'),
             '--setenv=CPUCOND_CHAIN_UNIT='+unit,'--setenv=PYTHONDONTWRITEBYTECODE=1',
             '/usr/bin/python3','-B','-u',str(CONTROL/'goal0076_dual_numa.py'),'--chain-worker'],stdin=subprocess.DEVNULL)
        ready=False
        for _ in range(60):
            if (CONTROL/'status.json').is_file():
                st=load(CONTROL/'status.json')
                if st.get('unit')==unit and st.get('phase')=='WAITING_FOR_HANDOVER_APPROVAL': ready=True;break
            need(unit_props(unit)['ActiveState'] in LIVE,'new controller failed to start')
            time.sleep(.25)
        need(ready,'new manager did not become ready; old chain not modified')
        old_unit=read(ROOT/'active-unit.txt').decode().strip()
        need(re.fullmatch(r'cpucond75-p012-\d+T\d+-[A-Za-z0-9]+\.service',old_unit),'unexpected original manager name')
        props=unit_props(old_unit); frozen_fd=None; old_stopped=False
        try:
            need(props['ActiveState'] in LIVE,'original chain is not active; inspect before migration')
            pid=int(props['MainPID']);need(pid>1,'original manager PID missing')
            need(old_unit in (Path('/proc')/str(pid)/'cgroup').read_text(),'manager PID/cgroup mismatch')
            args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
            need(b'--chain-worker' in args and str(ROOT/'control/goal0075_p012_chain.py').encode() in args,'not the waiting manager')
            frozen_fd=os.pidfd_open(pid)
            signal.pidfd_send_signal(frozen_fd,signal.SIGSTOP)
            wait_stopped(pid)
            need(load(ROOT/'status.json').get('phase')=='WAITING_FOR_P0','old manager is not waiting for P0')
            stage_unstarted(c)
            p0unit=read(P0/'completion-driven-v1/active-unit.txt').decode().strip()
            need(p0unit not in props.get('PartOf','').split(),'unexpected dependencies')
            p0props=unit_props(p0unit)
            need(old_unit not in p0props.get('PartOf','').split(),'stopping manager would affect P0')
            # No stage unit, queued subprocess, or unrelated dependent can be
            # stopped inadvertently. Requiring one sole PID makes this conservative.
            cg=Path('/sys/fs/cgroup')/props['ControlGroup'].lstrip('/')
            members={int(x) for p in cg.rglob('cgroup.procs') for x in p.read_text().split()}
            need(members=={pid},'old manager has a live child; unfreeze and try later')
            dependents=cmd(['systemctl','show',old_unit,'-p','ConsistsOf','--value'],capture_output=True,text=True).stdout.split()
            need(not dependents,'old manager has dependent stage units; leave them untouched')
            evidence={'utc':utc(),'old_manager_unit':old_unit,'old_manager_pid':pid,
                      'old_manager_state':load(ROOT/'status.json'),'p0_unit':p0unit,'p0_before':p0props,
                      'stopped_process_role':'waiting chain manager only; no P0 process signalled'}
            record(CONTROL/('old-manager-before-'+uuid.uuid4().hex[:8]+'.json'),evidence)
            # systemd sends SIGCONT after its termination signal. The stopped
            # manager cannot advance its Python loop in between our checks.
            cmd(['systemctl','stop',old_unit],timeout=45,stdin=subprocess.DEVNULL)
            old_stopped=True
            if p0props.get('ActiveState') in LIVE:
                after=unit_props(p0unit)
                if after.get('ActiveState') not in LIVE:
                    need(c.summary_exists_complete(P0,166),'P0 ended without complete results during handover')
            record(CONTROL/'approved.json',{'utc':utc(),'old_manager_unit':old_unit,'new_manager_unit':unit,
                   'p0_not_stopped_or_restarted':True,'p1_p2_never_started_at_handover':True})
            atomic(Path('/root/goal0076-current-chain.path'),str(CONTROL)+'\n',raw=True)
        except Exception:
            if frozen_fd is not None and not old_stopped:
                try: signal.pidfd_send_signal(frozen_fd,signal.SIGCONT)
                except ProcessLookupError: pass
            cmd(['systemctl','stop',unit],timeout=45,stdin=subprocess.DEVNULL)
            raise
        finally:
            if frozen_fd is not None: os.close(frozen_fd)
        print('DUAL_NUMA_CHAIN_ENABLED',flush=True)
        print('P0はそのまま継続。P0の検証・計測完了後、P1/P2を2ワーカーで順に生成します。',flush=True)
        print('unit='+unit,flush=True)

def chain_worker():
    host(); c=load_chain(); validate_config(c)
    unit=os.environ.get('CPUCOND_CHAIN_UNIT','')
    need(re.fullmatch(r'cpucond75-p012-dual76-[A-Za-z0-9-]+\.service',unit),'manager unit mismatch')
    need(unit in Path('/proc/self/cgroup').read_text(),'manager cgroup mismatch')
    new_status('WAITING_FOR_HANDOVER_APPROVAL',unit=unit)
    while not (CONTROL/'approved.json').is_file(): time.sleep(.5)
    need(load(CONTROL/'approved.json')['new_manager_unit']==unit,'approval unit mismatch')
    old_stage=c.stage_command
    def stage_command(root,condition,child,parent):
        argv=old_stage(root,condition,child,parent)
        pos=argv.index(str(ROOT/'control/goal0075_p012_chain.py'))
        argv[pos]=str(CONTROL/'goal0076_dual_numa.py')
        return argv
    c.stage_command=stage_command
    c.setstatus=lambda root,phase,**kw:new_status(phase,**kw)
    try:
        # Reuses old sequence, completion checks, legacy-P0 receipt and lock.
        c.orchestrate(ROOT)
        new_status('DUAL_NUMA_ALL_COMPLETE',model_prompt_unchanged=True,
                   p0_sequential_p1_p2_parallel=True,formal_equivalence_proven=False)
    except Exception as e:
        new_status('BLOCKED',error=type(e).__name__+': '+str(e));raise


def ensure_second_store(b,binary,freeze,workers):
    """Create new inodes, not links, for NUMA-local model file pages. No downloads."""
    m=b.vendor('model_support.py');m.DIGEST=freeze['manifest_sha256']
    if SECOND_STORE.exists():
        need(not SECOND_STORE.is_symlink(),'model store is a symlink')
        return m.verify_local_weights(SECOND_STORE)
    manifest=load(MODEL_STORE/MANIFEST_REL)
    descriptors={x['digest']:x for x in [manifest['config'],*manifest['layers']]}
    required=sum(x['size'] for x in descriptors.values())
    need(shutil.disk_usage(HOME).free > required+5*1024**3,'insufficient disk for independent model copy')
    staging=SECOND_STORE.with_name(SECOND_STORE.name+'.pending-'+uuid.uuid4().hex[:6])
    acct=pwd.getpwnam(b.ACCOUNT); staging.mkdir(mode=0o755)
    try:
        paths=[(MODEL_STORE/MANIFEST_REL,Path(MANIFEST_REL))]
        for key,d in descriptors.items():
            need(re.fullmatch('sha256:[0-9a-f]{64}',key),'invalid blob name')
            paths.append((MODEL_STORE/'blobs'/key.replace(':','-'),Path('blobs')/key.replace(':','-')))
        for source,relative in paths:
            need(source.is_file() and not source.is_symlink(),'unsafe source blob')
            dest=staging/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            cmd(['numactl','--physcpubind='+','.join(map(str,workers[1]['cpus'])),'--membind=1',
                 'cp','--reflink=never','--sparse=never','--',source,dest],timeout=1800,stdin=subprocess.DEVNULL)
            need((source.stat().st_dev,source.stat().st_ino)!=(dest.stat().st_dev,dest.stat().st_ino),'model files share inode')
            need(sha(source)==sha(dest),'copied model differs')
            os.chown(dest,acct.pw_uid,acct.pw_gid)
        for path in [staging,*staging.rglob('*')]:
            if path.is_dir(): os.chown(path,acct.pw_uid,acct.pw_gid);os.chmod(path,0o755)
        staging.rename(SECOND_STORE)
    except Exception:
        shutil.rmtree(staging,ignore_errors=True);raise
    return m.verify_local_weights(SECOND_STORE)


def worker_service_command(binary,b,config):
    return ['runuser','-u',b.ACCOUNT,'--','env','-i',f'HOME={b.HOME}', 'PATH=/usr/bin:/bin',
            'LC_ALL=C.UTF-8','OLLAMA_NO_CLOUD=1',f'OLLAMA_HOST=127.0.0.1:{config["port"]}',
            'OLLAMA_MODELS='+config['models'],'OLLAMA_NUM_PARALLEL=1','OLLAMA_MAX_LOADED_MODELS=1',
            'OLLAMA_CONTEXT_LENGTH=32768','numactl','--physcpubind='+','.join(map(str,config['cpus'])),
            '--membind='+str(config['node']),str(binary),'serve']

def inference_processes():
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
            if not args:continue
            name=Path(args[0]).name
            # Also inspect argv for runuser/env wrappers around the daemon.
            is_infer=(name in ('ollama','llama-server','ollama_llama_server') or
                      ('serve' in args and any(Path(x).name=='ollama' for x in args)))
            if is_infer:
                found.append({'pid':int(p.name),'cgroup':(p/'cgroup').read_text().strip().split('0::')[-1],
                              'args':args})
        except OSError:pass
    return found

def allow_no_own_inference(own,peers,processes=None):
    for p in inference_processes() if processes is None else processes:
        components=Path(p['cgroup']).parts
        # No substring matching: own or unknown service must be rejected.
        need(own not in components,'own inference has not stopped')
        need(any(u in components for u in peers),'foreign inference process is active')

def worker_command(unit,parent,work,assignment,index,log):
    return ['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
            '--property=RuntimeMaxSec=infinity','--property=MemoryMax=64G','--property=TasksMax=160',
            '--property=TimeoutStopSec=20','--property=KillMode=control-group','--property=PartOf='+parent,
            '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
            '--setenv=CPUCOND76_WORKER_UNIT='+unit,'--setenv=PYTHONDONTWRITEBYTECODE=1',
            '--working-directory='+str(work),'/usr/bin/python3','-B','-u',str(CONTROL/'goal0076_dual_numa.py'),
            '--gen-worker','--assignment',str(assignment),'--worker-index',str(index)]

def partition_records(plan,ids):
    byid={t['id']:t for t in plan['tasks']}; need(len(byid)==len(plan['tasks']),'duplicate task IDs')
    need(len(set(ids))==len(ids) and set(ids)<=set(byid),'bad partition')
    subset=copy.deepcopy(plan); subset['tasks']=[byid[x] for x in ids];subset['requests']=len(ids)
    return subset


def dual_generation(b,pkg,plan,run,deadline,freeze,binary):
    c=load_chain();cfg=validate_config(c);condition=plan['conditions'][0]
    need(condition in ('P1','P2') and len(plan['tasks'])==180,'not a P1/P2 full plan')
    b.check_busy();need(not inference_processes(),'inference already active')
    print('DUAL_NUMA_MODEL_COPY_CHECK: 第2ソケット用の独立モデルファイルを準備/照合します。',flush=True)
    copy_receipt=ensure_second_store(b,binary,freeze,cfg['workers'])
    session=run/'dual76'/('generation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6])
    session.mkdir(parents=True)
    parent=os.environ['CPUCOND_BATCH_UNIT']
    units=['cpucond76-infer-'+condition+'-'+str(i)+'-'+uuid.uuid4().hex[:8]+'.service' for i in (0,1)]
    assignment={'revision':'dual-numa-p12-v1','condition':condition,'work':str(pkg),'run':str(run),
                'parent_unit':parent,'units':units,'workers':cfg['workers'],
                'ids':cfg['assignments'][condition],'plan_sha256':sha(pkg/'plan.json'),
                'freeze':freeze,'binary':str(binary),'second_model_copy':copy_receipt,
                'model_payload_unchanged':True,'created_utc':utc()}
    record(session/'assignment.json',assignment)
    atomic(run/'dual76-current.json',{'directory':str(session),'workers':units,'condition':condition})
    launched=[];stopfile=session/'stop-new-requests.json'
    try:
        for i in (0,1):
            cmd(worker_command(units[i],parent,pkg,session/'assignment.json',i,run/'dual76'/f'worker-{i}.log'),stdin=subprocess.DEVNULL)
            launched.append(units[i])
        print('DUAL_NUMA_GENERATION_STARTED '+condition+' (socket0 + socket1)',flush=True)
        last=0
        while True:
            states=[unit_props(u)['ActiveState'] for u in launched]
            failed=any(s not in LIVE and (not (session/f'worker-{i}-result.json').exists() or
                       not load(session/f'worker-{i}-result.json').get('complete')) for i,s in enumerate(states))
            if failed and not stopfile.exists():
                record(stopfile,{'utc':utc(),'reason':'one worker ended without full terminal records',
                                 'peer_finishes_current_request_then_stops':True})
            if time.monotonic()-last>=30 or all(s not in LIVE for s in states):
                b.atomic(run/'progress.json',b.results_summary(plan,run));last=time.monotonic()
            if all(s not in LIVE for s in states):break
            time.sleep(2)
        # All worker units must have drained before the old pipeline can evaluate.
        need(not inference_processes(),'inference processes remain; measurement forbidden')
        results=[load(session/f'worker-{i}-result.json') for i in (0,1)]
        need(all(x.get('complete') for x in results),'parallel generation paused for safety; no retries')
        print('DUAL_NUMA_INFERENCE_STOPPED: 両推論を停止。既存の単独検証・計測へ進みます。',flush=True)
    finally:
        for u in launched:
            if unit_props(u)['ActiveState'] in LIVE:
                cmd(['systemctl','stop',u],timeout=45,stdin=subprocess.DEVNULL)
        need(not inference_processes(),'inference cleanup failed; do not measure')


def snapshot_inference(unit):
    out=[]
    for rec in inference_processes():
        if unit not in Path(rec['cgroup']).parts:continue
        p=Path('/proc')/str(rec['pid'])
        try:
            st={k:v.strip() for x in (p/'status').read_text().splitlines() if ':' in x for k,v in [x.split(':',1)]}
            from collections import Counter
            policies=Counter(x.split()[1] for x in (p/'numa_maps').read_text().splitlines() if len(x.split())>1)
            out.append({'pid':rec['pid'],'executable':Path(rec['args'][0]).name,
                        'cgroup':rec['cgroup'],'cpu_allowed':st.get('Cpus_allowed_list'),
                        'rss_kib':st.get('VmRSS'),'uid':st.get('Uid'),'numa_policy_counts':dict(policies)})
        except OSError:pass
    return out


def gen_worker(assignment_path,index):
    host(); c=load_chain();cfg=validate_config(c)
    need(index in (0,1),'bad worker index')
    path=assignment_path.resolve();need(path.is_relative_to(ROOT) and path.name=='assignment.json','assignment outside campaign')
    a=load(path);condition=a['condition'];need(condition in ('P1','P2'),'bad condition')
    pkg=ROOT/condition/'work';run=ROOT/condition/'results'
    need(a['work']==str(pkg) and a['run']==str(run),'worker path mismatch')
    need(a['plan_sha256']==cfg['plan_hashes'][condition]==sha(pkg/'plan.json'),'worker plan mismatch')
    need(a['workers']==cfg['workers'] and a['ids']==cfg['assignments'][condition],'worker configuration mismatch')
    own=a['units'][index];peer=a['units'][1-index]
    need(os.environ.get('CPUCOND76_WORKER_UNIT')==own and own in Path('/proc/self/cgroup').read_text(),'worker unit/cgroup mismatch')
    parent=unit_props(a['parent_unit'])
    need(parent['ActiveState'] in LIVE,'parent stage not active')
    props=unit_props(own,('MemoryMax','TasksMax','PartOf','RuntimeMaxUSec'))
    need(int(props['MemoryMax'])<=64*1024**3 and int(props['TasksMax'])<=160,'worker limits incorrect')
    need(a['parent_unit'] in props['PartOf'].split() and props['RuntimeMaxUSec']=='infinity','worker lifetime not linked to parent')
    b=c.base_module(pkg); plan=load(pkg/'plan.json');subset=partition_records(plan,a['ids'][str(index)])
    w=cfg['workers'][index]; session=path.parent
    b.SERVICE_PORT=w['port']
    b.model_command=lambda binary:worker_service_command(binary,b,w)
    b.check_busy=lambda:allow_no_own_inference(own,[peer])
    # The process has its own Python modules and API port. No shared module mutation.
    import runtime_support as rt
    import streaming_support as stream
    stopped=session/'stop-new-requests.json'
    rt.can_start=lambda item,now,deadline:not stopped.exists()
    rt.receive=functools.partial(stream.receive,port=w['port'])
    previous_extract=b.extract_response
    def extract(obj,item):
        code,receipt=previous_extract(obj,item)
        receipt['inference_execution']={'revision':'dual-numa-p12-v1','worker':index,
             'socket':w['socket'],'cpus':w['cpus'],'numa_node':w['node'],'parallel_workers_max':2,
             'request_payload_unchanged':True,'completion_not_semantic_equivalence_proof':True}
        return code,receipt
    b.extract_response=extract
    # Keep record schema and content, but use exclusive atomic publication so that
    # the coordinator never reads partially written JSON.
    b.jw=lambda p,x:record(Path(p),x)
    b.write=lambda p,x:atomic(Path(p),x,exclusive=True,raw=True)
    def safe_atomic(p,value):
        p=Path(p)
        if p==run/'progress.json':p=session/f'worker-{index}-progress.json'
        elif p==run/'live-generation.json':p=session/f'worker-{index}-live.json'
        atomic(p,value)
    b.atomic=safe_atomic
    # Bind metadata/preflight work to the same socket; Ollama is separately bound.
    os.sched_setaffinity(0,set(w['cpus']))
    need(sha(a['binary'])==b.RUNTIME_SHA and a['freeze']['manifest_sha256']==MODEL_DIGEST,'worker binary/model mismatch')
    need(sha(Path(w['models'])/MANIFEST_REL)==MODEL_DIGEST,'worker model manifest differs')
    # Source payload options remain frozen. No endpoint metadata appears in prompts.
    for item in subset['tasks']:
        request=b.safe(pkg,item['request']);payload=b.load(request)
        need(b.sha(request)==item['request_sha256'],'request changed')
        need(payload['options']['num_thread']==16 and payload['options']['num_gpu']==0 and payload['options']['num_ctx']==32768,
             'request execution options changed')
    record(session/f'worker-{index}-start.json',{'utc':utc(),'unit':own,'configuration':w,
           'requests':len(subset['tasks']),'original_plan_sha256':a['plan_sha256']})
    # Capture actual affinity/policy when the first stream response arrives, and
    # at completion. Do not equate bind policy with all file pages being local.
    original_receive=rt.receive
    def with_probe(payload,d,timeout_seconds,**kw):
        hb=kw.get('heartbeat');first=[True]
        def h(status):
            if first[0] or status.get('done_received'):
                obs=snapshot_inference(own)
                need(any(v['executable'] in ('ollama','llama-server','ollama_llama_server') for v in obs),
                     'cannot observe the owned inference process')
                for item in obs:
                    need(set(cpu_list(item['cpu_allowed']))<=set(w['cpus']),'inference escaped CPU mask')
                    if item['executable'] in ('ollama','llama-server','ollama_llama_server'):
                        expected_uid=str(pwd.getpwnam(b.ACCOUNT).pw_uid)
                        need(item['uid'].split()[0]==expected_uid and expected_uid!='0','inference UID mismatch')
                record(Path(d)/('placement-start.json' if first[0] else 'placement-final.json'),
                       {'utc':utc(),'worker':index,'processes':obs})
                first[0]=False
            if hb:hb(status)
        return original_receive(payload,d,timeout_seconds,heartbeat=h)
    rt.receive=with_probe
    error=None;start=time.monotonic()
    try:
        rt.generation_phase(b,pkg,subset,run,math.inf,a['freeze'],Path(a['binary']))
    except Exception as e:
        error=type(e).__name__+': '+str(e)
    finally:
        counts=b.results_summary(subset,run)
        complete=counts['requests_pending']==0 and error is None
        record(session/f'worker-{index}-result.json',{'utc':utc(),'worker':index,'complete':complete,
               'elapsed_seconds':time.monotonic()-start,'counts':counts,'error':error})
    need(complete,error or 'worker stopped before all assigned requests')


def stage_worker(condition):
    host();c=load_chain();validate_config(c)
    original=c.base_module
    def adapted(work):
        b=original(work)
        b.generation_phase=lambda pkg,p,r,d,f,binary:dual_generation(b,pkg,p,r,d,f,binary)
        summary=b.results_summary
        def summary76(plan,run):
            v=summary(plan,run);v['generation_runtime_revision']='dual-numa-p12-v1'
            v['generation_workers']=2;v['p0_runtime_differs']=True
            v['runtime_change_may_affect_generation']=True
            return v
        b.results_summary=summary76
        return b
    c.base_module=adapted
    c.stage_worker(ROOT,condition)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument('--enable',action='store_true');modes.add_argument('--chain-worker',action='store_true')
    modes.add_argument('--stage-worker',action='store_true');modes.add_argument('--gen-worker',action='store_true')
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--condition',choices=('P1','P2'))
    p.add_argument('--assignment',type=Path);p.add_argument('--worker-index',type=int)
    args=p.parse_args()
    try:
        need(args.root==ROOT,'wrong campaign root')
        if args.enable:enable()
        elif args.chain_worker:chain_worker()
        elif args.stage_worker:stage_worker(args.condition)
        else:gen_worker(args.assignment,args.worker_index)
        return 0
    except Exception as e:
        print('DUAL_NUMA_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr,flush=True)
        if args.chain_worker and CONTROL.exists():
            try:new_status('BLOCKED',error=type(e).__name__+': '+str(e))
            except Exception:pass
        return 1
if __name__=='__main__':raise SystemExit(main())
