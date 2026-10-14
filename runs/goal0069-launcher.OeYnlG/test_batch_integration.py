#!/usr/bin/env python3
"""信頼済み合成fixtureだけの統合試験。実サーバーの名前空間を試したとは扱わない。"""
import importlib.util, pathlib, tempfile, subprocess, shutil, struct, unittest, sys, time
from unittest.mock import patch
P=pathlib.Path
spec=importlib.util.spec_from_file_location('batch69',P(__file__).with_name('goal0069_batch_codegen.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class TrustedFixtureBox:
    def call(self,argv,inputs,stem,timeout=60,output_names=()):
        stem=P(stem);stem.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            root=P(tmp);i=root/'in';o=root/'out';i.mkdir();o.mkdir()
            for name,p in inputs.items():shutil.copyfile(p,i/name);(i/name).chmod(p.stat().st_mode & 0o777)
            def arg(x):return str(x).replace('/in/',str(i)+'/').replace('/out/',str(o)+'/').replace('-I/in','-I'+str(i))
            cmd=list(map(arg,argv));p=subprocess.run(cmd,capture_output=True,timeout=timeout)
            b.write(stem.with_suffix('.stdout'),p.stdout);b.write(stem.with_suffix('.stderr'),p.stderr)
            paths={}
            if p.returncode==0:
                for name in output_names:
                    q=stem.parent/(stem.name+'-'+name);shutil.copyfile(o/name,q)
                    if name=='program':q.chmod(0o755)
                    paths[name]=q
            return {'state':'ok' if p.returncode==0 else 'exit_nonzero','returncode':p.returncode},p.stdout,paths

class Integration(unittest.TestCase):
    def fixture(self,root):
        pkg=root/'pkg';run=root/'results';run.mkdir();d=pkg/'inputs/t/MINI';d.mkdir(parents=True)
        c='__attribute__((noinline)) void kernel_t(int n,double a[n]){for(int i=0;i<n;i++)a[i]*=2;}'
        (d/'kernel.c').write_text(c);(d/'driver.c').write_text(b.FIXTURE)
        (d/'oracle.raw').write_bytes(struct.pack('<3d',2,4,6))
        (pkg/'utilities').mkdir();(pkg/'utilities/polybench.h').write_text('')
        (pkg/'utilities/polybench.c').write_text('int dummy(void){return 0;}')
        clang,_=b.clang_path(False)
        p=subprocess.run([clang,'-O0','-Xclang','-disable-O0-optnone','-S','-emit-llvm',d/'kernel.c','-o',d/'kernel.ll'],capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr.decode())
        ir=d/'kernel.ll';ir.write_text(b.vendor('roundtrip_support.py').sanitize_ir(ir.read_text()))
        inst={'task':'t','size':'MINI','function':'kernel_t','sources':{
         'C':{'path':'inputs/t/MINI/kernel.c'},'IR':{'path':'inputs/t/MINI/kernel.ll'}},
         'driver':'inputs/t/MINI/driver.c','oracle':'inputs/t/MINI/oracle.raw'}
        return pkg,run,clang,inst
    def test_two_representations_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg,run,clang,inst=self.fixture(P(tmp));box=TrustedFixtureBox()
            base=b.prepare_baseline(box,clang,pkg,inst,run)
            self.assertTrue(base['passed'],base)
            for form in ('C','IR'):
                item={'id':'t__MINI__'+form,'task':'t','size':'MINI','form':form}
                gen=run/'generation'/item['id'];gen.mkdir(parents=True)
                src=pkg/inst['sources'][form]['path'];cand=gen/('candidate.c' if form=='C' else 'candidate.ll');shutil.copyfile(src,cand)
                b.jw(gen/'result.json',{'status':'saved','code_sha256':b.sha(cand)})
                result=b.validate_candidate(box,clang,pkg,{},run,item,inst,base)
                self.assertTrue(result['official_all_passed'],result)
                self.assertEqual(result['multiinput_status'],'not_implemented_for_task')
                self.assertTrue(result['measurement_eligible_provisional'])
                td=P(base['timing']['program'])
                r,raw=b.execute_program(box,td,run/('basic-time-'+form),[2]);self.assertEqual(r['state'],'ok');self.assertGreater(b.parse_batch(raw,2),0)
    def test_modified_correct_code_and_wrong_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg,run,clang,inst=self.fixture(P(tmp));box=TrustedFixtureBox();base=b.prepare_baseline(box,clang,pkg,inst,run)
            for tag,factor,answer in [('changed',2,True),('wrong',3,False)]:
                item={'id':tag,'task':'t','size':'MINI','form':'C'};gen=run/'generation'/tag;gen.mkdir(parents=True)
                cand=gen/'candidate.c';cand.write_text(f'void kernel_t(int n,double a[n]){{int i=0;while(i<n){{a[i]=a[i]*{factor};i++;}}}}')
                b.jw(gen/'result.json',{'status':'saved','code_sha256':b.sha(cand)})
                result=b.validate_candidate(box,clang,pkg,{},run,item,inst,base)
                self.assertEqual(result['official_all_passed'],answer,result)
    def test_preprocessed_driver_not_reincluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg,run,clang,inst=self.fixture(P(tmp));driver=pkg/inst['driver']
            pp=subprocess.check_output([clang,'-std=gnu11','-E','-P',driver],text=True)
            driver.write_text(pp);box=TrustedFixtureBox();base=b.prepare_baseline(box,clang,pkg,inst,run)
            self.assertTrue(base['passed'],base)
            r,raw=b.execute_program(box,P(base['timing']['program']),run/'check-time',[3]);self.assertEqual(r['state'],'ok');self.assertGreater(b.parse_batch(raw,3),0)

    def recovery_case(self,existing_response):
        with tempfile.TemporaryDirectory() as tmp:
            root=P(tmp);run=root/'run';(run/'sessions').mkdir(parents=True)
            item={'id':'k__MINI__C','task':'k','size':'MINI','form':'C','context_budget_ok':True,'input_byte_upper':1000}
            d=run/'generation'/item['id'];d.mkdir(parents=True)
            b.jw(d/'started.json',{'utc':'old'})
            if existing_response:b.jw(d/'response.raw.json',{'model':b.MODEL,'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':20,'response':'void kernel_k(){}'})
            plan={'tasks':[item]};calls=[]
            def fake(path,payload=None,timeout=20):
                calls.append(path)
                if path=='/api/version':return b'',{'version':'0.33.3'}
                if path=='/api/tags':return b'',{'models':[{'name':b.MODEL,'digest':'abc'}]}
                if path=='/api/show':return b'',{'model_info':{'qwen2.context_length':32768}}
                raise AssertionError('保存済み要求を再送した')
            class Service:
                def poll(self):return None
            with patch.object(b,'api',side_effect=fake),patch.object(b.subprocess,'Popen',return_value=Service()),patch.object(b,'stop'):
                b.generation_phase(root,plan,run,time.monotonic()+3600,{'manifest_sha256':'abc'},P('/not/executed'))
            self.assertNotIn('/api/generate',calls)
            return b.load(d/'result.json')
    def test_resume_saved_response_not_resent(self):
        self.assertEqual(self.recovery_case(True)['status'],'saved')
    def test_interrupted_request_not_resent(self):
        self.assertEqual(self.recovery_case(False)['status'],'interrupted_unknown_response')

if __name__=='__main__':unittest.main(verbosity=2)
