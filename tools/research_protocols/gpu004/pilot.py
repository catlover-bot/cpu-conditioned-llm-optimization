#!/usr/bin/env python3
"""GPU Code Pilot 001: 3 CUDA kernels x 5 hardware-prompt arms, A40 only.
No connection to the retired CPU server. NVRTC compiles device code only;
a trusted host runner verifies bitwise results and measures CUDA event times.
Generated host code, arbitrary includes, inline PTX and host execution are refused.
This is a purpose-built pipeline pilot, NOT PolyBench/ACC, Rodinia or KernelBench.
"""
from __future__ import annotations

# PUBLIC ARCHIVAL COPY. Source hashes are recorded in publication-provenance.json.
# Only operational instance fields and dependency loading differ from the source.
# Offline analysis needs no allocation, provider account, CUDA build or GPU.
import importlib.util as _public_importlib
from pathlib import Path as _PublicPath
_public_path = _PublicPath(__file__).resolve().parent.parent / 'gpu004' / '_public.py'
_public_spec = _public_importlib.spec_from_file_location('_cpucond_public_dependencies', _public_path)
_public = _public_importlib.module_from_spec(_public_spec)
_public_spec.loader.exec_module(_public)
import argparse
import base64
import contextlib
import csv
import datetime as dt
import fcntl
import gzip
import hashlib
import http.client
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import re
import resource
import shlex
import shutil
import signal
import socket
import stat
import statistics
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import traceback
import types
import unittest
from unittest import mock
import uuid

VERSION='gpu-code-pilot-001-v1'
ROOT=Path('/workspace/gpu-code-pilot-001-v1')
LOCAL_REL=Path('workspace/cpu-conditioned-llm-optimization/runs/gpu-code-pilot-001-v1')
SERVER='root@example.invalid'
SSH_PORT = 22
HOST_FP='SHA256:REPLACE_WITH_VERIFIED_HOST_KEY'
POD='PUBLIC_ALLOCATION_ID'
EXPECTED_GPU='GPU-REPLACE-WITH-VERIFIED-UUID'
A_SHA = 'a08d409b9ef2b30583042df80a3d31004d417f1febd235fdc5c46f48fbbc93c9'
MODEL='qwen2.5-coder:14b-instruct-q4_K_M'
ARMS=('P0','S1','S2','W1','W2')
PORT=11568
MAX_GENERATIONS=15
CAP=4096
REQUEST_SECONDS=600
RUN_SECONDS=6*3600
ACK_SECONDS=3600
GIB=1024**3
WORK_DEADLINE=None
# An acknowledgement is checked after generation and evaluation checkpoints.
# While the local computer is disconnected, the worker waits without more generation.
class Blocked(RuntimeError):pass

def need(ok,msg):
    if not ok:raise Blocked(msg)

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canon(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()
def parse(raw):
    def pairs(items):
        d={}
        for k,v in items:
            need(k not in d,'Duplicate JSON key');d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(Blocked('Nonfinite JSON')))
def safe(p):
    p=Path(p).absolute();need('..' not in p.parts,'Path traversal')
    for x in (p,*p.parents):need(not x.is_symlink(),'Symlink refused: '+str(x))
    return p

def read(p,limit=64*1024**2):
    p=safe(p)
    with p.open('rb') as f:
        s=os.fstat(f.fileno());need(stat.S_ISREG(s.st_mode) and s.st_size<=limit,'Nonregular/oversized file')
        b=f.read(limit+1);e=os.fstat(f.fileno())
    need(len(b)==s.st_size and (s.st_ino,s.st_mtime_ns,s.st_size)==(e.st_ino,e.st_mtime_ns,e.st_size),'File changed')
    return b

def hfile(p):
    p=safe(p);h=hashlib.sha256()
    with p.open('rb') as f:
        st=os.fstat(f.fileno());need(stat.S_ISREG(st.st_mode),'Nonregular file')
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
        en=os.fstat(f.fileno())
    need((st.st_ino,st.st_size,st.st_mtime_ns)==(en.st_ino,en.st_size,en.st_mtime_ns),'File changed while hashing')
    return h.hexdigest()

def save(p,b):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def jw(p,o):save(p,canon(o))
def atomic(p,o):
    p=safe(p);tmp=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex);save(tmp,canon(o));os.replace(tmp,p)
def module_a():
    return _public.load_module('assets.py', A_SHA)

def clean_env():
    return {'PATH':'/usr/local/cuda-12.8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'HOME':'/tmp','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1',
            'CUDA_VISIBLE_DEVICES':EXPECTED_GPU,'CUDA_CACHE_DISABLE':'1',
            'CUDA_MODULE_LOADING':'EAGER','OMP_NUM_THREADS':'4'}

def cgroup_start(pid):
    try:
        v=Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()
        return None if v[0]=='Z' else v[19]
    except (OSError,IndexError):return None

def alive(rec):return isinstance(rec.get('pid'),int) and rec.get('ticks') is not None and cgroup_start(rec['pid'])==rec['ticks']
def close_child(proc):
    if proc is None:return
    if proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=15)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=15)

@contextlib.contextmanager
def lock(path):
    p=safe(path);p.parent.mkdir(exist_ok=True,parents=True)
    fd=os.open(p,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'r+') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);yield

STATE={};STATE_LOCK=threading.Lock()
def update(**kw):
    with STATE_LOCK:
        STATE.update(kw,updated_utc=now());atomic(ROOT/'progress.json',STATE)
    if 'phase' in kw:print('GPU001_PHASE='+kw['phase'],flush=True)

def command(argv,log,timeout=180,env=None):
    log=safe(log);log.parent.mkdir(parents=True,exist_ok=True)
    if WORK_DEADLINE is not None:
        need(time.monotonic()<WORK_DEADLINE,'Pilot total wall budget reached')
        timeout=min(timeout,max(0.1,WORK_DEADLINE-time.monotonic()))
    p=None
    try:
        with log.open('xb') as f:
            p=subprocess.Popen([str(x) for x in argv],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                env=env or clean_env(),cwd=ROOT,start_new_session=True)
            try:return p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:close_child(p);return 124
    finally:
        if p is not None and p.poll() is None:close_child(p)

A_EMBED = _public.encoded_module('assets.py')

# CUDA numerics and restricted device-only compilation for GPU Code Pilot 001.
import array
import ctypes as ct
import ctypes.util
import math
import os
from pathlib import Path
import re
import struct
import time

SIGNATURE = 'extern "C" __global__ void kernel(const float* A, const float* B, float* C, int M, int N, int K)'
BODIES = {
'axpy': '''{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < M * N) C[i] = __fadd_rn(__fmul_rn(1.25f, A[i]), B[i]);
}''',
'transpose': '''{
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < M && col < N) C[col * M + row] = A[row * N + col];
}''',
'gemm_ordered': '''{
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < M && col < N) {
        float sum = 0.0f;
        for (int k = 0; k < K; ++k)
            sum = __fadd_rn(sum, __fmul_rn(A[row * K + k], B[k * N + col]));
        C[row * N + col] = sum;
    }
}'''}
SOURCES = {k:SIGNATURE+'\n'+v+'\n' for k,v in BODIES.items()}
TASKS = tuple(SOURCES)
SMALL_SHAPES = [(1,1,1),(1,17,7),(15,17,13),(17,33,7),(31,29,19),(32,32,32)]
PERF_SHAPES = {'axpy':[(1,1048576,1),(1,4194304,1)],
               'transpose':[(1024,1024,1),(1025,2049,1)],
               'gemm_ordered':[(128,192,129),(256,256,255)]}
TASK_INDEX = {t:i for i,t in enumerate(TASKS)}
NVRTC_OPTIONS = ['--gpu-architecture=sm_86','--std=c++17','--fmad=false','--ftz=false',
                 '--prec-div=true','--prec-sqrt=true','--restrict','--generate-line-info',
                 '--device-stack-protector=true']
ALLOWED_CALLS = {'if','for','while','switch','sizeof','int','float','unsigned','min','max',
                 '__fadd_rn','__fmul_rn','__fsub_rn','__syncthreads','__syncwarp',
                 '__shfl_sync','__shfl_up_sync','__shfl_down_sync','__shfl_xor_sync'}
SPECIAL_IDENT = {'__shared__','__restrict__','__syncthreads','__syncwarp',
                 '__fadd_rn','__fmul_rn','__fsub_rn','__shfl_sync',
                 '__shfl_up_sync','__shfl_down_sync','__shfl_xor_sync'}
BAN = {'asm','__asm','__asm__','extern','namespace','class','struct','typedef','using',
       'template','new','delete','printf','malloc','free','volatile','reinterpret_cast',
       'const_cast','static_cast','dynamic_cast','double','half','__half','atomicAdd',
       '__global__','__device__','__host__','throw','try','catch','goto','do'}

def strip_comments(s):
    # Disallow escaped-newline/trigraph/preprocessor ambiguities before parsing.
    require(isinstance(s,str) and s.isascii() and len(s)<=32768,'Non-ASCII/oversized CUDA source')
    require('\\' not in s and '#' not in s and '??' not in s,'Preprocessor/escape syntax is outside pilot policy')
    # Quotes are only legal in the fixed extern-C signature. Comments need no strings.
    return re.sub(r'/\*.*?\*/|//[^\n]*',' ',s,flags=re.S)

def source_policy(source):
    clean=strip_comments(source)
    stoks=re.findall(r'[A-Za-z_]\w*|\d+|[^\s]',SIGNATURE)
    toks=re.findall(r'[A-Za-z_]\w*|\d+|[^\s]',clean)
    require(toks[:len(stoks)]==stoks,'Fixed kernel signature is required')
    body=toks[len(stoks):]
    require(body and body[0]=='{' and body[-1]=='}','Exactly one kernel body required')
    depth=0
    for i,x in enumerate(body):
        if x=='{':depth+=1
        if x=='}':depth-=1
        require(depth>=0 and (depth>0 or i==len(body)-1),'Code outside kernel body')
        require(x not in ('"',"'",'@','`','$'),'Strings/character literals not allowed in kernel body')
        if re.fullmatch(r'[A-Za-z_]\w*',x):
            require(x not in BAN and not x.startswith(('cuda','cuBLAS','cooperative_groups','wmma')),
                    'Unsupported device-only construct: '+x)
            require(not x.startswith('__') or x in SPECIAL_IDENT,'Unknown intrinsic/reserved identifier: '+x)
            if i+1<len(body) and body[i+1]=='(':
                require(x in ALLOWED_CALLS,'Unknown callable: '+x)
    require(depth==0,'Unbalanced braces')
    require('<<<' not in clean and '>>>' not in clean,'Dynamic kernel launches forbidden')
    require(')(' not in re.sub(r'\s+','',clean),'Indirect call syntax forbidden')
    require('(*' not in re.sub(r'\s+','',clean),'Function pointer/declarator syntax forbidden')
    return source

def normalize_source(text):
    require(isinstance(text,str) and text.strip(),'Empty model output')
    text=text.strip()
    if text.startswith('```'):
        m=re.fullmatch(r'```(?:cuda|cpp|c\+\+|c)?\s*\n(.*?)\n```',text,re.S|re.I)
        require(m is not None and '```' not in m[1],'Invalid outer Markdown fence')
        text=m[1].strip()
    require('```' not in text,'Multiple/unbalanced code fences')
    return source_policy(text+'\n')

class NumericFailure(Exception): pass

def require(ok,msg):
    if not ok: raise NumericFailure(msg)

def bind(lib,name,args,ret=ct.c_int):
    fn=getattr(lib,name);fn.argtypes=args;fn.restype=ret;return fn

def nvrtc_compile(source,root):
    source_policy(source)
    candidates=[Path('/usr/local/cuda-12.8/lib64/libnvrtc.so'),Path('/usr/local/cuda/lib64/libnvrtc.so')]
    # Test environment may provide an explicit library without touching user systems.
    if os.environ.get('GPU001_TEST_NVRTC'): candidates.insert(0,Path(os.environ['GPU001_TEST_NVRTC']))
    p=next((p.resolve() for p in candidates if p.exists()),None)
    require(p is not None,'NVRTC library missing')
    lib=ct.CDLL(str(p));V=ct.c_void_p;S=ct.c_size_t;B=ct.c_char_p
    create=bind(lib,'nvrtcCreateProgram',[ct.POINTER(V),B,B,ct.c_int,ct.POINTER(B),ct.POINTER(B)])
    comp=bind(lib,'nvrtcCompileProgram',[V,ct.c_int,ct.POINTER(B)])
    destroy=bind(lib,'nvrtcDestroyProgram',[ct.POINTER(V)])
    ver=bind(lib,'nvrtcVersion',[ct.POINTER(ct.c_int),ct.POINTER(ct.c_int)])
    a,b=ct.c_int(),ct.c_int();require(ver(ct.byref(a),ct.byref(b))==0,'nvrtcVersion failed')
    require((a.value,b.value)==(12,8),'This pilot requires NVRTC 12.8')
    prog=V();require(create(ct.byref(prog),source.encode(),b'kernel.cu',0,None,None)==0,'nvrtcCreateProgram failed')
    root=Path(root)
    def data(kind):
        size=S();f=bind(lib,'nvrtcGet'+kind+'Size',[V,ct.POINTER(S)])
        rc=f(prog,ct.byref(size));require(rc==0,'NVRTC '+kind+' size failed: '+str(rc))
        require(0<size.value<=32*1024**2,'NVRTC output size out of range')
        buf=ct.create_string_buffer(size.value);f=bind(lib,'nvrtcGet'+kind,[V,V])
        require(f(prog,buf)==0,'NVRTC '+kind+' retrieval failed');return buf.raw
    try:
        opts=(B*len(NVRTC_OPTIONS))(*(x.encode() for x in NVRTC_OPTIONS))
        rc=comp(prog,len(opts),opts)
        log=data('ProgramLog').rstrip(b'\0');(root/'compile.log').write_bytes(log)
        require(rc==0,'NVRTC_COMPILE_FAILED; see compile.log')
        ptx=data('PTX').rstrip(b'\0');cubin=data('CUBIN')
        require(b'.entry kernel(' in ptx or re.search(rb'\.entry\s+kernel\s*\(',ptx),'Expected kernel entry missing')
        (root/'kernel.ptx').write_bytes(ptx);(root/'kernel.cubin').write_bytes(cubin)
        return {'nvrtc_version':[a.value,b.value],'options':NVRTC_OPTIONS,'nvrtc_library':str(p),'ptx_bytes':len(ptx),'cubin_bytes':len(cubin)}
    finally:destroy(ct.byref(prog))

# Minimal trusted host helper. No candidate host code is compiled or called.
# CUDA Driver functions are resolved from the globally loaded driver library.
HELPER_CPP = r'''
#include <cstdint>
#include <cstring>
#include <cmath>
#include <cfenv>
#include <dlfcn.h>
#if defined(__x86_64__)
#include <xmmintrin.h>
#endif
static void fp_mode() {
    std::fesetround(FE_TONEAREST);
#if defined(__x86_64__)
    _mm_setcsr(_mm_getcsr() & ~(unsigned((1u<<15)|(1u<<6))));
#endif
}
static float mul(float a,float b){volatile float r=a*b;return r;}
static float add(float a,float b){volatile float r=a+b;return r;}
extern "C" void make_data(float *a,int n,uint32_t seed,int transpose) {
    fp_mode();uint32_t x=seed?seed:1;
    const uint32_t special[]={0,0x80000000,1,0x80000001,0x007fffff,0x00800000,
        0x80800000,0x3f800001,0xbf800001,0x3f7fffff,0x33800000,0xb3800000};
    for(int i=0;i<n;++i){x^=x<<13;x^=x>>17;x^=x<<5;
        uint32_t bits=(x&0x807fffffu) | (uint32_t(120+(x%8))<<23);
        if(i%13==0)bits=special[(i/13+seed)%12];
        if(transpose && i%37==0)bits=x; // transpose copies all bit patterns.
        std::memcpy(a+i,&bits,4);
    }
}
extern "C" void reference(int task,const float*a,const float*b,float*c,int M,int N,int K){
    fp_mode();
    if(task==0){for(int i=0;i<M*N;++i)c[i]=add(mul(1.25f,a[i]),b[i]);}
    else if(task==1){for(int i=0;i<M;++i)for(int j=0;j<N;++j)std::memcpy(c+j*M+i,a+i*N+j,4);}
    else {for(int i=0;i<M;++i)for(int j=0;j<N;++j){float v=0.0f;
        for(int k=0;k<K;++k)v=add(v,mul(a[i*K+k],b[k*N+j]));c[i*N+j]=v;}}
}
extern "C" int cuda_batch(void*func,uint64_t A,uint64_t B,uint64_t C,int M,int N,int K,
                        unsigned gx,unsigned gy,unsigned bx,unsigned by,int count,void*start,void*stop,float*out) {
    using Launch=int(*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**);
    using Record=int(*)(void*,void*);using Sync=int(*)(void*);using Elapsed=int(*)(float*,void*,void*);
    auto launch=(Launch)dlsym(RTLD_DEFAULT,"cuLaunchKernel");
    auto record=(Record)dlsym(RTLD_DEFAULT,"cuEventRecord");
    auto sync=(Sync)dlsym(RTLD_DEFAULT,"cuEventSynchronize");
    auto elapsed=(Elapsed)dlsym(RTLD_DEFAULT,"cuEventElapsedTime");
    if(!launch||!record||!sync||!elapsed)return -999;
    void*params[]={&A,&B,&C,&M,&N,&K};int rc=record(start,nullptr);if(rc)return rc;
    for(int i=0;i<count;++i){rc=launch(func,gx,gy,1,bx,by,1,0,nullptr,params,nullptr);if(rc)return rc;}
    if((rc=record(stop,nullptr)))return rc;if((rc=sync(stop)))return rc;
    return elapsed(out,start,stop);
}
'''

class Helper:
    def __init__(self,path):
        self.lib=ct.CDLL(str(path));V=ct.c_void_p;I=ct.c_int;U=ct.c_uint;Q=ct.c_uint64
        self.gen=bind(self.lib,'make_data',[V,I,U,I],None)
        self.ref=bind(self.lib,'reference',[I,V,V,V,I,I,I],None)
        self.batch=bind(self.lib,'cuda_batch',[V,Q,Q,Q,I,I,I,U,U,U,U,I,V,V,ct.POINTER(ct.c_float)])
    def case(self,task,shape,seed):
        M,N,K=shape;na=M*K if task=='gemm_ordered' else M*N;nb=K*N if task=='gemm_ordered' else M*N
        a=(ct.c_float*na)();b=(ct.c_float*nb)();c=(ct.c_float*(M*N))()
        self.gen(a,na,seed,int(task=='transpose'));self.gen(b,nb,seed+19,0)
        self.ref(TASK_INDEX[task],a,b,c,M,N,K)
        return a,b,c

class CUDA:
    def __init__(self):
        self.lib=ct.CDLL('libcuda.so.1',mode=ct.RTLD_GLOBAL);L=self.lib
        I=ct.c_int;U=ct.c_uint;Q=ct.c_uint64;V=ct.c_void_p;S=ct.c_size_t
        self.f={}
        specs={
        'cuInit':[U], 'cuDeviceGet':[ct.POINTER(I),I],
        'cuDeviceGetName':[V,I,I], 'cuDeviceComputeCapability':[ct.POINTER(I),ct.POINTER(I),I],
        'cuDeviceTotalMem_v2':[ct.POINTER(S),I], 'cuDeviceGetAttribute':[ct.POINTER(I),I,I],
        'cuCtxCreate_v2':[ct.POINTER(V),U,I], 'cuCtxDestroy_v2':[V], 'cuCtxSynchronize':[],
        'cuModuleLoadData':[ct.POINTER(V),V], 'cuModuleUnload':[V],
        'cuModuleGetFunction':[ct.POINTER(V),V,ct.c_char_p],
        'cuMemAlloc_v2':[ct.POINTER(Q),S], 'cuMemFree_v2':[Q],
        'cuMemcpyHtoD_v2':[Q,V,S], 'cuMemcpyDtoH_v2':[V,Q,S],
        'cuLaunchKernel':[V,U,U,U,U,U,U,U,V,ct.POINTER(V),ct.POINTER(V)],
        'cuEventCreate':[ct.POINTER(V),U], 'cuEventDestroy_v2':[V],
        }
        for n,args in specs.items():self.f[n]=bind(L,n,args)
        self.ck('cuInit',0);dev=I();self.ck('cuDeviceGet',ct.byref(dev),0);self.dev=dev.value
        name=ct.create_string_buffer(256);self.ck('cuDeviceGetName',name,256,self.dev)
        major,minor=I(),I();self.ck('cuDeviceComputeCapability',ct.byref(major),ct.byref(minor),self.dev)
        mem=S();self.ck('cuDeviceTotalMem_v2',ct.byref(mem),self.dev)
        self.info={'name':name.value.decode(),'compute_capability':[major.value,minor.value],'memory_bytes':mem.value}
        for n,num in [('max_threads_per_block',1),('static_shared_memory_per_block',8),('warp_size',10),
                      ('registers_per_block',12),('multiprocessors',16),('l2_bytes',38),
                      ('max_threads_per_multiprocessor',39),('shared_memory_per_multiprocessor',81)]:
            val=I();self.ck('cuDeviceGetAttribute',ct.byref(val),num,self.dev);self.info[n]=val.value
        require(self.info['name']=='NVIDIA A40' and [major.value,minor.value]==[8,6],'Unexpected evaluation GPU')
        self.ctx=V();self.ck('cuCtxCreate_v2',ct.byref(self.ctx),0,self.dev)
        self.allocs=[];self.mods=[];self.events=[]
    def ck(self,n,*args):
        rc=self.f[n](*args)
        require(rc==0,'CUDA_DRIVER_ERROR '+n+' '+str(rc))
    def module(self,path):
        raw=Path(path).read_bytes();buf=ct.create_string_buffer(raw);mod=ct.c_void_p();fn=ct.c_void_p()
        self.ck('cuModuleLoadData',ct.byref(mod),buf);self.mods.append(mod)
        self.ck('cuModuleGetFunction',ct.byref(fn),mod,b'kernel');return fn
    def buffer(self,nbytes):
        ptr=ct.c_uint64();self.ck('cuMemAlloc_v2',ct.byref(ptr),nbytes);self.allocs.append(ptr.value);return ptr.value
    def put(self,ptr,raw):
        buf=ct.create_string_buffer(raw);self.ck('cuMemcpyHtoD_v2',ptr,buf,len(raw))
    def get(self,ptr,n):
        buf=ct.create_string_buffer(n);self.ck('cuMemcpyDtoH_v2',buf,ptr,n);return buf.raw
    def event(self):
        e=ct.c_void_p();self.ck('cuEventCreate',ct.byref(e),0);self.events.append(e);return e
    def launch(self,fn,ptrs,shape,task):
        M,N,K=shape;gx,gy,bx,by=launch_dims(task,shape)
        vals=[ct.c_uint64(p) for p in ptrs]+[ct.c_int(x) for x in shape]
        params=(ct.c_void_p*6)(*(ct.cast(ct.byref(v),ct.c_void_p) for v in vals))
        self.ck('cuLaunchKernel',fn,gx,gy,1,bx,by,1,0,None,params,None);self.ck('cuCtxSynchronize')
    def free_buffers(self):
        for p in self.allocs:self.ck('cuMemFree_v2',p)
        self.allocs=[]
    def close(self):
        # Context destruction releases all owned resources, including failed modules.
        if self.ctx:
            rc=self.f['cuCtxDestroy_v2'](self.ctx);self.ctx=None
            require(rc==0,'CUDA context cleanup failed: '+str(rc))

def launch_dims(task,shape):
    M,N,_=shape
    if task=='axpy':return ((M*N+255)//256,1,256,1)
    return ((N+15)//16,(M+15)//16,16,16)

GUARD=struct.pack('<I',0x5a693c17)*64

def alloc_case(gpu,helper,task,shape,seed):
    aa,bb,cc=helper.case(task,shape,seed)
    ar,br,expected=bytes(aa),bytes(bb),bytes(cc)
    raws=[ar,br,b'\xa5'*len(expected)]
    bases=[gpu.buffer(len(r)+2*len(GUARD)) for r in raws]
    for p,r in zip(bases,raws):gpu.put(p,GUARD+r+GUARD)
    return bases,[p+len(GUARD) for p in bases],ar,br,expected

def assert_state(gpu,bases,ar,br,expected):
    a=gpu.get(bases[0],len(ar)+2*len(GUARD));b=gpu.get(bases[1],len(br)+2*len(GUARD));c=gpu.get(bases[2],len(expected)+2*len(GUARD))
    require(a==GUARD+ar+GUARD and b==GUARD+br+GUARD,'INPUT_OR_INPUT_GUARD_CHANGED')
    require(c[:len(GUARD)]==GUARD and c[-len(GUARD):]==GUARD,'OUTPUT_GUARD_CHANGED')
    out=c[len(GUARD):-len(GUARD)]
    if out!=expected:
        i=next(i for i in range(len(expected)//4) if out[i*4:i*4+4]!=expected[i*4:i*4+4])
        raise NumericFailure(f'BITWISE_MISMATCH index={i} got={out[i*4:i*4+4].hex()} expected={expected[i*4:i*4+4].hex()}')
    return out

def check_kernel(gpu,helper,fn,task,large=True):
    cases=SMALL_SHAPES+(PERF_SHAPES[task] if large else [])
    records=[]
    for shape in cases:
        for seed in (1009,9173):
            bases,ptrs,a,b,expected=alloc_case(gpu,helper,task,shape,seed)
            for fill in (0xa5,0x5a):
                gpu.put(bases[2],GUARD+bytes([fill])*len(expected)+GUARD)
                gpu.launch(fn,ptrs,shape,task);assert_state(gpu,bases,a,b,expected)
            records.append({'shape':shape,'seed':seed,'elements':len(expected)//4,'reference_sha256':sha(expected)})
            gpu.free_buffers()
    return {'bitwise_pass':True,'test_cases':len(records),'records':records,'formal_equivalence_proven':False}

def paired_time(gpu,helper,f0,f1,task,shape):
    bases,ptrs,a,b,expected=alloc_case(gpu,helper,task,shape,4327)
    ev0,ev1=gpu.event(),gpu.event();gx,gy,bx,by=launch_dims(task,shape)
    def batch(fn,n):
        elapsed=ct.c_float()
        rc=helper.batch(fn,*ptrs,*shape,gx,gy,bx,by,n,ev0,ev1,ct.byref(elapsed))
        require(rc==0,'CUDA_TIMING_ERROR '+str(rc));require(math.isfinite(elapsed.value) and elapsed.value>0,'Invalid CUDA elapsed time')
        assert_state(gpu,bases,a,b,expected)
        return elapsed.value
    # Fixed warmup for both paths, then baseline-only launch-count calibration.
    batch(f0,128);batch(f1,128)
    n=1
    while True:
        t=batch(f0,n)
        if t>=5.0 or n>=4096:break
        n=min(4096,n*2)
    records=[]
    for session in range(2):
        batch(f0,64);batch(f1,64)
        for pair in range(8):
            order=(0,1) if (session+pair)%2==0 else (1,0);times={}
            for which in order:times[which]=batch((f0,f1)[which],n)
            records.append({'session':session,'pair':pair,'order':list(order),'repeats':n,
                            'baseline_ms':times[0]/n,'candidate_ms':times[1]/n,'ratio':times[0]/times[1]})
    gpu.free_buffers();return records

def archive_dir(src,label):
    need(re.fullmatch(r'[a-z0-9-]+',label) is not None,'Bad checkpoint label')
    src=safe(src);items={}
    for p in sorted(src.rglob('*')):
        safe(p)
        if p.is_dir():continue
        need(p.is_file(),'Special file in checkpoint');n=p.relative_to(src).as_posix();items[n]=hfile(p)
    need(items,'Empty checkpoint')
    manifest=canon(items)
    out=ROOT/'archives'/(label+'.tar.gz');part=out.with_suffix(out.suffix+'.partial')
    out.parent.mkdir(exist_ok=True)
    with part.open('xb') as sink:
        with tarfile.open(fileobj=sink,mode='w:gz',compresslevel=1) as tf:
            for n,h in sorted(items.items()):
                b=read(src/n);need(sha(b)==h,'Checkpoint source changed')
                ti=tarfile.TarInfo(n);ti.size=len(b);ti.mode=0o600;tf.addfile(ti,io.BytesIO(b))
            ti=tarfile.TarInfo('CHECKPOINT_SHA256.json');ti.size=len(manifest);ti.mode=0o600;tf.addfile(ti,io.BytesIO(manifest))
        sink.flush();os.fsync(sink.fileno())
    rec={'label':label,'sha256':hfile(part),'bytes':part.stat().st_size,'files':len(items),
         'manifest_sha256':sha(manifest),'utc':now()}
    verify_archive(part,rec);os.rename(part,out);jw(ROOT/'receipts'/(label+'.json'),rec)
    print('GPU001_CHECKPOINT_READY '+label,flush=True);return rec

def verify_archive(path,rec):
    need(path.stat().st_size==rec['bytes'] and hfile(path)==rec['sha256'],'Archive digest/size mismatch')
    observed={};tab=None
    with tarfile.open(path,'r:gz') as tf:
        for ti in tf:
            n=ti.name;p=PurePosixPath(n)
            need(n and str(p)==n and not p.is_absolute() and '..' not in p.parts and '\\' not in n,'Unsafe tar member')
            need(ti.isfile() and not ti.islnk() and ti.size<=64*1024**2 and n not in observed,'Invalid/repeated tar member')
            s=tf.extractfile(ti);b=s.read(ti.size+1);need(len(b)==ti.size,'Tar size mismatch');observed[n]=sha(b)
            if n=='CHECKPOINT_SHA256.json':tab=parse(b)
    need(isinstance(tab,dict) and observed.pop('CHECKPOINT_SHA256.json',None)==rec['manifest_sha256'],'Manifest missing/mismatch')
    need(tab==observed and len(tab)==rec['files'],'Checkpoint payload mismatch')
    return {'verified_files':len(tab),'sha256':rec['sha256']}

def wait_ack(rec):
    update(phase='WAITING_LOCAL_BACKUP',checkpoint=rec['label'])
    p=ROOT/'acks'/(rec['label']+'.json');deadline=time.monotonic()+ACK_SECONDS
    if WORK_DEADLINE is not None:deadline=min(deadline,WORK_DEADLINE)
    while not p.exists():
        need(time.monotonic()<deadline,'Local backup acknowledgement absent for 1h; no more generation; use --watch before deadline')
        time.sleep(2)
    need(parse(read(p)).get('sha256')==rec['sha256'],'Backup ACK mismatch')

def native_info():
    # Keep every CUDA context out of the long-lived coordinating process.
    d=ROOT/'setup/device-inventory';public_dirs(d);os.chown(d,65534,65534)
    job=d/'job.json';jw(job,{'mode':'info','output':str(d/'numeric-result.json')});job.chmod(0o444)
    rc=command([*unpriv_prefix(),'/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_numeric',str(job)],d/'process.log',60)
    need(rc==0 and (d/'numeric-result.json').is_file(),'CUDA device inventory failed before generation')
    r=parse(read(d/'numeric-result.json'));need(r.get('ok') is True,'Unprivileged CUDA device inventory failed')
    return r['gpu']

def profiles(info):
    fields=('name','compute_capability','warp_size','static_shared_memory_per_block',
            'registers_per_block','max_threads_per_multiprocessor','shared_memory_per_multiprocessor')
    actual={k:info[k] for k in fields}
    wrong={'name':'NVIDIA V100','compute_capability':[7,0],'warp_size':32,
           'static_shared_memory_per_block':49152,'registers_per_block':65536,
           'max_threads_per_multiprocessor':2048,'shared_memory_per_multiprocessor':98304}
    return {'P0':'No GPU model name or extra performance specification is supplied.',
            'S1':'Target GPU: NVIDIA A40.',
            'S2':'Target GPU profile:\n'+json.dumps(actual,sort_keys=True),
            'W1':'Target GPU: NVIDIA V100.',
            'W2':'Target GPU profile:\n'+json.dumps(wrong,sort_keys=True)}

def prompt(task,block):
    description={
      'axpy':'For every i < M*N, compute C[i] = RN32(RN32(1.25f*A[i]) + B[i]). Grid is 1D ceil(M*N/256), block=(256,1,1). K is unused.',
      'transpose':'Copy C[col*M+row] = A[row*N+col] bit for bit for row<M and col<N. B and K are unused. Grid=(ceil(N/16),ceil(M/16),1), block=(16,16,1).',
      'gemm_ordered':'For each C[row*N+col], initialize sum=+0.0f. In ascending k from 0 to K-1, compute product=RN32(A[row*K+k]*B[k*N+col]), then sum=RN32(sum+product). Store sum. Grid=(ceil(N/16),ceil(M/16),1), block=(16,16,1).',
    }[task]
    user=f'''Optimize the CUDA C++ kernel below. Return only the complete kernel, with exactly the supplied signature.
{block}

Task: {description}
A and B are disjoint read-only arrays. C is disjoint and must be fully overwritten.
All dimensions and array-size products fit signed 32-bit integers and are positive and variable, including dimensions not divisible by block sizes. Do not specialize to test data or dimensions.
For arithmetic, inputs are finite FP32 within [-4,4], including subnormals and signed zero. Transpose must copy every 32-bit pattern, including NaN payloads.
Strict contract: exact FP32 operation order and bitwise output equality. No error tolerance, no reassociation, no fast math, no TF32/FP16/Tensor Cores, no FMA contraction. Compiler uses fmad=false and ftz=false. Fused multiply-add is not permitted.
Launch shape is fixed as specified above; do not supply host code or a launch wrapper. Static shared memory up to 48 KiB is allowed. Every required barrier must be safe for ragged shapes.
Permitted: local scalar variables, arrays, __shared__, ordinary arithmetic/control flow, __fadd_rn, __fmul_rn, __fsub_rn, __syncthreads, __syncwarp, min/max, and synchronized shuffle intrinsics.
Not permitted: includes, preprocessor directives, helper functions, inline PTX/assembly, string literals in the body, atomics, dynamic parallelism, allocations, external libraries, pointer-to-function casts, host code, or changes to A/B. Keep the exact signature and use no additional top-level declaration.
This is a single attempt. No compilation or timing feedback will be supplied. If no safe improvement is found, return the original kernel.

----- BEGIN ORIGINAL CUDA -----
{SOURCES[task]}----- END ORIGINAL CUDA -----'''
    return [{'role':'system','content':'Optimize CUDA numerical kernels under the exact correctness contract. Return only the complete requested device kernel, without explanations or tools.'},
            {'role':'user','content':user}]

def plan_document(info):
    blocks=profiles(info);rng=random.Random(2026100801);groups=[]
    for task in TASKS:
        arms=list(ARMS);rng.shuffle(arms)
        groups.append({'task':task,'arms':arms,'requests':[{'id':task+'__'+a,'condition':a,'messages':prompt(task,blocks[a])} for a in arms]})
    return {'schema':VERSION,'scope':'custom CUDA pipeline pilot; not a standard benchmark or whole study',
      'groups':groups,'expected_generations':15,'generation_seed':69001,'generation_max_tokens':CAP,'request_wall_seconds':REQUEST_SECONDS,
      'source_names':list(TASKS),'forms':['CUDA_C++_device_kernel_to_CUDA_C++_device_kernel'],'profiles':blocks,
      'small_shapes':SMALL_SHAPES,'performance_shapes':PERF_SHAPES,'NVRTC_options':NVRTC_OPTIONS,
      'launch_shapes':'fixed by task; NOT chosen by LLM','oracle':'independent trusted CPU FP32 RN multiply then RN add, no FMA; transpose byte copy',
      'comparison':'byte exact including signed zeros and transpose NaN payloads; finite tests, not a formal proof',
      'timing':'hot-buffer CUDA event batch timings; baseline-only calibration target5ms max4096; 2 sessions x 8 AB/BA pairs; host copies/extraction/sanitizers excluded',
      'quality_thresholds':{'relative_iqr':0.1,'between_session_log':math.log(1.03),'identity_log':math.log(1.02)},
      'same_source_and_cubin_reported':True,'sanitizers':['memcheck','initcheck','racecheck','synccheck'],
      'safe_storage':'new Runpod namespace; local hash-verified checkpoint ACK before next generation group',
      'transport_has_no_retired_CPU_host':True,'no_candidate_retries':True,'run_wall_limit_seconds':RUN_SECONDS,
      'waiting_local_backup_limit_seconds':ACK_SECONDS,'strict_arithmetic_domain':'finite FP32 inputs [-4,4]; tests cover selected finite cases only',
      'not_a_final_GPU_specialization_study':True}

def helper_build():
    d=ROOT/'setup';d.mkdir(exist_ok=True);save(d/'trusted_helper.cpp',HELPER_CPP.encode())
    args=['g++','-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off',str(d/'trusted_helper.cpp'),'-ldl','-o',str(d/'trusted_helper.so')]
    jw(d/'host-build-command.json',args);rc=command(args,d/'host-build.log',180)
    need(rc==0,'Trusted host helper build failed; no LLM generation')
    (d/'trusted_helper.so').chmod(0o555)
    return d/'trusted_helper.so'

def unpriv_prefix():
    return ['setpriv','--reuid=65534','--regid=65534','--clear-groups','--bounding-set=-all',
            '--inh-caps=-all','--ambient-caps=-all','--no-new-privs']

def run_numeric(task,cubin,dest,helper,mode='check',baseline=None,shape=None,sanitizer=None):
    dest=safe(dest);dest.mkdir(parents=True,exist_ok=False);public_dirs(dest);os.chown(dest,65534,65534)
    job={'task':task,'mode':mode,'cubin':str(cubin),'cubin_sha256':hfile(cubin),
         'helper':str(helper),'helper_sha256':hfile(helper),'output':str(dest/'numeric-result.json')}
    if baseline is not None:job.update(baseline=str(baseline),baseline_sha256=hfile(baseline))
    if shape is not None:job['shape']=list(shape)
    if sanitizer:job['small_only']=True
    p=dest/'job.json';jw(p,job);p.chmod(0o444)
    app=['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_numeric',str(p)]
    if sanitizer:
        exe=sanitizer_path();app=[exe,'--tool',sanitizer,'--error-exitcode','97','--target-processes','all',*app]
    rc=command([*unpriv_prefix(),*app],dest/'process.log',timeout=600)
    result_path=dest/'numeric-result.json'
    result=parse(read(result_path)) if result_path.exists() else {'ok':False,'error':'NO_NUMERIC_RESULT'}
    result.update(process_returncode=rc)
    if sanitizer:
        text=read(dest/'process.log',16*1024**2).decode(errors='replace')
        clean=bool(re.search(r'ERROR SUMMARY:\s+0 errors',text))
        if sanitizer=='racecheck':clean=clean or bool(re.search(r'RACECHECK SUMMARY:\s+0 hazards',text))
        result['sanitizer']=sanitizer;result['sanitizer_clean']=clean and rc==0
        result['ok']=result.get('ok') is True and result['sanitizer_clean']
    else:result['ok']=result.get('ok') is True and rc==0
    jw(dest/'parent-result.json',result)
    return result

def sanitizer_path():
    candidates=['/usr/local/cuda-12.8/compute-sanitizer/compute-sanitizer','/usr/local/cuda-12.8/bin/compute-sanitizer']
    if shutil.which('compute-sanitizer'):candidates.insert(0,shutil.which('compute-sanitizer'))
    p=next((p for p in candidates if Path(p).is_file()),None)
    need(p is not None,'Compute Sanitizer missing; no generation is allowed before safety preflight')
    return p

def compile_candidate(source,dest):
    dest=safe(dest);dest.mkdir(parents=True,exist_ok=False);public_dirs(dest);os.chown(dest,65534,65534)
    src=dest/'kernel.cu';save(src,source.encode());src.chmod(0o444)
    job=dest/'job.json';jw(job,{'mode':'compile','source':str(src),'source_sha256':hfile(src),'output':str(dest/'numeric-result.json')});job.chmod(0o444)
    rc=command([*unpriv_prefix(),'/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_numeric',str(job)],dest/'process.log',180)
    res=parse(read(dest/'numeric-result.json')) if (dest/'numeric-result.json').exists() else {'ok':False,'error':'NO_COMPILE_RESULT'}
    res['process_returncode']=rc;res['ok']=res.get('ok') is True and rc==0
    if res['ok']:
        for n in ('kernel.cubin','kernel.ptx'):safe(dest/n).chmod(0o444)
        res.update(source_sha256=hfile(src),cubin_sha256=hfile(dest/'kernel.cubin'),ptx_sha256=hfile(dest/'kernel.ptx'))
    jw(dest/'parent-result.json',res);return res

def run_numeric_job(path):
    # Only this trusted runner executes host code. Generated content is NVRTC device input or a cubin.
    need(os.geteuid()==65534,'Numeric subprocess must be unprivileged')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(500,500))
    job=parse(read(path));out=safe(job['output']);need(out.parent==Path(path).parent,'Job output escaped')
    gpu=None
    try:
        if job['mode']=='compile':
            need(hfile(job['source'])==job['source_sha256'],'Source input changed')
            details=nvrtc_compile(read(job['source']).decode(),out.parent)
            result={'ok':True,'compile':details}
        elif job['mode']=='info':
            gpu=CUDA();result={'ok':True,'gpu':gpu.info}
        else:
            task=job['task'];need(task in TASKS,'Unknown kernel task')
            need(hfile(job['cubin'])==job['cubin_sha256'] and hfile(job['helper'])==job['helper_sha256'],'Numeric artifact hash mismatch')
            gpu=CUDA();helper=Helper(job['helper']);fn=gpu.module(job['cubin'])
            if job['mode']=='check':result={'ok':True,**check_kernel(gpu,helper,fn,task,not job.get('small_only',False))}
            else:
                need(job['mode']=='time' and hfile(job['baseline'])==job['baseline_sha256'],'Wrong timing job')
                baseline=gpu.module(job['baseline']);shape=tuple(job['shape']);need(shape in PERF_SHAPES[task],'Timing shape changed')
                result={'ok':True,'rows':paired_time(gpu,helper,baseline,fn,task,shape),'shape':shape}
        if gpu is not None:gpu.close();gpu=None
        jw(out,result);return 0
    except BaseException as exc:
        jw(out,{'ok':False,'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc()});return 3
    finally:
        if gpu is not None:
            try:gpu.close()
            except Exception:pass

def timing_metric(rows):
    need(len(rows)==16 and {(x['session'],x['pair']) for x in rows}=={(s,p) for s in range(2) for p in range(8)},'Incomplete time pairs')
    xs=[r['ratio'] for r in rows];need(all(isinstance(x,(int,float)) and x>0 and math.isfinite(x) for x in xs),'Bad time ratio')
    median=statistics.median(xs);q=statistics.quantiles(xs,n=4,method='inclusive');rel_iqr=(q[2]-q[0])/median
    sessions=[statistics.median([r['ratio'] for r in rows if r['session']==s]) for s in range(2)]
    reasons=[]
    if rel_iqr>0.1:reasons.append('paired_ratio_relative_iqr')
    if abs(math.log(sessions[0]/sessions[1]))>math.log(1.03):reasons.append('between_session_ratio_change')
    return {'speedup':median,'relative_iqr':rel_iqr,'session_medians':sessions,'quality_reasons':reasons,'measurement_valid':not reasons}

def no_other_gpu():
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:comm=(p/'comm').read_text().strip()
        except (FileNotFoundError,ProcessLookupError):continue
        need(comm not in ('llama-server','ollama'),'An inference engine is active; not stopping it')
    cp=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],capture_output=True,text=True,timeout=20,env=clean_env())
    need(cp.returncode==0,'GPU process inventory unavailable')
    need(not cp.stdout.strip(),'A GPU compute process is active; not stopping it: '+cp.stdout.strip())

def telemetry():
    p=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,temperature.gpu,clocks.sm,clocks.mem,power.draw,memory.used,utilization.gpu',
                      '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=20,env=clean_env())
    return {'utc':now(),'returncode':p.returncode,'csv':p.stdout,'stderr':p.stderr}

def sanitized_check(task,cubin,dest,helper):
    normal=run_numeric(task,cubin,dest/'bitwise',helper)
    if not normal['ok']:return {'passed':False,'stage':'bitwise_or_execution_failed','bitwise':normal}
    checks={}
    for s in ('memcheck','initcheck','racecheck','synccheck'):
        checks[s]=run_numeric(task,cubin,dest/s,helper,sanitizer=s)
        if not checks[s]['ok']:return {'passed':False,'stage':'sanitizer_failed','checks':checks,'bitwise':normal}
    return {'passed':True,'stage':'correctness_passed','bitwise':normal,'checks':checks,'formal_equivalence_proven':False}

def baseline_preflight(helper):
    controls={}
    for task in TASKS:
        update(phase='ORIGINAL_CUDA_PREFLIGHT',task=task)
        no_other_gpu();d=ROOT/'preflight'/task
        b=compile_candidate(SOURCES[task],d/'baseline');tw=compile_candidate(SOURCES[task],d/'identity')
        need(b['ok'] and tw['ok'],'Original CUDA compilation failed')
        need(b['cubin_sha256']==tw['cubin_sha256'],'Identical source compilation is not reproducible')
        v=sanitized_check(task,d/'baseline/kernel.cubin',d/'validation',helper)
        need(v['passed'],'Original CUDA correctness/sanitizer check failed; no LLM generation')
        # Explicit unchanged-source control, not merely identity inferred from timings.
        tiv=run_numeric(task,d/'identity/kernel.cubin',d/'identity-validation',helper)
        need(tiv['ok'],'Unchanged-source numerical control failed')
        per=[]
        for i,shape in enumerate(PERF_SHAPES[task]):
            r=run_numeric(task,d/'identity/kernel.cubin',d/f'identity-timing-{i}',helper,mode='time',baseline=d/'baseline/kernel.cubin',shape=shape)
            need(r['ok'],'Unchanged-source timing execution failed')
            mm=timing_metric(r['rows']);mm['shape']=list(shape)
            need(mm['measurement_valid'] and abs(math.log(mm['speedup']))<=math.log(1.02),
                 'Unchanged-source timing quality failed; baseline not reliable enough for pilot')
            per.append(mm)
        controls[task]={'baseline':b,'identity':tw,'validation':v,'timing':per}
        jw(d/'summary.json',controls[task]);print('GPU001_ORIGINAL_AND_IDENTITY_PASS '+task,flush=True)
    # A device-only intentionally wrong output verifies that mismatch detection is live.
    wrong=SIGNATURE+'\n{ int i = blockIdx.x * blockDim.x + threadIdx.x; if (i < M*N) C[i]=0.0f; }\n'
    d=ROOT/'preflight/negative-control';r=compile_candidate(wrong,d/'compiled');need(r['ok'],'Negative-control compile failed')
    v=run_numeric('axpy',d/'compiled/kernel.cubin',d/'validation',helper)
    need(not v['ok'] and 'BITWISE_MISMATCH' in v.get('error',''),'Broken CUDA output not detected')
    jw(d/'summary.json',{'expected_failure_detected':True,'result':v})
    return controls
def start_model(A,assets,folder):
    binary,model,cudaenv,*_=assets
    A.ROOT=folder;A.PORT=PORT
    folder.mkdir(parents=True,exist_ok=True);public_dirs(folder)
    home=folder/'infer-home';home.mkdir(mode=0o755,exist_ok=True);home.chmod(0o755)
    no_other_gpu()
    with socket.socket() as sock:sock.bind(('127.0.0.1',PORT))
    argv=A.server_argv(binary,model);env=clean_env();env.update(cudaenv,HOME=str(home),TMPDIR='/tmp')
    jw(folder/'server-command.json',argv)
    with (folder/'llama-server.log').open('xb') as log:
        proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=folder,env=env,start_new_session=True)
    try:
        deadline=time.monotonic()+600
        while time.monotonic()<deadline:
            need(proc.poll() is None,'LLM process exited during load')
            try:
                if A.api('/health',timeout=5).get('status')=='ok':break
            except (OSError,Exception):pass
            time.sleep(1)
        else:raise Blocked('LLM load timed out')
        props=A.api('/props');jw(folder/'props.json',props)
        need(props.get('total_slots')==1 and props['default_generation_settings']['n_ctx']==32768,'LLM slot/context mismatch')
        need(Path(props['model_path']).resolve()==model.resolve(),'Wrong LLM model loaded')
        need(sha(props['chat_template'].encode())=='55b2f4a26ac9ee719330a61a0c39d9e538b0e9322212f048326318cff4f8674a','Model template changed')
        off=A.wait_for_offload(folder/'llama-server.log',proc);jw(folder/'offload.json',off)
        need(off['offloaded_layers']==49,'Unexpected model layer count')
        return proc
    except BaseException:close_child(proc);raise

def response_code(response,cap=CAP):
    require(response.get('truncated') is False,'LLM context truncation')
    require(response.get('stop_type') in ('eos','word'),'LLM output cap/incomplete response')
    count=response.get('timings',{}).get('predicted_n')
    require(type(count) is int and 0<count<=cap+8,'Invalid output token count')
    return normalize_source(response.get('content'))

def generate_group(A,assets,group):
    task=group['task'];d=ROOT/'tasks'/task;d.mkdir(parents=True,exist_ok=True);public_dirs(d)
    results=[];proc=None;attempts=0
    try:
        for req in group['requests']:
            arm=req['condition'];rd=d/'generation'/arm;rd.mkdir(parents=True,exist_ok=False);public_dirs(rd)
            if proc is None:
                session=d/f'inference-session-{attempts:02d}'
                update(phase='LOADING_GENERATION_MODEL',task=task)
                proc=start_model(A,assets,session)
            update(phase='GENERATING_CUDA',task=task,condition=arm,current_id=req['id'])
            jw(rd/'role-request.json',req)
            rendered=A.api('/apply-template',{'messages':req['messages']})['prompt']
            need(isinstance(rendered,str) and all(x['content'] in rendered for x in req['messages']),'Template lost prompt content')
            save(rd/'rendered-prompt.txt',rendered.encode())
            token_record=A.api('/tokenize',{'content':rendered,'add_special':True,'parse_special':True})
            ids=token_record['tokens'];need(isinstance(ids,list) and all(type(i) is int and i>=0 for i in ids),'Invalid native input tokens')
            jw(rd/'native-tokens.json',token_record)
            need(len(ids)+CAP+16<=32768,'Prompt budget exceeded; no automatic truncation')
            body=dict(A.SAMPLING,prompt=ids,n_predict=CAP,stream=False,return_tokens=True,id_slot=0)
            jw(rd/'wire-request.json',body);jw(rd/'attempt-intent.json',{'id':req['id'],'attempt':1,'utc':now(),'max_tokens':CAP})
            attempts+=1
            with STATE_LOCK:total=STATE.get('generation_calls',0)+1
            need(total<=MAX_GENERATIONS,'Generation call ceiling reached');update(generation_calls=total)
            begin=time.monotonic()
            try:
                need(WORK_DEADLINE is None or time.monotonic()<WORK_DEADLINE,'Pilot wall budget reached')
                budget=REQUEST_SECONDS if WORK_DEADLINE is None else min(REQUEST_SECONDS,max(1,WORK_DEADLINE-time.monotonic()))
                response=A.api('/completion',body,timeout=budget)
                jw(rd/'raw-response.json',response)
                code=response_code(response);save(rd/'candidate.cu',code.encode())
                record={'id':req['id'],'task':task,'condition':arm,'generation_status':'saved','source_sha256':sha(code.encode()),
                        'source_equals_original':code==SOURCES[task],'error':None,'wall_seconds':time.monotonic()-begin,
                        'native_input_tokens':len(ids),'returned_input_tokens':response.get('tokens_evaluated'),
                        'tokens_per_second':response.get('timings',{}).get('predicted_per_second')}
                # The exact token array, not a retokenized string, was sent; reject truncation explicitly.
                need(response.get('tokens_evaluated')==len(ids),'LLM input accounting mismatch')
            except NumericFailure as exc:
                record={'id':req['id'],'task':task,'condition':arm,'generation_status':'invalid_generation','error':str(exc),'wall_seconds':time.monotonic()-begin}
            except (OSError,http.client.HTTPException,TimeoutError) as exc:
                record={'id':req['id'],'task':task,'condition':arm,'generation_status':'transport_or_timeout','error':type(exc).__name__+': '+str(exc),'wall_seconds':time.monotonic()-begin}
                # A timeout is an attempted slot, never a free retry. Cancel owned model before advancing.
                close_child(proc);proc=None
            jw(rd/'record.json',record);results.append(record)
            print('GPU001_GENERATION_TERMINAL '+req['id']+' '+record['generation_status'],flush=True)
    finally:
        close_child(proc);jw(d/'model-stopped-before-evaluation.json',{'utc':now(),'owned_process_stopped':True})
    no_other_gpu();return results

def evaluate_group(group,generated,helper,controls):
    task=group['task'];dest=ROOT/'tasks'/task;outcomes=[]
    for g in generated:
        arm=g['condition'];base=ROOT/'preflight'/task/'baseline/kernel.cubin';d=dest/'evaluation'/arm
        public_dirs(d.parent)
        o={**g,'correctness_passed':False,'stage':None,'measurements':[],'formal_equivalence_proven':False}
        if g['generation_status']!='saved':o['stage']='generation_failed';outcomes.append(o);continue
        update(phase='COMPILING_CUDA',task=task,condition=arm);no_other_gpu()
        source=read(dest/'generation'/arm/'candidate.cu').decode();need(sha(source.encode())==g['source_sha256'],'Candidate source changed')
        compiled=compile_candidate(source,d/'compiled');o['compilation']=compiled
        if not compiled['ok']:o['stage']='compile_failed';outcomes.append(o);continue
        cubin=d/'compiled/kernel.cubin';o['same_cubin_as_original']=hfile(cubin)==hfile(base)
        o['same_ptx_as_original']=hfile(d/'compiled/kernel.ptx')==hfile(base.with_suffix('.ptx'))
        update(phase='VERIFYING_CUDA',task=task,condition=arm)
        v=sanitized_check(task,cubin,d/'validation',helper);jw(d/'validation-summary.json',v);o['correctness_passed']=v['passed']
        if not v['passed']:o['stage']=v['stage'];outcomes.append(o);continue
        update(phase='MEASURING_GPU_KERNEL',task=task,condition=arm)
        no_other_gpu();jw(d/'telemetry-before.json',telemetry())
        for i,shape in enumerate(PERF_SHAPES[task]):
            r=run_numeric(task,cubin,d/f'timing-{i}',helper,mode='time',baseline=base,shape=shape)
            m={'shape':list(shape),'measurement_valid':False,'speedup':None}
            if r['ok']:
                m.update(timing_metric(r['rows']))
                # A same-session baseline-vs-baseline control follows each candidate measurement.
                twin=ROOT/'preflight'/task/'identity/kernel.cubin'
                ident=run_numeric(task,twin,d/f'identity-timing-{i}',helper,mode='time',baseline=base,shape=shape)
                if ident['ok']:
                    im=timing_metric(ident['rows']);m['identity']=im
                    if not im['measurement_valid'] or abs(math.log(im['speedup']))>math.log(1.02):
                        m['quality_reasons'].append('identity_control_shift');m['measurement_valid']=False
                else:m['quality_reasons'].append('identity_execution_failed');m['measurement_valid']=False
            else:m['error']=r.get('error','timing_execution_failed')
            m['recorded_speedup_gt_1_02']=m['measurement_valid'] and m['speedup']>1.02
            m['different_cubin_speedup_gt_1_02']=m['recorded_speedup_gt_1_02'] and not o['same_cubin_as_original']
            o['measurements'].append(m)
        o['stage']='measured';jw(d/'telemetry-after.json',telemetry());jw(d/'outcome.json',o);outcomes.append(o)
    jw(dest/'outcomes.json',outcomes);return outcomes

def public_dirs(path):
    path=safe(path);need(path==ROOT or path.is_relative_to(ROOT),'Permission change outside new namespace')
    path.mkdir(parents=True,exist_ok=True)
    for p in (path,*path.parents):
        if p==ROOT or p.is_relative_to(ROOT):p.chmod(0o755)
        else:break

def remote_guard():
    need(os.geteuid()==0 and Path('/workspace').is_dir(),'Run worker only in the authorized Runpod')
    if os.environ.get('RUNPOD_POD_ID'):need(os.environ['RUNPOD_POD_ID']==POD,'Wrong Pod ID')

def write_summary(outcomes):
    need(len(outcomes)==15 and {(o['task'],o['condition']) for o in outcomes}=={(t,a) for t in TASKS for a in ARMS},'Pilot grid incomplete')
    metrics=[m for o in outcomes for m in o['measurements']];valid=[m for m in metrics if m['measurement_valid']]
    summary={'state':'GPU_CODE_PILOT_001_COMPLETE','scope':'3 custom kernels x 5 conditions; 2 measurement sizes per passing candidate',
      'candidate_slots':15,'generation_calls':STATE.get('generation_calls',0),'generation_status_counts':{},
      'correctness_passed':sum(o['correctness_passed'] for o in outcomes),'valid_size_measurements':len(valid),
      'recorded_size_speedups_gt_1_02':sum(m['recorded_speedup_gt_1_02'] for m in metrics),
      'different_cubin_size_speedups_gt_1_02':sum(m['different_cubin_speedup_gt_1_02'] for m in metrics),
      'not_all_slots_successful':any(not o['correctness_passed'] for o in outcomes),
      'formal_equivalence_proven':False,'whole_GPU_study_complete':False,
      'not_a_comparison_to_cuBLAS_or_other_optimized_libraries':True,
      'measurement_scope':'hot buffers, CUDA event kernel batch times; excludes LLM, compiler, CPU reference and PCIe copy time',
      'no_post_result_error_tolerance_changes':True,'no_best_of_or_selective_retry':True,
      'model':MODEL,'gpu':'NVIDIA A40','all_calls_on_runpod':True,'utc':now()}
    for o in outcomes:
        g=o['generation_status'];summary['generation_status_counts'][g]=summary['generation_status_counts'].get(g,0)+1
    d=ROOT/'final';d.mkdir();jw(d/'summary.json',summary);jw(d/'outcomes.json',outcomes)
    rows=[]
    for o in outcomes:
        for m in o['measurements'] or [{}]:
            rows.append({k:o.get(k) for k in ('task','condition','generation_status','stage','correctness_passed','source_equals_original','same_cubin_as_original','same_ptx_as_original')}|m)
    stream=io.StringIO();keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(stream,keys);w.writeheader();w.writerows(rows);save(d/'outcomes.csv',stream.getvalue().encode())
    save(d/'protocol.json',read(ROOT/'setup/protocol.json'));return summary

def worker(allow):
    global WORK_DEADLINE
    WORK_DEADLINE=time.monotonic()+RUN_SECONDS
    remote_guard();need(allow,'Explicit ephemeral storage acknowledgement is required');os.umask(0o022)
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(Blocked('Termination requested; partial records retained')))
    public_dirs(ROOT);public_dirs(ROOT/'control');safe(ROOT/'control/runner.py').chmod(0o444)
    start=time.monotonic()
    try:
        with lock('/workspace/gpu-code-pilot-exclusive.lock'):
            update(phase='PREFLIGHT',generation_calls=0,whole_GPU_study_complete=False,started_utc=now())
            no_other_gpu();need(shutil.disk_usage(ROOT).free>=2*GIB,'Less than 2GiB free in experiment filesystem')
            for x in ('g++','setpriv'):need(shutil.which(x),'Required tool missing: '+x)
            sanit=sanitizer_path()
            need(Path('/usr/local/cuda-12.8/lib64/libnvrtc.so').exists() or Path('/usr/local/cuda/lib64/libnvrtc.so').exists(),'NVRTC 12.8 library missing')
            A=module_a();A.ROOT=ROOT
            with contextlib.redirect_stdout(sys.stderr):assets=A.cached_assets();gi=A.gpu_info()
            need(gi['uuid']==EXPECTED_GPU and gi['name']=='NVIDIA A40','Unexpected GPU allocation')
            # Inspect properties with a short-lived CUDA context, destroy before other execution.
            info=native_info();plan=plan_document(info)
            helper=helper_build();public_dirs(ROOT/'setup')
            jw(ROOT/'setup/protocol.json',plan);jw(ROOT/'setup/gpu-properties.json',info)
            jw(ROOT/'setup/telemetry.json',telemetry());jw(ROOT/'setup/sanitizer.json',{'path':sanit,'sha256':hfile(Path(sanit).resolve())})
            jw(ROOT/'setup/runtime-identity.json',assets[3]);jw(ROOT/'setup/model-cache.json',assets[5])
            toolchain={}
            nvlib=Path('/usr/local/cuda-12.8/lib64/libnvrtc.so')
            if not nvlib.exists():nvlib=Path('/usr/local/cuda/lib64/libnvrtc.so')
            real=nvlib.resolve()
            toolchain[str(real)]=hfile(real)
            for t in sorted(real.parent.glob('libnvrtc-builtins.so*')):
                if t.is_file():toolchain[str(t.resolve())]=hfile(t.resolve())
            jw(ROOT/'setup/toolchain-hashes.json',toolchain)
            save(ROOT/'setup/runner.py',read(ROOT/'control/runner.py'))
            for task,src in SOURCES.items():save(ROOT/'setup/sources'/(task+'.cu'),src.encode())
            controls=baseline_preflight(helper)
            r=archive_dir(ROOT/'setup','setup');wait_ack(r)
            r=archive_dir(ROOT/'preflight','cuda-preflight');wait_ack(r)
            allout=[]
            for group in plan['groups']:
                need(time.monotonic()-start<RUN_SECONDS,'Pilot total wall budget reached; no repeat of completed slots')
                generated=generate_group(A,assets,group);task=group['task']
                r=archive_dir(ROOT/'tasks'/task/'generation','generation-'+task.replace('_','-'));wait_ack(r)
                no_other_gpu();out=evaluate_group(group,generated,helper,controls);allout.extend(out)
                r=archive_dir(ROOT/'tasks'/task,'evaluated-'+task.replace('_','-'));wait_ack(r)
                with contextlib.redirect_stdout(sys.stderr):A.verify_cached_unchanged(assets[5])
            summary=write_summary(allout);rec=archive_dir(ROOT/'final','summary');wait_ack(rec)
            jw(ROOT/'completion.json',{'summary_sha256':hfile(ROOT/'final/summary.json'),'summary_checkpoint':rec,'utc':now()})
            update(phase='COMPLETE',generation_calls=summary['generation_calls'],candidate_slots=15)
            print('GPU_CODE_PILOT_001_COMPLETE; NOT_THE_FULL_GPU_STUDY',flush=True)
    except BaseException as exc:
        details={}
        for p in sorted(ROOT.rglob('*.log'),key=lambda p:p.stat().st_mtime if p.is_file() else 0)[-6:]:
            if p.is_file() and not p.is_symlink():
                with p.open('rb') as f:
                    f.seek(0,2);f.seek(max(0,f.tell()-6000));details[p.relative_to(ROOT).as_posix()]=f.read().decode(errors='replace')
        atomic(ROOT/'failure.json',{'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'last_logs':details,'utc':now()})
        update(phase='BLOCKED',error=type(exc).__name__+': '+str(exc));raise

def remote_status():
    remote_guard();d={'state':'NOT_STARTED','receipts':[]}
    for n in ('launch','progress','failure','completion'):
        p=ROOT/(n+'.json')
        if p.exists():d[n]=parse(read(p))
    for p in sorted((ROOT/'receipts').glob('*.json')) if (ROOT/'receipts').exists() else []:d['receipts'].append(parse(read(p)))
    if 'completion' in d:
        need(hfile(ROOT/'final/summary.json')==d['completion']['summary_sha256'],'Final summary changed')
        d.update(state='COMPLETE',summary=parse(read(ROOT/'final/summary.json')))
    elif 'failure' in d:d['state']='BLOCKED'
    elif 'launch' in d:d['state']='RUNNING' if alive(d['launch']) else 'INTERRUPTED'
    return d

def remote_launch(allow):
    remote_guard();need(allow,'Use --allow-ephemeral-with-local-checkpoints for this bounded pilot')
    with lock(ROOT/'launch.lock'):
        if (ROOT/'launch.json').exists():
            d=remote_status();need(d['state'] in ('RUNNING','COMPLETE'),'Previous attempt retained; no automatic rerun');return d
        with (ROOT/'worker.log').open('xb') as f:
            proc=subprocess.Popen(['/usr/bin/python3','-I','-S','-B','-u',str(ROOT/'control/runner.py'),'--_worker','--allow-ephemeral-with-local-checkpoints'],
                stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,env=clean_env(),start_new_session=True)
        ticks=cgroup_start(proc.pid);need(ticks is not None,'Worker did not start')
        jw(ROOT/'launch.json',{'pid':proc.pid,'ticks':ticks,'runner_sha256':hfile(ROOT/'control/runner.py'),'utc':now()});return remote_status()

def install_text(pin):
    return '''import os,sys,hashlib
from pathlib import Path
p=Path(%r)
assert os.geteuid()==0 and Path('/workspace').is_dir(), 'Wrong execution environment'
assert os.environ.get('RUNPOD_POD_ID',%r)==%r, 'Wrong Pod'
for q in (p,*p.parents):assert not q.is_symlink(), 'Symlink refused'
b=sys.stdin.buffer.read(1024*1024+1)
assert len(b)<=1024*1024 and hashlib.sha256(b).hexdigest()==%r, 'Upload hash mismatch'
p.parent.mkdir(parents=True,exist_ok=True)
if p.exists():assert p.is_file() and p.read_bytes()==b, 'Runner conflict'
else:
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
print('GPU001_RUNNER_UPLOADED')
'''%(str(ROOT/'control/runner.py'),POD,POD,pin)

def checkpoint_collect(con,rec):
    label=rec['label'];need(re.fullmatch(r'[a-z0-9-]+',label),'Invalid checkpoint label')
    d=safe(Path.home()/LOCAL_REL);d.mkdir(parents=True,exist_ok=True);out=d/(label+'.tar.gz')
    if out.exists():verify_archive(out,rec)
    else:
        need(shutil.disk_usage(d).free>rec['bytes']+128*1024**2,'Not enough local disk for checkpoint')
        part=d/(label+'.partial-'+uuid.uuid4().hex)
        cmd=['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_send',label]
        with part.open('xb') as f:
            p=subprocess.run(['ssh','-T',*con.opts,SERVER,shlex.join(cmd)],stdout=f,check=False)
            need(p.returncode==0,'Checkpoint transfer failed; .partial retained, no false ACK');f.flush();os.fsync(f.fileno())
        verify_archive(part,rec);os.rename(part,out)
    rp=d/(label+'-receipt.json')
    if rp.exists():need(read(rp)==canon(rec),'Stored checkpoint receipt differs')
    else:jw(rp,rec)
    con.run(['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_ack',label,rec['sha256']])
    atomic(d/(label+'-local-verified.json'),{'sha256':rec['sha256'],'files':rec['files'],'utc':now()})
    print('GPU001_LOCAL_CHECKPOINT_VERIFIED '+label,flush=True)

def local(mode,allow=False):
    need(os.geteuid()!=0,'Run from WSL as the regular user, without sudo')
    A=module_a();A.fingerprint_check(Path.home()/'.ssh/id_ed25519');con=A.Connection()
    # Every network command targets the retained Runpod only; never the retired server.
    try:
        if mode=='run':
            need(allow,'Explicit temporary storage acknowledgement required')
            raw=read(__file__);print(con.run(['/usr/bin/python3','-I','-S','-B','-c',install_text(sha(raw))],data=raw).decode(),flush=True)
            doc=parse(con.run(['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_launch','--allow-ephemeral-with-local-checkpoints']))
            print('GPU_CODE_PILOT_001_STARTED; up to 15 NEW CUDA generations; same A40 also evaluates',flush=True)
        elif mode=='stop':
            print(con.run(['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_stop']).decode());return
        else:doc=parse(con.run(['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_status']))
        seen=set()
        while True:
            if mode=='status':print(json.dumps(doc,ensure_ascii=False,indent=2));return
            for rec in doc['receipts']:
                if rec['label'] not in seen:checkpoint_collect(con,rec);seen.add(rec['label'])
            print(json.dumps({'state':doc['state'],**doc.get('progress',{})},ensure_ascii=False),flush=True)
            if doc['state'] in ('BLOCKED','INTERRUPTED'):
                d=safe(Path.home()/LOCAL_REL);d.mkdir(parents=True,exist_ok=True);atomic(d/'last-status.json',doc)
                raise Blocked(doc.get('failure',{}).get('error','Remote process stopped; do not repeat generation'))
            if doc['state']=='COMPLETE':
                d=safe(Path.home()/LOCAL_REL);atomic(d/'final-status.json',doc)
                print(json.dumps(doc['summary'],ensure_ascii=False,indent=2));print('GPU_CODE_PILOT_001_LOCAL_COPY_VERIFIED');return
            need(doc['state']=='RUNNING','Pilot has not started')
            if mode=='collect':return
            time.sleep(10);doc=parse(con.run(['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_status']))
    except KeyboardInterrupt:print('LOCAL_WATCH_STOPPED; remote pauses at next backup gate; reconnect --watch within 1h. Pod still billed.')
    finally:con.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for a in ('run','watch','status','collect','stop','self-test','_launch','_worker','_status','_stop'):g.add_argument('--'+a,action='store_true')
    g.add_argument('--_numeric');g.add_argument('--_send');g.add_argument('--_ack',nargs=2)
    p.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true')
    args=p.parse_args()
    if args.self_test:self_test();return
    if args._numeric:sys.exit(run_numeric_job(args._numeric))
    if args._worker:worker(args.allow_ephemeral_with_local_checkpoints);return
    if args._launch:print(json.dumps(remote_launch(args.allow_ephemeral_with_local_checkpoints)));return
    if args._status:print(json.dumps(remote_status()));return
    if args._stop:
        remote_guard();rec=parse(read(ROOT/'launch.json'))
        if alive(rec):os.kill(rec['pid'],signal.SIGTERM)
        print('OWNED_GPU001_WORKER_STOP_REQUESTED; no data deleted, no Pod termination');return
    if args._send or args._ack:
        remote_guard();label=args._send or args._ack[0];need(re.fullmatch(r'[a-z0-9-]+',label),'Bad label')
        rec=parse(read(ROOT/'receipts'/(label+'.json')))
        if args._send:
            path=ROOT/'archives'/(label+'.tar.gz');need(hfile(path)==rec['sha256'],'Checkpoint archive changed')
            with path.open('rb') as f:shutil.copyfileobj(f,sys.stdout.buffer,1024**2)
        else:
            need(args._ack[1]==rec['sha256'],'ACK digest differs');path=ROOT/'acks'/(label+'.json')
            obj={'sha256':rec['sha256']}
            if path.exists():need(parse(read(path))==obj,'ACK mismatch')
            else:jw(path,obj)
            print('ACK_STORED')
        return
    mode=next(x for x in ('run','watch','status','collect','stop') if getattr(args,x));local(mode,args.allow_ephemeral_with_local_checkpoints)


def self_test():
    class T(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.tmp=tempfile.TemporaryDirectory(prefix='gpu001-unit-')
            cls.base=Path(cls.tmp.name);cls.so=cls.base/'helper.so';src=cls.base/'helper.cpp';src.write_text(HELPER_CPP)
            c=subprocess.run(['g++','-O2','-std=c++17','-shared','-fPIC','-fno-fast-math','-ffp-contract=off',str(src),'-ldl','-o',str(cls.so)],capture_output=True,text=True)
            if c.returncode:raise RuntimeError('Host reference compile failed: '+c.stderr)
            cls.h=Helper(cls.so)
        @classmethod
        def tearDownClass(cls):cls.tmp.cleanup()
        def setUp(self):
            self.t=tempfile.TemporaryDirectory(prefix='gpu001-test-');self.r=Path(self.t.name)/'run';self.r.mkdir()
            self.p=mock.patch.dict(globals(),ROOT=self.r,STATE={});self.p.start()
        def tearDown(self):self.p.stop();self.t.cleanup()
        def info(self):return {'name':'NVIDIA A40','compute_capability':[8,6],'warp_size':32,'static_shared_memory_per_block':49152,'registers_per_block':65536,'max_threads_per_multiprocessor':1536,'shared_memory_per_multiprocessor':102400}
        def rows(self,ratio=1.0):return [{'session':s,'pair':p,'ratio':ratio,'baseline_ms':ratio,'candidate_ms':1.0,'repeats':16,'order':[0,1] if (s+p)%2==0 else [1,0]} for s in range(2) for p in range(8)]
        def test_original_policy(self):
            for v in SOURCES.values():self.assertEqual(source_policy(v),v)
        def test_policy_include(self):self.assertRaises(NumericFailure,source_policy,'#include <stdio.h>\n'+SOURCES['axpy'])
        def test_policy_host_main(self):self.assertRaises(NumericFailure,source_policy,SOURCES['axpy']+'int main() {return 0;}')
        def test_policy_indirect(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { ((void(*)())A)(); }')
        def test_policy_asm(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { asm("trap;"); }')
        def test_policy_quotes(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { int a="x"; }')
        def test_policy_unknown_call(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { system(1); }')
        def test_policy_escape(self):self.assertRaises(NumericFailure,source_policy,SOURCES['axpy']+'\\\n')
        def test_policy_fma(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { C[0]=__fmaf_rn(A[0],1.0f,B[0]); }')
        def test_policy_printf(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { printf(0); }')
        def test_policy_dynamic_parallel(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { kernel<<<1,1>>>(A,B,C,M,N,K); }')
        def test_policy_shared_barrier(self):self.assertEqual(source_policy(SIGNATURE+' { __shared__ float x[16][17]; x[threadIdx.x][0]=0.0f; __syncthreads(); }'),SIGNATURE+' { __shared__ float x[16][17]; x[threadIdx.x][0]=0.0f; __syncthreads(); }')
        def test_policy_unclosed(self):self.assertRaises(NumericFailure,source_policy,SIGNATURE+' {{ }')
        def test_normalization_single_fence(self):self.assertEqual(normalize_source('```cuda\n'+SOURCES['axpy']+'```'),SOURCES['axpy'])
        def test_normalization_multifence(self):self.assertRaises(NumericFailure,normalize_source,'```cuda\n'+SOURCES['axpy']+'```\n```a```')
        def test_normalization_plain(self):self.assertEqual(normalize_source(SOURCES['axpy']),SOURCES['axpy'])
        def test_plan_grid(self):
            p=plan_document(self.info());self.assertEqual(sum(len(g['requests']) for g in p['groups']),15)
            self.assertEqual({r['id'] for g in p['groups'] for r in g['requests']},{t+'__'+a for t in TASKS for a in ARMS})
        def test_plan_deterministic(self):self.assertEqual(canon(plan_document(self.info())),canon(plan_document(self.info())))
        def test_prompts_english(self):
            for g in plan_document(self.info())['groups']:
                for r in g['requests']:self.assertTrue(all(m['content'].isascii() for m in r['messages']))
        def test_prompt_changes_only_profile(self):
            blocks=profiles(self.info())
            for t in TASKS:
                neut=[prompt(t,blocks[a])[1]['content'].replace(blocks[a],'<HARDWARE>') for a in ARMS]
                self.assertEqual(len(set(neut)),1)
        def test_prompt_source_byte_exact(self):
            for g in plan_document(self.info())['groups']:
                for r in g['requests']:self.assertIn('----- BEGIN ORIGINAL CUDA -----\n'+SOURCES[g['task']]+'----- END ORIGINAL CUDA -----',r['messages'][1]['content'])
        def test_no_fast_math_options(self):
            self.assertIn('--fmad=false',NVRTC_OPTIONS);self.assertIn('--ftz=false',NVRTC_OPTIONS);self.assertFalse(any('use_fast_math' in v for v in NVRTC_OPTIONS))
        def test_device_arch(self):self.assertIn('--gpu-architecture=sm_86',NVRTC_OPTIONS)
        def test_launch_tail(self):self.assertEqual(launch_dims('transpose',(17,33,1)),(3,2,16,16));self.assertEqual(launch_dims('axpy',(1,257,1)),(2,1,256,1))
        def test_helper_axpy_real(self):
            a=(ct.c_float*6)(1,-1,0.0,-0.0,2**-149,-2**-149);b=(ct.c_float*6)(1,1,0.0,-0.0,0.0,0.0);c=(ct.c_float*6)()
            self.h.ref(0,a,b,c,1,6,1)
            rn=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]
            expected=b''.join(struct.pack('<f',rn(rn(1.25*x)+y)) for x,y in zip(a,b));self.assertEqual(bytes(c),expected)
        def test_helper_gemm_real(self):
            a=(ct.c_float*6)(1.0,2.0,3.0,-1.0,2.0,1.0);b=(ct.c_float*6)(1,2,3,4,5,6);c=(ct.c_float*4)()
            self.h.ref(2,a,b,c,2,2,3);self.assertEqual(list(c),[22.,28.,10.,12.])
        def test_helper_transpose_bits(self):
            values=[0,0x80000000,0x7fc01234,0xffc09876,1,0x7f800000]
            ar=(ct.c_uint32*6)(*values);b=(ct.c_float*6)();out=(ct.c_uint32*6)()
            self.h.ref(1,ar,b,out,2,3,1);self.assertEqual(list(out),[values[i] for i in (0,3,1,4,2,5)])
        def test_deterministic_data(self):
            a,b,c=self.h.case('gemm_ordered',(17,15,13),1009);x,y,z=self.h.case('gemm_ordered',(17,15,13),1009)
            self.assertEqual(bytes(a),bytes(x));self.assertEqual(bytes(c),bytes(z))
        def test_helper_input_bounds(self):
            a,b,c=self.h.case('gemm_ordered',(17,15,13),9173)
            self.assertTrue(all(math.isfinite(v) and abs(v)<=4 for v in a));self.assertTrue(all(math.isfinite(v) for v in c))
        def test_host_timer_no_gpu_false_success(self):
            value=ct.c_float();self.assertEqual(self.h.batch(None,0,0,0,1,1,1,1,1,1,1,1,None,None,ct.byref(value)),-999)
        def test_metric_identity(self):self.assertTrue(timing_metric(self.rows())['measurement_valid'])
        def test_metric_speedup(self):self.assertEqual(timing_metric(self.rows(1.5))['speedup'],1.5)
        def test_metric_session_drift(self):
            r=self.rows()
            for x in r:
                if x['session']==1:x['ratio']=1.1
            self.assertIn('between_session_ratio_change',timing_metric(r)['quality_reasons'])
        def test_metric_variation(self):
            r=self.rows()
            for i,x in enumerate(r):x['ratio']=1.0 if i%2==0 else 1.5
            self.assertIn('paired_ratio_relative_iqr',timing_metric(r)['quality_reasons'])
        def test_metric_missing(self):self.assertRaises(Blocked,timing_metric,self.rows()[:-1])
        def test_metric_nan(self):
            r=self.rows();r[0]['ratio']=float('nan');self.assertRaises(Blocked,timing_metric,r)
        def test_json_dupe(self):self.assertRaises(Blocked,parse,'{"x":1,"x":2}')
        def test_json_nan(self):self.assertRaises(Blocked,parse,'{"x":NaN}')
        def test_no_overwrite(self):
            p=self.r/'x';save(p,b'x');self.assertRaises(FileExistsError,save,p,b'y')
        def test_symlink(self):
            p=self.r/'x';p.symlink_to(self.r/'missing');self.assertRaises(Blocked,read,p)
        def test_clean_environment(self):
            with mock.patch.dict(os.environ,{'OPENAI_API_KEY':'secret','SSH_AUTH_SOCK':'secret'}):
                self.assertNotIn('OPENAI_API_KEY',clean_env());self.assertNotIn('SSH_AUTH_SOCK',clean_env())
        def test_no_retired_destination(self):
            self.assertEqual(SERVER,'root@example.invalid');self.assertEqual(module_a().SERVER,SERVER)
        def test_embedded_runtime(self):self.assertEqual(module_a().CACHED_BINARY_SHA,'67090bf56f3deb8349bd744a27c252effe910944489fd04900b0c7a744f86780')
        def test_inference_stops_early_error(self):
            a=types.SimpleNamespace();group=plan_document(self.info())['groups'][0]
            with mock.patch.dict(globals(),start_model=mock.Mock(side_effect=Blocked('load failed')),no_other_gpu=mock.Mock(),close_child=mock.Mock()) as p:
                self.assertRaises(Blocked,generate_group,a,None,group)
                self.assertTrue((self.r/'tasks/axpy/model-stopped-before-evaluation.json').is_file())
        def test_response_limit_rejected(self):
            self.assertRaises(NumericFailure,response_code,{'truncated':False,'stop_type':'limit','content':SOURCES['axpy'],'timings':{'predicted_n':4096}})
        def test_response_truncated_rejected(self):self.assertRaises(NumericFailure,response_code,{'truncated':True})
        def test_response_ok(self):self.assertEqual(response_code({'truncated':False,'stop_type':'word','content':SOURCES['axpy'],'timings':{'predicted_n':40}}),SOURCES['axpy'])
        def test_archive_roundtrip(self):
            d=self.r/'sample';save(d/'x',b'hello');rec=archive_dir(d,'sample');self.assertEqual(verify_archive(self.r/'archives/sample.tar.gz',rec)['verified_files'],1)
        def test_archive_corruption(self):
            d=self.r/'sample';save(d/'x',b'hello');rec=archive_dir(d,'sample');rec['sha256']='0'*64;self.assertRaises(Blocked,verify_archive,self.r/'archives/sample.tar.gz',rec)
        def test_archive_symlink(self):
            d=self.r/'sample';d.mkdir();(d/'x').symlink_to('/etc/passwd');self.assertRaises(Blocked,archive_dir,d,'sample')
        def test_ack_missing_blocks_next_step(self):
            with mock.patch.dict(globals(),ACK_SECONDS=0):self.assertRaises(Blocked,wait_ack,{'label':'sample','sha256':'0'*64})
        def test_ack_bad_hash(self):
            jw(self.r/'acks/sample.json',{'sha256':'1'*64});self.assertRaises(Blocked,wait_ack,{'label':'sample','sha256':'0'*64})
        def test_ack_good(self):
            jw(self.r/'acks/sample.json',{'sha256':'0'*64});wait_ack({'label':'sample','sha256':'0'*64})
        def test_public_ancestors(self):
            public_dirs(self.r/'a/b/c');self.assertEqual(stat.S_IMODE((self.r/'a').stat().st_mode),0o755)
        def test_public_outside_refused(self):self.assertRaises(Blocked,public_dirs,Path(self.t.name)/'outside')
        def test_process_lifecycle(self):
            p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
            try:self.assertTrue(alive({'pid':p.pid,'ticks':cgroup_start(p.pid)}));close_child(p);self.assertIsNotNone(p.poll())
            finally:close_child(p)
        def test_command_timeout_real_child(self):
            rc=command([sys.executable,'-c','import time;time.sleep(30)'],self.r/'timeout.log',0.05)
            self.assertEqual(rc,124)
        def test_install_code_syntax(self):compile(install_text('0'*64),'install','exec')
        def test_phase_order_and_15_slots_with_mocks(self):
            plan=plan_document(self.info());h=self.so;orig=ROOT;events=[]
            def comp(source,dest):
                public_dirs(dest);save(dest/'kernel.cubin',source.encode());save(dest/'kernel.ptx',source.encode());return {'ok':True}
            def numeric(task,cubin,dest,helper,mode='check',**kwargs):
                public_dirs(dest);events.append(mode)
                return {'ok':True,**({'rows':self.rows()} if mode=='time' else {'bitwise_pass':True})}
            allout=[]
            with mock.patch.dict(globals(),compile_candidate=comp,run_numeric=numeric,
                    sanitized_check=lambda *a,**kw:{'passed':True},no_other_gpu=lambda:None,telemetry=lambda:{'utc':'test'}):
                for group in plan['groups']:
                    task=group['task'];d=orig/'preflight'/task;save(d/'baseline/kernel.cubin',SOURCES[task].encode());save(d/'baseline/kernel.ptx',SOURCES[task].encode());save(d/'identity/kernel.cubin',SOURCES[task].encode())
                    generated=[]
                    for req in group['requests']:
                        arm=req['condition'];save(orig/'tasks'/task/'generation'/arm/'candidate.cu',SOURCES[task].encode())
                        generated.append({'id':req['id'],'task':task,'condition':arm,'generation_status':'saved','source_sha256':sha(SOURCES[task].encode())})
                    allout+=evaluate_group(group,generated,h,{})
                save(orig/'setup/protocol.json',canon(plan));summary=write_summary(allout)
            self.assertEqual(len(allout),15);self.assertEqual(summary['valid_size_measurements'],30)
            self.assertEqual(len(events),60);self.assertTrue(all(x=='time' for x in events))
        def test_generation_failure_not_evaluated(self):
            group=plan_document(self.info())['groups'][0];public_dirs(self.r/'tasks/axpy')
            bad=[{'id':'axpy__'+a,'task':'axpy','condition':a,'generation_status':'invalid_generation'} for a in ARMS]
            with mock.patch.dict(globals(),compile_candidate=mock.Mock(side_effect=AssertionError('must not compile'))):
                out=evaluate_group(group,bad,self.so,{});self.assertEqual(len(out),5);self.assertTrue(all(o['stage']=='generation_failed' for o in out))
        def test_generation_all_five_and_stop(self):
            group=plan_document(self.info())['groups'][0]
            class Api:
                SAMPLING=module_a().SAMPLING
                def api(s,path,body=None,timeout=60):
                    if path=='/apply-template':return {'prompt': ''.join(m['content'] for m in body['messages'])}
                    if path=='/tokenize':return {'tokens':[1,2,3]}
                    if path=='/completion':return {'truncated':False,'stop_type':'word','tokens_evaluated':3,'content':SOURCES['axpy'],'timings':{'predicted_n':50}}
                    raise AssertionError(path)
            stop=mock.Mock();start=mock.Mock(return_value=object())
            with mock.patch.dict(globals(),start_model=start,close_child=stop,no_other_gpu=lambda:None):
                r=generate_group(Api(),None,group)
            self.assertEqual(len(r),5);self.assertEqual(STATE['generation_calls'],5);self.assertEqual(start.call_count,1)
            self.assertTrue(all(x['generation_status']=='saved' for x in r));self.assertEqual(stop.call_count,1)
        def test_generation_timeout_is_not_retried(self):
            group=plan_document(self.info())['groups'][0]
            class Api:
                SAMPLING=module_a().SAMPLING
                def api(s,path,body=None,timeout=60):
                    if path=='/apply-template':return {'prompt': ''.join(m['content'] for m in body['messages'])}
                    if path=='/tokenize':return {'tokens':[1,2,3]}
                    raise TimeoutError('test timeout')
            start=mock.Mock(return_value=object())
            with mock.patch.dict(globals(),start_model=start,close_child=mock.Mock(),no_other_gpu=lambda:None):r=generate_group(Api(),None,group)
            self.assertEqual(STATE['generation_calls'],5);self.assertEqual(start.call_count,5)
            self.assertTrue(all(x['generation_status']=='transport_or_timeout' for x in r))
        def test_stale_ack_cannot_advance(self):
            jw(self.r/'acks/test.json',{'sha256':'1'*64})
            self.assertRaises(Blocked,wait_ack,{'label':'test','sha256':'2'*64})
        def test_nonce_path_declarations_refused(self):
            self.assertRaises(NumericFailure,source_policy,SIGNATURE+' { } __device__ int x; { }')
        def test_no_result_without_full_grid(self):self.assertRaises(Blocked,write_summary,[])
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    need(result.wasSuccessful(),'Local tests failed')
    print('GPU_CODE_PILOT_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=POLICY_ARCHIVE_ACCOUNTING_MOCK_GPU_FLOW_REAL_HOST_FP32_HELPER_AND_CHILD_TIMEOUT; NO_REAL_SSH_NVRTC_CUDA_GPU_OR_LLM_EXECUTION')

if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('INTERRUPTED; results retained',file=sys.stderr);sys.exit(130)
    except Exception as exc:print('GPU001_BLOCKED: '+type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(2)
