#!/usr/bin/env python3
from __future__ import annotations

import argparse, contextlib, fcntl, hashlib, importlib.util, json, math, os
from pathlib import Path
import random, re, shutil, statistics, struct, subprocess, sys, tempfile, time, unittest, uuid
from datetime import datetime, timezone

PROTOCOL_ID='cpu-conditioned-final-v1.2'
SIZES=('MINI_DATASET','SMALL_DATASET','MEDIUM_DATASET')
SIZE_LABEL={'MINI_DATASET':'MINI','SMALL_DATASET':'SMALL','MEDIUM_DATASET':'MEDIUM'}
COMMON=['-std=gnu11','-fno-fast-math','-ffp-contract=off','-fno-lto']
PROFILES={
 'oracle_O0':['-O0'],
 'generic_O3':['-O3'],
 'native_O3':['-O3','-march=native'],
 'sanitized':['-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer'],
}
INITIAL_TARGET_NS=5_000_000
ESCALATED_TARGET_NS=20_000_000
MAX_K=16384
SESSIONS=2
PAIRS_PER_SESSION=8
REL_IQR=0.10
IDENTITY_LOG_EFFECT=math.log(1.02)
SESSION_LOG_CHANGE=math.log(1.03)
VERIFY_TIMEOUT=60
BATCH_TIMEOUT=60
BASE_SEED=51054
DRY_IDS=('identity','loop_00_unroll_count_2','loop_00_interleave_count_2','loop_00_vectorize_width_2')


def sha_bytes(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def sha_file(p:Path)->str:
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def jread(p:Path):return json.loads(p.read_text(encoding='utf-8'))
def jwrite(p:Path,x):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex[:8])
 with t.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 t.replace(p)

def git(repo:Path,*args:str)->str:
 p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=30)
 if p.returncode:raise RuntimeError('git_failed:'+p.stderr.decode(errors='replace')[:1000])
 return p.stdout.decode('utf-8','strict')
def tracked(repo:Path):return {n:sha_file(repo/n) for n in git(repo,'ls-files','-z').split('\0') if n}

def load_smoke(repo:Path):
 p=repo/'tools/research_protocols/goal0054_identity_liveout_smoke.py'
 spec=importlib.util.spec_from_file_location('_smoke',p); m=importlib.util.module_from_spec(spec)
 old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
 try:spec.loader.exec_module(m)
 finally:sys.dont_write_bytecode=old
 return m

def loops(smoke,fn:str):return [m.start() for m in re.finditer(r'\bfor\s*\(',smoke.mask_noncode(fn))]
def parse_candidate(cid:str):
 if cid=='identity':return None
 m=re.fullmatch(r'loop_([0-9]{2})_(unroll_count|interleave_count|vectorize_width)_([0-9]+)',cid)
 if not m:raise ValueError('bad_candidate_id:'+cid)
 i,h,v=int(m[1]),m[2],int(m[3]); allowed={'unroll_count':{2,4,8,16},'interleave_count':{2,4,8},'vectorize_width':{2,4,8}}
 if v not in allowed[h]:raise ValueError('candidate_outside_frozen_space')
 return i,h,v

def insert_hint(smoke,s:str,kernel:str,cid:str,expected:int)->str:
 x=parse_candidate(cid)
 if x is None:return s
 i,h,v=x; a,b=smoke.function_span(s,kernel,'void'); fn=s[a:b]; ps=loops(smoke,fn)
 if len(ps)!=expected:raise RuntimeError(f'loop_count_changed:{len(ps)}:{expected}')
 if i>=len(ps):raise RuntimeError('loop_index_oob')
 at=a+ps[i]; return s[:at]+f'#pragma clang loop {h}({v})\n'+s[at:]

def call_expr(smoke,main:str,token:str)->str:
 masked=smoke.mask_noncode(main); ms=list(re.finditer(r'\b'+re.escape(token)+r'\b',masked))
 if len(ms)!=1:raise RuntimeError(f'{token}:occurrences:{len(ms)}')
 o=masked.find('(',ms[0].end()); c=smoke.matching(masked,o,'(',')'); return main[ms[0].start():c+1]+';'
def statement_bounds(smoke,main:str,token:str):
 masked=smoke.mask_noncode(main); ms=list(re.finditer(r'\b'+re.escape(token)+r'\b',masked))
 if len(ms)!=1:raise RuntimeError(f'{token}:occurrences:{len(ms)}')
 pos=ms[0].start(); start=max(masked.rfind(';',0,pos),masked.rfind('{',0,pos))+1; end=masked.find(';',pos)
 if end<0:raise RuntimeError(token+':no_semicolon')
 return start,end+1

TIMER_HELPER = """
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint64_t cpucond_clock_ns(void) {
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC_RAW, &ts) != 0) {
    perror("clock_gettime");
    exit(92);
  }
  return (uint64_t)ts.tv_sec * 1000000000ULL
       + (uint64_t)ts.tv_nsec;
}
"""

def replace_main(smoke,s:str,kernel:str)->str:
 a,b=smoke.function_span(s,'main','int'); main=s[a:b]
 init=call_expr(smoke,main,'init_array'); kern=call_expr(smoke,main,kernel); pr=call_expr(smoke,main,'print_array')
 start,_=statement_bounds(smoke,main,'init_array'); _,end=statement_bounds(smoke,main,'print_array')
 block=f'''\n  if(argc!=3){{fputs("usage: program verify|batch K\\n",stderr);return 64;}}\n  char*cpucond_end=NULL; long cpucond_k_long=strtol(argv[2],&cpucond_end,10);\n  if(!cpucond_end||*cpucond_end||cpucond_k_long<1||cpucond_k_long>{MAX_K}){{fputs("invalid K\\n",stderr);return 65;}}\n  int cpucond_k=(int)cpucond_k_long;\n  if(!strcmp(argv[1],"verify")){{\n    {init}\n    {kern}\n    {pr}\n    if(fflush(stdout)!=0)return 66;\n  }}else if(!strcmp(argv[1],"batch")){{\n    {init}\n    __asm__ __volatile__("" ::: "memory"); {kern} __asm__ __volatile__("" ::: "memory");\n    uint64_t cpucond_total=0;\n    for(int cpucond_rep=0;cpucond_rep<cpucond_k;++cpucond_rep){{\n      {init}\n      __asm__ __volatile__("" ::: "memory");\n      uint64_t cpucond_a=cpucond_clock_ns();\n      {kern}\n      __asm__ __volatile__("" ::: "memory");\n      uint64_t cpucond_b=cpucond_clock_ns();\n      if(cpucond_b<=cpucond_a)return 67; cpucond_total+=cpucond_b-cpucond_a;\n    }}\n    printf("CPUCOND_BATCH %d %llu\\n",cpucond_k,(unsigned long long)cpucond_total);\n  }}else{{fputs("invalid mode\\n",stderr);return 68;}}\n'''
 return TIMER_HELPER+'\n'+s[:a]+main[:start]+block+main[end:]+s[b:]

def transform(smoke,original:str,kernel:str,cid:str,expected:int):
 s=insert_hint(smoke,original,kernel,cid,expected); s=smoke.add_noinline(s,kernel); s,n=smoke.raw_instrument_print_array(s); s=replace_main(smoke,s,kernel)
 return s,{'candidate_id':cid,'raw_emission_sites':n,'source_sha256':sha_bytes(s.encode())}

# ELF64 raw symbol-byte extractor.
def elf_function(path:Path,wanted:str):
 b=path.read_bytes()
 if len(b)<64 or b[:6]!=b'\x7fELF\x02\x01':raise ValueError('not_ELF64_LE')
 h=struct.unpack_from('<16sHHIQQQIHHHHHH',b,0); shoff,ents,num=h[6],h[11],h[12]
 if ents!=64 or not(0<num<65536) or shoff+ents*num>len(b):raise ValueError('bad_sections')
 secs=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+ents*i) for i in range(num)]
 def span(o,n):
  if o<0 or n<0 or o+n>len(b):raise ValueError('bad_range')
  return b[o:o+n]
 found=[]
 for sec in secs:
  if sec[1]!=2:continue
  if sec[9]!=24 or sec[5]%24 or sec[6]>=num:raise ValueError('bad_symtab')
  st=secs[sec[6]]; names=span(st[4],st[5]); syms=span(sec[4],sec[5])
  for o in range(0,len(syms),24):
   name,info,other,index,value,size=struct.unpack_from('<IBBHQQ',syms,o)
   if name>=len(names):raise ValueError('bad_name')
   e=names.find(b'\0',name)
   if e<0:raise ValueError('bad_name_end')
   if names[name:e].decode(errors='replace')!=wanted or (info&15)!=2:continue
   if index<=0 or index>=num or size<=0:raise ValueError('bad_function_symbol')
   p=secs[index]; d=value-p[3]
   if d<0 or d+size>p[5]:raise ValueError('function_outside_section')
   code=span(p[4]+d,size); found.append({'size':size,'bytes_sha256':sha_bytes(code)})
 if len(found)!=1:raise ValueError(f'function_not_unique:{len(found)}')
 return found[0]

def run_command(argv,out:Path,timeout=120,extra=None):
 out.mkdir(parents=True,exist_ok=False); env=dict(os.environ,LC_ALL='C'); env.update(extra or {}); start=time.monotonic_ns()
 try:
  p=subprocess.run(argv,capture_output=True,timeout=timeout,env=env); state='ok' if p.returncode==0 else 'process_failed'; rc=p.returncode; so,se=p.stdout,p.stderr
 except subprocess.TimeoutExpired as e:state='timeout';rc=None;so,se=e.stdout or b'',e.stderr or b''
 except OSError as e:state='launch_failed';rc=None;so,se=b'',str(e).encode()
 (out/'stdout.raw').write_bytes(so);(out/'stderr.raw').write_bytes(se); rec={'argv':argv,'state':state,'returncode':rc,'elapsed_ns':time.monotonic_ns()-start,'stdout_sha256':sha_bytes(so),'stderr_sha256':sha_bytes(se)};jwrite(out/'command.json',rec);return rec

def checked(argv,out,timeout=120,extra=None):
 r=run_command(argv,out,timeout,extra)
 if r['state']!='ok':raise RuntimeError('command_'+r['state']+':'+(out/'stderr.raw').read_text(errors='replace')[:1500])
 return r

def cflags(profile):return [*COMMON,*PROFILES[profile]]

def compile_utilities(clang,pb,root):
 ans={}
 for p in PROFILES:
  d=root/p;d.mkdir(parents=True,exist_ok=True);obj=d/'polybench.o';checked([clang,*cflags(p),'-c',str(pb/'utilities/polybench.c'),'-o',str(obj)],d/'compile');ans[p]=obj
 return ans

def compile_candidate(clang,pb,source_dir,text,size,profile,util,out):
 out.mkdir(parents=True,exist_ok=True);src=out/'candidate.c';obj=out/'candidate.o';binary=out/'program';src.write_text(text,encoding='utf-8'); defs=[f'-D{size}','-DPOLYBENCH_USE_C99_PROTO','-DPOLYBENCH_DUMP_ARRAYS'];inc=['-I',str(pb/'utilities'),'-I',str(source_dir)]
 checked([clang,*cflags(profile),*defs,*inc,'-c',str(src),'-o',str(obj)],out/'compile');checked([clang,*cflags(profile),str(obj),str(util),'-lm','-o',str(binary)],out/'link')
 return {'profile':profile,'binary':str(binary),'binary_sha256':sha_file(binary),'object_sha256':sha_file(obj),'source_sha256':sha_file(src)}

def verify(build,evidence):
 b=Path(build['binary']);
 if sha_file(b)!=build['binary_sha256']:raise RuntimeError('binary_changed')
 r=run_command([str(b),'verify','1'],evidence,VERIFY_TIMEOUT,{'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'});return r,(evidence/'stdout.raw').read_bytes()
def judge(exp,obs,state):return {'passed':state=='ok' and obs==exp,'state':state,'expected_sha256':sha_bytes(exp),'observed_sha256':sha_bytes(obs),'expected_bytes':len(exp),'observed_bytes':len(obs)}

def parse_batch(raw,state,k):
 if state!='ok':raise RuntimeError('batch_'+state)
 m=re.fullmatch(rb'CPUCOND_BATCH ([0-9]+) ([0-9]+)\n',raw)
 if not m:raise RuntimeError('malformed_batch')
 kk,total=map(int,m.groups())
 if kk!=k or total<=0:raise RuntimeError('bad_batch_values')
 return {'batch_count':kk,'batch_elapsed_ns':total,'per_call_ns':total/kk}
def run_batch(build,k,out):
 b=Path(build['binary'])
 if sha_file(b)!=build['binary_sha256']:raise RuntimeError('binary_changed')
 r=run_command([str(b),'batch',str(k)],out,BATCH_TIMEOUT);return parse_batch((out/'stdout.raw').read_bytes(),r['state'],k)

def calibrate(ref,target,out):
 ev=[];k=1
 while k<=MAX_K:
  obs=[run_batch(ref,k,out/f'k{k}-r{i}') for i in range(3)]; med=statistics.median(x['batch_elapsed_ns'] for x in obs);ev.append({'k':k,'median_batch_ns':med,'observations':obs})
  if med>=target:
   ans={'target_ns':target,'selected_k':k,'target_reached':True,'evidence':ev};jwrite(out/'calibration.json',ans);return ans
  k*=2
 raise RuntimeError('calibration_target_not_reached')

def balanced(seed):
 bits=[0,1]*4;random.Random(seed).shuffle(bits);return [(['candidate','reference'] if b else ['reference','candidate']) for b in bits]
def med_iqr(xs):
 med=statistics.median(xs);q=statistics.quantiles(xs,n=4,method='inclusive');return med,q[2]-q[0]
def summarize(rows,identity):
 ratios=[x['speedup'] for x in rows];refs=[x['reference_ns'] for x in rows];cands=[x['candidate_ns'] for x in rows];rm,ri=med_iqr(ratios);am,ai=med_iqr(refs);bm,bi=med_iqr(cands);w=[]
 if ri/rm>REL_IQR:w.append('high_paired_ratio_variability')
 if ai/am>REL_IQR:w.append('high_reference_variability')
 if bi/bm>REL_IQR:w.append('high_candidate_variability')
 if identity and abs(math.log(rm))>IDENTITY_LOG_EFFECT:w.append('identity_control_shift')
 return {'pairs':len(rows),'median_paired_speedup':rm,'paired_speedup_iqr':ri,'reference_batch_median_ns':am,'candidate_batch_median_ns':bm,'quality_warnings':w,'measurement_valid':True}
def seed_for(k,s,c,session):return int(hashlib.sha256(f'{BASE_SEED}|{k}|{s}|{c}|{session}'.encode()).hexdigest()[:8],16)

def measure_one(ref,cand,cid,k,kernel,size,out):
 allr=[];sums=[]
 for session in range(SESSIONS):
  rs=[]
  for trial,order in enumerate(balanced(seed_for(kernel,size,cid,session))):
   vals={};actual=[]
   try:
    for token in order:
     label,build=('reference',ref) if token=='reference' else (cid,cand);actual.append(label);vals[label]=run_batch(build,k,out/f's{session}-p{trial:02d}'/label)
   except Exception as e:return allr+[{'candidate_id':cid,'session':session,'trial':trial,'measurement_valid':False,'error':type(e).__name__+':'+str(e)}],[{'candidate_id':cid,'session':session,'measurement_valid':False,'quality_warnings':['candidate_measurement_invalid']}]
   rn=vals['reference']['batch_elapsed_ns'];cn=vals[cid]['batch_elapsed_ns'];row={'candidate_id':cid,'session':session,'trial':trial,'order':actual,'batch_count':k,'reference_ns':rn,'candidate_ns':cn,'speedup':rn/cn,'measurement_valid':True};rs.append(row);allr.append(row)
  sm=summarize(rs,cid=='identity');sm.update({'candidate_id':cid,'session':session,'batch_count':k});sums.append(sm)
 if len(sums)==2 and all(x['measurement_valid'] for x in sums):
  if abs(math.log(sums[0]['median_paired_speedup']/sums[1]['median_paired_speedup']))>SESSION_LOG_CHANGE:
   for x in sums:x['quality_warnings'].append('between_session_change')
 return allr,sums

def measure_at_target(ref,natives,reps,kernel,size,target,out):
 out.mkdir(parents=True,exist_ok=True);cal=calibrate(ref,target,out/'calibration');k=cal['selected_k'];tim={};sums={};r,s=measure_one(ref,ref,'identity',k,kernel,size,out/'identity');tim['identity']=r;sums['identity']=s
 for cid in reps:r,s=measure_one(ref,natives[cid],cid,k,kernel,size,out/cid);tim[cid]=r;sums[cid]=s
 jwrite(out/'timing.json',tim);jwrite(out/'timing-summary.json',sums);return {'calibration':cal,'timing':tim,'summaries':sums}

def load_inputs(repo):
 pp=repo/'configs/final-experiment-v1.2.json';mp=repo/'configs/final-candidate-manifest-v1.json';p=jread(pp);m=jread(mp)
 if p.get('protocol_id')!=PROTOCOL_ID or p['dataset']['performance_sizes']!=['MINI','SMALL','MEDIUM'] or p['dataset']['main_instance_count']!=90 or p['dataset']['main_candidate_instance_count']!=4740:raise RuntimeError('protocol_scope_mismatch')
 if m['kernel_count']!=30 or m['total_candidates_across_30_kernels']!=1580:raise RuntimeError('manifest_scope_mismatch')
 intake=repo/'runs/goal0041-dataset-intake/20260910T132522.441454Z-69857bdb';return p,m,jread(intake/'polybench-catalog.json'),intake/'upstream/polybench-c-4.2.1-beta',pp,mp

def candidate_ids(e):
 ids=['identity']
 for loop in e['loops']:ids += [x['candidate_id'] for x in loop['candidates']]
 if len(ids)!=e['candidate_count_including_identity'] or len(set(ids))!=len(ids):raise RuntimeError('candidate_manifest_bad')
 return ids
@contextlib.contextmanager
def affinity(cpu):
 old=os.sched_getaffinity(0);chosen=min(old) if cpu is None else cpu
 if chosen not in old:raise RuntimeError('cpu_unavailable')
 os.sched_setaffinity(0,{chosen})
 try:yield chosen
 finally:os.sched_setaffinity(0,old)
def read_or_none(p):
 try:return Path(p).read_text().strip()
 except OSError:return None
def host_obs():
 model=None
 try:
  for line in Path('/proc/cpuinfo').read_text().split('\n\n')[0].splitlines():
   if ':' in line and line.split(':',1)[0].strip()=='model name':model=line.split(':',1)[1].strip();break
 except OSError:pass
 return {'cpu_model':model,'available_cpus':sorted(os.sched_getaffinity(0)),'no_turbo':read_or_none('/sys/devices/system/cpu/intel_pstate/no_turbo'),'smt_control':read_or_none('/sys/devices/system/cpu/smt/control'),'smt_active':read_or_none('/sys/devices/system/cpu/smt/active'),'cpu0_governor':read_or_none('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')}

def gate_instance(smoke,clang,pb,cat,entry,size,ids,utils,out):
 kid=entry['kernel_id'];kernel='kernel_'+kid.replace('-','_');sp=pb/cat['source']
 if sha_file(sp)!=cat['source_sha256']:raise RuntimeError('source_hash_changed')
 original=sp.read_text(encoding='utf-8');rs,meta=transform(smoke,original,kernel,'identity',entry['syntactic_loop_count']);rb=compile_candidate(clang,pb,sp.parent,rs,size,'oracle_O0',utils['oracle_O0'],out/'oracle-O0');rr,oracle=verify(rb,out/'oracle-verify')
 if rr['state']!='ok' or not oracle:raise RuntimeError('oracle_failed')
 bad=bytearray(oracle);bad[len(bad)//2]^=1
 if judge(oracle,bytes(bad),'ok')['passed']:raise RuntimeError('negative_control_accepted')
 (out/'oracle.raw').write_bytes(oracle);jwrite(out/'oracle.json',{'oracle_sha256':sha_bytes(oracle),'oracle_bytes':len(oracle),'negative_control_rejected':True,'reference_transform':meta})
 rows=[];natives={};infos={}
 for idx,cid in enumerate(ids,1):
  cd=out/'candidates'/cid;cd.mkdir(parents=True,exist_ok=True)
  try:
   src,tm=transform(smoke,original,kernel,cid,entry['syntactic_loop_count']);(cd/'transformed.c').write_text(src,encoding='utf-8');prs={};admit=True;native=None
   for profile in ('generic_O3','native_O3','sanitized'):
    b=compile_candidate(clang,pb,sp.parent,src,size,profile,utils[profile],cd/'build'/profile);rec,raw=verify(b,cd/'verify'/profile);j=judge(oracle,raw,rec['state']);prs[profile]={**j,'binary_sha256':b['binary_sha256'],'object_sha256':b['object_sha256']};admit &= j['passed'];
    if j['passed'] and (cd/'verify'/profile/'stdout.raw').exists():(cd/'verify'/profile/'stdout.raw').unlink()
    elif not j['passed']:(cd/'verify'/profile/'mismatch.raw').write_bytes(raw)
    if profile=='native_O3':native=b
   row={'candidate_id':cid,'admitted':bool(admit),'transform':tm,'profiles':prs}
   if admit:
    info=elf_function(Path(native['binary']),kernel);row['function']={'size':info['size'],'bytes_sha256':info['bytes_sha256']};natives[cid]=native;infos[cid]=info
   rows.append(row);print(f'  gate {kid}/{SIZE_LABEL[size]} {idx}/{len(ids)} {cid}: '+('PASS' if admit else 'REJECT'),flush=True)
  except Exception as e:rows.append({'candidate_id':cid,'admitted':False,'error':type(e).__name__+':'+str(e)});print(f'  gate {kid}/{SIZE_LABEL[size]} {idx}/{len(ids)} {cid}: BLOCKED {e}',flush=True)
 jwrite(out/'gate.json',{'oracle_sha256':sha_bytes(oracle),'oracle_bytes':len(oracle),'candidate_rows':rows,'formal_equivalence_proven':False})
 if 'identity' not in natives:raise RuntimeError('identity_not_admitted')
 groups={}
 for cid,inf in infos.items():groups.setdefault(inf['bytes_sha256'],[]).append(cid)
 ih=infos['identity']['bytes_sha256'];alias={};grows=[];reps=[]
 for h,members in sorted(groups.items()):
  members=sorted(members);same=h==ih;rep='identity' if same else members[0];reps += [] if same else [rep]
  for cid in members:alias[cid]=rep
  grows.append({'function_bytes_sha256':h,'candidate_ids':members,'representative':rep,'same_as_identity':same})
 jwrite(out/'machine-code-groups.json',grows);jwrite(out/'alias-map.json',alias)
 return {'rows':rows,'groups':grows,'alias':alias,'reps':reps},natives

def run_instance(smoke,clang,pb,cat,entry,size,ids,utils,out):
 gate,native=gate_instance(smoke,clang,pb,cat,entry,size,ids,utils,out);ref=native['identity']
 # Identity first at 5 ms. Escalate before measuring candidates if dirty.
 cal=calibrate(ref,INITIAL_TARGET_NS,out/'identity-initial-calibration');k=cal['selected_k'];ir,isum=measure_one(ref,ref,'identity',k,entry['kernel_id'],size,out/'identity-initial')
 dirty=any((not x.get('measurement_valid',False)) or x.get('quality_warnings') for x in isum);target=INITIAL_TARGET_NS;identity_rows=ir;identity_sum=isum
 if dirty:
  cal=calibrate(ref,ESCALATED_TARGET_NS,out/'identity-escalated-calibration');k=cal['selected_k'];identity_rows,identity_sum=measure_one(ref,ref,'identity',k,entry['kernel_id'],size,out/'identity-escalated');target=ESCALATED_TARGET_NS
 instance_valid=all(x.get('measurement_valid',False) and not x.get('quality_warnings') for x in identity_sum)
 timing={'identity':identity_rows};sums={'identity':identity_sum};invalid=[]
 if instance_valid:
  for cid in gate['reps']:
   r,s=measure_one(ref,native[cid],cid,k,entry['kernel_id'],size,out/'measurement'/cid);timing[cid]=r;sums[cid]=s
   if any((not x.get('measurement_valid',False)) or x.get('quality_warnings') for x in s):invalid.append(cid)
 jwrite(out/'final-timing.json',timing);jwrite(out/'final-timing-summary.json',sums)
 summary={'kernel_id':entry['kernel_id'],'size':size,'size_label':SIZE_LABEL[size],'candidate_ids_requested':len(ids),'candidates_admitted':sum(bool(x.get('admitted')) for x in gate['rows']),'unique_machine_code_groups':len(gate['groups']),'nonidentity_representatives_measured':len(gate['reps']) if instance_valid else 0,'aliases_to_identity':sum(v=='identity' for v in gate['alias'].values()),'initial_identity_triggered_escalation':dirty,'escalated':dirty,'instance_valid':instance_valid,'final_target_ns':target,'final_k':k,'candidate_representatives_invalid_no_rerun':invalid,'identity_summaries':identity_sum,'formal_equivalence_proven':False};jwrite(out/'instance-summary.json',summary);return summary

def preserve_incomplete(inst):
 if inst.exists() and not (inst/'instance-summary.json').is_file():inst.rename(inst.with_name(inst.name+'.incomplete-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]))

def execute(repo,cpu,dry,resume):
 smoke=load_smoke(repo);protocol,manifest,catalog,pb,pp,mp=load_inputs(repo);clang=shutil.which('clang')
 if not clang:raise RuntimeError('clang_missing')
 cats={x['id']:x for x in catalog};entries={x['kernel_id']:x for x in manifest['kernels']};role='dry-run' if dry else 'final';kernels=[dry] if dry else [x['kernel_id'] for x in manifest['kernels']]
 if dry and dry not in entries:raise RuntimeError('unknown_dry_kernel')
 head=git(repo,'rev-parse','HEAD').strip();before=tracked(repo)
 if resume:
  out=resume.resolve();prov=jread(out/'provenance.json')
  for k,v in {'role':role,'git_head':head,'protocol_sha256':sha_file(pp),'manifest_sha256':sha_file(mp)}.items():
   if prov.get(k)!=v:raise RuntimeError('resume_mismatch:'+k)
 else:
  rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8];out=repo/'runs'/('goal0054-dry-run' if dry else 'goal0054-final-atlas')/rid;out.mkdir(parents=True);jwrite(out/'provenance.json',{'role':role,'git_head':head,'protocol_sha256':sha_file(pp),'manifest_sha256':sha_file(mp),'host':host_obs(),'llm_requests':0,'network_requests':0})
 utilroot=out/'utility';utils={p:utilroot/p/'polybench.o' for p in PROFILES} if all((utilroot/p/'polybench.o').is_file() for p in PROFILES) else compile_utilities(clang,pb,utilroot);completed=[]
 with affinity(cpu) as chosen:
  if not (out/'affinity.json').exists():jwrite(out/'affinity.json',{'applied_cpu':chosen})
  for kid in kernels:
   entry=entries[kid];ids=candidate_ids(entry);ids=list(DRY_IDS) if dry else ids
   if dry:
    miss=[x for x in ids if x not in candidate_ids(entry)]
    if miss:raise RuntimeError('dry_ids_missing:'+str(miss))
   for size in SIZES:
    inst=out/kid/size
    if (inst/'instance-summary.json').is_file():completed.append(jread(inst/'instance-summary.json'));print(f'SKIP {kid}/{SIZE_LABEL[size]}',flush=True);continue
    preserve_incomplete(inst);inst.mkdir(parents=True);print(f'=== {role.upper()} {kid}/{SIZE_LABEL[size]} candidates={len(ids)} ===',flush=True);s=run_instance(smoke,clang,pb,cats[kid],entry,size,ids,utils,inst);completed.append(s);print(f"DONE {kid}/{SIZE_LABEL[size]} valid={s['instance_valid']} admitted={s['candidates_admitted']}/{len(ids)} groups={s['unique_machine_code_groups']} escalated={s['escalated']}",flush=True);jwrite(out/'progress.json',{'instances_completed':len(completed),'last_kernel':kid,'last_size':size,'updated_utc':datetime.now(timezone.utc).isoformat()})
 if tracked(repo)!=before or git(repo,'rev-parse','HEAD').strip()!=head:raise RuntimeError('tracked_repo_changed')
 expected=len(kernels)*3;done=len(completed)==expected;summary={'completion':'FINAL_ATLAS_DRY_RUN_COMPLETE' if dry and done else 'FINAL_PHYSICAL_ATLAS_COMPLETE' if done else 'FINAL_ATLAS_INCOMPLETE','role':role,'passed':done,'instances_completed':len(completed),'instances_expected':expected,'instances_valid':sum(bool(x.get('instance_valid')) for x in completed),'instances_escalated':sum(bool(x.get('escalated')) for x in completed),'formal_equivalence_proven':False,'llm_requests':0,'network_requests':0,'run_directory':str(out)};jwrite(out/'summary.json',summary);print(summary['completion']);print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if done else 1

class Tests(unittest.TestCase):
 def test_parse(self):self.assertEqual(parse_candidate('loop_03_unroll_count_16'),(3,'unroll_count',16));self.assertIsNone(parse_candidate('identity'))
 def test_balance(self):x=balanced(1);self.assertEqual(len(x),8);self.assertEqual(sum(y[0]=='reference' for y in x),4)
 def test_negative(self):self.assertFalse(judge(b'a',b'b','ok')['passed'])
 def test_identity_quality(self):
  rows=[{'speedup':1.0,'reference_ns':6_000_000,'candidate_ns':6_000_000} for _ in range(8)];self.assertEqual(summarize(rows,True)['quality_warnings'],[])

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--cpu',type=int);p.add_argument('--self-test',action='store_true');p.add_argument('--dry-run');p.add_argument('--resume',type=Path);a=p.parse_args();r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 if not r.wasSuccessful():return 1
 if a.self_test:return 0
 if a.resume and a.dry_run:p.error('--resume is final-run only')
 repo=a.repo.resolve();os.umask(0o077);lock=Path(tempfile.gettempdir())/f'cpucond-final-atlas-{os.getuid()}.lock'
 try:
  with lock.open('a+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);return execute(repo,a.cpu,a.dry_run,a.resume)
 except Exception as e:print('FINAL_ATLAS_BLOCKED:',type(e).__name__+':'+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
