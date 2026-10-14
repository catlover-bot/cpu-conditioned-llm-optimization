from __future__ import annotations
import copy
import http.server
import importlib.util
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest import mock
import goal0073_resource_amendment as a
from streaming_support import Collector, StreamFailure, receive
import runtime_support as rt
import goal0069_batch_codegen as b

MODEL=a.MODEL

def line(text='', done=False, reason='stop'):
    d={'model':MODEL,'response':text,'done':done}
    if done:d.update(done_reason=reason,prompt_eval_count=20,eval_count=3,eval_duration=3000000)
    return json.dumps(d,ensure_ascii=False).encode()+b'\n'

class MockResponse:
    def __init__(self,lines,status=200):self.lines=iter(lines);self.status=status
    def readline(self,n):return next(self.lines,b'')
    def read(self,n):return b'error'

class MockConnection:
    def __init__(self,response):self.response=response;self.sock=None;self.requests=[]
    def connect(self):pass
    def request(self,*args,**kwargs):self.requests.append((args,kwargs))
    def getresponse(self):return self.response
    def close(self):pass

class Tests(unittest.TestCase):
    def test_stream_join(self):
        c=Collector(MODEL)
        c.add(line('a'));c.add(line('b'));c.add(line('c',True))
        self.assertEqual(c.finish()['response'],'abc')
    def test_unicode(self):
        c=Collector(MODEL);c.add(line('あ'));c.add(line('é',True))
        self.assertEqual(c.finish()['response'],'あé')
    def test_incomplete(self):
        c=Collector(MODEL);c.add(line('x'))
        with self.assertRaises(StreamFailure):c.finish()
    def test_wrong_model(self):
        c=Collector(MODEL)
        with self.assertRaises(StreamFailure):c.add(b'{"model":"bad","done":true,"response":"x"}')
    def test_duplicate(self):
        with self.assertRaises(StreamFailure):Collector(MODEL).add(b'{"model":"a","model":"b"}')
    def test_nan(self):
        with self.assertRaises(StreamFailure):Collector(MODEL).add(b'{"x":NaN}')
    def test_model_error(self):
        with self.assertRaises(StreamFailure):Collector(MODEL).add(b'{"error":"failure"}')
    def test_record_after_done(self):
        c=Collector(MODEL);c.add(line('x',True))
        with self.assertRaises(StreamFailure):c.add(line('y'))
    def test_empty_final_metadata(self):
        c=Collector(MODEL);c.add(line('kernel'));c.add(line('',True))
        self.assertEqual(c.finish()['response'],'kernel')
    def test_length_is_recorded_not_success(self):
        c=Collector(MODEL);c.add(line('x',True,'length'))
        self.assertEqual(c.finish()['done_reason'],'length')
        with self.assertRaises(b.Blocked):b.extract_response(c.finish(),{'form':'IR','task':'t','input_byte_upper':50})
    def test_unknown_done_reason(self):
        with self.assertRaises(StreamFailure):Collector(MODEL).add(line('x',True,'other'))
    def test_thinking_rejected(self):
        d=json.loads(line('x',True));d['thinking']='secret'
        with self.assertRaises(StreamFailure):Collector(MODEL).add(json.dumps(d))
    def test_stream_payload_required(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(StreamFailure):receive({'model':MODEL,'raw':True,'stream':False},t,1)
    def test_stream_files_saved(self):
        conn=MockConnection(MockResponse([line('code'),line('',True)]))
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            obj,meta=receive({'model':MODEL,'raw':True,'stream':True},d,2,
                 connection_factory=lambda *a,**kw:conn)
            self.assertEqual(obj['response'],'code')
            self.assertEqual((d/'response.partial.txt').read_text(),'code')
            self.assertTrue(meta['reconstructed_response'])
            self.assertEqual(conn.requests[0][0],('POST','/api/generate'))
    def test_partial_retained_on_disconnect(self):
        conn=MockConnection(MockResponse([line('partial')]))
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(StreamFailure):receive({'model':MODEL,'raw':True,'stream':True},t,1,
                connection_factory=lambda *a,**kw:conn)
            self.assertEqual((Path(t)/'response.partial.txt').read_text(),'partial')
    def test_no_resubmit_existing_stream(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t)/'response.stream.jsonl').touch()
            with self.assertRaises(StreamFailure):receive({'model':MODEL,'raw':True,'stream':True},t,1)
    def test_http_error_retained(self):
        conn=MockConnection(MockResponse([],400))
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(StreamFailure):receive({'model':MODEL,'raw':True,'stream':True},t,1,
                connection_factory=lambda *a,**kw:conn)
            self.assertTrue((Path(t)/'response.http-error.txt').exists())
    def test_fixed_budgets(self):
        self.assertEqual(rt.request_limit({'form':'C'}),1800)
        self.assertEqual(rt.request_limit({'form':'IR'}),7200)
        self.assertEqual(b.CAPS,{'C':4096,'IR':16384})
    def test_no_start_without_full_time(self):
        self.assertFalse(rt.can_start({'form':'IR'},0,7200))
        self.assertTrue(rt.can_start({'form':'IR'},0,7245))
    def test_budget_known_long(self):
        x=a.budget(12360,11906,'IR')
        self.assertEqual(x['context_slack'],3992)
        self.assertEqual(x['unchanged_fallback_slack'],4414)
    def test_budget_output_reject(self):
        with self.assertRaises(a.Refuse):a.budget(1000,16384,'IR')
    def test_budget_context_reject(self):
        with self.assertRaises(a.Refuse):a.budget(17000,1000,'IR')
    def test_budget_boolean_reject(self):
        with self.assertRaises(a.Refuse):a.budget(True,10,'C')
    def test_request_only_two_changes(self):
        old={'model':MODEL,'raw':True,'stream':False,'prompt':'same',
             'options':{'num_ctx':32768,'num_predict':8192,'seed':69001}}
        before=copy.deepcopy(old);new=a.amend_request(old,'IR')
        self.assertEqual(old,before)
        expected=copy.deepcopy(old);expected['stream']=True;expected['options']['num_predict']=16384
        self.assertEqual(new,expected)
    def test_old_contract_rejected(self):
        with self.assertRaises(a.Refuse):a.amend_request({'model':MODEL,'stream':True},'IR')
    def test_safe_absolute(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(a.Refuse):a.safe(Path(t),'/root')
    def test_safe_escape(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(a.Refuse):a.safe(Path(t),'../other')
    def test_safe_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t)/'link').symlink_to('/tmp')
            with self.assertRaises(a.Refuse):a.safe(Path(t),'link/test')
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'file';a.write(p,b'a')
            with self.assertRaises(FileExistsError):a.write(p,b'b')
    def test_unstarted(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(a.prior_state(Path(t),'task')['attempted'])
    def test_old_exclusion_unattempted(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'results/generation/task';d.mkdir(parents=True)
            a.jw(d/'result.json',{'status':'input_budget_excluded'})
            self.assertFalse(a.prior_state(Path(t),'task')['attempted'])
    def test_saved_attempt_not_retried(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'results/generation/task';d.mkdir(parents=True)
            a.jw(d/'result.json',{'status':'saved'})
            self.assertTrue(a.prior_state(Path(t),'task')['attempted'])
    def test_timeout_attempt_not_retried(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'results/generation/task';d.mkdir(parents=True)
            a.jw(d/'result.json',{'status':'generation_transport_failure'})
            self.assertTrue(a.prior_state(Path(t),'task')['attempted'])
    def test_started_unknown_not_retried(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'results/generation/task';d.mkdir(parents=True)
            a.jw(d/'started.json',{'utc':'x'})
            self.assertTrue(a.prior_state(Path(t),'task')['attempted'])
    def test_partial_not_retried(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'results/generation/task';d.mkdir(parents=True)
            a.write(d/'response.partial.txt',b'x')
            self.assertTrue(a.prior_state(Path(t),'task')['attempted'])
    def test_result_scope_subset(self):
        with tempfile.TemporaryDirectory() as t:
            x=b.results_summary({'tasks':[{'id':'x'}],'scope':'new resource cohort'},Path(t))
            self.assertEqual(x['planned_requests'],1)
            self.assertEqual(x['requests_pending'],1)
            self.assertEqual(x['scope'],'new resource cohort')
    def test_precise_stop_at_cap_allowed(self):
        item={'form':'C','task':'t','input_byte_upper':100}
        obj=json.loads(line('void kernel_t(void){}',True));obj.update(eval_count=4096,prompt_eval_count=20)
        code,_=b.extract_response(obj,item)
        self.assertIn('kernel_t',code)
    def test_validator_functions_unchanged(self):
        import ast
        here=Path(__file__).resolve().parent
        old=ast.parse((here/'legacy_runner.py').read_text())
        new=ast.parse((here/'goal0069_batch_codegen.py').read_text())
        def fs(tree):return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        oo,nn=fs(old),fs(new)
        for name in ('Sandbox','prepare_baseline','stress_gate','validate_candidate','measurement','policy','abi_c','ir_abi','host_guard'):
            self.assertEqual(oo[name],nn[name],name)
    def test_real_loopback_stream(self):
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.server.body=self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.end_headers()
                for raw in (line('hello'),line(' world',True)):
                    self.wfile.write(raw);self.wfile.flush()
            def log_message(self,*args):pass
        server=http.server.HTTPServer(('127.0.0.1',0),H)
        th=threading.Thread(target=server.handle_request,daemon=True);th.start()
        try:
            with tempfile.TemporaryDirectory() as t:
                obj,_=receive({'model':MODEL,'raw':True,'stream':True},t,2,port=server.server_port)
                self.assertEqual(obj['response'],'hello world')
                self.assertTrue(json.loads(server.body)['stream'])
        finally:server.server_close();th.join(2)
    def test_real_absolute_timeout_retains_fragments(self):
        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.end_headers()
                try:
                    for _ in range(30):
                        self.wfile.write(line('x'));self.wfile.flush();time.sleep(.02)
                except (BrokenPipeError,ConnectionResetError):pass
            def log_message(self,*args):pass
        server=http.server.HTTPServer(('127.0.0.1',0),H)
        th=threading.Thread(target=server.handle_request,daemon=True);th.start()
        try:
            with tempfile.TemporaryDirectory() as t:
                start=time.monotonic()
                with self.assertRaises((TimeoutError,StreamFailure,OSError)):
                    receive({'model':MODEL,'raw':True,'stream':True},t,.15,port=server.server_port)
                self.assertLess(time.monotonic()-start,2)
                self.assertTrue((Path(t)/'response.partial.txt').stat().st_size>0)
        finally:server.server_close();th.join(2)


class IntegrationTests(unittest.TestCase):
    def test_generation_timeout_continues_without_resend(self):
        import contextlib, io
        freeze={'manifest_sha256':'abc'}
        class Proc:
            pid=987654
            def poll(self):return None
        def api(path,payload=None,timeout=20):
            data={'/api/version':{'version':'0.33.3'},
                  '/api/tags':{'models':[{'name':MODEL,'digest':'abc'}]},
                  '/api/show':{'model_info':{'qwen2.context_length':32768}}}[path]
            return b'',data
        calls=[]
        def fake_receive(payload,d,*args,**kw):
            calls.append(d.name)
            if len(calls)==1:raise TimeoutError('test timeout')
            obj=json.loads(line('void kernel_t(void){}',True))
            return obj,{'reconstructed_response':True}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pkg=root/'work';pkg.mkdir();run=root/'results';(run/'sessions').mkdir(parents=True)
            tasks=[]
            for n in ('one','two'):
                req={'model':MODEL,'raw':True,'stream':True,'options':{'num_predict':4096}}
                b.jw(pkg/(n+'.json'),req)
                tasks.append({'id':n,'form':'C','task':'t','size':'MINI','context_budget_ok':True,
                    'request':n+'.json','request_sha256':b.sha(pkg/(n+'.json')),
                    'reference_tokenizer_input_tokens':20,'input_byte_upper':50})
            plan={'tasks':tasks,'revision':a.REV,'scope':'test'}
            with mock.patch.object(rt,'receive',side_effect=fake_receive), \
                 mock.patch.object(b,'check_busy'),mock.patch.object(b,'stop') as stop, \
                 mock.patch.object(b,'api',side_effect=api), \
                 mock.patch.object(b.subprocess,'Popen',side_effect=lambda *x,**kw:Proc()) as popen, \
                 contextlib.redirect_stdout(io.StringIO()):
                rt.generation_phase(b,pkg,plan,run,time.monotonic()+10000,freeze,Path('/dummy'))
            self.assertEqual(calls,['one','two'])
            self.assertEqual(popen.call_count,2)
            self.assertEqual(b.load(run/'generation/one/result.json')['status'],'generation_transport_failure')
            self.assertEqual(b.load(run/'generation/two/result.json')['status'],'saved')
            # A subsequent resume submits neither completed request.
            calls.clear()
            with mock.patch.object(rt,'receive',side_effect=fake_receive),mock.patch.object(b,'check_busy'), \
                 mock.patch.object(b,'stop'),contextlib.redirect_stdout(io.StringIO()):
                rt.generation_phase(b,pkg,plan,run,time.monotonic()+10000,freeze,Path('/dummy'))
            self.assertEqual(calls,[])

    def test_prepare_180_audit_166_new_no_old_write(self):
        import contextlib, io, types
        import sys
        class Encoding:
            def __init__(self,text):self.ids=list(text.encode())
        class Token:
            @classmethod
            def from_file(cls,path):return cls()
            def no_truncation(self):pass
            def no_padding(self):pass
            def encode(self,text,add_special_tokens=False):return Encoding(text)
            def decode(self,ids,skip_special_tokens=False):return bytes(ids).decode()
        kit=Path(__file__).resolve().parent
        verify=a.verify_list
        def partialverify(root):return {} if root==kit else verify(root)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parent=root/'parent';work=parent/'work';work.mkdir(parents=True)
            supp=root/'supp';(supp/'work').mkdir(parents=True)
            audit=root/'audit/report';audit.mkdir(parents=True)
            plan={'conditions':['P0'],'prompt_language':'en','tasks':[],
                  'instances_list':[],'representations':['C','IR']}
            for size in ('MINI','SMALL','MEDIUM'):
                for k in range(30):
                    task=f'k{k:02d}';prefix=f'inputs/{task}/{size}'
                    inst={'task':task,'size':size,'sources':{},'driver':prefix+'/driver.c','oracle':prefix+'/oracle.raw'}
                    for form,ext in (('C','c'),('IR','ll')):
                        tid=f'{task}__{size}__{form}__P0__s0';src=prefix+'/kernel.'+ext
                        content=b'original source\n';a.write(work/src,content)
                        inst['sources'][form]={'path':src,'sha256':a.digest(content)}
                        req={'model':MODEL,'prompt':'exact prompt '+tid,'raw':True,'stream':False,
                             'options':{'num_ctx':32768,'num_predict':a.OLD_CAPS[form],'seed':69001}}
                        path='requests/'+tid+'.json';a.jw(work/path,req)
                        plan['tasks'].append({'id':tid,'task':task,'size':size,'form':form,'condition':'P0',
                            'request':path,'request_sha256':a.digest(a.read(work/path)),'source':src})
                    a.write(work/inst['driver'],b'driver');a.write(work/inst['oracle'],b'reference')
                    plan['instances_list'].append(inst)
            a.jw(work/'plan.json',plan);a.write(work/'goal0069_batch_codegen.py',b'legacy')
            a.write(work/'utilities/polybench.c',b'util');a.write(work/'utilities/polybench.h',b'header')
            a.seal(work)
            a.jw(supp/'work/plan.json',{'revision':'supp'})
            for task in plan['tasks'][:13]:
                a.jw(parent/'results/generation'/task['id']/'result.json',{'status':'saved'})
            # Former exclusion can have a failed first attempt in supplement.
            tid=plan['tasks'][13]['id']
            a.jw(parent/'results/generation'/tid/'result.json',{'status':'input_budget_excluded'})
            a.jw(supp/'results/generation'/tid/'result.json',{'status':'generation_transport_failure'})
            a.write(audit.parent/'tokenizer.json',b'tokenizer')
            psha=a.digest(a.read(work/'plan.json'));ssha=a.digest(a.read(supp/'work/plan.json'))
            a.jw(audit/'summary.json',{'source_plan_sha256':psha,'observed_count_mismatches':0,
                'crosscheck_supported_on_saved_examples':True,'tokenizer_sha256':a.digest(b'tokenizer')})
            def inv():
                return {str(f.relative_to(root)):a.digest(a.read(f)) for p in (parent,supp,audit.parent) for f in p.rglob('*') if f.is_file()}
            before=inv();out=root/'new'
            with mock.patch.object(a,'idle'),mock.patch.object(a,'LOCK_FILE',str(root/'lock')), \
                 mock.patch.object(a,'verify_list',side_effect=partialverify), \
                 mock.patch.object(a,'PARENT_SHA',psha),mock.patch.object(a,'SUPPLEMENT_SHA',ssha), \
                 mock.patch.object(a,'RUNNER_SHA',a.digest(b'legacy')), \
                 mock.patch.object(a.importlib.metadata,'version',return_value='0.21.4'), \
                 mock.patch.dict(sys.modules,{'tokenizers':types.SimpleNamespace(Tokenizer=Token)}), \
                 contextlib.redirect_stdout(io.StringIO()):
                a.prepare(parent,supp,audit,out)
            self.assertEqual(inv(),before)
            new=a.load(out/'work/plan.json')
            self.assertEqual(new['requests'],166)
            self.assertEqual(len(new['tasks']),166)
            self.assertEqual(new['resource_amendment']['old_attempted_requests_retained'],14)
            self.assertFalse(set(t['id'] for t in new['tasks']) & set(t['id'] for t in plan['tasks'][:14]))
            for t in new['tasks']:
                q=a.load(out/'work'/t['request']);old=a.load(work/t['request'])
                self.assertEqual(q['prompt'],old['prompt']);q['stream']=False
                q['options']['num_predict']=old['options']['num_predict'];self.assertEqual(q,old)
            verify(out/'work')

if __name__=='__main__':unittest.main(verbosity=2)
