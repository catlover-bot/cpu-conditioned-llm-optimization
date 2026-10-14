#!/usr/bin/env python3
"""Trusted tests only. No model calls. bwrap/systemd are not simulated as real security validation."""
import ast
import contextlib
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

KIT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('upgrade70',KIT/'goal0070_upgrade.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
b=u.import_runner(KIT/'goal0069_batch_codegen.py')
BASE=KIT/'legacy-test-only'

class Tests(unittest.TestCase):
    def test_prompt_all_instruction_languages_english(self):
        for name in b.vendor('stress_support.py').TASKS:
            domain=b.vendor('stress_support.py').contract(name)['domain']
            for form in ('C','IR'):
                text=b.prompt('/* SOURCE */',form,name,'MINI',domain)
                self.assertTrue(text.isascii())
                self.assertIn('This is condition P0.',text)
    def test_source_is_preserved_even_unicode_comment(self):
        source='// 参照コード\nvoid kernel_t(){}\n'
        text=b.prompt(source,'C','t','MINI')
        self.assertIn(source.rstrip()+'\n----- END ORIGINAL CODE -----',text)
        self.assertTrue(text.partition('----- BEGIN ORIGINAL CODE -----')[0].isascii())
    def test_no_cpu_or_ranking_context(self):
        text=b.prompt('void kernel_t(){}','C','t','SMALL')
        for token in ('Haswell','EPYC','Zen 2','oracle_speedup','candidate_id'):
            self.assertNotIn(token,text)
    def test_seed_limits_identical(self):
        payload,_=b.request_for('void kernel_t(){}','C','t','MINI')
        self.assertEqual(payload['options']['seed'],69001)
        self.assertEqual(payload['options']['num_thread'],16)
        self.assertEqual(payload['options']['num_ctx'],32768)
        self.assertEqual(payload['options']['num_predict'],4096)
        self.assertEqual(payload['model'],'qwen2.5-coder:32b-instruct-q4_K_M')
    def test_japanese_domain_rejected(self):
        with self.assertRaises(b.Blocked):b.prompt('x','C','t','MINI','日本語')
    def test_drop_script_exact(self):self.assertEqual(b.SANDBOX_DROP,(KIT/'sandbox_drop.py').read_text())
    def test_probe_script_exact(self):self.assertEqual(b.SANDBOX_PROBE,(KIT/'sandbox_probe.py').read_text())
    def test_capability_clear_kept(self):
        self.assertIn('libc.capset',b.SANDBOX_DROP)
        self.assertIn('PR_CAP_AMBIENT_CLEAR_ALL',b.SANDBOX_DROP)
        self.assertIn('no_new_privs',b.SANDBOX_DROP)
    def test_no_validation_bypass(self):
        import inspect
        source=inspect.getsource(b.Sandbox.preflight)
        self.assertIn('raise Blocked',source)
        self.assertIn("v is True",source)
        self.assertIn('sandbox-compile-probe',source)
    def test_namespace_flags_remain(self):
        box=object.__new__(b.Sandbox)
        argv=box.argv(['/usr/bin/true'],{},None)
        for flag in ('--unshare-pid','--unshare-net','--unshare-ipc','--unshare-uts','--cap-drop'):
            self.assertIn(flag,argv)
        self.assertNotIn('--share-net',argv)
        self.assertEqual(argv[argv.index('--cap-drop')+1],'ALL')
        caps=[argv[i+1] for i,v in enumerate(argv) if v=='--cap-add']
        self.assertEqual(caps,['CAP_SETUID','CAP_SETGID'])
    def test_tmpfs_private_permission_not_host_permission(self):
        box=object.__new__(b.Sandbox)
        argv=box.argv(['/usr/bin/true'],{},None)
        ix=argv.index('--tmpfs')
        self.assertEqual(argv[ix-2:ix+2],['--perms','1777','--tmpfs','/tmp'])
        self.assertNotIn('--bind',argv)
    def test_parent_attempts_not_discarded(self):
        # Scope validator is exercised separately with a real synthetic 180-request parent.
        src=(KIT/'goal0070_upgrade.py').read_text()
        self.assertIn('attempt/output evidence exists',src)
        self.assertIn("'requests_pending':180",src)
    def test_missing_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(u.Refuse):u.safe(Path(tmp),'missing')
    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(u.Refuse):u.safe(Path(tmp),'../outside')
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'a').write_text('x');(root/'b').symlink_to(root/'a')
            with self.assertRaises(u.Refuse):u.safe(root,'b')
    def test_json_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(u.Refuse):u.load(p)
    def test_json_nan_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a';p.write_text('{"x":NaN}')
            with self.assertRaises(u.Refuse):u.load(p)
    def test_write_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'a';u.write(p,'x')
            with self.assertRaises(FileExistsError):u.write(p,'y')
    def capability_child(self,launcher):
        # Recreate bwrap 0.9 requested CapInh=SETUID|SETGID in a *child*.
        # This tests privilege dropping, NOT namespace isolation.
        prefix='''import ctypes,os,sys
lib=ctypes.CDLL(None,use_errno=True)
class H(ctypes.Structure):_fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
class D(ctypes.Structure):_fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
h=H(0x20080522,0);ds=(D*2)();ds[0].effective=192;ds[0].permitted=192;ds[0].inheritable=192
if lib.capset(ctypes.byref(h),ds)!=0:raise OSError(ctypes.get_errno(),'test capability setup')
'''
        target='import os,json; print(json.dumps({"uid":os.getuid(),"caps":[x for x in open("/proc/self/status").read().splitlines() if x.startswith(("Cap","NoNewPrivs"))]}))'
        prefix+='os.execv(sys.executable,[sys.executable,"-I","-S","-c",'+repr(launcher)+',"/usr/bin/python3","-I","-S","-c",'+repr(target)+'])\n'
        return subprocess.run([sys.executable,'-I','-S','-c',prefix],capture_output=True,text=True,timeout=15)
    @unittest.skipUnless(os.geteuid()==0 and Path('/proc/self/status').exists(),'requires child privilege-drop permission')
    def test_legacy_assertion_reproduced_inherited_caps(self):
        legacy=('import os,sys,ctypes;os.setgroups([]);os.setgid(65534);os.setuid(65534);'
          'libc=ctypes.CDLL(None);assert libc.prctl(38,1,0,0,0)==0;'
          'assert os.getuid()==65534;st=open("/proc/self/status").read();assert all(int(st.split(k+":")[1].split()[0],16)==0 for k in ("CapEff","CapPrm","CapInh","CapAmb"));'
          'os.execv(sys.argv[1],sys.argv[1:])')
        result=self.capability_child(legacy)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertIn('AssertionError',result.stderr)
    @unittest.skipUnless(os.geteuid()==0 and Path('/proc/self/status').exists(),'requires child privilege-drop permission')
    def test_new_launcher_clears_inherited_caps(self):
        result=self.capability_child(b.SANDBOX_DROP)
        self.assertEqual(result.returncode,0,result.stderr)
        obj=json.loads(result.stdout)
        self.assertEqual(obj['uid'],65534)
        caps=dict(line.split(':',1) for line in obj['caps'])
        for key in ('CapEff','CapPrm','CapInh','CapAmb'):
            self.assertEqual(int(caps[key].strip(),16),0)
        self.assertEqual(caps['NoNewPrivs'].strip(),'1')
    def test_runner_compute_functions_unchanged(self):
        if not (BASE/'goal0069_batch_codegen.py').exists():self.skipTest('legacy comparison fixture omitted')
        old=ast.parse((BASE/'goal0069_batch_codegen.py').read_text())
        new=ast.parse((KIT/'goal0069_batch_codegen.py').read_text())
        def funcs(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
        of,nf=funcs(old),funcs(new)
        for name in ('extract_response','object_build','link','execute_program','prepare_baseline',
                     'validate_candidate','stress_gate','measurement','timing','qsummary','policy','generation_phase'):
            self.assertEqual(of[name],nf[name],name)
    def test_full_180_request_migration(self):
        if not (BASE/'goal0069_batch_codegen.py').exists():self.skipTest('legacy comparison fixture omitted')
        with tempfile.TemporaryDirectory() as tmp:
            parent=Path(tmp)/'parent';work=parent/'work';work.mkdir(parents=True)
            for name in ('goal0069_batch_codegen.py','server_launch.sh',*b.VENDORS):
                src=(BASE if (BASE/name).exists() else KIT)/name
                shutil.copyfile(src,work/name)
            old=u.import_runner(work/'goal0069_batch_codegen.py')
            items=[];instances=[]
            for size in b.SIZES:
                for k in range(30):
                    task='k'+str(k);sources={}
                    for form,ext in [('C','c'),('IR','ll')]:
                        rel=f'inputs/{task}/{size}/kernel.{ext}'
                        source='void kernel_'+task+'(){}' if form=='C' else 'define void @kernel_'+task+'() { ret void }'
                        u.write(work/rel,source);sources[form]={'path':rel,'sha256':u.sha(work/rel)}
                        req,upper=old.request_for(source,form,task,size)
                        rid=old.make_task_id(task,size,form);rp='requests/'+rid+'.json';u.jw(work/rp,req)
                        items.append({'id':rid,'task':task,'size':size,'form':form,'condition':'P0','sample':0,'seed':b.SEED,
                                      'source':rel,'request':rp,'request_sha256':u.sha(work/rp),
                                      'input_byte_upper':upper,'context_budget_ok':True})
                    instances.append({'task':task,'size':size,'sources':sources})
            plan={'revision':u.OLD_REV,'requests':180,'instances':90,'kernels':30,
                  'tasks':items,'instances_list':instances,'conditions':['P0'],'representations':['C','IR'],'samples':1}
            u.jw(work/'plan.json',plan);b.seal(work)
            summary={'completion':'DATASET_BATCH_BLOCKED','planned_requests':180,'requests_pending':180,
                      'generated_texts':0,'generation_terminal':0,'validation_terminal':0,'measurement_terminal':0}
            u.jw(parent/'results/summary.json',summary)
            before=u.inventory(parent)
            with contextlib.redirect_stdout(io.StringIO()):
                target=u.migrate(parent,Path(tmp)/'new',KIT,expected_plan_sha=None)
            self.assertEqual(before,u.inventory(parent))
            self.assertFalse((target/'results').exists())
            np=u.load(target/'work/plan.json')
            self.assertEqual(len(np['tasks']),180)
            self.assertEqual(np['conditions'],['P0']);self.assertEqual(np['prompt_language'],'en')
            u.verify_list(target/'work')
            self.assertEqual(np['instances_list'],plan['instances_list'])
            for a,c in zip(plan['tasks'],np['tasks']):
                self.assertEqual(a['id'],c['id']);self.assertNotEqual(a['request_sha256'],c['request_sha256'])
            # Refuse migration after any attempt exists, even if the summary is stale.
            u.write(parent/'results/generation/t/started.json','{}')
            with self.assertRaises(u.Refuse):u.validate_parent(parent,None)
            with self.assertRaises(u.Refuse):u.migrate(parent,target,KIT,None)

if __name__=='__main__':unittest.main(verbosity=2)
