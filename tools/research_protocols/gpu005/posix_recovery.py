#!/usr/bin/env python3
"""GPU005 L4 recovery: private POSIX work area, checkpoint mirrors, no generation.
Read-only preservation of the exact pre-candidate chown failure. Does not disable
chown, setpriv, CUDA validation, environment pins or checkpoint acknowledgment.
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
import argparse, ast, base64, contextlib, ctypes, gzip, hashlib, inspect, json
import os, re, shutil, stat, subprocess, sys, tempfile, time, types, unittest
from pathlib import Path
from unittest import mock
BASE_SHA = '421892f14e556c0b4dece66c0a457446459380b21c0c1514eeb8efe1bf5a3eaf'
BASE_EMBED = _public.encoded_module('portability.py')
BASE_RAW = gzip.decompress(base64.b64decode(BASE_EMBED,validate=True))
if hashlib.sha256(BASE_RAW).hexdigest()!=BASE_SHA:
    raise RuntimeError('Embedded original runner changed')
T = _public.load_module('portability.py', BASE_SHA)

C,P=T.C,T.P
read,save,parse,canon,sha,hfile,need,now=T.read,T.save,T.parse,T.canon,T.sha,T.hfile,T.need,T.now
MIB=1024**2
ORIGIN=Path('/workspace/gpu005-portability-v1')
WORK=Path('/tmp/gpu005-l4-posix-v1')
MIRROR=Path('/workspace/gpu005-l4-posix-checkpoints-v1')
LOCAL_REL=Path('workspace/cpu-conditioned-llm-optimization/runs/gpu005-l4-posix-recovery-v1')
BUNDLE_SHA='57ba08d41c9e6b55a6dfafb9bc8d26d697fcdc958c0a6588eb83e1d1e5000ada'
GPU_UUID='GPU-REPLACE-WITH-VERIFIED-UUID'
HOST_FP='SHA256:REPLACE_WITH_VERIFIED_HOST_KEY'
SCHEMA='gpu005-l4-posix-storage-recovery-v1'
ORIGINAL_CONFIGURE=T.configure_runtime
ORIGINAL_WORKER=T.worker
ORIGINAL_ARCHIVE=P.archive_dir
T.ROOT=WORK


def put_once(path,raw):
    path=T.safe(path)
    if path.exists():need(read(path,256*MIB)==raw,'Existing file differs; not overwritten: '+str(path))
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        part=path.with_name(path.name+'.partial-'+os.urandom(6).hex())
        save(part,raw)
        need(hfile(part)==sha(raw),'Written file hash mismatch')
        # All production callers hold the run/controller lock.
        need(not path.exists(),'Destination appeared while writing')
        os.rename(part,path)
    need(hfile(path)==sha(raw),'Stored bytes differ')


def tree_bytes(root,limit=64*MIB):
    root=T.safe(root);need(root.is_dir(),'Missing original failure directory')
    files={};total=0
    for parent,dirs,names in os.walk(root,followlinks=False):
        for n in dirs:
            p=T.safe(Path(parent)/n);need(p.is_dir(),'Unsafe directory in old run')
        for n in names:
            p=T.safe(Path(parent)/n);b=read(p,32*MIB);total+=len(b)
            need(total<=limit and len(files)<5000,'Failure snapshot too large')
            files[p.relative_to(root).as_posix()]=b
    return files


def pid_alive_strict(rec):
    need(type(rec.get('pid')) is int and isinstance(rec.get('ticks'),str),'Invalid original launch identity')
    try:s=Path('/proc',str(rec['pid']),'stat').read_text()
    except FileNotFoundError:return False
    fields=s.split(') ',1)[1].split()
    return fields[0]!='Z' and fields[19]==rec['ticks']


def validate_failed_files(files,target,bundle_sha,alive=pid_alive_strict):
    need(sha(files.get('control/runner.py',b''))==BASE_SHA,'Original runner differs')
    need(parse(files['control/target.json'])==target,'Original target differs')
    need(sha(files.get('inputs/portable-inputs.tar.gz',b''))==bundle_sha,'Original bundle differs')
    need(not alive(parse(files['launch.json'])),'Original worker is still active; it is not stopped automatically')
    progress=parse(files['progress.json']);failure=parse(files['failure.json'])
    need(progress.get('phase')=='BLOCKED','Original run is not blocked')
    for k in ('evaluation_terminal','new_generation_calls'):
        need(type(progress.get(k)) is int and progress[k]==0,'Original work already started or status missing: '+k)
    expected="Operation not permitted: '/workspace/gpu005-portability-v1/preflight/gemm/1x1x1/baseline'"
    need(failure.get('error','').startswith('PermissionError: [Errno 1] '+expected),'Not the known preflight chown failure')
    need('os.chown(dest,65534,65534)' in failure.get('traceback',''),'Expected chown site not recorded')
    names=set(files)
    need({n for n in names if n.startswith('receipts/')}=={'receipts/setup.json'},'Numerical checkpoints already exist')
    need('completion.json' not in names,'Original run already complete')
    forbidden=('groups/','exploration/','confirmation/','selection/','block-validation/','final/')
    need(not any(n.startswith(forbidden) for n in names),'Candidate/control evaluation evidence exists')
    for n in names:
        if n.startswith('preflight/'):
            need(n.startswith('preflight/gemm/host-replay/'),'Unexpected preflight work: '+n)
        need(not n.endswith(('/job.json','/numeric-result.json','/parent-result.json','.ptx','.cubin')),
             'Numerical job may have started: '+n)
    r=parse(files['receipts/setup.json'])
    need(r.get('label')=='setup','Unexpected original receipt')
    archived_setup=T.read_archive(files['archives/setup.tar.gz'],r)
    for n,b in archived_setup.items():
        need(files.get('setup/'+n)==b,'Original setup file differs from verified checkpoint: '+n)
    return {'original_failure':failure['error'],'original_evaluation_terminal':0,
            'old_gpu_numeric_jobs_observed':0,'new_generation_calls':0,
            'old_host_helper_and_scalar_replay_may_have_run':True,
            'original_file_hashes':{n:sha(b) for n,b in files.items()}}


def mount_record(path):
    path=str(T.safe(path));matches=[]
    def dec(v):return re.sub(r'\\([0-7]{3})',lambda m:chr(int(m[1],8)),v)
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1);a,b=left.split(),right.split();m=dec(a[4])
        if path==m or path.startswith(m.rstrip('/')+'/'):
            matches.append({'target':m,'filesystem':b[0],'source':dec(b[1]),'options':a[5]})
    need(matches,'Mount identity unavailable')
    return max(matches,key=lambda x:len(x['target']))


def private_workspace_checks(root,helper):
    """Test the real chown + dropped-UID path on the NEW local work filesystem."""
    root=T.safe(root);helper=T.safe(helper)
    need(os.geteuid()==0,'Filesystem acceptance must run in the authorized root Pod')
    need(root.stat().st_uid==0 and not root.stat().st_mode&0o022,'Work root must be root-owned and not group/world writable')
    mount=mount_record(root)
    need(mount['filesystem'] in ('overlay','ext4','xfs','btrfs','ext3','ext2'),
         'Work filesystem is not an accepted local disk: '+mount['filesystem'])
    free=shutil.disk_usage(root).free
    need(free>=4*1024**3,'Local work disk needs at least 4GiB; no automatic disk changes')
    base=Path(tempfile.mkdtemp(prefix='posix-check-',dir=root));base.chmod(0o755)
    protected=base/'root-owned.txt';save(protected,b'CONTROL_READ_ONLY');protected.chmod(0o444)
    so=base/'trusted-helper.so';save(so,read(helper));so.chmod(0o555)
    child=base/'numeric';child.mkdir(mode=0o755);os.chown(child,65534,65534)
    st=child.stat();need((st.st_uid,st.st_gid)==(65534,65534),'chown returned without expected ownership')
    code=r'''import ctypes,json,os,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]);guard=pathlib.Path(sys.argv[2]);lib=sys.argv[3]
assert os.geteuid()==65534 and os.getegid()==65534
s={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in x}
for k in ('CapEff','CapPrm','CapInh','CapBnd','CapAmb'):assert int(s[k],16)==0
assert s['NoNewPrivs']=='1'
p=root/'test.partial'
with p.open('xb') as f:f.write(b'POSIX_WRITE_OK');f.flush();os.fsync(f.fileno())
p.chmod(0o400);p.rename(root/'test.bin');assert (root/'test.bin').read_bytes()==b'POSIX_WRITE_OK'
assert guard.read_bytes()==b'CONTROL_READ_ONLY'
try:
    with guard.open('ab'):pass
except PermissionError:pass
else:raise RuntimeError('Unprivileged process can modify control file')
x=root/'exec-check';x.write_text('#!/bin/sh\nexit 0\n');x.chmod(0o500)
subprocess.run([str(x)],check=True,timeout=10)
ctypes.CDLL(lib)
print(json.dumps({'euid':os.geteuid(),'egid':os.getegid(),'capabilities_zero':True,'no_new_privileges':True,'write_fsync_rename_chmod':True,'exec_and_dlopen':True,'control_write_denied':True}))
'''
    cp=subprocess.run(P.unpriv_prefix()+['/usr/bin/python3','-I','-S','-B','-c',code,str(child),str(protected),str(so)],
                      env=P.clean_env(),capture_output=True,timeout=30)
    need(cp.returncode==0,'Nonroot local work test failed: '+cp.stderr.decode(errors='replace')[-2000:])
    return {'path':str(root),'test_directory':str(base),'mount':mount,'observed_free_bytes':free,
            'chown_65534_passed':True,'unprivileged':parse(cp.stdout),
            'temporary_container_storage':True,'quota_and_persistence_not_proven':True}


def mirror_probe(mirror):
    mirror=T.safe(mirror);mirror.mkdir(parents=True,exist_ok=True)
    d=Path(tempfile.mkdtemp(prefix='io-check-',dir=mirror))
    b=b'GPU005_CHECKPOINT_STORAGE_CHECK\n';put_once(d/'probe.bin',b)
    return {'path':str(mirror),'mount':mount_record(mirror),'write_fsync_rename_hash_passed':True,
            'no_chown_required':True,'quota_and_persistence_not_proven':True}


def scoped_target(t):
    T.validate_target(t,True)
    need(t['profile']=='L4' and t['expected_gpu_uuid']==GPU_UUID and t['host_fingerprint']==HOST_FP,
         'This recovery is only for the recorded L4 allocation/host key')


def original_snapshot(target,bundle_sha):
    files=tree_bytes(ORIGIN)
    report=validate_failed_files(files,target,bundle_sha)
    return files,report


def prepare_remote_storage(target):
    scoped_target(target);T.remote_guard()
    need(not (WORK/'launch.json').exists(),'Recovery worker was already launched; use --watch instead')
    with P.lock('/workspace/gpu-code-pilot-exclusive.lock'):
        T.check_runtime(target)
        files,old=original_snapshot(target,BUNDLE_SHA)
        # Preserve all old files, not just the last error; never rename/delete the original.
        dest=WORK/'recovery';dest.mkdir(exist_ok=True)
        recpath=dest/'failed-origin-receipt.json'
        if recpath.exists():
            r=parse(read(recpath));prior=T.read_archive(read(dest/'failed-origin.tar.gz'),r)
            need(prior==files,'Original failed run changed after snapshot')
        else:
            raw,r=T.make_archive(files,'failed-origin')
            put_once(dest/'failed-origin.tar.gz',raw);put_once(recpath,canon(r))
        helper=ORIGIN/'setup/host-helper.so'
        expected=parse(files['setup/host-helper-identity.json'])['sha256']
        need(hfile(helper)==expected,'Original trusted host helper changed')
        P.public_dirs(WORK/'control');P.public_dirs(WORK/'inputs')
        WORK.chmod(0o755)
        test=private_workspace_checks(WORK,helper)
        mirror=mirror_probe(MIRROR)
        report={'schema':SCHEMA,'target_sha256':sha(canon(target)), 'input_bundle_sha256':BUNDLE_SHA,
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'failed_origin_receipt':r,'original_file_hashes':old['original_file_hashes'],
            'work_storage':test,'checkpoint_mirror':mirror,'original_mount':mount_record(ORIGIN),
            'new_generation_calls':0,'provider_http_calls':0,'candidate_gpu_execution_started':False,
            'original_files_modified':False,'utc':now()}
        raw=read(dest/'failed-origin.tar.gz')
        put_once(MIRROR/'recovery/failed-origin.tar.gz',raw)
        put_once(MIRROR/'recovery/failed-origin-receipt.json',canon(r))
        # Storage acceptance can be refreshed ONLY before any new worker launch, with no job execution.
        T.atomic(dest/'storage-acceptance.json',report)
        T.atomic(MIRROR/'recovery/storage-acceptance.json',report)
        return report


def validate_storage_gate(target):
    scoped_target(target)
    d=WORK/'recovery';report=parse(read(d/'storage-acceptance.json'))
    ack=parse(read(d/'local-preservation-ack.json'))
    need(report['schema']==SCHEMA and report['target_sha256']==sha(canon(target)),'Storage target pin mismatch')
    need(report['input_bundle_sha256']==BUNDLE_SHA and hfile(WORK/'inputs/portable-inputs.tar.gz')==BUNDLE_SHA,'Storage input pin mismatch')
    need(report['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'Pod restarted; work storage must not be assumed preserved')
    need(ack=={'failed_origin_sha256':report['failed_origin_receipt']['sha256'],
               'target_sha256':report['target_sha256'],'input_bundle_sha256':BUNDLE_SHA},'Missing local preservation acknowledgment')
    _,current=original_snapshot(target,BUNDLE_SHA)
    need(current['original_file_hashes']==report['original_file_hashes'],'Original failure evidence changed')
    need(report['work_storage']['chown_65534_passed'] is True and report['checkpoint_mirror']['write_fsync_rename_hash_passed'] is True,'Storage acceptance not passed')
    need(shutil.disk_usage(WORK).free>=4*1024**3,'Local work disk below 4GiB')
    return report


def mirrored_archive(src,label):
    need(shutil.disk_usage(WORK).free>=512*MIB,'Work disk low; keep records, do not delete previous data')
    r=ORIGINAL_ARCHIVE(src,label);raw=read(WORK/'archives'/(label+'.tar.gz'),256*MIB)
    T.read_archive(raw,r)
    put_once(MIRROR/'archives'/(label+'.tar.gz'),raw)
    put_once(MIRROR/'receipts'/(label+'.json'),canon(r))
    print('GPU005_STORAGE_MIRROR_VERIFIED '+label,flush=True)
    return r


def configure_runtime(target,root=None):
    ans=ORIGINAL_CONFIGURE(target,root if root is not None else WORK)
    P.archive_dir=mirrored_archive
    return ans
T.configure_runtime=configure_runtime


def worker(target,allow):
    try:
        os.umask(0o022)
        P.public_dirs(WORK/'control');P.public_dirs(WORK/'inputs')
        report=validate_storage_gate(target)
        # The POSIX prerequisite is re-tested under the clean worker environment.
        newtest=private_workspace_checks(WORK,ORIGIN/'setup/host-helper.so')
        T.jw(WORK/'setup/storage-recovery.json',report)
        T.jw(WORK/'setup/worker-posix-recheck.json',newtest)
        T.jw(WORK/'final/storage-recovery.json',report)
        print('GPU005_POSIX_WORK_STORAGE_ACCEPTED; UNPRIVILEGED_EXECUTION_RETAINED',flush=True)
        return ORIGINAL_WORKER(target,allow)
    except BaseException as exc:
        if not (WORK/'failure.json').exists():
            import traceback
            P.atomic(WORK/'failure.json',{'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'utc':now()})
            P.update(phase='BLOCKED',error=str(exc))
        raise
T.worker=worker


def local_prepare_and_run(args):
    need(os.geteuid()!=0,'Run locally from WSL without sudo')
    source=T.safe(args.prepared_dir);local=T.safe(args.recovery_dir)
    need(local!=source and not local.is_relative_to(source),'Use a separate local recovery directory')
    target=parse(read(args.target));scoped_target(target)
    raw=read(source/'portable-inputs.tar.gz');r=parse(read(source/'portable-inputs-receipt.json'))
    need(sha(raw)==BUNDLE_SHA,'Wrong source candidate bundle')
    T.bundle_data(raw,r)
    oldlocal=source/'results/l4'
    oldsetup=parse(read(oldlocal/'setup-receipt.json'))
    T.read_archive(read(oldlocal/'setup.tar.gz'),oldsetup)
    local.mkdir(parents=True,exist_ok=True)
    with P.lock(local/'recovery-controller.lock'):
        put_once(local/'portable-inputs.tar.gz',raw);put_once(local/'portable-inputs-receipt.json',canon(r))
        put_once(local/'runner.py',read(__file__,2*MIB));put_once(local/'target-l4-pinned.json',canon(target))
        con=T.Connection(target)
        try:
            upload=T.installation_archive({'control/runner.py':read(__file__,2*MIB),
                'control/target.json':canon(target),'inputs/portable-inputs.tar.gz':raw,
                'inputs/portable-inputs-receipt.json':canon(r)})
            print(con.run(['/usr/bin/python3','-I','-S','-B','-c',T.installation_code(sha(upload))],data=upload).decode().strip())
            report=parse(con.run(T.remote_command('--_prepare_storage'),timeout=300))
            oldr=report['failed_origin_receipt']
            oldraw=con.run(T.remote_command('--_send_failure_snapshot'),timeout=300)
            oldfiles=T.read_archive(oldraw,oldr)
            need(parse(oldfiles['receipts/setup.json'])==oldsetup,'Old failure snapshot does not match WSL setup receipt')
            put_once(local/'recovery/failed-origin.tar.gz',oldraw)
            put_once(local/'recovery/failed-origin-receipt.json',canon(oldr))
            T.atomic(local/'recovery/storage-acceptance.json',report)
            print('GPU005_FAILED_RUN_LOCAL_COPY_VERIFIED='+str(local/'recovery/failed-origin.tar.gz'),flush=True)
            print(json.dumps({'original_mount':report['original_mount'],'work_storage':report['work_storage'],
                'checkpoint_mirror':report['checkpoint_mirror'],'new_generation_calls':0},indent=2))
            print(con.run(T.remote_command('--_storage_ack',oldr['sha256'])).decode().strip())
        finally:con.close()
    print('NEXT: unchanged 85 candidates; no provider API; fresh GPU preflight in local POSIX work area.',flush=True)
    T.local_run('run',local/'target-l4-pinned.json',local,args.allow_ephemeral_with_local_checkpoints)


def remote_extra(args):
    target=T.remote_target();configure_runtime(target);T.remote_guard()
    if args._prepare_storage:
        print(json.dumps(prepare_remote_storage(target)));return
    if args._send_failure_snapshot:
        d=WORK/'recovery';r=parse(read(d/'failed-origin-receipt.json'));raw=read(d/'failed-origin.tar.gz')
        T.read_archive(raw,r);sys.stdout.buffer.write(raw);return
    if args._storage_ack:
        r=parse(read(WORK/'recovery/failed-origin-receipt.json'))
        need(args._storage_ack==r['sha256'],'Wrong preservation ACK')
        put_once(WORK/'recovery/local-preservation-ack.json',canon({'failed_origin_sha256':r['sha256'],
            'target_sha256':sha(canon(target)),'input_bundle_sha256':BUNDLE_SHA}))
        print('GPU005_STORAGE_RECOVERY_READY; NO_GPU_CANDIDATE_EXECUTION_YET')


def original_tests(numerical=False):
    # Run the EXACT original distribution separately; storage recovery does not change its tests.
    with tempfile.TemporaryDirectory(prefix='gpu005-pinned-regression-') as d:
        p=Path(d)/'original.py';p.write_bytes(BASE_RAW)
        cp=subprocess.run([sys.executable,'-I','-S','-B',str(p),
            '--numeric-core-self-test' if numerical else '--self-test'],timeout=180)
        need(cp.returncode==0,'Pinned original regression failed')


def storage_self_test():
    class Tests(unittest.TestCase):
        def setUp(self):
            self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        def tearDown(self):self.tmp.cleanup()
        def fixture(self):
            rdata,r=T.make_archive({'fixture.txt':b'known'},'setup')
            target={'fixture':True};bundle=b'fixture bundle'
            f={'control/runner.py':BASE_RAW,'control/target.json':canon(target),
                'inputs/portable-inputs.tar.gz':bundle,'launch.json':canon({'pid':111,'ticks':'222'}),
                'progress.json':canon({'phase':'BLOCKED','new_generation_calls':0,'evaluation_terminal':0}),
                'failure.json':canon({'error':"PermissionError: [Errno 1] Operation not permitted: '/workspace/gpu005-portability-v1/preflight/gemm/1x1x1/baseline'",'traceback':'os.chown(dest,65534,65534)'}),
                'receipts/setup.json':canon(r),'archives/setup.tar.gz':rdata,'setup/fixture.txt':b'known',
                'preflight/gemm/host-replay/1x1x1.cpp':b'trusted host replay'}
            return f,target,sha(bundle)
        def valid(self,f,t,h):return validate_failed_files(f,t,h,alive=lambda x:False)
        def reject(self,mutator):
            f,t,h=self.fixture();mutator(f)
            with self.assertRaises(Exception):self.valid(f,t,h)
        def test_original_full_hash(self):self.assertEqual(sha(BASE_RAW),BASE_SHA)
        def test_numeric_core_hash_unchanged(self):self.assertEqual(T.CORE_SHA,'afe6858e7d510084a40e97aa81c14fa9da907fc80bc23f4a8b76f1eccf14e90a')
        def test_numeric_chown_and_uid_retained(self):
            tree=ast.parse(BASE_RAW);n=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='numeric')
            text=ast.get_source_segment(BASE_RAW.decode(),n)
            self.assertIn('os.chown(dest,65534,65534)',text);self.assertIn('P.unpriv_prefix()',text)
            self.assertEqual(T.numeric.__code__.co_filename,'<pinned-gpu005-portability-v1>')
        def test_known_failure_accepted(self):
            f,t,h=self.fixture();self.assertEqual(self.valid(f,t,h)['old_gpu_numeric_jobs_observed'],0)
        def test_different_error_refused(self):self.reject(lambda f:f.update({'failure.json':canon({'error':'other'})}))
        def test_wrong_runner_refused(self):self.reject(lambda f:f.update({'control/runner.py':b'bad'}))
        def test_wrong_target_refused(self):self.reject(lambda f:f.update({'control/target.json':b'{}'}))
        def test_wrong_bundle_refused(self):self.reject(lambda f:f.update({'inputs/portable-inputs.tar.gz':b'bad'}))
        def test_old_running_refused(self):
            f,t,h=self.fixture()
            with self.assertRaises(Exception):validate_failed_files(f,t,h,alive=lambda x:True)
        def test_missing_count_refused(self):self.reject(lambda f:f.update({'progress.json':canon({'phase':'BLOCKED'})}))
        def test_work_started_refused(self):self.reject(lambda f:f.update({'progress.json':canon({'phase':'BLOCKED','new_generation_calls':0,'evaluation_terminal':1})}))
        def test_other_checkpoint_refused(self):self.reject(lambda f:f.update({'receipts/original-controls.json':b'{}'}))
        def test_completion_refused(self):self.reject(lambda f:f.update({'completion.json':b'{}'}))
        def test_candidate_group_refused(self):self.reject(lambda f:f.update({'groups/g/outcomes.json':b'[]'}))
        def test_baseline_job_refused(self):self.reject(lambda f:f.update({'preflight/gemm/1x1x1/baseline/job.json':b'{}'}))
        def test_compiled_cubin_refused(self):self.reject(lambda f:f.update({'preflight/gemm/1x1x1/baseline/kernel.cubin':b'x'}))
        def test_archive_tamper_refused(self):self.reject(lambda f:f.update({'archives/setup.tar.gz':b'bad'}))
        def test_snapshot_does_not_change_source(self):
            p=self.d/'old';p.mkdir();(p/'x').write_bytes(b'old');before=tree_bytes(p);raw,r=T.make_archive(before,'failed-origin')
            self.assertEqual(tree_bytes(p),before);self.assertEqual(T.read_archive(raw,r),before)
        def test_snapshot_symlink_refused(self):
            p=self.d/'old';p.mkdir();(p/'x').symlink_to('/etc/passwd')
            with self.assertRaises(Exception):tree_bytes(p)
        def test_snapshot_directory_symlink_refused(self):
            p=self.d/'old';p.mkdir();(p/'x').symlink_to('/tmp')
            with self.assertRaises(Exception):tree_bytes(p)
        def test_put_once_unchanged(self):
            p=self.d/'x';put_once(p,b'abc');ino=p.stat().st_ino;put_once(p,b'abc');self.assertEqual(ino,p.stat().st_ino)
        def test_put_once_conflict_refused(self):
            p=self.d/'x';put_once(p,b'abc')
            with self.assertRaises(Exception):put_once(p,b'def')
            self.assertEqual(p.read_bytes(),b'abc')
        def test_put_once_symlink_refused(self):
            p=self.d/'x';p.symlink_to('/tmp/x')
            with self.assertRaises(Exception):put_once(p,b'x')
        def test_mount_lookup(self):self.assertTrue(mount_record('/tmp')['filesystem'])
        def test_no_new_generation(self):
            with self.assertRaises(Exception):T.forbid_generation()
        def test_remote_work_separate(self):
            self.assertNotEqual(WORK,ORIGIN);self.assertFalse(WORK.is_relative_to(ORIGIN));self.assertEqual(WORK.parent,Path('/tmp'))
        def test_mirror_roundtrip(self):
            global WORK,MIRROR
            oldw,oldm=WORK,MIRROR;op=P.ROOT
            try:
                WORK=self.d/'work';MIRROR=self.d/'mirror';WORK.mkdir();P.ROOT=WORK
                d=WORK/'setup';d.mkdir();save(d/'x',b'known')
                r=mirrored_archive(d,'setup')
                self.assertEqual(T.read_archive(read(MIRROR/'archives/setup.tar.gz'),r),{'x':b'known'})
            finally:WORK,MIRROR=oldw,oldm;P.ROOT=op
        def test_mirror_probe_no_chown(self):
            with mock.patch.object(os,'chown',side_effect=AssertionError('must not chown mirror')):
                self.assertTrue(mirror_probe(self.d/'mirror')['no_chown_required'])
        def test_uid_current_process_alive(self):
            self.assertTrue(pid_alive_strict({'pid':os.getpid(),'ticks':P.cgroup_start(os.getpid())}))
        def test_new_gate_before_worker(self):
            with mock.patch(__name__+'.validate_storage_gate',side_effect=RuntimeError('gate blocked')),\
                 mock.patch.object(P,'atomic'),mock.patch.object(P,'update'),\
                 mock.patch(__name__+'.ORIGINAL_WORKER') as cb:
                with self.assertRaises(RuntimeError):worker({},True)
                cb.assert_not_called()
        def test_setup_record_changes_refused(self):self.reject(lambda f:f.update({'setup/fixture.txt':b'changed'}))
        def test_complete_storage_prepare_and_ack_gate_mock_device(self):
            global WORK,MIRROR,ORIGIN,BUNDLE_SHA
            ow,om,oo,ob=WORK,MIRROR,ORIGIN,BUNDLE_SHA
            pr,gr=P.ROOT,T.ROOT
            try:
                WORK=self.d/'work';MIRROR=self.d/'mirror';ORIGIN=self.d/'origin';WORK.mkdir();ORIGIN.mkdir()
                P.ROOT=WORK;T.ROOT=WORK
                f,t,h=self.fixture();BUNDLE_SHA=h
                helper=b'trusted fixture';f['setup/host-helper.so']=helper
                f['setup/host-helper-identity.json']=canon({'sha256':sha(helper)})
                sr,srec=T.make_archive({n[6:]:b for n,b in f.items() if n.startswith('setup/')},'setup')
                f['archives/setup.tar.gz']=sr;f['receipts/setup.json']=canon(srec)
                for n,b in f.items():save(ORIGIN/n,b)
                save(WORK/'inputs/portable-inputs.tar.gz',f['inputs/portable-inputs.tar.gz'])
                before=tree_bytes(ORIGIN)
                fake={'chown_65534_passed':True,'fixture_only':True}
                real_lock=P.lock
                with mock.patch(__name__+'.scoped_target'),mock.patch.object(T,'remote_guard'),\
                     mock.patch.object(T,'check_runtime'),mock.patch(__name__+'.private_workspace_checks',return_value=fake),\
                     mock.patch.object(P,'lock',side_effect=lambda x:real_lock(self.d/'test.lock')),\
                     mock.patch.object(shutil,'disk_usage',return_value=shutil._ntuple_diskusage(10*1024**3,1,9*1024**3)):
                    report=prepare_remote_storage(t)
                    self.assertEqual(tree_bytes(ORIGIN),before)
                    with self.assertRaises(Exception):validate_storage_gate(t)
                    ack={'failed_origin_sha256':report['failed_origin_receipt']['sha256'],
                         'target_sha256':sha(canon(t)),'input_bundle_sha256':h}
                    put_once(WORK/'recovery/local-preservation-ack.json',canon(ack))
                    self.assertEqual(validate_storage_gate(t)['target_sha256'],sha(canon(t)))
                    put_once(ORIGIN/'later.txt',b'external change')
                    with self.assertRaises(Exception):validate_storage_gate(t)
                    self.assertTrue((MIRROR/'recovery/failed-origin.tar.gz').exists())
            finally:
                WORK,MIRROR,ORIGIN,BUNDLE_SHA=ow,om,oo,ob;P.ROOT=pr;T.ROOT=gr
        @unittest.skipUnless(os.geteuid()==0,'Real chown/drop-UID test requires root; runtime repeats on Pod')
        def test_real_chown_nonroot_rw_exec_dlopen(self):
            # Test under /tmp so every parent is searchable by UID 65534.
            with tempfile.TemporaryDirectory(prefix='gpu005-posix-live-') as d:
                root=Path(d);root.chmod(0o755);src=root/'helper.cpp';src.write_text('extern "C" int f(){return 7;}')
                so=root/'helper.so';subprocess.run(['g++','-shared','-fPIC',str(src),'-o',str(so)],check=True,capture_output=True)
                with mock.patch.object(shutil,'disk_usage',return_value=shutil._ntuple_diskusage(10*1024**3,1,9*1024**3)):
                    report=private_workspace_checks(root,so)
                self.assertTrue(report['unprivileged']['exec_and_dlopen']);self.assertEqual(report['unprivileged']['euid'],65534)
        @unittest.skipUnless(os.geteuid()==0,'chown failure injection requires root path')
        def test_chown_failure_is_not_ignored(self):
            self.d.chmod(0o755);lib=self.d/'x.so';lib.write_bytes(b'not used')
            with mock.patch.object(os,'chown',side_effect=PermissionError(1,'denied')),\
                 mock.patch.object(shutil,'disk_usage',return_value=shutil._ntuple_diskusage(10*1024**3,1,9*1024**3)):
                with self.assertRaises(PermissionError):private_workspace_checks(self.d,lib)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    need(result.wasSuccessful(),'Storage recovery tests failed')
    print('GPU005_POSIX_RECOVERY_SELF_TEST=PASS tests='+str(result.testsRun)+' skipped='+str(len(result.skipped)))
    print('TEST_SCOPE=LOCAL_FAILURE_FIXTURES_ARCHIVES_AND_PRIVILEGE_TESTS; NO_REAL_SSH_OR_GPU_EXECUTION')


def main():
    p=argparse.ArgumentParser(description=__doc__);a=p.add_mutually_exclusive_group(required=True)
    for n in ('run','watch','collect','status','stop','self-test','portability-core-self-test','numeric-core-self-test',
              '_prepare_storage','_send_failure_snapshot','_launch','_worker','_status','_stop'):
        a.add_argument('--'+n,action='store_true')
    a.add_argument('--_storage_ack');a.add_argument('--_numeric');a.add_argument('--_send');a.add_argument('--_ack',nargs=2)
    p.add_argument('--target',type=Path)
    p.add_argument('--prepared-dir',type=Path,default=Path.home()/T.PREP_REL)
    p.add_argument('--recovery-dir',type=Path,default=Path.home()/LOCAL_REL)
    p.add_argument('--allow-ephemeral-with-local-checkpoints',action='store_true')
    args=p.parse_args()
    if args.self_test:storage_self_test();return 0
    if args.portability_core_self_test:original_tests();return 0
    if args.numeric_core_self_test:original_tests(True);return 0
    if args._prepare_storage or args._send_failure_snapshot or args._storage_ack:remote_extra(args);return 0
    if any((args._worker,args._launch,args._status,args._stop,args._numeric,args._send,args._ack)):
        return T.remote_mode(args)
    if args.run:
        need(args.target is not None and args.allow_ephemeral_with_local_checkpoints,'Explicit target and temporary-work permission required')
        local_prepare_and_run(args);return 0
    # Monitoring uses the pin preserved inside the NEW recovery directory, not the old results.
    target=args.recovery_dir/'target-l4-pinned.json';scoped_target(parse(read(target)))
    T.local_run(next(n for n in ('watch','collect','status','stop') if getattr(args,n)),target,args.recovery_dir,False)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (Exception,KeyboardInterrupt) as e:
        print('GPU005_POSIX_RECOVERY_BLOCKED: '+type(e).__name__+': '+str(e),file=sys.stderr)
        print('OLD_RESULTS_KEPT; NO_ROOT_CANDIDATE_FALLBACK; NO_GENERATION; NO_AUTOMATIC_RETRY_OR_POD_TERMINATION',file=sys.stderr)
        sys.exit(2)
