#!/usr/bin/env python3
"""Prepare a new, explicitly heterogeneous resource-amendment cohort.
All 180 source/request pairs are audited. Only requests never attempted in either
old job enter this queue. Old successful/failed attempts are referenced, never
rewritten, reclassified as model failures, or automatically retried.
"""
from __future__ import annotations
import argparse
import contextlib
import copy
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import uuid

REV = 'polybench-direct-codegen-resource-amendment-v1'
PARENT_SHA = '1606a944f79e5e445f3511414f39d8eeee60617b575b596b932374d65f56eac6'
SUPPLEMENT_SHA = '97de40c0a9d4346d576525e30f1965ee09faeae2a58f10ef3bd38bc57c32db77'
RUNNER_SHA = 'd445c3794b3ef748c626dd074e1739188d75b42b177240471a90321dba254182'
MODEL = 'qwen2.5-coder:32b-instruct-q4_K_M'
NEW_CAPS = {'C':4096, 'IR':16384}
OLD_CAPS = {'C':4096, 'IR':8192}
CTX = 32768
LIMIT = 64*1024*1024
LOCK_FILE = "/var/lock/cpucond-batch-codegen.lock"

class Refuse(RuntimeError): pass

def need(x,msg):
    if not x: raise Refuse(msg)

def utc(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),'通常ファイルでない: '+str(p))
    with p.open('rb') as f: raw=f.read(LIMIT+1)
    need(len(raw)<=LIMIT,'ファイル過大: '+str(p))
    return raw

def decode(raw):
    def pairs(xs):
        d={}
        for k,v in xs:
            need(k not in d,'JSONキー重複');d[k]=v
        return d
    def bad(s): raise Refuse('非有限JSON: '+s)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def load(p): return decode(read(p))
def encode(x): return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()

def safe(root,rel):
    q=PurePosixPath(rel)
    need(isinstance(rel,str) and rel and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,'範囲外パス')
    root=Path(root).resolve();p=root.joinpath(*q.parts)
    need(p.resolve().is_relative_to(root) and p!=root,'範囲外パス')
    for a in [p,*p.parents]:
        if a==root:break
        need(not a.is_symlink(),'リンクを拒否')
    return p

def write(p,raw):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())

def jw(p,x):write(p,encode(x))
def verify_list(root):
    table={}
    for line in read(root/'SHA256SUMS').decode().splitlines():
        h,sep,n=line.partition('  ');n=n.removeprefix('./')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and n not in table,'ハッシュ一覧不正')
        need(digest(read(safe(root,n)))==h,'ハッシュ不一致: '+n)
        table[n]=h
    return table

def seal(root):
    rows=[]
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),'リンクを拒否')
        if p.is_file() and p.name!='SHA256SUMS':
            rows.append(digest(read(p))+'  '+p.relative_to(root).as_posix()+'\n')
    write(root/'SHA256SUMS',''.join(rows).encode())

def idle(jobs):
    for job in jobs:
        unit_path=job/'active-unit.txt'
        if not unit_path.exists():continue
        unit=read(unit_path).decode().strip()
        need(re.fullmatch(r'cpucond[0-9]+-[A-Za-z0-9-]+\.service',unit),'unit名不正')
        p=subprocess.run(['systemctl','show',unit,'-p','ActiveState','--value'],capture_output=True,text=True,timeout=15)
        if p.returncode:
            need('not found' in p.stderr.lower() or 'could not be found' in p.stderr.lower(),'サービス状態を取得できません')
        else:
            need(p.stdout.strip() in ('inactive','failed'),'既存ジョブが稼働中です。停止せず待ちます: '+unit)
    for d in Path('/proc').iterdir():
        if not d.name.isdigit() or int(d.name)==os.getpid():continue
        try: args=(d/'cmdline').read_bytes().split(b'\0')
        except OSError:continue
        names={Path(a.decode(errors='replace')).name for a in args if a}
        if 'ollama' in names and (b'serve' in args or b'runner' in args):
            raise Refuse('別の推論処理があります。停止しません: '+d.name)
        if names & {'goal0054_final_physical_atlas.py','goal0068_verify_reviewed_qwen32_c.py'}:
            raise Refuse('別の計測/検証処理があります: '+d.name)


def prior_state(job,tid):
    d=safe(job,'results/generation/'+tid)
    if not d.exists():return {'attempted':False,'status':'not_started','files':{}}
    files={}
    for p in sorted(d.rglob('*')):
        need(not p.is_symlink(),'生成記録にリンク')
        if p.is_file(): files[p.relative_to(d).as_posix()]=digest(read(p))
    result=load(d/'result.json') if (d/'result.json').exists() else None
    if not files:
        return {'attempted':False,'status':'empty_directory','files':{}}
    only_exclusion=(set(files)=={'result.json'} and result.get('status')=='input_budget_excluded')
    if only_exclusion:
        return {'attempted':False,'status':'input_budget_excluded','files':files}
    return {'attempted':True,'status':result.get('status') if result else 'attempt_or_response_unknown','files':files}


def amend_request(old,form):
    need(form in NEW_CAPS,'表現不正')
    need(old.get('model')==MODEL and old.get('raw') is True and old.get('stream') is False,'旧要求形式不一致')
    need(old['options']['num_ctx']==CTX and old['options']['num_predict']==OLD_CAPS[form],'旧予算不一致')
    new=copy.deepcopy(old)
    new['stream']=True
    new['options']['num_predict']=NEW_CAPS[form]
    return new


def budget(input_tokens,source_tokens,form):
    need(all(type(x) is int and x>0 for x in (input_tokens,source_tokens)),'トークン数不正')
    cap=NEW_CAPS[form]
    # Include a small end/format reserve for the unchanged-code fallback.
    need(source_tokens+64<=cap,'未変更コードが出力枠に入りません。自動で課題を除外しません')
    need(input_tokens+cap+32<=CTX,'文脈長に収まりません。自動で切り詰めません')
    return {'input_tokens':input_tokens,'source_tokens':source_tokens,
        'output_cap':cap,'context_slack':CTX-input_tokens-cap-32,
        'unchanged_fallback_slack':cap-source_tokens-64}


@contextlib.contextmanager
def experiment_lock():
    with Path(LOCK_FILE).open('a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise Refuse('既存処理のロックが使用中です')
        yield


def prepare(parent,supplement,audit,out):
    with experiment_lock():
        return _prepare_locked(parent,supplement,audit,out)


def _prepare_locked(parent,supplement,audit,out):
    parent=parent.resolve();supplement=supplement.resolve();audit=audit.resolve();out=out.absolute()
    need(not out.is_relative_to(parent) and not out.is_relative_to(supplement),'旧ジョブ内へは書きません')
    idle([parent,supplement,out])
    if out.exists():
        verify_list(out/'work');p=load(out/'work/plan.json')
        need(p['revision']==REV and p['resource_amendment']['parent_job']==str(parent),'異なる既存ジョブです')
        print('RESOURCE_BATCH_REUSED');print('保存先:',out);return
    kit=Path(__file__).resolve().parent
    verify_list(kit)
    hashes=verify_list(parent/'work')
    need(hashes.get('plan.json')==PARENT_SHA and hashes.get('goal0069_batch_codegen.py')==RUNNER_SHA,'旧版の計画/実行器不一致')
    need(digest(read(supplement/'work/plan.json'))==SUPPLEMENT_SHA,'補完計画不一致')
    plan=load(parent/'work/plan.json')
    need(plan['conditions']==['P0'] and plan['prompt_language']=='en' and len(plan['tasks'])==180,'旧計画の条件不一致')
    need(len({x['id'] for x in plan['tasks']})==180,'要求ID重複')
    for t in plan['tasks']:
        need(re.fullmatch(r'[A-Za-z0-9_-]+',t['id']),'要求ID不正')
    summary=load(audit/'summary.json')
    need(summary['source_plan_sha256']==PARENT_SHA and summary['observed_count_mismatches']==0,'監査結果不一致')
    need(summary['crosscheck_supported_on_saved_examples'] is True,'実応答との照合が未確認')
    tokenfile=audit.parent/'tokenizer.json'
    need(digest(read(tokenfile))==summary['tokenizer_sha256'],'トークナイザー不一致')
    need(importlib.metadata.version('tokenizers')=='0.21.4','tokenizers版不一致')
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(tokenfile));tokenizer.no_truncation();tokenizer.no_padding()
    prior={};rows=[];tasks=[];payloads={}
    instances={(i['task'],i['size']):i for i in plan['instances_list']}
    for t in plan['tasks']:
        tid=t['id'];form=t['form']
        raw=read(safe(parent/'work',t['request']))
        need(digest(raw)==t['request_sha256'],'要求ハッシュ不一致')
        request=decode(raw);new=amend_request(request,form)
        source=read(safe(parent/'work',t['source']))
        need(digest(source)==instances[(t['task'],t['size'])]['sources'][form]['sha256'],'元コード不一致')
        encoding=tokenizer.encode(request['prompt'],add_special_tokens=False)
        need(tokenizer.decode(encoding.ids,skip_special_tokens=False)==request['prompt'],'入力計数往復不一致')
        inp=len(encoding.ids)
        srcn=len(tokenizer.encode(source.decode('utf-8').rstrip(),add_special_tokens=False).ids)
        b=budget(inp,srcn,form)
        a=prior_state(parent,tid);s=prior_state(supplement,tid)
        need(not(a['attempted'] and s['attempted']),'二重送信記録があります: '+tid)
        prior[tid]={'parent':a,'supplement':s}
        attempted=a['attempted'] or s['attempted']
        rows.append({'id':tid,'form':form,**b,'previously_attempted':attempted,
            'parent_status':a['status'],'supplement_status':s['status']})
        # Check all existing full responses against the pinned tokenizer.
        for root, st in ((parent,a),(supplement,s)):
            if 'response.raw.json' in st['files']:
                response=load(root/'results/generation'/tid/'response.raw.json')
                need(response.get('prompt_eval_count')==inp,'過去応答の入力数不一致')
        if attempted:continue
        n=copy.deepcopy(t);newraw=encode(new)
        n.update(old_request_sha256=t['request_sha256'],request_sha256=digest(newraw),
            context_budget_ok=True,reference_tokenizer_input_tokens=inp,
            source_output_tokens=srcn,resource_policy=REV,
            request_timeout_seconds=1800 if form=='C' else 7200)
        tasks.append(n);payloads[tid]=newraw
    need(tasks,'未送信要求がありません。既存結果を再生成しません')
    keys={(t['task'],t['size']) for t in tasks}
    newplan=copy.deepcopy(plan)
    newplan.update(revision=REV,requests=len(tasks),tasks=tasks,output_caps=NEW_CAPS,
        instances=len(keys),kernels=len({k for k,s in keys}),
        instances_list=[i for i in plan['instances_list'] if (i['task'],i['size']) in keys],
        scope='previously never-attempted requests only; corrected resource budget; provisional, not a homogeneous 180-sample cohort',
        context_policy='official token counts + complete unchanged-source output + fixed reserves',
        resource_amendment={'id':REV,'parent_job':str(parent),'supplement_job':str(supplement),
            'parent_plan_sha256':PARENT_SHA,'supplement_plan_sha256':SUPPLEMENT_SHA,
            'original_unique_requests':180,'old_attempted_requests_retained':180-len(tasks),
            'new_first_transmissions':len(tasks),'no_old_attempts_retried':True,
            'old_results_merged_as_same_budget':False,
            'prompt_and_source_bytes_unchanged':True,'context_length_unchanged':True,
            'output_caps_old':OLD_CAPS,'output_caps_new':NEW_CAPS,
            'request_timeout_seconds':{'C':1800,'IR':7200},'idle_timeout_seconds':1800,
            'stream':True,'session_seconds':14400,'generation_hours':3.5,
            'consecutive_transport_failure_stop':2,
            'old_failures_reclassified':False,
            'tokenizer_sha256':summary['tokenizer_sha256'],
            'all_30_multiinput_validator_complete':False})
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=out.with_name(out.name+'.preparing-'+uuid.uuid4().hex[:8]);stage.mkdir()
    try:
        work=stage/'work';work.mkdir()
        selected={'utilities/polybench.c','utilities/polybench.h'}
        for i in newplan['instances_list']:
            selected.update((i['driver'],i['oracle']))
            selected.update(v['path'] for v in i['sources'].values())
        for n in selected:
            raw=read(safe(parent/'work',n));need(digest(raw)==hashes[n],'コピー時ハッシュ不一致');write(work/n,raw)
        for n in ('goal0069_batch_codegen.py','streaming_support.py','runtime_support.py',
                  'goal0073_resource_amendment.py','server_launch.sh','model_support.py',
                  'roundtrip_support.py','stress_support.py','runner-change.diff'):
            write(work/n,read(kit/n))
        for t in tasks:write(work/t['request'],payloads[t['id']])
        jw(work/'plan.json',newplan)
        jw(work/'amendment-evidence/prior-attempts.json',prior)
        write(work/'amendment-evidence/parent-plan.json',read(parent/'work/plan.json'))
        write(work/'amendment-evidence/supplement-plan.json',read(supplement/'work/plan.json'))
        write(work/'amendment-evidence/token-audit-summary.json',read(audit/'summary.json'))
        with (work/'budget-audit.csv').open('x',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        jw(work/'preparation-receipt.json',{'created_utc':utc(),'audited_requests':180,
           'planned_first_transmissions':len(tasks),'previously_attempted_retained':180-len(tasks),
           'model_calls':0,'old_files_changed':False,'amendment':newplan['resource_amendment']})
        # Refuse races with old jobs or mutation of already attempted records.
        idle([parent,supplement])
        for t in plan['tasks']:
            need(prior[t['id']]=={'parent':prior_state(parent,t['id']),
                'supplement':prior_state(supplement,t['id'])},'準備中に旧生成記録が変化')
        seal(work);stage.rename(out)
    except Exception:
        shutil.rmtree(stage);raise
    print('RESOURCE_BATCH_PREPARED')
    print('監査: 180/180。未変更コードの出力枠と文脈長を全件確認。')
    print('旧版で送信済み:',180-len(tasks),'件（再生成しません）')
    print('新版の初回送信予定:',len(tasks),'件')
    for form in ('C','IR'):
        r=[x for x in rows if x['form']==form]
        print(form,'最大元コードtoken=',max(x['source_tokens'] for x in r),
              '出力枠=',NEW_CAPS[form],'最小文脈余裕=',min(x['context_slack'] for x in r))
    print('保存先:',out)
    print('この段階の生成API呼出し=0。新旧の予算を同一条件として合算しません。')


def check_ready(job):
    job=job.resolve();verify_list(job/'work');plan=load(job/'work/plan.json')
    need(plan.get('revision')==REV,'新版の計画ではありません')
    a=plan['resource_amendment'];parent=Path(a['parent_job']);supp=Path(a['supplement_job'])
    idle([parent,supp,job])
    for t in plan['tasks']:
        need(not prior_state(parent,t['id'])['attempted'] and
             not prior_state(supp,t['id'])['attempted'],
             '旧ジョブが新版の未送信要求を既に送信しています。二重生成を拒否: '+t['id'])
    with experiment_lock():
        pass
    print('RESOURCE_BATCH_READY_TO_START')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--check-ready',action='store_true')
    p.add_argument('--parent-job',type=Path);p.add_argument('--supplement-job',type=Path)
    p.add_argument('--audit',type=Path);p.add_argument('--out',type=Path);p.add_argument('--job',type=Path)
    args=p.parse_args()
    try:
        if args.prepare:
            need(all(x is not None for x in (args.parent_job,args.supplement_job,args.audit,args.out)),'準備引数不足')
            prepare(args.parent_job,args.supplement_job,args.audit,args.out)
        else:
            need(args.job is not None,'--jobが必要');check_ready(args.job)
        return 0
    except Exception as e:
        print('RESOURCE_BATCH_BLOCKED:',type(e).__name__+': '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
