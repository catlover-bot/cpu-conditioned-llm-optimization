#!/usr/bin/env python3
"""Read-only descriptive audit/export of the completed cpucond P0/P1/P2 campaign.
No candidate import, compilation, execution, model API, retry, or service mutation.
--collect writes a new report directory; --archive makes a separate full raw backup.
All comparisons are exploratory/descriptive; no significance or universal correctness claim.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import stat
import statistics
import subprocess
import sys
import tarfile
import tempfile
import uuid

ROOT = Path('/srv/research/cpucond-p012-zen2-v1')
P0 = Path('/srv/research/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent')
MODEL = 'qwen2.5-coder:32b-instruct-q4_K_M'
P0_HASH = '6abe9c69297a494c0f5df736da1c76d2d789f326567359dc32e3c7c293be848d'
LIVE = {'active','activating','deactivating','reloading'}
ID = re.compile(r'([a-z0-9-]+)__(MINI|SMALL|MEDIUM)__(C|IR)__(P[012])__s0')
BEGIN = '----- BEGIN ORIGINAL CODE -----\n'
END = '----- END ORIGINAL CODE -----'
P0_LINE = 'No CPU-specific model name or performance information is supplied. This is condition P0.'
MAX_JSON = 32 * 1024 * 1024

class Refuse(RuntimeError): pass

def need(ok, message):
    if not ok: raise Refuse(message)

def now(): return datetime.now(timezone.utc).isoformat()

def pairs(xs):
    d = {}
    for k,v in xs:
        need(k not in d, 'JSONキー重複: '+k); d[k]=v
    return d

def loads(raw):
    def bad(x): raise Refuse('JSONの非有限値: '+x)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def regular(path):
    path = Path(path)
    need(path.is_absolute(), '絶対パスではありません: '+str(path))
    for p in (path, *path.parents):
        need(not p.is_symlink(), 'リンクを拒否: '+str(p))
    need(path.is_file(), '通常ファイルがありません: '+str(path))
    return path

def digest(path):
    h=hashlib.sha256()
    with regular(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_json(path):
    p=regular(path); need(p.stat().st_size <= MAX_JSON, 'JSONが過大: '+str(p))
    return loads(p.read_bytes())

def relfile(root, name):
    need(isinstance(name,str) and '\\' not in name, '不正な相対パス')
    q=PurePosixPath(name)
    need(q.parts and not q.is_absolute() and '..' not in q.parts, '不正な相対パス: '+name)
    p=Path(root).joinpath(*q.parts)
    need(p.resolve().is_relative_to(Path(root).resolve()), 'パス範囲外')
    return regular(p)

def dump(path, x):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')

def positive(x, name):
    need(type(x) in (int,float) and math.isfinite(x) and x>0, '不正な正数: '+name)
    return float(x)

def flag(obj, key, default=None):
    x=obj.get(key,default); need(type(x) is bool,'真偽値が不正: '+key); return x

def close(a,b): return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-12)

def geom(xs):
    return math.exp(statistics.fmean(math.log(positive(x,'幾何平均')) for x in xs)) if xs else None

def qsummary(rows, identity=False):
    warnings=[]
    for key,label in (('speedup','ratio'),('reference_ns','reference'),('candidate_ns','candidate')):
        x=[positive(r[key],key) for r in rows]; q=statistics.quantiles(x,n=4,method='inclusive')
        if (q[2]-q[0])/statistics.median(x)>0.10: warnings.append(label+'_variable')
    m=statistics.median([r['speedup'] for r in rows])
    if identity and abs(math.log(m))>math.log(1.02): warnings.append('identity_shift')
    return {'median_speedup':m,'warnings':warnings}

def audit_timing(rows, stored, identity=False):
    need(isinstance(rows,list) and len(rows)==16,'計測行数が16ではありません')
    seen=set(); groups={0:[],1:[]}
    for r in rows:
        s,t=r.get('session'),r.get('trial')
        need(type(s) is int and s in groups and type(t) is int and 0<=t<8,'計測ID不正')
        need((s,t) not in seen,'計測ID重複'); seen.add((s,t))
        a=positive(r['reference_ns'],'reference_ns'); b=positive(r['candidate_ns'],'candidate_ns')
        need(close(positive(r['speedup'],'speedup'),a/b),'保存済み速度比と計測値が不一致')
        groups[s].append(r)
    calculated=[qsummary(groups[s],identity) for s in (0,1)]
    if abs(math.log(calculated[0]['median_speedup']/calculated[1]['median_speedup']))>math.log(1.03):
        for c in calculated:c['warnings'].append('session_change')
    need(isinstance(stored,list) and len(stored)==2,'計測要約が2組ではありません')
    for c,v in zip(calculated,stored):
        need(close(c['median_speedup'],v['median_speedup']) and c['warnings']==v['warnings'],
             '計測品質の再計算と記録が不一致')
    return geom([x['median_speedup'] for x in calculated]), not any(x['warnings'] for x in calculated)

def key(item):
    m=ID.fullmatch(item['id']); need(m is not None,'要求ID不正: '+str(item.get('id')))
    k,s,f,c=m.groups()
    need((k,s,f,c)==(item.get('task'),item.get('size'),item.get('form'),item.get('condition')),'要求IDと属性が不一致')
    return (k,s,f)

def summarize(rows):
    good=[r['speedup'] for r in rows if r['measurement_valid']]
    return {
      'planned':len(rows), 'saved':sum(r['generation_status']=='saved' for r in rows),
      'official_passed':sum(r['official_passed'] for r in rows),
      'multiinput_passed':sum(r['multiinput_status']=='passed' for r in rows),
      'multiinput_not_implemented':sum(r['multiinput_status']=='not_implemented_for_task' for r in rows),
      'measurement_eligible':sum(r['measurement_eligible'] for r in rows),
      'measurement_valid':len(good),'observed_faster':sum(s>1 for s in good),
      'observed_slower':sum(s<1 for s in good),'observed_equal':sum(s==1 for s in good),
      'faster_fraction_of_all_requests':sum(s>1 for s in good)/len(rows) if rows else None,
      'measured_only_speedup_geomean':geom(good),
      'measured_only_speedup_median':statistics.median(good) if good else None,
      'generation_status_counts':dict(Counter(r['generation_status'] for r in rows)),
      'validation_status_counts':dict(Counter(r['validation_status'] for r in rows)),
      'failed_details':[{k:r[k] for k in ('id','generation_status','generation_error','validation_status','validation_errors','measurement_errors')}
          for r in rows if r['generation_status']!='saved' or not r['official_passed'] or r['multiinput_status']=='failed' or r['validation_status']=='validation_error' or (r['measurement_eligible'] and not r['measurement_valid'])]}

def paired(left,right,keys):
    # left is the comparison reference. Conditional speed statistics exclude neither side silently.
    counts=Counter(); ratios=[]
    for k in sorted(keys):
        a,b=left[k],right[k]
        counts[f'official_{int(a["official_passed"])}{int(b["official_passed"])}']+=1
        if a['measurement_valid'] and b['measurement_valid']:
            ratio=b['speedup']/a['speedup'];ratios.append(ratio)
            counts['right_faster' if ratio>1 else 'left_faster' if ratio<1 else 'observed_equal']+=1
        else:counts['no_usable_paired_speed']+=1
    return {'paired_requests':len(keys),'contingency':dict(counts),'both_measurement_valid':len(ratios),
      'conditional_geomean_right_over_left':geom(ratios),
      'conditional_median_right_over_left':statistics.median(ratios) if ratios else None,
      'note':'速度比較は双方で計測品質を満たす共通候補だけ。別時間帯の参照に対する比の比較であり、同時再測定や有意差検定ではない。'}

class Reader:
    def __init__(self): self.files={}
    def json(self,p):
        p=regular(p);x=read_json(p);self.files[str(p)]=digest(p);return x
    def hash(self,p):
        p=regular(p);h=digest(p);self.files[str(p)]=h;return h
    def text(self,p):
        p=regular(p);self.hash(p);return p.read_text(encoding='utf-8')

def read_condition(label,job,expected,reader):
    w=job/'work';r=job/'results';plan=reader.json(w/'plan.json');s=reader.json(r/'summary.json')
    need(plan['model']==MODEL and plan['prompt_language']=='en' and plan['conditions']==[label],'モデル・言語・条件が不一致')
    need(plan['requests']==expected and len(plan['tasks'])==expected,'計画件数不一致')
    need(s['completion']=='DATASET_BATCH_COMPLETE','条件が完了していません: '+label)
    for name in ('planned_requests','generation_terminal','validation_terminal'):
        need(type(s.get(name)) is int and s[name]==expected,'最終要約の件数不一致: '+label+'/'+name)
    need(s.get('requests_pending')==0 and s.get('measurement_pending')==0,'未処理があります')
    result={};baseline_cache={};requests={}
    instances={(i['task'],i['size']):i for i in plan['instances_list']}
    for item in plan['tasks']:
        k=key(item); need(k not in result,'課題の重複'); tid=item['id']
        reqpath=relfile(w,item['request']);need(reader.hash(reqpath)==item['request_sha256'],'送信要求ハッシュ不一致')
        req=reader.json(reqpath); requests[k]=req
        src=relfile(w,item['source']);sourcehash=reader.hash(src)
        need(sourcehash==instances[k[:2]]['sources'][k[2]]['sha256'],'入力コードハッシュ不一致')
        need(req['model']==MODEL and req['raw'] is True,'生成要求のモデル・形式が違います')
        need(req['prompt'].count(BEGIN)==1 and req['prompt'].count(END)==1,'プロンプトのコード区切り不一致')
        need(req['prompt'].split(BEGIN)[1].split(END)[0]==reader.text(src).rstrip()+'\n','入力全文がプロンプトと不一致')
        g=reader.json(r/'generation'/tid/'result.json');v=reader.json(r/'validation'/tid/'result.json')
        actual_request=r/'generation'/tid/'request.json'
        if actual_request.exists():need(reader.json(actual_request)==req,'保存した実送信要求が計画と不一致')
        for optional in ('started.json','response.raw.json','transport-receipt.json'):
            op=r/'generation'/tid/optional
            if op.exists():reader.json(op)
        need(isinstance(g.get('status'),str),'生成状態がありません')
        official=flag(v,'official_all_passed');eligible=flag(v,'measurement_eligible_provisional')
        multi=v['multiinput_status']; need(multi in ('passed','failed','not_run','not_implemented_for_task'),'追加検証状態が未知')
        if g['status']=='saved':
            candidate=r/'generation'/tid/('candidate.c' if k[2]=='C' else 'candidate.ll')
            need(reader.hash(candidate)==g['code_sha256'],'生成コードハッシュ不一致')
        else: need(not official and not eligible,'生成失敗なのに合格しています')
        if official:
            prof=v.get('official_profiles',[])
            need(len(prof)==3 and {x['profile'] for x in prof}=={'generic','native','sanitized'},'公式入力検査の条件不足')
            need(all(flag(x,'passed') for x in prof),'公式入力の検査要約不一致')
        need(eligible==(official and multi in ('passed','not_implemented_for_task')),'計測対象判定が不一致')
        mpath=r/'measurement'/tid/'result.json';m=reader.json(mpath) if mpath.exists() else None
        need((m is not None)==eligible,'計測記録の有無と対象判定が不一致')
        valid=flag(m,'measurement_valid') if m is not None else False
        speed=None
        if m is not None and m.get('rows') is not None:
            calculated,quality=audit_timing(m['rows'],m['session_summaries'])
            need(close(calculated,positive(m['speedup'],'summary speedup')),'速度倍率集計が不一致')
            need(valid==quality,'計測品質判定が不一致')
        if valid:
            need(m.get('rows') is not None,'計測品質合格なのに計測行がありません')
            name=k[0]+'__'+k[1]
            if name not in baseline_cache:
                baseline_cache[name]=reader.json(r/'baseline-timing'/name/'result.json')
            bt=baseline_cache[name]
            _,identity_good=audit_timing(bt['identity_rows'],bt['identity_sessions'],True)
            need(flag(bt,'valid') and identity_good,'元コード同士の計測品質に問題があります')
            speed=float(m['speedup'])
        receipt=g.get('receipt',{})
        row={'condition':label,'kernel':k[0],'size':k[1],'form':k[2],'id':tid,
          'source_sha256':sourcehash,'generation_status':g['status'],'generation_error':g.get('error',''),
          'validation_status':v.get('status',''),'validation_errors':v.get('errors',[]),
          'official_passed':official,'multiinput_status':multi,'measurement_eligible':eligible,
          'measurement_valid':valid,'speedup':speed,'measurement_errors':m.get('errors',[]) if m else [],
          'input_tokens':receipt.get('input_tokens'),'output_tokens':receipt.get('output_tokens'),
          'eval_duration_ns':receipt.get('eval_duration_ns'),
          'generation_runtime':s.get('generation_runtime_revision','sequential-P0'),
          'request_sha256':item['request_sha256'],'candidate_sha256':g.get('code_sha256'),
          'same_budget_p0_key': '__'.join(k)+'__P0__s0'}
        result[k]=row
    check=summarize(list(result.values()))
    for recorded,calculated in (('generated_texts','saved'),('official_gate_passed','official_passed'),
                               ('measurement_quality_passed','measurement_valid'),
                               ('measurement_eligible_provisional','measurement_eligible')):
        need(s[recorded]==check[calculated],'実ファイルと最終要約が不一致: '+label+'/'+recorded)
    return result,plan,requests,s

def verify_prompt_pair(a,b,block):
    need(a['prompt'].count(P0_LINE)==1 and b['prompt'].count(block)==1,'CPU説明ブロックが一意ではありません')
    normalized=dict(b); normalized['prompt']=b['prompt'].replace(block,P0_LINE,1)
    need(normalized==a,'CPU説明以外の要求設定が違います')

def current_host_idle(chain,p0):
    need(socket.gethostname()=='cpucond-zen2-01','想定したサーバーではありません')
    status=read_json(chain/'dual-numa-v1/status.json')
    need(status.get('phase')=='DUAL_NUMA_ALL_COMPLETE','連続実行が完了していません')
    for pointer in (chain/'dual-numa-v1/active-unit.txt',chain/'P1/active-unit.txt',
                    chain/'P2/active-unit.txt',p0/'completion-driven-v1/active-unit.txt'):
        if not pointer.exists(): continue
        unit=regular(pointer).read_text().strip()
        need(re.fullmatch(r'cpucond[A-Za-z0-9-]+\.service',unit),'サービス名不正')
        c=subprocess.run(['systemctl','show',unit,'-p','ActiveState','--value'],capture_output=True,text=True,timeout=15)
        need(c.returncode==0,'サービス確認に失敗: '+unit)
        need(c.stdout.strip() not in LIVE,'処理がまだ動いています: '+unit)
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
        except OSError:continue
        if not args:continue
        name=Path(args[0]).name
        need(not (name in ('llama-server','ollama_llama_server') or (name=='ollama' and any(x in ('serve','runner') for x in args))),
             '推論プロセスが残っています: '+p.name)
    lock=open('/var/lock/cpucond-batch-codegen.lock','a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:lock.close();raise Refuse('検証・計測ロックが使用中です')
    return lock

def encode_csv(path,rows):
    need(bool(rows),'CSV行がありません')
    with Path(path).open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})

def build_report(chain,p0,out,expected=(166,180,180),verify_p0_hash=True):
    reader=Reader(); campaign=reader.json(chain/'control/campaign.json')
    for optional in (chain/'control/hardware-profile.json',chain/'dual-numa-v1/status.json',chain/'p0-completion-receipt.json'):
        if optional.exists():reader.json(optional)
    if verify_p0_hash: need(reader.hash(p0/'work/plan.json')==P0_HASH,'P0計画の版が違います')
    cohorts={};plans={};requests={};summaries={}
    jobs={'P0':p0,'P1':chain/'P1','P2':chain/'P2'}
    for (label,job),n in zip(jobs.items(),expected):
        print(label+': 個別の生成・検証記録と計測値を照合中...',flush=True)
        cohorts[label],plans[label],requests[label],summaries[label]=read_condition(label,job,n,reader)
        if label!='P0':need(reader.hash(job/'work/plan.json')==campaign['plans_sha256'][label],'条件計画が登録記録と不一致')
    shared=set(cohorts['P0']);allkeys=set(cohorts['P1'])
    need(allkeys==set(cohorts['P2']) and shared<=allkeys,'条件間の要求集合が一致しません')
    need({r['id'] for r in cohorts['P0'].values()}==set(campaign['same_budget_comparison_ids']),'固定した共通集合と不一致')
    blocks={label:reader.text(chain/f'control/{label}-hardware-block.txt').rstrip('\n') for label in ('P1','P2')}
    for k in sorted(allkeys):
        need(cohorts['P1'][k]['source_sha256']==cohorts['P2'][k]['source_sha256'],'P1/P2の入力コード不一致')
        a=dict(requests['P1'][k]); a['prompt']=a['prompt'].replace(blocks['P1'],P0_LINE,1)
        verify_prompt_pair(a,requests['P2'][k],blocks['P2'])
        if k in shared:
            need(cohorts['P0'][k]['source_sha256']==cohorts['P1'][k]['source_sha256'],'P0/P1の入力コード不一致')
            verify_prompt_pair(requests['P0'][k],requests['P1'][k],blocks['P1'])
    scopes={'all_available':{l:set(r) for l,r in cohorts.items()},
            'same_input_budget_common':{l:shared for l in cohorts}}
    stats={}
    for scope,sel in scopes.items():
        stats[scope]={}
        for label,keys in sel.items():
            stats[scope][label]={}
            for form in ('ALL','C','IR'):
                rows=[cohorts[label][k] for k in sorted(keys) if form=='ALL' or k[2]==form]
                stats[scope][label][form]=summarize(rows)
    comps={}
    for left,right,keys,name in (('P0','P1',shared,'P1_vs_P0_common'),('P0','P2',shared,'P2_vs_P0_common'),
                                 ('P1','P2',allkeys,'P2_vs_P1_all')):
        comps[name]={f:paired(cohorts[left],cohorts[right],{k for k in keys if f=='ALL' or k[2]==f}) for f in ('ALL','C','IR')}
    caveats=['記述集計のみ。有意差検定・全入力での意味的同値証明ではない。',
      '公式入力合格と多入力合格を分離。未実装を合格扱いしない。',
      '品質合格は高速化と同義ではない。高速化率の分母には不合格・生成失敗も残す。',
      '条件別幾何平均は各条件の品質合格群のみ。生存候補が異なるため、その値だけで条件の優劣を決めない。',
      'P0は逐次、P1/P2は並列推論。実行時期も異なる。共通166要求でもこれらの交絡は解消しない。',
      '旧予算のP0の14要求は対応比較から除外し、原本バックアップでは保持する。',
      '原本の低レベルstdoutを全件再実行・再解釈したものではない。保存済みの計測行・要約を再計算した。']
    summary={'completion':'P012_DESCRIPTIVE_EXPORT_COMPLETE','utc':now(),
      'source_counts':dict(zip(jobs,expected)),'comparisons':comps,'statistics':stats,'caveats':caveats,
      'new_model_calls':0,'new_compilations':0,'new_benchmark_executions':0}
    out.mkdir(parents=True,exist_ok=False)
    report=out/'analysis';report.mkdir()
    dump(report/'summary.json',summary)
    allrows=[cohorts[label][k] for label in cohorts for k in sorted(cohorts[label])]
    encode_csv(report/'candidate-results.csv',allrows)
    pairedrows=[]
    for k in sorted(allkeys):
        rr={'kernel':k[0],'size':k[1],'form':k[2],'same_budget_common':k in shared}
        for label in cohorts:
            r=cohorts[label].get(k,{})
            for f in ('generation_status','official_passed','multiinput_status','measurement_valid','speedup'):
                rr[label+'_'+f]=r.get(f)
        pairedrows.append(rr)
    encode_csv(report/'paired-results.csv',pairedrows)
    reportlines=['=== P0/P1/P2 保存済み結果の記述集計 ===']
    for scope in stats:
        reportlines+=['','【'+('全要求（P0の分母は166、P1/P2は180）' if scope=='all_available' else '同じ入力・生成予算の共通要求。実行方式は異なる')+'】']
        for label in cohorts:
            for f in ('ALL','C','IR'):
                s=stats[scope][label][f]
                gm=s['measured_only_speedup_geomean'];gs='未計測' if gm is None else f'{gm:.6f}'
                reportlines.append(f'{label}/{f}: 予定={s["planned"]} 保存={s["saved"]} 公式一致={s["official_passed"]} 追加検証合格={s["multiinput_passed"]} 品質合格={s["measurement_valid"]} 観測倍率>1={s["observed_faster"]} <1={s["observed_slower"]} 条件内品質合格群の幾何平均={gs}')
    for name,forms in comps.items():
        reportlines+=['','【'+name+'】']
        for f,p in forms.items():
            gm=p['conditional_geomean_right_over_left'];gs='なし' if gm is None else f'{gm:.6f}'
            reportlines.append(f'{f}: 対応数={p["paired_requests"]} 両方品質合格={p["both_measurement_valid"]} 速度比の幾何平均(右/左)={gs} 採否と勝敗={p["contingency"]}')
    failed=[r for r in allrows if r['generation_status']!='saved']
    reportlines+=['','【生成が成功扱いにならなかった要求】']
    reportlines += [r['id']+': '+r['generation_status']+' '+str(r['generation_error']) for r in failed] or ['なし']
    reportlines += ['','【注意】',*caveats]
    reporttext='\n'.join(reportlines)+'\n';(report/'report-ja.txt').write_text(reporttext,encoding='utf-8')
    # Preserve the source records used to calculate the report. Binary objects and model weights are not in the light bundle.
    allowed_bases=[p0,chain]
    for full,h in reader.files.items():
        source=Path(full)
        need(digest(source)==h,'解析中に入力が変更: '+full)
        base=next((b for b in allowed_bases if source.is_relative_to(b)),None)
        need(base is not None,'未承認の資料パス')
        rel=Path('p0-current' if base==p0 else 'campaign')/source.relative_to(base)
        dest=report/'source-records'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,dest)
    source_entries=[{'path':p,'sha256':h} for p,h in sorted(reader.files.items())]
    dump(report/'integrity-receipt.json',{'created_utc':now(),'inputs_read':source_entries,
      'raw_measurement_summary_recomputed':True,'source_files_modified':False,
      'source_stdout_independently_reexecuted':False,'full_raw_archive_is_separate':True})
    paths=sorted(p for p in report.rglob('*') if p.is_file())
    with (report/'SHA256SUMS').open('x') as f:
        for p in paths:f.write(digest(p)+'  '+p.relative_to(report).as_posix()+'\n')
    archive=out/'analysis-bundle.tgz'
    with tarfile.open(archive,'w:gz',compresslevel=3) as tf:tf.add(report,arcname='analysis')
    (out/'analysis-bundle.tgz.sha256').write_text(digest(archive)+'  analysis-bundle.tgz\n')
    print(reporttext,flush=True)
    print('P012_DESCRIPTIVE_EXPORT_COMPLETE\n保存先:',out,flush=True)
    return summary

def collect():
    lock=current_host_idle(ROOT,P0)
    try:
        base=Path('/srv/research/cpucond-final-exports');base.mkdir(exist_ok=True)
        out=base/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
        build_report(ROOT,P0,out)
        pointer=Path('/root/goal0077-current-export.path')
        temp=pointer.with_name(pointer.name+'.tmp-'+uuid.uuid4().hex)
        temp.write_text(str(out)+'\n');temp.replace(pointer)
    finally:lock.close()

def list_regular_files(root):
    need(root.is_absolute() and root.is_dir() and not root.is_symlink(),'バックアップ元不正: '+str(root))
    found=[]
    for directory,dirs,files in os.walk(root,followlinks=False):
        d=Path(directory)
        for name in dirs:need(not (d/name).is_symlink(),'バックアップ元にディレクトリリンク')
        for name in files:
            p=d/name
            need(not any(c in str(p) for c in '\n\r\t'),'ファイル名に制御文字')
            need(stat.S_ISREG(p.lstat().st_mode),'原本内の特殊ファイル・リンクを拒否: '+str(p))
            found.append(p)
    return sorted(found)

def archive_full(export):
    export=Path(export).resolve()
    need(export.parent==Path('/srv/research/cpucond-final-exports') and (export/'analysis/summary.json').is_file(),'書き出し先を確認できません')
    need(read_json(export/'analysis/summary.json')['completion']=='P012_DESCRIPTIVE_EXPORT_COMPLETE','解析書き出し未完了')
    lock=current_host_idle(ROOT,P0)
    receipt=read_json(export/'analysis/integrity-receipt.json')
    for entry in receipt['inputs_read']:
        need(digest(Path(entry['path']))==entry['sha256'],'集計後に入力が変更: '+entry['path'])
    target=export/'full-experiment.tgz';part=export/'full-experiment.tgz.partial'
    try:
        need(not target.exists() and not part.exists(),'既存のバックアップを上書きしません')
        campaign=read_json(ROOT/'control/campaign.json')
        legacy=Path(campaign['full_p0_job']);supp=Path(campaign['supplement_p0_job'])
        need(legacy==Path('/srv/research/cpucond-batch-en-20260912T074659-7093'),'旧P0パス不一致')
        need(supp==Path(str(legacy)+'-context6-v1'),'旧補完パス不一致')
        roots=[P0,ROOT,legacy,supp]
        # Include token audit report (not its venv), needed for context admission provenance.
        token_report=Path('/srv/research/cpucond-token-audit-20260912T102556/report')
        if token_report.is_dir():roots.append(token_report)
        files=[p for root in roots for p in list_regular_files(root)]
        need(len(files)==len(set(files)),'バックアップのファイル重複')
        size=sum(p.stat().st_size for p in files)
        need(shutil.disk_usage(export).free > size*1.05+1024**3,'安全側に見積もったバックアップ空き容量が不足')
        print(f'原本バックアップ対象={len(files)} files、未圧縮={size/1024**3:.2f} GiB。モデル重みは含めません。',flush=True)
        index=export/'backup-index';index.mkdir()
        snapshot={}
        with (index/'SOURCE_SHA256SUMS').open('x') as out:
            for n,p in enumerate(files,1):
                before=p.stat();h=digest(p);after=p.stat()
                need((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'原本が更新されています')
                snapshot[str(p)]=(after.st_size,after.st_mtime_ns)
                out.write(h+'  '+p.relative_to('/root').as_posix()+'\n')
                if n%5000==0:print(f'原本ハッシュ {n}/{len(files)}',flush=True)
        dump(index/'manifest.json',{'created_utc':now(),'roots':[str(x) for x in roots],
           'regular_files':len(files),'uncompressed_bytes':size,'model_weights_included':False,
           'full_raw_generation_streams_and_measurements_included':True,'excluded':['model weights outside campaign paths','OS and Python environments']})
        filelist=index/'file-list.nul'
        filelist.write_bytes(b''.join(str(p.relative_to('/root')).encode()+b'\0' for p in files))
        argv=['tar','--format=pax']
        if shutil.which('pigz'):argv+=['-I','pigz -1 -p 8']
        else:argv+=['-z']
        argv+=['-cf',str(part),'-C','/root','--null','--verbatim-files-from','-T',str(filelist),
               '-C',str(export),'backup-index','analysis']
        print('原本を圧縮中。完了まではサーバーを終了しないでください。',flush=True)
        subprocess.run(argv,check=True,stdin=subprocess.DEVNULL)
        for name,old in snapshot.items():
            s=Path(name).stat();need(old==(s.st_size,s.st_mtime_ns),'アーカイブ中に原本が変更')
        part.rename(target)
        h=digest(target)
        (export/'full-experiment.tgz.sha256').write_text(h+'  full-experiment.tgz\n')
        dump(export/'backup-complete.json',{'completion':'P012_FULL_BACKUP_READY','utc':now(),
          'path':str(target),'bytes':target.stat().st_size,'sha256':h})
        print('P012_FULL_BACKUP_READY\n'+h+'  full-experiment.tgz',flush=True)
    finally:lock.close()

def main():
    a=argparse.ArgumentParser(description=__doc__)
    group=a.add_mutually_exclusive_group(required=True)
    group.add_argument('--collect',action='store_true')
    group.add_argument('--archive',type=Path)
    args=a.parse_args()
    try:
        if args.collect:collect()
        else:archive_full(args.archive)
    except (Refuse,OSError,ValueError,KeyError,subprocess.SubprocessError) as e:
        print('P012_EXPORT_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
