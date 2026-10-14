#!/usr/bin/env python3
"""Fixed-ledger, matched C/IR confirmation. No LLM, no edits to old results.
Production compilation and execution are ONLY through the existing bwrap sandbox.
Two measurement rounds with balanced within-instance orders; no best-run selection.
"""
from __future__ import annotations
import argparse, collections, csv, fcntl, hashlib, json, math, os
from pathlib import Path
import random, re, shutil, signal, statistics, subprocess, sys, tarfile, time, uuid
from datetime import datetime, timezone
import batch_support as B

REV = 'matched-native-confirmation-v1'
LEDGER_SHA = '4133cb3199fd601779b9f24b421396898fd11041fa125b8e93151b04e16ba32f'
MAX_K = 65536
TARGET_NS = 5_000_000
SEED = 83001
ROUNDS = 2
CALL_TIMEOUT = 120
LINK_FLAGS = ['-no-pie']
CLOCK_SOURCE = '''#include <time.h>
#include <stdlib.h>
#include <fenv.h>
#include <xmmintrin.h>
void cpucond83_init_environment(void) {
  if(fesetround(FE_TONEAREST)) exit(91);
  _mm_setcsr(_mm_getcsr() & ~((1u<<15)|(1u<<6)));
}
unsigned long long cpucond83_clock(void) {
  struct timespec t;
  if(clock_gettime(CLOCK_MONOTONIC_RAW, &t)) exit(92);
  return (unsigned long long)t.tv_sec*1000000000ULL + (unsigned long long)t.tv_nsec;
}
'''

class Blocked(RuntimeError): pass

def need(x, message):
    if not x: raise Blocked(message)

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return B.sha(p)
def shab(b): return hashlib.sha256(b).hexdigest()
def load(p): return B.load(p)
def jw(p,x): B.jw(p,x)
def put(p,b): B.write(p,b)
def atomic(p,x): B.atomic(p,x)
def safe(root,rel): return B.safe(root,rel)
def positive(x):
    need(type(x) in (int,float) and math.isfinite(x) and x>0, 'non-positive/nonfinite time')
    return float(x)
def gmean(xs):
    return math.exp(statistics.fmean(math.log(positive(x)) for x in xs)) if xs else None

def verify_package(root):
    root=Path(root).resolve(); hashes=B.hm(root)
    for rel,h in hashes.items(): need(sha(safe(root,rel))==h,'package hash mismatch: '+rel)
    p=load(root/'plan.json')
    need(p['revision']==REV and p['ledger_sha256']==LEDGER_SHA,'wrong fixed ledger')
    need(sha(root/'ledger/report/eligibility.jsonl')==p['ledger_eligibility_sha256'],'ledger altered')
    rows=[B.loads(x) for x in (root/'ledger/report/eligibility.jsonl').read_text().splitlines()]
    need(rows==p['requests'],'ledger versus plan differs')
    need(len(rows)==526 and len({r['id'] for r in rows})==526,'wrong request universe')
    accepted={r['id']:r for r in rows if r['eligible_under_recorded_checks'] is True}
    need(len(accepted)==351,'wrong accepted universe')
    need(collections.Counter(r['form'] for r in accepted.values())=={'C':203,'IR':148},'form counts differ')
    need(collections.Counter(r['condition'] for r in accepted.values())=={'P0':106,'P1':119,'P2':126},'condition counts differ')
    need(len(p['instances'])==90 and len({g['id'] for g in p['instances']})==90,'wrong group universe')
    seen=set()
    for g in p['instances']:
        need(re.fullmatch(r'[A-Za-z0-9_-]+',g['id']) and g['id']==g['kernel']+'__'+g['size'],'invalid group id')
        need(len(g['cases'])==2 and set(g['sources'])=={'C','IR'},'incomplete references')
        refs=[*g['sources'].values(),g['driver']]
        for c in g['cases']: refs += [c['harness'],c['oracle']]
        for d in refs:
            need(sha(safe(root,d['path']))==d['sha256'],'input hash mismatch: '+d['path'])
        for v in g['candidates']:
            tid=v['id'];need(tid in accepted and tid not in seen,'ineligible/duplicate candidate')
            r=accepted[tid];seen.add(tid)
            need((r['kernel'],r['size'],r['form'],r['condition'])==(g['kernel'],g['size'],v['form'],v['condition']),'candidate metadata mismatch')
            need(v['source']['sha256']==r['source_sha256']==sha(safe(root,v['source']['path'])),'candidate source altered')
    need(seen==set(accepted),'candidate set not complete')
    return p

def check_busy():
    forbidden={'goal0069_batch_codegen.py','goal0054_final_physical_atlas.py',
               'goal0079_revalidate_all30.py','goal0079_revalidate_all30_v1_1.py'}
    found=[]
    for d in Path('/proc').iterdir():
        if not d.name.isdigit() or int(d.name)==os.getpid(): continue
        try: args=[x.decode(errors='replace') for x in (d/'cmdline').read_bytes().split(b'\0') if x]
        except OSError: continue
        names={Path(x).name for x in args}
        if 'llama-server' in names or 'ollama_llama_server' in names or (('ollama' in names) and ('serve' in args or 'runner' in args)) or names&forbidden:
            found.append(d.name)
    need(not found,'別の推論/検証/旧計測が稼働中です: '+','.join(found))

def host_record():
    need(os.geteuid()==0,'trusted launcher must be root; child programs are unprivileged')
    need(Path('/proc/sys/kernel/hostname').read_text().strip()=='cpucond-zen2-01','wrong host')
    need('AMD EPYC 7402' in Path('/proc/cpuinfo').read_text(),'wrong CPU')
    need(2 in os.sched_getaffinity(0) and Path('/sys/devices/system/cpu/cpu2/node0').exists(),'CPU2/node0 unavailable')
    states={}
    for file,want in [('/sys/devices/system/cpu/smt/active','0'),('/sys/devices/system/cpu/cpufreq/boost','0'),('/sys/devices/system/cpu/cpu2/cpufreq/scaling_governor','performance')]:
        value=Path(file).read_text().strip();need(value==want,'host setting changed: '+file);states[file]=value
    clang,cv=B.clang_path()
    opt=shutil.which('opt-18');need(opt,'opt-18 is required; not installing automatically')
    ov=subprocess.check_output([opt,'--version'],text=True,timeout=10)
    need('LLVM version 18.1.3' in ov,'LLVM verifier version changed')
    deps={}
    for path in ['/lib/x86_64-linux-gnu/libc.so.6','/lib/x86_64-linux-gnu/libm.so.6','/lib64/ld-linux-x86-64.so.2']:
        p=Path(path).resolve();need(p.is_file(),'missing runtime library '+path);deps[str(p)]=sha(p)
    return {'hostname':os.uname().nodename,'kernel_release':os.uname().release,
            'machine_id':Path('/etc/machine-id').read_text().strip(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'clang':clang,'clang_version':cv,'clang_sha256':sha(Path(clang).resolve()),
            'opt':opt,'opt_version':ov,'opt_sha256':sha(Path(opt).resolve()),
            'runtime_libraries':deps,'host_states':states,
            'randomize_va_space':Path('/proc/sys/kernel/randomize_va_space').read_text().strip()}

def timing_driver(source,function):
    """Use the archived initialization and dump verbatim; instrument only main.
    check mode runs the SAME executable at the selected K and dumps final output.
    No correctness oracle or other candidate is mounted inside the executable.
    """
    a,b,e=B.main_bounds(source);body=source[b+1:e-1]
    init=B.statement_calls(body,'init_array');call=B.statement_calls(body,function);dump=B.statement_calls(body,'print_array')
    need(len(init)==len(call)==len(dump)==1,'expected one init/kernel/dump in trusted driver')
    prefix=body[:init[0][0]]
    frees='\n'.join(x[2] for x in sorted(B.statement_calls(body,'free')+B.statement_calls(body,'polybench_free_data')))
    text='extern unsigned long long cpucond83_clock(void);\nextern void cpucond83_init_environment(void);\n'+source[:a]
    text+='''int main(int argc, char **argv) {
'''+prefix+'''
  if(argc != 2 && argc != 3) return 64;
  char *ep=0; long K=strtol(argv[1], &ep, 10);
  if(!ep || *ep || K<1 || K>65536) return 65;
  int check=(argc==3);
  cpucond83_init_environment();
'''+init[0][2]+call[0][2]+'''
  unsigned long long total=0;
  for(long rr=0;rr<K;++rr) {
'''+init[0][2]+'''
    __asm__ __volatile__("" ::: "memory");
    unsigned long long start=cpucond83_clock();
'''+call[0][2]+'''
    __asm__ __volatile__("" ::: "memory");
    unsigned long long end=cpucond83_clock();
    if(end<=start || total > (~0ULL)-(end-start)) return 66;
    total+=end-start;
  }
  if(check) {
'''+dump[0][2]+'''
  } else {
    printf("CPUCOND83_BATCH %ld %llu\\n",K,total);
  }
'''+frees+'\nreturn 0;\n}\n'
    return text

def parse_time(raw,k):
    m=re.fullmatch(rb'CPUCOND83_BATCH ([0-9]+) ([0-9]+)\n',raw)
    need(m is not None and int(m[1])==k and int(m[2])>0,'timing output malformed')
    return int(m[2])

def build(box,clang,src,stem,flags): return B.object_build(box,clang,src,stem,flags)
def link(box,clang,objs,stem): return B.link(box,clang,objs,stem,LINK_FLAGS)
def execute(box,program,stem,args=(),timeout=CALL_TIMEOUT):
    return B.execute_program(box,program,stem,args,timeout=timeout)

def make_utility(box,clang,plan,out):
    d=out/'shared';d.mkdir()
    inp={}
    for name,v in plan['utility_sources'].items():
        p=Path(v['server_path']);need(p.is_file() and not p.is_symlink() and sha(p)==v['sha256'],'archived utility changed/missing: '+str(p))
        dest=d/name;put(dest,p.read_bytes());inp[name]=dest
    rec,raw,_=box.call([clang,'-std=gnu11','-E','-P','-I/in','/in/polybench.c'],inp,d/'utility-preprocess',60)
    need(rec['state']=='ok','utility preprocessing failed')
    src=d/'utility-preprocessed.c';put(src,raw)
    util=build(box,clang,src,d/'utility',['-O0',*B.GENERIC])
    clock_src=d/'clock.c';put(clock_src,CLOCK_SOURCE)
    clock=build(box,clang,clock_src,d/'clock',['-O3',*B.GENERIC])
    return util,clock

def verify_ir(box,opt,src,stem):
    rec,raw,_=box.call([opt,'-passes=verify','-disable-output','/in/source.ll'],{'source.ll':src},stem,60)
    if rec['state']!='ok': raise B.CandidateFailure('LLVM18 structural check rejected input; '+str(stem))

def bind_files(root,d): return safe(root,d['path'])

def prepare_group(pkg,g,out,box,clang,opt,util,clock):
    d=out/'build'/g['id'];d.mkdir(parents=True)
    oc=bind_files(pkg,g['sources']['C']);oi=bind_files(pkg,g['sources']['IR']);driver=bind_files(pkg,g['driver'])
    official_o=build(box,clang,driver,d/'official-driver',['-O0',*B.GENERIC])
    ref_o0=build(box,clang,oc,d/'reference-o0',['-O0',*B.GENERIC])
    ref_exe=link(box,clang,[official_o,ref_o0,util],d/'reference-official')
    rec,oracle=execute(box,ref_exe,d/'reference-official-run')
    need(rec['state']=='ok' and bool(oracle) and shab(oracle)==g['official_output_sha256'], 'archived official reference mismatch: '+g['id'])
    custom=[]
    for i,c in enumerate(g['cases']):
        ho=build(box,clang,bind_files(pkg,c['harness']),d/f'case{i}-harness',['-O0',*B.GENERIC])
        exp=bind_files(pkg,c['oracle']).read_bytes()
        exe=link(box,clang,[ho,ref_o0],d/f'case{i}-reference')
        rec,raw=execute(box,exe,d/f'case{i}-reference-run')
        need(rec['state']=='ok' and raw==exp and raw,'reference custom-case mismatch: '+g['id'])
        custom.append((ho,exp))
    td=d/'timing-driver.c';put(td,timing_driver(driver.read_text(),g['function']))
    tdo=build(box,clang,td,d/'timing-driver',['-O3',*B.NATIVE])
    definitions=[{'label':'reference_C','form':'C','source':g['sources']['C'],'is_reference':True,'historical_native_object_sha256':g.get('historical_reference_c_object_sha256')},
                 {'label':'reference_IR','form':'IR','source':g['sources']['IR'],'is_reference':True}]
    definitions += [{**x,'label':x['id'],'is_reference':False} for x in g['candidates']]
    variants={}
    for v in definitions:
        vd=d/v['label'];vd.mkdir();src=bind_files(pkg,v['source'])
        info={k:v[k] for k in ('label','form','is_reference')}
        info.update({'source_sha256':sha(src),'ready':False,'errors':[]})
        try:
            if v['form']=='IR':verify_ir(box,opt,src,vd/'ir-verify')
            obj=build(box,clang,src,vd/'kernel',['-O3',*B.NATIVE])
            B.symbols_ok(box,obj,g['function'],vd/'symbols')
            exe=link(box,clang,[official_o,obj,util],vd/'official')
            rec,raw=execute(box,exe,vd/'official-run')
            if rec['state']!='ok' or raw!=oracle:raise B.CandidateFailure('official output recheck failed')
            for i,(ho,expected) in enumerate(custom):
                ce=link(box,clang,[ho,obj],vd/f'case{i}')
                rec,raw=execute(box,ce,vd/f'case{i}-run')
                if rec['state']!='ok' or raw!=expected:raise B.CandidateFailure(f'archived custom case {i} failed')
            program=link(box,clang,[tdo,clock,obj,util],vd/'timed')
            rec,raw=execute(box,program,vd/'timed-check-k1',[1,'check'])
            if rec['state']!='ok' or raw!=oracle:raise B.CandidateFailure('timed binary final-output check failed')
            rec,dynamic,_=box.call(['/usr/bin/readelf','-d','/in/program'],{'program':program},vd/'dynamic-dependencies',20)
            need(rec['state']=='ok','cannot inspect ELF dependencies')
            libs=re.findall(r'\(NEEDED\).*?\[([^\]]+)\]',dynamic.decode())
            need(set(libs)<= {'libc.so.6','libm.so.6'},'unexpected dynamic dependency '+repr(libs))
            old=v.get('historical_native_object_sha256')
            info.update({'ready':True,'object_path':str(obj),'object_sha256':sha(obj),
                         'binary_path':str(program),'binary_sha256':sha(program),'dynamic_needed':sorted(libs),
                         'historical_object_match':None if old is None else sha(obj)==old,
                         'historical_native_object_sha256':old,'rechecked_inputs':3})
        except B.CandidateFailure as exc:
            info['errors'].append(str(exc))
            if v['is_reference']: raise Blocked(g['id']+': reference build/recheck failed: '+str(exc)) from exc
        variants[v['label']]=info;jw(vd/'preparation.json',info)
    ready=[v for v in variants.values() if v['ready']]
    # Deduplicate only final, linked executable files under the same driver/libraries.
    classes={};aliases={}
    for v in ready:
        h=v['binary_sha256'];aliases[v['label']]=h
        if h not in classes:classes[h]={'program':v['binary_path'],'aliases':[]}
        classes[h]['aliases'].append(v['label'])
    result={'kernel':g['kernel'],'size':g['size'],'id':g['id'],'variants':variants,
            'classes':classes,'aliases':aliases,'official_oracle_sha256':shab(oracle),'timing_driver_sha256':sha(td),
            'linked_binary_deduplication':True,'old_labels_modified':False}
    jw(d/'prepared.json',result)
    return result

def choose_schedule(labels,seed):
    need(len(labels)>=2 and len(labels)==len(set(labels)),'labels invalid')
    base=sorted(labels);random.Random(seed).shuffle(base);n=len(base)
    out=[]
    for _ in range(math.ceil(4/n)):
        for order in (base,list(reversed(base))):
            for offset in range(n):out.append(order[offset:]+order[:offset])
    return out

def idseed(group_id,round_id=0):
    return int(hashlib.sha256((str(SEED)+'/'+group_id+'/'+str(round_id)).encode()).hexdigest()[:16],16)

def run_timed(box,program,stem,k):
    rec,raw=execute(box,Path(program),stem,[k])
    if rec['state']!='ok':raise B.CandidateFailure('timing execution '+rec['state'])
    try:return parse_time(raw,k)
    except Blocked as e: raise B.CandidateFailure(str(e)) from e

def calibrate(box,prepared,out):
    d=out/'calibration'/prepared['id'];d.mkdir(parents=True)
    ref=prepared['classes'][prepared['aliases']['reference_C']]['program'];k=1;records=[]
    while k<=MAX_K:
        times=[run_timed(box,ref,d/f'k{k}-rep{i}',k) for i in range(3)]
        records.append({'k':k,'ns':times})
        if statistics.median(times)>=TARGET_NS:break
        k*=2
    if k>MAX_K:
        info={'valid':False,'error':'reference calibration did not reach target','records':records}
        jw(d/'result.json',info);return info
    # Check final state of the same binary at the actual batch length, outside timing.
    failures={}
    for h,v in prepared['classes'].items():
        rec,raw=execute(box,Path(v['program']),d/(h[:20]+'-check'),[k,'check'])
        if rec['state']!='ok' or not raw or shab(raw)!=prepared['official_oracle_sha256']:
            failures[h]='batched_final_output_failed'
    refs={prepared['aliases']['reference_C'],prepared['aliases']['reference_IR']}
    need(not refs & set(failures),'reference batched final-output check failed: '+prepared['id'])
    info={'valid':True,'k':k,'records':records,'classes_excluded':failures,'time_target_ns':TARGET_NS,'used_reference_only':True}
    jw(d/'result.json',info);return info

def measure_round(box,prepared,calibration,out,round_id,prior_failures=None):
    d=out/'timings'/prepared['id']/f'round{round_id}';d.mkdir(parents=True)
    bad=dict(calibration['classes_excluded']);bad.update(prior_failures or {})
    refid=prepared['aliases']['reference_C']
    labels=[h for h in prepared['classes'] if h not in calibration['classes_excluded']]+['identity-control']
    order=choose_schedule(labels,idseed(prepared['id'],round_id));jw(d/'schedule.json',order)
    rows=[];k=calibration['k']
    for block,sequence in enumerate(order):
        row={'round':round_id,'block':block,'k':k,'sequence':sequence,'times_ns':{},'errors':{},'start_utc':now()}
        for position,label in enumerate(sequence):
            h=refid if label=='identity-control' else label
            if h in bad:row['errors'][label]=bad[h];continue
            stem=d/f'b{block:03d}-p{position:02d}'
            try:row['times_ns'][label]=run_timed(box,prepared['classes'][h]['program'],stem,k)
            except B.CandidateFailure as exc:
                row['errors'][label]=str(exc);bad[h]='previous_execution_failure_no_retry'
        row['finish_utc']=now();jw(d/f'block{block:03d}.json',row);rows.append(row)
    record={'round':round_id,'k':k,'rows':rows,'classes_failed':bad,'complete_block_target':len(order)}
    jw(d/'result.json',record);return record

def variability(xs):
    need(len(xs)>=4,'insufficient observations')
    q=statistics.quantiles(xs,n=4,method='inclusive');med=statistics.median(xs)
    return (q[2]-q[0])/positive(med)

def quality_for_pair(rounds,left,right,identity=False):
    warnings=[];meds=[];details=[]
    for r in rounds:
        values=[];ls=[];rs=[]
        for row in r['rows']:
            if left not in row['times_ns'] or right not in row['times_ns']:
                warnings.append('incomplete_block');continue
            l=positive(row['times_ns'][left]);rr=positive(row['times_ns'][right]);ls.append(l);rs.append(rr);values.append(l/rr)
        if len(values)!=r['complete_block_target'] or len(values)<4:
            details.append({'round':r['round'],'valid':False,'n':len(values)});continue
        m=statistics.median(values);meds.append(m)
        vars={'left':variability(ls),'right':variability(rs),'ratio':variability(values)}
        for key,v in vars.items():
            if v>0.10:warnings.append(f'r{r["round"]}_{key}_variable')
        if identity and abs(math.log(m))>math.log(1.02):warnings.append('identity_shift')
        details.append({'round':r['round'],'valid':True,'n':len(values),'median_ratio':m,'relative_iqr':vars})
    if len(meds)!=ROUNDS:warnings.append('missing_round')
    if len(meds)==ROUNDS and abs(math.log(meds[0]/meds[1]))>math.log(1.03):warnings.append('between_round_ratio_change')
    return {'valid':not warnings,'ratio':gmean(meds) if len(meds)==ROUNDS else None,
            'warnings':sorted(set(warnings)),'round_details':details,'equal_executable':left==right}

def summarize_group(prepared,cal,rounds):
    aliases=prepared['aliases'];ref=aliases['reference_C'];ir=aliases['reference_IR']
    control=quality_for_pair(rounds,ref,'identity-control',True)
    variants={}
    for label,v in prepared['variants'].items():
        item={'label':label,'form':v['form'],'is_reference':v['is_reference'],'measurement_valid':False,
              'source_sha256':v['source_sha256'],'status':'preparation_failed','errors':v['errors']}
        if v['ready']:
            h=v['binary_sha256'];item['binary_sha256']=h;item['object_sha256']=v['object_sha256']
            if h in cal['classes_excluded']:item['status']='batched_output_failed'
            else:
                qc=quality_for_pair(rounds,ref,h);qi=quality_for_pair(rounds,ir,h)
                item.update({'status':'measured','measurement_valid':control['valid'] and qc['valid'],
                  'against_original_c':qc,'against_unchanged_ir':qi,
                  'ir_path_valid':control['valid'] and qi['valid'],
                  'speedup_vs_original_c':qc['ratio'],'speedup_vs_unchanged_ir':qi['ratio'],
                  'same_binary_as_original_c':h==ref,'same_binary_as_original_ir':h==ir})
        variants[label]=item
    pairs=[]
    for form in ('C','IR'):
        for left,right in (('P0','P1'),('P0','P2'),('P1','P2')):
            l=next((k for k,v in prepared['variants'].items() if not v['is_reference'] and v['form']==form and k.split('__')[3]==left),None)
            r=next((k for k,v in prepared['variants'].items() if not v['is_reference'] and v['form']==form and k.split('__')[3]==right),None)
            if l in aliases and r in aliases:
                q=quality_for_pair(rounds,aliases[l],aliases[r]);q['valid']=q['valid'] and control['valid']
                pairs.append({'left_id':l,'right_id':r,'ratio_interpretation':'right speedup divided by left speedup = time(left)/time(right)',**q})
    return {'id':prepared['id'],'identity_control':control,'variants':variants,'paired_condition_comparisons':pairs,
            'baseline_path_effect':{**quality_for_pair(rounds,ref,ir),'identity_control_valid':control['valid']},'k':cal['k'],'rounds':ROUNDS,'binary_classes':len(prepared['classes'])}

def export_report(plan,out,groups):
    index={label:v for g in groups.values() for label,v in g.get('variants',{}).items() if not v['is_reference']}
    rows=[]
    for r in plan['requests']:
        v=index.get(r['id']);row={k:r[k] for k in ('id','condition','kernel','size','form')}
        row.update({'eligible_before_confirmation':r['eligible_under_recorded_checks'],
          'status':v['status'] if v else ('unmeasured' if r['eligible_under_recorded_checks'] else 'excluded_by_frozen_validation'),
          'measurement_valid':bool(v and v['measurement_valid']),
          'speedup_vs_original_c':v.get('speedup_vs_original_c') if v else None,
          'ir_incremental_valid':bool(v and v['form']=='IR' and v.get('ir_path_valid')),
          'speedup_vs_unchanged_ir':v.get('speedup_vs_unchanged_ir') if v and v['form']=='IR' else None,
          'same_binary_as_original_c':v.get('same_binary_as_original_c') if v else None,
          'same_binary_as_original_ir':v.get('same_binary_as_original_ir') if v else None})
        rows.append(row)
    put(out/'candidate-results.jsonl',''.join(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n' for x in rows))
    with (out/'candidate-results.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    stats={};lines=['=== 同時期・対応付き確認計測 ===','元の要求数=526。事前採用候補=351。旧採否は変更していません。']
    for condition in ('P0','P1','P2'):
        for form in ('ALL','C','IR'):
            rs=[r for r in rows if r['condition']==condition and (form=='ALL' or r['form']==form)]
            vs=[r['speedup_vs_original_c'] for r in rs if r['measurement_valid']]
            irs=[r['speedup_vs_unchanged_ir'] for r in rs if r['ir_incremental_valid']]
            key=condition+'/'+form
            stats[key]={'requests':len(rs),'eligible':sum(r['eligible_before_confirmation'] for r in rs),
                        'valid_measured':len(vs),'observed_speedup_gt_one':sum(x>1 for x in vs),
                        'conditional_geomean_vs_original_c':gmean(vs),
                        'ir_valid':len(irs),'conditional_geomean_vs_unchanged_ir':gmean(irs)}
            z=stats[key];lines.append(f'{key}: 分母={len(rs)} 計測品質合格={len(vs)} 観測倍率>1={z["observed_speedup_gt_one"]} 条件付き幾何平均={z["conditional_geomean_vs_original_c"]}')
    paired_rows=[]; paired_summary={}
    req_index={(r['condition'],r['kernel'],r['size'],r['form']):r for r in plan['requests']}
    perf_index={r['id']:r for r in rows}
    pair_index={(p['left_id'],p['right_id']):p for g in groups.values() for p in g.get('paired_condition_comparisons',[])}
    for left,right in (('P0','P1'),('P0','P2'),('P1','P2')):
        prefix=right+'_vs_'+left
        for key,lr in req_index.items():
            if key[0]!=left:continue
            rr=req_index.get((right,*key[1:]))
            if rr is None:continue
            a,b=perf_index[lr['id']],perf_index[rr['id']];q=pair_index.get((lr['id'],rr['id']))
            valid=bool(q and q['valid'] and a['measurement_valid'] and b['measurement_valid'])
            paired_rows.append({'comparison':prefix,'kernel':lr['kernel'],'size':lr['size'],'form':lr['form'],
               'left_id':lr['id'],'right_id':rr['id'],'left_eligible':lr['eligible_under_recorded_checks'],
               'right_eligible':rr['eligible_under_recorded_checks'],'paired_measurement_valid':valid,
               'right_over_left_speed_ratio':q['ratio'] if q else None,'same_linked_binary':q['equal_executable'] if q else None})
        for form in ('ALL','C','IR'):
            rs=[r for r in paired_rows if r['comparison']==prefix and (form=='ALL' or r['form']==form)]
            accepted=[r for r in rs if r['paired_measurement_valid']]
            paired_summary[prefix+'/'+form]={'paired_request_count':len(rs),'usable_pairs':len(accepted),
                'conditional_geomean_right_over_left':gmean([r['right_over_left_speed_ratio'] for r in accepted]),
                'same_binary_pairs':sum(r['same_linked_binary'] for r in accepted)}
            z=paired_summary[prefix+'/'+form]
            lines.append(f'{prefix}/{form}: 対応分母={len(rs)} 計測可能組={len(accepted)} 同一実行ファイル={z["same_binary_pairs"]} 速度比={z["conditional_geomean_right_over_left"]}')
    put(out/'paired-results.jsonl',''.join(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n' for x in paired_rows))
    if paired_rows:
        with (out/'paired-results.csv').open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(paired_rows[0]));w.writeheader();w.writerows(paired_rows)
    lines+=['同一実行ファイルは同一の測定系列を共有。要求数を独立反復数とは数えない。',
            '同一条件の2計測ラウンド。異なる日・独立起動・複数LLM試行の代わりではない。',
            '品質合格は統計的有意な高速化を意味しない。全入力での同値証明ではない。',
            'P0の生成方式とP1/P2の生成方式が違う交絡は、この確認計測では解消しない。']
    put(out/'report-ja.txt','\n'.join(lines)+'\n')
    total_valid=sum(r['measurement_valid'] for r in rows)
    return {'completion':'MATCHED_CONFIRMATION_COMPLETE','revision':REV,'phase':'complete','created_utc':now(),
            'requests_in_ledger':526,'candidates_eligible':351,'groups_completed':len(groups),
            'candidate_measurement_quality_passed':total_valid,'by_condition_form':stats,'paired_comparisons':paired_summary,
            'model_calls':0,'candidate_source_edits':0,'old_labels_modified':False,'formal_equivalence_proven':False,
            'interpretation':'Prospective confirmation of archived eligible sources; quality failures retained, no reruns selected by speed.'}

def main_run(pkg,out):
    pkg=Path(pkg).resolve();out=Path(out).resolve();plan=verify_package(pkg)
    need(not out.exists(),'output exists; refusing automatic rerun/overwrite')
    out.mkdir(parents=True)
    lock=open('/var/lock/cpucond-batch-codegen.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    jw(out/'frozen-protocol.json',load(pkg/'protocol.json'));jw(out/'frozen-plan.json',plan)
    box=None;start=time.monotonic()
    try:
        check_busy();host=host_record();jw(out/'host-before.json',host)
        box=B.Sandbox(out/'sandbox');box.preflight()
        util,clock=make_utility(box,host['clang'],plan,out)
        prepared={}
        for i,g in enumerate(plan['instances']):
            atomic(out/'progress.json',{'phase':'prepare_binaries','groups_completed':i,'groups_planned':90,'current':g['id'],'utc':now()})
            prepared[g['id']]=prepare_group(pkg,g,out,box,host['clang'],host['opt'],util,clock)
            print(f'準備 {i+1}/90 {g["id"]}: 候補={len(g["candidates"])} 実行ファイル種類={len(prepared[g["id"]]["classes"])}',flush=True)
        check_busy();need(host_record()==host,'host changed after compilation');print('全ビルド終了。推論なし・コンパイル並行なしで確認計測へ進みます。',flush=True)
        # Quiet interval after compilation, not a performance-selected retry.
        time.sleep(10)
        calibrations={};good=[]
        for i,g in enumerate(plan['instances']):
            k=g['id'];atomic(out/'progress.json',{'phase':'reference_calibration','groups_completed':i,'groups_planned':90,'current':k,'utc':now()})
            calibrations[k]=calibrate(box,prepared[k],out)
            if calibrations[k]['valid']:good.append(k)
            print('校正',k,'K=',calibrations[k].get('k'),'有効=',calibrations[k]['valid'],flush=True)
        measured={k:[] for k in good}
        for rnd in range(ROUNDS):
            check_busy();need(host_record()==host,'host changed before measurement round')
            order=list(good);random.Random(SEED+1000+rnd).shuffle(order);jw(out/f'group-order-round{rnd}.json',order)
            for i,k in enumerate(order):
                atomic(out/'progress.json',{'phase':'confirmation_measurement','round':rnd+1,'rounds':ROUNDS,'groups_completed':i,'groups_planned':len(order),'current':k,'utc':now()})
                previous=measured[k][-1]['classes_failed'] if measured[k] else {}
                measured[k].append(measure_round(box,prepared[k],calibrations[k],out,rnd,previous))
                print(f'計測 ラウンド{rnd+1}/2 {i+1}/{len(order)} {k}',flush=True)
        check_busy();after=host_record();jw(out/'host-after.json',after);need(host==after,'host changed during measurement')
        summaries={}
        for k in good:
            s=summarize_group(prepared[k],calibrations[k],measured[k]);summaries[k]=s;jw(out/'instance-results'/f'{k}.json',s)
        for k in prepared:
            if k not in good:
                s={'id':k,'variants':{},'measurement_status':'reference_calibration_failed','calibration':calibrations[k]};summaries[k]=s;jw(out/'instance-results'/f'{k}.json',s)
        result=export_report(plan,out,summaries);result['elapsed_seconds']=time.monotonic()-start
        result['calibration_failed_groups']=[k for k in prepared if k not in good]
        result['candidate_preparation_failed_ids']=[v['label'] for p in prepared.values() for v in p['variants'].values() if not v['is_reference'] and not v['ready']]
        result['total_linked_binary_classes']=sum(len(p['classes']) for p in prepared.values())
        result['requested_measurement_role_count']=351+2*90
        jw(out/'summary.json',result);atomic(out/'progress.json',result)
        print((out/'report-ja.txt').read_text(),flush=True);print(result['completion'],flush=True)
        B.seal(out)
        archive=out.parent/'confirmation-results.tgz'
        need(not archive.exists(),'archive exists')
        with tarfile.open(archive,'x:gz',compresslevel=1) as tf:tf.add(out,arcname='confirmation-results',recursive=True)
        put(archive.with_name(archive.name+'.sha256'),sha(archive)+'  '+archive.name+'\n')
        print('共有用:',archive,flush=True)
        return 0
    except Exception as exc:
        fail={'completion':'MATCHED_CONFIRMATION_BLOCKED','phase':'blocked','error':type(exc).__name__+': '+str(exc),'utc':now(),'model_calls':0,'old_labels_modified':False}
        jw(out/'failure.json',fail);atomic(out/'progress.json',fail)
        print(json.dumps(fail,ensure_ascii=False,indent=2),flush=True)
        return 1
    finally:
        if box:box.close()
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--check-package',action='store_true');ap.add_argument('--package',type=Path,default=Path(__file__).resolve().parent);ap.add_argument('--out',type=Path)
    a=ap.parse_args()
    if a.check_package:
        p=verify_package(a.package);print('CONFIRMATION_PACKAGE_VERIFIED: 526要求・351候補・90組の元C/IR');return 0
    need(a.run and a.out is not None,'use --run --out');return main_run(a.package,a.out)
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print('MATCHED_CONFIRMATION_BLOCKED:',type(e).__name__,str(e),file=sys.stderr);sys.exit(1)
