#!/usr/bin/env python3
"""Measure independent, reset-outside-timer kernel batches from a completed v1 run.

No new candidates, LLM/network requests, installations or repository changes.
Reuse unchanged v1 native kernel objects; link a new checked batch driver.
This changes the measurement workload: independent-state batch throughput is NOT
single-call latency. Do not combine these measurements with v1 timings.
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timezone

REVISION = 'polybench-independent-batch-v2'
SOURCE_REL = 'runs/goal0042-polybench-gated/20260910T135401.288727Z-b607e940'
BASE_SHA = '139f31a5d1c14d38ed6124ccad8e515e48d98a630740ee29e6a5aa62ef5177a1'
TASKS = ('gemm','atax','jacobi-2d','trisolv','nussinov','correlation')
CANDIDATES = ('reference','identity','hint_unroll_4','wrong_output_control')
MAX_BATCH = 4096
MEMORY_CAP = 128 * 1024 * 1024
TARGET_NS = 1_000_000
PAIRS_PER_SESSION = 10
SESSIONS = 2
THRESHOLDS = {'min_batch_duration_ns': 500_000, 'relative_iqr':0.10,
              'identity_log_effect': math.log(1.02), 'session_log_change':math.log(1.03)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fsha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def jwrite(path: Path, value) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def jread(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_base(path: Path):
    if not path.is_file() or fsha(path)!=BASE_SHA:
        raise RuntimeError('saved_v1_runner_hash_mismatch')
    spec=importlib.util.spec_from_file_location('_cpucond_saved_gated_v1',path)
    module=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:spec.loader.exec_module(module)
    finally:sys.dont_write_bytecode=old
    return module


# The original driver is used for declarations, guards, parsing and FP settings.
# The batch has separately allocated states. Input/expected values are shared,
# but each kernel call operates on its own full set of arrays.
BATCH_HELPERS = r'''
static int batch_number(const char*s){char*e=0;long v=strtol(s,&e,10);if(!*s||*e||v<1||v>4096)fail("bad_batch_count");return(int)v;}
static void batch_reset(Buffer*lanes,Buffer*template,int nb,int count){
 for(int z=0;z<count;z++)for(int k=0;k<nb;k++)memcpy(lanes[z*nb+k].data,template[k].initial,template[k].bytes);
}
static void batch_inspect(Buffer*lanes,int nb,int count){
 for(int z=0;z<count;z++)exact_check(lanes+z*nb,nb);
}
static uint64_t batch_call(Buffer*lanes,int nb,int count,int p,int q,int r,int t){
 __asm__ __volatile__("" ::: "memory");
 uint64_t a=ns();
 for(int z=0;z<count;z++){Buffer*b=lanes+z*nb; @CALL@}
 __asm__ __volatile__("" ::: "memory");
 uint64_t e=ns();
 if(e<=a)fail("nonpositive_batch_duration");return e-a;
}
'''
BATCH_BRANCH = r'''}else if(!strcmp(argv[6],"batch")){
  int count=batch_number(argv[8]);
  f=fopen(argv[7],"rb");if(!f)fail("expected_open_failed");
  for(int k=0;k<nb;k++)if(fread(b[k].expected,1,b[k].bytes,f)!=b[k].bytes)fail("short_expected");
  if(fgetc(f)!=EOF)fail("trailing_expected");fclose(f);
  size_t bytes=0;for(int k=0;k<nb;k++)bytes+=b[k].bytes;
  size_t working=(bytes+128*(size_t)nb)*(size_t)count;
  size_t allocation=working+bytes*3+128*(size_t)nb+sizeof(Buffer)*(size_t)count*(size_t)nb;
  if(allocation>134217728)fail("batch_memory_cap");
  Buffer*lanes=calloc((size_t)count*(size_t)nb,sizeof(Buffer));if(!lanes)fail("allocation_failed");
  for(int z=0;z<count;z++)for(int k=0;k<nb;k++){
   Buffer*x=lanes+z*nb+k;*x=b[k];
   x->allocation=malloc(x->bytes+128);if(!x->allocation)fail("allocation_failed");
   memset(x->allocation,0xA5,x->bytes+128);x->data=x->allocation+64;
  }
  /* Warm the SAME independent-state workload. No accumulation across calls. */
  for(int warm=0;warm<2;warm++){
   batch_reset(lanes,b,nb,count);(void)batch_call(lanes,nb,count,p,q,r,t);batch_inspect(lanes,nb,count);
  }
  batch_reset(lanes,b,nb,count);
  uint64_t duration=batch_call(lanes,nb,count,p,q,r,t);
  batch_inspect(lanes,nb,count);
  printf("CPUCOND_BATCH %d %llu %zu\n",count,(unsigned long long)duration,working);
  for(int z=0;z<count;z++)for(int k=0;k<nb;k++)free(lanes[z*nb+k].allocation);
  free(lanes);
 }else fail("invalid_mode");'''


def batch_driver(base, task: str) -> str:
    s=base.driver(task)
    old='if(argc!=8)fail("usage: program p q r t input.bin verify|time expected.bin");'
    new='if(argc!=9)fail("usage: program p q r t input.bin verify|batch expected.bin batch_count");'
    if s.count(old)!=1 or s.count('int main(int argc,char**argv){')!=1:
        raise RuntimeError('driver_structure_changed')
    s=s.replace(old,new)
    # Keep verify path; remove the old single-call time branch, not a fallback.
    start=s.index('}else if(!strcmp(argv[6],"time")){')
    end=s.index('}else fail("invalid_mode");',start)+len('}else fail("invalid_mode");')
    s=s[:start]+BATCH_BRANCH.replace('@CALL@',base.CALLS[task])+s[end:]
    s=s.replace('int main(int argc,char**argv){',BATCH_HELPERS.replace('@CALL@',base.CALLS[task])+'\nint main(int argc,char**argv){')
    if '@CALL@' in s or s.count('CPUCOND_KERNEL_NS'):
        raise RuntimeError('incomplete_batch_driver')
    return s


def parse_batch(raw: bytes, state: str, count: int) -> dict:
    if state!='ok':raise RuntimeError('batch_process_failed')
    m=re.fullmatch(rb'CPUCOND_BATCH ([0-9]+) ([0-9]+) ([0-9]+)\n',raw)
    if not m:raise RuntimeError('malformed_batch_output')
    k,ns,working=map(int,m.groups())
    if k!=count or not(1<=k<=MAX_BATCH) or ns<=0 or working<=0 or working>MEMORY_CAP:
        raise RuntimeError('invalid_batch_values')
    return {'batch_count':k,'batch_elapsed_ns':ns,'per_call_amortized_ns':ns/k,
            'working_state_allocation_bytes':working,'all_batch_outputs_checked':True}


def memory_cost(base, task: str, case: dict, count: int) -> int:
    ls=base.layout(task,case['p'],case['q'],case['r'])
    bytes_=sum(struct.calcsize('<'+typ)*n for _,typ,n,_ in ls)
    # C Buffer has 4 pointers + size_t + 2 ints on the required 64-bit host.
    return (bytes_+128*len(ls))*count+bytes_*3+128*len(ls)+48*count*len(ls)


def powers(base,task,case):
    result=[];n=1
    while n<=MAX_BATCH and memory_cost(base,task,case,n)<=MEMORY_CAP:
        result.append(n);n*=2
    if not result:raise RuntimeError('no_feasible_batch_size')
    return result


def schedule() -> list[dict]:
    rng=random.Random(104302)
    rows=[]
    for session in range(SESSIONS):
        # Exact order balance for each candidate in each independent session.
        orders={v:([0,1]*(PAIRS_PER_SESSION//2)) for v in ('identity','hint_unroll_4')}
        for v in orders:rng.shuffle(orders[v])
        for trial in range(PAIRS_PER_SESSION):
            vs=['identity','hint_unroll_4'];rng.shuffle(vs)
            for v in vs:
                order=['reference',v]
                if orders[v][trial]:order.reverse()
                rows.append({'session':session,'trial':trial,'candidate':v,'order':order})
    return rows


def quartile_iqr(values):
    q=statistics.quantiles(values,n=4,method='inclusive');return q[2]-q[0]


def summarize(rows: list[dict]) -> dict:
    if len(rows)<4:raise ValueError('insufficient_pairs')
    ratios=[r['speedup'] for r in rows]
    med=statistics.median(ratios)
    ref=[r['reference']['batch_elapsed_ns'] for r in rows]
    cand=[r['candidate_observation']['batch_elapsed_ns'] for r in rows]
    warnings=[]
    if min(ref+cand)<THRESHOLDS['min_batch_duration_ns']:warnings.append('short_batch_duration')
    if quartile_iqr(ratios)/med>THRESHOLDS['relative_iqr']:warnings.append('high_paired_ratio_variability')
    if quartile_iqr(ref)/statistics.median(ref)>THRESHOLDS['relative_iqr']:warnings.append('high_reference_variability')
    if quartile_iqr(cand)/statistics.median(cand)>THRESHOLDS['relative_iqr']:warnings.append('high_candidate_variability')
    if rows[0]['candidate']=='identity' and abs(math.log(med))>THRESHOLDS['identity_log_effect']:
        warnings.append('identity_control_shift')
    return {'pairs':len(rows),'median_paired_speedup':med,'paired_ratio_iqr':quartile_iqr(ratios),
            'reference_batch_median_ns':statistics.median(ref),'candidate_batch_median_ns':statistics.median(cand),
            'candidate_per_call_amortized_median_ns':statistics.median([r['candidate_observation']['per_call_amortized_ns'] for r in rows]),
            'quality_warnings':warnings,'statistical_significance_tested':False,
            'measurement_role':'independent_state_batch_throughput_not_single_call_latency'}


# Read exact function range from ELF64. No instruction/address normalization.
def elf_function(path: Path, wanted='cpucond_kernel') -> dict:
    b=path.read_bytes()
    if len(b)<64 or b[:6]!=b'\x7fELF\x02\x01':raise ValueError('requires_little_endian_ELF64')
    h=struct.unpack_from('<16sHHIQQQIHHHHHH',b,0)
    shoff,shentsize,shnum=h[6],h[11],h[12]
    if shentsize!=64 or not(0<shnum<65536) or shoff+64*shnum>len(b):raise ValueError('bad_section_table')
    sections=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+64*i) for i in range(shnum)]
    def span(offset,size):
        if offset<0 or size<0 or offset+size>len(b):raise ValueError('ELF_range_outside_file')
        return b[offset:offset+size]
    found=[]
    for sec in sections:
        if sec[1]!=2:continue # .symtab, not duplicate dynamic symbols
        if sec[9]!=24 or sec[5]%24 or sec[6]>=shnum:raise ValueError('bad_symbol_table')
        st=sections[sec[6]];names=span(st[4],st[5]);symbols=span(sec[4],sec[5])
        for i in range(0,len(symbols),24):
            name,info,other,index,value,size=struct.unpack_from('<IBBHQQ',symbols,i)
            if name>=len(names):raise ValueError('bad_symbol_name')
            end=names.find(b'\0',name)
            if end<0:raise ValueError('unterminated_symbol_name')
            if names[name:end].decode(errors='replace')!=wanted or info&15!=2:continue
            if index<=0 or index>=shnum or size<=0:raise ValueError('undefined_or_empty_function')
            part=sections[index];delta=value-part[3]
            if delta<0 or delta+size>part[5]:raise ValueError('function_outside_section')
            code=span(part[4]+delta,size)
            found.append({'symbol':wanted,'virtual_address':value,'size':size,'bytes_sha256':sha(code),
                          'bytes_hex':code.hex(),'scope':'raw_symbol_byte_range_only',
                          'semantic_equivalence_proven':False,'dependencies_resolved':False})
    if len(found)!=1:raise ValueError('function_not_uniquely_located')
    return found[0]


def loop_inventory(text: str) -> list[dict]:
    # Source navigation only: no dependency/safety/hotness inference.
    rows=[]
    for m in re.finditer(r'\bfor\s*\(',text):
        start=m.end()-1;depth=1;end=start+1
        while end<len(text) and depth:
            if text[end]=='(':depth+=1
            elif text[end]==')':depth-=1
            end+=1
        if depth:raise ValueError('unterminated_loop_header')
        rows.append({'loop_id':f'loop_{len(rows):02d}','line':text.count('\n',0,m.start())+1,
                     'header':text[m.start():end],'is_v1_hint_target':len(rows)==0,
                     'hotness':'not_measured','legal_transformations':'not_inferred'})
    return rows


def source_check(base, source: Path) -> dict:
    n=base.check_artifacts(source)
    s=jread(source/'summary.json')
    if s.get('completion')!='POLYBENCH_GATED_RUN_COMPLETE' or s.get('passed') is not True:
        raise RuntimeError('source_gate_run_incomplete')
    if set(x['task'] for x in s.get('tasks',[]))!=set(TASKS):raise RuntimeError('source_tasks_mismatch')
    for task in TASKS:
        gate=jread(source/task/'gate.json')
        if gate.get('negative_control_detected_in_every_case') is not True:raise RuntimeError('source_negative_control_failed')
        for v in ('reference','identity','hint_unroll_4'):
            if gate['candidate_admission'].get(v) is not True:raise RuntimeError('source_gate_denied')
        if gate['candidate_admission'].get('wrong_output_control') is not False:raise RuntimeError('negative_control_admitted')
    return {'source_run':str(source),'artifact_manifest_sha256':fsha(source/'artifacts.json'),
            'source_artifacts_checked':n,'source_summary_sha256':fsha(source/'summary.json')}


def link_drivers(base, source: Path, task: str, compiler: str, out: Path) -> dict:
    d=out/'build';d.mkdir()
    original_builds=jread(source/task/'builds.json')
    (d/'batch-driver.c').write_text(batch_driver(base,task))
    flags=original_builds['native/reference']['flags']
    if flags!=base.FP_FLAGS+base.PROFILES['native']:raise RuntimeError('native_build_flags_changed')
    if any(original_builds['native/'+v]['flags']!=flags for v in CANDIDATES):
        raise RuntimeError('candidate_native_flags_are_not_identical')
    base.ok_command([compiler,*flags,'-c',str(d/'batch-driver.c'),'-o',str(d/'batch-driver.o')],d/'driver-compile')
    builds={}
    for variant in CANDIDATES:
        dest=d/variant;dest.mkdir()
        src=source/task/'build/native'/variant
        # Reuse the previously validated kernel OBJECT unmodified.
        shutil.copyfile(src/'kernel.o',dest/'kernel.o');shutil.copyfile(src/'kernel.c',dest/'kernel.c')
        base.ok_command([compiler,*flags,str(dest/'kernel.o'),str(d/'batch-driver.o'),'-lm','-o',str(dest/'program')],dest/'link')
        if fsha(src/'kernel.o')!=fsha(dest/'kernel.o'):raise RuntimeError('kernel_object_changed')
        builds[variant]={'binary':str(dest/'program'),'binary_sha256':fsha(dest/'program'),
                        'object_sha256':fsha(dest/'kernel.o'),'reused_object_unchanged':True,
                        'source_sha256':fsha(dest/'kernel.c'),'flags':flags}
    jwrite(d/'builds.json',builds)
    analyses={}
    tool=shutil.which('llvm-objdump') or shutil.which('objdump')
    for v in ('reference','identity','hint_unroll_4'):
        dst=d/v
        for name in ('kernel.ll','kernel.s','kernel.opt.yaml'):
            old=source/task/'build/native'/v/name
            if old.is_file():shutil.copyfile(old,dst/name)
        if tool:
            base.command([tool,'-d','--disassemble-symbols=cpucond_kernel',str(dst/'program')] if 'llvm' in Path(tool).name else
                         [tool,'-d','--disassemble=cpucond_kernel',str(dst/'program')],dst/'disassembly')
        try:analyses[v]=elf_function(dst/'program')
        except ValueError as e:analyses[v]={'analysis_available':False,'reason':str(e)}
    comparisons={}
    for v in ('identity','hint_unroll_4'):
        a,b=analyses['reference'],analyses[v]
        comparisons[v]={'raw_function_range_equal':(a['bytes_sha256']==b['bytes_sha256']) if 'bytes_sha256' in a and 'bytes_sha256' in b else None,
            'reference_size':a.get('size'),'candidate_size':b.get('size'),
            'semantics_or_transformation_effect_not_proven':True}
    jwrite(out/'code-analysis.json',{'functions':analyses,'comparisons':comparisons})
    jwrite(out/'loop-inventory.json',loop_inventory((d/'reference/kernel.c').read_text()))
    return builds


def checked_call(base,build,case,inp,expected,mode,count,evidence,hashes):
    for p in (Path(build['binary']),inp,expected):
        expected_hash=build['binary_sha256'] if p==Path(build['binary']) else hashes[str(p)]
        if fsha(p)!=expected_hash:raise RuntimeError('changed_executable_or_test_data')
    return base.command([build['binary'],*[str(case[k]) for k in ('p','q','r','t')],str(inp),mode,str(expected),str(count)],evidence)


def process_task(base,source,task,compiler,out):
    d=out/task;d.mkdir()
    original=source/task
    builds=link_drivers(base,source,task,compiler,d)
    cs=jread(original/'cases.json')
    if cs!=base.cases(task):raise RuntimeError('v1_case_plan_changed')
    # Copy the exact old input bytes and reference outputs; no new initializers.
    inputs={};expected={};hashes={}
    for c in cs:
        cid=c['case_id'];di=d/'test-data'/cid;di.mkdir(parents=True)
        inp=di/'input.bin';exp=di/'expected.bin'
        shutil.copyfile(original/'inputs'/(cid+'.bin'),inp)
        shutil.copyfile(original/'validation/oracle_O0'/cid/'stdout.raw',exp)
        inputs[cid]=inp;expected[cid]=exp;hashes[str(inp)]=fsha(inp);hashes[str(exp)]=fsha(exp)
    jwrite(d/'cases.json',cs);jwrite(d/'test-data-sha256.json',hashes)
    rows={}
    for v in CANDIDATES:
        rs=[]
        for c in cs:
            cid=c['case_id'];ev=d/'validation'/v/cid
            rec=checked_call(base,builds[v],c,inputs[cid],expected[cid],'verify',1,ev,hashes)
            r=base.compare_result(task,c,inputs[cid].read_bytes(),expected[cid].read_bytes(),(ev/'stdout.raw').read_bytes(),rec['state'])
            r['case_id']=cid;rs.append(r);jwrite(ev/'result.json',r)
        rows[v]=rs
    negative=all(not r['passed'] and r.get('reason')=='value_mismatch' for r in rows['wrong_output_control'])
    passed=negative and all(all(r['passed'] for r in rows[v]) for v in ('reference','identity','hint_unroll_4'))
    gate={'passed':passed,'negative_control_rejected':negative,'rows':rows,'old_generic_and_sanitized_gate_reused':True,
          'new_driver_native_verification':True,'kernel_objects_unchanged':True,'formal_equivalence_proven':False}
    jwrite(d/'gate.json',gate);gate_hash=fsha(d/'gate.json')
    if not passed:raise RuntimeError('new_driver_gate_denied: '+task)
    print(task+': new-driver gate passed; unchanged kernel objects',flush=True)
    timings=[];calibrations=[];summaries=[]
    with base.affinity() as cpu:
        jwrite(d/'affinity.json',{'cpu':cpu,'scope':'runner and children; no exclusive CPU reservation'})
        for c in [x for x in cs if x['timing']]:
            cid=c['case_id'];cal=[];selected=None
            # Reference-only powers-of-two rule is fixed before seeing candidate times.
            for k in powers(base,task,c):
                values=[]
                for rep in range(3):
                    base.assert_inference_idle()
                    ev=d/'calibration'/cid/f'k{k}-r{rep}'
                    rec=checked_call(base,builds['reference'],c,inputs[cid],expected[cid],'batch',k,ev,hashes)
                    obs=parse_batch((ev/'stdout.raw').read_bytes(),rec['state'],k);values.append(obs)
                med=statistics.median(x['batch_elapsed_ns'] for x in values)
                cal.append({'count':k,'median_batch_ns':med,'observations':values})
                selected=k
                if med>=TARGET_NS:break
            calibration={'case_id':cid,'selected_batch_count':selected,'target_ns':TARGET_NS,
                         'target_reached':cal[-1]['median_batch_ns']>=TARGET_NS,'evidence':cal,
                         'policy':'reference_only_first_power_of_two_to_reach_target_with_memory_cap',
                         'not_candidate_search':True,'not_published_cross_CPU_workload_selection':True}
            jwrite(d/'calibration'/cid/'calibration.json',calibration);calibrations.append(calibration)
            plan=schedule();jwrite(d/'plans'/(cid+'.json'),{'schedule':plan,'batch_count':selected,'gate_sha256':gate_hash,
                'driver_and_dispatch_overhead_included':True,'memory_cost_upper_bound_bytes':memory_cost(base,task,c,selected),
                'calibration_not_used_for_speedup':True,'same_batch_for_all_candidates_and_sessions':True})
            print(f'{task}/{cid}: K={selected}, reference pilot={cal[-1]["median_batch_ns"]/1e6:.3f} ms; fixed before comparisons',flush=True)
            for pair_id,s in enumerate(plan):
                base.assert_inference_idle()
                if fsha(d/'gate.json')!=gate_hash:raise RuntimeError('gate_changed')
                vals={}
                for v in s['order']:
                    ev=d/'measurements'/cid/f'pair-{pair_id:03d}'/v
                    rec=checked_call(base,builds[v],c,inputs[cid],expected[cid],'batch',selected,ev,hashes)
                    vals[v]=parse_batch((ev/'stdout.raw').read_bytes(),rec['state'],selected)
                row={**s,'case_id':cid,'pair_id':pair_id,'batch_count':selected,'cpu':cpu,
                     'reference':vals['reference'],'candidate_observation':vals[s['candidate']],
                     'speedup':vals['reference']['batch_elapsed_ns']/vals[s['candidate']]['batch_elapsed_ns']}
                timings.append(row);jwrite(d/'measurements'/cid/f'pair-{pair_id:03d}'/'pair.json',row)
            for v in ('identity','hint_unroll_4'):
                by_session=[]
                for session in range(SESSIONS):
                    ss=summarize([r for r in timings if r['case_id']==cid and r['candidate']==v and r['session']==session])
                    ss.update(session=session,case_id=cid,candidate=v,batch_count=selected);by_session.append(ss)
                stability=abs(math.log(by_session[0]['median_paired_speedup']/by_session[1]['median_paired_speedup']))
                if stability>THRESHOLDS['session_log_change']:
                    for ss in by_session:ss['quality_warnings'].append('between_session_change')
                for ss in by_session:
                    if not calibration['target_reached']:ss['quality_warnings'].append('calibration_target_not_reached_at_cap')
                summaries.extend(by_session)
        # If an identity control drifts, do not bless the hint in that case/session.
        for x in summaries:
            if x['candidate']=='hint_unroll_4':
                ctrl=next(y for y in summaries if y['candidate']=='identity' and y['case_id']==x['case_id'] and y['session']==x['session'])
                if ctrl['quality_warnings']:x['quality_warnings'].append('identity_control_warning')
    jwrite(d/'timing.json',timings);jwrite(d/'timing-summary.json',summaries)
    short=sum(bool(x['quality_warnings']) for x in summaries)
    print(f'{task}: completed {len(timings)} pairs; {short}/{len(summaries)} summaries carry warnings',flush=True)
    return {'task':task,'passed':True,'validation_cases':len(cs),'negative_control_rejected':negative,
            'comparisons':jread(d/'code-analysis.json')['comparisons'],'calibration':[{k:v for k,v in x.items() if k!='evidence'} for x in calibrations],
            'timing':summaries,'timing_pairs':len(timings),'warnings_are_not_significance_tests':True,
            'comparison_timed_batches':2*len(timings),
            'calibration_timed_batches':sum(3*len(x['evidence']) for x in calibrations),
            'warmup_batches':2*(2*len(timings)+sum(3*len(x['evidence']) for x in calibrations)),
            'comparison_kernel_calls_including_warmups':sum(6*x['batch_count'] for x in timings),
            'calibration_kernel_calls_including_warmups':sum(9*y['count'] for x in calibrations for y in x['evidence'])}


def host_observation(base,out):
    d={'uname':platform.uname()._asdict(),'available_cpus':sorted(os.sched_getaffinity(0)),
       'CPU_topology_is_OS_observation_not_independently_confirmed_physical_spec':True}
    try:
        first=Path('/proc/cpuinfo').read_text().split('\n\n')[0]
        fields=dict(x.split(':',1) for x in first.splitlines() if ':' in x)
        d['cpu_model']=next((v.strip() for k,v in fields.items() if k.strip()=='model name'),None)
    except OSError:d['cpu_model']=None
    d['caches']=[]
    cpu=min(os.sched_getaffinity(0))
    for p in sorted(Path(f'/sys/devices/system/cpu/cpu{cpu}/cache').glob('index*')):
        x={'source':str(p)}
        for n in ('level','type','size','coherency_line_size','shared_cpu_list','ways_of_associativity'):
            try:x[n]=(p/n).read_text().strip()
            except OSError:x[n]=None
        d['caches'].append(x)
    jwrite(out/'host-observation.json',d)
    return d


def report_text(s):
    lines=['# PolyBench independent-state batch timing',s['completion'],'',
      '旧runは不変。候補の計算本体・native kernel.oは再利用。新しいドライバと計測条件は別run。',
      '独立入力状態のバッチ throughput。旧runの単発latencyとは比較・結合しない。',
      '初期化・検査は時間外。計測範囲にディスパッチループとカーネル呼出しを含む。空測定の差引きなし。',
      'Kはreferenceだけで較正し、候補・セッション間で固定。将来のCPU間主評価には共通K/shapeを別途固定する。',
      '新ドライバで全14条件を検証し、各バッチの全出力を比較。全入力同値性の証明ではない。',
      '2セッションを別集計。10ペア/候補/サイズ/セッション。品質警告なしも有意差の証明ではない。',
      '', '| Task | Case | K | Candidate | Session | Speedup | Candidate batch ms | Warnings |',
      '|---|---|---:|---|---:|---:|---:|---|']
    for t in s['tasks']:
        if not t['passed']:lines+=['BLOCKED '+t['task']+': '+t.get('error','unknown')];continue
        for x in t['timing']:
            lines.append(f'| {t["task"]} | {x["case_id"]} | {x["batch_count"]} | {x["candidate"]} | {x["session"]} | {x["median_paired_speedup"]:.5f} | {x["candidate_batch_median_ns"]/1e6:.3f} | {", ".join(x["quality_warnings"])} |')
    lines+=['','## Executed function raw-byte comparison','関数範囲だけの一致/相違。定数・外部呼出しの同値性や展開効果は証明しない。']
    for t in s['tasks']:
        if t['passed']:lines.append(t['task']+': '+json.dumps(t['comparisons'],ensure_ascii=False))
    lines+=['','## Summary',json.dumps(s,ensure_ascii=False,indent=2)]
    return '\n'.join(lines)+'\n'


def execute(args):
    repo=args.repo.resolve();source=(args.source_run or repo/SOURCE_REL).resolve()
    if not (repo/'src/cpucond').is_dir():raise RuntimeError('wrong_repository')
    if platform.machine() not in ('x86_64','amd64') or struct.calcsize('P')!=8:raise RuntimeError('requires_x86_64_linux')
    base=load_base(source/'runner.py');receipt=source_check(base,source)
    before=base.tracked(repo);head=base.git(repo,'rev-parse','HEAD').strip()
    old_manifest=fsha(source/'artifacts.json')
    prov=jread(source/'provenance.json');compiler=prov['compiler']
    if not Path(compiler).is_file() or fsha(Path(compiler))!=prov['compiler_sha256']:raise RuntimeError('compiler_changed_since_source_run')
    base.assert_inference_idle()
    rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    out=repo/'runs/goal0043-measurement'/rid;out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(Path(__file__),out/'runner.py');shutil.copyfile(source/'runner.py',out/'dependency-v1.py')
    jwrite(out/'source-receipt.json',receipt)
    jwrite(out/'plan.json',{'revision':REVISION,'tasks':TASKS,'candidates':CANDIDATES,'target_batch_ns':TARGET_NS,
       'min_accepted_descriptive_batch_ns':THRESHOLDS['min_batch_duration_ns'],'memory_cap_bytes':MEMORY_CAP,
       'max_batch_count':MAX_BATCH,'sessions':SESSIONS,'pairs_per_session':PAIRS_PER_SESSION,
       'thresholds':THRESHOLDS,'workload':'independent_state_batch_throughput',
       'not_single_invocation_latency':True,'no_semantic_relaxation':True,'no_candidate_search':True,
       'counterbalancing':'randomized candidate order, exactly balanced reference/candidate order in each session',
       'existing_cpucond_CLI_unchanged':True,'LLM_evaluation':False,'formal_equivalence_proven':False})
    host=host_observation(base,out)
    jwrite(out/'provenance.json',{'git_head':head,'tracked_source_sha256':before,'compiler':compiler,
        'compiler_sha256':fsha(Path(compiler)),'runner_sha256':fsha(out/'runner.py'),'dependency_sha256':BASE_SHA,
        'compiler_version':subprocess.check_output([compiler,'--version'],timeout=30).decode(errors='replace')})
    print('Run:',out,flush=True);tasks=[]
    for task in TASKS:
        try:tasks.append(process_task(base,source,task,compiler,out))
        except Exception as e:
            tasks.append({'task':task,'passed':False,'error':type(e).__name__+': '+str(e)});print(task+': BLOCKED: '+str(e),flush=True)
    same=before==base.tracked(repo) and head==base.git(repo,'rev-parse','HEAD').strip()
    old_same=old_manifest==fsha(source/'artifacts.json')
    base.check_artifacts(source) # all prior files, including inputs/results remain exact
    passed=same and old_same and all(t['passed'] for t in tasks)
    s={'completion':'MEASUREMENT_RUN_COMPLETE' if passed else 'MEASUREMENT_RUN_BLOCKED','passed':passed,
       'run_directory':str(out),'tasks_completed':sum(t['passed'] for t in tasks),'tasks_planned':len(TASKS),
       'source_run_unchanged':old_same,'repository_tracked_sources_unchanged':same,
       'new_model_requests':0,'network_requests':0,'new_candidate_transformations':0,
       'equivalence_proven':False,'publishable_benchmark':False,'CPU_information_effect_evaluated':False,
       'measurement_protocol':'independent_state_batch_throughput_not_old_single_call_latency',
       'environment_role':'development_measurement_protocol','tasks':tasks}
    jwrite(out/'summary.json',s);text=report_text(s);(out/'report.md').write_text(text,encoding='utf-8')
    jwrite(out/'artifacts.json',base.snapshot(out));count=base.check_artifacts(out)
    dest=Path('/mnt/c/Users/m.hirotaka/Downloads')
    if not dest.is_dir():dest=Path.home()/'cpucond-recovery';dest.mkdir(parents=True,exist_ok=True)
    share=dest/f'cpucond-measurement-{rid}.txt'
    with share.open('x',encoding='utf-8') as f:f.write(text)
    print('Artifacts checked:',count);print(s['completion']);print(json.dumps({k:v for k,v in s.items() if k!='tasks'},ensure_ascii=False,indent=2));print('Shareable report:',share)
    return 0 if passed else 1


class Tests(unittest.TestCase):
    def test_sha(self):self.assertEqual(sha(b'a'),hashlib.sha256(b'a').hexdigest())
    def test_parse(self):self.assertEqual(parse_batch(b'CPUCOND_BATCH 4 1000 1200\n','ok',4)['per_call_amortized_ns'],250)
    def test_count_mismatch(self):
        with self.assertRaises(RuntimeError):parse_batch(b'CPUCOND_BATCH 4 1000 1200\n','ok',8)
    def test_empty(self):
        with self.assertRaises(RuntimeError):parse_batch(b'','ok',1)
    def test_trailing(self):
        with self.assertRaises(RuntimeError):parse_batch(b'CPUCOND_BATCH 4 1000 1200\nx','ok',4)
    def test_failed(self):
        with self.assertRaises(RuntimeError):parse_batch(b'CPUCOND_BATCH 4 1000 1200\n','timeout',4)
    def test_zero(self):
        with self.assertRaises(RuntimeError):parse_batch(b'CPUCOND_BATCH 4 0 1200\n','ok',4)
    def test_mem(self):
        with self.assertRaises(RuntimeError):parse_batch(b'CPUCOND_BATCH 4 1000 999999999\n','ok',4)
    def test_schedule_determinism(self):self.assertEqual(schedule(),schedule())
    def test_schedule_balance(self):
        rs=schedule()
        for s in range(SESSIONS):
            for v in ('identity','hint_unroll_4'):
                x=[r for r in rs if r['session']==s and r['candidate']==v]
                self.assertEqual(len(x),10);self.assertEqual(sum(y['order'][0]=='reference' for y in x),5)
    def test_no_negative_in_schedule(self):self.assertNotIn('wrong_output_control',json.dumps(schedule()))
    def test_loops(self):
        x=loop_inventory('void f(){for(int i=0;i<(n+1);i++)for(int j=0;j<n;j++)a[j]=i;}')
        self.assertEqual(len(x),2);self.assertTrue(x[0]['is_v1_hint_target']);self.assertFalse(x[1]['is_v1_hint_target'])
    def test_bad_loop(self):
        with self.assertRaises(ValueError):loop_inventory('for(')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as p:
            x=Path(p)/'j';jwrite(x,{})
            with self.assertRaises(FileExistsError):jwrite(x,{})
    def test_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as p:
            with self.assertRaises(ValueError):jwrite(Path(p)/'j',{'x':math.nan})
    def test_bad_elf(self):
        with tempfile.TemporaryDirectory() as p:
            f=Path(p)/'x';f.write_bytes(b'not ELF')
            with self.assertRaises(ValueError):elf_function(f)
    def sample_rows(self,ratio=1.0,batch=2000000):
        return [{'candidate':'identity','speedup':ratio,'reference':{'batch_elapsed_ns':int(batch*ratio)},
                 'candidate_observation':{'batch_elapsed_ns':batch,'per_call_amortized_ns':batch/4}} for _ in range(10)]
    def test_stable_identity(self):self.assertEqual(summarize(self.sample_rows())['quality_warnings'],[])
    def test_identity_shift(self):self.assertIn('identity_control_shift',summarize(self.sample_rows(1.1))['quality_warnings'])
    def test_short_warning(self):self.assertIn('short_batch_duration',summarize(self.sample_rows(batch=1000))['quality_warnings'])
    def test_no_significance_claim(self):self.assertFalse(summarize(self.sample_rows())['statistical_significance_tested'])
    def test_insufficient(self):
        with self.assertRaises(ValueError):summarize([])
    def test_declared_calibration_target(self):self.assertEqual(TARGET_NS,1000000)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--source-run',type=Path)
    p.add_argument('--self-test',action='store_true');args=p.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():return 1
    if args.self_test:return 0
    os.umask(0o077)
    try:
        lock=Path(tempfile.gettempdir())/f'cpucond-execution-{os.getuid()}.lock'
        with lock.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return execute(args)
    except Exception as e:
        print('MEASUREMENT_RUN_BLOCKED:',type(e).__name__+': '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
