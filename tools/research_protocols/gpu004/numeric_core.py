#!/usr/bin/env python3
"""GPU002: PolyBench/ACC-derived strict CUDA kernel optimization, six tasks, 90 requests.
Single authorized Runpod; no retired server connections. See PROTOCOL for adaptations.
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
import argparse,base64,contextlib,csv,ctypes as ct,gzip,hashlib,http.client,io,json,math,os,random,re,resource,shlex,shutil,signal,socket,stat,statistics,subprocess,sys,tarfile,tempfile,time,traceback,types,unittest,urllib.request,uuid
from pathlib import Path
from unittest import mock

PILOT_SHA = '1af5b19127cd3fc959915dca357b20f2c8ed4ee47043206ad7354e83f7125452'
PILOT_EMBED = _public.encoded_module('pilot.py')
UPSTREAM_LICENSE='Copyright (C) 2013-2016 University of Delaware.\n\nRedistribution and use in source and binary forms, with or without\nmodification, are permitted provided that the following conditions are met:\n\n1. Redistributions of source code must retain the above copyright notice,\nthis list of conditions and the following disclaimer.\n\n2. Redistributions in binary form must reproduce the above copyright notice,\nthis list of conditions and the following disclaimer in the documentation\nand/or other materials provided with the distribution.\n\n3. Neither the name of the copyright holder nor the names of its contributors\nmay be used to endorse or promote products derived from this software without\nspecific prior written permission.\n\nTHIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"\nAND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE\nIMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE\nDISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE\nFOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL\nDAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR\nSERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER\nCAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,\nOR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE\nOF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.\n\n\nPolyBench/ACC is based on PolyBench. PolyBench has the following license:\n\nOHIO STATE UNIVERSITY SOFTWARE DISTRIBUTION LICENSE\n\nPolyBench/C, a collection of benchmarks containing static control\nparts (the "Software")\nCopyright (c) 2010-2016, Ohio State University. All rights reserved.\n\nThe Software is available for download and use subject to the terms\nand conditions of this License.  Access or use of the Software\nconstitutes acceptance and agreement to the terms and conditions of\nthis License.  Redistribution and use of the Software in source and\nbinary forms, with or without modification, are permitted provided\nthat the following conditions are met:\n\n1. Redistributions of source code must retain the above copyright\nnotice, this list of conditions and the capitalized paragraph below.\n\n2. Redistributions in binary form must reproduce the above copyright\nnotice, this list of conditions and the capitalized paragraph below in\nthe documentation and/or other materials provided with the\ndistribution.\n\n3. The name of Ohio State University, or its faculty, staff or\nstudents may not be used to endorse or promote products derived from\nthe Software without specific prior written permission.\n\nThis software was produced with support from the U.S. Defense Advanced\nResearch Projects Agency (DARPA), the U.S. Department of Energy (DoE)\nand the U.S. National Science Foundation. Nothing in this work should\nbe construed as reflecting the official policy or position of the\nDefense Department, the United States government or Ohio State\nUniversity.\n\nTHIS SOFTWARE HAS BEEN APPROVED FOR PUBLIC RELEASE, UNLIMITED\nDISTRIBUTION.  THE SOFTWARE IS PROVIDED "AS IS" AND WITHOUT ANY\nEXPRESS, IMPLIED OR STATUTORY WARRANTIES, INCLUDING, BUT NOT LIMITED\nTO, WARRANTIES OF ACCURACY, COMPLETENESS, NONINFRINGEMENT,\nMERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.\nACCESS OR USE OF THE SOFTWARE IS ENTIRELY AT THE USER\'S RISK.  IN NO\nEVENT SHALL OHIO STATE UNIVERSITY OR ITS FACULTY, STAFF OR STUDENTS BE\nLIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR\nCONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF\nSUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR\nBUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,\nWHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE\nOR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN\nIF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  THE SOFTWARE USER SHALL\nINDEMNIFY, DEFEND AND HOLD HARMLESS OHIO STATE UNIVERSITY AND ITS\nFACULTY, STAFF AND STUDENTS FROM ANY AND ALL CLAIMS, ACTIONS, DAMAGES,\nLOSSES, LIABILITIES, COSTS AND EXPENSES, INCLUDING ATTORNEYS\' FEES AND\nCOURT COSTS, DIRECTLY OR INDIRECTLY ARISING OUT OF OR IN CONNECTION\nWITH ACCESS OR USE OF THE SOFTWARE.\n'

def _load_support():
    return _public.load_module('pilot.py', PILOT_SHA)
P=_load_support()
ROOT=Path('/workspace/gpu-code-polybench-002-v1')
LOCAL_REL=Path('workspace/cpu-conditioned-llm-optimization/runs/gpu-code-polybench-002-v1')
VERSION='gpu002-polybench-six-strict-v1'
COMMIT='70ea4ca9047dc4ec9c3ca79b4c91b3b2cc1510e7'
UPSTREAM='https://raw.githubusercontent.com/cavazos-lab/PolyBench-ACC/'+COMMIT+'/'
CAP=8192
SEEDS=(69001,69002,69003)
ARMS=('P0','S1','S2','W1','W2')
TOTAL=90
RUN_SECONDS=24*3600
ACK_SECONDS=12*3600
REQUEST_SECONDS=900
MODEL=P.MODEL
Blocked=P.Blocked
NumericFailure=P.NumericFailure
need=P.need;require=P.require;sha=P.sha;canon=P.canon;parse=P.parse;save=P.save;read=P.read;hfile=P.hfile;jw=P.jw;now=P.now

def configure(root=None):
    global ROOT
    if root is not None:ROOT=Path(root)
    P.ROOT=ROOT;P.LOCAL_REL=LOCAL_REL;P.VERSION=VERSION;P.PORT=11578
    P.__file__=__file__;P.RUN_SECONDS=RUN_SECONDS;P.ACK_SECONDS=ACK_SECONDS
    P.MAX_GENERATIONS=TOTAL;P.CAP=CAP;P.REQUEST_SECONDS=REQUEST_SECONDS
configure()

# Canonical token-equivalent copies of the six upstream CUDA functions.
# Redistribution covered by the upstream LICENSE embedded in the distributed runner.
SPECS={
'gemm':dict(path='CUDA/linear-algebra/kernels/gemm/gemm.cu',blob='30629e95203d75a1af8e06e667237633044a4393',function='gemm_kernel',base=[32,8],kind=0,perf=[(128,128,128),(256,256,256)],
source='''__global__ void gemm_kernel(int ni, int nj, int nk, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{ int j = blockIdx.x * blockDim.x + threadIdx.x; int i = blockIdx.y * blockDim.y + threadIdx.y;
if ((i < _PB_NI) && (j < _PB_NJ)) { c[i * NJ + j] *= beta; int k; for(k=0; k < _PB_NK; k++) { c[i * NJ + j] += alpha * a[i * NK + k] * b[k * NJ +j]; } } }'''),
'gesummv':dict(path='CUDA/linear-algebra/kernels/gesummv/gesummv.cu',blob='5556adf155d37d5acdf7c7a6216d0db92eb74a71',function='gesummv_kernel',base=[256,1],kind=1,perf=[(1024,1024,1),(2048,2048,1)],
source='''__global__ void gesummv_kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{ int i = blockIdx.x * blockDim.x + threadIdx.x; if (i < _PB_N) { int j; for(j = 0; j < _PB_N; j++) { tmp[i] += A[i * N + j] * x[j]; y[i] += B[i * N + j] * x[j]; } y[i] = alpha * tmp[i] + beta * y[i]; } }'''),
'syrk':dict(path='CUDA/linear-algebra/kernels/syrk/syrk.cu',blob='a80e1238bd577de83a97886fbe7ef5a7fb84572f',function='syrk_kernel',base=[32,8],kind=2,perf=[(256,256,1),(512,512,1)],
source='''__global__ void syrk_kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *c)
{ int j = blockIdx.x * blockDim.x + threadIdx.x; int i = blockIdx.y * blockDim.y + threadIdx.y; if ((i < _PB_NI) && (j < _PB_NI)) { c[i * NI + j] *= beta; int k; for(k=0; k < _PB_NJ; k++) { c[i * NI + j] += alpha * a[i * NJ + k] * a[j * NJ + k]; } } }'''),
'syr2k':dict(path='CUDA/linear-algebra/kernels/syr2k/syr2k.cu',blob='b400bcb98a2ba40319ce6f57f50de3fb431e61d5',function='syr2k_kernel',base=[32,8],kind=3,perf=[(256,256,1),(512,512,1)],
source='''__global__ void syr2k_kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{ int j = blockIdx.x * blockDim.x + threadIdx.x; int i = blockIdx.y * blockDim.y + threadIdx.y; if ((i < NI) && (j < NI)) { c[i * NI + j] *= beta; int k; for(k = 0; k < NJ; k++) { c[i * NI + j] += alpha * a[i * NJ + k] * b[j * NJ + k] + alpha * b[i * NJ + k] * a[j * NJ + k]; } } }'''),
'convolution-2d':dict(path='CUDA/stencils/convolution-2d/2DConvolution.cu',blob='1b9a53973771911995a472d3551e5a3680c149ff',function='convolution2D_kernel',base=[32,8],kind=4,perf=[(1024,1024,1),(2048,2048,1)],
source='''__global__ void convolution2D_kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{ int j = blockIdx.x * blockDim.x + threadIdx.x; int i = blockIdx.y * blockDim.y + threadIdx.y;
DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;
c11 = +0.2; c21 = +0.5; c31 = -0.8; c12 = -0.3; c22 = +0.6; c32 = -0.9; c13 = +0.4; c23 = +0.7; c33 = +0.10;
if ((i < _PB_NI-1) && (j < _PB_NJ-1) && (i > 0) && (j > 0)) {
B[i * NJ + j] = c11 * A[(i - 1) * NJ + (j - 1)] + c21 * A[(i - 1) * NJ + (j + 0)] + c31 * A[(i - 1) * NJ + (j + 1)]
+ c12 * A[(i + 0) * NJ + (j - 1)] + c22 * A[(i + 0) * NJ + (j + 0)] + c32 * A[(i + 0) * NJ + (j + 1)]
+ c13 * A[(i + 1) * NJ + (j - 1)] + c23 * A[(i + 1) * NJ + (j + 0)] + c33 * A[(i + 1) * NJ + (j + 1)]; } }'''),
'convolution-3d':dict(path='CUDA/stencils/convolution-3d/3DConvolution.cu',blob='569f50bca326a836d79108416aa2c8b5d4c2dc85',function='convolution3D_kernel',base=[32,8],kind=5,perf=[(64,64,64),(128,128,128)],
source='''__global__ void convolution3D_kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{ int k = blockIdx.x * blockDim.x + threadIdx.x; int j = blockIdx.y * blockDim.y + threadIdx.y;
DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;
c11 = +2; c21 = +5; c31 = -8; c12 = -3; c22 = +6; c32 = -9; c13 = +4; c23 = +7; c33 = +10;
if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0)) {
B[i*(NK * NJ) + j*NK + k] = c11 * A[(i - 1)*(NK * NJ) + (j - 1)*NK + (k - 1)] + c13 * A[(i + 1)*(NK * NJ) + (j - 1)*NK + (k - 1)]
+ c21 * A[(i - 1)*(NK * NJ) + (j - 1)*NK + (k - 1)] + c23 * A[(i + 1)*(NK * NJ) + (j - 1)*NK + (k - 1)]
+ c31 * A[(i - 1)*(NK * NJ) + (j - 1)*NK + (k - 1)] + c33 * A[(i + 1)*(NK * NJ) + (j - 1)*NK + (k - 1)]
+ c12 * A[(i + 0)*(NK * NJ) + (j - 1)*NK + (k + 0)] + c22 * A[(i + 0)*(NK * NJ) + (j + 0)*NK + (k + 0)]
+ c32 * A[(i + 0)*(NK * NJ) + (j + 1)*NK + (k + 0)] + c11 * A[(i - 1)*(NK * NJ) + (j - 1)*NK + (k + 1)]
+ c13 * A[(i + 1)*(NK * NJ) + (j - 1)*NK + (k + 1)] + c21 * A[(i - 1)*(NK * NJ) + (j + 0)*NK + (k + 1)]
+ c23 * A[(i + 1)*(NK * NJ) + (j + 0)*NK + (k + 1)] + c31 * A[(i - 1)*(NK * NJ) + (j + 1)*NK + (k + 1)]
+ c33 * A[(i + 1)*(NK * NJ) + (j + 1)*NK + (k + 1)]; } }''')}

TASKS=tuple(SPECS)
HEADER_PINS={
'gemm':'7988b06e272bd31024781f312e6f977b805fe39c',
'gesummv':'7d6d879a00a878566ab1a48d0edd85b8f27f4b69',
'syrk':'6eeba01a44184a7c217a29bbcb9ede15d1598334',
'syr2k':'16c12eda1f821ca65bec0b4cea576b27fff2e6a5',
'convolution-2d':'86b4fcf7d5ca486e5ad7e186ce440488f6f1178f',
'convolution-3d':'d72f5305e3929e809a454467edc0819012ea0e26'}

def tokens(text):
    text=re.sub(r'/\*.*?\*/|//[^\n]*',' ',text,flags=re.S)
    return re.findall(r'[A-Za-z_]\w*|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?[fFuUlL]*|[^\s]',text)

def extract_kernel(raw,task):
    text=raw.decode('utf-8');masked=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S)
    spec=SPECS[task];pat=r'__global__\s+void\s+'+spec['function']+r'\s*\('
    ms=list(re.finditer(pat,masked));need(len(ms)==1,'Original device function missing or ambiguous: '+task)
    start=ms[0].start();pos=masked.index('{',ms[0].end());depth=1;end=pos+1
    while depth and end<len(masked):
        depth+=(masked[end]=='{')-(masked[end]=='}');end+=1
    need(depth==0,'Unbalanced upstream function')
    body=text[start:end]
    need(tokens(body)==tokens(spec['source']),'Upstream kernel differs from reviewed token-level contract: '+task)
    adapted='extern "C" '+re.sub(r'\b'+spec['function']+r'\b','kernel',body,count=1)+'\n'
    return adapted,dict(original_function=spec['function'],original_function_sha256=sha(body.encode()),
        original_line_start=text.count('\n',0,start)+1,original_line_end=text.count('\n',0,end)+1,
        adapter='Only extern C linkage and symbol name kernel added; device body unchanged',adapted_source_sha256=sha(adapted.encode()))

def baseline_source(task):
    path=ROOT/'setup/sources'/(task+'.cu')
    return read(path).decode() if path.is_file() else 'extern "C" '+SPECS[task]['source'].replace(SPECS[task]['function'],'kernel',1)+'\n'

def signature(task):return baseline_source(task).split('{',1)[0].strip()

def small_shapes(task):
    if task=='gesummv':return [(1,1,1),(17,17,1),(257,257,1)]
    if task=='gemm':return [(1,1,1),(7,13,11),(17,33,19)]
    if task=='convolution-3d':return [(1,1,1),(5,7,9),(9,17,33)]
    return [(1,1,1),(7,13,1),(33,17,1)]

def shapes(task):return small_shapes(task)+[tuple(x) for x in SPECS[task]['perf']]

def shape_id(shape):return 'x'.join(str(x) for x in shape)

def allowed_blocks(task):
    return [(64,1),(128,1),(256,1),(512,1)] if task=='gesummv' else [(32,8),(16,16),(64,4),(128,2),(256,1),(32,4),(64,2),(128,1)]

def candidate_source(text,task):
    require(isinstance(text,str) and 0<len(text)<=65536,'Empty/oversized response')
    text=text.strip()
    if text.startswith('```'):
        m=re.fullmatch(r'```(?:cuda|cpp|c\+\+|c)?\s*\n(.*?)\n```',text,re.S|re.I)
        require(m is not None and '```' not in m[1],'Invalid outer fence');text=m[1].strip()
    block=tuple(SPECS[task]['base'])
    first=text.splitlines()[0]
    if first.startswith('// BLOCK '):
        m=re.fullmatch(r'// BLOCK (\d+) (\d+)',first);require(m is not None,'Invalid block declaration')
        block=tuple(map(int,m.groups()));text='\n'.join(text.splitlines()[1:]).strip()
    require(block in allowed_blocks(task),'Block outside preregistered choices')
    old=P.SIGNATURE;old_calls=set(P.ALLOWED_CALLS)
    try:
        P.SIGNATURE=signature(task);P.ALLOWED_CALLS.add('DATA_TYPE')
        P.source_policy(text+'\n')
    finally:P.SIGNATURE=old;P.ALLOWED_CALLS=old_calls
    return text+'\n',list(block)

def definitions(shape):
    m,n,k=shape
    return f'''#define DATA_TYPE float
#define NI {m}
#define NJ {n}
#define NK {k}
#define N {m}
#define _PB_NI ni
#define _PB_NJ nj
#define _PB_NK nk
#define _PB_N n
'''

def dimensions(task,shape):
    m,n,k=shape
    if task=='gemm':return [m*k,k*n,m*n],{2}
    if task=='gesummv':return [m*m,m*m,m,m,m],{2,4}
    if task=='syrk':return [m*n,m*m],{1}
    if task=='syr2k':return [m*n,m*n,m*m],{2}
    size=m*n*(k if task=='convolution-3d' else 1);return [size,size],{1}

def scalar_args(task,shape,ptrs,alpha,beta,slicevar):
    m,n,k=shape;I=ct.c_int;F=ct.c_float;Q=ct.c_uint64;p=[Q(x) for x in ptrs]
    if task=='gemm':return [I(m),I(n),I(k),F(alpha),F(beta),*p]
    if task=='gesummv':return [I(m),F(alpha),F(beta),*p]
    if task in ('syrk','syr2k'):return [I(m),I(n),F(alpha),F(beta),*p]
    if task=='convolution-2d':return [I(m),I(n),*p]
    return [I(m),I(n),I(k),*p,slicevar]

def grids(task,shape,block):
    m,n,k=shape;bx,by=block
    x,y=(m,1) if task=='gesummv' else (m,m) if task in ('syrk','syr2k') else (k,n) if task=='convolution-3d' else (n,m)
    return ((x+bx-1)//bx,(y+by-1)//by,bx,by)

def public_fetch(path,pin):
    errors=[]
    endpoints=[(UPSTREAM+path,False),('https://api.github.com/repos/cavazos-lab/PolyBench-ACC/git/blobs/'+pin,True)]
    for url,is_api in endpoints:
        req=urllib.request.Request(url,headers={'User-Agent':'cpucond-gpu002-source-intake/1','Accept':'application/vnd.github+json' if is_api else '*/*'})
        try:
            with urllib.request.urlopen(req,timeout=60) as f:raw=f.read(2*1024**2+1)
        except (OSError,TimeoutError) as exc:errors.append(type(exc).__name__+': '+str(exc));continue
        need(len(raw)<=2*1024**2,'Oversized upstream input')
        if is_api:
            obj=parse(raw);need(obj.get('sha')==pin and obj.get('encoding')=='base64','Unexpected source API response')
            raw=base64.b64decode(''.join(obj['content'].split()),validate=True)
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pin,'Upstream Git blob mismatch: '+path)
        return raw
    raise Blocked('Cannot retrieve pinned source: '+path+'; '+repr(errors))

def intake():
    manifest={};records={}
    files={'LICENSE':'c6e212c6e641e5a25197398fd04d3e7183ab423f','README.md':'57b2ed79c4ee4f78c560995cb893557f88fd7f6d'}
    files.update({s['path']:s['blob'] for s in SPECS.values()})
    for task,pin in HEADER_PINS.items():files[SPECS[task]['path']+'h']=pin
    for path,pin in files.items():
        raw=public_fetch(path,pin);save(ROOT/'setup/upstream'/path,raw)
        manifest[path]={'git_blob_sha1':pin,'sha256':sha(raw),'bytes':len(raw)}
    for task,s in SPECS.items():
        raw=read(ROOT/'setup/upstream'/s['path']);src,rec=extract_kernel(raw,task)
        candidate_source(src,task);save(ROOT/'setup/sources'/(task+'.cu'),src.encode());records[task]=rec
        hdr=read(ROOT/'setup/upstream'/(s['path']+'h')).decode()
        for label,shape in zip(('MINI_DATASET','SMALL_DATASET'),s['perf']):
            mm=re.search(r'#\s*ifdef\s+'+label+r'\b(.*?)#\s*endif',hdr,re.S);need(mm is not None,'Missing upstream size block')
            vals={a:int(v) for a,v in re.findall(r'#\s*define\s+(NI|NJ|NK|N)\s+(\d+)',mm[1])}
            actual=(vals['N'],vals['N'],1) if task=='gesummv' else (vals['NI'],vals['NJ'],vals.get('NK',1))
            need(actual==tuple(shape),'Reviewed benchmark size differs from original header')
        for axis,v in zip(('X','Y'),s['base']):
            need(re.search(r'#define DIM_THREAD_BLOCK_'+axis+r'\s+'+str(v)+r'\b',hdr) is not None,'Original block dimensions changed')
    jw(ROOT/'setup/upstream-manifest.json',{'repository':'cavazos-lab/PolyBench-ACC','commit':COMMIT,'files':manifest,'extractions':records})
    save(ROOT/'setup/LICENSE',UPSTREAM_LICENSE.encode())
    return manifest

PROTOCOL={
 'cohort':VERSION,'suite':'PolyBench/ACC-derived strict CUDA subset','upstream_commit':COMMIT,
 'citation':'Grauer-Gray et al. Auto-tuning a High-Level Language Targeted to GPU Codes. InPar 2012.',
 'selection':'Six reviewed single-entry CUDA programs: 4 linear algebra and 2 stencils. Fixed before any GPU002 generation; not all CUDA benchmarks.',
 'exclusions':'All other PolyBench/ACC programs are outside this first cohort: multiple device functions, iterative multi-stage graphs or unimplemented validation adapters. No post-generation task selection.',
 'preregistration_scope':'Frozen before GPU002 generation, after reviewing GPU001; not externally preregistered',
 'unit_of_analysis':'Six kernels, with nested seeds and sizes. 180 possible size measurements are not 180 independent benchmarks',
 'tasks':list(TASKS),'candidate_slots':TOTAL,'generation_seeds':list(SEEDS),'arms':list(ARMS),'samples_per_task_arm':3,
 'model':MODEL,'model_unchanged':True,'context':32768,'max_output_tokens':CAP,'request_wall_seconds':REQUEST_SECONDS,
 'actual_host':'A40 only; no Cherry connections','representation':'CUDA device kernel -> CUDA device kernel, optional enumerated block shape',
 'launch_policy':'Optional first comment // BLOCK X Y; grid recalculated by trusted host; convolution-3d retains original host i-slice launch loop',
 'strict_semantics':'FP32, no FMA/reassociation/fast-math/TF32; compare all live-out bytes; finite selected tests, not formal equivalence',
 'baseline':'Original upstream CUDA body, extern C and symbol normalization only; same compiler, macro shapes, reset and timing path as candidate',
 'host_adaptations':[
  'Original .cu/.cuh saved. Original executable and percentage-difference checker are NOT used.',
  'NI/NJ/NK/N remain compile-time strides; _PB macros use runtime arguments; logical dimensions equal allocated extents in tested cases.',
  'Rectangular launch grid uses x=columns,y=rows; upstream GEMM/2DConv host reverses extents. Device arithmetic unchanged.',
  'gesummv original GPU tmp/y inputs uninitialized by its host: explicitly zero-initialize both before every invocation.',
  'syr2k original CPU sums two products separately but GPU sums them before accumulation: the strict oracle follows the CUDA grouping.',
  '2D convolution CUDA term order differs from original CPU loop: oracle follows the CUDA expression order.',
  'Convolution outputs initialized; boundaries must remain bitwise unchanged. Full output and scratch state is verified.',
  '3D convolution repeated offset terms retained exactly; not repaired into another stencil.',
  'Performance sizes use upstream MINI/SMALL extents; extra ragged correctness sizes and initialized-data streams are ours, not claims of original published timings.'],
 'measurement':'CUDA event time per full invocation, output reset excluded before EACH invocation; average 1..128 invocation durations; hot/reset buffers; original-vs-candidate AB/BA',
 'numerical_inputs':'Stock-like initialization plus two deterministic signed finite FP32 input streams including selected signed zero/subnormal cases; gesummv tmp/y start +0.',
 'timing_input':'seed=4327; output is restored each invocation; no accumulating overflow across repetitions',
 'timing_repetitions':'2 sessions x 8 AB/BA pairs; baseline-only calibration 5ms target with max128; candidate cannot affect repetitions',
 'sanitizers':'memcheck/initcheck/racecheck/synccheck on largest small ragged shape for all 3 data seeds; bitwise checks also on all performance shapes',
 'unchanged_control':'Separate compile of same source + original block, numerical check, contemporaneous identity timings',
 'positive_control':'Original body with an alternate allowed block must also pass; this checks launch flexibility, not a promised speedup',
 'retry_policy':'No selective regeneration or remeasurement; distinct 3 seeds fixed beforehand. Ordinary candidate failures retained; infrastructure failures block.',
 'scope':'First main-data cohort, not whole GPU study and not comparison to cuBLAS/CUTLASS; no performance significance claim from a 1.02 threshold alone',
 'storage':'Ephemeral Runpod; hash-verified WSL checkpoint ACK at setup and every generation/evaluation group; wait up to12h; run cap24h; no Pod deletion'
}

HELPER='\n#include <cstdint>\n#include <cstring>\n#include <cmath>\n#include <cfenv>\n#include <dlfcn.h>\n#if defined(__x86_64__)\n#include <xmmintrin.h>\n#endif\nstatic void fp_mode() {\n    std::fesetround(FE_TONEAREST);\n#if defined(__x86_64__)\n    _mm_setcsr(_mm_getcsr() & ~(unsigned((1u<<15)|(1u<<6))));\n#endif\n}\nstatic float mul(float a,float b){volatile float r=a*b;return r;}\nstatic float add(float a,float b){volatile float r=a+b;return r;}\nextern "C" void make_data(float *a,int n,uint32_t seed,int transpose) {\n    fp_mode();uint32_t x=seed?seed:1;\n    const uint32_t special[]={0,0x80000000,1,0x80000001,0x007fffff,0x00800000,\n        0x80800000,0x3f800001,0xbf800001,0x3f7fffff,0x33800000,0xb3800000};\n    for(int i=0;i<n;++i){x^=x<<13;x^=x>>17;x^=x<<5;\n        uint32_t bits=(x&0x807fffffu) | (uint32_t(120+(x%8))<<23);\n        if(i%13==0)bits=special[(i/13+seed)%12];\n        if(transpose && i%37==0)bits=x; // transpose copies all bit patterns.\n        std::memcpy(a+i,&bits,4);\n    }\n}\nextern "C" void reference(int task,const float*a,const float*b,float*c,int M,int N,int K){\n    fp_mode();\n    if(task==0){for(int i=0;i<M*N;++i)c[i]=add(mul(1.25f,a[i]),b[i]);}\n    else if(task==1){for(int i=0;i<M;++i)for(int j=0;j<N;++j)std::memcpy(c+j*M+i,a+i*N+j,4);}\n    else {for(int i=0;i<M;++i)for(int j=0;j<N;++j){float v=0.0f;\n        for(int k=0;k<K;++k)v=add(v,mul(a[i*K+k],b[k*N+j]));c[i*N+j]=v;}}\n}\nextern "C" int cuda_batch(void*func,uint64_t A,uint64_t B,uint64_t C,int M,int N,int K,\n                        unsigned gx,unsigned gy,unsigned bx,unsigned by,int count,void*start,void*stop,float*out) {\n    using Launch=int(*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**);\n    using Record=int(*)(void*,void*);using Sync=int(*)(void*);using Elapsed=int(*)(float*,void*,void*);\n    auto launch=(Launch)dlsym(RTLD_DEFAULT,"cuLaunchKernel");\n    auto record=(Record)dlsym(RTLD_DEFAULT,"cuEventRecord");\n    auto sync=(Sync)dlsym(RTLD_DEFAULT,"cuEventSynchronize");\n    auto elapsed=(Elapsed)dlsym(RTLD_DEFAULT,"cuEventElapsedTime");\n    if(!launch||!record||!sync||!elapsed)return -999;\n    void*params[]={&A,&B,&C,&M,&N,&K};int rc=record(start,nullptr);if(rc)return rc;\n    for(int i=0;i<count;++i){rc=launch(func,gx,gy,1,bx,by,1,0,nullptr,params,nullptr);if(rc)return rc;}\n    if((rc=record(stop,nullptr)))return rc;if((rc=sync(stop)))return rc;\n    return elapsed(out,start,stop);\n}\nextern "C" void suite_init(int t,float*a,float*b,float*c,float*d,float*e,int m,int n,int k,int seed){\n fp_mode();\n if(t==1){for(int i=0;i<m;++i){c[i]=0.0f;e[i]=0.0f;}}\n if(seed!=0)return;\n if(t==0){for(int i=0;i<m;++i)for(int j=0;j<k;++j)a[i*k+j]=float(i*j)/float(m);\n for(int i=0;i<k;++i)for(int j=0;j<n;++j)b[i*n+j]=float(i*j)/float(m);\n for(int i=0;i<m;++i)for(int j=0;j<n;++j)c[i*n+j]=float(i*j)/float(m);}\n if(t==1){for(int i=0;i<m;++i){d[i]=float(i)/float(m);for(int j=0;j<m;++j){a[i*m+j]=float(i*j)/float(m);b[i*m+j]=float(i*j)/float(m);}}}\n if(t==2||t==3){for(int i=0;i<m;++i)for(int j=0;j<n;++j){a[i*n+j]=float(i*j)/float(m);if(t==3)b[i*n+j]=float(i*j)/float(m);}\n float*out=t==2?b:c;for(int i=0;i<m;++i)for(int j=0;j<m;++j)out[i*m+j]=float(i*j)/float(m);}\n if(t==4){uint32_t x=17;for(int i=0;i<m*n;++i){x=x*1664525u+1013904223u;a[i]=float(x>>8)/16777216.0f;b[i]=0.25f;}}\n if(t==5){for(int i=0;i<m;++i)for(int j=0;j<n;++j)for(int z=0;z<k;++z){a[(i*n+j)*k+z]=float(i%12+2*(j%7)+3*(z%13));b[(i*n+j)*k+z]=0.25f;}}\n}\nextern "C" void suite_ref(int t,const float*a,float*b,float*c,float*d,float*e,int m,int n,int k,float al,float be){\n fp_mode();\n if(t==0){for(int i=0;i<m;++i)for(int j=0;j<n;++j){float v=mul(c[i*n+j],be);for(int z=0;z<k;++z)v=add(v,mul(mul(al,a[i*k+z]),b[z*n+j]));c[i*n+j]=v;}}\n if(t==1){for(int i=0;i<m;++i){float v=c[i],w=e[i];for(int j=0;j<m;++j){v=add(v,mul(a[i*m+j],d[j]));w=add(w,mul(b[i*m+j],d[j]));}c[i]=v;e[i]=add(mul(al,v),mul(be,w));}}\n if(t==2){for(int i=0;i<m;++i)for(int j=0;j<m;++j){float v=mul(b[i*m+j],be);for(int z=0;z<n;++z)v=add(v,mul(mul(al,a[i*n+z]),a[j*n+z]));b[i*m+j]=v;}}\n if(t==3){for(int i=0;i<m;++i)for(int j=0;j<m;++j){float v=mul(c[i*m+j],be);for(int z=0;z<n;++z){float x=mul(mul(al,a[i*n+z]),b[j*n+z]);float y=mul(mul(al,b[i*n+z]),a[j*n+z]);v=add(v,add(x,y));}c[i*m+j]=v;}}\n if(t==4){const float coef[]={.2f,.5f,-.8f,-.3f,.6f,-.9f,.4f,.7f,.10f};\n for(int i=1;i<m-1;++i)for(int j=1;j<n-1;++j){float v=mul(coef[0],a[(i-1)*n+j-1]);for(int z=1;z<9;++z)v=add(v,mul(coef[z],a[(i+z/3-1)*n+(j+z%3-1)]));b[i*n+j]=v;}}\n if(t==5){const float coef[]={2,4,5,7,-8,10,-3,6,-9,2,4,5,7,-8,10};\n const int di[]={-1,1,-1,1,-1,1,0,0,0,-1,1,-1,1,-1,1};\n const int dj[]={-1,-1,-1,-1,-1,-1,-1,0,1,-1,-1,0,0,1,1};\n const int dk[]={-1,-1,-1,-1,-1,-1,0,0,0,1,1,1,1,1,1};\n for(int i=1;i<m-1;++i)for(int j=1;j<n-1;++j)for(int z=1;z<k-1;++z){float v=mul(coef[0],a[((i+di[0])*n+j+dj[0])*k+z+dk[0]]);\n for(int q=1;q<15;++q)v=add(v,mul(coef[q],a[((i+di[q])*n+j+dj[q])*k+z+dk[q]]));b[(i*n+j)*k+z]=v;}}\n}\n// All data restoration precedes the event interval on each invocation.\n// A 3D stencil invocation consists of all original i-slice launches, not one plane.\nextern "C" int suite_time(void*fn,void**args,int gx,int gy,int bx,int by,int count,int slices,int*slice,\n int nout,const uint64_t*dst,const uint64_t*src,const uint64_t*bytes,void*start,void*stop,float*out){\n using Launch=int(*)(void*,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**);\n using Copy=int(*)(uint64_t,uint64_t,size_t);using Record=int(*)(void*,void*);using Sync=int(*)(void*);using Elapsed=int(*)(float*,void*,void*);\n auto launch=(Launch)dlsym(RTLD_DEFAULT,"cuLaunchKernel");auto copy=(Copy)dlsym(RTLD_DEFAULT,"cuMemcpyDtoD_v2");\n auto record=(Record)dlsym(RTLD_DEFAULT,"cuEventRecord");auto sync=(Sync)dlsym(RTLD_DEFAULT,"cuEventSynchronize");auto elapsed=(Elapsed)dlsym(RTLD_DEFAULT,"cuEventElapsedTime");\n if(!launch||!copy||!record||!sync||!elapsed)return -999;\n if(count<1||count>128||slices==0)return -998;\n double total=0;int rc=0;\n for(int r=0;r<count;++r){\n  for(int i=0;i<nout;++i)if((rc=copy(dst[i],src[i],bytes[i])))return rc;\n  if((rc=record(start,nullptr)))return rc;\n  for(int s=1;s<=(slices<0?1:slices);++s){*slice=s;if((rc=launch(fn,gx,gy,1,bx,by,1,0,nullptr,args,nullptr)))return rc;}\n  if((rc=record(stop,nullptr)))return rc;if((rc=sync(stop)))return rc;\n  float ms=0;if((rc=elapsed(&ms,start,stop)))return rc;if(!(ms>0))return -997;total+=ms;\n }\n *out=float(total);return 0;\n}\n'

class HostHelper:
    def __init__(self,path):
        self.lib=ct.CDLL(str(path));V=ct.c_void_p;I=ct.c_int;F=ct.c_float;U=ct.c_uint;Q=ct.c_uint64
        self.gen=P.bind(self.lib,'make_data',[V,I,U,I],None)
        self.init=P.bind(self.lib,'suite_init',[I,V,V,V,V,V,I,I,I,I],None)
        self.ref=P.bind(self.lib,'suite_ref',[I,V,V,V,V,V,I,I,I,F,F],None)
        self.timing=P.bind(self.lib,'suite_time',[V,ct.POINTER(V),I,I,I,I,I,I,ct.POINTER(I),I,ct.POINTER(Q),ct.POINTER(Q),ct.POINTER(Q),V,V,ct.POINTER(F)])
    def case(self,task,shape,seed):
        lengths,outputs=dimensions(task,shape);arrays=[(ct.c_float*n)() for n in lengths]
        for i,a in enumerate(arrays):self.gen(a,len(a),seed+37*i,0)
        args=arrays+[None]*(5-len(arrays))
        self.init(SPECS[task]['kind'],*args,*shape,seed)
        alpha,beta=((43532.,12313.) if task=='gesummv' else (32412.,2123.)) if seed==0 else (1.25,-0.75)
        raw=[bytes(a) for a in arrays];expected=[(ct.c_float*n).from_buffer_copy(r) for n,r in zip(lengths,raw)]
        self.ref(SPECS[task]['kind'],*(expected+[None]*(5-len(expected))),*shape,alpha,beta)
        return raw,[bytes(x) for x in expected],outputs,alpha,beta

class GPU(P.CUDA):
    def __init__(self):
        super().__init__();P.bind(self.lib,'cuFuncGetAttribute',[ct.POINTER(ct.c_int),ct.c_int,ct.c_void_p])
    def module(self,path):
        fn=super().module(path);v=ct.c_int();rc=self.lib.cuFuncGetAttribute(ct.byref(v),1,fn)
        require(rc==0 and v.value<=49152,'Static shared memory exceeds frozen 48KiB contract');return fn

class DeviceCase:
    def __init__(self,gpu,helper,task,shape,seed):
        self.g=gpu;self.h=helper;self.task=task;self.shape=shape
        self.raw,self.expected,self.outputs,alpha,beta=helper.case(task,shape,seed)
        self.bases=[gpu.buffer(len(x)+2*len(P.GUARD)) for x in self.raw]
        for p,r in zip(self.bases,self.raw):gpu.put(p,P.GUARD+r+P.GUARD)
        self.ptrs=[p+len(P.GUARD) for p in self.bases];self.slice=ct.c_int(1)
        self.vals=scalar_args(task,shape,self.ptrs,alpha,beta,self.slice)
        self.params=(ct.c_void_p*len(self.vals))(*(ct.cast(ct.byref(v),ct.c_void_p) for v in self.vals))
        self.reset_ptrs=[]
        for i in sorted(self.outputs):
            p=gpu.buffer(len(self.raw[i]));gpu.put(p,self.raw[i]);self.reset_ptrs.append(p)
        Q=ct.c_uint64;self.dsts=(Q*len(self.outputs))(*(self.ptrs[i] for i in sorted(self.outputs)))
        self.srcs=(Q*len(self.outputs))(*self.reset_ptrs);self.sizes=(Q*len(self.outputs))(*(len(self.raw[i]) for i in sorted(self.outputs)))
    def reset(self):
        for i in self.outputs:self.g.put(self.ptrs[i],self.raw[i])
    def check(self):
        for i,(p,expected) in enumerate(zip(self.bases,self.expected)):
            got=self.g.get(p,len(expected)+2*len(P.GUARD))
            require(got[:len(P.GUARD)]==P.GUARD and got[-len(P.GUARD):]==P.GUARD,'GUARD_CHANGED array='+str(i))
            got=got[len(P.GUARD):-len(P.GUARD)]
            if got!=expected:
                off=next(j for j in range(0,len(got),4) if got[j:j+4]!=expected[j:j+4])
                raise NumericFailure('BITWISE_MISMATCH array='+str(i)+' element='+str(off//4)+' got='+got[off:off+4].hex()+' expected='+expected[off:off+4].hex())
    def launch(self,fn,block):
        self.reset();gx,gy,bx,by=grids(self.task,self.shape,block)
        for i in (range(1,self.shape[0]-1) if self.task=='convolution-3d' else (1,)):
            self.slice.value=i;self.g.ck('cuLaunchKernel',fn,gx,gy,1,bx,by,1,0,None,self.params,None)
        self.g.ck('cuCtxSynchronize');self.check()
    def batch(self,fn,block,count,events):
        out=ct.c_float();rc=self.h.timing(fn,self.params,*grids(self.task,self.shape,block),count,
           self.shape[0]-2 if self.task=='convolution-3d' else -1,ct.byref(self.slice),len(self.outputs),self.dsts,self.srcs,self.sizes,*events,ct.byref(out))
        require(rc==0,'CUDA_TIMING_ERROR '+str(rc));require(math.isfinite(out.value) and out.value>0,'Invalid GPU event time')
        self.check();return out.value

def paired(gpu,helper,f0,f1,task,shape,block):
    case=DeviceCase(gpu,helper,task,shape,4327);events=(gpu.event(),gpu.event());base=SPECS[task]['base']
    case.batch(f0,base,8,events);case.batch(f1,block,8,events);n=1
    while n<128 and case.batch(f0,base,n,events)<5:n*=2
    rows=[]
    for session in range(2):
        case.batch(f0,base,8,events);case.batch(f1,block,8,events)
        for p in range(8):
            order=[0,1] if (p+session)%2==0 else [1,0];ts={}
            for w in order:ts[w]=case.batch((f0,f1)[w],(base,block)[w],n,events)/n
            rows.append(dict(session=session,pair=p,order=order,repeats=n,baseline_ms=ts[0],candidate_ms=ts[1],ratio=ts[0]/ts[1]))
    gpu.free_buffers();return rows

def cpu_emulator_source(task,shape,src):
    # Independent scalar oracle and a host replay of the upstream CUDA are both tested.
    base=src.replace('__global__','')
    m,n,k=shape
    params= {'gemm':'m,n,k,al,be,a,b,c','gesummv':'m,al,be,a,b,c,d,e','syrk':'m,n,al,be,a,b','syr2k':'m,n,al,be,a,b,c',
      'convolution-2d':'m,n,a,b','convolution-3d':'m,n,k,a,b,i'}[task]
    x,y=(m,1) if task=='gesummv' else (m,m) if task in ('syrk','syr2k') else (k,n) if task=='convolution-3d' else (n,m)
    loop_i=f'for(int i=1;i<m-1;++i)' if task=='convolution-3d' else ''
    return definitions(shape)+'''struct Dim {int x,y,z;};
static Dim blockIdx={0,0,0},blockDim={1,1,1},threadIdx={0,0,0};
'''+base+f'''extern "C" void emulate(float*a,float*b,float*c,float*d,float*e,float al,float be){{
int m={m},n={n},k={k}; {loop_i}
for(int yy=0;yy<{y};++yy)for(int xx=0;xx<{x};++xx){{threadIdx.x=xx;threadIdx.y=yy;kernel({params});}}}}
'''

def build_helper():
    d=ROOT/'setup';P.public_dirs(d);src=d/'host-helper.cpp';save(src,HELPER.encode())
    so=d/'host-helper.so';argv=['g++','-O2','-std=c++17','-shared','-fPIC','-fno-fast-math','-ffp-contract=off',str(src),'-ldl','-o',str(so)]
    jw(d/'host-helper-build.json',argv);rc=P.command(argv,d/'host-helper-build.log',180)
    need(rc==0,'Trusted host helper build failed');so.chmod(0o555);return so

def oracle_replay_check(task,helper):
    hh=HostHelper(helper);d=ROOT/'preflight'/task/'host-replay';P.public_dirs(d);entries=[]
    for sh in shapes(task):
        f=d/(shape_id(sh)+'.cpp');so=f.with_suffix('.so');save(f,cpu_emulator_source(task,sh,baseline_source(task)).encode())
        rc=P.command(['g++','-O2','-std=c++17','-shared','-fPIC','-fno-fast-math','-ffp-contract=off',str(f),'-o',str(so)],f.with_suffix('.log'),180)
        need(rc==0,'Original CPU replay build failed: '+task)
        lib=ct.CDLL(str(so));fn=P.bind(lib,'emulate',[ct.c_void_p]*5+[ct.c_float]*2,None)
        for seed in (0,1009,9173):
            raw,expected,outputs,al,be=hh.case(task,sh,seed)
            arrays=[(ct.c_float*(len(r)//4)).from_buffer_copy(r) for r in raw]
            fn(*(arrays+[None]*(5-len(arrays))),al,be)
            need([bytes(x) for x in arrays]==expected,'Trusted oracle disagrees with scalar replay of upstream CUDA: '+task+' '+str(sh)+' '+str(seed))
            entries.append(dict(shape=sh,seed=seed,expected_sha256=[sha(x) for x in expected]))
    jw(d/'summary.json',{'passed':True,'cases':entries,'oracle_scope':'Original CUDA scalar replay vs separately written strict scalar oracle; no generated host code'})

_ORIG_NUMERIC=P.run_numeric_job

def numeric_job(path):
    if parse(read(path)).get('mode')=='info':return _ORIG_NUMERIC(path)
    need(os.geteuid()==65534,'Numeric worker must be unprivileged')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(600,600))
    path=P.safe(path);need(path.is_relative_to(ROOT),'Job outside experiment');job=parse(read(path));out=P.safe(job['output']);need(out.parent==path.parent,'Output escape');gpu=None
    try:
        task=job['task'];sh=tuple(job['shape']);need(task in SPECS and sh in shapes(task),'Unknown task or shape')
        if job['mode']=='compile':
            need(hfile(job['source'])==job['source_sha256'],'Source modified')
            src,block=candidate_source(read(job['source']).decode(),task)
            policy=P.source_policy
            try:
                P.source_policy=lambda text:text # prefix is trusted; unprefixed candidate was strictly checked above.
                details=P.nvrtc_compile(definitions(sh)+src,out.parent)
            finally:P.source_policy=policy
            result={'ok':True,'compile':details}
        else:
            need(hfile(job['helper'])==job['helper_sha256'],'Trusted helper changed')
            need(hfile(job['cubin'])==job['cubin_sha256'],'Candidate object changed');block=job['block'];need(tuple(block) in allowed_blocks(task),'Block changed')
            gpu=GPU();helper=HostHelper(job['helper']);fn=gpu.module(job['cubin'])
            if job['mode']=='check':
                records=[]
                for seed in (0,1009,9173):
                    c=DeviceCase(gpu,helper,task,sh,seed);c.launch(fn,block)
                    records.append(dict(seed=seed,expected_sha256=[sha(x) for x in c.expected]));gpu.free_buffers()
                result={'ok':True,'bitwise_pass':True,'shape':sh,'cases':records,'formal_equivalence_proven':False}
            else:
                need(job['mode']=='time' and sh in [tuple(s) for s in SPECS[task]['perf']],'Invalid timing job')
                need(hfile(job['baseline'])==job['baseline_sha256'],'Baseline changed')
                base=gpu.module(job['baseline']);result={'ok':True,'rows':paired(gpu,helper,base,fn,task,sh,block),'shape':sh}
        if gpu is not None:gpu.close();gpu=None
        jw(out,result);return 0
    except BaseException as exc:
        jw(out,{'ok':False,'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc()});return 3
    finally:
        if gpu is not None:
            with contextlib.suppress(Exception):gpu.close()

def numeric(task,sh,dest,mode,*,source=None,cubin=None,helper=None,block=None,baseline=None,sanitizer=None):
    dest=P.safe(dest);dest.mkdir(parents=True,exist_ok=False);P.public_dirs(dest);os.chown(dest,65534,65534)
    j=dict(task=task,shape=list(sh),mode=mode,output=str(dest/'numeric-result.json'))
    if source is not None:
        save(dest/'kernel.cu',source.encode());(dest/'kernel.cu').chmod(0o444);j.update(source=str(dest/'kernel.cu'),source_sha256=sha(source.encode()))
    if cubin is not None:j.update(cubin=str(cubin),cubin_sha256=hfile(cubin),block=list(block),helper=str(helper),helper_sha256=hfile(helper))
    if baseline is not None:j.update(baseline=str(baseline),baseline_sha256=hfile(baseline))
    jp=dest/'job.json';jw(jp,j);jp.chmod(0o444)
    argv=P.unpriv_prefix()
    if sanitizer:argv+=[P.sanitizer_path(),'--tool',sanitizer,'--error-exitcode','86','--target-processes','all']
    argv+=['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py'),'--_numeric',str(jp)]
    rc=P.command(argv,dest/'process.log',600 if sanitizer else 300)
    res=parse(read(dest/'numeric-result.json')) if (dest/'numeric-result.json').exists() else {'ok':False,'error':'NO_RESULT'}
    res['process_returncode']=rc;res['ok']=res.get('ok') is True and rc==0
    if sanitizer:
        text=read(dest/'process.log',32*1024**2).decode(errors='replace')
        clean=bool(re.search(r'ERROR SUMMARY:\s+0 errors',text)) or sanitizer=='racecheck' and bool(re.search(r'RACECHECK SUMMARY:\s+0 hazards',text))
        res['sanitizer_clean']=bool(clean and rc==0);res['ok']=res['ok'] and res['sanitizer_clean']
    if mode=='compile' and res['ok']:
        for ext in ('ptx','cubin'):
            p=dest/('kernel.'+ext);p.chmod(0o444);res[ext+'_sha256']=hfile(p)
    jw(dest/'parent-result.json',res)
    # Device/context failures are not quietly counted as bad generated arithmetic.
    error=res.get('error','')
    fatal_driver=('CUDA_DRIVER_ERROR' in error and not re.search(r'cuLaunchKernel (?:1|701)\b',error))
    if not res['ok'] and (fatal_driver or rc in (124,-9)):
        raise Blocked('GPU execution infrastructure failure; retained: '+str(dest)+' '+res.get('error','timeout'))
    return res

BASES={}

def compile_checked(task,sh,source,dest):return numeric(task,sh,dest,'compile',source=source)

def validate_object(task,sh,cubin,dest,helper,block,sanit=False):
    r=numeric(task,sh,dest/'bitwise','check',cubin=cubin,helper=helper,block=block)
    if not r['ok']:return {'passed':False,'stage':'bitwise_or_execution_failed','bitwise':r}
    ss={}
    if sanit:
        for tool in ('memcheck','initcheck','racecheck','synccheck'):
            ss[tool]=numeric(task,sh,dest/tool,'check',cubin=cubin,helper=helper,block=block,sanitizer=tool)
            if not ss[tool]['ok']:return {'passed':False,'stage':'sanitizer_failed','bitwise':r,'sanitizers':ss}
    return {'passed':True,'bitwise':r,'sanitizers':ss,'formal_equivalence_proven':False}

def baseline_preflight(helper):
    for task in TASKS:
        P.update(phase='ORIGINAL_REFERENCE_PREFLIGHT',task=task);oracle_replay_check(task,helper)
        for sh in shapes(task):
            d=ROOT/'preflight'/task/shape_id(sh);src=baseline_source(task)
            b=compile_checked(task,sh,src,d/'baseline');t=compile_checked(task,sh,src,d/'identity')
            need(b['ok'] and t['ok'],'Upstream baseline compile failed: '+task)
            need(b['cubin_sha256']==t['cubin_sha256'],'Identical compile is not reproducible')
            base=d/'baseline/kernel.cubin';twin=d/'identity/kernel.cubin';block=SPECS[task]['base']
            v=validate_object(task,sh,base,d/'validation',helper,block,sanit=sh==small_shapes(task)[-1]);need(v['passed'],'Upstream GPU baseline disagrees with strict reference: '+str(d))
            alt=next(x for x in allowed_blocks(task) if tuple(x)!=tuple(block))
            pos=validate_object(task,sh,base,d/'alternate-block',helper,alt);need(pos['passed'],'Allowed alternate block fails on original')
            if sh in [tuple(x) for x in SPECS[task]['perf']]:
                rr=numeric(task,sh,d/'identity-timing','time',cubin=twin,baseline=base,helper=helper,block=block)
                need(rr['ok'],'Identity timing failed');mm=P.timing_metric(rr['rows']);need(mm['measurement_valid'] and abs(math.log(mm['speedup']))<=math.log(1.02),'Identity control drift')
                jw(d/'identity-summary.json',mm)
            BASES[task,sh]=(base,twin)
    # Empty GEMM leaves initialized C unchanged; the strict oracle must reject it.
    task='gemm';sh=small_shapes(task)[1];d=ROOT/'preflight/negative-control'
    r=compile_checked(task,sh,signature(task)+' {}\n',d/'compiled');need(r['ok'],'Negative-control compile failed')
    v=validate_object(task,sh,d/'compiled/kernel.cubin',d/'validation',helper,SPECS[task]['base'])
    need(not v['passed'] and 'BITWISE_MISMATCH' in v['bitwise'].get('error',''),'Empty incorrect kernel not detected')
    jw(d/'expected-failure.json',v)

TASK_CONTRACT={
'gemm':'c initially contains C0. For each element: multiply C0 by beta, then in increasing k add (alpha*a)*b with the original left association. ni=NI,nj=NJ,nk=NK.',
'gesummv':'A,B,x are read-only. tmp and y are initially +0. Both tmp and y are live outputs. Preserve sequential j accumulation, then y=alpha*tmp+beta*y. n=N.',
'syrk':'a is read-only, c is in/out. Preserve beta scaling then increasing-k accumulation as written. Compute FULL square output, not only one triangle. ni=NI,nj=NJ.',
'syr2k':'a,b read-only, c in/out. Preserve the CUDA expression: form the TWO products, add them together, then add that sum to c in increasing k. Do NOT replace by two separate c updates. Compute the full square. ni=NI,nj=NJ.',
'convolution-2d':'A read-only. B is initialized. Compute only interior and preserve all boundary bytes. Preserve the CUDA term order, not the differently ordered upstream CPU formula. ni=NI,nj=NJ.',
'convolution-3d':'A read-only. B initialized; preserve boundaries. Trusted host launches one call per i=1..ni-2, in order, with x covering k and y covering j. Keep repeated offset terms exactly as written; do not correct the stencil. ni=NI,nj=NJ,nk=NK.'}

def make_prompt(task,block):
    src=baseline_source(task);base=SPECS[task]['base']
    text=f'''Optimize this existing CUDA device kernel. Return only the COMPLETE kernel with the exact supplied signature.
{block}

Workload contract: {TASK_CONTRACT[task]}
DATA_TYPE is float. NI,NJ,NK,N are compile-time allocation strides; corresponding runtime extents equal those values in every valid invocation. _PB_NI=ni, _PB_NJ=nj, _PB_NK=nk, _PB_N=n. These macros and DATA_TYPE are provided by a trusted prefix. Do not define them.
Preserve exact FP32 operation grouping and order, including the original parenthesization and sequential accumulation. Inputs are finite FP32, with selected signed zero/subnormal cases. Do not change to FMA, TF32, FP16, Tensor Cores or reassociated reductions. Compiler uses fmad=false, ftz=false, prec-div=true, prec-sqrt=true. Round-to-nearest is meant; no RN32 function exists. Permitted rounding intrinsics are __fmul_rn and __fadd_rn (plus __fsub_rn). No error tolerance.
All declared outputs and scratch outputs must match; input arrays must remain unchanged. Arrays are disjoint. Dimensions are positive, including ragged dimensions and dimensions equal to 1. Do not specialize to seed, timing count or test values.
You may optionally put exactly one first line // BLOCK X Y, selecting from {allowed_blocks(task)}. Without that line the block is {base}. The trusted host recomputes a covering grid. You cannot supply a host launcher, extra kernel, library call or alter the convolution-3d slice loop.
Allowed inside the kernel: scalar variables, arrays, static shared memory up to48KiB, arithmetic/control flow, __syncthreads, __syncwarp, synchronized shuffle intrinsics, min/max. Barriers must be safe for ragged dimensions. No include, preprocessing, helper function, inline PTX, host code, dynamic launch/allocation, atomics, function pointers or extra top-level declarations. You may use DATA_TYPE as a type.
This request is independent. No compiler or timing feedback will be supplied. If no safe improvement is found return the original kernel. Explain nothing.
----- BEGIN ORIGINAL CUDA -----
{src}----- END ORIGINAL CUDA -----'''
    return [{'role':'system','content':'Optimize CUDA numerical code under the exact correctness contract. Return only the complete requested device kernel and optional block comment, no tools or explanations.'},{'role':'user','content':text}]

def plan_document(info):
    blocks=P.profiles(info);order=[]
    for ti,t in enumerate(TASKS):
        for si,seed in enumerate(SEEDS):
            arms=list(ARMS);random.Random(2026100802+ti*100+si).shuffle(arms)
            order.append(dict(task=t,seed=seed,label=t+'-s'+str(seed),requests=[dict(id=t+'__'+a+'__s'+str(seed),task=t,condition=a,seed=seed,messages=make_prompt(t,blocks[a])) for a in arms]))
    random.Random(2026100802).shuffle(order)
    return {**PROTOCOL,'groups':order,'gpu_profiles':blocks,'small_shapes':{t:small_shapes(t) for t in TASKS},'performance_shapes':{t:SPECS[t]['perf'] for t in TASKS},'nvrtc_options':P.NVRTC_OPTIONS,'source_sha256':{t:sha(baseline_source(t).encode()) for t in TASKS}}

def response_candidate(resp,task):
    require(resp.get('truncated') is False,'LLM_CONTEXT_TRUNCATED');require(resp.get('stop_type') in ('eos','word'),'LLM_OUTPUT_INCOMPLETE')
    c=resp.get('timings',{}).get('predicted_n');require(type(c) is int and 0<c<=CAP+8,'OUTPUT_TOKEN_COUNT_INVALID')
    return candidate_source(resp.get('content'),task)

def generate_group(A,assets,group):
    d=ROOT/'groups'/group['label'];P.public_dirs(d);records=[];proc=None;transport_bad=0
    try:
        for ix,r in enumerate(group['requests']):
            rd=d/'generation'/r['condition'];P.public_dirs(rd)
            if proc is None:proc=P.start_model(A,assets,d/('inference-'+str(ix)))
            P.update(phase='GENERATING_MAIN_CUDA',current_id=r['id'],task=r['task'])
            jw(rd/'request.json',r);text=A.api('/apply-template',{'messages':r['messages']})['prompt']
            need(all(m['content'] in text for m in r['messages']),'Template dropped messages');save(rd/'rendered.txt',text.encode())
            ids=A.api('/tokenize',dict(content=text,add_special=True,parse_special=True))['tokens'];need(ids and all(type(x) is int and x>=0 for x in ids),'Bad token IDs')
            need(len(ids)+CAP+16<=32768,'Input exceeds context budget; do not truncate');jw(rd/'tokens.json',ids)
            body=dict(A.SAMPLING,seed=r['seed'],prompt=ids,n_predict=CAP,stream=False,return_tokens=True,id_slot=0)
            jw(rd/'wire-request.json',body);jw(rd/'intent.json',{'id':r['id'],'attempt':1,'utc':now()})
            calls=P.STATE.get('generation_calls',0)+1;need(calls<=TOTAL,'Call ceiling');P.update(generation_calls=calls)
            start=time.monotonic();rec={k:r[k] for k in ('id','task','condition','seed')};rec['generation_status']='saved'
            try:
                response=A.api('/completion',body,timeout=min(REQUEST_SECONDS,max(1,P.WORK_DEADLINE-time.monotonic())))
                jw(rd/'response.json',response);need(response.get('tokens_evaluated')==len(ids),'Native input token count disagreement')
                source,b=response_candidate(response,r['task']);save(rd/'candidate.cu',source.encode())
                rec.update(source_sha256=sha(source.encode()),source_equals_original=source==baseline_source(r['task']),block=b,error=None,
                  output_tokens=response['timings']['predicted_n'],tokens_per_second=response['timings'].get('predicted_per_second'))
                transport_bad=0
            except NumericFailure as exc:rec.update(generation_status='invalid_generation',error=str(exc));transport_bad=0
            except (OSError,http.client.HTTPException,TimeoutError) as exc:
                rec.update(generation_status='transport_or_timeout',error=type(exc).__name__+': '+str(exc));transport_bad+=1;P.close_child(proc);proc=None
            rec['wall_seconds']=time.monotonic()-start;jw(rd/'record.json',rec);records.append(rec)
            print('GPU002_GENERATION_TERMINAL '+r['id']+' '+rec['generation_status'],flush=True)
            need(transport_bad<3,'Three consecutive transport failures; stop instead of treating infrastructure loss as candidate failure')
    finally:P.close_child(proc);jw(d/'model-stopped.json',{'utc':now(),'owned_model_stopped':True})
    P.no_other_gpu();return records

def evaluate_group(group,records,helper):
    task=group['task'];root=ROOT/'groups'/group['label'];out=[]
    for r in records:
        P.update(phase='EVALUATING_MAIN_CUDA',current_id=r['id']);P.no_other_gpu()
        o={**r,'correctness_passed':False,'measurements':[],'stage':'generation_failed'};d=root/'evaluation'/r['condition']
        if r['generation_status']!='saved':out.append(o);continue
        src=read(root/'generation'/r['condition']/'candidate.cu').decode();need(sha(src.encode())==r['source_sha256'],'Saved candidate modified')
        compiled={};checks=[];o['stage']='compile_failed'
        for sh in shapes(task):
            dd=d/shape_id(sh);cc=compile_checked(task,sh,src,dd/'compiled');compiled[sh]=cc
            if not cc['ok']:break
            v=validate_object(task,sh,dd/'compiled/kernel.cubin',dd/'validation',helper,r['block'],sanit=sh==small_shapes(task)[-1]);checks.append(v)
            if not v['passed']:o['stage']=v['stage'];break
        else:o['correctness_passed']=True;o['stage']='measured'
        o['compilation']={shape_id(sh):v for sh,v in compiled.items()};o['checks']=checks
        if o['correctness_passed']:
            jw(d/'telemetry-before.json',P.telemetry())
            for sh in [tuple(x) for x in SPECS[task]['perf']]:
                P.no_other_gpu();dd=d/shape_id(sh);base,twin=BASES[task,sh];cubin=dd/'compiled/kernel.cubin'
                rr=numeric(task,sh,dd/'timing','time',cubin=cubin,baseline=base,helper=helper,block=r['block'])
                mm={'shape':sh,'measurement_valid':False,'speedup':None,'same_launch_as_original':list(r['block'])==SPECS[task]['base'],'same_cubin':hfile(cubin)==hfile(base),'same_ptx':hfile(cubin.with_suffix('.ptx'))==hfile(base.with_suffix('.ptx'))}
                if rr['ok']:
                    mm.update(P.timing_metric(rr['rows']));im=numeric(task,sh,dd/'identity-timing','time',cubin=twin,baseline=base,helper=helper,block=SPECS[task]['base'])
                    if im['ok']:
                        imetric=P.timing_metric(im['rows']);mm['identity']=imetric
                        if not imetric['measurement_valid'] or abs(math.log(imetric['speedup']))>math.log(1.02):mm['quality_reasons'].append('identity_control_shift');mm['measurement_valid']=False
                    else:mm['quality_reasons'].append('identity_execution_failed');mm['measurement_valid']=False
                else:mm['error']=rr.get('error','timing_failed')
                mm['speedup_gt_1_02']=mm['measurement_valid'] and mm['speedup']>1.02;o['measurements'].append(mm)
            jw(d/'telemetry-after.json',P.telemetry())
        jw(d/'outcome.json',o);out.append(o)
        P.update(evaluation_terminal=P.STATE.get('evaluation_terminal',0)+1)
    jw(root/'outcomes.json',out);return out

def summarize(outcomes,plan):
    need(len(outcomes)==TOTAL and {o['id'] for o in outcomes}=={r['id'] for g in plan['groups'] for r in g['requests']},'90-slot accounting incomplete')
    valid=[m for o in outcomes for m in o['measurements'] if m['measurement_valid']]
    summary={'state':'GPU002_POLYBENCH_MAIN_COHORT_COMPLETE','scope':PROTOCOL['suite'],'tasks':list(TASKS),'candidate_slots':TOTAL,
      'generation_calls':P.STATE.get('generation_calls',0),'generation_status_counts':{s:sum(o['generation_status']==s for o in outcomes) for s in sorted({o['generation_status'] for o in outcomes})},
      'correctness_passed':sum(o['correctness_passed'] for o in outcomes),'valid_size_measurements':len(valid),'size_speedups_gt_1_02':sum(m['speedup_gt_1_02'] for m in valid),
      'changed_object_or_launch_size_speedups_gt_1_02':sum(m['speedup_gt_1_02'] and (not m['same_cubin'] or not m['same_launch_as_original']) for m in valid),
      'same_source_saved':sum(o.get('source_equals_original',False) for o in outcomes),'formal_equivalence_proven':False,'whole_GPU_study_complete':False,
      'no_best_of_selection':True,'no_error_tolerance_changes':True,'upstream_commit':COMMIT,'utc':now()}
    d=ROOT/'final';jw(d/'summary.json',summary);jw(d/'outcomes.json',outcomes);jw(d/'protocol.json',plan)
    rows=[{k:o.get(k) for k in ('id','task','condition','seed','stage','generation_status','correctness_passed','source_equals_original','block','error')}|m for o in outcomes for m in o['measurements'] or [{}]]
    def csvbytes(rows):
        s=io.StringIO();keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(s,keys);w.writeheader();w.writerows(rows);return s.getvalue().encode()
    save(d/'outcomes.csv',csvbytes(rows));pairs=[];by={(r['task'],r['seed'],r['condition']):r for r in outcomes}
    for task in TASKS:
        for seed in SEEDS:
            for n,b in [('S1','P0'),('S2','P0'),('S1','W1'),('S2','W2')]:
                a,z=by[task,seed,n],by[task,seed,b]
                za={tuple(m['shape']):m for m in z['measurements']}
                for m in a['measurements']:
                    zz=za.get(tuple(m['shape']))
                    if zz and m['measurement_valid'] and zz['measurement_valid']:
                        sh=shape_id(m['shape']);pairs.append(dict(task=task,seed=seed,shape=sh,contrast=n+'_over_'+b,speedup_ratio=m['speedup']/zz['speedup'],
                            same_cubin_between_arms=a['compilation'][sh]['cubin_sha256']==z['compilation'][sh]['cubin_sha256']))
    if pairs:save(d/'matched_pairs_descriptive.csv',csvbytes(pairs))
    return summary

def wait_ack(rec):
    P.update(phase='WAITING_LOCAL_BACKUP',checkpoint=rec['label']);path=ROOT/'acks'/(rec['label']+'.json');end=min(P.WORK_DEADLINE or math.inf,time.monotonic()+ACK_SECONDS)
    while not path.exists():
        need(time.monotonic()<end,'No local ACK before12h/run deadline; no more generation');time.sleep(2)
    need(parse(read(path)).get('sha256')==rec['sha256'],'Backup ACK mismatch')

def checkpoint(src,label):
    rec=P.archive_dir(src,label);wait_ack(rec);print('GPU002_CHECKPOINT_ACKED '+label,flush=True)

def worker(allow):
    configure();P.remote_guard();need(allow,'Ephemeral storage ACK flag required');P.WORK_DEADLINE=time.monotonic()+RUN_SECONDS
    os.umask(0o022);P.public_dirs(ROOT);P.public_dirs(ROOT/'control');(ROOT/'control/runner.py').chmod(0o444)
    signal.signal(signal.SIGTERM,lambda s,f:(_ for _ in ()).throw(Blocked('Termination requested; evidence retained')))
    try:
        with P.lock('/workspace/gpu-code-pilot-exclusive.lock'):
            P.update(phase='SOURCE_INTAKE',generation_calls=0,evaluation_terminal=0,started_utc=now());P.no_other_gpu()
            need(shutil.disk_usage(ROOT).free>=4*P.GIB,'Need4GiB free; no old files deleted')
            intake();P.sanitizer_path();info=P.native_info();plan=plan_document(info);jw(ROOT/'setup/protocol.json',plan)
            A=P.module_a();A.ROOT=ROOT
            with contextlib.redirect_stdout(sys.stderr):assets=A.cached_assets();gi=A.gpu_info()
            need(gi['uuid']==P.EXPECTED_GPU,'GPU allocation changed');jw(ROOT/'setup/gpu.json',info);jw(ROOT/'setup/telemetry.json',P.telemetry())
            jw(ROOT/'setup/model-runtime.json',assets[3]);jw(ROOT/'setup/cache.json',assets[5]);save(ROOT/'setup/runner.py',read(__file__))
            helper=build_helper();jw(ROOT/'setup/toolchain.json',{'helper_sha256':hfile(helper),'sanitizer_sha256':hfile(Path(P.sanitizer_path()).resolve()),'nvrtc_options':P.NVRTC_OPTIONS,'nvrtc_sha256':hfile(next(p.resolve() for p in (Path('/usr/local/cuda-12.8/lib64/libnvrtc.so'),Path('/usr/local/cuda/lib64/libnvrtc.so')) if p.exists()))})
            checkpoint(ROOT/'setup','setup')
            baseline_preflight(helper);checkpoint(ROOT/'preflight','original-controls')
            outcomes=[]
            for group in plan['groups']:
                need(time.monotonic()<P.WORK_DEADLINE,'Run wall limit; no generation retry')
                generated=generate_group(A,assets,group)
                checkpoint(ROOT/'groups'/group['label']/'generation','generation-'+group['label'])
                new=evaluate_group(group,generated,helper);outcomes.extend(new)
                checkpoint(ROOT/'groups'/group['label'],'evaluated-'+group['label'])
                with contextlib.redirect_stdout(sys.stderr):A.verify_cached_unchanged(assets[5])
                P.update(completed_groups=len(outcomes)//5,evaluation_terminal=len(outcomes))
            summary=summarize(outcomes,plan);rec=P.archive_dir(ROOT/'final','summary');wait_ack(rec)
            jw(ROOT/'completion.json',{'summary_sha256':hfile(ROOT/'final/summary.json'),'summary_checkpoint':rec,'utc':now()});P.update(phase='COMPLETE')
            print('GPU002_POLYBENCH_MAIN_COHORT_COMPLETE',flush=True)
    except BaseException as exc:
        tails={}
        for p in sorted(ROOT.rglob('*.log'),key=lambda p:p.stat().st_mtime if p.is_file() else 0)[-4:]:
            if p.is_file() and not p.is_symlink():
                with p.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-5000));tails[p.relative_to(ROOT).as_posix()]=f.read().decode(errors='replace')
        P.atomic(ROOT/'failure.json',{'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'last_logs':tails,'utc':now()})
        P.update(phase='BLOCKED',error=str(exc));raise

def local(mode,allow=False):
    need(os.geteuid()!=0,'Run from WSL without sudo');A=P.module_a();A.fingerprint_check(Path.home()/'.ssh/id_ed25519');con=A.Connection()
    try:
        command=['/usr/bin/python3','-I','-S','-B',str(ROOT/'control/runner.py')]
        if mode=='run':
            need(allow,'Explicit ephemeral checkpoint authorization required');raw=read(__file__)
            print(con.run(['/usr/bin/python3','-I','-S','-B','-c',P.install_text(sha(raw))],data=raw).decode(),flush=True)
            doc=parse(con.run(command+['--_launch','--allow-ephemeral-with-local-checkpoints']))
            print('GPU002_MAIN_EXPERIMENT_STARTED; source intake -> reference controls ->90 new requests -> verification/timing',flush=True)
        elif mode=='stop':print(con.run(command+['--_stop']).decode());return
        else:doc=parse(con.run(command+['--_status']))
        seen=set()
        while True:
            if mode=='status':print(json.dumps(doc,ensure_ascii=False,indent=2));return
            for r in doc['receipts']:
                if r['label'] not in seen:P.checkpoint_collect(con,r);seen.add(r['label'])
            print(json.dumps({'state':doc['state'],**doc.get('progress',{})}),flush=True)
            if doc['state'] in ('BLOCKED','INTERRUPTED'):
                d=Path.home()/LOCAL_REL;d.mkdir(exist_ok=True,parents=True);P.atomic(d/'last-status.json',doc)
                print(json.dumps(doc.get('failure',{}),ensure_ascii=False,indent=2));raise Blocked('Remote interrupted; no automatic retry')
            if doc['state']=='COMPLETE':
                P.atomic(Path.home()/LOCAL_REL/'final-status.json',doc);print(json.dumps(doc['summary'],ensure_ascii=False,indent=2));print('GPU002_POLYBENCH_LOCAL_COPY_VERIFIED');return
            need(doc['state']=='RUNNING','Experiment not running')
            if mode=='collect':return
            time.sleep(15);doc=parse(con.run(command+['--_status']))
    except KeyboardInterrupt:print('LOCAL_WATCH_CLOSED; worker waits at checkpoint, reconnect --watch within12h/run cap. Pod still billed.')
    finally:con.close()

def self_test():
    class T(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.top=tempfile.TemporaryDirectory(prefix='gpu002-tests-');cls.base=Path(cls.top.name);cls.so=cls.base/'helper.so'
            src=cls.base/'helper.cpp';src.write_text(HELPER)
            p=subprocess.run(['g++','-O2','-std=c++17','-shared','-fPIC','-fno-fast-math','-ffp-contract=off',str(src),'-ldl','-o',str(cls.so)],capture_output=True,text=True)
            if p.returncode:raise RuntimeError('Host helper compile failed: '+p.stderr)
            cls.hh=HostHelper(cls.so)
        @classmethod
        def tearDownClass(cls):cls.top.cleanup()
        def setUp(self):
            self.tmp=tempfile.TemporaryDirectory(prefix='gpu002-case-');self.root=Path(self.tmp.name)/'run';self.root.mkdir()
            self.old=ROOT;configure(self.root);P.STATE={};P.WORK_DEADLINE=None;BASES.clear()
        def tearDown(self):configure(self.old);self.tmp.cleanup()
        def info(self):return {'name':'NVIDIA A40','compute_capability':[8,6],'warp_size':32,'static_shared_memory_per_block':49152,'registers_per_block':65536,'max_threads_per_multiprocessor':1536,'shared_memory_per_multiprocessor':102400}
        def rows(self,ratio=1):return [dict(session=s,pair=p,ratio=ratio,baseline_ms=ratio,candidate_ms=1,repeats=1,order=[0,1] if (s+p)%2==0 else [1,0]) for s in range(2) for p in range(8)]
        def test_embedded_support_pin(self):self.assertEqual(sha(gzip.decompress(base64.b64decode(PILOT_EMBED))),PILOT_SHA)
        def test_provenance_commit(self):self.assertEqual(len(COMMIT),40);self.assertEqual(len(SPECS),6)
        def test_license_present(self):self.assertIn('OHIO STATE UNIVERSITY',UPSTREAM_LICENSE);self.assertIn('University of Delaware',UPSTREAM_LICENSE)
        def test_six_original_policies(self):
            for t in TASKS:
                s,b=candidate_source(baseline_source(t),t);self.assertEqual(tokens(s),tokens(baseline_source(t)));self.assertEqual(b,SPECS[t]['base'])
        def test_reviewed_original_extraction(self):
            for t in TASKS:
                raw=('// leading\n'+SPECS[t]['source']+'\nvoid other() {}').encode()
                s,r=extract_kernel(raw,t);self.assertEqual(tokens(s),tokens(baseline_source(t)));self.assertEqual(r['original_line_start'],2)
        def test_original_token_change_blocks(self):
            t='gemm';self.assertRaises(Blocked,extract_kernel,SPECS[t]['source'].replace('+=','-=').encode(),t)
        def test_ambiguous_original_blocks(self):
            t='gemm';self.assertRaises(Blocked,extract_kernel,(SPECS[t]['source']*2).encode(),t)
        def test_90_unique_requests(self):
            p=plan_document(self.info());r=[r for g in p['groups'] for r in g['requests']];self.assertEqual(len(r),90);self.assertEqual(len({x['id'] for x in r}),90)
        def test_18_five_arm_groups(self):
            gs=plan_document(self.info())['groups'];self.assertEqual(len(gs),18)
            for g in gs:self.assertEqual({x['condition'] for x in g['requests']},set(ARMS));self.assertEqual(len({x['seed'] for x in g['requests']}),1)
        def test_three_seeds_not_bestof(self):self.assertEqual(SEEDS,(69001,69002,69003));self.assertIn('No selective',PROTOCOL['retry_policy'])
        def test_prompt_only_hardware_varies(self):
            plan=plan_document(self.info());blocks=plan['gpu_profiles']
            for g in plan['groups']:
                neutral=[r['messages'][1]['content'].replace(blocks[r['condition']],'<GPU>') for r in g['requests']]
                self.assertEqual(len(set(neutral)),1)
        def test_prompt_rounding_clarity(self):
            for t in TASKS:
                p=make_prompt(t,'TEST')[1]['content'];self.assertIn('no RN32 function exists',p);self.assertNotIn('RN32(',p);self.assertIn('__fadd_rn',p)
        def test_block_alternates(self):
            for t in TASKS:
                for b in allowed_blocks(t):self.assertEqual(candidate_source('// BLOCK %d %d\n'%b+baseline_source(t),t)[1],list(b))
        def test_block_bad_rejected(self):self.assertRaises(NumericFailure,candidate_source,'// BLOCK 1024 1024\n'+baseline_source('gemm'),'gemm')
        def test_block_malformed(self):self.assertRaises(NumericFailure,candidate_source,'// BLOCK x 2\n'+baseline_source('gemm'),'gemm')
        def test_unknown_call_rejected(self):self.assertRaises(NumericFailure,candidate_source,signature('gemm')+'{ RN32(1); }','gemm')
        def test_header_injection_rejected(self):self.assertRaises(NumericFailure,candidate_source,'#include <stdio.h>\n'+baseline_source('gemm'),'gemm')
        def test_extra_host_code_rejected(self):self.assertRaises(NumericFailure,candidate_source,baseline_source('gemm')+'int main(){return 0;}','gemm')
        def test_fma_rejected(self):self.assertRaises(NumericFailure,candidate_source,signature('gemm')+'{ c[0]=__fmaf_rn(a[0],b[0],c[0]); }','gemm')
        def test_signature_change_rejected(self):self.assertRaises(NumericFailure,candidate_source,baseline_source('gemm').replace('int ni','long ni'),'gemm')
        def test_scalar_cast_allowed(self):self.assertEqual(candidate_source(signature('gemm')+'{ c[0]=DATA_TYPE(0); }','gemm')[1],[32,8])
        def test_fenced_source_allowed(self):self.assertEqual(candidate_source('```cuda\n'+baseline_source('gemm')+'```','gemm')[1],[32,8])
        def test_multiple_fences_rejected(self):self.assertRaises(NumericFailure,candidate_source,'```cuda\n'+baseline_source('gemm')+'```\n```c\nx\n```','gemm')
        def test_response_length_limit(self):self.assertRaises(NumericFailure,response_candidate,{'truncated':False,'stop_type':'limit'},'gemm')
        def test_response_context_truncation(self):self.assertRaises(NumericFailure,response_candidate,{'truncated':True},'gemm')
        def test_response_original(self):self.assertEqual(response_candidate({'truncated':False,'stop_type':'eos','timings':{'predicted_n':100},'content':baseline_source('gemm')},'gemm')[1],[32,8])
        def test_definitions_symbolic(self):self.assertIn('#define _PB_NJ nj',definitions((7,13,11)));self.assertIn('#define NJ 13',definitions((7,13,11)))
        def test_grid_rectangular(self):self.assertEqual(grids('gemm',(7,70,11),(32,8)),(3,1,32,8))
        def test_grid_syrk_square(self):self.assertEqual(grids('syrk',(33,7,1),(32,8)),(2,5,32,8))
        def test_grid_conv3d_planes(self):self.assertEqual(grids('convolution-3d',(9,17,70),(32,8)),(3,3,32,8))
        def test_output_sets(self):self.assertEqual(dimensions('gesummv',(17,17,1)),([289,289,17,17,17],{2,4}))
        def test_argument_layout(self):
            for t,c in zip(TASKS,(8,8,6,7,4,6)):
                ptrs=list(range(1,len(dimensions(t,small_shapes(t)[1])[0])+1));self.assertEqual(len(scalar_args(t,small_shapes(t)[1],ptrs,1.25,-.75,ct.c_int(1))),c)
        def test_gesummv_scratch_is_initialized(self):
            raw,exp,outs,*_=self.hh.case('gesummv',(17,17,1),9173)
            self.assertEqual(raw[2],b'\0'*68);self.assertEqual(raw[4],b'\0'*68);self.assertNotEqual(exp[2],raw[2])
        def test_conv_boundaries_preserved(self):
            for t in ('convolution-2d','convolution-3d'):
                raw,exp,*_=self.hh.case(t,small_shapes(t)[1],1009);self.assertEqual(raw[1][:4],exp[1][:4]);self.assertEqual(raw[0],exp[0])
        def test_oracle_deterministic(self):self.assertEqual(self.hh.case('gemm',(7,13,11),1009),self.hh.case('gemm',(7,13,11),1009))
        def test_oracle_and_original_scalar_cuda_all_six(self):
            for t in TASKS:
                for sh in small_shapes(t):
                    path=self.root/(t+'-'+shape_id(sh)+'.cpp');so=path.with_suffix('.so');path.write_text(cpu_emulator_source(t,sh,baseline_source(t)))
                    p=subprocess.run(['g++','-O2','-std=c++17','-fPIC','-shared','-fno-fast-math','-ffp-contract=off',str(path),'-o',str(so)],capture_output=True,text=True)
                    self.assertEqual(p.returncode,0,p.stderr);lib=ct.CDLL(str(so));fn=P.bind(lib,'emulate',[ct.c_void_p]*5+[ct.c_float]*2,None)
                    for seed in (0,1009,9173):
                        raw,expected,outputs,al,be=self.hh.case(t,sh,seed);a=[(ct.c_float*(len(x)//4)).from_buffer_copy(x) for x in raw]
                        fn(*(a+[None]*(5-len(a))),al,be);self.assertEqual([bytes(x) for x in a],expected,(t,sh,seed))
        def test_gemm_negative_control_would_fail(self):
            raw,exp,*_=self.hh.case('gemm',(7,13,11),1009);self.assertNotEqual(raw[2],exp[2])
        def test_state_guard_detects_input(self):
            g=FakeGPU();c=DeviceCase(g,self.hh,'gemm',(7,13,11),1009)
            for p,e in zip(c.bases,c.expected):g.put(p,P.GUARD+e+P.GUARD)
            c.check();g.put(c.bases[0],b'x'+g.get(c.bases[0],len(c.expected[0])+2*len(P.GUARD))[1:]);self.assertRaises(NumericFailure,c.check)
        def test_state_detects_output(self):
            g=FakeGPU();c=DeviceCase(g,self.hh,'gemm',(7,13,11),1009);self.assertRaises(NumericFailure,c.check)
        def test_device_params_and_slices(self):
            g=FakeGPU();c=DeviceCase(g,self.hh,'convolution-3d',(5,7,9),1009)
            with mock.patch.object(c,'check'):
                c.launch(ct.c_void_p(88),[32,8])
            self.assertEqual(g.launches,3);self.assertEqual(c.slice.value,3)
        def test_paired_uses_distinct_objects_and_blocks(self):
            calls=[]
            class C:
                def __init__(*a):pass
                def batch(s,fn,block,n,ev):calls.append((fn,tuple(block),n));return n*(1 if fn==11 else 2)
            with mock.patch.dict(globals(),DeviceCase=C):
                rows=paired(FakeGPU(),None,11,22,'gemm',(128,128,128),[16,16])
            self.assertEqual(len(rows),16);self.assertTrue(all(r['ratio']==.5 for r in rows));self.assertTrue(any(x[:2]==(22,(16,16)) for x in calls))
        def test_timing_metric_bad_pairs(self):self.assertRaises(Blocked,P.timing_metric,self.rows()[:-1])
        def test_timing_metric_known_ratio(self):self.assertEqual(P.timing_metric(self.rows(1.3))['speedup'],1.3)
        def test_no_overwrite(self):save(self.root/'x',b'a');self.assertRaises(FileExistsError,save,self.root/'x',b'b')
        def test_archive_roundtrip(self):
            d=self.root/'sample';save(d/'a',b'a');rec=P.archive_dir(d,'sample');self.assertEqual(P.verify_archive(self.root/'archives/sample.tar.gz',rec)['verified_files'],1)
        def test_archive_bad_hash(self):
            d=self.root/'sample';save(d/'a',b'a');rec=P.archive_dir(d,'sample');rec['sha256']='0'*64;self.assertRaises(Blocked,P.verify_archive,self.root/'archives/sample.tar.gz',rec)
        def test_symlinks_refused(self):
            (self.root/'x').symlink_to('/etc/passwd');self.assertRaises(Blocked,read,self.root/'x')
        def test_missing_ack_not_success(self):
            with mock.patch.dict(globals(),ACK_SECONDS=0):self.assertRaises(Blocked,wait_ack,{'label':'x','sha256':'0'*64})
        def test_bad_ack_blocks(self):jw(self.root/'acks/x.json',{'sha256':'1'*64});self.assertRaises(Blocked,wait_ack,{'label':'x','sha256':'0'*64})
        def test_matching_ack(self):jw(self.root/'acks/x.json',{'sha256':'0'*64});wait_ack({'label':'x','sha256':'0'*64})
        def test_no_old_results_paths(self):self.assertNotIn('pilot-001',str(ROOT));self.assertNotIn('Cherry',P.SERVER);self.assertEqual(P.SERVER,'root@example.invalid')
        def test_generate_five_with_mock_api(self):
            group=plan_document(self.info())['groups'][0];task=group['task'];current=[None]
            class A:
                SAMPLING=P.module_a().SAMPLING
                def api(self,url,data=None,**kw):
                    if url=='/apply-template':return {'prompt':'\n'.join(x['content'] for x in data['messages'])}
                    if url=='/tokenize':return {'tokens':[1,2,3]}
                    current[0]=data
                    return dict(truncated=False,stop_type='eos',tokens_evaluated=3,timings={'predicted_n':10,'predicted_per_second':50},content=baseline_source(task))
            P.WORK_DEADLINE=time.monotonic()+60
            with mock.patch.object(P,'start_model',return_value=None),mock.patch.object(P,'no_other_gpu'):
                recs=generate_group(A(),(),group)
            self.assertEqual(len(recs),5);self.assertTrue(all(x['generation_status']=='saved' for x in recs));self.assertEqual(current[0]['seed'],group['seed']);self.assertEqual(P.STATE['generation_calls'],5)
        def test_generation_bad_source_not_numeric_failure(self):
            resp=dict(truncated=False,stop_type='eos',timings={'predicted_n':12},content=signature('gemm')+'{ RN32(1); }')
            self.assertRaises(NumericFailure,response_candidate,resp,'gemm')
        def test_full_90_accounting_mock(self):
            plan=plan_document(self.info());out=[]
            for g in plan['groups']:
                for r in g['requests']:out.append({k:r[k] for k in ('id','task','condition','seed')}|{'stage':'generation_failed','generation_status':'invalid_generation','correctness_passed':False,'measurements':[]})
            summary=summarize(out,plan);self.assertEqual(summary['candidate_slots'],90);self.assertEqual(summary['valid_size_measurements'],0)
        def test_incomplete_not_complete(self):self.assertRaises(Blocked,summarize,[],plan_document(self.info()))
        def test_duplicate_not_complete(self):
            plan=plan_document(self.info());r=plan['groups'][0]['requests'][0];self.assertRaises(Blocked,summarize,[r]*90,plan)
        def test_child_timeout_cleanup_real(self):
            rc=P.command([sys.executable,'-c','import time; time.sleep(20)'],self.root/'timeout.log',.1);self.assertEqual(rc,124)
        def test_install_syntax(self):compile(P.install_text('0'*64),'install','exec')
        def test_compile_options_strict(self):self.assertIn('--fmad=false',P.NVRTC_OPTIONS);self.assertIn('--ftz=false',P.NVRTC_OPTIONS)
        def test_timing_resets_before_events(self):
            s=HELPER.split('extern "C" int suite_time',1)[1];self.assertLess(s.index('rc=copy('),s.index('rc=record(start'))
        def test_numeric_info_routes_to_original(self):
            job=self.root/'job.json';jw(job,{'mode':'info'})
            with mock.patch.dict(globals(),_ORIG_NUMERIC=lambda path:91):self.assertEqual(numeric_job(str(job)),91)
        def test_source_download_pin(self):
            data=b'public source';pin=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            with mock.patch('urllib.request.urlopen',return_value=io.BytesIO(data)):self.assertEqual(public_fetch('x',pin),data)
        def test_source_hash_mismatch_not_fallback(self):
            with mock.patch('urllib.request.urlopen',return_value=io.BytesIO(b'wrong')) as op:
                self.assertRaises(Blocked,public_fetch,'x','0'*40);self.assertEqual(op.call_count,1)
        def test_source_api_fallback(self):
            data=b'public source';pin=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            reply=canon(dict(sha=pin,encoding='base64',content=base64.b64encode(data).decode()))
            with mock.patch('urllib.request.urlopen',side_effect=[OSError('offline raw endpoint'),io.BytesIO(reply)]):self.assertEqual(public_fetch('x',pin),data)
        def test_header_coverage(self):self.assertEqual(set(HEADER_PINS),set(TASKS))
        def test_published_performance_sizes(self):
            self.assertEqual(SPECS['gemm']['perf'],[(128,128,128),(256,256,256)])
            self.assertEqual(SPECS['syrk']['perf'],[(256,256,1),(512,512,1)])
            self.assertEqual(SPECS['convolution-3d']['perf'],[(64,64,64),(128,128,128)])
        def test_report_has_scope_adaptations(self):self.assertGreater(len(PROTOCOL['host_adaptations']),5);self.assertIn('not all',PROTOCOL['selection'])
        def test_evaluate_all_shapes_and_hash_identity_mock(self):
            group=plan_document(self.info())['groups'][0];task=group['task'];records=[];calls=[]
            for sh in shapes(task):
                d=self.root/'preflight'/task/shape_id(sh)
                for label in ('baseline','identity'):
                    save(d/label/'kernel.cubin',baseline_source(task).encode());save(d/label/'kernel.ptx',baseline_source(task).encode())
                BASES[task,sh]=(d/'baseline/kernel.cubin',d/'identity/kernel.cubin')
            for r in group['requests']:
                source=baseline_source(task);save(self.root/'groups'/group['label']/'generation'/r['condition']/'candidate.cu',source.encode())
                records.append({k:r[k] for k in ('id','task','condition','seed')}|dict(generation_status='saved',source_sha256=sha(source.encode()),source_equals_original=True,block=SPECS[task]['base']))
            def comp(t,sh,src,d):
                save(d/'kernel.cubin',src.encode());save(d/'kernel.ptx',src.encode());return dict(ok=True,cubin_sha256=sha(src.encode()),ptx_sha256=sha(src.encode()))
            def nr(t,sh,d,mode,**kw):calls.append((mode,sh));return dict(ok=True,rows=self.rows())
            with mock.patch.dict(globals(),compile_checked=comp,validate_object=lambda *a,**k:{'passed':True},numeric=nr),mock.patch.object(P,'no_other_gpu'),mock.patch.object(P,'telemetry',return_value={}):
                outcomes=evaluate_group(group,records,self.so)
            self.assertEqual(len(outcomes),5);self.assertEqual(len(calls),20)
            self.assertTrue(all(o['correctness_passed'] and len(o['measurements'])==2 for o in outcomes))
            self.assertTrue(all(m['same_cubin'] and m['measurement_valid'] for o in outcomes for m in o['measurements']))
        def test_worker_reaches_90_terminal_and_final_ack_with_mocks(self):
            stages=[];save(self.root/'control/runner.py',b'# mocked runner')
            def source_intake():
                for t in TASKS:save(self.root/'setup/sources'/(t+'.cu'),baseline_source(t).encode())
            def hb():
                shutil.copyfile(self.so,self.root/'setup/host-helper.so');return self.root/'setup/host-helper.so'
            def gen(A,assets,g):
                stages.append(('gen',g['label']));save(self.root/'groups'/g['label']/'generation/raw',b'synthetic')
                P.STATE['generation_calls']=P.STATE.get('generation_calls',0)+5
                return [{k:r[k] for k in ('id','task','condition','seed')}|dict(generation_status='invalid_generation',error='fixture') for r in g['requests']]
            def ev(g,rs,h):
                stages.append(('eval',g['label']));return [r|dict(correctness_passed=False,stage='generation_failed',measurements=[]) for r in rs]
            A=types.SimpleNamespace(cached_assets=lambda:('bin','model',{}, {},{},{}),gpu_info=lambda:{'uuid':P.EXPECTED_GPU},verify_cached_unchanged=lambda _:None)
            fakefile=self.root/'fake-sanit';save(fakefile,b'test');real=Path('/usr/local/cuda-12.8/lib64/libnvrtc.so')
            orig_exists=Path.exists
            def exist(p):return True if p==real else orig_exists(p)
            orig_hfile=hfile
            def h(p):return '0'*64 if Path(p)==real else orig_hfile(p)
            with mock.patch.dict(globals(),intake=source_intake,build_helper=hb,baseline_preflight=lambda h:stages.append(('controls',None)),generate_group=gen,evaluate_group=ev,checkpoint=lambda src,label:stages.append(('checkpoint',label)),wait_ack=lambda rec:stages.append(('ack',rec['label'])),hfile=h),mock.patch.object(P,'remote_guard'),mock.patch.object(P,'no_other_gpu'),mock.patch.object(P,'native_info',return_value=self.info()),mock.patch.object(P,'module_a',return_value=A),mock.patch.object(P,'telemetry',return_value={}),mock.patch.object(P,'sanitizer_path',return_value=str(fakefile)),mock.patch('pathlib.Path.exists',exist),mock.patch.object(P,'lock',return_value=contextlib.nullcontext()),mock.patch('signal.signal'):
                worker(True)
            doc=parse(read(self.root/'final/summary.json'))
            self.assertEqual(doc['generation_calls'],90);self.assertEqual(doc['candidate_slots'],90);self.assertTrue((self.root/'completion.json').exists())
            self.assertEqual(sum(s[0]=='gen' for s in stages),18);self.assertEqual(sum(s[0]=='eval' for s in stages),18)
            self.assertLess(stages.index(('controls',None)),next(i for i,x in enumerate(stages) if x[0]=='gen'))
        def test_cpp_timing_driver_abi_real_child(self):
            src=self.root/'fake-driver.cpp';lib=self.root/'fake-driver.so'
            src.write_text(r'''#include <stdint.h>
#include <stddef.h>
static int nr=0,nl=0,stage=0,bad=0;static uintptr_t last=0;
extern "C" int cuMemcpyDtoD_v2(uint64_t,uint64_t,size_t){++nr;stage=0;return 0;}
extern "C" int cuEventRecord(void*event,void*){if((uintptr_t)event==1){if(stage!=0)++bad;stage=1;}else stage=2;return 0;}
extern "C" int cuLaunchKernel(void*fn,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,unsigned,void*,void**,void**){if(stage!=1)++bad;++nl;last=(uintptr_t)fn;return 0;}
extern "C" int cuEventSynchronize(void*){return stage==2?0:9;}
extern "C" int cuEventElapsedTime(float*out,void*,void*){*out=last==11?1.0f:2.0f;return 0;}
extern "C" int count_reset(){return nr;}extern "C" int count_launch(){return nl;}extern "C" int bad_order(){return bad;}
''')
            c=subprocess.run(['g++','-shared','-fPIC',str(src),'-o',str(lib)],capture_output=True,text=True);self.assertEqual(c.returncode,0,c.stderr)
            code='''import ctypes as c,sys
L=c.CDLL(sys.argv[1],mode=c.RTLD_GLOBAL);H=c.CDLL(sys.argv[2]);V=c.c_void_p;I=c.c_int;Q=c.c_uint64;F=c.c_float
f=H.suite_time;f.restype=I;f.argtypes=[V,c.POINTER(V),I,I,I,I,I,I,c.POINTER(I),I,c.POINTER(Q),c.POINTER(Q),c.POINTER(Q),V,V,c.POINTER(F)]
s=I(1);p=(V*1)(c.cast(c.byref(s),V));a=(Q*2)(1,2);b=(Q*2)(3,4);z=(Q*2)(4,4);out=F()
assert f(V(22),p,1,1,32,8,3,4,c.byref(s),2,a,b,z,V(1),V(2),c.byref(out))==0
assert out.value==6 and L.count_reset()==6 and L.count_launch()==12 and L.bad_order()==0
assert f(V(11),p,1,1,32,8,3,-1,c.byref(s),2,a,b,z,V(1),V(2),c.byref(out))==0
assert out.value==3 and L.count_reset()==12 and L.count_launch()==15 and L.bad_order()==0
print('CPP_DRIVER_ABI_RESET_EVENT_ORDER_AND_DISTINCT_FUNCTIONS=PASS')
'''
            r=subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(lib),str(self.so)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertIn('=PASS',r.stdout)
    class FakeGPU:
        def __init__(self):self.mem={};self.next=1024;self.launches=0
        def buffer(self,n):p=self.next;self.next+=n+1024;self.mem[p]=bytearray(n);return p
        def put(self,p,r):
            for b,a in self.mem.items():
                if b<=p and p+len(r)<=b+len(a):a[p-b:p-b+len(r)]=r;return
            raise RuntimeError('mock pointer out of range')
        def get(self,p,n):
            for b,a in self.mem.items():
                if b<=p and p+n<=b+len(a):return bytes(a[p-b:p-b+n])
            raise RuntimeError('mock pointer out of range')
        def ck(self,n,*args):
            if n=='cuLaunchKernel':self.launches+=1
        def event(self):return ct.c_void_p(11)
        def free_buffers(self):self.mem.clear()
    with contextlib.redirect_stdout(io.StringIO()):
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    need(result.wasSuccessful(),'Main-cohort self tests failed')
    print('GPU002_SELF_TEST=PASS tests='+str(result.testsRun))
    print('TEST_SCOPE=HOST_CPP_ORACLE_VS_SCALAR_ORIGINAL_CUDA_AND_MOCK_CONTROL_FLOW; NO_REAL_A40_NVRTC_SANITIZER_OR_SSH_EXECUTION')


def main():
    configure();P.worker=worker;P.run_numeric_job=numeric_job;P.local=local;P.self_test=self_test
    P.main()
if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('INTERRUPTED; NO_AUTOMATIC_RETRY',file=sys.stderr);sys.exit(130)
    except BaseException as e:
        if isinstance(e,SystemExit):raise
        print('GPU002_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(2)
