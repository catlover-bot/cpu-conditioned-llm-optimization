#!/usr/bin/env python3
"""Verify all saved IR with LLVM 18; replay 14 discordant official tests.
No model calls, no speed measurements, no changes to old labels or sources.
The fixed v1.1 validator is reused only for sandboxing/builds, not as an IR verifier.
"""
from __future__ import annotations
import argparse, collections, contextlib, fcntl, hashlib, importlib.util, json
import os, re, shutil, subprocess, sys, time, uuid
from pathlib import Path, PurePosixPath

REV = 'ir-structure-and-official-regression-v1'
VALIDATOR_SHA = '81dae012bfba1c7ebe2db583f3813dd96a828acdf540c701c733d1c4aeaf3f53'
CROSSWALK_SHA = 'b410b60d0546ec450bff92fb8286e794f1c50e5b86751ef87881a331959d4c42'
ROOTS = {'P0': Path('/srv/research/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent'),
         'P1': Path('/srv/research/cpucond-p012-zen2-v1/P1'), 'P2': Path('/srv/research/cpucond-p012-zen2-v1/P2')}
GENERIC = ['--target=x86_64-unknown-linux-gnu', '-march=x86-64', '-mtune=generic']
PROFILES = [('generic', ['-O3', *GENERIC], False),
            ('native', ['-O3', '--target=x86_64-unknown-linux-gnu', '-march=native'], False),
            ('sanitized', ['-O1', *GENERIC, '-fsanitize=address,undefined', '-fno-sanitize-recover=all'], True)]

class Blocked(RuntimeError): pass

def require(x, msg):
    if not x: raise Blocked(msg)

def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def pairs_unique(items):
    d={}
    for k,v in items:
        require(k not in d, 'duplicate JSON key: '+k); d[k]=v
    return d

def parse_json(text):
    return json.loads(text, object_pairs_hook=pairs_unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(Blocked('nonfinite JSON')))

def load(p): return parse_json(Path(p).read_text(encoding='utf-8'))

def write(p,x):
    p=Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    t=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex)
    t.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n'); t.replace(p)

def regular(root, rel):
    root=Path(root).resolve(); q=PurePosixPath(str(rel))
    require(not q.is_absolute() and q.parts and '..' not in q.parts, 'unsafe relative path')
    p=root
    for part in q.parts:
        p=p/part; require(not p.is_symlink(),'symlink: '+str(p))
    require(p.is_file() and p.resolve().is_relative_to(root),'missing input: '+str(p))
    return p

def manifest(root):
    root=Path(root); out={}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        h,sep,n=line.partition('  '); n=n.removeprefix('./')
        require(sep and re.fullmatch('[0-9a-f]{64}',h) and n not in out,'invalid manifest')
        out[n]=h
    return out

def verify_manifest(root):
    ms=manifest(root)
    for n,h in ms.items(): require(digest(regular(root,n))==h,'hash mismatch: '+n)
    return ms

def trusted_validator(records):
    p=regular(records,'validator-v1.1.py'); require(digest(p)==VALIDATOR_SHA,'validator changed')
    spec=importlib.util.spec_from_file_location('_fixed_revalidation_81',p)
    m=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode; sys.dont_write_bytecode=True
    try: spec.loader.exec_module(m)
    finally: sys.dont_write_bytecode=old
    return m

def inventory(records):
    p=regular(records,'candidate-crosswalk.jsonl');require(digest(p)==CROSSWALK_SHA,'crosswalk changed')
    rows=[parse_json(s) for s in p.read_text().splitlines()]
    require(len(rows)==526 and len({r['id'] for r in rows})==526,'requirement count')
    require(sum(r['old_generation_status']=='saved' for r in rows)==525,'saved count')
    for r in rows:
        require(re.fullmatch('[A-Za-z0-9_-]+',r['id']) and r['form'] in ('C','IR') and r['condition'] in ROOTS,'bad row')
    return rows

def source(records,row,original=False,form=None):
    form=form or row['form']; ext='c' if form=='C' else 'll'
    if original: rel=f"records/results/extracted/originals/{row['kernel']}/{row['size']}/kernel.{ext}"
    else: rel=f"records/results/extracted/candidates/{row['condition']}/{row['id']}/candidate.{ext}"
    p=regular(records,rel)
    if not original: require(digest(p)==row['source_sha256'],'candidate changed')
    return p

def find_opt():
    p=shutil.which('opt-18');require(p,'opt-18 not found; install llvm-18, do not skip verification')
    v=subprocess.check_output([p,'--version'],text=True,timeout=10)
    require(re.search(r'LLVM version 18\.1\.',v),'LLVM 18.1.x required: '+v)
    return str(Path(p).resolve()),v

def verify_ir(box,opt,path,stem):
    rec,raw,_=box.call([opt,'-passes=verify','-disable-output','/in/module.ll'],{'module.ll':path},stem,60)
    error=Path(stem).with_suffix('.stderr').read_text(errors='replace')
    if rec['state']=='timeout': raise Blocked('IR verifier timeout, not a candidate verdict')
    if rec['returncode'] is not None and rec['returncode']<0:
        known_abort = rec['returncode']==-6 and ('Broken module found' in error or 'input module is broken' in error)
        if not known_abort: raise Blocked('IR verifier crashed without a recognized module-rejection diagnostic')
    return {'passed':rec['state']=='ok','state':rec['state'],'returncode':rec['returncode'],
            'source_sha256':digest(path),'stderr_excerpt':error[:16000]}

def build(box,v,clang,src,stem,flags,form='C',proto=None):
    rec,obj=v.compile_obj(box,clang,src,stem,flags,form,proto)
    return rec,obj

def link_run(box,v,clang,objs,stem,san=False):
    rec,exe=v.link_prog(box,clang,objs,Path(str(stem)+'-link'),san)
    if rec['state']!='ok' or not exe:return {'passed':False,'state':'link_failed'},b''
    return v.run_prog(box,exe,Path(str(stem)+'-run'),180)

def official_inputs(row,records,out):
    # These original files must still exist on the user's server. Copy verified
    # bytes to the new run; no modification of the original experiment folder.
    pkg=ROOTS[row['condition']]/'work'; ms=manifest(pkg)
    result={}
    for name,rel in [('driver',f"inputs/{row['kernel']}/{row['size']}/driver.c"),
                     ('original',f"inputs/{row['kernel']}/{row['size']}/kernel.c"),
                     ('utility','utilities/polybench.c'),('header','utilities/polybench.h')]:
        require(rel in ms,'official input absent from manifest: '+rel)
        p=regular(pkg,rel);require(digest(p)==ms[rel],'official input changed: '+rel)
        q=out/(name+('.h' if name=='header' else '.c'));q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());result[name]=q
    require(digest(result['original'])==digest(source(records,row,True,'C')),'official reference mismatch')
    return result

def replay_official(row,records,out,box,v,clang):
    d=out/'official'/row['id'];d.mkdir(parents=True)
    src=source(records,row); inp=official_inputs(row,records,d/'inputs')
    fn,params=v.parse_kernel(inp['original'].read_text(),row['kernel'])
    proto=d/'prototype.h';v.prototype_file(proto,fn,params)
    v.policy(src.read_text(),row['form'],fn)
    rec,raw,_=box.call([clang,'-std=gnu11','-E','-P','-I/in','/in/polybench.c'],
        {'polybench.c':inp['utility'],'polybench.h':inp['header']},d/'utility-preprocess',60)
    require(rec['state']=='ok','official utility preprocessing failed')
    uc=d/'utility-preprocessed.c';uc.write_bytes(raw)
    rec,uo=build(box,v,clang,uc,d/'utility-compile',['-O0',*GENERIC]);require(rec['state']=='ok' and uo,'utility compile failed')
    rec,ref=build(box,v,clang,inp['original'],d/'reference-o0',['-O0',*GENERIC]);require(rec['state']=='ok' and ref,'oracle compile failed')
    rec,drv=build(box,v,clang,inp['driver'],d/'driver-o0',['-O0',*GENERIC]);require(rec['state']=='ok' and drv,'driver compile failed')
    rr,oracle=link_run(box,v,clang,[drv,ref,uo],d/'oracle');require(rr['state']=='ok' and oracle,'oracle execution failed')
    # Require the same-host reference to reproduce the frozen official oracle.
    frozen=ROOTS[row['condition']]/'results/baselines'/(row['kernel']+'__'+row['size'])/'O0/verify.stdout'
    require(frozen.is_file() and not frozen.is_symlink(),'missing old oracle')
    require(frozen.read_bytes()==oracle,'new official oracle differs; do not relabel candidate')
    profiles={}
    for label,flags,san in PROFILES:
        bflags=flags
        rec,base=build(box,v,clang,inp['original'],d/(label+'-base'),bflags,'C',proto)
        require(rec['state']=='ok' and base,'baseline compilation failed: '+label)
        ds=['-O0',*GENERIC]+(['-fsanitize=address,undefined','-fno-sanitize-recover=all'] if san else [])
        rec,ho=build(box,v,clang,inp['driver'],d/(label+'-driver'),ds);require(rec['state']=='ok' and ho,'driver compile failed')
        br,braw=link_run(box,v,clang,[ho,base,uo],d/(label+'-baseline'),san)
        require(br['state']=='ok' and braw==oracle,'official baseline differs: '+label)
        rec,co=build(box,v,clang,src,d/(label+'-candidate'),flags,row['form'],proto if row['form']=='C' else None)
        if rec['state']!='ok' or not co:profiles[label]={'passed':False,'state':'compile_failed'};continue
        rr,craw=link_run(box,v,clang,[ho,co,uo],d/(label+'-candidate'),san)
        profiles[label]={'passed':rr['state']=='ok' and craw==oracle,'state':rr['state'],
             'stdout_sha256':hashlib.sha256(craw).hexdigest(),'oracle_sha256':hashlib.sha256(oracle).hexdigest(),
             'candidate_bytes':len(craw),'oracle_bytes':len(oracle)}
    return {'id':row['id'],'source_sha256':digest(src),'profiles':profiles,
            'official_recheck_passed':all(x['passed'] for x in profiles.values()),
            'not_a_new_performance_measurement':True}

def require_idle():
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==os.getpid():continue
        try:args=(p/'cmdline').read_bytes().split(b'\0');exe=Path(os.fsdecode(args[0])).name
        except (OSError,IndexError):continue
        if exe in ('ollama','llama-server','ollama_llama_server') and any(a in (b'serve',b'runner',b'--model') for a in args[1:]):
            raise Blocked('inference still active; will not stop it')


def run(a):
    require(os.geteuid()==0,'server mode requires root only for bwrap launcher')
    require(os.uname().nodename=='cpucond-zen2-01','wrong host')
    records=Path(a.records).resolve();out=Path(a.out).resolve();require(not out.exists(),'output exists; do not overwrite')
    require_idle();opt,ov=find_opt();v=trusted_validator(records);clang,cv=v.clang18()
    require(24 in os.sched_getaffinity(0),'cpu24 not available')
    out.mkdir(parents=True)
    status={'revision':REV,'phase':'integrity','completion':'RUNNING','model_calls':0,'performance_measurements':0,
            'old_labels_modified':False,'llvm_opt_version':ov,'clang_version':cv,'records':str(records)}
    def progress(): status['updated_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());write(out/'progress.json',status)
    try:
        progress();verify_manifest(records);rows=inventory(records)
        box=v.Sandbox(out/'sandbox',24,1);v.sandbox_preflight(box,clang,out/'preflight')
        # A deliberately ill-formed module must be rejected by this exact opt.
        bad=out/'preflight/invalid-dominance.ll';bad.write_text('define i32 @probe(i1 %c) {\nentry:\n br i1 %c, label %a, label %b\na:\n %x=add i32 1, 2\n br label %b\nb:\n ret i32 %x\n}\n')
        b=verify_ir(box,opt,bad,out/'preflight/negative-ir')
        require(not b['passed'] and 'dominate' in b['stderr_excerpt'],'IR negative control failed')
        originals=sorted((records/'records/results/extracted/originals').glob('*/*/kernel.ll'));require(len(originals)==90,'original IR count')
        for i,p in enumerate(originals,1):
            q=verify_ir(box,opt,p,out/'ir-originals'/p.parent.parent.name/p.parent.name/'verify');require(q['passed'],'original IR failed verifier: '+str(p))
        print('ORIGINAL_IR_VERIFIED 90/90',flush=True)
        irs={};status['phase']='verify_saved_ir'
        for row in rows:
            if row['form']!='IR' or row['old_generation_status']!='saved':continue
            q=verify_ir(box,opt,source(records,row),out/'ir-candidates'/row['id']/'verify');q['id']=row['id'];q['previous_dynamic_passed']=row['new_passed'];irs[row['id']]=q
            write(out/'ir-candidates'/row['id']/'result.json',q)
            status['ir_completed']=len(irs);progress()
        require(len(irs)==263,'candidate IR count')
        write(out/'ir-verification.json',list(irs.values()))
        print('SAVED_IR_VERIFIED',len(irs),'accepted',sum(x['passed'] for x in irs.values()),flush=True)
        discord=[r for r in rows if r['transition']=='old_not_pass__new_pass'];require(len(discord)==14,'discordant count')
        status['phase']='official_input_recheck';outcomes=[]
        for row in discord:
            if row['form']=='IR' and not irs[row['id']]['passed']:
                q={'id':row['id'],'state':'rejected_before_execution','reason':'IR verifier rejected','official_recheck_passed':False}
            else:q=replay_official(row,records,out,box,v,clang)
            outcomes.append(q);write(out/'official'/row['id']/'result.json',q)
            print(row['id'],'official_recheck=',q['official_recheck_passed'],flush=True)
            status['official_rechecks_completed']=len(outcomes);progress()
        write(out/'official-rechecks.json',outcomes)
        status.update({'phase':'complete','completion':'IR_AND_OFFICIAL_RECHECK_COMPLETE',
           'original_ir_verified':90,'candidate_ir_checked':263,'candidate_ir_well_formed':sum(x['passed'] for x in irs.values()),
           'previous_dynamic_pass_but_ir_rejected':[r['id'] for r in rows if r['new_passed'] and r['id'] in irs and not irs[r['id']]['passed']],
           'discordant_candidates':14,'discordant_official_recheck_passed':sum(x['official_recheck_passed'] for x in outcomes),
           'source_code_edits':0,'ir_verification_is_not_semantic_equivalence':True})
        write(out/'summary.json',status);progress()
        print(json.dumps(status,ensure_ascii=False,indent=2),flush=True)
        print('IR_AND_OFFICIAL_RECHECK_COMPLETE',flush=True)
    except Exception as e:
        status.update({'phase':'blocked','completion':'IR_AND_OFFICIAL_RECHECK_BLOCKED','error':type(e).__name__+': '+str(e)})
        write(out/'failure.json',status);progress();raise


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--records',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    # This lock applies to this new check only. Existing jobs are never killed.
    fd=os.open('/run/lock/cpucond-0081.lock',os.O_CREAT|os.O_RDWR,0o600)
    try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);run(a)
    finally:os.close(fd)
if __name__=='__main__':main()
