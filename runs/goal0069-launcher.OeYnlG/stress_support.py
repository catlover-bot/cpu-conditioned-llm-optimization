#!/usr/bin/env python3
"""C/LLVM IRコード生成経路の、多入力・全配列比較の開発用ゲート。

prepare: Goal0062の検証済みC/IRから小さな実機転送パッケージを作る。
run: 既存の開発用6課題×3サイズについて、未変更C/IRと既知の誤変換を実行する。
ネットワーク/API/Git更新/OS設定変更/速度測定はしない。
実行対象はハッシュ固定した参照と本ツールが作る負例のみ。
未知のLLM生成物を実行する入口は意図的に設けない。隔離実行器は別途必要。
最終30課題評価を6課題に減らすものではない。有限テストであり同値証明ではない。
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import random
import re
import shutil
import signal
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
import uuid

REVISION='codegen-development-gate-v1'
ADAPTER_SOURCE_BLOB='ef1717039a02000ab1bdf0ccaf6b98a99cd94412'
ROUNDTRIP_TOOL_SHA='caae960ddf1c919eb24c14ab55b85e9b35d351b966c1acf485816c31a88ff886'
TASKS=('gemm','atax','jacobi-2d','trisolv','nussinov','correlation')
SIZES=('MINI','SMALL','MEDIUM')
COMMON=['-std=gnu11','-fno-fast-math','-ffp-contract=off','-fno-lto']
GENERIC=['--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic']
NATIVE=['--target=x86_64-unknown-linux-gnu','-march=native']
MAX_FILE_BYTES=16*1024*1024

class GateError(RuntimeError):pass

def need(ok,msg):
    if not ok:raise GateError(msg)

def digest(data):return hashlib.sha256(data).hexdigest()

def file_sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def unique(pairs):
    d={}
    for k,v in pairs:
        need(k not in d,'JSONキー重複: '+k);d[k]=v
    return d

def load(p):
    def bad(v):raise GateError('不正なJSON数値: '+v)
    return json.loads(Path(p).read_text(encoding='utf-8'),object_pairs_hook=unique,parse_constant=bad)

def write(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(data,str):data=data.encode('utf-8')
    with p.open('xb') as f:f.write(data)

def jwrite(p,obj):write(p,json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def safe(root,rel):
    root=Path(root).resolve();q=PurePosixPath(rel)
    need(bool(q.parts) and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,'不正なパス: '+rel)
    p=root/Path(*q.parts)
    need(p.is_file() and root in p.resolve().parents,'ファイル欠落/範囲外: '+str(p))
    cur=p
    while cur!=root:
        need(not cur.is_symlink(),'リンクは許可しません: '+str(cur));cur=cur.parent
    return p

def get_manifest(root):
    result={}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        h,sep,rel=line.partition('  ')
        need(sep and re.fullmatch('[0-9a-f]{64}',h) and rel not in result,'ハッシュ一覧が不正')
        result[rel]=h
    return result

def hash_directory(root):
    pairs=[]
    for p in sorted(root.rglob('*')):
        need(not p.is_symlink(),'リンク入り結果は保存しません')
        if p.is_file() and p.name!='SHA256SUMS':pairs.append((p.relative_to(root).as_posix(),file_sha(p)))
    write(root/'SHA256SUMS',''.join(f'{h}  {rel}\n' for rel,h in pairs))
    return file_sha(root/'SHA256SUMS')

def cmd(argv,stem,timeout=120):
    """Known reference/control programs only. Record errors without counting them as passes."""
    stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
    env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LC_ALL':'C','HOME':str(stem.parent),
         'TMPDIR':str(stem.parent),'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1',
         'UBSAN_OPTIONS':'halt_on_error=1:print_stacktrace=1'}
    so_path=stem.with_suffix('.stdout');se_path=stem.with_suffix('.stderr')
    code=None;state='launch_failed'
    with so_path.open('xb') as so,se_path.open('xb') as se:
        try:
            p=subprocess.Popen([str(x) for x in argv],stdout=so,stderr=se,env=env,cwd=stem.parent,start_new_session=True)
            try:code=p.wait(timeout=timeout);state='ok' if code==0 else 'process_failed'
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);p.wait();state='timeout'
        except OSError as e:se.write(str(e).encode())
    rec={'argv':[str(x) for x in argv],'state':state,'returncode':code,
         'stdout_sha256':file_sha(so_path),'stderr_sha256':file_sha(se_path)}
    jwrite(stem.with_suffix('.command.json'),rec)
    return rec

def must(argv,stem,timeout=120):
    rec=cmd(argv,stem,timeout)
    need(rec['state']=='ok',f'コンパイル/準備失敗: {stem}.stderr');return rec

def compiler(requested=None,strict=True):
    for name in ([requested] if requested else ['clang-18','clang']):
        path=shutil.which(name or '')
        if not path:continue
        v=subprocess.check_output([path,'--version'],text=True,timeout=10).splitlines()[0]
        if not strict or re.search(r'clang version 18\.1\.3\b',v):return path,v
    raise GateError('Clang 18.1.3が必要です。自動インストールはしません。')
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

# The data layouts/generators above are reused from the pinned prior six-kernel
# adapter. The executable harness below is verification-only; it has no timer.
HARNESS=r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <fenv.h>
#include <xmmintrin.h>
#if __has_feature(address_sanitizer)
#include <sanitizer/asan_interface.h>
#define POISON(a,n) __asan_poison_memory_region((a),(n))
#define UNPOISON(a,n) __asan_unpoison_memory_region((a),(n))
#else
#define POISON(a,n) ((void)0)
#define UNPOISON(a,n) ((void)0)
#endif
_Static_assert(sizeof(double)==8 && DBL_MANT_DIG==53,"binary64 required");
_Static_assert(sizeof(int)==4,"int32 required");
void @FUNCTION@(@SIGNATURE@);
typedef struct {unsigned char *allocation,*data,*initial;size_t bytes;int width,ro;} Buffer;
static void fail(const char*s){fprintf(stderr,"%s\n",s);exit(4);}
static void add(Buffer*b,int*nb,size_t count,int width,int ro){
 Buffer*x=&b[(*nb)++];x->bytes=count*(size_t)width;x->width=width;x->ro=ro;
 x->allocation=malloc(x->bytes+128);x->initial=malloc(x->bytes);
 if(!x->allocation||!x->initial)fail("allocation_failed");
 memset(x->allocation,0xA5,x->bytes+128);x->data=x->allocation+64;
}
static int number(const char*s){char*end;long n=strtol(s,&end,10);if(!*s||*end||n<1||n>512)fail("bad_dimension");return(int)n;}
int main(int argc,char**argv){
 if(argc!=6)fail("usage: program p q r t input.bin");
 uint16_t endian=1;if(*(unsigned char*)&endian!=1)fail("little_endian_required");
 if(fesetround(FE_TONEAREST))fail("rounding_mode_failed");
 _mm_setcsr(_mm_getcsr()&~((1u<<15)|(1u<<6)));
 int p=number(argv[1]),q=number(argv[2]),r=number(argv[3]),t=number(argv[4]);
 @DIMCHECK@
 Buffer b[4]={0};int nb=0;@SETUP@
 FILE*f=fopen(argv[5],"rb");if(!f)fail("input_open_failed");
 for(int k=0;k<nb;k++){
  if(fread(b[k].initial,1,b[k].bytes,f)!=b[k].bytes)fail("short_input");
  memcpy(b[k].data,b[k].initial,b[k].bytes);
  POISON(b[k].allocation,64);POISON(b[k].data+b[k].bytes,64);
 }
 if(fgetc(f)!=EOF)fail("trailing_input");fclose(f);
 @CALL@
 for(int k=0;k<nb;k++){
  UNPOISON(b[k].allocation,64);UNPOISON(b[k].data+b[k].bytes,64);
  for(int j=0;j<64;j++)if(b[k].allocation[j]!=0xA5||b[k].data[b[k].bytes+j]!=0xA5)fail("guard_changed");
  if(b[k].ro&&memcmp(b[k].data,b[k].initial,b[k].bytes))fail("readonly_input_changed");
  if(b[k].width==8)for(size_t j=0;j<b[k].bytes;j+=8){double x;memcpy(&x,b[k].data+j,8);if(!isfinite(x))fail("nonfinite_output");}
 }
 for(int k=0;k<nb;k++)if(fwrite(b[k].data,1,b[k].bytes,stdout)!=b[k].bytes)fail("short_write");
 if(fflush(stdout))fail("flush_failed");
 for(int k=0;k<nb;k++){free(b[k].allocation);free(b[k].initial);}
 return 0;
}
'''

RO_TARGET={'gemm':'A[0][0]','atax':'A[0][0]','trisolv':'L[0][0]','nussinov':'seq[0]'}
GUARD_TARGET={'gemm':'C[ni-1][nj]','atax':'y[n]','jacobi-2d':'A[n-1][n]',
              'trisolv':'x[n]','nussinov':'table[n-1][n]','correlation':'corr[m-1][m]'}
SKIP_TARGET={'gemm':'C[ni-1][nj-1]','atax':'y[n-1]','jacobi-2d':'A[n-2][n-2]',
             'trisolv':'x[n-1]','nussinov':'table[0][n-1]','correlation':'corr[m-1][m-1]'}

def function_name(task):return 'kernel_'+task.replace('-','_')

def harness(task):
    s=HARNESS
    for k,v in {'FUNCTION':function_name(task),'SIGNATURE':WRAPPER_SIGS[task], 'SETUP':SETUP[task],
                'CALL':CALLS[task].replace('cpucond_kernel',function_name(task)),
                'DIMCHECK':'if(p<3)fail("n_ge_3_required");' if task=='jacobi-2d' else ''}.items():
        s=s.replace('@'+k+'@',v)
    need(not re.search(r'@[A-Z]+@',s),'テンプレート変数が残りました');return s

def mask(text):
    pat=r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pat,lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),text,flags=re.S)

def bounds(text,name):
    m=mask(text);hits=[]
    for match in re.finditer(r'\bvoid\s+'+re.escape(name)+r'\s*\(',m):
        p=m.index('(',match.start());depth=0
        for q in range(p,len(m)):
            depth+=(m[q]=='(');depth-=(m[q]==')')
            if depth==0:break
        q+=1
        while q<len(m) and m[q].isspace():q+=1
        if q==len(m) or m[q]!='{':continue
        opening=q;depth=0
        for end in range(q,len(m)):
            depth+=(m[end]=='{');depth-=(m[end]=='}')
            if depth==0:hits.append((opening,end));break
    need(len(hits)==1,'計算関数を一意に抽出できません: '+name);return hits[0]

def flip(target):
    # byte-wise, so this also exercises signed-zero and integer comparisons.
    return f'((unsigned char *)(void *)&({target}))[0] ^= 1u;'

def mutate(src,task,kind):
    a,b=bounds(src,function_name(task))
    if kind=='wrong_output':return src[:b]+'\n'+flip(SKIP_TARGET[task])+'\n'+src[b:]
    if kind=='readonly':return src[:b]+'\n'+flip(RO_TARGET[task])+'\n'+src[b:]
    if kind=='out_of_bounds':return src[:b]+'\n'+flip(GUARD_TARGET[task])+'\n'+src[b:]
    if kind=='skip_update':
        target=SKIP_TARGET[task]
        return (src[:a+1]+f'\n__typeof__({target}) cpucond_saved = {target};\n'+src[a+1:b]
                +f'\n{target} = cpucond_saved;\n'+src[b:])
    raise GateError('未知の負例: '+kind)

def profiles():
    san=['-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer']
    return [('C-generic','C',['-O3',*GENERIC]),('IR-generic','IR',['-O3',*GENERIC]),
            ('C-native','C',['-O3',*NATIVE]),('IR-native','IR',['-O3',*NATIVE]),
            ('C-sanitized','C',[*san,*GENERIC]),('IR-sanitized','IR',[*san,*GENERIC])]

def checked_data(task,c):
    data=input_blob(task,c);validate_blob(task,c,data);return data

def collect_contracts():
    d={}
    for task in TASKS:
        x=contract(task)
        # These facts describe the CURRENT limited suite, not a universal validator.
        x.update({'source_adapter_git_blob':ADAPTER_SOURCE_BLOB,
          'admitted_candidate_family':'unmodified C/IR and explicit generated negative controls for development',
          'test_cases':cases(task),'test_count':len(cases(task)),
          'measured_performance':False,'production_all_30_validator_complete':False,
          'arbitrary_C_or_IR_or_ASM_candidate_supported':False,
          'read_guard_detection':'ASan-poisoned redzones in sanitized builds; ordinary guards detect writes only',
          'readonly_contract':'post-call byte preservation; transient writes followed by restoration not detected',
          'uninitialized_read_detection':'not guaranteed; ASan/UBSan are not MemorySanitizer',
          'ir_ubsan_coverage':'not guaranteed for pre-existing IR; ASan address checks are explicitly enabled',
          'negative_fixture_id':'v1-dense'})
        for c in x['test_cases']:c['timing']=False
        d[task]=x
    return d

def prepare(repo,roundtrip,out=None):
    repo=Path(repo).resolve();rt=Path(roundtrip).resolve()
    need(rt.is_dir(),'Goal0062の結果フォルダーがありません')
    summary=load(rt/'summary.json');manifest=load(rt/'manifest.json');hashes=get_manifest(rt)
    need(summary.get('completion')=='CODEGEN_ROUNDTRIP_COMPLETE' and summary.get('instances_passed')==90,'90/90成功済み入力が必要です')
    tool=safe(rt,'tool-source.py');need(file_sha(tool)==ROUNDTRIP_TOOL_SHA,'Goal0062生成器が指定版と異なります')
    for rel in ('summary.json','manifest.json','tool-source.py'):
        p=safe(rt,rel);need(hashes.get(rel)==file_sha(p),'Goal0062記録のハッシュ不一致: '+rel)
    rows={(r['kernel'],r['size']):r for r in manifest['rows']}
    need(len(rows)==90,'入力一覧が90件ではありません')
    rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    dest=Path(out).resolve() if out else repo/'runs'/'goal0063-codegen-gate-prep'/rid
    dest.mkdir(parents=True,exist_ok=False);package=dest/'package';package.mkdir()
    write(package/'goal0063_codegen_gate.py',Path(__file__).read_bytes())
    items=[]
    for task in TASKS:
        for size in SIZES:
            row=rows[(task,size)];need(row.get('passed') is True,'Goal0062条件が不合格')
            item={'task':task,'size':size,'sources':{}}
            for form,key,ext in [('C','c_input','c'),('IR','ir_input','ll')]:
                rel=row[key];p=safe(rt,rel);data=p.read_bytes()
                need(hashes.get(rel)==digest(data),'検証済み入力のハッシュ不一致: '+rel)
                q=f'inputs/{task}/{size}/kernel.{ext}'
                write(package/q,data);item['sources'][form]={'path':q,'sha256':digest(data)}
            items.append(item)
    info={'package_id':rid,'revision':REVISION,'scope':'development_six_kernels_three_compiled_sizes',
          'final_main_dataset_unchanged':'30 kernels x 3 sizes', 'source_roundtrip':str(rt),
          'source_roundtrip_manifest_sha256':file_sha(rt/'manifest.json'),
          'tool_sha256':file_sha(package/'goal0063_codegen_gate.py'),'source_compiler':load(rt/'provenance.json')['compiler'],
          'contracts':collect_contracts(),'items':items,'model_requests':0,'performance_measurements':0}
    jwrite(package/'package.json',info);hash_directory(package)
    archive=dest/'cpucond-codegen-gate.tgz'
    with tarfile.open(archive,'w:gz') as tf:
        for p in sorted(package.rglob('*')):
            if p.is_file():tf.add(p,arcname=p.relative_to(package).as_posix(),recursive=False)
    h=file_sha(archive);write(dest/'cpucond-codegen-gate.tgz.sha256',h+'  cpucond-codegen-gate.tgz\n')
    receipt={'completion':'CODEGEN_GATE_PACKAGE_READY','package_directory':str(package),'archive':str(archive),
             'archive_sha256':h,'instances':len(items),'reference_inputs':2*len(items),'api_calls':0}
    jwrite(dest/'prepared.json',receipt)
    # A locator only. Never used as evidence without validating prepared.json.
    pointer=repo/'runs'/'goal0063-latest-package.txt';tmp=pointer.with_name(pointer.name+'.'+uuid.uuid4().hex)
    tmp.write_text(str(dest)+'\n',encoding='utf-8');os.replace(tmp,pointer)
    print('CODEGEN_GATE_PACKAGE_READY');print('開発用条件: 18（6課題×3サイズ）');print('入力: C/IR 合計36件')
    print('転送パッケージ:',archive);print('SHA-256:',h);return 0

def build_binary(clang,src,hpath,out,flags):
    out.mkdir(parents=True,exist_ok=False)
    f=[*COMMON,*flags]
    # Mark sanitizer attributes for re-read IR. Clang adds sanitizer passes only
    # to functions bearing the sanitizer attribute; this is not a safety proof.
    buildsrc=src
    if src.suffix=='.ll' and any('fsanitize=address' in x for x in flags):
        text=src.read_text();text,n=re.subn(r'^(define\s+[^\n]*)(\{)\s*$',r'\1 sanitize_address \2',text,flags=re.M)
        need(n==1,'IRのサニタイザー対象関数が一意でない')
        buildsrc=out/'sanitized-input.ll';write(buildsrc,text)
    must([clang,*f,'-c',buildsrc,'-o',out/'kernel.o'],out/'compile-kernel')
    must([clang,*f,'-c',hpath,'-o',out/'harness.o'],out/'compile-harness')
    must([clang,*f,out/'harness.o',out/'kernel.o','-lm','-o',out/'program'],out/'link')
    return out/'program'

def verify_one(clang,root,item,out):
    task=item['task'];size=item['size'];name=function_name(task)
    d=out/'cases'/task/size;d.mkdir(parents=True,exist_ok=False)
    csrc=safe(root,item['sources']['C']['path']);isrc=safe(root,item['sources']['IR']['path'])
    driver=d/'harness.c';write(driver,harness(task))
    data_cases=cases(task)
    inputs={}
    for c in data_cases:
        p=d/'test-inputs'/(c['case_id']+'.bin');write(p,checked_data(task,c));inputs[c['case_id']]=p
    reference=build_binary(clang,csrc,driver,d/'reference-O0',['-O0',*GENERIC])
    oracles={};tests=[]
    for c in data_cases:
        stem=d/'reference-results'/c['case_id'];rec=cmd([reference,c['p'],c['q'],c['r'],c['t'],inputs[c['case_id']]],stem,60)
        need(rec['state']=='ok','元コードが追加入力で実行失敗: '+str(stem))
        raw=stem.with_suffix('.stdout').read_bytes();inp=inputs[c['case_id']].read_bytes()
        validate_blob(task,c,raw)
        judge=compare_result(task,c,inp,raw,raw,'ok');need(judge['passed'],'元コードの読み取り専用/数値契約違反')
        oracles[c['case_id']]=raw
    for label,form,flags in profiles():
        exe=build_binary(clang,csrc if form=='C' else isrc,driver,d/'positive'/label,flags)
        for c in data_cases:
            stem=d/'positive-results'/label/c['case_id'];rec=cmd([exe,c['p'],c['q'],c['r'],c['t'],inputs[c['case_id']]],stem,60)
            raw=stem.with_suffix('.stdout').read_bytes()
            j=compare_result(task,c,inputs[c['case_id']].read_bytes(),oracles[c['case_id']],raw,rec['state'])
            tests.append({'profile':label,'case_id':c['case_id'],**j})
    negative=[]
    # Fixed 7x9x5 dense case. The 3-element Nussinov fixture can have
    # a legitimately unchanged final entry, so it cannot test skipped updates.
    # This negative-control fixture is fixed before any model output.
    c=data_cases[3]
    kinds=['wrong_output','skip_update','out_of_bounds']+(['readonly'] if task in RO_TARGET else [])
    for kind in kinds:
        negdir=d/'negative-sources'/kind;negdir.mkdir(parents=True,exist_ok=False)
        nsrc=negdir/'kernel.c';write(nsrc,mutate(csrc.read_text(),task,kind))
        nir=negdir/'kernel.ll'
        must([clang,*COMMON,*GENERIC,'-O0','-Xclang','-disable-O0-optnone','-S','-emit-llvm',nsrc,'-o',nir],negdir/'emit')
        for form,src in [('C',nsrc),('IR',nir)]:
            flags=['-O1','-fsanitize=address,undefined','-fno-sanitize-recover=all',*GENERIC] if kind=='out_of_bounds' else ['-O3',*GENERIC]
            exe=build_binary(clang,src,driver,d/'negative-build'/kind/form,flags)
            stem=d/'negative-results'/kind/form
            rec=cmd([exe,c['p'],c['q'],c['r'],c['t'],inputs[c['case_id']]],stem,60)
            raw=stem.with_suffix('.stdout').read_bytes();err=stem.with_suffix('.stderr').read_text(errors='replace')
            j=compare_result(task,c,inputs[c['case_id']].read_bytes(),oracles[c['case_id']],raw,rec['state'])
            expected_reason=('AddressSanitizer' in err or 'runtime error:' in err) if kind=='out_of_bounds' else (
                'readonly_input_changed' in err if kind=='readonly' else j.get('reason')=='value_mismatch')
            # Timeout, crash or compile error is NOT evidence of desired detection.
            rejected=not j['passed'] and rec['state']!='timeout' and expected_reason
            negative.append({'kind':kind,'representation':form,'detected_expected_failure':rejected,
                'comparison':j,'process_state':rec['state']})
    result={'task':task,'size':size,'positive_checks':len(tests),'positive_passed':sum(x['passed'] for x in tests),
       'negative_checks':len(negative),'negative_detected':sum(x['detected_expected_failure'] for x in negative),
       'all_passed':all(x['passed'] for x in tests) and all(x['detected_expected_failure'] for x in negative),
       'full_state_comparison':True,'formal_equivalence_proven':False,'api_calls':0,'performance_measurements':0,
       'positive_results':tests,'negative_results':negative}
    jwrite(d/'result.json',result)
    print(f'{task:16s} {size:6s} 未変更C/IR={result["positive_passed"]}/{len(tests)} 誤変換検出={result["negative_detected"]}/{len(negative)}',flush=True)
    return result

def host_record():
    d={'hostname':platform.node(),'platform':platform.platform(),'machine':platform.machine(),
       'affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None}
    cpu=Path('/proc/cpuinfo')
    if cpu.exists():
        m=re.search(r'^model name\s*:\s*(.*)$',cpu.read_text(),re.M);d['cpu_model']=m[1] if m else None
    return d

def execute(package,clang,version,jobs,expect_cpu=None,outdir=None):
    path=Path(package).resolve();root=path.parent;info=load(path)
    need(info['revision']==REVISION,'パッケージ版が異なります')
    need(info['tool_sha256']==file_sha(Path(__file__)),'実行スクリプトのハッシュが異なります')
    for rel,h in get_manifest(root).items():need(file_sha(safe(root,rel))==h,'パッケージのハッシュ不一致: '+rel)
    items=info['items'];need(len(items)==18 and {(x['task'],x['size']) for x in items}=={(t,s) for t in TASKS for s in SIZES},'6課題×3サイズの一覧が不正')
    for item in items:
        for spec in item['sources'].values():need(file_sha(safe(root,spec['path']))==spec['sha256'],'参照ソースのハッシュ不一致')
    host=host_record()
    if expect_cpu:need(expect_cpu in (host.get('cpu_model') or ''),'指定CPUと実機が違います: '+str(host.get('cpu_model')))
    need(platform.machine()=='x86_64' and sys.byteorder=='little','x86_64 little endian Linuxが必要です')
    rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'-'+uuid.uuid4().hex[:8]
    out=Path(outdir).resolve() if outdir else root/'results'/rid;out.mkdir(parents=True,exist_ok=False)
    write(out/'tool-source.py',Path(__file__).read_bytes());write(out/'package.json',path.read_bytes())
    jwrite(out/'provenance.json',{'host':host,'compiler':version,'compiler_sha256':file_sha(Path(clang)),
            'package_manifest_sha256':file_sha(path),'tool_sha256':file_sha(Path(__file__)),
            'executions_are_known_reference_and_controls_only':True,'parallel_jobs':jobs,
            'statistical_performance_use_prohibited':True})
    results=[];errors=[]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        work={pool.submit(verify_one,clang,root,x,out):x for x in items}
        for future in as_completed(work):
            x=work[future]
            try:results.append(future.result())
            except Exception as e:
                msg=f'{x["task"]}/{x["size"]}: {type(e).__name__}: {e}';errors.append(msg);print('停止対象:',msg,flush=True)
    passed=len(results)==18 and not errors and all(x['all_passed'] for x in results)
    summary={'completion':'CODEGEN_DEV_GATE_COMPLETE' if passed else 'CODEGEN_DEV_GATE_BLOCKED',
       'instances_planned':18,'instances_completed':len(results),'instances_passed':sum(x['all_passed'] for x in results),
       'positive_checks':sum(x['positive_checks'] for x in results),'positive_passed':sum(x['positive_passed'] for x in results),
       'negative_checks':sum(x['negative_checks'] for x in results),'negative_detected':sum(x['negative_detected'] for x in results),
       'errors':errors,'run_directory':str(out),'scope':'six development kernels x three source sizes',
       'final_30_kernel_validator_complete':False,'arbitrary_generated_code_execution_enabled':False,
       'formal_equivalence_proven':False,'api_calls':0,'performance_measurements':0}
    jwrite(out/'summary.json',summary);hash_directory(out)
    print('\n=== コード生成経路の多入力検証 ===');print(json.dumps(summary,ensure_ascii=False,indent=2));print(summary['completion'])
    return 0 if passed else 1

# Small independent program with gemm ABI; exercises checker behavior, not HPC performance.
SYNTHETIC=r'''
#include <stdint.h>
__attribute__((noinline)) void kernel_gemm(int ni,int nj,int nk,double alpha,double beta,double C[ni][nj],double A[ni][nk],double B[nk][nj]) {
for(int i=0;i<ni;i++)for(int j=0;j<nj;j++) { C[i][j]=beta*C[i][j]; for(int k=0;k<nk;k++)C[i][j]+=alpha*A[i][k]*B[k][j]; }
}
'''
class Tests(unittest.TestCase):
    def test_layout(self):self.assertEqual(layout('gemm',3,5,4)[0],('C','d',15,False))
    def test_dimensions(self):
        with self.assertRaises(ValueError):layout('gemm',0,5,4)
    def test_jacobi_dimension(self):
        with self.assertRaises(ValueError):layout('jacobi-2d',2,3,4)
    def test_input_determinism(self):
        for t in TASKS:
            for c in cases(t):self.assertEqual(checked_data(t,c),checked_data(t,c))
    def test_case_count(self):self.assertTrue(all(len(cases(t))==14 for t in TASKS))
    def test_fullstate_readonly(self):
        c=cases('gemm')[0];b=input_blob('gemm',c);x=bytearray(b);x[3*5*8]^=1
        self.assertEqual(compare_result('gemm',c,b,b,bytes(x),'ok')['reason'],'readonly_input_changed')
    def test_value_mismatch(self):
        c=cases('gemm')[0];b=input_blob('gemm',c);x=bytearray(b);x[0]^=1
        self.assertFalse(compare_result('gemm',c,b,b,bytes(x),'ok')['passed'])
    def test_short(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        self.assertFalse(compare_result('gemm',c,b,b,b[:-1],'ok')['passed'])
    def test_long(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        self.assertFalse(compare_result('gemm',c,b,b,b+b'x','ok')['passed'])
    def test_nonfinite(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        self.assertFalse(compare_result('gemm',c,b,b,struct.pack('<d',float('nan'))+b[8:],'ok')['passed'])
    def test_timeout_not_pass(self):
        c=cases('gemm')[0];b=input_blob('gemm',c)
        self.assertFalse(compare_result('gemm',c,b,b,b,'timeout')['passed'])
    def test_nonsingular_triangle(self):
        c=cases('trisolv')[0];a=struct.unpack('<9d',input_blob('trisolv',c)[:72])
        self.assertTrue(all(a[i*3+i]==2 for i in range(3)))
    def test_signed_zero(self):
        c=cases('gemm')[2];b=input_blob('gemm',c)
        self.assertNotEqual(b[:8],struct.pack('<d',0.0))
    def test_ro_map(self):self.assertEqual(set(RO_TARGET),{'gemm','atax','trisolv','nussinov'})
    def test_no_timer(self):self.assertNotIn('clock_gettime',harness('gemm'))
    def test_template(self):self.assertTrue(all('@' not in harness(t) for t in TASKS))
    def test_poisoned_guards(self):self.assertIn('POISON(b[k].data+b[k].bytes,64)',harness('gemm'))
    def test_json_duplicate(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'j';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(GateError):load(p)
    def test_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'f';write(p,b'x')
            with self.assertRaises(FileExistsError):write(p,b'y')
    def test_path(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(GateError):safe(Path(t),'../p')
    def test_duplicate_function(self):
        with self.assertRaises(GateError):bounds(SYNTHETIC+SYNTHETIC,'kernel_gemm')
    def test_mutants_compile_and_reject_c_ir(self):
        clang,v=compiler(strict=False)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);write(root/'kernel.c',SYNTHETIC)
            must([clang,*COMMON,*GENERIC,'-O0','-Xclang','-disable-O0-optnone','-S','-emit-llvm',root/'kernel.c','-o',root/'kernel.ll'],root/'emit')
            item={'task':'gemm','size':'MINI','sources':{'C':{'path':'kernel.c'},'IR':{'path':'kernel.ll'}}}
            result=verify_one(clang,root,item,root/'work');self.assertTrue(result['all_passed'],result)
            self.assertEqual(result['negative_detected'],8);self.assertEqual(result['positive_passed'],84)
    def test_reference_noop_reject(self):self.assertNotEqual(mutate(SYNTHETIC,'gemm','wrong_output'),SYNTHETIC)
    def test_scope_not_main(self):self.assertTrue(all(not d['production_all_30_validator_complete'] for d in collect_contracts().values()))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test',action='store_true');g.add_argument('--prepare',action='store_true');g.add_argument('--package',type=Path)
    ap.add_argument('--repo',type=Path,default=Path.cwd());ap.add_argument('--roundtrip',type=Path)
    ap.add_argument('--out',type=Path);ap.add_argument('--clang');ap.add_argument('--jobs',type=int,default=4)
    ap.add_argument('--expect-cpu')
    a=ap.parse_args()
    try:
        if a.self_test:
            r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
            return 0 if r.wasSuccessful() else 1
        if a.prepare:
            need(a.roundtrip is not None,'--roundtrip を指定してください');return prepare(a.repo,a.roundtrip,a.out)
        need(1<=a.jobs<=8,'同時実行数は1〜8です')
        clang,v=compiler(a.clang);return execute(a.package,clang,v,a.jobs,a.expect_cpu,a.out)
    except Exception as e:
        print('CODEGEN_DEV_GATE_BLOCKED:',type(e).__name__+': '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
