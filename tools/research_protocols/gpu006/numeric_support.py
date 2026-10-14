# Public plaintext numerical projection; no deployment/bootstrap/model startup/main.
from __future__ import annotations
import contextlib,ctypes as ct,datetime as dt,hashlib,json,math,os,re,resource,shutil,stat,statistics,struct,subprocess,sys,tempfile,time,traceback
from pathlib import Path
ROOT=Path("research-artifacts/gpu006")
WORK_DEADLINE=0
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

SIGNATURE = 'extern "C" __global__ void kernel(const float* A, const float* B, float* C, int M, int N, int K)'

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

def unpriv_prefix():
    return ['setpriv','--reuid=65534','--regid=65534','--clear-groups','--bounding-set=-all',
            '--inh-caps=-all','--ambient-caps=-all','--no-new-privs']

def sanitizer_path():
    candidates=['/usr/local/cuda-12.8/compute-sanitizer/compute-sanitizer','/usr/local/cuda-12.8/bin/compute-sanitizer']
    if shutil.which('compute-sanitizer'):candidates.insert(0,shutil.which('compute-sanitizer'))
    p=next((p for p in candidates if Path(p).is_file()),None)
    need(p is not None,'Compute Sanitizer missing; no generation is allowed before safety preflight')
    return p

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

def public_dirs(path):
    path=safe(path);need(path==ROOT or path.is_relative_to(ROOT),'Permission change outside new namespace')
    path.mkdir(parents=True,exist_ok=True)
    for p in (path,*path.parents):
        if p==ROOT or p.is_relative_to(ROOT):p.chmod(0o755)
        else:break
