#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, contextlib, fcntl, hashlib, json, math, os, re, resource, shutil, signal, subprocess, sys, tarfile, tempfile, time, uuid
from pathlib import Path, PurePosixPath
from collections import Counter

REV='all30-custom-fullstate-revalidation-v1.1'
ORIGINAL_SCRIPT_SHA256='a2df1c7c196a231920824bccc91596c4544736721360e3cf5b95f7252b770b2c'
SIZES=('MINI','SMALL','MEDIUM')
EXPECTED_EVIDENCE_SHA='398c2af1dff04a390613f209fcdde99022ec251464a798742bc0cd2d4ec09c79'
PROFILES=('measured_native','generic','sanitized')
FORM_EXT={'C':'c','IR':'ll'}

# Two independent small valid-input cases per task. Values are runtime values, not size-category constants.
CASES={
'2mm':[{'ni':7,'nj':9,'nk':5,'nl':11,'alpha':1.5,'beta':1.2},{'ni':9,'nj':7,'nk':11,'nl':5,'alpha':-0.75,'beta':0.5}],
'3mm':[{'ni':7,'nj':9,'nk':5,'nl':11,'nm':6},{'ni':9,'nj':7,'nk':11,'nl':5,'nm':8}],
'adi':[{'tsteps':3,'n':9},{'tsteps':4,'n':11}],
'atax':[{'m':7,'n':9},{'m':9,'n':7}],
'bicg':[{'m':7,'n':9},{'m':9,'n':7}],
'cholesky':[{'n':9},{'n':11}],
'correlation':[{'m':7,'n':11,'float_n':11.0},{'m':9,'n':13,'float_n':13.0}],
'covariance':[{'m':7,'n':11,'float_n':11.0},{'m':9,'n':13,'float_n':13.0}],
'deriche':[{'w':9,'h':7,'alpha':0.25},{'w':11,'h':9,'alpha':0.375}],
'doitgen':[{'nr':5,'nq':7,'np':9},{'nr':7,'nq':5,'np':11}],
'durbin':[{'n':11},{'n':13}],
'fdtd-2d':[{'tmax':5,'nx':7,'ny':9},{'tmax':4,'nx':9,'ny':7}],
'floyd-warshall':[{'n':11},{'n':13}],
'gemm':[{'ni':7,'nj':9,'nk':5,'alpha':1.5,'beta':1.2},{'ni':9,'nj':7,'nk':11,'alpha':-0.75,'beta':0.5}],
'gemver':[{'n':11,'alpha':1.5,'beta':1.2},{'n':13,'alpha':-0.75,'beta':0.5}],
'gesummv':[{'n':11,'alpha':1.5,'beta':1.2},{'n':13,'alpha':-0.75,'beta':0.5}],
'gramschmidt':[{'m':13,'n':7},{'m':15,'n':9}],
'heat-3d':[{'tsteps':3,'n':9},{'tsteps':4,'n':11}],
'jacobi-1d':[{'tsteps':5,'n':17},{'tsteps':4,'n':19}],
'jacobi-2d':[{'tsteps':5,'n':9},{'tsteps':4,'n':11}],
'lu':[{'n':9},{'n':11}],
'ludcmp':[{'n':9},{'n':11}],
'mvt':[{'n':11},{'n':13}],
'nussinov':[{'n':11},{'n':13}],
'seidel-2d':[{'tsteps':5,'n':9},{'tsteps':4,'n':11}],
'symm':[{'m':7,'n':9,'alpha':1.5,'beta':1.2},{'m':9,'n':7,'alpha':-0.75,'beta':0.5}],
'syr2k':[{'n':7,'m':9,'alpha':1.5,'beta':1.2},{'n':9,'m':7,'alpha':-0.75,'beta':0.5}],
'syrk':[{'n':7,'m':9,'alpha':1.5,'beta':1.2},{'n':9,'m':7,'alpha':-0.75,'beta':0.5}],
'trisolv':[{'n':11},{'n':13}],
'trmm':[{'m':7,'n':9,'alpha':1.5},{'m':9,'n':7,'alpha':-0.75}],
}

READONLY={
'2mm':{'A','B','C'}, '3mm':{'A','B','C','D'}, 'adi':set(), 'atax':{'A','x'}, 'bicg':{'A','p','r'},
'cholesky':set(), 'correlation':set(), 'covariance':set(), 'deriche':{'imgIn'}, 'doitgen':{'C4'},
'durbin':{'r'}, 'fdtd-2d':{'_fict_'}, 'floyd-warshall':set(), 'gemm':{'A','B'},
'gemver':{'u1','v1','u2','v2','y','z'}, 'gesummv':{'A','B','x'}, 'gramschmidt':set(),
'heat-3d':set(), 'jacobi-1d':set(), 'jacobi-2d':set(), 'lu':set(), 'ludcmp':{'b'},
'mvt':{'y_1','y_2','A'}, 'nussinov':{'seq'}, 'seidel-2d':set(), 'symm':{'A','B'},
'syr2k':{'A','B'}, 'syrk':{'A'}, 'trisolv':{'L','b'}, 'trmm':{'A'},
}

class VError(RuntimeError): pass
class CandidateFailure(Exception): pass

def need(x,msg):
    if not x: raise VError(msg)
def sha_file(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def shab(b): return hashlib.sha256(b).hexdigest()
def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))
def jwrite(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(p)

def split_top(s,sep=','):
    out=[];start=0;depth=0
    pairs={'(':')','[':']','{':'}'}; opens=set(pairs); closes=set(pairs.values())
    for i,ch in enumerate(s):
        if ch in opens: depth+=1
        elif ch in closes: depth-=1
        elif ch==sep and depth==0: out.append(s[start:i].strip());start=i+1
    out.append(s[start:].strip());return out

def parse_kernel(src,task):
    fn='kernel_'+task.replace('-','_')
    m=re.search(r'(?:__attribute__\s*\(\(noinline\)\)\s+)?void\s+'+re.escape(fn)+r'\s*\((.*?)\)\s*\{',src,re.S)
    need(m is not None,'kernel signature not found: '+task)
    params=[]
    for raw in split_top(m.group(1)):
        raw=re.sub(r'\s+',' ',raw).strip(); dims=[x.strip() for x in re.findall(r'\[([^\]]+)\]',raw)]
        pre=re.sub(r'\[[^\]]+\]','',raw).strip(); parts=pre.split(); need(len(parts)>=2,'bad param '+raw)
        name=parts[-1];typ=' '.join(parts[:-1]);
        if typ=='base': typ='char'
        params.append({'raw':raw,'type':typ,'name':name,'dims':dims})
    return fn,params

def normalize_proto_param(p):
    raw=p['raw']
    if raw.startswith('base '): raw='char '+raw[len('base '):]
    return raw

def ir_signature(text,fn):
    m=re.search(r'^define\s+([^\n]*?)@'+re.escape(fn)+r'\s*\(',text,re.M)
    if not m: raise CandidateFailure('ir_missing_function')
    start=m.end()-1;depth=0;end=None
    for i in range(start,len(text)):
        c=text[i]
        if c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0: end=i;break
    if end is None: raise CandidateFailure('ir_bad_signature')
    prefix=m.group(1)
    cc='default'
    for token in ('fastcc','coldcc','cc 10','cc 11'):
        if token in prefix: cc=token
    params=[]
    for seg in split_top(text[start+1:end]):
        seg=seg.strip()
        if not seg: continue
        typ=seg.split()[0]
        params.append(typ)
    # all study kernels return void
    return {'cc':cc,'return':'void' if re.search(r'\bvoid\s*$',prefix) else prefix.split()[-1], 'params':params}

def mask_noncode(text):
    pat=r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pat,lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group(0)),text,flags=re.S)

def policy(source,form,fn):
    s=mask_noncode(source) if form=='C' else re.sub(r';[^\n]*','',source)
    forbidden=r'\b(?:system|popen|fork|vfork|execve|execvp|ptrace|syscall|dlopen|dlsym|fopen|freopen|printf|fprintf|fwrite|puts|socket|connect|clock_gettime|rdtsc|cpuid|fesetround|fesetenv|_mm_setcsr|__builtin_ia32_ldmxcsr|exit|_Exit|abort|fma|fmaf|fmal)\b'
    if re.search(forbidden,s): raise CandidateFailure('policy_forbidden_side_effect_or_intrinsic')
    if re.search(r'\b(?:asm|__asm__|__asm)\b|target-cpu|target-features|tune-cpu|llvm\.global_(?:ctors|dtors)|\bmain\s*\(',s): raise CandidateFailure('policy_hook_or_target_attribute')
    if form=='C':
        for line in s.splitlines():
            if line.lstrip().startswith('#include') and not re.fullmatch(r'\s*#\s*include\s*<(math|stdint|stddef|stdbool|float|limits)\.h>\s*',line):
                raise CandidateFailure('policy_include')
        if re.search(r'__attribute__\s*\(\([^)]*(constructor|destructor|alias|ifunc|section|target)',s): raise CandidateFailure('policy_attribute')
        if not re.search(r'\bvoid\s+'+re.escape(fn)+r'\s*\(',s): raise CandidateFailure('policy_missing_function')
    else:
        if re.search(r'\b(?:fadd|fsub|fmul|fdiv|frem|fcmp|call)\s+(?:fast|reassoc|nnan|ninf|nsz|arcp|contract|afn)\b',s): raise CandidateFailure('policy_relaxed_fp')
        if re.search(r'@llvm\.(?:fma|fmuladd|x86.*fmadd)',s): raise CandidateFailure('policy_fma')
        if not re.search(r'^define\b[^\n]*@'+re.escape(fn)+r'\(',s,re.M): raise CandidateFailure('policy_missing_function')

def scalar_literal(typ,val):
    if typ=='int': return str(int(val))
    if typ in ('double','float'):
        x=float(val); need(math.isfinite(x),'nonfinite scalar')
        return repr(x)+(('f') if typ=='float' else '')
    raise VError('unknown scalar '+typ)

def special_init(task,arrays,case_index):
    # Returns C statements applied after generic fill. Names exist as typed pointers.
    s=[]; seed=101+case_index*37
    if task=='cholesky':
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++) A[i][j]=(i==j)?(4.0+(double)i/64.0):(double)(((i+j+%d)%%7)+1)/512.0;'%seed)
    if task in ('lu','ludcmp'):
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++) A[i][j]=(i==j)?4.0:(double)(((i*7+j*3+%d)%%9)-4)/512.0;'%seed)
    if task=='trisolv':
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++) L[i][j]=(j>i)?0.0:((i==j)?2.0:(double)(((i*5+j*3+%d)%%7)-3)/512.0);'%seed)
    if task=='gramschmidt':
        s.append('for(int i=0;i<m;i++)for(int j=0;j<n;j++) A[i][j]=(i==j)?1.0:(double)(((i*11+j*5+%d)%%11)-5)/512.0;'%seed)
    if task=='correlation':
        s.append('for(int i=0;i<n;i++)for(int j=0;j<m;j++) data[i][j]=(double)(((i*i*7+j*11+i*j*3+%d)%%97)-48)/64.0;'%seed)
    if task=='durbin':
        s.append('for(int i=0;i<n;i++) r[i]=(double)(((i*5+%d)%%7)-3)/2048.0;'%seed)
    if task=='nussinov':
        s.append('for(int i=0;i<n;i++) seq[i]=(char)((i*3+%d)%%4);'%seed)
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++) table[i][j]=0;')
    if task=='symm':
        s.append('for(int i=0;i<m;i++)for(int j=0;j<m;j++) A[i][j]=(i==j)?1.0:(double)(((i+j+%d)%%9)-4)/128.0;'%seed)
    if task in ('syrk','syr2k'):
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++){ double z=(i==j)?1.0:(double)(((i+j+%d)%%9)-4)/128.0; C[i][j]=z; C[j][i]=z; }'%seed)
    if task=='trmm':
        s.append('for(int i=0;i<m;i++)for(int j=0;j<m;j++) A[i][j]=(j>i)?0.0:((i==j)?1.0:(double)(((i*5+j*3+%d)%%9)-4)/128.0);'%seed)
    if task=='floyd-warshall':
        s.append('for(int i=0;i<n;i++)for(int j=0;j<n;j++) path[i][j]=(i==j)?0:((((i*13+j*7+%d)%%11)==0)?999:1+((i*17+j*5+%d)%%23));'%(seed,seed))
    return '\n'.join(s)

HARNESS_HEAD=r'''#define _GNU_SOURCE
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fenv.h>
#include <xmmintrin.h>
#if __has_feature(address_sanitizer)
#include <sanitizer/asan_interface.h>
#define ASAN_POISON(a,n) __asan_poison_memory_region((a),(n))
#define ASAN_UNPOISON(a,n) __asan_unpoison_memory_region((a),(n))
#else
#define ASAN_POISON(a,n) ((void)0)
#define ASAN_UNPOISON(a,n) ((void)0)
#endif

typedef struct { unsigned char *region,*data; size_t bytes,usable,total; int ro; } GB;
static size_t PG;
static void die(const char*s){fprintf(stderr,"%s\n",s);_Exit(90);}
static GB gb_make(size_t bytes,int ro){
 if(!bytes)die("zero_bytes"); if(!PG)PG=(size_t)sysconf(_SC_PAGESIZE);
 size_t usable=(bytes+PG-1)/PG*PG; size_t total=usable+2*PG;
 unsigned char *r=mmap(NULL,total,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); if(r==MAP_FAILED)die("mmap_failed");
 unsigned char *d=r+PG; if(mprotect(d,usable,PROT_READ|PROT_WRITE))die("mprotect_rw_failed");
 memset(d,0xA5,usable); GB g={r,d,bytes,usable,total,ro}; return g;
}
static void gb_seal(GB*g){ if(g->usable>g->bytes) ASAN_POISON(g->data+g->bytes,g->usable-g->bytes); if(g->ro && mprotect(g->data,g->usable,PROT_READ))die("mprotect_ro_failed"); }
static void gb_unseal(GB*g){ if(g->ro && mprotect(g->data,g->usable,PROT_READ|PROT_WRITE))die("mprotect_unseal_failed"); if(g->usable>g->bytes) ASAN_UNPOISON(g->data+g->bytes,g->usable-g->bytes); }
static void gb_check(GB*g){ for(size_t i=g->bytes;i<g->usable;i++) if(g->data[i]!=0xA5)die("padding_changed"); }
static double dv(size_t i,unsigned seed,int mode){ uint64_t x=(uint64_t)i*6364136223846793005ULL+(uint64_t)seed*1442695040888963407ULL; if(mode==0){int v=(int)((x>>17)%97)-48;return (double)v/128.0;} switch((i+seed)%8){case 0:return 0.25;case 1:return -0.25;case 2:return 0x1p-40;case 3:return -0x1p-40;case 4:return 0.0;case 5:return -0.0;case 6:return 0.125;default:return -0.375;} }
static float fv(size_t i,unsigned seed,int mode){ return (float)dv(i,seed,mode); }
'''

def harness_source(task,params,case,index):
    fn='kernel_'+task.replace('-','_')
    proto=', '.join(normalize_proto_param(p) for p in params)
    lines=[HARNESS_HEAD, f'void {fn}({proto});\n', 'int main(void){', 'if(fesetround(FE_TONEAREST)) die("rounding");', '_mm_setcsr(_mm_getcsr()&~((1u<<15)|(1u<<6)));']
    # scalars
    for p in params:
        if not p['dims']:
            need(p['name'] in case,'missing scalar '+task+':'+p['name'])
            lines.append(f"{p['type']} {p['name']} = {scalar_literal(p['type'],case[p['name']])};")
    arrays=[]
    seed=101+index*37
    for ai,p in enumerate(params):
        if not p['dims']: continue
        name=p['name'];typ=p['type'];dims=p['dims']; count=' * '.join(f'((size_t)({d}))' for d in dims)
        ro=1 if name in READONLY[task] else 0
        lines.append(f'size_t count_{name} = {count};')
        lines.append(f'GB buf_{name}=gb_make(count_{name}*sizeof({typ}),{ro});')
        if len(dims)==1:
            lines.append(f'{typ} *{name}=({typ}*)buf_{name}.data;')
        else:
            suffix=''.join(f'[{d}]' for d in dims[1:])
            lines.append(f'{typ} (*{name}){suffix}=({typ} (*){suffix})buf_{name}.data;')
        # generic initialization
        if typ=='double': lines.append(f'for(size_t z=0;z<count_{name};z++) ((double*)buf_{name}.data)[z]=dv(z,{seed+ai*13},{index});')
        elif typ=='float': lines.append(f'for(size_t z=0;z<count_{name};z++) ((float*)buf_{name}.data)[z]=fv(z,{seed+ai*13},{index});')
        elif typ=='int': lines.append(f'for(size_t z=0;z<count_{name};z++) ((int*)buf_{name}.data)[z]=(int)(1+((z*17u+{seed+ai*13}u)%29u));')
        elif typ in ('char','base'): lines.append(f'for(size_t z=0;z<count_{name};z++) ((unsigned char*)buf_{name}.data)[z]=(unsigned char)((z+{seed+ai*13})%4u);')
        else: raise VError('unsupported array type '+typ)
        arrays.append(name)
    sp=special_init(task,arrays,index)
    if sp: lines.append(sp)
    for name in arrays: lines.append(f'gb_seal(&buf_{name});')
    args=', '.join(p['name'] for p in params)
    lines.append(f'{fn}({args});')
    for name in arrays: lines.append(f'gb_unseal(&buf_{name}); gb_check(&buf_{name});')
    for name in arrays: lines.append(f'if(fwrite(buf_{name}.data,1,buf_{name}.bytes,stdout)!=buf_{name}.bytes) die("write_failed");')
    lines.append('if(fflush(stdout)) die("flush_failed"); return 0; }')
    return '\n'.join(lines)+'\n'

def safe_tar_write(ti,tf,dest,max_bytes=32*1024*1024):
    need(ti.isfile() and not ti.issym() and not ti.islnk(),'unsafe tar member '+ti.name)
    need(ti.size<=max_bytes,'oversize '+ti.name)
    f=tf.extractfile(ti);need(f is not None,'extract fail '+ti.name)
    data=f.read(max_bytes+1);need(len(data)==ti.size,'read mismatch '+ti.name)
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return data

def safe_extract_selected(archive,out):
    """Recover frozen sources per (kernel, source-size), and candidate objects.

    Do not reuse MINI for other sizes: e.g. heat-3d contains 20/40/100
    literal time-step counts in the actual source supplied to the model.
    No module inside the archive is imported or executed.
    """
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=[]; seen_original=set(); old_object_by_key={}; original_hashes={}
    roots={'P0':'evidence/originals/cpucond-batch-en-20260912T074659-7093-resource-v2-unsent',
           'P1':'evidence/originals/cpucond-p012-zen2-v1/P1','P2':'evidence/originals/cpucond-p012-zen2-v1/P2'}
    source_pat=re.compile(r'^(.*?)/results/generation/([^/]+)/candidate\.(c|ll)$')
    object_pat=re.compile(r'^(.*?)/results/validation/([^/]+)/native-kernel-result\.o$')
    original_pat=re.compile(r'^(.*?)/work/inputs/([^/]+)/(MINI|SMALL|MEDIUM)/kernel\.(c|ll)$')
    seen_members=set()
    with tarfile.open(archive,'r:gz') as tf:
        for ti in tf:
            n=ti.name
            pp=PurePosixPath(n)
            need(not pp.is_absolute() and '..' not in pp.parts,'unsafe archive path')
            m=original_pat.match(n)
            if m and m.group(1) in roots.values():
                root,task,size,ext=m.groups();need(task in CASES,'unknown original kernel')
                key=(task,size,ext)
                need(n not in seen_members,'duplicate original archive member');seen_members.add(n)
                need(ti.isfile() and not ti.issym() and not ti.islnk(),'unsafe original')
                need(0<ti.size<=32*1024*1024,'original size')
                f=tf.extractfile(ti);need(f is not None,'missing original')
                data=f.read();need(len(data)==ti.size,'short original')
                digest=shab(data)
                if key in original_hashes:
                    need(original_hashes[key]==digest,'original differs between conditions: '+str(key))
                else:
                    original_hashes[key]=digest
                    dest=out/'originals'/task/size/f'kernel.{ext}'
                    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                seen_original.add(key)
                continue
            m=source_pat.match(n)
            if m:
                cond=next((c for c,r in roots.items() if m.group(1)==r),None)
                if cond:
                    tid,ext=m.group(2),m.group(3)
                    need(re.fullmatch(r'[A-Za-z0-9_-]+',tid),'bad candidate ID')
                    parts=tid.split('__');need(len(parts)==5,'bad task tuple')
                    task,size,form,c,sample=parts
                    need(task in CASES and size in SIZES and c==cond and sample=='s0','bad candidate tuple')
                    need(form in FORM_EXT and FORM_EXT[form]==ext,'candidate form mismatch')
                    dest=out/'candidates'/cond/tid/f'candidate.{ext}'
                    need(not dest.exists(),'duplicate candidate')
                    data=safe_tar_write(ti,tf,dest)
                    rows.append({'condition':cond,'id':tid,'task':task,'size':size,'form':form,
                                 'source':str(dest),'old_native_object':None,'source_sha256':shab(data)})
                    continue
            m=object_pat.match(n)
            if m:
                cond=next((c for c,r in roots.items() if m.group(1)==r),None)
                if cond:
                    tid=m.group(2);need(re.fullmatch(r'[A-Za-z0-9_-]+',tid),'bad object ID')
                    need((cond,tid) not in old_object_by_key,'duplicate object')
                    dest=out/'candidates'/cond/tid/'old-native.o'
                    safe_tar_write(ti,tf,dest);old_object_by_key[(cond,tid)]=str(dest)
    expected={(t,s,e) for t in CASES for s in SIZES for e in ('c','ll')}
    need(seen_original==expected,'expected 180 original C/IR files for 30 x 3 sizes')
    rows.sort(key=lambda x:(x['condition'],x['task'],x['size'],x['form']))
    need(len(rows)==525,f'expected 525 saved candidates, got {len(rows)}')
    need(Counter(r['condition'] for r in rows)=={'P0':166,'P1':180,'P2':179},'condition counts')
    seen_ids=set()
    for row in rows:
        key=(row['condition'],row['id']);need(key not in seen_ids,'duplicate candidate '+str(key));seen_ids.add(key)
        row['old_native_object']=old_object_by_key.get(key)
        row['reference_key']=[row['task'],row['size']]
        row['reference_c_sha256']=original_hashes[(row['task'],row['size'],'c')]
        row['reference_ir_sha256']=original_hashes[(row['task'],row['size'],'ll')]
    need(len(old_object_by_key)==371,'expected 371 frozen native objects')
    return rows

# --- sandbox runner: root-only on the rented host; every candidate executes as nobody in bwrap/net namespace ---
DROP='"""Trusted launcher text, executed inside bwrap before the compiler/candidate.\nNot a standalone host administrator tool; it only reduces process privileges.\n"""\nimport ctypes\nimport json\nimport os\nimport sys\n\nstage = \'initial\'\nlibc = ctypes.CDLL(None, use_errno=True)\n\nclass Header(ctypes.Structure):\n    _fields_ = [(\'version\', ctypes.c_uint32), (\'pid\', ctypes.c_int)]\n\nclass Data(ctypes.Structure):\n    _fields_ = [(\'effective\', ctypes.c_uint32), (\'permitted\', ctypes.c_uint32),\n                (\'inheritable\', ctypes.c_uint32)]\n\nlibc.capset.argtypes = [ctypes.POINTER(Header), ctypes.POINTER(Data)]\nlibc.capset.restype = ctypes.c_int\nlibc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,\n                       ctypes.c_ulong, ctypes.c_ulong]\nlibc.prctl.restype = ctypes.c_int\n\n\ndef snapshot():\n    with open(\'/proc/self/status\', encoding=\'ascii\') as f:\n        st = dict(line.rstrip().split(\':\', 1) for line in f if \':\' in line)\n    return {\'uid\': list(os.getresuid()), \'gid\': list(os.getresgid()),\n            \'groups\': os.getgroups(), \'capabilities\': {\n                k: int(st[k].strip(), 16)\n                for k in (\'CapEff\', \'CapPrm\', \'CapInh\', \'CapAmb\', \'CapBnd\')},\n            \'no_new_privs\': int(st[\'NoNewPrivs\'].strip())}\n\n\ndef checked(rc, op):\n    if rc != 0:\n        err = ctypes.get_errno()\n        raise OSError(err, op + \': \' + os.strerror(err))\n\ntry:\n    if len(sys.argv) < 2:\n        raise RuntimeError(\'missing trusted executable\')\n    before = snapshot()\n    stage = \'no_new_privs\'\n    checked(libc.prctl(38, 1, 0, 0, 0), \'PR_SET_NO_NEW_PRIVS\')\n    stage = \'drop_supplementary_groups\'\n    os.setgroups([])\n    stage = \'drop_gids\'\n    os.setresgid(65534, 65534, 65534)\n    stage = \'drop_uids\'\n    os.setresuid(65534, 65534, 65534)\n    after_uid = snapshot()\n    # UID changes do not clear the inheritable capability set. Clear it\n    # explicitly together with the permitted/effective sets. No extra caps added.\n    stage = \'clear_capability_sets\'\n    header = Header(0x20080522, 0)  # Linux capability ABI v3, current thread\n    zero = (Data * 2)()\n    checked(libc.capset(ctypes.byref(header), zero), \'capset(empty)\')\n    stage = \'clear_ambient_capabilities\'\n    checked(libc.prctl(47, 4, 0, 0, 0), \'PR_CAP_AMBIENT_CLEAR_ALL\')\n    stage = \'verify_dropped_privileges\'\n    after = snapshot()\n    checks = {\n        \'all_uids_65534\': after[\'uid\'] == [65534] * 3,\n        \'all_gids_65534\': after[\'gid\'] == [65534] * 3,\n        \'no_supplementary_groups\': after[\'groups\'] == [],\n        \'cap_eff_prm_inh_amb_zero\': all(after[\'capabilities\'][k] == 0\n             for k in (\'CapEff\', \'CapPrm\', \'CapInh\', \'CapAmb\')),\n        \'no_new_privs\': after[\'no_new_privs\'] == 1,\n    }\n    failed = [k for k, v in checks.items() if not v]\n    if failed:\n        raise RuntimeError(\'failed privilege checks: \' + \', \'.join(failed))\n    if any(\'__CPUCOND_PREFLIGHT_V2__\' in x for x in sys.argv[1:]):\n        print(\'SANDBOX_PRIVILEGE_DIAGNOSTIC \' + json.dumps({\n            \'before\': before, \'after_uid_change\': after_uid,\n            \'after_explicit_clear\': after, \'checks\': checks}, sort_keys=True),\n            file=sys.stderr, flush=True)\n    stage = \'exec_unprivileged\'\n    import resource\n    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))\n    resource.setrlimit(resource.RLIMIT_FSIZE, (67108864, 67108864))\n    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))\n    os.execv(sys.argv[1], sys.argv[1:])\nexcept Exception as exc:\n    try:\n        current = snapshot()\n    except Exception:\n        current = None\n    print(\'SANDBOX_LAUNCHER_FAILED \' + json.dumps({\n        \'stage\': stage, \'error\': type(exc).__name__ + \': \' + str(exc),\n        \'current\': current}, sort_keys=True), file=sys.stderr, flush=True)\n    sys.exit(125)\n'
SANDBOX_PROBE="# __CPUCOND_PREFLIGHT_V2__\n# HOST_NAMESPACES is supplied by the trusted parent as a literal mapping.\nimport json\nimport os\nimport socket\nimport sys\nimport tempfile\n\nchecks = {}\nevidence = {}\nerrors = {}\n\ndef test(name, fn):\n    try:\n        value = fn()\n        checks[name] = value is True\n        if value is not True:\n            errors[name] = repr(value)\n    except Exception as exc:\n        checks[name] = False\n        errors[name] = type(exc).__name__ + ': ' + str(exc)\n\ntry:\n    with open('/proc/self/status', encoding='ascii') as f:\n        status = dict(line.rstrip().split(':', 1) for line in f if ':' in line)\n    evidence['capabilities'] = {k: int(status[k].strip(), 16)\n       for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb', 'CapBnd')}\n    evidence['uid'] = list(os.getresuid())\n    evidence['gid'] = list(os.getresgid())\n    evidence['groups'] = os.getgroups()\n    evidence['no_new_privs'] = int(status['NoNewPrivs'].strip())\n    evidence['namespaces'] = {k: os.readlink('/proc/self/ns/' + k)\n       for k in ('net', 'pid', 'mnt', 'ipc', 'uts')}\n    evidence['network_interfaces'] = [name for _, name in socket.if_nameindex()]\n    evidence['cwd'] = os.getcwd()\n    evidence['cpu_affinity'] = sorted(os.sched_getaffinity(0))\n    test('all_uids_65534', lambda: evidence['uid'] == [65534] * 3)\n    test('all_gids_65534', lambda: evidence['gid'] == [65534] * 3)\n    test('no_supplementary_groups', lambda: evidence['groups'] == [])\n    test('cap_eff_prm_inh_amb_zero', lambda: all(evidence['capabilities'][k] == 0\n        for k in ('CapEff', 'CapPrm', 'CapInh', 'CapAmb')))\n    test('no_new_privs', lambda: evidence['no_new_privs'] == 1)\n    test('root_directory_absent', lambda: not os.path.lexists('/root'))\n    test('model_store_absent', lambda: not os.path.lexists('/var/lib/cpucond-infer'))\n    test('working_directory_tmp', lambda: evidence['cwd'] == '/tmp')\n    test('cpu_affinity_2', lambda: evidence['cpu_affinity'] == [2])\n    for name in ('net', 'pid', 'mnt', 'ipc', 'uts'):\n        test(name + '_namespace_separate', lambda n=name:\n             evidence['namespaces'][n] != HOST_NAMESPACES[n])\n    test('no_host_network_interface', lambda: set(evidence['network_interfaces']) <= {'lo'})\n    def writable_tmp():\n        with tempfile.TemporaryFile(dir='/tmp') as f:\n            f.write(b'test')\n        return True\n    def writable_scratch():\n        with open('/out/write-probe', 'xb') as f:\n            f.write(b'CPUCOND_SCRATCH_OK\\n')\n        return True\n    def readonly_usr():\n        path = '/usr/.cpucond-readonly-probe-' + str(os.getpid())\n        try:\n            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)\n        except OSError as exc:\n            return exc.errno in (13, 30, 1)\n        else:\n            os.close(fd)\n            os.unlink(path)\n            return False\n    test('tmp_writable', writable_tmp)\n    test('scratch_writable', writable_scratch)\n    test('usr_not_writable', readonly_usr)\nexcept Exception as exc:\n    checks['probe_completed'] = False\n    errors['probe_completed'] = type(exc).__name__ + ': ' + str(exc)\n\nresult = {'checks': checks, 'failed_checks': [k for k, v in checks.items() if not v],\n          'evidence': evidence, 'errors': errors}\nprint(json.dumps(result, sort_keys=True), flush=True)\nsys.exit(0 if checks and all(checks.values()) else 125)\n"

class Sandbox:
    def __init__(self,root,cpu=24,node=1):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.cpu=cpu;self.node=node;self.n=0
        need(os.geteuid()==0,'run mode requires root for isolated bwrap')
        need(shutil.which('bwrap') is not None,'bwrap missing');need(shutil.which('numactl') is not None,'numactl missing')
    def call(self,argv,inputs,stem,timeout=120,outputs=()):
        self.n+=1;stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
        scratch=self.root/f'scratch-{self.n}-{uuid.uuid4().hex[:8]}' if outputs else None
        if scratch:
            scratch.mkdir(mode=0o700);os.chown(scratch,65534,65534)
        a=['numactl',f'--physcpubind={self.cpu}',f'--membind={self.node}','bwrap','--die-with-parent','--new-session','--unshare-pid','--unshare-net','--unshare-ipc','--unshare-uts','--cap-drop','ALL','--cap-add','CAP_SETUID','--cap-add','CAP_SETGID','--clearenv','--setenv','PATH','/usr/bin:/bin','--setenv','LC_ALL','C','--setenv','HOME','/tmp','--setenv','TMPDIR','/tmp','--setenv','ASAN_OPTIONS','detect_leaks=0:halt_on_error=1','--setenv','UBSAN_OPTIONS','halt_on_error=1:print_stacktrace=1','--ro-bind','/usr','/usr']
        for p in ('/lib','/lib64','/bin','/sbin'):
            if Path(p).exists():a+=['--ro-bind',p,p]
        a+=['--proc','/proc','--dev','/dev','--perms','1777','--tmpfs','/tmp','--dir','/in','--dir','/out','--dir','/etc']
        for f in ('/etc/ld.so.cache','/etc/ld.so.conf'):
            if Path(f).is_file():a+=['--ro-bind',f,f]
        for name,p in inputs.items():
            need(re.fullmatch(r'[A-Za-z0-9_.-]+',name) is not None,'bad input name');p=Path(p);need(p.is_file() and not p.is_symlink(),'bad sandbox file')
            a+=['--ro-bind',str(p.resolve()),'/in/'+name]
        if scratch:a+=['--bind',str(scratch.resolve()),'/out']
        a+=['--chdir','/tmp','--','/usr/bin/python3','-I','-S','-c',DROP,*map(str,argv)]
        so=stem.with_suffix('.stdout');se=stem.with_suffix('.stderr')
        with so.open('wb') as fo,se.open('wb') as fe:
            p=subprocess.Popen(a,stdout=fo,stderr=fe,stdin=subprocess.DEVNULL,start_new_session=True)
            try:rc=p.wait(timeout=timeout);state='ok' if rc==0 else 'exit_nonzero'
            except subprocess.TimeoutExpired:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait();rc=None;state='timeout'
        out={}
        if state=='ok' and scratch:
            for name in outputs:
                q=scratch/name
                if not q.is_file() or q.is_symlink():state='invalid_output';break
                dest=stem.parent/(stem.name+'-'+name);dest.write_bytes(q.read_bytes());
                if name=='program':os.chmod(dest,0o755)
                out[name]=dest
        if scratch:shutil.rmtree(scratch,ignore_errors=True)
        if rc == 125 or b'SANDBOX_LAUNCHER_FAILED' in se.read_bytes():
            raise VError('sandbox launcher failed; see '+str(se))
        rec={'argv':list(map(str,argv)),'state':state,'returncode':rc,'cpu':self.cpu,'node':self.node,'network_isolated':True,'host_uid':65534,'timeout_s':timeout}
        jwrite(stem.with_suffix('.command.json'),rec);return rec,so.read_bytes(),out

def clang18():
    for name in ('clang-18','clang'):
        p=shutil.which(name)
        if not p:continue
        line=subprocess.check_output([p,'--version'],text=True).splitlines()[0]
        if re.search(r'clang version 18\.1\.3\b',line):return p,line
    raise VError('Clang 18.1.3 required')

def compile_obj(box,clang,src,stem,flags,form,proto=None):
    inputs={'source.'+FORM_EXT[form]:src};argv=[clang]
    if form=='C':
        argv+=['-std=gnu11']
        if proto:
            inputs['prototype.h']=proto;argv+=['-include','/in/prototype.h']
    argv+=['-fno-fast-math','-ffp-contract=off','-fno-lto',*flags,'-c','/in/source.'+FORM_EXT[form],'-o','/out/result.o']
    rec,_,out=box.call(argv,inputs,stem,180,('result.o',));return rec,out.get('result.o')

def compile_harness(box,clang,src,stem,sanitized=False):
    flags=['-std=gnu11','-fno-fast-math','-ffp-contract=off','-fno-lto','-O1' if sanitized else '-O0','--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic']
    if sanitized:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
    return compile_obj(box,clang,src,stem,flags,'C')[1]

def link_prog(box,clang,objs,stem,sanitized=False):
    inputs={f'o{i}.o':p for i,p in enumerate(objs)};argv=[clang,*[f'/in/o{i}.o' for i in range(len(objs))],'-lm']
    if sanitized:argv+=['-fsanitize=address,undefined']
    argv+=['-o','/out/program'];rec,_,out=box.call(argv,inputs,stem,120,('program',));return rec,out.get('program')

def run_prog(box,program,stem,timeout=120):
    rec,raw,_=box.call(['/in/program'],{'program':program},stem,timeout);return rec,raw

def prototype_file(path,fn,params):
    proto='void '+fn+'('+', '.join(normalize_proto_param(p) for p in params)+');\n';Path(path).write_text(proto,encoding='utf-8')

def native_case_baselines(box,clang,work,task,original_c,params):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    out={}; fn='kernel_'+task.replace('-','_');proto=work/'prototype.h';prototype_file(proto,fn,params)
    for ci,case in enumerate(CASES[task]):
        cd=work/f'case{ci}';cd.mkdir(parents=True,exist_ok=True)
        hs=cd/'harness.c';hs.write_text(harness_source(task,params,case,ci),encoding='utf-8')
        # O0 oracle
        ko_rec,ko=compile_obj(box,clang,original_c,cd/'ref-o0',['-O0','--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic'],'C',proto)
        need(ko_rec['state']=='ok' and ko,'reference O0 compile failed '+task)
        ho=compile_harness(box,clang,hs,cd/'harness-o0',False);need(ho,'harness compile failed '+task)
        lr,exe=link_prog(box,clang,[ho,ko],cd/'ref-link');need(lr['state']=='ok' and exe,'ref link fail')
        rr,oracle=run_prog(box,exe,cd/'ref-run');need(rr['state']=='ok' and oracle,'ref run fail '+task)
        # native baseline must match oracle
        kn_rec,kn=compile_obj(box,clang,original_c,cd/'base-native',['-O3','--target=x86_64-unknown-linux-gnu','-march=native'],'C',proto)
        need(kn_rec['state']=='ok' and kn,'baseline native compile fail')
        lr,bexe=link_prog(box,clang,[ho,kn],cd/'base-link');need(lr['state']=='ok' and bexe,'base link fail')
        br,braw=run_prog(box,bexe,cd/'base-run');need(br['state']=='ok' and braw==oracle,'baseline native differs from O0: '+task)
        out[ci]={'harness':hs,'oracle':oracle,'prototype':proto}
    return out

def candidate_revalidate(box,clang,row,original_c,original_ir,params,base,out):
    d=Path(out);d.mkdir(parents=True,exist_ok=True);fn='kernel_'+row['task'].replace('-','_');src=Path(row['source']);form=row['form']
    result={'reference_c_sha256':sha_file(original_c),'reference_ir_sha256':sha_file(original_ir),'id':row['id'],'condition':row['condition'],'task':row['task'],'size':row['size'],'form':form,'source_sha256':row['source_sha256'],'old_native_object':row['old_native_object'],'status':'pending','profiles':{},'cases':[],'passed':False,'errors':[]}
    try:
        source=src.read_text(encoding='utf-8');policy(source,form,fn)
        proto=Path(base[0]['prototype'])
        if form=='C':
            rec,_,_=box.call([clang,'-std=gnu11','-fsyntax-only','-include','/in/prototype.h','/in/source.c'],{'prototype.h':proto,'source.c':src},d/'abi',120)
            if rec['state']!='ok': raise CandidateFailure('c_abi_incompatible')
        else:
            orig=Path(original_ir).read_text(encoding='utf-8')
            if ir_signature(source,fn)!=ir_signature(orig,fn): raise CandidateFailure('ir_signature_changed')
        fresh={}
        for label,flags,san in [
            ('generic',['-O3','--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic'],False),
            ('native',['-O3','--target=x86_64-unknown-linux-gnu','-march=native'],False),
            ('sanitized',['-O1','--target=x86_64-unknown-linux-gnu','-march=x86-64','-mtune=generic','-fsanitize=address,undefined','-fno-sanitize-recover=all'],True),
        ]:
            rec,obj=compile_obj(box,clang,src,d/(label+'-compile'),flags,form,proto if form=='C' else None)
            if rec['state']!='ok' or obj is None:
                result['profiles'][label]={'compile_state':rec['state'],'passed':False};fresh[label]=None;continue
            result['profiles'][label]={'compile_state':'ok','object_sha256':sha_file(obj),'passed':True};fresh[label]=obj
        old=Path(row['old_native_object']) if row['old_native_object'] else None
        if old and old.is_file() and fresh.get('native'):
            result['old_native_sha256']=sha_file(old);result['fresh_native_matches_old']=sha_file(old)==sha_file(fresh['native'])
        # Exact previously measured native object when available, otherwise fresh native.
        measured_obj=old if old and old.is_file() else fresh.get('native')
        all_pass=True
        for ci in sorted(base):
            cbase=base[ci];oracle=cbase['oracle'];hs=Path(cbase['harness']);cr={'case':ci,'profiles':{}}
            for label,obj,san in [('measured_native',measured_obj,False),('generic',fresh.get('generic'),False),('sanitized',fresh.get('sanitized'),True)]:
                if obj is None:
                    cr['profiles'][label]={'passed':False,'reason':'compile_failed'};all_pass=False;continue
                ho=compile_harness(box,clang,hs,d/f'case{ci}-{label}-harness',san); 
                if not ho: raise VError('trusted harness compilation failed: '+str(d))
                lr,exe=link_prog(box,clang,[ho,obj],d/f'case{ci}-{label}-link',san)
                if lr['state']!='ok' or not exe: cr['profiles'][label]={'passed':False,'reason':'link_failed'};all_pass=False;continue
                rr,raw=run_prog(box,exe,d/f'case{ci}-{label}-run',180)
                passed=rr['state']=='ok' and raw==oracle
                cr['profiles'][label]={'passed':passed,'state':rr['state'],'stdout_sha256':shab(raw),'oracle_sha256':shab(oracle),'bytes':len(raw)}
                all_pass &= passed
            result['cases'].append(cr)
        result['passed']=bool(all_pass);result['status']='checked'
    except CandidateFailure as e:
        result['status']='rejected';result['errors'].append(str(e))
    except Exception as e:
        result['status']='validator_error';result['errors'].append(type(e).__name__+': '+str(e))
        jwrite(d/'result.json',result)
        raise VError('validator error, not candidate failure: '+str(d)+': '+str(e)) from e
    jwrite(d/'result.json',result);return result

def sandbox_preflight(box,clang,work):
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    host={k:os.readlink('/proc/self/ns/'+k) for k in ('net','pid','mnt','ipc','uts')}
    probe=SANDBOX_PROBE.replace("evidence['cpu_affinity'] == [2]",f"evidence['cpu_affinity'] == [{box.cpu}]")
    probe="HOST_NAMESPACES = "+repr(host)+"\n"+probe
    rec,raw,files=box.call(['/usr/bin/python3','-I','-S','-c',probe],{},work/'isolation',30,('write-probe',))
    try: data=json.loads(raw)
    except Exception: raise VError('preflight has no readable report; see '+str(work))
    jwrite(work/'isolation-report.json',data)
    need(rec['state']=='ok' and data.get('checks') and all(x is True for x in data['checks'].values()),
         'sandbox preflight failed; see '+str(work))
    print('REVALIDATION_SANDBOX_OK',flush=True)
    source=work/'trusted-probe.c'
    source.write_text('#include <stdio.h>\nint main(void){puts("REVALIDATION_COMPILER_OK");return 0;}\n')
    for san in (False,True):
        tag='sanitized' if san else 'plain'
        flags=['-O1','-march=x86-64']
        if san:flags+=['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        rec,obj=compile_obj(box,clang,source,work/('probe-'+tag),flags,'C')
        need(rec['state']=='ok' and obj,'preflight compiler failed: '+tag)
        rec,exe=link_prog(box,clang,[obj],work/('link-'+tag),san)
        need(rec['state']=='ok' and exe,'preflight linker failed: '+tag)
        rec,output=run_prog(box,exe,work/('exec-'+tag))
        need(rec['state']=='ok' and output==b'REVALIDATION_COMPILER_OK\n','preflight execution failed: '+tag)
    print('REVALIDATION_COMPILER_OK',flush=True)


def run_all(args):
    archive=Path(args.evidence).resolve();need(sha_file(archive)==EXPECTED_EVIDENCE_SHA,'evidence SHA mismatch')
    clang,ver=clang18();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    state={'revision':REV,'completion':'RUNNING','phase':'preflight','candidates_completed':0,'baselines_completed':0,
           'evidence_sha256':EXPECTED_EVIDENCE_SHA,'clang':ver,'script_sha256':sha_file(__file__),
           'model_calls':0,'performance_measurements':0,'old_labels_modified':False}
    def progress():
        state['updated_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        jwrite(out/'progress.json',state)
    try:
        progress()
        box=Sandbox(out/'sandbox',args.cpu,args.node)
        sandbox_preflight(box,clang,out/'preflight')
        state['phase']='evidence_extract';progress()
        extracted=out/'extracted';rows=safe_extract_selected(archive,extracted)
        jwrite(out/'candidate-inventory.json',rows)
        originals={};baselines={};state['phase']='original_baselines';progress()
        for task in sorted(CASES):
            for size in SIZES:
                key=(task,size)
                oc=extracted/'originals'/task/size/'kernel.c'
                oi=extracted/'originals'/task/size/'kernel.ll'
                fn,params=parse_kernel(oc.read_text(),task)
                originals[key]=(oc,oi,params)
                baselines[key]=native_case_baselines(box,clang,out/'baselines'/task/size,task,oc,params)
                state['baselines_completed']+=1;progress()
                print('baseline',task,size,'2 cases OK',flush=True)
        state['phase']='candidate_revalidation';progress();results=[]
        for i,row in enumerate(rows,1):
            key=(row['task'],row['size']);oc,oi,params=originals[key]
            r=candidate_revalidate(box,clang,row,oc,oi,params,baselines[key],out/'results'/row['condition']/row['id'])
            results.append(r);state['candidates_completed']=i
            state['candidate_passed']=sum(x['passed'] for x in results);progress()
            if i%10==0 or not r['passed']:print(f'{i}/{len(rows)} {row["id"]} -> {r["status"]} pass={r["passed"]}',flush=True)
        summary={'completion':'ALL30_REVALIDATION_COMPLETE','revision':REV,'evidence_sha256':EXPECTED_EVIDENCE_SHA,
                 'clang':ver,'saved_candidates':len(results),'passed':sum(r['passed'] for r in results),
                 'failed':sum(not r['passed'] for r in results),'validator_errors':0,
                 'reference_kernel_size_pairs':len(baselines),'reference_test_cases':2*len(baselines),
                 'by_condition':{},'by_form':{},'formal_equivalence_proven':False,'test_cases_per_kernel_source_size':2,
                 'profiles':['measured_native','generic','sanitized'],
                 'model_calls':0,'performance_measurements':0,'old_labels_modified':False,
                 'scope':'Two custom runtime cases for each original source-size; exact all-array final-state comparison; finite dynamic validation, not proof.'}
        for c in ('P0','P1','P2'):
            rr=[r for r in results if r['condition']==c];summary['by_condition'][c]={'saved':len(rr),'passed':sum(r['passed'] for r in rr)}
        for f in ('C','IR'):
            rr=[r for r in results if r['form']==f];summary['by_form'][f]={'saved':len(rr),'passed':sum(r['passed'] for r in rr)}
        jwrite(out/'summary.json',summary);state['phase']='complete';state['completion']='ALL30_REVALIDATION_COMPLETE';progress()
        print(json.dumps(summary,ensure_ascii=False,indent=2));print('ALL30_REVALIDATION_COMPLETE',flush=True)
    except BaseException as exc:
        state['completion']='ALL30_REVALIDATION_BLOCKED';state['error']=type(exc).__name__+': '+str(exc)
        progress();jwrite(out/'failure.json',state)
        print('ALL30_REVALIDATION_BLOCKED: '+state['error'],file=sys.stderr,flush=True)
        raise

def self_test():
    import unittest
    class T(unittest.TestCase):
        def test_counts(self): self.assertEqual(len(CASES),30); self.assertTrue(all(len(v)==2 for v in CASES.values()))
        def test_readonly(self): self.assertEqual(set(CASES),set(READONLY))
        def test_split(self): self.assertEqual(split_top('int a, double x[n][m], int z'),['int a','double x[n][m]','int z'])
        def test_ir_sig(self):
            x='define dso_local void @k(i32 noundef %n, ptr noundef %A) #0 {\nret void\n}'
            self.assertEqual(ir_signature(x,'k')['params'],['i32','ptr'])
        def test_policy_bad(self):
            with self.assertRaises(CandidateFailure):policy('void k(void){system("x");}','C','k')
        def test_harness(self):
            src='__attribute__((noinline)) void kernel_gemm(int ni,int nj,int nk,double alpha,double beta,double C[ni][nj],double A[ni][nk],double B[nk][nj]){C[0][0]+=A[0][0]*B[0][0];}'
            _,p=parse_kernel(src,'gemm');h=harness_source('gemm',p,CASES['gemm'][0],0);self.assertIn('kernel_gemm(',h);self.assertIn('mprotect',h)
        def test_c_abi_text(self):
            src='void kernel_floyd_warshall(int n,int path[n+0][n+0]){}';_,p=parse_kernel(src,'floyd-warshall');self.assertIn('n+0',p[1]['raw'].replace(' ',''))
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T);r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():raise SystemExit(1)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--evidence');ap.add_argument('--out');ap.add_argument('--cpu',type=int,default=24);ap.add_argument('--node',type=int,default=1);a=ap.parse_args()
    if a.self_test:self_test();return
    need(a.evidence and a.out,'--evidence and --out required')
    need(os.geteuid()==0,'run mode requires sandbox setup privileges')
    with open('/run/lock/cpucond-revalidation079.lock','a') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise VError('another revalidation is running')
        run_all(a)
if __name__=='__main__': main()
