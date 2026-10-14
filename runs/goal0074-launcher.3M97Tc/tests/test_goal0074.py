import ast
import builtins
from contextlib import ExitStack, redirect_stdout
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT=Path(__file__).resolve().parents[1]
KIT=ROOT
BASE=ROOT/'test_reference'
sys.path.insert(0,str(KIT))
import goal0074_finish_all as c

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

class StaticTests(unittest.TestCase):
    def test_origin_hashes(self):
        for n,h in c.ORIGIN.items():
            if n!='plan.json':self.assertEqual(hashlib.sha256((BASE/n).read_bytes()).hexdigest(),h)
    def test_no_total_deadlines(self):
        source=(KIT/'until_complete_pipeline.py').read_text()
        self.assertIn('gen_end=math.inf',source)
        self.assertIn("Sandbox(run/'sandbox-records'/uuid.uuid4().hex[:8],None)",source)
        self.assertNotIn('time.monotonic()+300',source)
        self.assertNotIn('time.monotonic()+180',source)
        self.assertNotIn('start+max_hours',source)
    def test_no_finite_configuration(self):
        source=(KIT/'goal0074_finish_all.py').read_text()
        self.assertIn('--property=RuntimeMaxSec=infinity',source)
        self.assertIn('--property=MemoryMax=96G',source)
        self.assertIn('--property=TasksMax=256',source)
        self.assertIn('--property=KillMode=control-group',source)
        self.assertNotIn("['systemctl','stop'",source)
    def test_per_request_and_stream_preserved(self):
        rt=(BASE/'runtime_support.py').read_text()
        self.assertIn("return 1800 if item['form'] == 'C' else 7200",rt)
        self.assertIn('consecutive_transport_failures >= 2',rt)
        self.assertIn('if not response.exists():',rt)
        self.assertIn("(d/'result.json').is_file()",rt)
        st=(BASE/'streaming_support.py').read_text()
        self.assertIn('idle_seconds=1800',st)
    def test_replaced_only_orchestration(self):
        ns=ast.parse((KIT/'until_complete_pipeline.py').read_text())
        self.assertEqual(len(ns.body),1)
        self.assertEqual(ns.body[0].name,'run_pipeline_until_complete')
    def test_import_frozen_not_exec_candidate(self):
        self.assertNotIn('candidate.ll',(KIT/'goal0074_finish_all.py').read_text())
        self.assertNotIn('candidate.c',(KIT/'goal0074_finish_all.py').read_text())
    def test_same_unit_guard(self):
        import re
        self.assertIsNotNone(re.fullmatch(r'cpucond69-[A-Za-z0-9-]+\.service','cpucond69-completion74-20260913T010203-aaaaaa.service'))
    def test_cap_guard_untouched(self):
        b=(BASE/'goal0069_batch_codegen.py').read_text()
        self.assertIn("'メモリ上限が96GiBを超えています'",b)
        self.assertIn("'プロセス・スレッド数上限が256を超えています'",b)
    def test_completion_counts(self):
        x={'planned_requests':3,'generation_terminal':3,'validation_terminal':3,'measurement_pending':0,'completion':'DATASET_BATCH_COMPLETE'}
        self.assertTrue(c.completed(x))
        for k,v in [('generation_terminal',2),('validation_terminal',2),('measurement_pending',1),('completion','DATASET_BATCH_PAUSED')]:
            with self.subTest(k=k):self.assertFalse(c.completed(dict(x,**{k:v})))
    def test_completion_bool_rejected(self):
        self.assertFalse(c.completed({'planned_requests':True}))
    def test_json_duplicate(self):
        with self.assertRaises(c.Refuse):c.decode('{"a":1,"a":2}')
    def test_json_nan(self):
        with self.assertRaises(c.Refuse):c.decode('{"a":NaN}')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_text('x');(p/'b').symlink_to(p/'a')
            with self.assertRaises(c.Refuse):c.read(p/'b')
    def test_busy_transition_no_stop(self):
        with tempfile.TemporaryDirectory() as td:
            job=Path(td);(job/c.CONTROL).mkdir();(job/'active-unit.txt').write_text('cpucond69-existing.service')
            q=Mock(side_effect=['active','deactivating','inactive']);sleep=Mock()
            with patch.object(c,'watched_jobs',return_value=[job]),redirect_stdout(io.StringIO()):
                c.wait_for_idle(job,{},'cpucond69-new.service',query=q,sleep=sleep)
            self.assertEqual(sleep.call_args_list, [((60,),),((60,),)])
            self.assertEqual((job/'active-unit.txt').read_text(),'cpucond69-existing.service')
    def test_busy_self_not_waited(self):
        with tempfile.TemporaryDirectory() as td:
            job=Path(td);(job/c.CONTROL).mkdir();(job/'active-unit.txt').write_text('cpucond69-self.service')
            q=Mock();sleep=Mock()
            with patch.object(c,'watched_jobs',return_value=[job]):c.wait_for_idle(job,{},'cpucond69-self.service',query=q,sleep=sleep)
            q.assert_not_called();sleep.assert_not_called()
    def test_failed_environment_not_blindly_restart(self):
        with tempfile.TemporaryDirectory() as td:
            job=Path(td);(job/'results').mkdir();(job/'results/summary.json').write_text(json.dumps({'current_session':{'plan_sha256':c.PLAN_SHA,'errors':['e']},'completion':'DATASET_BATCH_BLOCKED'}))
            with self.assertRaises(c.Refuse):c.previous_safe(job)
    def test_past_normal_pause_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            job=Path(td);(job/'results').mkdir();(job/'results/summary.json').write_text(json.dumps({'current_session':{'plan_sha256':c.PLAN_SHA,'errors':[]},'completion':'DATASET_BATCH_PAUSED'}))
            c.previous_safe(job)
    def test_active_controller_not_relaunched(self):
        with tempfile.TemporaryDirectory() as td:
            job=Path(td);(job/c.CONTROL).mkdir();(job/c.CONTROL/'active-unit.txt').write_text('cpucond69-self.service')
            native_open=builtins.open
            def redir(p,*a,**kw):return native_open(job/'test.lock' if str(p).startswith('/var/lock/') else p,*a,**kw)
            with patch.object(c,'verify_kit'),patch.object(c,'unit_state',return_value='active'),patch.object(c,'command') as cmd,patch('builtins.open',redir),redirect_stdout(io.StringIO()):
                c.launch(job)
                cmd.assert_not_called()

class FlowTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);self.pkg=self.root/'work';self.pkg.mkdir()
        self.run=self.root/'results';self.run.mkdir()
        self.b=module('test_b_'+self.root.name,BASE/'goal0069_batch_codegen.py')
        self.b.__dict__['__name__']=self.b.__name__
        exec(compile((KIT/'until_complete_pipeline.py').read_text(),'until_complete_pipeline.py','exec'),self.b.__dict__)
        self.plan={'revision':self.b.REV,'requests':3,'tasks':[{'id':f'k{i}__MINI__C__P0__s0','task':f'k{i}','size':'MINI','form':'C'} for i in range(3)],'instances_list':[{'task':f'k{i}','size':'MINI'} for i in range(3)]}
        raw=self.b.enc(self.plan);(self.pkg/'plan.json').write_bytes(raw);(self.pkg/'SHA256SUMS').write_text(self.b.shab(raw)+'  plan.json\n')
        self.effects=[];self.fail=[];self.skip=[];self.active=False
        owner=self
        class FakeBox:
            def __init__(s,root,deadline=None):
                owner.assertIsNone(deadline);owner.effects.append('sandbox')
            def preflight(s):owner.effects.append('preflight')
            def close(s):pass
        def gen(pkg,plan,run,deadline,freeze,binary):
            owner.assertTrue(math.isinf(deadline));owner.active=True;owner.effects.append('gen-start')
            for t in plan['tasks']:
                d=run/'generation'/t['id'];p=d/'result.json'
                if p.exists() or t['id'] in owner.skip:continue
                owner.b.jw(p,{'status':'generation_transport_failure' if t['id'] in owner.fail else 'saved','utc':owner.b.now()});owner.effects.append(t['id'])
            owner.active=False;owner.effects.append('gen-stop')
        def check_busy():owner.assertFalse(owner.active)
        def validate(box,clang,pkg,plan,run,t,inst,base):
            owner.assertFalse(owner.active);owner.effects.append('validate')
            x={'official_all_passed':True,'multiinput_status':'not_implemented_for_task','measurement_eligible_provisional':True};owner.b.jw(run/'validation'/t['id']/'result.json',x);return x
        def measure(box,clang,run,inst,t,base,v):
            owner.assertFalse(owner.active);owner.effects.append('measure')
            x={'measurement_valid':True,'speedup':0.9};owner.b.jw(run/'measurement'/t['id']/'result.json',x);return x
        native_open=builtins.open
        def redir(p,*a,**kw):return native_open(owner.root/'batch.lock' if str(p)=='/var/lock/cpucond-batch-codegen.lock' else p,*a,**kw)
        self.stack=ExitStack()
        for name,value in {'host_guard':lambda:None,'clang_path':lambda:('/usr/bin/python3','test'), 'Sandbox':FakeBox,
                           'model_state':lambda:(None,None,{'digest':'test'},{}),'generation_phase':gen,
                           'check_busy':check_busy,'prepare_baseline':lambda *a:{},'validate_candidate':validate,
                           'measurement':measure,'open':redir}.items():
            self.stack.enter_context(patch.object(self.b,name,value,create=True))
        self.stack.enter_context(patch.object(self.b.signal,'signal'))
    def tearDown(self):self.stack.close();self.t.cleanup()
    def runit(self):
        with redirect_stdout(io.StringIO()):rc=self.b.run_pipeline_until_complete(self.pkg)
        return rc,json.loads((self.run/'summary.json').read_text())
    def test_all_done_no_hour_checks(self):
        rc,x=self.runit();self.assertEqual(rc,0);self.assertTrue(c.completed(x));self.assertEqual(x['current_session']['max_hours'],None)
        self.assertEqual(x['current_session']['phase'],'completed');self.assertFalse(x['all_30_multinput_validation_complete'])
    def test_generation_before_measurement(self):
        self.runit();self.assertLess(self.effects.index('gen-stop'),self.effects.index('measure'))
    def test_saved_attempt_not_regenerated(self):
        tid=self.plan['tasks'][0]['id'];p=self.run/'generation'/tid/'result.json';self.b.jw(p,{'status':'saved','utc':'old'})
        raw=p.read_bytes();self.runit();self.assertNotIn(tid,self.effects);self.assertEqual(p.read_bytes(),raw)
    def test_failed_attempt_counted_and_skipped(self):
        self.fail=[self.plan['tasks'][0]['id']];rc,x=self.runit();self.assertEqual(rc,0);self.assertEqual(x['generation_non_success'],1);self.assertEqual(x['validation_terminal'],3);self.assertEqual(x['measurement_terminal'],2)
    def test_guard_stop_not_infinite_loop(self):
        self.fail=[t['id'] for t in self.plan['tasks'][:2]];self.skip=[self.plan['tasks'][2]['id']]
        rc,x=self.runit();self.assertEqual(rc,1);self.assertEqual(x['completion'],'DATASET_BATCH_BLOCKED');self.assertEqual(x['requests_pending'],1)
    def test_second_run_no_repeat_evaluation(self):
        self.runit();old=len(self.effects);rc,x=self.runit();self.assertTrue(c.completed(x));self.assertEqual(self.effects[old:],['sandbox','preflight'])
    def test_plan_unchanged(self):
        raw=(self.pkg/'plan.json').read_bytes();self.runit();self.assertEqual((self.pkg/'plan.json').read_bytes(),raw)
    def test_pause_receipts_kept(self):
        (self.run/'sessions').mkdir();p=self.run/'sessions/old.json';p.write_text('{"old":true}')
        self.runit();self.assertEqual(p.read_text(),'{"old":true}');self.assertGreater(len(list((self.run/'sessions').glob('*'))),1)
    def test_same_generation_kwargs(self):
        before=self.b.CAPS.copy();self.runit();self.assertEqual(before,{'C':4096,'IR':16384});self.assertEqual(self.b.CAPS,before)

if __name__=='__main__':unittest.main(verbosity=2)
