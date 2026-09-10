#!/usr/bin/env python3
"""Offline, full-state PolyBench development gate and paired kernel timing.

Consumes the completed dataset-intake run. Does not edit repository sources,
old runs, or upstream files; no network, LLM requests, installations, or Git writes.
This is a separate runner. The older cpucond CLI is NOT modified/integrated.

Default: self-tests, lock, input verification, six real kernel adapters, full-state
bit comparisons, negative controls, then gated native paired timings.
--verify-only omits timing. --check RUN validates saved artifact hashes.
--self-test does not consume a repository or run a benchmark.
"""
from __future__ import annotations
import argparse
import contextlib
import csv
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
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

REVISION = 'polybench-gated-run-v1'
INTAKE_REL = 'runs/goal0041-dataset-intake/20260910T132522.441454Z-69857bdb'
TASKS = ('gemm', 'atax', 'jacobi-2d', 'trisolv', 'nussinov', 'correlation')
CANDIDATES = ('reference', 'identity', 'hint_unroll_4', 'wrong_output_control')
FP_FLAGS = ['-std=c11', '-fno-fast-math', '-ffp-contract=off', '-fno-lto']
PROFILES = {
    'oracle_O0': ['-O0'],
    'generic': ['-O3'],
    'native': ['-O3', '-march=native'],
    'sanitized': ['-O1', '-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer'],
}
PREFLAGS = ['-std=c11', '-DMINI_DATASET', '-DPOLYBENCH_USE_C99_PROTO']
# Do NOT define POLYBENCH_USE_SCALAR_LB: in this release it selects fixed macro bounds!
C_PREFIX = '#include <math.h>\n#include <stdint.h>\n#include <string.h>\ntypedef char base;\n'
HINT = '#pragma clang loop unroll_count(4)\n'
MAX_BYTES = 100 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def safe(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or '\\' in rel or '\x00' in rel:
        raise ValueError('invalid_relative_name')
    p = PurePosixPath(rel)
    if p.is_absolute() or '..' in p.parts or str(p) == '.':
        raise ValueError('unsafe_relative_name')
    out = root / str(p)
    if not out.resolve().is_relative_to(root.resolve()):
        raise ValueError('outside_root')
    q = out
    while q != root:
        if q.is_symlink():
            raise ValueError('symlink_refused')
        q = q.parent
    return out


def snapshot(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise RuntimeError(f'symlink_refused: {p}')
        if p.is_file():
            out[str(p.relative_to(root))] = file_sha(p)
    return out


def check_artifacts(run: Path) -> int:
    m = json.loads((run/'artifacts.json').read_text())
    if not isinstance(m, dict) or not m:
        raise RuntimeError('empty_artifact_manifest')
    got = snapshot(run)
    got.pop('artifacts.json', None)
    if got != m:
        raise RuntimeError('artifact_manifest_mismatch')
    for name in m:
        safe(run, name)
    return len(m)


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('git_read_failed: '+p.stderr.decode(errors='replace')[:600])
    return p.stdout.decode('utf-8')


def tracked(repo: Path) -> dict[str, str]:
    return {n: file_sha(safe(repo,n)) for n in git(repo,'ls-files','-z').split('\0') if n}


def command(argv: list[str], evidence: Path, timeout: int = 90) -> dict:
    evidence.mkdir(parents=True, exist_ok=False)
    start = time.monotonic_ns()
    env = dict(os.environ, LC_ALL='C', ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    try:
        p = subprocess.run(argv, capture_output=True, cwd=evidence, timeout=timeout, env=env)
        state = 'ok' if p.returncode == 0 else 'process_failed'
        code, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        state, code, stdout, stderr = 'timeout', None, e.stdout or b'', e.stderr or b''
    except OSError as e:
        state, code, stdout, stderr = 'launch_failed', None, b'', str(e).encode()
    (evidence/'stdout.raw').write_bytes(stdout)
    (evidence/'stderr.raw').write_bytes(stderr)
    rec = {'argv':argv,'state':state,'returncode':code,'process_elapsed_ns':time.monotonic_ns()-start,
           'process_elapsed_is_kernel_time':False, 'stdout_sha256':sha(stdout), 'stderr_sha256':sha(stderr)}
    write_json(evidence/'command.json',rec)
    return rec


def ok_command(argv: list[str], evidence: Path) -> dict:
    rec = command(argv,evidence)
    if rec['state'] != 'ok':
        raise RuntimeError(f'command_failed ({rec["state"]}): {evidence}/stderr.raw')
    return rec


def extract_function(text: str, name: str) -> str:
    # Navigation only, not a semantic proof. Input is the compiler's preprocessed C.
    matches = list(re.finditer(r'\bstatic\s+void\s+'+re.escape(name)+r'\s*\(',text))
    if len(matches) != 1:
        raise RuntimeError(f'expected_one_kernel_definition: {name}: {len(matches)}')
    start = matches[0].start()
    opening = text.find('{',matches[0].end())
    if opening < 0 or ';' in text[matches[0].end():opening]:
        raise RuntimeError('kernel_definition_not_found')
    depth, quote, escape, end = 0, None, False, None
    for pos in range(opening,len(text)):
        c = text[pos]
        if quote:
            if escape: escape=False
            elif c=='\\': escape=True
            elif c==quote: quote=None
            continue
        if c in ('"', "'"): quote=c
        elif c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                end=pos+1; break
    if end is None:
        raise RuntimeError('unbalanced_kernel')
    return text[start:end]


def normalize_kernel(original: str, name: str) -> str:
    renamed, count = re.subn(r'^static\s+void\s+'+re.escape(name)+r'\b',
                             '__attribute__((noinline)) void cpucond_kernel', original, count=1)
    if count!=1:
        raise RuntimeError('kernel_export_failed')
    # Leave the complete compound statement byte-for-byte unchanged.
    if original[original.index('{'):] != renamed[renamed.index('{'):]:
        raise RuntimeError('kernel_body_changed')
    return renamed


def with_hint(base: str) -> str:
    body = base.index('{')
    m = re.search(r'\bfor\s*\(',base[body:])
    if not m:
        raise RuntimeError('no_loop_for_hint')
    at = body+m.start()
    # The initial loop is directly after declarations/pragmas, not after an if.
    result=base[:at]+'\n'+HINT+base[at:]
    if result[:at]+result[at+len(HINT)+1:] != base:
        raise RuntimeError('unexpected_hint_change')
    return result


def layout(task: str, p: int, q: int, r: int) -> list[tuple[str,str,int,bool]]:
    if not all(type(x) is int and 1<=x<=512 for x in (p,q,r)):
        raise ValueError('dimensions_outside_1_512')
    if task=='gemm': return [('C','d',p*q,False),('A','d',p*r,True),('B','d',r*q,True)]
    if task=='atax': return [('A','d',p*q,True),('x','d',q,True),('y','d',q,False),('tmp','d',p,False)]
    if task=='jacobi-2d':
        if p<3: raise ValueError('jacobi_requires_n_ge_3')
        return [('A','d',p*p,False),('B','d',p*p,False)]
    if task=='trisolv': return [('L','d',p*p,True),('x','d',p,False),('b','d',p,True)]
    if task=='nussinov': return [('seq','B',p,True),('table','i',p*p,False)]
    if task=='correlation': return [('data','d',q*p,False),('corr','d',p*p,False),('mean','d',p,False),('stddev','d',p,False)]
    raise ValueError('unknown_task')


def cases(task: str) -> list[dict]:
    out=[]
    for a,(p,q,r) in enumerate(((3,5,4),(7,9,5),(17,15,19),(32,33,31))):
        for b,fam in enumerate(('dense','cancellation','signed_zero_tiny')):
            out.append({'case_id':f'v{a}-{fam}','p':p,'q':q,'r':r,'t':3,
                        'family':fam,'seed':701+17*a+b,'timing':False})
    for p in (64,128):
        out.append({'case_id':f'perf{p}-dense','p':p,'q':p+1,'r':p-1,'t':5,
                    'family':'dense','seed':971,'timing':True})
    return out


def input_blob(task: str, c: dict) -> bytes:
    p,q,r = (c[x] for x in ('p','q','r'))
    rng=random.Random(c['seed'])
    parts=[]
    def val(j: int) -> float:
        if c['family']=='dense':
            # Full 52-bit mantissa, varying binary exponent and sign; not the old 16-bit lattice.
            bits=(rng.getrandbits(1)<<63)|((1023-rng.randrange(1,9))<<52)|rng.getrandbits(52)
            return struct.unpack('<d',struct.pack('<Q',bits))[0]
        if c['family']=='cancellation':
            return (0.25,-0.25,2.0**-56,-2.0**-54,0.1,-0.3)[j%6]
        if c['family']=='signed_zero_tiny':
            return (-0.0,0.0,2.0**-1022,-2.0**-1022,2.0**-1074,-2.0**-1074)[j%6]
        raise ValueError('unknown_input_family')
    for name,typ,count,ro in layout(task,p,q,r):
        if typ=='B':
            values=[rng.randrange(4) if c['family']=='dense' else (j%4 if c['family']=='cancellation' else 0) for j in range(count)]
        elif typ=='i': values=[0]*count
        elif task=='trisolv' and name=='L':
            values=[]
            for i in range(p):
                for j in range(p):
                    # Nonsingular lower triangular domain, no division-by-zero or explosive growth.
                    values.append(2.0 if i==j else (val(i*p+j)/(8*p) if j<i else 0.0))
        elif (task=='atax' and name in ('y','tmp')) or (task=='correlation' and name!='data') or (task=='trisolv' and name=='x'):
            values=[-0.125]*count
        else: values=[val(j) for j in range(count)]
        parts.append(struct.pack('<'+str(count)+typ,*values))
    return b''.join(parts)


def validate_blob(task: str, c: dict, raw: bytes) -> None:
    off=0
    for name,typ,count,ro in layout(task,c['p'],c['q'],c['r']):
        size=struct.calcsize('<'+typ)*count
        data=raw[off:off+size]
        if len(data)!=size:
            raise ValueError('short_output')
        if typ=='d' and any(not math.isfinite(v[0]) for v in struct.iter_unpack('<d',data)):
            raise ValueError('nonfinite_output')
        if typ=='B' and any(v>3 for v in data):
            raise ValueError('sequence_domain_violation')
        off+=size
    if len(raw)!=off:
        raise ValueError('trailing_or_empty_output')


def compare_result(task: str, c: dict, inp: bytes, oracle: bytes, result: bytes, state: str) -> dict:
    if state!='ok':
        return {'passed':False,'reason':state}
    try:
        validate_blob(task,c,result)
    except ValueError as e:
        return {'passed':False,'reason':str(e)}
    off=0
    for name,typ,count,ro in layout(task,c['p'],c['q'],c['r']):
        length=count*struct.calcsize('<'+typ)
        if ro and result[off:off+length]!=inp[off:off+length]:
            return {'passed':False,'reason':'readonly_input_changed','buffer':name}
        off+=length
    if result!=oracle:
        at=next(i for i,(x,y) in enumerate(zip(result,oracle)) if x!=y)
        return {'passed':False,'reason':'value_mismatch','first_differing_byte':at,
                'expected_byte':oracle[at],'observed_byte':result[at]}
    return {'passed':True,'reason':'all_declared_buffer_bytes_match'}


def admit(rows: list[dict], count: int, variant: str, negative_ok: bool) -> bool:
    return variant!='wrong_output_control' and negative_ok and len(rows)==count and all(x['passed'] for x in rows)


WRAPPER_SIGS={
'gemm':'int ni,int nj,int nk,double alpha,double beta,double C[ni][nj],double A[ni][nk],double B[nk][nj]',
'atax':'int m,int n,double A[m][n],double x[n],double y[n],double tmp[m]',
'jacobi-2d':'int tsteps,int n,double A[n][n],double B[n][n]',
 'trisolv':'int n,double L[n][n],double x[n],double b[n]',
 'nussinov':'int n,char seq[n],int table[n][n]',
 'correlation':'int m,int n,double float_n,double data[n][m],double corr[m][m],double mean[m],double stddev[m]',
}
CALLS={
'gemm':'cpucond_kernel(p,q,r,1.5,1.2,(double(*)[q])b[0].data,(double(*)[r])b[1].data,(double(*)[q])b[2].data);',
'atax':'cpucond_kernel(p,q,(double(*)[q])b[0].data,(double*)b[1].data,(double*)b[2].data,(double*)b[3].data);',
'jacobi-2d':'cpucond_kernel(t,p,(double(*)[p])b[0].data,(double(*)[p])b[1].data);',
 'trisolv':'cpucond_kernel(p,(double(*)[p])b[0].data,(double*)b[1].data,(double*)b[2].data);',
 'nussinov':'cpucond_kernel(p,(char*)b[0].data,(int(*)[p])b[1].data);',
 'correlation':'cpucond_kernel(p,q,(double)q,(double(*)[p])b[0].data,(double(*)[p])b[1].data,(double*)b[2].data,(double*)b[3].data);',
}
WRONG_TARGETS={
'gemm':'C[ni-1][nj-1]', 'atax':'y[n-1]', 'jacobi-2d':'A[n-2][n-2]',
 'trisolv':'x[n-1]', 'nussinov':'table[0][n-1]', 'correlation':'corr[m-1][m-1]',
}
SETUP={
'gemm':'add(b,&nb,(size_t)p*q,8,0); add(b,&nb,(size_t)p*r,8,1); add(b,&nb,(size_t)r*q,8,1);',
'atax':'add(b,&nb,(size_t)p*q,8,1); add(b,&nb,q,8,1); add(b,&nb,q,8,0); add(b,&nb,p,8,0);',
'jacobi-2d':'add(b,&nb,(size_t)p*p,8,0); add(b,&nb,(size_t)p*p,8,0);',
 'trisolv':'add(b,&nb,(size_t)p*p,8,1); add(b,&nb,p,8,0); add(b,&nb,p,8,1);',
 'nussinov':'add(b,&nb,p,1,1); add(b,&nb,(size_t)p*p,4,0);',
 'correlation':'add(b,&nb,(size_t)q*p,8,0); add(b,&nb,(size_t)p*p,8,0); add(b,&nb,p,8,0); add(b,&nb,p,8,0);',
}
DRIVER=r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <fenv.h>
#include <time.h>
#if defined(__SSE__)
#include <xmmintrin.h>
#endif
_Static_assert(sizeof(double)==8 && DBL_MANT_DIG==53 && DBL_MAX_EXP==1024,"binary64 required");
_Static_assert(sizeof(int)==4,"32 bit int required");
void cpucond_kernel(@SIGNATURE@);
typedef struct {unsigned char *allocation,*data,*initial,*expected; size_t bytes; int width,ro;} Buffer;
static void fail(const char *s){fprintf(stderr,"%s\n",s);exit(4);}
static void add(Buffer *b,int *nb,size_t count,int width,int ro){
 Buffer *x=&b[(*nb)++]; x->bytes=count*(size_t)width;x->width=width;x->ro=ro;
 x->allocation=malloc(x->bytes+128); x->initial=malloc(x->bytes);x->expected=malloc(x->bytes);
 if(!x->allocation||!x->initial||!x->expected)fail("allocation_failed");
 memset(x->allocation,0xA5,x->bytes+128);x->data=x->allocation+64;
}
static void inspect(Buffer*b,int nb){
 for(int k=0;k<nb;k++){
  for(int j=0;j<64;j++)if(b[k].allocation[j]!=0xA5||b[k].data[b[k].bytes+j]!=0xA5)fail("guard_changed");
  if(b[k].ro&&memcmp(b[k].data,b[k].initial,b[k].bytes))fail("readonly_input_changed");
  if(b[k].width==8)for(size_t j=0;j<b[k].bytes;j+=8){double d;memcpy(&d,b[k].data+j,8);if(!isfinite(d))fail("nonfinite_output");}
 }
}
static void reset(Buffer*b,int nb){for(int k=0;k<nb;k++)memcpy(b[k].data,b[k].initial,b[k].bytes);}
static void exact_check(Buffer*b,int nb){inspect(b,nb);for(int k=0;k<nb;k++)if(memcmp(b[k].data,b[k].expected,b[k].bytes))fail("timed_result_mismatch");}
static uint64_t ns(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC_RAW,&t))fail("clock_failed");return (uint64_t)t.tv_sec*UINT64_C(1000000000)+(uint64_t)t.tv_nsec;}
static int number(const char*s){char*e=0;long v=strtol(s,&e,10);if(!*s||*e||v<1||v>512)fail("bad_dimension");return(int)v;}
int main(int argc,char**argv){
 if(argc!=8)fail("usage: program p q r t input.bin verify|time expected.bin");
 uint16_t endian=1;if(*(unsigned char*)&endian!=1)fail("little_endian_required");
 if(fesetround(FE_TONEAREST)!=0)fail("rounding_mode_failed");
#if defined(__SSE__)
 _mm_setcsr(_mm_getcsr()&~((1u<<15)|(1u<<6))); /* disable FTZ and DAZ in this process */
#endif
 int p=number(argv[1]),q=number(argv[2]),r=number(argv[3]),t=number(argv[4]);
 @DIMCHECK@
 Buffer b[4]={0};int nb=0; @SETUP@
 FILE*f=fopen(argv[5],"rb");if(!f)fail("input_open_failed");
 for(int k=0;k<nb;k++)if(fread(b[k].initial,1,b[k].bytes,f)!=b[k].bytes)fail("short_input");
 if(fgetc(f)!=EOF)fail("trailing_input");fclose(f);
 if(!strcmp(argv[6],"verify")){
  reset(b,nb); @CALL@
  inspect(b,nb);
  for(int k=0;k<nb;k++)if(fwrite(b[k].data,1,b[k].bytes,stdout)!=b[k].bytes)fail("output_failed");
 }else if(!strcmp(argv[6],"time")){
  f=fopen(argv[7],"rb");if(!f)fail("expected_open_failed");
  for(int k=0;k<nb;k++)if(fread(b[k].expected,1,b[k].bytes,f)!=b[k].bytes)fail("short_expected");
  if(fgetc(f)!=EOF)fail("trailing_expected");fclose(f);
  for(int warm=0;warm<2;warm++){reset(b,nb); @CALL@ exact_check(b,nb);}
  reset(b,nb); uint64_t a=ns(); @CALL@ uint64_t z=ns();
  exact_check(b,nb);if(z<=a)fail("nonpositive_kernel_duration");
  printf("CPUCOND_KERNEL_NS %llu\n",(unsigned long long)(z-a));
 }else fail("invalid_mode");
 for(int k=0;k<nb;k++){free(b[k].allocation);free(b[k].initial);free(b[k].expected);}
 return 0;
}
'''


def driver(task: str) -> str:
    s=DRIVER
    for tag,val in {'SIGNATURE':WRAPPER_SIGS[task], 'SETUP':SETUP[task], 'CALL':CALLS[task],
                    'DIMCHECK':'if(p<3)fail("jacobi_requires_n_ge_3");' if task=='jacobi-2d' else ''}.items():
        s=s.replace('@'+tag+'@',val)
    return s


def candidate_source(task: str, normalized: str, variant: str) -> str:
    if variant in ('reference','identity'): content=normalized
    elif variant=='hint_unroll_4': content=with_hint(normalized)
    elif variant=='wrong_output_control':
        target=WRONG_TARGETS[task]
        if task=='nussinov': mutation=f'\n{target} ^= 1;\n'
        else: mutation=f'\n{{ uint64_t z; memcpy(&z, &{target}, 8); z ^= 1; memcpy(&{target}, &z, 8); }}\n'
        content=normalized[:-1]+mutation+'}'
    else: raise ValueError('unknown_variant')
    return C_PREFIX+content+'\n'


def preprocessed_kernel(compiler: str, root: Path, row: dict, d: Path) -> tuple[str,dict]:
    source=safe(root,row['source'])
    inc=[ '-I',str(root/'utilities'),'-I',str(source.parent)]
    rec=ok_command([compiler,*PREFLAGS,*inc,'-E','-P',str(source)],d/'preprocess')
    text=(d/'preprocess/stdout.raw').read_text()
    name='kernel_'+row['id'].replace('-','_')
    block=extract_function(text,name)
    # Exact fragment is retained; no mathematical rewrite or header substitution.
    (d/'extracted-original.c').write_text(block+'\n')
    n=normalize_kernel(block,name)
    # Headers must actually have selected original types, not implicit/different types.
    typ='int' if row['id']=='nussinov' else 'double'
    if typ not in n[:n.index('{')]: raise RuntimeError('unexpected_kernel_type')
    return n,{'source':row['source'],'source_sha256':file_sha(source),'extracted_sha256':sha(block.encode()),
              'normalized_sha256':sha(n.encode()),'preprocessor_command':rec['argv'],
              'body_preserved_byte_for_byte':True,'extraction_is_semantic_proof':False}


def compile_variant(compiler: str, task: str, code: str, drv: str, flags: list[str], d: Path, analyze: bool) -> dict:
    d.mkdir(parents=True, exist_ok=False)
    (d/'kernel.c').write_text(code)
    (d/'driver.c').write_text(drv)
    base=[compiler,*FP_FLAGS,*flags]
    records=[]
    for unit in ('kernel','driver'):
        extra=['-fsave-optimization-record'] if analyze and unit=='kernel' else []
        records.append(ok_command([*base,*extra,'-c',str(d/(unit+'.c')),'-o',str(d/(unit+'.o'))],d/(unit+'-compile')))
    records.append(ok_command([*base,str(d/'kernel.o'),str(d/'driver.o'),'-lm','-o',str(d/'program')],d/'link'))
    if analyze:
        for label,args in [('ir',['-S','-emit-llvm']),('asm',['-S'])]:
            extension='ll' if label=='ir' else 's'
            ok_command([*base,*args,str(d/'kernel.c'),'-o',str(d/('kernel.'+extension))],d/label)
        tool=shutil.which('llvm-objdump') or shutil.which('objdump')
        if tool:
            rec=command([tool,'-d',str(d/'program')],d/'disassembly')
            if rec['state']!='ok': raise RuntimeError('disassembly_failed')
        else:
            write_json(d/'analysis-unavailable.json',{'reason':'no_objdump','not_equivalent_to_no_code_change':True})
    return {'binary':str(d/'program'),'binary_sha256':file_sha(d/'program'),
            'kernel_source_sha256':file_sha(d/'kernel.c'),'driver_source_sha256':file_sha(d/'driver.c'),
            'flags':base[1:],'commands':records}


def run_binary(build: dict,c: dict,inp: Path,mode: str,expected: Path,evidence: Path) -> dict:
    binary=Path(build['binary'])
    if file_sha(binary)!=build['binary_sha256']:
        raise RuntimeError('binary_changed_since_build')
    return command([str(binary),str(c['p']),str(c['q']),str(c['r']),str(c['t']),str(inp),mode,str(expected)],evidence)


def assert_inference_idle() -> dict:
    # No HTTP/API calls; process check only. Idle serve is allowed; runner is not.
    bad=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try:
            b=(p/'cmdline').read_bytes()
        except (OSError,PermissionError): continue
        parts=[x.decode(errors='replace') for x in b.split(b'\0') if x]
        if not parts: continue
        executable=Path(parts[0]).name.lower()
        if ((executable=='ollama' and any(x.lower()=='runner' for x in parts[1:3])) or
            executable in ('llama-server','llama-cli','ollama_llama_server')):
            bad.append({'pid':int(p.name),'executable':executable})
    if bad:
        raise RuntimeError('active_local_inference_detected_stop_it_before_timing: '+json.dumps(bad))
    return {'known_inference_runners_detected':0,'method':'local_process_name_scan',
            'all_external_load_excluded':False}


@contextlib.contextmanager
def affinity():
    old=os.sched_getaffinity(0)
    if not old: raise RuntimeError('no_available_cpu')
    cpu=min(old)
    os.sched_setaffinity(0,{cpu})
    try:
        if os.sched_getaffinity(0)!={cpu}: raise RuntimeError('affinity_not_applied')
        yield cpu
    finally: os.sched_setaffinity(0,old)


def iqr(xs: list[int|float]) -> float:
    q=statistics.quantiles(xs,n=4,method='inclusive')
    return q[2]-q[0]


def parse_timing(raw: bytes,state: str) -> int:
    if state!='ok': raise RuntimeError('timing_process_failed')
    m=re.fullmatch(rb'CPUCOND_KERNEL_NS ([0-9]+)\n',raw)
    if not m or int(m[1])<=0: raise RuntimeError('invalid_kernel_time')
    return int(m[1])


def contract(task: str) -> dict:
    domain={
      'gemm':'Finite binary64 A,B,C in declared test generators; alpha=1.5, beta=1.2. No change to multiplication association or k accumulation order.',
      'atax':'Finite binary64 A,x; observe y AND tmp. Neither A nor x may change.',
      'jacobi-2d':'n>=3; positive fixed step counts; both A and B (including boundaries) are observed. Time-step order must remain.',
      'trisolv':'Finite nonsingular lower triangle; test diagonal=2, small off-diagonal values. L and b remain unchanged; observe every x.',
      'nussinov':'char sequence values 0..3, zero-initialized 32-bit integer table; observe whole table, preserve sequence. Dimensions <=512.',
      'correlation':'Finite binary64 data, float_n=runtime n>0; retain original epsilon and sqrt/order. Observe data,corr,mean,stddev.',
    }
    return {'task':task,'contract_revision':REVISION,'domain':domain[task],
      'same_as_upstream_initialization':False,'input_domain_role':'explicit_custom_adapter_tests_not_stock_initializer',
      'array_aliasing':'distinct allocations as declared; overlapping arrays not supported',
      'comparison':'exact bytes of ALL passed arrays, including intermediates; finite outputs required',
      'floating_point':'binary64 RN-even, no fast math/contraction; signed zero and subnormals retained',
      'exception_flags_observable':False,'errno_observable':False,'nan_inf_inputs_allowed':False,
      'trust_boundary':'same Clang toolchain O0 reference, C/runtime/library/compiler trusted; no universal proof',
      'admitted_candidate_family':'identity or an added compiler unroll hint only; negative control deliberately corrupts output',
      'formal_equivalence_proven':False,'arbitrary_C_or_IR_or_ASM_candidate_supported':False}


def consume_intake(intake: Path,repo: Path) -> tuple[Path,list[dict],dict]:
    count=check_artifacts(intake)
    summary=json.loads((intake/'summary.json').read_text())
    if summary.get('completion')!='DATASET_INTAKE_COMPLETE' or summary.get('passed') is not True:
        raise RuntimeError('intake_not_complete')
    lock=json.loads((intake/'dataset-lock.json').read_text())
    upstream=intake/'upstream'
    if snapshot(upstream)!=lock['upstream_file_sha256']:
        raise RuntimeError('upstream_hashes_changed')
    rows=json.loads((intake/'polybench-catalog.json').read_text())
    if len(rows)!=30 or len({r['id'] for r in rows})!=30:
        raise RuntimeError('unexpected_polybench_catalog')
    selected=[next(r for r in rows if r['id']==name) for name in TASKS]
    root=upstream/'polybench-c-4.2.1-beta'
    observed={x['kernel_id']:x for x in json.loads((intake/'build-results.json').read_text())}
    for row in selected:
        expected_type='int' if row['id']=='nussinov' else 'double'
        if observed.get(row['id'],{}).get('observed_DATA_TYPE_macro')!=expected_type:
            raise RuntimeError('unexpected_original_DATA_TYPE: '+row['id'])
        if file_sha(safe(root,row['source']))!=row['source_sha256'] or file_sha(safe(root,row['header']))!=row['header_sha256']:
            raise RuntimeError('selected_kernel_changed')
    return root,selected,{'intake_run':str(intake),'artifacts_checked':count,
         'intake_manifest_sha256':file_sha(intake/'artifacts.json'),'datasets':lock['datasets'],
         'tsvc_handling':'unchanged lexical index; no TSVC execution or admission in this runner'}


def run_task(task: str, row: dict, pb: Path, compiler: str, out: Path, do_time: bool) -> dict:
    d=out/task;d.mkdir()
    cs=cases(task)
    write_json(d/'contract.json',contract(task));write_json(d/'cases.json',cs)
    normalized,origin=preprocessed_kernel(compiler,pb,row,d)
    write_json(d/'kernel-provenance.json',origin)
    inputpaths={}
    (d/'inputs').mkdir()
    for c in cs:
        path=d/'inputs'/(c['case_id']+'.bin');path.write_bytes(input_blob(task,c));inputpaths[c['case_id']]=path
    input_hashes={k:file_sha(p) for k,p in inputpaths.items()}
    write_json(d/'input-hashes.json',input_hashes)
    build={}
    for prof,flags in PROFILES.items():
        for variant in (('reference',) if prof=='oracle_O0' else CANDIDATES):
            build[(prof,variant)]=compile_variant(compiler,task,candidate_source(task,normalized,variant),driver(task),flags,d/'build'/prof/variant,prof=='native' and variant!='wrong_output_control')
    write_json(d/'builds.json', {p+'/'+v:b for (p,v),b in build.items()})
    oracles={}; rows_out={}; negative_ok=True
    for c in cs:
        key=c['case_id']; ev=d/'validation'/'oracle_O0'/key
        rec=run_binary(build[('oracle_O0','reference')],c,inputpaths[key],'verify',Path('/dev/null'),ev)
        raw=(ev/'stdout.raw').read_bytes();inp=inputpaths[key].read_bytes()
        judged=compare_result(task,c,inp,raw,raw,rec['state'])
        if not judged['passed']: raise RuntimeError(f'oracle_invalid: {task} {key}: {judged}')
        oracles[key]=ev/'stdout.raw'
    for prof in ('generic','native','sanitized'):
        for variant in CANDIDATES:
            rows_out[(prof,variant)]=[]
            for c in cs:
                key=c['case_id'];ev=d/'validation'/prof/variant/key
                rec=run_binary(build[(prof,variant)],c,inputpaths[key],'verify',Path('/dev/null'),ev)
                result=compare_result(task,c,inputpaths[key].read_bytes(),oracles[key].read_bytes(),(ev/'stdout.raw').read_bytes(),rec['state'])
                result.update(case_id=key,binary_sha256=build[(prof,variant)]['binary_sha256'])
                write_json(ev/'result.json',result);rows_out[(prof,variant)].append(result)
            nr=rows_out[(prof,variant)]
            print(f'{task}/{prof}/{variant}: exact={sum(r["passed"] for r in nr)}/{len(cs)}',flush=True)
            if variant=='wrong_output_control' and not all(not r['passed'] and r['reason']=='value_mismatch' for r in nr): negative_ok=False
    admissions={}
    for variant in CANDIDATES:
        allrows=[r for prof in ('generic','native','sanitized') for r in rows_out[(prof,variant)]]
        admissions[variant]=admit(allrows,3*len(cs),variant,negative_ok)
    oracle_hashes={k:file_sha(p) for k,p in oracles.items()}
    if input_hashes!={k:file_sha(p) for k,p in inputpaths.items()}:raise RuntimeError('inputs_changed_during_validation')
    gate={'candidate_admission':admissions,'negative_control_detected_in_every_case':negative_ok,
          'input_sha256':input_hashes,'reference_output_sha256':oracle_hashes,
          'correctness_rows':{p+'/'+v:r for (p,v),r in rows_out.items()},
          'criteria':'all generic/native/sanitized results equal O0 reference full-state output; negative controls fail by value mismatch',
          'proof':False,'existing_cpucond_CLI_modified':False}
    write_json(d/'gate.json',gate)
    gate_hash=file_sha(d/'gate.json')
    allgood=negative_ok and all(admissions[v] for v in ('reference','identity','hint_unroll_4'))
    timing=[]
    if do_time and allgood:
        # Gate is mandatory and cannot be bypassed via a CLI flag.
        idle=assert_inference_idle()
        rng=random.Random(414209)
        schedules=[]
        for c in cs:
            if not c['timing']: continue
            for trial in range(7):
                variants=['identity','hint_unroll_4'];rng.shuffle(variants)
                for v in variants:
                    order=['reference',v];rng.shuffle(order)
                    schedules.append({'case_id':c['case_id'],'trial':trial,'candidate':v,'order':order})
        write_json(d/'measurement-plan.json',{'schedule':schedules,'gate_sha256':gate_hash,
          'profile':'native','phases':['confirmation_only_no_search'],'warmups_per_process':2,
          'clock':'CLOCK_MONOTONIC_RAW','all_buffers_rechecked_after_each_call':True,
          'min_duration_warning_ns':100000,'relative_iqr_warning':0.2,'inference_observation':idle})
        by_case={c['case_id']:c for c in cs}
        with affinity() as cpu:
            write_json(d/'affinity.json',{'applied_cpu':cpu,'scope':'this_runner_and_children_during_measurement'})
            for i,s in enumerate(schedules):
                if file_sha(d/'gate.json')!=gate_hash or not admissions[s['candidate']]: raise RuntimeError('gate_changed_or_denied')
                assert_inference_idle()
                c=by_case[s['case_id']];obs={}
                if file_sha(inputpaths[c['case_id']])!=input_hashes[c['case_id']] or file_sha(oracles[c['case_id']])!=oracle_hashes[c['case_id']]:
                    raise RuntimeError('timing_input_or_expected_output_changed')
                for v in s['order']:
                    ev=d/'timing'/f'pair-{i:03d}'/v
                    rec=run_binary(build[('native',v)],c,inputpaths[c['case_id']],'time',oracles[c['case_id']],ev)
                    obs[v]=parse_timing((ev/'stdout.raw').read_bytes(),rec['state'])
                timing.append({**s,'durations_ns':obs,'speedup':obs['reference']/obs[s['candidate']],
                               'cpu':cpu,'all_observable_buffers_matched':True})
        write_json(d/'timing.json',timing)
    aggregate=[]
    for c in cs:
        for v in ('identity','hint_unroll_4'):
            selected=[t for t in timing if t['case_id']==c['case_id'] and t['candidate']==v]
            if not selected:continue
            ratios=[t['speedup'] for t in selected];dur=[t['durations_ns'][v] for t in selected]
            warnings=[]
            if min(dur)<100000:warnings.append('short_kernel_duration')
            if iqr(dur)/statistics.median(dur)>0.2:warnings.append('high_duration_variability')
            if iqr(ratios)/statistics.median(ratios)>0.2:warnings.append('high_paired_ratio_variability')
            aggregate.append({'case_id':c['case_id'],'candidate':v,'pairs':len(selected),
              'candidate_median_ns':statistics.median(dur),'candidate_iqr_ns':iqr(dur),
              'median_paired_speedup':statistics.median(ratios),'paired_speedup_iqr':iqr(ratios),
              'quality_warnings':warnings,'interpretation':'development_description_not_significance'})
    write_json(d/'timing-summary.json',aggregate)
    return {'task':task,'cases':len(cs),'passed':allgood,'gate':admissions,
            'negative_control_all_rejected':negative_ok,'timing_pairs':len(timing),'timing':aggregate,
            'unknown_pragma_effect':True,'speedup_is_not_a_pass_requirement':True}


def execute(args) -> int:
    repo=args.repo.resolve()
    if not (repo/'src/cpucond').is_dir():raise RuntimeError('wrong_repo')
    if sys.byteorder!='little':raise RuntimeError('little_endian_host_required')
    compiler=shutil.which('clang')
    if not compiler: raise RuntimeError('clang_missing_no_install_attempted')
    compiler=str(Path(compiler).resolve())
    intake=(args.intake or repo/INTAKE_REL).resolve()
    pb,rows,receipt=consume_intake(intake,repo)
    before=tracked(repo);head=git(repo,'rev-parse','HEAD').strip();upstream=snapshot(intake/'upstream')
    rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    out=repo/'runs/goal0042-polybench-gated'/rid;out.mkdir(parents=True,exist_ok=False)
    print('Run:',out,flush=True)
    shutil.copyfile(Path(__file__).resolve(),out/'runner.py')
    shutil.copyfile(pb/'LICENSE.txt',out/'PolyBench-LICENSE.txt')
    write_json(out/'input-receipt.json',receipt)
    write_json(out/'provenance.json',{'revision':REVISION,'git_head':head,'git_status':git(repo,'status','--short','--branch'),
        'tracked_source_sha256':before,'runner_sha256':file_sha(out/'runner.py'),'compiler':compiler,
        'compiler_sha256':file_sha(Path(compiler)), 'host':platform.uname()._asdict(),
        'available_cpus':sorted(os.sched_getaffinity(0)), 'existing_cli_gate_integrated':False})
    write_json(out/'plan.json',{'tasks':TASKS,'candidate_family':CANDIDATES,'profiles':PROFILES,'fp_flags':FP_FLAGS,
       'candidate_manifest_fixed_before_measurement':True,'timing_enabled':not args.verify_only,
       'unroll_hint_target':'first for loop of preprocessed kernel; not necessarily the performance bottleneck',
       'input_initialization':'custom bounded input families, not stock PolyBench initializer',
       'LLM_evaluation':False,'cross_CPU_evaluation':False,'TSVC_evaluation':False,
       'formal_equivalence_proven':False,'publishable_benchmark':False})
    taskresults=[];failure=None
    try:
        ok_command([compiler,'--version'],out/'compiler-version')
        for row in rows:
            try: taskresults.append(run_task(row['id'],row,pb,compiler,out,not args.verify_only))
            except Exception as e:
                taskresults.append({'task':row['id'],'passed':False,'failure':type(e).__name__+': '+str(e),'timing':[]})
                print(f'{row["id"]}: BLOCKED: {e}',flush=True)
        same=before==tracked(repo) and head==git(repo,'rev-parse','HEAD').strip()
        up_same=upstream==snapshot(intake/'upstream')
        if not same or not up_same: raise RuntimeError('existing_sources_changed')
    except Exception as e:
        failure=type(e).__name__+': '+str(e);same=before==tracked(repo);up_same=upstream==snapshot(intake/'upstream')
    passed=len(taskresults)==6 and all(t['passed'] for t in taskresults) and failure is None and same and up_same
    summary={'completion':'POLYBENCH_GATED_RUN_COMPLETE' if passed else 'POLYBENCH_GATED_RUN_BLOCKED',
      'passed':passed,'run_directory':str(out),'tasks_completed':sum(t['passed'] for t in taskresults),
      'tasks_planned':6,'case_count_per_task':14,'source_files_unchanged':same,'upstream_sources_unchanged':up_same,
      'runner_evaluation_gate_integrated':True,'existing_cpucond_CLI_gate_integrated':False,
      'equivalence_proven':False,'main_benchmark_admissible':False,'publishable_benchmark':False,
      'llm_requests':0,'model_downloads':0,'network_requests':0,
      'performance_measurements':sum(2*t.get('timing_pairs',0) for t in taskresults),
      'environment_role':'development_polybench_correctness_and_gated_timing','failure':failure,'tasks':taskresults}
    write_json(out/'summary.json',summary)
    lines=['# PolyBench: full-state gate and development timing','',summary['completion'],
      '全入力での同値性証明ではない。既存cpucond CLIは変更していない。LLMのCPU情報効果は未評価。',
      '原カーネルを実際に前処理して抽出。初期化は明示した独自の有限入力で、stock benchmark結果とは分ける。',
      'hintはコンパイラへの展開依頼のみ。数式のソース変更なし。採用・高速化・意図した変換の残存は別問題。',
      '', '| Task | gate | negative control | timing pairs |','|---|---|---|---|']
    for t in taskresults:
        lines.append(f'| {t["task"]} | {t["passed"]} | {t.get("negative_control_all_rejected","unknown")} | {t.get("timing_pairs",0)} |')
        if t.get('failure'):lines.append('\nBLOCKED: '+t['failure']+'\n')
    lines+=['','| Task | Case | Candidate | Paired median speedup | Warnings |','|---|---|---|---:|---|']
    for t in taskresults:
        for x in t.get('timing',[]):lines.append(f'| {t["task"]} | {x["case_id"]} | {x["candidate"]} | {x["median_paired_speedup"]:.5f} | {", ".join(x["quality_warnings"])} |')
    lines+=['','探索は行っていない。全条件を固定してから7ペアを測定。各呼出し後、時間外で全配列を原出力とmemcmp。',
      '再初期化・入力読込み・全出力検査・プロセス起動はカーネル時間に含めない。',
      '保護領域とASan/UBSanは全種類の不正読出しや未定義動作を証明的に排除するものではない。',
      'FTZ/DAZをこの実行プロセス内で無効化し、RN-evenを設定。例外フラグとerrnoは契約対象外。',
      'TSVC2の151宣言は未検証の索引のまま。元入力・型・仮定・同値性証明の範囲を混ぜない。',
      '', '## Summary',json.dumps(summary,ensure_ascii=False,indent=2)]
    report='\n'.join(lines)+'\n';(out/'report.md').write_text(report,encoding='utf-8')
    write_json(out/'artifacts.json',snapshot(out));count=check_artifacts(out)
    dest=Path('/mnt/c/Users/m.hirotaka/Downloads')
    if not dest.is_dir():dest=Path.home()/'cpucond-recovery';dest.mkdir(parents=True,exist_ok=True)
    share=dest/f'cpucond-polybench-gated-{rid}.txt'
    with share.open('x',encoding='utf-8') as f:f.write(report)
    print('Artifacts checked:',count)
    print(summary['completion']);print(json.dumps({k:v for k,v in summary.items() if k!='tasks'},ensure_ascii=False,indent=2))
    print('Shareable report:',share)
    return 0 if passed else 1


class Tests(unittest.TestCase):
    def test_extract(self):
        s='static void kernel_a(int n){int i; for(i=0;i<n;i++){ (void)i; }}\nint main(void){return 0;}'
        f=extract_function(s,'kernel_a');self.assertTrue(f.endswith('}}'));self.assertNotIn('main',f)
    def test_duplicate(self):
        s='static void k(void){}\nstatic void k(void){}'
        with self.assertRaises(RuntimeError):extract_function(s,'k')
    def test_prototype(self):
        with self.assertRaises(RuntimeError):extract_function('static void k(void);','k')
    def test_brace_in_string(self):
        f=extract_function('static void k(void){char*s="}";}','k');self.assertTrue(f.endswith(';}'))
    def test_no_function(self):
        with self.assertRaises(RuntimeError):extract_function('int x;','k')
    def test_body_preserved(self):
        s='static void k(int n) { for(int i=0;i<n;i++){} }';n=normalize_kernel(s,'k');self.assertEqual(s[s.index('{'):],n[n.index('{'):])
    def test_hint_only(self):
        s='void cpucond_kernel(int n){for(int i=0;i<n;i++){} }';self.assertEqual(with_hint(s).replace('\n'+HINT,''),s)
    def test_no_loop(self):
        with self.assertRaises(RuntimeError):with_hint('void k(void){}')
    def test_all_tasks_layouts(self):
        for t in TASKS:self.assertTrue(layout(t,3,5,4))
    def test_zero_dimension(self):
        with self.assertRaises(ValueError):layout('gemm',0,2,2)
    def test_oversized(self):
        with self.assertRaises(ValueError):layout('gemm',513,2,2)
    def test_unknown(self):
        with self.assertRaises(ValueError):layout('foo',3,3,3)
    def test_jacobi_min(self):
        with self.assertRaises(ValueError):layout('jacobi-2d',1,2,2)
    def test_input_determinism(self):
        for t in TASKS:
            for c in cases(t):self.assertEqual(input_blob(t,c),input_blob(t,c))
    def test_case_count(self):
        for t in TASKS:self.assertEqual(len(cases(t)),14)
    def test_timing_cases_also_validated(self):
        for t in TASKS:self.assertEqual(sum(c['timing'] for c in cases(t)),2)
    def test_blobs(self):
        for t in TASKS:
            for c in cases(t):validate_blob(t,c,input_blob(t,c))
    def test_missing_output(self):
        with self.assertRaises(ValueError):validate_blob('gemm',cases('gemm')[0],b'')
    def test_trailing_output(self):
        c=cases('gemm')[0]
        with self.assertRaises(ValueError):validate_blob('gemm',c,input_blob('gemm',c)+b'\0')
    def test_nonfinite(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        with self.assertRaises(ValueError):validate_blob('gemm',c,struct.pack('<d',float('nan'))+b[8:])
    def test_signed_zero_distinct(self):
        c=cases('gemm')[0];b=input_blob('gemm',c);a=struct.pack('<d',0.0)+b[8:];z=struct.pack('<d',-0.0)+b[8:]
        self.assertEqual(compare_result('gemm',c,b,a,z,'ok')['reason'],'value_mismatch')
    def test_readonly_change(self):
        c=cases('atax')[0];b=input_blob('atax',c);z=bytes([b[0]^1])+b[1:]
        self.assertEqual(compare_result('atax',c,b,b,z,'ok')['reason'],'readonly_input_changed')
    def test_failed_process(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        self.assertFalse(compare_result('gemm',c,b,b,b,'timeout')['passed'])
    def test_gate_negative(self):self.assertFalse(admit([{'passed':True}],1,'wrong_output_control',True))
    def test_gate_missing(self):self.assertFalse(admit([],1,'identity',True))
    def test_gate_control_missing(self):self.assertFalse(admit([{'passed':True}],1,'identity',False))
    def test_gate_pass(self):self.assertTrue(admit([{'passed':True}],1,'identity',True))
    def test_gate_fail(self):self.assertFalse(admit([{'passed':False}],1,'identity',True))
    def test_timing_parser(self):self.assertEqual(parse_timing(b'CPUCOND_KERNEL_NS 42\n','ok'),42)
    def test_timing_invalid(self):
        for b in (b'42',b'CPUCOND_KERNEL_NS 0\n',b'CPUCOND_KERNEL_NS -2\n'):
            with self.assertRaises(RuntimeError):parse_timing(b,'ok')
    def test_safe_path(self):
        for x in ('../x','/tmp/x','a/../../x','a\\b'):
            with self.assertRaises(ValueError):safe(Path('/tmp'),x)
    def test_file_no_overwrite(self):
        with tempfile.TemporaryDirectory() as z:
            p=Path(z)/'x';write_json(p,{})
            with self.assertRaises(FileExistsError):write_json(p,{})
    def test_artifact_tamper(self):
        with tempfile.TemporaryDirectory() as z:
            p=Path(z);(p/'x').write_bytes(b'a');write_json(p/'artifacts.json',snapshot(p));self.assertEqual(check_artifacts(p),1)
            (p/'x').write_bytes(b'b')
            with self.assertRaises(RuntimeError):check_artifacts(p)
    def test_driver_complete(self):
        for t in TASKS:
            text=driver(t);self.assertNotIn('@',text);self.assertIn('memcmp',text);self.assertIn('CLOCK_MONOTONIC_RAW',text)
    def test_identity_source(self):
        s='__attribute__((noinline)) void cpucond_kernel(void){}'
        self.assertEqual(candidate_source('gemm',s,'reference'),candidate_source('gemm',s,'identity'))


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.cwd());p.add_argument('--intake',type=Path)
    p.add_argument('--self-test',action='store_true');p.add_argument('--verify-only',action='store_true')
    p.add_argument('--check',type=Path)
    args=p.parse_args()
    if args.check:
        print('Artifacts checked:',check_artifacts(args.check.resolve()));return 0
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():return 1
    if args.self_test:return 0
    os.umask(0o077)
    lock=Path(tempfile.gettempdir())/f'cpucond-execution-{os.getuid()}.lock'
    try:
        with lock.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return execute(args)
    except Exception as e:
        print('POLYBENCH_GATED_RUN_BLOCKED:',type(e).__name__+': '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
