#!/usr/bin/env python3
"""Create a separate English batch from a blocked, never-started Goal0069 plan.
No old request/result is overwritten. No inference, download, remote call or
candidate execution occurs in this migration. The existing launcher starts the
new run only after the strengthened sandbox/compile self-checks pass.
"""
from __future__ import annotations
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone

OLD_RUNNER_SHA = 'aaffc7895a8cc4970a35f9b39bba786a300789ce86bf012268b44c3ad45579b6'
OLD_LAUNCHER_SHA = 'e47265d562c5332a9b8057e601bc53ef59b2484ca7fc1beacef9f170a4be2933'
EXPECTED_PLAN_SHA = 'ff460ea4631634b540c996d77ae1ab11b502f3adb65a335af0f956df245f97bf'
OLD_REV = 'polybench-direct-codegen-batch-wave1-v1'
NEW_REV = 'polybench-direct-codegen-batch-wave1-en-v2'
REPLACEMENTS = ('goal0069_batch_codegen.py', 'server_launch.sh')

class Refuse(RuntimeError):
    pass

def need(value, why):
    if not value:
        raise Refuse(why)

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def pairs(items):
    out={}
    for k,v in items:
        need(k not in out,'duplicate JSON key: '+k)
        out[k]=v
    return out

def load(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink() and p.stat().st_size<64*1024*1024,
         'missing/linked/oversized file: '+str(p))
    def invalid(v):
        raise Refuse('invalid JSON number: '+v)
    return json.loads(p.read_bytes(),object_pairs_hook=pairs,parse_constant=invalid)

def write(p,b):
    p=Path(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:
        f.write(b.encode() if isinstance(b,str) else b)
        f.flush()
        os.fsync(f.fileno())

def jw(p,x):
    write(p,json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def safe(root,rel):
    need(isinstance(rel,str),'non-string path')
    q=PurePosixPath(rel)
    need(q.parts and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,
         'invalid relative path: '+rel)
    root=Path(root).resolve()
    p=root.joinpath(*q.parts)
    for component in [p,*p.parents]:
        if component==root:break
        need(not component.is_symlink(),'symlink rejected: '+str(component))
    need(root in p.resolve().parents and p.is_file(),'missing/outside file: '+rel)
    return p

def inventory(root):
    root=Path(root)
    out={}
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),'linked evidence rejected: '+str(p))
        if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
    return out

def verify_list(root):
    root=Path(root)
    rows={}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        h,sep,rel=line.partition('  ')
        rel=rel.removeprefix('./')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and rel not in rows,'invalid SHA256SUMS')
        need(sha(safe(root,rel))==h,'file hash mismatch: '+rel)
        rows[rel]=h
    need(rows,'empty SHA256SUMS')
    return rows

def import_runner(p):
    spec=importlib.util.spec_from_file_location('goal70_'+uuid.uuid4().hex,p)
    mod=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:spec.loader.exec_module(mod)
    finally:sys.dont_write_bytecode=old
    return mod

def validate_parent(parent, expected_plan_sha=EXPECTED_PLAN_SHA):
    parent=Path(parent).resolve()
    work=parent/'work'
    hashes=verify_list(work)
    need(hashes.get('goal0069_batch_codegen.py')==OLD_RUNNER_SHA,'unexpected old runner version')
    need(hashes.get('server_launch.sh')==OLD_LAUNCHER_SHA,'unexpected old launcher version')
    plan=load(work/'plan.json')
    if expected_plan_sha is not None:
        need(sha(work/'plan.json')==expected_plan_sha,'old plan does not match reported plan')
    need(plan.get('revision')==OLD_REV,'old plan revision differs')
    need(plan.get('requests')==180 and len(plan.get('tasks',[]))==180 and
         plan.get('instances')==90 and len(plan.get('instances_list',[]))==90 and
         plan.get('conditions')==['P0'] and plan.get('representations')==['C','IR'] and
         plan.get('samples')==1,'old plan scope differs')
    summary=load(parent/'results/summary.json')
    need(summary.get('completion')=='DATASET_BATCH_BLOCKED','old batch is not the reported blocked run')
    for key,val in {'planned_requests':180,'requests_pending':180,'generated_texts':0,
                    'generation_terminal':0,'validation_terminal':0,'measurement_terminal':0}.items():
        need(summary.get(key)==val,'refuse migration: '+key+' does not match unused batch')
    for name in ('generation','validation','measurement'):
        sub=parent/'results'/name
        need(not sub.exists() or not any(p.is_file() or p.is_symlink() for p in sub.rglob('*')),
             'attempt/output evidence exists in '+name+'; do not discard or reclassify it')
    seen=set()
    for item in plan['tasks']:
        need(item['id'] not in seen,'duplicate task id')
        seen.add(item['id'])
        need(item['condition']=='P0' and item['sample']==0,'unexpected condition/sample')
        need(sha(safe(work,item['request']))==item['request_sha256'],'request hash mismatch')
        safe(work,item['source'])
    return hashes,plan

def migrate(parent, target, kit, expected_plan_sha=EXPECTED_PLAN_SHA):
    parent=Path(parent).resolve(); target=Path(target).resolve(); kit=Path(kit).resolve()
    need(not target.exists(),'destination exists; old/new runs must not be overwritten')
    old_hashes,oldplan=validate_parent(parent,expected_plan_sha)
    old_snapshot=inventory(parent)
    target.mkdir(mode=0o700)
    work=target/'work';work.mkdir()
    # Only files verified by the old manifest are copied, never a generated code tree.
    for rel,h in old_hashes.items():
        write(work/rel,safe(parent/'work',rel).read_bytes())
    for name in REPLACEMENTS:
        (work/name).unlink()
        write(work/name,(kit/name).read_bytes())
    m=import_runner(work/'goal0069_batch_codegen.py')
    old=import_runner(parent/'work/goal0069_batch_codegen.py')
    need(m.REV==NEW_REV,'new runner revision differs')
    g=m.vendor('stress_support.py')
    plan=copy.deepcopy(oldplan)
    plan['revision']=NEW_REV
    plan['prompt_language']='en'
    plan['prompt_revision']=m.PROMPT_REVISION
    plan['source_code_bytes_unchanged']=True
    plan['parent_blocked_plan_sha256']=sha(parent/'work/plan.json')
    plan['parent_blocked_run']=str(parent)
    plan['revision_reason']='Translate all instruction text to English before any batch generation; explicitly clear inherited capabilities, fix private tmpfs permissions, and add named sandbox diagnostics.'
    plan['no_language_ablation_claim']=True
    mapping=[]
    for item in plan['tasks']:
        source=safe(work,item['source']).read_text()
        domain=g.contract(item['task'])['domain'] if item['task'] in g.TASKS else None
        old_payload=load(safe(work,item['request']))
        old_rebuilt,_=old.request_for(source,item['form'],item['task'],item['size'],domain)
        need(old_payload==old_rebuilt,'old prompt differs from the recorded generator: '+item['id'])
        payload,upper=m.request_for(source,item['form'],item['task'],item['size'],domain)
        need({k:v for k,v in old_payload.items() if k!='prompt'} ==
             {k:v for k,v in payload.items() if k!='prompt'},'generation parameters changed')
        text=payload['prompt']
        intro,sep,end=text.partition('----- BEGIN ORIGINAL CODE -----\n')
        need(sep and intro.isascii(),'non-English instruction text remains')
        ending='\n----- END ORIGINAL CODE -----\n'
        need(source.rstrip()+ending in end,'source code changed during prompt translation')
        old_request_hash=item['request_sha256']
        request=work/item['request'];request.unlink();jw(request,payload)
        item['request_sha256']=sha(request)
        item['input_byte_upper']=upper
        item['context_budget_ok']=upper+m.CAPS[item['form']]<=m.CTX
        item['prompt_language']='en'
        mapping.append({'id':item['id'],'source_sha256':sha(work/item['source']),
                        'old_request_sha256':old_request_hash,'new_request_sha256':item['request_sha256'],
                        'sampling_parameters_unchanged':True})
    (work/'plan.json').unlink();jw(work/'plan.json',plan)
    jw(work/'english-migration.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
       'parent_job':str(parent),'parent_plan_sha256':sha(parent/'work/plan.json'),
       'parent_summary_sha256':sha(parent/'results/summary.json'),
       'changed_instruction_language_only':True,'sandbox_launcher_also_hardened':True,
       'generated_attempts_imported':0,'source_inputs_unchanged':True,'requests':mapping})
    # Verify every old file except deliberate runner/launcher/plan/request replacements.
    changed={'plan.json',*REPLACEMENTS,*[x['request'] for x in oldplan['tasks']]}
    for rel,h in old_hashes.items():
        if rel not in changed:
            need(sha(work/rel)==h,'unexpected non-prompt input change: '+rel)
    m.seal(work)
    need(inventory(parent)==old_snapshot,'old evidence changed while migrating; refuse to launch')
    jw(target/'parent-preservation.json',{'verified_utc':datetime.now(timezone.utc).isoformat(),
         'parent_job':str(parent),'parent_files_unchanged':True,'parent_inventory':old_snapshot})
    write(target/'new-plan-sha256.txt',sha(work/'plan.json')+'  work/plan.json\n')
    print('ENGLISH_BATCH_PACKAGE_READY',flush=True)
    print('旧記録を保持。全180件の指示文を英語化。CPU情報なし(P0)・各1試行は変更なし。',flush=True)
    print('モデル・seed・出力上限・入力ソース・検証式・計測式は変更なし。',flush=True)
    print('文脈長の保守判定で送信不可:',sum(not x['context_budget_ok'] for x in plan['tasks']),'件',flush=True)
    print('新しい作業場所:',target,flush=True)
    print('新しい計画SHA-256:',sha(work/'plan.json'),flush=True)
    return target

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply',action='store_true',required=True)
    ap.add_argument('--parent',type=Path,required=True)
    ap.add_argument('--target',type=Path,required=True)
    args=ap.parse_args()
    need(os.geteuid()==0,'run the migration on the server as the trusted root controller')
    need(Path('/proc/sys/kernel/hostname').read_text().strip()=='cpucond-zen2-01','wrong server')
    need('AMD EPYC 7402' in Path('/proc/cpuinfo').read_text(),'wrong CPU')
    for p in (args.parent,args.target):
        need(p.is_absolute() and str(p).startswith('/srv/research/cpucond-batch') and '..' not in p.parts,
             'unexpected job location')
    lock=open('/var/lock/cpucond-batch-codegen.lock','a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for job in (args.parent,args.target):
        unitfile=job/'active-unit.txt'
        if unitfile.exists():
            unit=unitfile.read_text().strip()
            need(re.fullmatch(r'cpucond69-[A-Za-z0-9-]+\.service',unit),'invalid unit name')
            result=subprocess.run(['systemctl','is-active','--quiet',unit],timeout=10)
            need(result.returncode!=0,'another job is active; no process will be stopped automatically')
    kit=Path(__file__).resolve().parent
    verify_list(kit)
    migrate(args.parent,args.target,kit)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('移行停止:',type(exc).__name__+': '+str(exc),file=sys.stderr)
        raise SystemExit(1)
