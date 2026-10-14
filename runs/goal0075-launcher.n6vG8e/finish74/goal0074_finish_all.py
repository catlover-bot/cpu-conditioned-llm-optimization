#!/usr/bin/env python3
"""Completion-driven handover for the fixed Goal0073 queue.
No aggregate deadline, no model downloads, no resubmission, no root fallback.
Only scheduling changes. Original work/plan/requests and validators stay intact.
"""
from __future__ import annotations
import argparse
import ast
import difflib
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
import time
import uuid
from datetime import datetime, timezone

JOB = Path('/srv/research/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent')
CONTROL = 'completion-driven-v1'
PLAN_SHA = '6abe9c69297a494c0f5df736da1c76d2d789f326567359dc32e3c7c293be848d'
ORIGIN = {
 'goal0069_batch_codegen.py':'c0f16b48924a81320aee74f16b6b136503667d648a0dc2ee61e2c807c53fc47c',
 'runtime_support.py':'65e8fa3acdbb8242a9c1300757439f56ca699a350c49cf6c9b9b85d93f6c0eed',
 'streaming_support.py':'6fb3e1548e6deaf817d1dfd07348fb359112b4917751c09787de955b20bc1fd5',
 'goal0073_resource_amendment.py':'d68593c25d8fa0c7a926b7930e19dcc62d7489ea99bb89e35d83d7a2eaff54e0',
 'plan.json': PLAN_SHA,
}
FILES = ('goal0074_finish_all.py','until_complete_pipeline.py','pipeline-change.diff')
class Refuse(RuntimeError): pass

def need(ok, text):
    if not ok: raise Refuse(text)

def now(): return datetime.now(timezone.utc).isoformat()

def digest(raw): return hashlib.sha256(raw).hexdigest()

def read(path, limit=64*1024*1024):
    path=Path(path)
    need(path.is_file() and not path.is_symlink(), '通常ファイルではありません: '+str(path))
    with path.open('rb') as f: raw=f.read(limit+1)
    need(len(raw)<=limit, '過大なファイルです: '+str(path))
    return raw

def decode(raw):
    def pairs(xs):
        d={}
        for k,v in xs:
            need(k not in d,'JSONキー重複');d[k]=v
        return d
    def bad(s): raise Refuse('非有限JSON: '+s)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)

def load(path): return decode(read(path))

def encoded(x): return (json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()

def write(path, raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f: f.write(raw);f.flush();os.fsync(f.fileno())

def atomic(path, raw):
    path=Path(path)
    need(not path.is_symlink(),'出力先がリンクです')
    temp=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    write(temp,raw);os.replace(temp,path)

def status(job, phase, **kwargs):
    atomic(job/CONTROL/'status.json',encoded({'phase':phase,'utc':now(),'job':str(job),
        'total_wall_time_limit_seconds':None,**kwargs}))

def command(argv, **kwargs):
    return subprocess.run(argv,check=True,timeout=30,**kwargs)

def unit_state(unit):
    need(re.fullmatch(r'cpucond[0-9]+-[A-Za-z0-9-]+\.service',unit) is not None,'サービス名不正')
    r=subprocess.run(['systemctl','show',unit,'-p','ActiveState','--value'],
                     capture_output=True,text=True,timeout=15,env={**os.environ,'LC_ALL':'C'})
    if r.returncode:
        if 'not found' in r.stderr.lower() or 'could not be found' in r.stderr.lower(): return 'inactive'
        raise Refuse('systemdの状態を取得できません: '+r.stderr[:500])
    s=r.stdout.strip()
    need(s in ('active','activating','reloading','deactivating','inactive','failed'),'不明なサービス状態: '+s)
    return s

def live_state(s): return s in ('active','activating','reloading','deactivating')

def expected_origin(work):
    for name,h in ORIGIN.items():
        need(digest(read(work/name))==h,'旧版の固定ファイルと異なります: '+name)
    plan=load(work/'plan.json')
    need(plan.get('requests')==166 and len(plan.get('tasks',[]))==166,'166件の固定キューではありません')
    return plan

def need_host(job):
    need(os.geteuid()==0,'サーバーの管理者として起動してください')
    need(job==JOB and job.resolve()==JOB and not job.is_symlink(),'対象ジョブが違います')
    need(Path('/proc/sys/kernel/hostname').read_text().strip()=='cpucond-zen2-01','対象ホストが違います')
    need('AMD EPYC 7402' in Path('/proc/cpuinfo').read_text(),'CPUが違います')

def verify_kit(root):
    rows={}
    for line in read(root/'SHA256SUMS').decode().splitlines():
        h,sep,n=line.partition('  ')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and n in FILES and n not in rows,'配布ハッシュ一覧が不正')
        need(digest(read(root/n))==h,'配布ファイルのハッシュ不一致: '+n)
        rows[n]=h
    need(set(rows)==set(FILES),'配布ファイルが不足')
    return rows

def install(job, kit):
    need_host(job);hashes=verify_kit(kit);expected_origin(job/'work')
    target=job/CONTROL
    if target.exists():
        need(not target.is_symlink(),'制御用ディレクトリがリンクです')
        for n,h in hashes.items():need(digest(read(target/n))==h,'以前の制御器と異なります: '+n)
        print('FINISH_ALL_CONTROLLER_REUSED',flush=True)
    else:
        stage=job/(CONTROL+'.preparing-'+uuid.uuid4().hex[:8]);stage.mkdir()
        for n in FILES:write(stage/n,read(kit/n))
        write(stage/'SHA256SUMS',read(kit/'SHA256SUMS'))
        write(stage/'installation.json',encoded({'utc':now(),'original_files':ORIGIN,'controller_files':hashes,
            'termination':'all_fixed_queue_items_have_terminal_generation_validation_and_eligible_measurement_records',
            'model_prompt_seed_per_request_budgets_unchanged':True,
            'old_work_and_plan_unchanged':True,'old_per_request_results_not_overwritten':True,
            'mutable_summary_snapshotted_before_handover':True,
            'wait_for_running_session_without_interrupt':True,
            'global_time_limit':None,'generation_window':None,
            'safety_stops_retained':['isolation_or_integrity_failure','consecutive_two_transport_failures','host_change','external_stop'],
            'request_time_limits_seconds':{'C':1800,'IR':7200},'stream_idle_seconds':1800,
            'does_not_complete_P1_P2_other_models_or_GPU':True}))
        stage.rename(target)
        print('FINISH_ALL_CONTROLLER_PREPARED',flush=True)
    atomic(Path('/root/goal0074-current-job.path'),(str(job)+'\n').encode())
    return target

def completed(x):
    n=x.get('planned_requests')
    return (type(n) is int and n>0 and x.get('generation_terminal')==n and
            x.get('validation_terminal')==n and x.get('measurement_pending')==0 and
            x.get('completion')=='DATASET_BATCH_COMPLETE')

def launch(job):
    control=job/CONTROL;verify_kit(control)
    with open('/var/lock/cpucond-completion74-launch.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        marker=control/'active-unit.txt'
        if marker.exists():
            unit=read(marker).decode().strip()
            if live_state(unit_state(unit)):
                print('FINISH_ALL_ALREADY_RUNNING\nunit='+unit,flush=True);return
        summary=job/'results/summary.json'
        if summary.is_file() and completed(load(summary)):
            print('FINISH_ALL_ALREADY_COMPLETE',flush=True);return
        unit='cpucond69-completion74-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]+'.service'
        atomic(marker,(unit+'\n').encode())
        status(job,'STARTING_CONTROLLER',unit=unit)
        argv=['systemd-run','--unit='+unit,'--property=Type=exec','--property=Restart=no',
              '--property=RuntimeMaxSec=infinity','--property=MemoryMax=96G',
              '--property=TasksMax=256','--property=TimeoutStopSec=20','--property=KillMode=control-group',
              '--property=StandardOutput=append:'+str(job/'run.log'),
              '--property=StandardError=append:'+str(job/'run.log'),
              '--setenv=CPUCOND_BATCH_UNIT='+unit,'--setenv=PYTHONDONTWRITEBYTECODE=1',
              '--working-directory='+str(job/'work'),'/usr/bin/python3','-B','-u',
              str(control/'goal0074_finish_all.py'),'--worker','--job',str(job)]
        try: command(argv,stdin=subprocess.DEVNULL)
        except Exception as e:
            status(job,'LAUNCH_FAILED',error=type(e).__name__+':'+str(e));raise
        print('FINISH_ALL_SERVICE_STARTED\nunit='+unit+'\njob='+str(job),flush=True)
        print('現在のセッションが動いていれば、終了を待って自動引き継ぎします。全体時間上限はありません。',flush=True)

def watched_jobs(plan,job):
    a=plan['resource_amendment']
    paths=[Path(a['parent_job']),Path(a['supplement_job']),job]
    for p in paths:need(p.is_absolute() and p.parent==Path('/root') and not p.is_symlink(),'監視対象のパスが不正')
    return paths

def wait_for_idle(job,plan,self_unit,query=unit_state,sleep=time.sleep):
    last=None
    while True:
        busy=[]
        for other in watched_jobs(plan,job):
            marker=other/'active-unit.txt'
            if not marker.exists():continue
            u=read(marker).decode().strip()
            if u==self_unit:continue
            if live_state(query(u)):busy.append(u)
        if not busy:return
        status(job,'WAITING_FOR_CURRENT_SESSION',unit=self_unit,waiting_units=busy,
               automatic_handover=True,model_calls_by_waiter=0)
        if busy!=last:
            print('FINISH_ALL_WAITING_AUTO_HANDOVER\n現在のセッションは中断しません: '+', '.join(busy),flush=True)
            last=busy
        sleep(60)

def load_base(work):
    expected_origin(work)
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(work))
    spec=importlib.util.spec_from_file_location('cpucond74_frozen_base',work/'goal0069_batch_codegen.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def previous_safe(job):
    p=job/'results/summary.json'
    if not p.exists():return
    x=load(p)
    need(x.get('current_session',{}).get('plan_sha256')==PLAN_SHA,'直前の結果の計画が異なります')
    need(x.get('completion')!='DATASET_BATCH_BLOCKED' and not x.get('current_session',{}).get('errors'),
         '直前のセッションに環境/記録エラーがあります。無条件で再開しません')

def worker(job):
    need_host(job);control=job/CONTROL;verify_kit(control);plan=expected_origin(job/'work')
    unit=os.environ.get('CPUCOND_BATCH_UNIT','')
    need(re.fullmatch(r'cpucond69-completion74-[A-Za-z0-9-]+\.service',unit) is not None,'管理サービス名不正')
    need(unit in Path('/proc/self/cgroup').read_text(),'実際のsystemd所属が不一致')
    props=command(['systemctl','show',unit,'-p','RuntimeMaxUSec','--value'],capture_output=True,text=True).stdout.strip()
    need(props=='infinity','管理側の総時間上限が残っています: '+props)
    with open('/var/lock/cpucond-completion74-worker.lock','a') as exclusive:
        fcntl.flock(exclusive,fcntl.LOCK_EX|fcntl.LOCK_NB)
        wait_for_idle(job,plan,unit)
        previous_safe(job)
        # This checks hashes, both old jobs, no duplicate old attempts, and the
        # existing experiment lock. It runs before publishing our active unit.
        command(['/usr/bin/python3','-B',str(job/'work/goal0073_resource_amendment.py'),
                 '--check-ready','--job',str(job)],stdin=subprocess.DEVNULL)
        b=load_base(job/'work')
        summary=b.results_summary(plan,job/'results')
        prior=job/'results/summary.json'
        if prior.exists() and completed(load(prior)):
            status(job,'ALL_DONE_ALREADY',summary=summary);print('FINISH_ALL_COMPLETE',flush=True);return 0
        snapshot=control/('handover-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:6]);snapshot.mkdir()
        for rel in ('active-unit.txt','results/summary.json','results/progress.json'):
            p=job/rel
            if p.is_file():write(snapshot/(p.name+'.before'),read(p))
        write(snapshot/'receipt.json',encoded({'utc':now(),'unit':unit,'plan_sha256':PLAN_SHA,
            'counts_before':summary,'new_model_requests_not_yet_sent':True,
            'global_time_limit_seconds':None,'per_request_timeout_unchanged':True}))
        atomic(job/'active-unit.txt',(unit+'\n').encode())
        status(job,'RUNNING_UNTIL_COMPLETE',unit=unit,counts_before=summary)
        code=read(control/'until_complete_pipeline.py').decode()
        tree=ast.parse(code)
        need(len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef) and
             tree.body[0].name=='run_pipeline_until_complete','制御関数の構造が不正')
        # The scheduling-only function uses the verified original namespace,
        # including unmodified validators, streaming transport and model options.
        exec(compile(code,str(control/'until_complete_pipeline.py'),'exec'),b.__dict__)
        print('FINISH_ALL_RUNNING\n全体の時間上限なし。未処理要求→検証→対象分の暫定計測まで実行します。',flush=True)
        rc=b.run_pipeline_until_complete(job/'work')
        final=load(job/'results/summary.json')
        if rc==0 and completed(final):
            status(job,'ALL_DONE',unit=unit,summary=final)
            print('FINISH_ALL_COMPLETE\n全要求の処理完了（全件の正しさ合格とは別）。契約は変更しません。',flush=True)
            return 0
        status(job,'BLOCKED_OR_INTERRUPTED',unit=unit,summary=final)
        print('FINISH_ALL_BLOCKED_OR_INTERRUPTED\n安全上の停止/外部停止です。自動再送しません。',flush=True)
        return 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--install-launch',action='store_true');g.add_argument('--worker',action='store_true')
    p.add_argument('--job',type=Path,default=JOB)
    args=p.parse_args()
    try:
        if args.install_launch:
            install(args.job,Path(__file__).resolve().parent);launch(args.job);return 0
        return worker(args.job)
    except Exception as e:
        if args.job==JOB and (args.job/CONTROL).is_dir():
            try:status(args.job,'BLOCKED',error=type(e).__name__+': '+str(e))
            except Exception:pass
        print('FINISH_ALL_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr,flush=True);return 1
if __name__=='__main__':raise SystemExit(main())
