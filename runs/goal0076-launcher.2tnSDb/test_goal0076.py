#!/usr/bin/env python3
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import goal0076_dual_numa as m


def plan(condition='P1'):
    tasks=[]
    for k in range(30):
        for size in ('MINI','SMALL','MEDIUM'):
            for form in ('C','IR'):
                tasks.append({'task':f'k{k:02d}','size':size,'form':form,
                              'id':f'k{k:02d}__{size}__{form}__{condition}__s0',
                              'condition':condition})
    return {'tasks':tasks,'requests':180,'conditions':[condition]}

def synthetic_topology(root):
    root.mkdir()
    (root/'online').write_text('0-47\n')
    for cpu in list(range(2,18))+list(range(26,42)):
        p=root/f'cpu{cpu}';(p/'topology').mkdir(parents=True)
        node=0 if cpu<24 else 1
        (p/'topology/physical_package_id').write_text(str(node))
        (p/'topology/core_id').write_text(str(cpu%24))
        (p/f'node{node}').mkdir()


class BasicTests(unittest.TestCase):
    def test_duplicate_json(self):
        with self.assertRaises(m.Refuse):m.decode('{"a":1,"a":2}')
    def test_nan(self):
        with self.assertRaises(m.Refuse):m.decode('{"a":NaN}')
    def test_atomic_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r';m.record(p,{'v':1})
            with self.assertRaises(FileExistsError):m.record(p,{'v':2})
            self.assertEqual(m.load(p),{'v':1})
    def test_atomic_update(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r';m.atomic(p,{'a':1});m.atomic(p,{'a':2})
            self.assertEqual(m.load(p),{'a':2})
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r';q=Path(d)/'q';q.write_text('{}');p.symlink_to(q)
            with self.assertRaises(m.Refuse):m.atomic(p,{})
    def test_partial_json_never_published(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r';m.atomic(p,{'v':0});bad=[]
            def writer():
                for i in range(50):m.atomic(p,{'v':i,'payload':'x'*1000})
            t=threading.Thread(target=writer);t.start()
            while t.is_alive():
                try:json.loads(p.read_text())
                except Exception as e:bad.append(str(e))
            t.join();self.assertEqual(bad,[])
    def test_cpulist(self):self.assertEqual(m.cpu_list('2-4,8'),[2,3,4,8])
    def test_invalid_cpulist(self):
        with self.assertRaises(m.Refuse):m.cpu_list('2-1')
    def test_topology(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'cpu';synthetic_topology(root)
            workers=m.topology(root)
            self.assertEqual(workers[0]['cpus'],list(range(2,18)))
            self.assertEqual(workers[1]['cpus'],list(range(26,42)))
    def test_wrong_node(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'cpu';synthetic_topology(root)
            (root/'cpu26/node1').rmdir();(root/'cpu26/node0').mkdir()
            with self.assertRaises(m.Refuse):m.topology(root)
    def test_offline(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'cpu';synthetic_topology(root);(root/'online').write_text('0-40')
            with self.assertRaises(m.Refuse):m.topology(root)
    def test_same_physical_core(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'cpu';synthetic_topology(root);(root/'cpu27/topology/core_id').write_text('2')
            with self.assertRaises(m.Refuse):m.topology(root)
    def test_no_repeat_partition(self):
        p=plan();a=m.assignments(p)
        self.assertEqual(len(a[0]),90);self.assertEqual(len(a[1]),90)
        self.assertFalse(set(a[0])&set(a[1]))
        self.assertEqual(set(a[0])|set(a[1]),{x['id'] for x in p['tasks']})
    def test_same_workers_p1_p2(self):
        a=m.assignments(plan('P1'));b=m.assignments(plan('P2'))
        for i in (0,1):self.assertEqual([x.replace('__P1__','__P2__') for x in a[i]],b[i])
    def test_same_workers_c_ir(self):
        a=m.assignments(plan())
        for v in a.values():
            ids=set(v)
            for tid in v:
                if '__C__' in tid:self.assertIn(tid.replace('__C__','__IR__'),ids)
    def test_duplicate_task(self):
        p=plan();p['tasks'][0]['id']=p['tasks'][1]['id']
        with self.assertRaises(m.Refuse):m.assignments(p)
    def test_bad_task_count(self):
        with self.assertRaises(m.Refuse):m.assignments({'tasks':[]})
    def test_partition_preserves_payloads(self):
        p=plan();original=copy.deepcopy(p)
        subset=m.partition_records(p,m.assignments(p)[0])
        self.assertEqual(p,original);self.assertEqual(subset['requests'],90)
        for t in subset['tasks']:self.assertIn(t,p['tasks'])
    def test_invalid_partition(self):
        with self.assertRaises(m.Refuse):m.partition_records(plan(),['nobody'])
    def test_duplicate_partition(self):
        p=plan();key=p['tasks'][0]['id']
        with self.assertRaises(m.Refuse):m.partition_records(p,[key,key])
    def test_worker_model_options(self):
        b=types.SimpleNamespace(ACCOUNT='cpucond-infer',HOME=m.HOME)
        w={'port':11481,'models':'/some/private/models','cpus':list(range(26,42)),'node':1}
        a=m.worker_service_command(Path('/opt/ollama'),b,w)
        self.assertIn('OLLAMA_NUM_PARALLEL=1',a);self.assertIn('OLLAMA_NO_CLOUD=1',a)
        self.assertIn('OLLAMA_MODELS=/some/private/models',a);self.assertIn('--membind=1',a)
        self.assertIn('OLLAMA_HOST=127.0.0.1:11481',a);self.assertNotIn('pull',a)
    def test_unprivileged_service(self):
        b=types.SimpleNamespace(ACCOUNT='cpucond-infer',HOME=m.HOME)
        w={'port':11480,'models':'/some/models','cpus':[2,3],'node':0}
        a=m.worker_service_command(Path('/opt/ollama'),b,w)
        self.assertEqual(a[:4],['runuser','-u','cpucond-infer','--'])
    def test_worker_unit_lifetime(self):
        a=m.worker_command('cpucond76-w.service','cpucond69-stage.service',Path('/w'),Path('/a'),0,Path('/l'))
        self.assertIn('--property=RuntimeMaxSec=infinity',a)
        self.assertIn('--property=PartOf=cpucond69-stage.service',a)
        self.assertIn('--property=KillMode=control-group',a)
        self.assertIn('--property=MemoryMax=64G',a)
    def test_unknown_inference_blocks(self):
        with self.assertRaises(m.Refuse):m.allow_no_own_inference('a.service',['b.service'],[{'cgroup':'/system.slice/other.service'}])
    def test_peer_allowed(self):m.allow_no_own_inference('a.service',['b.service'],[{'cgroup':'/system.slice/b.service'}])
    def test_own_survivor_blocks(self):
        with self.assertRaises(m.Refuse):m.allow_no_own_inference('a.service',['b.service'],[{'cgroup':'/system.slice/a.service'}])
    def test_substring_unit_not_allowed(self):
        with self.assertRaises(m.Refuse):m.allow_no_own_inference('a.service',['b.service'],[{'cgroup':'/system.slice/xb.service'}])
    def test_no_inference_allowed(self):m.allow_no_own_inference('a.service',['b.service'],[])
    def test_pid_suspend_resume_real(self):
        if not hasattr(os,'pidfd_open'):self.skipTest('Linux pidfd not available')
        p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(15)'])
        fd=os.pidfd_open(p.pid)
        try:
            signal=__import__('signal');signal.pidfd_send_signal(fd,signal.SIGSTOP)
            m.wait_stopped(p.pid);signal.pidfd_send_signal(fd,signal.SIGCONT)
        finally:os.close(fd);p.terminate();p.wait()
    def test_unstarted_condition_blocks_if_records(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'ROOT',Path(d)):
            g=Path(d)/'P1/results/generation/id';g.mkdir(parents=True);(g/'started.json').write_text('{}')
            with self.assertRaises(m.Refuse):m.stage_unstarted(None)
    def test_no_record_condition_allowed(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'ROOT',Path(d)):
            for con in ('P1','P2'):(Path(d)/con).mkdir()
            m.stage_unstarted(None)
    def test_live_stage_blocks(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'ROOT',Path(d)):
            p=Path(d)/'P1';p.mkdir();(p/'active-unit.txt').write_text('cpucond69-sequence75-P1-abc.service')
            with patch.object(m,'unit_props',return_value={'ActiveState':'active'}):
                with self.assertRaises(m.Refuse):m.stage_unstarted(None)
    def test_p0_has_no_adapted_generation(self):
        import inspect
        self.assertIn("condition in ('P1','P2')",inspect.getsource(m.dual_generation))
        self.assertNotIn('SIGTERM',inspect.getsource(m.enable))
    def test_exclusively_atomic_payload_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'request.json';obj={'model':'x','prompt':'exact\ncode','options':{'seed':69001}}
            m.record(p,obj);self.assertEqual(p.read_bytes(),m.enc(obj))
    def test_no_total_time_cap_generation(self):
        import inspect
        self.assertIn('math.inf',inspect.getsource(m.gen_worker))
        self.assertIn('not stopped.exists()',inspect.getsource(m.gen_worker))
    def test_two_daemons_stop_before_eval(self):
        import inspect
        text=inspect.getsource(m.dual_generation)
        self.assertLess(text.index('all(s not in LIVE'),text.index('DUAL_NUMA_INFERENCE_STOPPED'))
        self.assertIn("need(not inference_processes()",text)
    def test_private_copy_not_hardlink(self):
        import inspect
        text=inspect.getsource(m.ensure_second_store)
        self.assertIn('--reflink=never',text);self.assertIn('st_ino',text)
    def test_original_validation_not_changed(self):
        tree=ast.parse(Path(m.__file__).read_text());names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertNotIn('validate_candidate',names);self.assertNotIn('measurement',names);self.assertNotIn('Sandbox',names)
    def test_original_p0_records_preserved(self):
        import inspect
        self.assertNotIn('P0 /',inspect.getsource(m.atomic))
        self.assertIn("'p0_execution_unchanged':True",inspect.getsource(m.enable))
    def test_only_waiting_manager_can_be_stopped(self):
        import inspect
        text=inspect.getsource(m.enable)
        self.assertIn("get('phase')=='WAITING_FOR_P0'",text)
        self.assertIn('members=={pid}',text)
        self.assertIn('need(not dependents',text)
        self.assertIn('signal.SIGCONT',text)
    def test_signal_targets_verified_pidfd_not_process_name(self):
        import inspect
        text=inspect.getsource(m.enable)
        self.assertIn('os.pidfd_open(pid)',text);self.assertNotIn('pkill',text)
    def test_assignment_model_prompt_unchanged(self):
        import inspect
        text=inspect.getsource(m.gen_worker)
        self.assertIn("b.sha(request)==item['request_sha256']",text)
        self.assertNotIn("payload['prompt']=",text)
    def test_partial_failure_stops_peer_at_boundary(self):
        import inspect
        self.assertIn('stop-new-requests.json',inspect.getsource(m.dual_generation))
        self.assertIn('not stopped.exists()',inspect.getsource(m.gen_worker))
    def test_generation_metadata_has_mode_change(self):
        import inspect
        text=inspect.getsource(m.stage_worker)
        self.assertIn("v['p0_runtime_differs']=True",text)
    def test_generators_do_not_download(self):
        import inspect
        text=inspect.getsource(m)
        self.assertNotIn('https://',text);self.assertNotIn('ollama pull',text)


class DualFlowTests(unittest.TestCase):
    def test_coordinator_runs_two_partitions_and_joins(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pkg=root/'work';pkg.mkdir();(pkg/'plan.json').write_text('{}');run=root/'results';run.mkdir()
            cfg={'workers':[{'cpus':[2],'node':0},{'cpus':[26],'node':1}],
                 'assignments':{'P1':{'0':['a'],'1':['b']}}}
            calls=[];written=[]
            b=types.SimpleNamespace(check_busy=lambda:None,atomic=lambda p,x:written.append((p,x)),results_summary=lambda p,r:{'requests_pending':0})
            def command(argv,**kw):
                calls.append(argv)
                ap=Path(argv[argv.index('--assignment')+1]);i=int(argv[argv.index('--worker-index')+1])
                m.record(ap.parent/f'worker-{i}-result.json',{'complete':True})
                return types.SimpleNamespace()
            with patch.object(m,'load_chain',return_value=object()),patch.object(m,'validate_config',return_value=cfg), \
                 patch.object(m,'ensure_second_store',return_value={}),patch.object(m,'inference_processes',return_value=[]), \
                 patch.object(m,'cmd',side_effect=command),patch.object(m,'unit_props',return_value={'ActiveState':'inactive'}), \
                 patch.dict(os.environ,{'CPUCOND_BATCH_UNIT':'cpucond69-stage.service'}):
                m.dual_generation(b,pkg,plan(),run,float('inf'),{},Path('/bin/fake'))
            self.assertEqual(len(calls),2)
            self.assertEqual({a[a.index('--worker-index')+1] for a in calls},{'0','1'})
            self.assertTrue(written)
    def test_coordinator_incomplete_worker_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pkg=root/'work';pkg.mkdir();(pkg/'plan.json').write_text('{}');run=root/'results';run.mkdir()
            cfg={'workers':[{'cpus':[2],'node':0},{'cpus':[26],'node':1}],
                 'assignments':{'P1':{'0':['a'],'1':['b']}}}
            b=types.SimpleNamespace(check_busy=lambda:None,atomic=lambda *a:None,results_summary=lambda *a:{'requests_pending':1})
            def command(argv,**kw):
                ap=Path(argv[argv.index('--assignment')+1]);i=int(argv[argv.index('--worker-index')+1])
                m.record(ap.parent/f'worker-{i}-result.json',{'complete':i==0})
            with patch.object(m,'load_chain',return_value=object()),patch.object(m,'validate_config',return_value=cfg), \
                 patch.object(m,'ensure_second_store',return_value={}),patch.object(m,'inference_processes',return_value=[]), \
                 patch.object(m,'cmd',side_effect=command),patch.object(m,'unit_props',return_value={'ActiveState':'inactive'}), \
                 patch.dict(os.environ,{'CPUCOND_BATCH_UNIT':'cpucond69-stage.service'}):
                with self.assertRaises(m.Refuse):m.dual_generation(b,pkg,plan(),run,float('inf'),{},Path('/bin/fake'))
            self.assertEqual(len(list(run.glob('dual76/*/stop-new-requests.json'))),1)
    def test_no_model_copy_when_foreign_inference(self):
        with patch.object(m,'load_chain',return_value=object()),patch.object(m,'validate_config',return_value={}), \
             patch.object(m,'inference_processes',return_value=[{'pid':1}]),patch.object(m,'ensure_second_store') as copy_store:
            b=types.SimpleNamespace(check_busy=lambda:None)
            with self.assertRaises(m.Refuse):m.dual_generation(b,Path('/w'),plan(),Path('/r'),float('inf'),{},Path('/b'))
            copy_store.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
