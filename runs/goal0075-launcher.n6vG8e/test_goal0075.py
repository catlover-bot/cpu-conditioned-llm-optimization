#!/usr/bin/env python3
"""Synthetic tests only: no model/API/server commands or cloud credentials."""
from pathlib import Path
from contextlib import ExitStack,redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch,Mock
import copy,io,json,re,sys,tempfile,unittest,hashlib,ast,builtins
sys.path.insert(0,str(Path(__file__).resolve().parent))
import goal0075_p012_chain as c

class FakeTokenizer:
    def encode(self,s,add_special_tokens=False):
        assert add_special_tokens is False
        return SimpleNamespace(ids=list(s.encode('utf-8')))
    def decode(self,ids,skip_special_tokens=False):
        assert skip_special_tokens is False
        return bytes(ids).decode('utf-8')

def profile():
    return {'schema':'test','recorded_utc':'frozen','static_profile':{
        'product_name':'AMD EPYC 7402','microarchitecture':'Zen 2','socket_count':2,
        'physical_cores_per_socket':{'0':24,'1':24},'installed_logical_processor_count':96,
        'numa_node_count':2,'relevant_isa_flags_reported':['avx','avx2','fma'],
        'cache_domains_for_cpu2':[{'level':1,'type':'Data','size_bytes':32768,'line_bytes':64,'ways':8,'sets':64,'online_physical_cores_in_domain':1},
          {'level':3,'type':'Unified','size_bytes':16*1024*1024,'line_bytes':64,'ways':16,'sets':16384,'online_physical_cores_in_domain':3}]},
        'host_identity':{'machine_id':'test','boot_id':'test'},'execution_state_not_added_to_P2':{'boost':'0'},
        'raw_readonly_evidence':{}}

def request(form='C',src='void kernel_x(int n) {}\n'):
    return {'model':c.MODEL,'raw':True,'stream':False,'keep_alive':'30m',
      'options':{'num_ctx':32768,'num_predict':4096 if form=='C' else 8192,
        'seed':69001,'temperature':0.2,'num_thread':16},
      'prompt':'<|im_start|>system\nReturn code.<|im_end|>\n<|im_start|>user\n'
          +'Target function: kernel_x\nRequired output: '+('a complete C translation unit' if form=='C' else 'a complete LLVM 18 textual IR module')+'\n'
          +c.P0_LINE+'\nContract: preserve bits\n'+c.BEGIN+src.rstrip()+'\n'+c.END+'\n<|im_end|>\n<|im_start|>assistant\n'}

class BasicTests(unittest.TestCase):
    def test_cpu_list(self):self.assertEqual(c.cpu_list('0-3,50'),[0,1,2,3,50])
    def test_bad_cpu_list(self):
        for s in ('1-0','-1','x','999999',''):
            with self.subTest(s=s),self.assertRaises(c.Refuse):c.cpu_list(s)
    def test_cache_units(self):
        self.assertEqual(c.cache_bytes('32K'),32768);self.assertEqual(c.cache_bytes('16M'),16*1024**2)
    def test_bad_cache_units(self):
        for v in ('unknown','0','nan','1.5M'):
            with self.subTest(v=v),self.assertRaises(c.Refuse):c.cache_bytes(v)
    def test_duplicate_json(self):
        with self.assertRaises(c.Refuse):c.decode('{"a":1,"a":2}')
    def test_nan(self):
        with self.assertRaises(c.Refuse):c.decode('{"a":NaN}')
    def test_exclusive_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';c.write(p,b'one')
            with self.assertRaises(FileExistsError):c.write(p,b'two')
            self.assertEqual(p.read_bytes(),b'one')
    def test_bad_paths(self):
        with tempfile.TemporaryDirectory() as d:
            for rel in ('../x','/root/x','x\\z',''):
                with self.subTest(rel=rel),self.assertRaises(c.Refuse):c.safe(Path(d),rel)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c.write(p/'a',b'x');(p/'b').symlink_to(p/'a')
            with self.assertRaises(c.Refuse):c.read(p/'b')
            with self.assertRaises(c.Refuse):c.safe(p,'b')
    def test_hash_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c.write(p/'a',b'one');c.seal(p);c.verify_tree(p)
            (p/'a').write_bytes(b'two')
            with self.assertRaises(c.Refuse):c.verify_tree(p)
    def test_p1_only_identity(self):
        t=c.info_block(profile(),'P1')
        self.assertIn('AMD EPYC 7402',t);self.assertIn('Zen 2',t)
        for word in ('KiB','socket','NUMA','avx','bandwidth'):self.assertNotIn(word,t)
    def test_p2_cache_domain_not_total(self):
        t=c.info_block(profile(),'P2')
        self.assertIn('16384 KiB',t);self.assertNotIn('262144 KiB',t)
        self.assertIn('not a sum across the machine',t)
    def test_p2_no_results_or_dynamic_clocks(self):
        t=c.info_block(profile(),'P2')
        for token in ('speedup','oracle','MHz','throughput','boost='):self.assertNotIn(token,t)
        self.assertIn('FMA prohibition',t)
    def test_english_no_new_special_tokens(self):
        for cond in c.CONDITIONS:
            t=c.info_block(profile(),cond);self.assertTrue(t.isascii());self.assertNotIn('<|',t)
    def test_only_hardware_and_adopted_budget_changes(self):
        for form in c.FORMS:
            for cond in c.CONDITIONS:
                src='void kernel_x(int n) {}\n';old=request(form,src);frozen=copy.deepcopy(old)
                new,b=c.condition_request(old,src,cond,profile(),FakeTokenizer())
                normalized=copy.deepcopy(old);normalized['stream']=True;normalized['options']['num_predict']=c.CAPS[form]
                normalized['prompt']=old['prompt'].replace(c.P0_LINE,c.info_block(profile(),cond))
                self.assertEqual(new,normalized);self.assertEqual(old,frozen)
                self.assertGreater(b['context_slack'],0)
    def test_source_preserved_byte_for_byte(self):
        src='void kernel_x(int n) { /* unknown */\n  n+=1;\n}\n'
        n,_=c.condition_request(request('C',src),src,'P1',profile(),FakeTokenizer())
        self.assertEqual(n['prompt'].split(c.BEGIN)[1].split(c.END)[0],src)
    def test_template_missing_blocks(self):
        q=request();q['prompt']=q['prompt'].replace(c.P0_LINE,'CPU none')
        with self.assertRaises(c.Refuse):c.condition_request(q,'void kernel_x(int n) {}\n','P1',profile(),FakeTokenizer())
    def test_source_mismatch_blocks(self):
        with self.assertRaises(c.Refuse):c.condition_request(request(),'wrong code','P1',profile(),FakeTokenizer())
    def test_duplicate_hardware_marker_blocks(self):
        q=request();q['prompt']+=c.P0_LINE
        with self.assertRaises(c.Refuse):c.condition_request(q,'void kernel_x(int n) {}\n','P1',profile(),FakeTokenizer())
    def test_context_overflow_blocks_not_excludes(self):
        src='void kernel_x(int n) {}\n';q=request();q['prompt']=(' ' * 33000)+q['prompt']
        with self.assertRaises(c.Refuse):c.condition_request(q,src,'P2',profile(),FakeTokenizer())
    def test_fallback_overflow_blocks(self):
        src='void kernel_x(int n) {\n'+(' '*4100)+'}\n'
        with self.assertRaises(c.Refuse):c.condition_request(request('C',src),src,'P1',profile(),FakeTokenizer())
    def test_wrong_model_blocks(self):
        q=request();q['model']='other'
        with self.assertRaises(c.Refuse):c.condition_request(q,'void kernel_x(int n) {}\n','P1',profile(),FakeTokenizer())
    def test_no_unsupported_condition(self):
        with self.assertRaises(c.Refuse):c.info_block(profile(),'P3')
    def test_complete_requires_measurement(self):
        d={'planned_requests':180,'generation_terminal':180,'validation_terminal':180,'measurement_pending':0,'completion':'DATASET_BATCH_COMPLETE','current_session':{'errors':[]}}
        self.assertTrue(c.completed(d,180))
        for k,v in [('planned_requests',True),('generation_terminal',179),('validation_terminal',179),('measurement_pending',1),('completion','DATASET_BATCH_PAUSED')]:
            with self.subTest(k=k):self.assertFalse(c.completed(dict(d,**{k:v}),180))
    def test_candidate_failures_may_be_terminal(self):
        d={'planned_requests':180,'generation_terminal':180,'validation_terminal':180,'measurement_pending':0,'completion':'DATASET_BATCH_COMPLETE','generated_texts':100,'official_gate_passed':2}
        self.assertTrue(c.completed(d,180))
    def test_blocked_predecessor_not_advanced(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);job=root/'P1';job.mkdir()
            with self.assertRaises(c.Refuse),redirect_stdout(io.StringIO()):
                c.wait_service(root,'P1',job,'cpucond69-x.service',query=lambda x:'inactive',pause=lambda x:None)
    def test_wait_is_automatic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);job=root/'P1';c.jw(job/'results/summary.json',{'planned_requests':180,'generation_terminal':180,'validation_terminal':180,'measurement_pending':0,'completion':'DATASET_BATCH_COMPLETE'})
            query=Mock(side_effect=['active','active','inactive']);sleep=Mock()
            with redirect_stdout(io.StringIO()):c.wait_service(root,'P1',job,'cpucond69-x.service',query=query,pause=sleep)
            self.assertEqual(sleep.call_count,2);self.assertEqual(c.load(root/'status.json')['phase'],'P1_COMPLETE')
    def test_child_unit_passes_existing_guard(self):
        u='cpucond69-sequence75-P1-20260913T100000-ab.service';self.assertRegex(u,r'^cpucond69-[A-Za-z0-9-]+\.service$')
    def test_no_total_timeout_in_child(self):
        args=c.stage_command(Path('/root/test'),'P1','cpucond69-test.service','cpucond75-parent.service')
        self.assertIn('--property=RuntimeMaxSec=infinity',args)
        self.assertIn('--property=MemoryMax=96G',args);self.assertIn('--property=TasksMax=256',args)
        self.assertIn('--property=PartOf=cpucond75-parent.service',args)
    def test_no_model_generation_at_prepare(self):
        text=Path(c.__file__).read_text();tree=ast.parse(text)
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and node.name=='prepare':
                body=ast.get_source_segment(text,node)
                for v in ('generation_phase','model_state','run_pipeline','subprocess'):self.assertNotIn(v,body)
    def test_scheduler_unchanged(self):
        root=Path(__file__).parent
        f=c.import_path('original74',root/'finish74/goal0074_finish_all.py')
        f.verify_kit(root/'finish74')
        text=(root/'finish74/until_complete_pipeline.py').read_text()
        self.assertIn('gen_end=math.inf',text);self.assertIn('check_busy();host_guard()',text)

class PreparationTests(unittest.TestCase):
    def test_prepare_all360_no_prior_source_mutation(self):
        with tempfile.TemporaryDirectory() as d,ExitStack() as stack:
            root=Path(d);full=root/'old';p0=root/'p0';out=root/'campaign';kit=Path(c.__file__).parent
            tasks=[];instances=[]
            for k in range(30):
                for size in ('MINI','SMALL','MEDIUM'):
                    task=f'k{k:02d}';base=f'inputs/{task}/{size}';sources={}
                    for form,ext in (('C','c'),('IR','ll')):
                        src='void kernel_x(int n) {}\n';rel=base+'/kernel.'+ext;c.write(full/'work'/rel,src.encode())
                        sources[form]={'path':rel,'sha256':c.digest(src.encode())}
                        q=request(form,src);tid=f'{task}__{size}__{form}__P0__s0';r='requests/'+tid+'.json';c.jw(full/'work'/r,q)
                        tasks.append({'id':tid,'task':task,'size':size,'form':form,'condition':'P0','source':rel,'request':r,
                            'request_sha256':c.digest(c.read(full/'work'/r)),'sample':0,'seed':69001,'context_budget_ok':True,'input_byte_upper':len(q['prompt'])+32})
                    driver=base+'/driver.c';oracle=base+'/oracle.raw';c.write(full/'work'/driver,b'driver');c.write(full/'work'/oracle,b'bytes')
                    instances.append({'task':task,'size':size,'sources':sources,'driver':driver,'oracle':oracle})
            for rel in ('utilities/polybench.c','utilities/polybench.h'):c.write(full/'work'/rel,b'utils')
            fullplan={'conditions':['P0'],'requests':180,'tasks':tasks,'instances_list':instances,'prompt_language':'en',
                'kernels':30,'instances':90,'representations':['C','IR'],'samples':1,'additional_calls_for_P1_P2':False}
            p0plan={**fullplan,'requests':166,'tasks':tasks[14:]}
            c.jw(full/'work/plan.json',fullplan);c.seal(full/'work')
            fakehash={}
            for name in c.BASE_HASHES:
                raw=('fixed implementation '+name).encode();c.write(p0/'work'/name,raw);fakehash[name]=c.digest(raw)
            before={str(p):c.digest(p.read_bytes()) for p in root.rglob('*') if p.is_file()}
            stack.enter_context(patch.object(c,'FULL',full));stack.enter_context(patch.object(c,'P0',p0))
            stack.enter_context(patch.object(c,'BASE_HASHES',fakehash))
            stack.enter_context(patch.object(c,'verify_sources',return_value=(fullplan,p0plan,c.verify_tree(full/'work'),fakehash)))
            with redirect_stdout(io.StringIO()):c.prepare(out,kit,FakeTokenizer(),profile())
            campaign=c.verify_installed(out)
            self.assertEqual(campaign['additional_requests'],360);self.assertEqual(len(campaign['same_budget_comparison_ids']),166)
            for condition in c.CONDITIONS:
                work=out/condition/'work';p=c.load(work/'plan.json')
                self.assertEqual(p['requests'],180);self.assertEqual(p['conditions'],[condition]);self.assertTrue(p['additional_calls_for_P1_P2'])
                self.assertEqual(len({x['id'] for x in p['tasks']}),180)
                for t,original in zip(p['tasks'],tasks):
                    req=c.load(work/t['request']);old=c.load(full/'work'/original['request'])
                    self.assertEqual(req['prompt'].split(c.BEGIN)[1],old['prompt'].split(c.BEGIN)[1])
                    self.assertEqual(req['options']['seed'],old['options']['seed'])
                    self.assertNotIn(c.P0_LINE,req['prompt']);self.assertIn('condition '+condition,req['prompt'])
                    self.assertNotIn('oracle',req['prompt']);self.assertNotIn('speedup',req['prompt'])
                for name,h in fakehash.items():self.assertEqual(c.digest(c.read(work/name)),h)
            for p,h in before.items():self.assertEqual(c.digest(Path(p).read_bytes()),h)
            snap={str(p):c.digest(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
            with redirect_stdout(io.StringIO()):c.prepare(out,kit,None,None)
            for p,h in snap.items():self.assertEqual(c.digest(Path(p).read_bytes()),h)

class SequenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.effects=[];self.done=set();self.s=ExitStack()
        c.jw(self.root/'control/campaign.json',{})
        self.s.enter_context(patch.object(c,'host'));self.s.enter_context(patch.object(c,'verify_installed',return_value={}))
        self.s.enter_context(patch.dict(c.os.environ,{'CPUCOND_CHAIN_UNIT':'cpucond75-p012-test.service'}))
        real_read=Path.read_text
        def readtext(path,*a,**k):
            if str(path)=='/proc/self/cgroup':return '0::/system.slice/cpucond75-p012-test.service'
            return real_read(path,*a,**k)
        self.s.enter_context(patch.object(Path,'read_text',readtext))
        real_open=builtins.open
        def op(path,*a,**k):return real_open(self.root/'test.lock' if str(path)=='/var/lock/cpucond-p01275-worker.lock' else path,*a,**k)
        self.s.enter_context(patch('builtins.open',op))
        self.s.enter_context(patch.object(c,'P0',self.root/'P0'))
        self.s.enter_context(patch.object(c,'summary_exists_complete',side_effect=lambda j,n:j.name in self.done))
        def launch(job):
            self.effects.append('launchP0');c.write(job/'completion-driven-v1/active-unit.txt',b'cpucond69-completion74-test.service\n')
        self.s.enter_context(patch.object(c,'finish74',return_value=SimpleNamespace(launch=launch,CONTROL='completion-driven-v1')))
        self.s.enter_context(patch.object(c,'p0_receipt',side_effect=lambda root:self.effects.append('receiptP0')))
        def start(root,condition,parent):self.effects.append('launch'+condition);return 'cpucond69-'+condition+'.service'
        self.s.enter_context(patch.object(c,'start_stage',side_effect=start))
        def wait(root,cond,job,unit):self.effects.append('wait'+cond);self.done.add(cond)
        self.s.enter_context(patch.object(c,'wait_service',side_effect=wait))
        self.s.enter_context(patch.object(c,'base_module',return_value=SimpleNamespace(results_summary=lambda p,r:{'generation_terminal':180,'validation_terminal':180,'measurement_pending':0})))
        for cond in ('P1','P2'):c.jw(self.root/cond/'work/plan.json',{})
    def tearDown(self):self.s.close();self.temp.cleanup()
    def test_p0_then_p1_then_p2(self):
        with redirect_stdout(io.StringIO()):c.orchestrate(self.root)
        self.assertEqual(self.effects,['launchP0','waitP0','receiptP0','launchP1','waitP1','launchP2','waitP2'])
        self.assertEqual(c.load(self.root/'status.json')['phase'],'P012_ALL_COMPLETE')
    def test_already_complete_not_regenerated(self):
        self.done={'P0','P1'}
        with redirect_stdout(io.StringIO()):c.orchestrate(self.root)
        self.assertEqual(self.effects,['receiptP0','launchP2','waitP2'])
    def test_failed_p0_no_p1(self):
        with patch.object(c,'wait_service',side_effect=c.Refuse('P0 failure')):
            with self.assertRaises(c.Refuse),redirect_stdout(io.StringIO()):c.orchestrate(self.root)
        self.assertEqual(self.effects,['launchP0'])
    def test_failed_p1_no_p2(self):
        self.done={'P0'}
        with patch.object(c,'wait_service',side_effect=c.Refuse('P1 failure')):
            with self.assertRaises(c.Refuse),redirect_stdout(io.StringIO()):c.orchestrate(self.root)
        self.assertEqual(self.effects,['receiptP0','launchP1'])
    def test_all_already_done_no_launch(self):
        self.done={'P0','P1','P2'}
        with redirect_stdout(io.StringIO()):c.orchestrate(self.root)
        self.assertEqual(self.effects,['receiptP0'])

class HardwareTests(unittest.TestCase):
    def fixture(self,root):
        cpu=root/'cpu';node=root/'node';proc=root/'proc'
        def put(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(str(s))
        put(cpu/'present','0-95');put(cpu/'online','0-47');put(node/'online','0-1')
        put(cpu/'smt/active','0');put(cpu/'cpufreq/boost','0');put(cpu/'cpu2/cpufreq/scaling_governor','performance')
        put(cpu/'cpu2/topology/thread_siblings_list','2,50')
        blocks=[]
        for i in range(48):
            put(cpu/f'cpu{i}/topology/core_id',i%24);put(cpu/f'cpu{i}/topology/physical_package_id',i//24)
            (cpu/f'cpu{i}/node{i//24}').mkdir()
            blocks.append(f'processor : {i}\nmodel name : AMD EPYC 7402 24-Core Processor\ncpu family : 23\nmodel : 49\nstepping : 0\nflags : avx avx2 fma sse2')
        put(proc/'cpuinfo','\n\n'.join(blocks))
        for idx,level,typ,size,shared in [(0,1,'Data','32K','2,50'),(1,1,'Instruction','32K','2,50'),(2,2,'Unified','512K','2,50'),(3,3,'Unified','16M','0-2,48-50')]:
            p=cpu/f'cpu2/cache/index{idx}'
            for k,v in {'level':level,'type':typ,'size':size,'shared_cpu_list':shared,'coherency_line_size':64,'ways_of_associativity':8,'number_of_sets':64}.items():put(p/k,v)
        return cpu,node,proc
    def test_reads_cache_domain_without_machine_sum(self):
        with tempfile.TemporaryDirectory() as d:
            p=c.capture_hardware(*self.fixture(Path(d)))
            st=p['static_profile'];self.assertEqual(st['online_physical_core_count'],48)
            self.assertEqual(st['installed_logical_processor_count'],96)
            self.assertEqual(st['cache_domains_for_cpu2'][-1]['size_bytes'],16777216)
            self.assertEqual(st['cache_domains_for_cpu2'][-1]['online_physical_cores_in_domain'],3)
            self.assertEqual(st['cpu2_smt_siblings_reported'],[2,50])
    def test_wrong_boost_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.fixture(Path(d));(paths[0]/'cpufreq/boost').write_text('1')
            with self.assertRaises(c.Refuse):c.capture_hardware(*paths)
    def test_missing_cache_information_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.fixture(Path(d));(paths[0]/'cpu2/cache/index3/level').write_text('4')
            with self.assertRaises(c.Refuse):c.capture_hardware(*paths)
    def test_recorded_clock_not_in_static_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            paths=self.fixture(Path(d));withclock=(paths[2]/'cpuinfo').read_text()+'\ncpu MHz : 9999'
            (paths[2]/'cpuinfo').write_text(withclock)
            p=c.capture_hardware(*paths);self.assertNotIn('9999',c.info_block(p,'P2'))

if __name__=='__main__':unittest.main(verbosity=2)
