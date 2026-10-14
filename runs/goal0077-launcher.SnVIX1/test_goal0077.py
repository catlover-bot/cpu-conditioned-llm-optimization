from __future__ import annotations
import contextlib
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import goal0077_export_p012 as b


def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')

def rows(speed=1.02):
    return [{'session':s,'trial':i,'reference_ns':1020000,'candidate_ns':1020000/speed,
             'speedup':speed,'order':i%2,'batch':1} for s in range(2) for i in range(8)]

def summaries(xs,identity=False):
    return [b.qsummary([x for x in xs if x['session']==s],identity) for s in (0,1)]

def fixture(root,n_all=180,n_common=166):
    chain=root/'campaign';p0=root/'p0'; control=chain/'control';control.mkdir(parents=True)
    # Same composition as 30 kernels x 3 sizes x 2 forms, with a restricted common cohort.
    keys=[(f'k{i:02d}',size,form) for size in ('MINI','SMALL','MEDIUM') for i in range(30) for form in ('C','IR')][:n_all]
    plans={}; stats={};commonids=[]
    for label,base,selected in (('P0',p0,keys[-n_common:]),('P1',chain/'P1',keys),('P2',chain/'P2',keys)):
        items=[];inst={};data=[]
        for i,k in enumerate(selected):
            name,size,form=k;tid='__'.join(k)+'__'+label+'__s0'
            src=f'inputs/{name}/{size}/kernel.'+('c' if form=='C' else 'll')
            text='void kernel_'+name+'(void) {}\n' if form=='C' else 'define void @kernel_'+name+'() { ret void }\n'
            path=base/'work'/src;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            h=b.digest(path)
            ik=(name,size)
            inst.setdefault(ik,{'task':name,'size':size,'sources':{}})['sources'][form]={'path':src,'sha256':h}
            block=b.P0_LINE if label=='P0' else f'Target CPU information (condition {label}):\n- CPU model: AMD EPYC 7402.'
            req={'model':b.MODEL,'raw':True,'stream':True,'prompt':'Optimize.\n'+block+'\n'+b.BEGIN+text+b.END,
                 'options':{'seed':1,'num_ctx':32768,'num_predict':4096 if form=='C' else 16384}}
            rpath=f'requests/{tid}.json';write(base/'work'/rpath,req)
            items.append({'id':tid,'task':name,'size':size,'form':form,'condition':label,'source':src,
                          'request':rpath,'request_sha256':b.digest(base/'work'/rpath)})
            gdir=base/'results/generation'/tid;gdir.mkdir(parents=True)
            genfail=label=='P2' and i==0
            failure=i%9==2
            speed=1.02 if label=='P0' else 1.04 if label=='P1' else .98
            g={'status':'invalid_generation','error':'test truncated'} if genfail else {'status':'saved','code_sha256':h,'receipt':{'input_tokens':22,'output_tokens':5}}
            if not genfail:(gdir/('candidate.c' if form=='C' else 'candidate.ll')).write_text(text)
            write(gdir/'result.json',g)
            ok=not genfail and not failure
            v={'status':'generation_failed' if genfail else 'candidate_rejected' if failure else 'checked',
               'official_all_passed':ok,'multiinput_status':'not_implemented_for_task' if ok else 'not_run',
               'measurement_eligible_provisional':ok,'errors':[]}
            if ok:v['official_profiles']=[{'profile':x,'passed':True} for x in ('generic','native','sanitized')]
            write(base/'results/validation'/tid/'result.json',v)
            if ok:
                xs=rows(speed)
                m={'measurement_valid':True,'speedup':speed,'rows':xs,'session_summaries':summaries(xs),'errors':[]}
                write(base/'results/measurement'/tid/'result.json',m)
                identity=rows(1.0)
                write(base/'results/baseline-timing'/(name+'__'+size)/'result.json',
                      {'valid':True,'identity_rows':identity,'identity_sessions':summaries(identity,True)})
            data.append({'id':tid,'official_passed':ok,'measurement_eligible':ok,'measurement_valid':ok,
                         'generation_status':g['status'],'multiinput_status':v['multiinput_status'],'speedup':speed if ok else None,
                         'validation_status':v['status'],'generation_error':g.get('error',''),'validation_errors':[],'measurement_errors':[]})
        plan={'requests':len(items),'model':b.MODEL,'conditions':[label],'prompt_language':'en','tasks':items,'instances_list':list(inst.values())}
        write(base/'work/plan.json',plan);plans[label]=plan
        s=b.summarize(data)
        summ={'completion':'DATASET_BATCH_COMPLETE','planned_requests':len(items),'generation_terminal':len(items),
              'validation_terminal':len(items),'requests_pending':0,'measurement_pending':0,
              'generated_texts':s['saved'],'official_gate_passed':s['official_passed'],'measurement_quality_passed':s['measurement_valid'],
              'measurement_eligible_provisional':s['measurement_eligible']}
        write(base/'results/summary.json',summ);stats[label]=s
        if label=='P0':commonids=[x['id'] for x in items]
        else:(control/f'{label}-hardware-block.txt').write_text(block+'\n')
    campaign={'plans_sha256':{x:b.digest(chain/x/'work/plan.json') for x in ('P1','P2')},'same_budget_comparison_ids':commonids}
    write(control/'campaign.json',campaign)
    return chain,p0,stats


class UnitTests(unittest.TestCase):
    def test_duplicate_json(self):
        with self.assertRaises(b.Refuse):b.loads('{"a":1,"a":2}')
    def test_nan(self):
        with self.assertRaises(b.Refuse):b.loads('{"a":NaN}')
    def test_bool_strict(self):
        with self.assertRaises(b.Refuse):b.flag({'x':1},'x')
    def test_positive(self):
        for x in (True,0,-1,math.inf,math.nan,'1'):
            with self.assertRaises(b.Refuse):b.positive(x,'x')
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            for p in ('/root/file','../file','a/../../file','a\\file'):
                with self.assertRaises(b.Refuse):b.relfile(Path(d),p)
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'a').write_text('x');(r/'b').symlink_to(r/'a')
            with self.assertRaises(b.Refuse):b.digest(r/'b')
    def test_timing(self):
        xs=rows();s,ok=b.audit_timing(xs,summaries(xs));self.assertTrue(ok);self.assertAlmostEqual(s,1.02)
    def test_timing_duplicate(self):
        xs=rows();xs[-1]=copy.deepcopy(xs[0])
        with self.assertRaises(b.Refuse):b.audit_timing(xs,summaries(xs))
    def test_timing_ratio_tamper(self):
        xs=rows();xs[0]['speedup']=2
        with self.assertRaises(b.Refuse):b.audit_timing(xs,summaries(xs))
    def test_timing_quality_tamper(self):
        xs=rows();summ=summaries(xs);summ[0]['warnings']=['fake']
        with self.assertRaises(b.Refuse):b.audit_timing(xs,summ)
    def test_prompt_only_cpu_changes(self):
        a={'prompt':'hi\n'+b.P0_LINE,'options':{'seed':1}};c=copy.deepcopy(a);c['prompt']='hi\nCPU'
        b.verify_prompt_pair(a,c,'CPU');c['options']['seed']=2
        with self.assertRaises(b.Refuse):b.verify_prompt_pair(a,c,'CPU')
    def test_matched_no_survivor_count_as_all(self):
        a={i:{'official_passed':i!=2,'measurement_valid':i!=2,'speedup':1.0 if i!=2 else None} for i in range(3)}
        z={i:{'official_passed':True,'measurement_valid':True,'speedup':2.0} for i in range(3)}
        p=b.paired(a,z,set(a));self.assertEqual(p['paired_requests'],3);self.assertEqual(p['both_measurement_valid'],2)
        self.assertEqual(p['contingency']['official_01'],1);self.assertEqual(p['conditional_geomean_right_over_left'],2)
    def test_equal_counts_different_ids(self):
        a={i:{'official_passed':i!=0,'measurement_valid':i!=0,'speedup':1.0 if i!=0 else None} for i in range(3)}
        c={i:{'official_passed':i!=1,'measurement_valid':i!=1,'speedup':1.0 if i!=1 else None} for i in range(3)}
        p=b.paired(a,c,set(a));self.assertEqual(p['contingency']['official_01'],1);self.assertEqual(p['contingency']['official_10'],1)
    def test_wrong_id(self):
        with self.assertRaises(b.Refuse):b.key({'id':'../../bad'})
    def test_object_code_not_used(self):
        # The exporter only reads text/JSON, never imports or executes generated code.
        text=Path(b.__file__).read_text();self.assertNotIn('importlib',text);self.assertNotIn('exec(',text)
    def test_archive_list_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'x').write_text('x');(root/'link').symlink_to(root/'x')
            with self.assertRaises(b.Refuse):b.list_regular_files(root)

class IntegrationTests(unittest.TestCase):
    def test_full_526_export(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);chain,p0,stats=fixture(root)
            before={str(p):b.digest(p) for p in root.rglob('*') if p.is_file()}
            with contextlib.redirect_stdout(io.StringIO()):report=b.build_report(chain,p0,root/'export',verify_p0_hash=False)
            self.assertEqual(report['source_counts'],{'P0':166,'P1':180,'P2':180})
            self.assertEqual(report['comparisons']['P1_vs_P0_common']['ALL']['paired_requests'],166)
            self.assertEqual(report['comparisons']['P2_vs_P1_all']['ALL']['paired_requests'],180)
            self.assertEqual(report['statistics']['all_available']['P2']['ALL']['saved'],179)
            for p,h in before.items():self.assertEqual(b.digest(Path(p)),h)
            with tarfile.open(root/'export/analysis-bundle.tgz') as tf:
                names=tf.getnames();self.assertIn('analysis/paired-results.csv',names);self.assertIn('analysis/SHA256SUMS',names)
            self.assertEqual(len(list((root/'export/analysis').glob('*.csv'))),2)
    def test_candidate_tamper_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);chain,p0,_=fixture(root,4,2)
            cand=next((p0/'results/generation').rglob('candidate.c'));cand.write_text('void bad(){}')
            with self.assertRaises(b.Refuse):b.read_condition('P0',p0,2,b.Reader())
    def test_summary_tamper_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);chain,p0,_=fixture(root,4,2);path=p0/'results/summary.json'
            v=b.read_json(path);v['generated_texts']=0;write(path,v)
            with self.assertRaises(b.Refuse):b.read_condition('P0',p0,2,b.Reader())
    def test_nonterminal_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,p0,_=fixture(root,4,2);path=p0/'results/summary.json'
            v=b.read_json(path);v['completion']='DATASET_BATCH_PAUSED';write(path,v)
            with self.assertRaises(b.Refuse):b.read_condition('P0',p0,2,b.Reader())
    def test_source_hash_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,p0,_=fixture(root,4,2)
            p=next((p0/'work/inputs').rglob('kernel.c'));p.write_text('bad')
            with self.assertRaises(b.Refuse):b.read_condition('P0',p0,2,b.Reader())
    def test_archive_tar_shape(self):
        # Real tar/pigz fallback command with two -C roots and NUL file list.
        import subprocess,shutil
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);base=r/'root';out=r/'out';base.mkdir();out.mkdir()
            (base/'job').mkdir();(base/'job/a.txt').write_text('raw')
            (out/'backup-index').mkdir();(out/'analysis').mkdir();(out/'analysis/report.txt').write_text('report')
            p=out/'backup-index/file-list.nul';p.write_bytes(b'job/a.txt\0')
            target=out/'full.tgz'
            cmd=['tar','--format=pax','-z','-cf',str(target),'-C',str(base),'--null','--verbatim-files-from','-T',str(p),'-C',str(out),'backup-index','analysis']
            subprocess.run(cmd,check=True,stdin=subprocess.DEVNULL,capture_output=True)
            with tarfile.open(target) as tf:
                self.assertEqual(tf.extractfile('job/a.txt').read(),b'raw');self.assertEqual(tf.extractfile('analysis/report.txt').read(),b'report')

if __name__=='__main__':unittest.main(verbosity=2)
