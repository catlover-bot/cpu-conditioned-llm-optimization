#!/usr/bin/env python3
"""Read-only audit/export of Goal 0079 v1.1 results. Never executes experiment code."""
from __future__ import annotations
import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import uuid

REV = 'revalidation-crosswalk-export-v1'
OLD_SHA = '7bb1725e871fd6c4377de7bd4cf5f299ded8c97d2b34c605062b9a723aca7b54'
EVIDENCE_SHA = '398c2af1dff04a390613f209fcdde99022ec251464a798742bc0cd2d4ec09c79'
VALIDATOR_SHA = '81dae012bfba1c7ebe2db583f3813dd96a828acdf540c701c733d1c4aeaf3f53'
COND_COUNTS = {'P0':166, 'P1':180, 'P2':179}
FORMS = {'C':'c', 'IR':'ll'}
PROFILES = {'measured_native','generic','sanitized'}
TASKS = set('2mm 3mm adi atax bicg cholesky correlation covariance deriche doitgen durbin fdtd-2d floyd-warshall gemm gemver gesummv gramschmidt heat-3d jacobi-1d jacobi-2d lu ludcmp mvt nussinov seidel-2d symm syr2k syrk trisolv trmm'.split())
ROOTS = {'P0':'analysis/source-records/p0-current', 'P1':'analysis/source-records/campaign/P1', 'P2':'analysis/source-records/campaign/P2'}

class AuditError(RuntimeError): pass

def need(ok, message):
    if not ok: raise AuditError(message)

def boolval(x):
    need(type(x) is bool, 'boolean required')
    return x

def positive(x):
    need(type(x) in (int,float) and math.isfinite(x) and x>0, 'finite positive value required')
    return float(x)

def unique_object(pairs):
    out={}
    for k,v in pairs:
        need(k not in out, 'duplicate JSON key: '+k); out[k]=v
    return out

def jloads(b):
    def bad(x): raise AuditError('nonfinite JSON: '+x)
    return json.loads(b, object_pairs_hook=unique_object, parse_constant=bad)

def hbytes(b): return hashlib.sha256(b).hexdigest()

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def safe_rel(text):
    p=PurePosixPath(text)
    need(not p.is_absolute() and p.parts and '..' not in p.parts and str(p)==text, 'unsafe path: '+text)
    need('\n' not in text and '\r' not in text and '\\' not in text, 'invalid path characters')
    return p

def local_file(root,rel):
    p=safe_rel(rel); q=root
    for part in p.parts:
        q=q/part
        need(not q.is_symlink(), 'symlink rejected: '+str(q))
    need(q.is_file(), 'missing regular file: '+str(q))
    return q

def read_bytes(root,rel,limit=32*1024*1024):
    q=local_file(root,rel)
    need(q.stat().st_size<=limit, 'file too large: '+rel)
    return q.read_bytes()

def read_json(root,rel): return jloads(read_bytes(root,rel))

def save_json(path,x):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')

def csvbool(x):
    need(x in ('True','False'), 'invalid CSV boolean'); return x=='True'

def task_id(tid):
    need(isinstance(tid,str) and re.fullmatch(r'[A-Za-z0-9_-]+',tid), 'bad ID')
    p=tid.split('__'); need(len(p)==5, 'bad tuple: '+tid)
    t,s,f,c,sample=p
    need(t in TASKS and s in ('MINI','SMALL','MEDIUM') and f in FORMS and c in COND_COUNTS and sample=='s0','bad tuple: '+tid)
    return t,s,f,c

def old_archive(path, expected=OLD_SHA):
    need(sha(path)==expected,'old analysis archive SHA mismatch')
    data={}; seen=set(); total=0
    with tarfile.open(path,'r:gz') as tf:
        for m in tf:
            safe_rel(m.name)
            need(m.name not in seen,'duplicate archive entry');seen.add(m.name)
            need(m.isdir() or m.isfile(), 'non-regular archive member')
            if not m.isfile(): continue
            need(0<=m.size<=32*1024*1024, 'archive member size')
            total+=m.size;need(total<=512*1024*1024, 'archive total size')
            f=tf.extractfile(m);need(f is not None,'archive read failure')
            b=f.read();need(len(b)==m.size,'short archive read');data[m.name]=b
    manifest=data.get('analysis/SHA256SUMS');need(manifest is not None,'old internal hashes absent')
    entries={}
    for line in manifest.decode('utf-8').splitlines():
        if not line: continue
        need(len(line)>66 and re.fullmatch(r'[0-9a-f]{64}',line[:64]) and line[64:66] in ('  ',' *'),'bad checksum line')
        rel=line[66:]
        if rel.startswith('./'):rel=rel[2:]
        safe_rel(rel);name='analysis/'+rel
        need(name not in entries,'duplicate manifest path');entries[name]=line[:64]
    need(set(entries)==set(data)-{'analysis/SHA256SUMS'},'old manifest inventory mismatch')
    for name,digest in entries.items():need(hbytes(data[name])==digest,'old internal hash mismatch: '+name)
    rows=list(csv.DictReader(io.StringIO(data['analysis/candidate-results.csv'].decode('utf-8'))))
    need(len(rows)==526,'old request count mismatch')
    index={}
    for r in rows:
        t,s,f,c=task_id(r['id'])
        need(r['condition']==c and r['kernel']==t and r['form']==f and r['size']==s,'old row tuple mismatch')
        need(r['id'] not in index,'duplicate old request ID');index[r['id']]=r
    need(collections.Counter(r['condition'] for r in rows)=={'P0':166,'P1':180,'P2':180},'old planned counts')
    need(sum(r['generation_status']=='saved' for r in rows)==525,'old saved count')
    return index,data

def inspect_new(job):
    root=job/'results'
    need(not (root/'failure.json').exists(),'failure.json present; no successful export')
    summary=read_json(root,'summary.json');progress=read_json(root,'progress.json')
    need(summary['completion']=='ALL30_REVALIDATION_COMPLETE','run not complete')
    need(summary['revision']=='all30-custom-fullstate-revalidation-v1.1','unexpected validator revision')
    need(summary['evidence_sha256']==EVIDENCE_SHA,'evidence SHA mismatch')
    need('clang version 18.1.3' in summary['clang'],'unexpected compiler')
    need(summary['model_calls']==0 and summary['performance_measurements']==0 and summary['old_labels_modified'] is False,'unexpected run scope')
    need(summary['formal_equivalence_proven'] is False,'unexpected proof flag')
    need(summary['saved_candidates']==525 and summary['validator_errors']==0,'run incomplete or validator error')
    need(summary['reference_kernel_size_pairs']==90 and summary['reference_test_cases']==180 and summary['test_cases_per_kernel_source_size']==2,'reference coverage mismatch')
    need(progress['completion']=='ALL30_REVALIDATION_COMPLETE' and progress['candidates_completed']==525 and progress['baselines_completed']==90,'progress incomplete')
    need(progress['script_sha256']==VALIDATOR_SHA,'validator SHA mismatch')
    inv=read_json(root,'candidate-inventory.json');need(type(inv) is list and len(inv)==525,'inventory count')
    index={}; refs={}; native_count=0
    for i in inv:
        tid=i['id'];t,s,f,c=task_id(tid)
        need(tid not in index,'duplicate candidate inventory')
        need((i['task'],i['size'],i['form'],i['condition'])==(t,s,f,c),'inventory tuple')
        source=local_file(root,f'extracted/candidates/{c}/{tid}/candidate.{FORMS[f]}')
        need(str(source)==i['source'],'source path mismatch')
        need(sha(source)==i['source_sha256'],'candidate source tamper')
        for form,ext in FORMS.items():
            op=local_file(root,f'extracted/originals/{t}/{s}/kernel.{ext}')
            digest=sha(op)
            need(digest==i['reference_c_sha256' if form=='C' else 'reference_ir_sha256'],'reference hash mismatch')
            refs[(t,s,form)]=digest
        path=f'results/{c}/{tid}/result.json'
        r=read_json(root,path)
        need((r['id'],r['task'],r['size'],r['form'],r['condition'])==(tid,t,s,f,c),'result identity mismatch')
        need(r['source_sha256']==i['source_sha256'],'result source hash')
        need(r['reference_c_sha256']==refs[(t,s,'C')] and r['reference_ir_sha256']==refs[(t,s,'IR')],'result reference hash')
        need(r['old_native_object']==i['old_native_object'],'old object pointer mismatch')
        if i['old_native_object'] is not None:
            native_count+=1
            op=local_file(root,f'extracted/candidates/{c}/{tid}/old-native.o')
            need(str(op)==i['old_native_object'],'old native object path')
            oldsha=sha(op)
        else: oldsha=None
        need(r['status'] in ('checked','rejected'),'validator failure or incomplete result')
        passed=boolval(r['passed']); reasons=[]
        if r['status']=='rejected':
            need(not passed and r['errors'],'invalid rejected result')
            reasons.extend(str(e) for e in r['errors'])
        else:
            need(not r['errors'],'unexpected checked errors')
            # Identity of the code objects that the recorded runs linked.
            need(set(r['profiles'])=={'generic','native','sanitized'},'compile profile set mismatch')
            for label,build in r['profiles'].items():
                if build.get('compile_state')=='ok':
                    fp=local_file(root,f'results/{c}/{tid}/{label}-compile-result.o')
                    need(sha(fp)==build['object_sha256'],'fresh object SHA mismatch')
                else:need(build.get('passed') is False,'failed compile marked passed')
            if 'old_native_sha256' in r:
                need(oldsha==r['old_native_sha256'],'stored old native SHA mismatch')
                fp=local_file(root,f'results/{c}/{tid}/native-compile-result.o')
                need(boolval(r['fresh_native_matches_old'])==(sha(fp)==oldsha),'fresh/old object comparison mismatch')
            need(len(r['cases'])==2 and {q['case'] for q in r['cases']}=={0,1},'two-case inventory mismatch')
            derived=True
            for case in r['cases']:
                ci=case['case'];need(type(ci) is int,'bad case number')
                need(set(case['profiles'])==PROFILES,'runtime profile set mismatch')
                oracle=read_bytes(root,f'baselines/{t}/{s}/case{ci}/ref-run.stdout')
                need(bool(oracle),'empty reference output')
                braw=read_bytes(root,f'baselines/{t}/{s}/case{ci}/base-run.stdout')
                need(braw==oracle,'trusted baseline differs')
                for name,detail in case['profiles'].items():
                    v=boolval(detail['passed']);derived &= v
                    prefix=f'results/{c}/{tid}/case{ci}-{name}-run'
                    if 'state' in detail:
                        command=read_json(root,prefix+'.command.json')
                        raw=read_bytes(root,prefix+'.stdout')
                        need(command['state']==detail['state'],'runtime status mismatch')
                        need(hbytes(raw)==detail['stdout_sha256'] and hbytes(oracle)==detail['oracle_sha256'] and len(raw)==detail['bytes'],'runtime hash mismatch')
                        need(v==(command['state']=='ok' and raw==oracle),'reported pass differs from stdout comparison')
                        if not v:reasons.append(f'case{ci}/{name}/'+('output_mismatch' if command['state']=='ok' else command['state']))
                    else:
                        need(not v and detail.get('reason') in ('compile_failed','link_failed'),'invalid unexecuted case')
                        reasons.append(f'case{ci}/{name}/'+detail['reason'])
            need(passed==derived,'pass flag differs from six checks')
        r['_old_native_actual_sha256']=oldsha;r['_failure_categories']=sorted(set(reasons))
        index[tid]=r
    need(native_count==371,'old native inventory mismatch')
    need(collections.Counter(r['condition'] for r in index.values())==COND_COUNTS,'new condition inventory mismatch')
    need(len(refs)==180,'reference source inventory mismatch')
    # All 90 reference pairs (including kernels with every candidate rejected).
    for t in sorted(TASKS):
        for s in ('MINI','SMALL','MEDIUM'):
            for ci in (0,1):
                for stem in ('ref-run','base-run'):
                    cmd=read_json(root,f'baselines/{t}/{s}/case{ci}/{stem}.command.json')
                    need(cmd['state']=='ok','baseline execution did not pass')
                need(read_bytes(root,f'baselines/{t}/{s}/case{ci}/ref-run.stdout')==read_bytes(root,f'baselines/{t}/{s}/case{ci}/base-run.stdout'),'baseline outputs differ')
    need(sum(r['passed'] for r in index.values())==summary['passed'],'summary passed mismatch')
    need(sum(not r['passed'] for r in index.values())==summary['failed'],'summary failed mismatch')
    for field,label in (('condition','by_condition'),('form','by_form')):
        for key,aggregate in summary[label].items():
            rows=[r for r in index.values() if r[field]==key]
            need(aggregate=={'saved':len(rows),'passed':sum(r['passed'] for r in rows)},'subgroup summary mismatch')
    return summary,index

def gm(x):return math.exp(sum(map(math.log,x))/len(x)) if x else None

def join_records(old,new,data):
    rows=[];alltrans=collections.Counter()
    for tid,o in old.items():
        t,s,f,c=task_id(tid);n=new.get(tid)
        saved=o['generation_status']=='saved'
        need(saved==(n is not None),'old/new saved inventory differs')
        if n:need(o['candidate_sha256']==n['source_sha256'] and o['source_sha256']==n['reference_c_sha256' if f=='C' else 'reference_ir_sha256'],'old/new source identity differs')
        off=csvbool(o['official_passed']);valid=csvbool(o['measurement_valid'])
        speed=positive(float(o['speedup'])) if valid else None
        newpass=n['passed'] if n else None
        transition=('old_pass' if off else 'old_not_pass')+'__'+('new_pass' if newpass else 'new_not_pass' if n else 'no_saved_code')
        alltrans[transition]+=1
        verified_old=False
        if valid:
            mpath=ROOTS[c]+f'/results/measurement/{tid}/result.json'
            need(mpath in data,'measurement record missing')
            m=jloads(data[mpath]);need(m['id']==tid and m['measurement_valid'] is True,'old measurement identity')
            need(math.isclose(positive(m['speedup']),speed,rel_tol=1e-12),'old speed mismatch')
            need(n is not None and n['_old_native_actual_sha256']==m['candidate_object_sha256'],'measured object identity mismatch')
            verified_old=True
        eligible= bool(newpass and off and valid and verified_old)
        rows.append({'id':tid,'condition':c,'kernel':t,'size':s,'form':f,
          'old_generation_status':o['generation_status'], 'old_validation_status':o['validation_status'],
          'old_validation_errors':o['validation_errors'], 'old_official_passed':off,
          'old_multiinput_status':o['multiinput_status'], 'new_status':n['status'] if n else 'no_saved_code',
          'new_passed':newpass, 'new_failure_categories':n['_failure_categories'] if n else [],
          'transition':transition, 'old_measurement_valid':valid,'historical_speedup':speed,
          'historical_object_hash_verified':verified_old,
          'new_checks_and_historical_timing_available':eligible,
          'source_sha256':n['source_sha256'] if n else None,
          'fresh_native_matches_old':n.get('fresh_native_matches_old') if n else None,
          'needs_old_official_recheck':bool(newpass and not off),
          'needs_performance_measurement_if_adopted':bool(newpass and not valid)})
    need(set(new)=={r['id'] for r in rows if r['source_sha256']},'joined new ID set mismatch')
    groups=[]
    for c in ('P0','P1','P2'):
        for form in ('ALL','C','IR'):
            rr=[r for r in rows if r['condition']==c and (form=='ALL' or r['form']==form)]
            eligible=[r for r in rr if r['new_checks_and_historical_timing_available']]
            groups.append({'condition':c,'form':form,'planned':len(rr),
              'new_passed':sum(r['new_passed'] is True for r in rr),
              'transitions':dict(collections.Counter(r['transition'] for r in rr)),
              'historical_measured_and_new_passed':len(eligible),
              'historical_speed_gt_1':sum(r['historical_speedup']>1 for r in eligible),
              'historical_survivor_geomean':gm([r['historical_speedup'] for r in eligible]),
              'new_pass_without_old_official_pass':sum(r['needs_old_official_recheck'] for r in rr),
              'new_pass_without_old_valid_timing':sum(r['needs_performance_measurement_if_adopted'] for r in rr)})
    keyed={(r['condition'],r['kernel'],r['size'],r['form']):r for r in rows}
    pairs=[]
    for a,b,common in (('P0','P1',True),('P0','P2',True),('P1','P2',False)):
        for form in ('ALL','C','IR'):
            basis=[r for r in rows if r['condition']==('P0' if common else 'P1') and (form=='ALL' or r['form']==form)]
            ratios=[];counts=collections.Counter()
            for r in basis:
                ra=keyed[(a,r['kernel'],r['size'],r['form'])];rb=keyed[(b,r['kernel'],r['size'],r['form'])]
                counts[f"new_{int(ra['new_passed'] is True)}{int(rb['new_passed'] is True)}"]+=1
                if ra['new_checks_and_historical_timing_available'] and rb['new_checks_and_historical_timing_available']:
                    ratios.append(rb['historical_speedup']/ra['historical_speedup'])
            pairs.append({'comparison':b+'_vs_'+a+('_common166' if common else '_all180'),'form':form,
                          'matched_requests':len(basis),'new_acceptance_pairs':dict(counts),
                          'both_old_quality_and_new_passed':len(ratios),
                          'historical_paired_ratio_geomean':gm(ratios)})
    return rows,{'overall_transitions':dict(alltrans),'groups':groups,'pairs':pairs,
                 'new_run_has_performance_measurements':False,
                 'filtered_historical_speeds_are_not_confirmation_measurements':True,
                 'new_tests_do_not_replace_old_tests':True,
                 'formal_equivalence_proven':False}

def export(job,oldpath,out):
    need(job.is_dir() and not job.is_symlink(),'bad run directory')
    need(not out.exists(),'output already exists')
    print('旧解析アーカイブのハッシュ・内部記録を照合...',flush=True)
    old,data=old_archive(oldpath)
    print('再検証525候補・180参照ケース・保存出力を照合...',flush=True)
    summary,new=inspect_new(job)
    rows,joined=join_records(old,new,data)
    out.mkdir(parents=True);stage=out/'revalidation-results';stage.mkdir()
    save_json(stage/'summary-joined.json',joined)
    save_json(stage/'revalidation-summary.json',summary)
    with (stage/'candidate-crosswalk.jsonl').open('x',encoding='utf-8') as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n')
    known=[r for r in rows if r['kernel'] in ('gesummv','heat-3d','floyd-warshall','nussinov')]
    save_json(stage/'known-issue-records.json',known)
    # Copy only data/code/object records; no linked executables, no scratch, no model files.
    suffixes={'.json','.stdout','.stderr','.c','.ll','.h','.o'}
    copied=[];snapshots=[]
    resultroot=job/'results'
    for directory,dirs,files in os.walk(resultroot,followlinks=False):
        d=Path(directory)
        for name in list(dirs):
            p=d/name;need(not p.is_symlink(),'symlink in results tree')
            if d==resultroot and name=='sandbox':dirs.remove(name)
        for name in sorted(files):
            p=d/name;need(not p.is_symlink(),'symlink result file')
            need(stat.S_ISREG(p.stat().st_mode),'nonregular result file')
            if p.suffix not in suffixes:continue
            rel=p.relative_to(job).as_posix();safe_rel(rel)
            b=p.read_bytes();need(len(b)<=32*1024*1024,'record too large')
            dest=stage/'records'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
            snapshots.append((p,hbytes(b)));copied.append('records/'+rel)
    for name in ('run.log','active-unit.txt','implementation.path','source-job.path'):
        p=job/name
        if not p.exists():continue
        b=read_bytes(job,name,64*1024*1024);dest=stage/'records'/name;dest.write_bytes(b);snapshots.append((p,hbytes(b)))
    impl=Path(read_bytes(job,'implementation.path').decode().strip())
    source=local_file(impl,'goal0079_revalidate_all30_v1_1.py')
    need(sha(source)==VALIDATOR_SHA,'implementation file hash mismatch')
    (stage/'validator-v1.1.py').write_bytes(source.read_bytes())
    report=['=== 再検証と旧判定の対応 ===','全要求526、保存525。再生成・再実行・新たな計測はしません。']
    for g in joined['groups']:
        v=g['historical_survivor_geomean'];avg='なし' if v is None else f'{v:.6f}'
        report.append(f"{g['condition']}/{g['form']}: 分母={g['planned']} 新検証合格={g['new_passed']} 旧品質合格かつ新検証合格={g['historical_measured_and_new_passed']} 旧速度の条件付き幾何平均={avg}")
        report.append('  判定の対応='+json.dumps(g['transitions'],ensure_ascii=False))
    report+=['','旧不合格→新合格は、旧入力での再確認が必要です。即座に最終合格へ変更しません。',
             '表示した速度は既存測定値の再抽出です。新しい確認計測ではありません。',
             '小さい2入力の合格は、全入力での同値証明でも、旧テストの代替でもありません。',
             '共通166要求とP1/P2全180要求を分離。推論方式・測定時期の違いは残ります。']
    report='\n'.join(report)+'\n';(stage/'report-ja.txt').write_text(report,encoding='utf-8')
    for p,digest in snapshots:need(sha(p)==digest,'file changed while collecting: '+str(p))
    receipt={'completion':'REVALIDATION_RESULTS_EXPORT_COMPLETE','created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
       'revision':REV,'source_job':str(job),'old_analysis_sha256':sha(oldpath),
       'validator_sha256':VALIDATOR_SHA,'collector_sha256':sha(__file__),
       'requests':526,'saved_candidates':525,'new_passed':summary['passed'],
       'result_record_files':len(copied),'source_files_modified':False,'model_calls':0,'code_executions':0,
       'performance_measurements':0,'formal_equivalence_proven':False}
    save_json(stage/'export-receipt.json',receipt)
    entries=[]
    for p in sorted(stage.rglob('*')):
        if p.is_file():entries.append((p.relative_to(stage).as_posix(),sha(p)))
    (stage/'SHA256SUMS').write_text(''.join(f'{h}  {n}\n' for n,h in entries),encoding='utf-8')
    tarpath=out/'revalidation-results.tgz'
    with tarfile.open(tarpath,'w:gz',compresslevel=1) as tf:
        tf.add(stage,arcname='revalidation-results',recursive=True)
    digest=sha(tarpath)
    (out/'revalidation-results.tgz.sha256').write_text(digest+'  revalidation-results.tgz\n',encoding='ascii')
    print(report,flush=True);print('REVALIDATION_RESULTS_EXPORT_COMPLETE');print('共有用:',tarpath);print('SHA-256:',digest)
    return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--job',type=Path,required=True);ap.add_argument('--old-analysis',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    try: export(a.job,a.old_analysis,a.out)
    except (AuditError,OSError,ValueError,KeyError) as e:
        print('REVALIDATION_EXPORT_BLOCKED: '+str(e),file=__import__('sys').stderr);raise SystemExit(1)
if __name__=='__main__':main()
