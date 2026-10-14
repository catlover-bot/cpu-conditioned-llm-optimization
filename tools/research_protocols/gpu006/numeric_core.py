# Recorded GPU006 numerical source projected as plaintext.
# Original arithmetic/C oracle definitions are preserved; private live deployment is not reconstructed.
from __future__ import annotations
import contextlib,ctypes as ct,hashlib,json,math,os,re,resource,statistics,struct,traceback
from pathlib import Path
import numeric_support as P
ROOT=Path(__file__).resolve().parents[3]/"research-artifacts/gpu006/reference"
Blocked=P.Blocked
NumericFailure=P.NumericFailure
need=P.need
require=P.require
sha=P.sha
canon=P.canon
parse=P.parse
read=P.read
hfile=P.hfile
save=P.save
jw=P.jw
_ORIG_NUMERIC=P.run_numeric_job
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

def baseline_source(task):
    return read(ROOT/"sources"/(task+".cu")).decode()
