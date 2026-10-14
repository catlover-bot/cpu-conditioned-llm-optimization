#!/usr/bin/env python3
"""Regression tests for launch/mapping; these never execute generated candidates."""
import ast, contextlib, ctypes, importlib.util, io, json, os, re, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixed79', HERE/'goal0079_revalidate_all30_v1_1.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FakeBox:
    def __init__(self,*args,**kw): self.cpu=24;self.node=1
    def call(self,argv,inputs,stem,timeout=120,outputs=()):
        stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True)
        files={}
        for name in outputs:
            p=stem.parent/(stem.name+'-'+name);p.write_bytes(b'fake-object');files[name]=p
        raw=b'reference-result' if not outputs else b''
        return {'state':'ok','returncode':0},raw,files

class RegressionTests(unittest.TestCase):
    def test_missing_directory_fixed(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);src=p/'original.c';src.write_text('void kernel_gemm(void){}')
            work=p/'not-yet-created/baselines/gemm/MINI'
            with mock.patch.object(m,'harness_source',return_value='int main(void){return 0;}'):
                result=m.native_case_baselines(FakeBox(),'clang',work,'gemm',src,[])
            self.assertTrue((work/'prototype.h').is_file());self.assertEqual(len(result),2)
    def test_failed_reference_is_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            with mock.patch.object(m,'harness_source',return_value='x'),mock.patch.object(m,'compile_obj',return_value=({'state':'exit_nonzero'},None)):
                with self.assertRaises(m.VError):m.native_case_baselines(FakeBox(),'clang',p/'b','gemm',p/'s',[])
    def test_constants_unchanged(self):
        self.assertEqual(m.CASES['heat-3d'],[{'tsteps':3,'n':9},{'tsteps':4,'n':11}])
        self.assertEqual(len(m.CASES),30);self.assertTrue(all(len(v)==2 for v in m.CASES.values()))
    def test_capability_clear_before_exec(self):
        self.assertLess(m.DROP.index("capset(empty)"),m.DROP.index('os.execv('))
        self.assertIn('PR_SET_NO_NEW_PRIVS',m.DROP);self.assertIn('PR_CAP_AMBIENT_CLEAR_ALL',m.DROP)
        compile(m.DROP,'trusted drop','exec')
    def test_preflight_required_before_extract(self):
        code=(HERE/'goal0079_revalidate_all30_v1_1.py').read_text()
        part=code[code.index('def run_all'):code.index('def self_test')]
        self.assertLess(part.index('sandbox_preflight('),part.index('safe_extract_selected('))
        self.assertLess(part.index('native_case_baselines('),part.index('candidate_revalidate('))
    def test_no_skip_policy_changes(self):
        for form,txt in [('C','void kernel_gemm(void){system("true");}'),('IR','define void @kernel_gemm() { call void @system() ret void }')]:
            with self.assertRaises(m.CandidateFailure):m.policy(txt,form,'kernel_gemm')
    def test_helpers_raise_validator_error(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);c=p/'c.c';c.write_text('void kernel_gemm(void){}');ll=p/'i.ll';ll.write_text('')
            row={'condition':'P1','id':'gemm__MINI__C__P1__s0','task':'gemm','size':'MINI','form':'C','source':str(c),'old_native_object':None,'source_sha256':m.sha_file(c)}
            with mock.patch.object(m,'compile_obj',side_effect=m.VError('infrastructure')):
                with self.assertRaises(m.VError):m.candidate_revalidate(FakeBox(),'clang',row,c,ll,[],{0:{'prototype':p/'p.h'}},p/'output')
            r=json.loads((p/'output/result.json').read_text());self.assertEqual(r['status'],'validator_error')
    def test_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            args=type('Args',(),{'evidence':str(Path(td)/'archive'),'out':td,'cpu':24,'node':1})()
            with mock.patch.object(m,'sha_file',return_value=m.EXPECTED_EVIDENCE_SHA),mock.patch.object(m,'clang18',return_value=('clang','stub')):
                with self.assertRaises(FileExistsError):m.run_all(args)
    def test_run_error_writes_failure_not_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'out';args=type('Args',(),{'evidence':str(Path(td)/'archive'),'out':str(root),'cpu':24,'node':1})()
            with mock.patch.object(m,'sha_file',return_value=m.EXPECTED_EVIDENCE_SHA),mock.patch.object(m,'clang18',return_value=('clang','stub')),mock.patch.object(m,'Sandbox',FakeBox),mock.patch.object(m,'sandbox_preflight',side_effect=m.VError('preflight-refused')):
                with self.assertRaises(m.VError),contextlib.redirect_stderr(io.StringIO()):m.run_all(args)
            self.assertFalse((root/'summary.json').exists())
            self.assertEqual(json.loads((root/'failure.json').read_text())['completion'],'ALL30_REVALIDATION_BLOCKED')
    def test_runtime_source_not_mutated(self):
        code=(HERE/'goal0079_revalidate_all30_v1_1.py').read_text()
        self.assertIn("key=(row['task'],row['size'])",code)
        self.assertIn("out/'baselines'/task/size",code)
        self.assertIn("/run/lock/cpucond-revalidation079.lock",code)
    def test_full_525_mock_orchestration_90_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'out';args=type('Args',(),{'evidence':str(Path(td)/'archive'),'out':str(root),'cpu':24,'node':1})()
            rows=[]
            combos=[(t,s,f) for t in sorted(m.CASES) for s in m.SIZES for f in ('C','IR')]
            for cond, count in [('P0',166),('P1',180),('P2',179)]:
                for t,s,f in combos[:count]:rows.append({'task':t,'size':s,'form':f,'condition':cond,'id':f'{t}__{s}__{f}__{cond}__s0'})
            def extract(archive,out):
                for t in m.CASES:
                    for s in m.SIZES:
                        d=out/'originals'/t/s;d.mkdir(parents=True)
                        (d/'kernel.c').write_text(f'void kernel_{t.replace("-","_")}(void) {{ /*{s}*/ }}')
                        (d/'kernel.ll').write_text(s)
                return rows
            calls=[]
            def baseline(box,clang,work,task,oc,params):
                calls.append((task,oc.parent.name));return {0:{'source_size':oc.parent.name},1:{'source_size':oc.parent.name}}
            def candidate(box,clang,row,oc,oi,params,base,out):
                self.assertEqual(oc.parent.name,row['size']);self.assertEqual(oi.read_text(),row['size'])
                self.assertEqual(base[0]['source_size'],row['size'])
                return dict(row,passed=True,status='checked')
            with mock.patch.object(m,'sha_file',return_value=m.EXPECTED_EVIDENCE_SHA),mock.patch.object(m,'clang18',return_value=('clang','stub')),mock.patch.object(m,'Sandbox',FakeBox),mock.patch.object(m,'sandbox_preflight'),mock.patch.object(m,'safe_extract_selected',side_effect=extract),mock.patch.object(m,'parse_kernel',return_value=('kernel',[])),mock.patch.object(m,'native_case_baselines',side_effect=baseline),mock.patch.object(m,'candidate_revalidate',side_effect=candidate),contextlib.redirect_stdout(io.StringIO()):m.run_all(args)
            self.assertEqual(len(set(calls)),90)
            x=json.loads((root/'summary.json').read_text());self.assertEqual(x['saved_candidates'],525)
            self.assertEqual(x['reference_test_cases'],180);self.assertEqual(x['validator_errors'],0)
    def test_real_inheritable_drop_child_only(self):
        if os.geteuid()!=0:self.skipTest('requires root; production preflight also checks this')
        # Configure a child with CAP_SETUID/CAP_SETGID in every set, then exec
        # the trusted DROP string. The parent process privileges are untouched.
        helper=r'''
import ctypes,os,sys
class H(ctypes.Structure): _fields_=[('v',ctypes.c_uint32),('p',ctypes.c_int)]
class D(ctypes.Structure): _fields_=[('e',ctypes.c_uint32),('p',ctypes.c_uint32),('i',ctypes.c_uint32)]
l=ctypes.CDLL(None,use_errno=True)
h=H(0x20080522,0);d=(D*2)();d[0]=D(192,192,192)
if l.capset(ctypes.byref(h),d): raise OSError(ctypes.get_errno(),'capset')
for cap in (6,7):
 if l.prctl(47,2,cap,0,0): raise OSError(ctypes.get_errno(),'ambient')
exec(compile(sys.argv[1],'<DROP>','exec'))
'''
        probe='import os,json;print(json.dumps({"uid":os.getresuid(),"gid":os.getresgid(),"status":open("/proc/self/status").read()}))'
        # exec(DROP) expects argv[1:] to be command; inject helper argv shift.
        helper=helper.replace("exec(compile(sys.argv[1],'<DROP>','exec'))", "drop=sys.argv[1];sys.argv=sys.argv[1:];exec(compile(drop,'<DROP>','exec'))")
        proc=subprocess.run([sys.executable,'-I','-S','-c',helper,m.DROP,'/usr/bin/python3','-I','-S','-c',probe],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
        self.assertEqual(proc.returncode,0,proc.stderr.decode());v=json.loads(proc.stdout)
        self.assertEqual(v['uid'],[65534]*3);self.assertEqual(v['gid'],[65534]*3)
        for key in ('CapEff','CapPrm','CapInh','CapAmb'):
            self.assertEqual(int(re.search('^'+key+r':\s*(\w+)',v['status'],re.M).group(1),16),0)

if __name__=='__main__':unittest.main(verbosity=2)
