import collections
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import goal0080_collect_revalidation as m


def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(x if isinstance(x,bytes) else json.dumps(x).encode())


def fixture(root):
    job=root/'job';r=job/'results';kit=root/'kit';impl=kit/'goal0079_revalidate_all30_v1_1.py'
    write(impl,b'# synthetic fixture: never run\n');validator_sha=m.sha(impl)
    write(job/'implementation.path',str(kit).encode());write(job/'run.log',b'synthetic fixture\n')
    combos=[(t,s,f) for t in sorted(m.TASKS) for s in ('MINI','SMALL','MEDIUM') for f in ('C','IR')]
    originals={}
    for t,s,f in combos:
        b=f'original:{t}:{s}:{f}'.encode();originals[(t,s,f)]=m.hbytes(b)
        write(r/f'extracted/originals/{t}/{s}/kernel.{m.FORMS[f]}',b)
    for t in sorted(m.TASKS):
        for s in ('MINI','SMALL','MEDIUM'):
            for ci in (0,1):
                base=r/f'baselines/{t}/{s}/case{ci}'
                for stem in ('ref-run','base-run'):
                    write(base/(stem+'.stdout'),f'oracle {t}/{s}/{ci}'.encode())
                    write(base/(stem+'.command.json'),{'state':'ok'})
                write(base/'harness.c',b'/* trusted fixture */\n')
    inv=[];oldrows=[];oldfiles={};idx=0;newresults=[]
    for c in ('P0','P1','P2'):
        for t,s,f in (combos[14:] if c=='P0' else combos):
            tid=f'{t}__{s}__{f}__{c}__s0'
            saved=not(c=='P2' and t=='trmm' and s=='MINI' and f=='C')
            cand=f'candidate:{tid}'.encode()
            o={'condition':c,'kernel':t,'size':s,'form':f,'id':tid,'source_sha256':originals[(t,s,f)],
               'candidate_sha256':m.hbytes(cand) if saved else '', 'generation_status':'saved' if saved else 'invalid_generation',
               'official_passed':str(saved and idx<373),'multiinput_status':'not_implemented_for_task',
               'measurement_valid':str(saved and idx<371),'speedup':'1.25' if saved and idx<371 else '',
               'validation_status':'checked','validation_errors':'[]'}
            oldrows.append(o)
            if not saved:continue
            src=r/f'extracted/candidates/{c}/{tid}/candidate.{m.FORMS[f]}';write(src,cand)
            obj=None;objsha=None
            if idx<371:
                obj=r/f'extracted/candidates/{c}/{tid}/old-native.o';write(obj,f'object:{tid}'.encode());objsha=m.sha(obj)
                mp=m.ROOTS[c]+f'/results/measurement/{tid}/result.json'
                oldfiles[mp]=json.dumps({'id':tid,'measurement_valid':True,'speedup':1.25,'candidate_object_sha256':objsha}).encode()
            invrow={'id':tid,'condition':c,'task':t,'size':s,'form':f,'source':str(src),
                    'source_sha256':m.hbytes(cand),'old_native_object':str(obj) if obj else None,
                    'reference_c_sha256':originals[(t,s,'C')],'reference_ir_sha256':originals[(t,s,'IR')]}
            inv.append(invrow)
            passes=idx%7<5
            n={k:invrow[k] for k in ('id','condition','task','size','form','source_sha256','old_native_object','reference_c_sha256','reference_ir_sha256')}
            n.update({'status':'checked','passed':passes,'errors':[],'profiles':{},'cases':[]})
            for label in ('generic','native','sanitized'):
                freshbytes=(obj.read_bytes() if obj and label=='native' else f'fresh {label} {tid}'.encode())
                write(r/f'results/{c}/{tid}/{label}-compile-result.o',freshbytes)
                n['profiles'][label]={'compile_state':'ok','object_sha256':m.hbytes(freshbytes),'passed':True}
            if obj:n['old_native_sha256']=objsha;n['fresh_native_matches_old']=True
            for ci in (0,1):
                q={'case':ci,'profiles':{}}
                oracle=f'oracle {t}/{s}/{ci}'.encode()
                for label in m.PROFILES:
                    output=oracle if passes or ci!=0 or label!='generic' else b'wrong'
                    stem=r/f'results/{c}/{tid}/case{ci}-{label}-run'
                    write(stem.with_suffix('.stdout'),output)
                    write(stem.with_suffix('.stderr'),b'')
                    write(stem.with_suffix('.command.json'),{'state':'ok','returncode':0})
                    q['profiles'][label]={'passed':output==oracle,'state':'ok','stdout_sha256':m.hbytes(output),
                        'oracle_sha256':m.hbytes(oracle),'bytes':len(output)}
                n['cases'].append(q)
            write(r/f'results/{c}/{tid}/result.json',n);newresults.append(n);idx+=1
    summary={'completion':'ALL30_REVALIDATION_COMPLETE','revision':'all30-custom-fullstate-revalidation-v1.1',
             'evidence_sha256':m.EVIDENCE_SHA,'clang':'Ubuntu clang version 18.1.3 (fixture)',
             'saved_candidates':525,'passed':sum(n['passed'] for n in newresults),
             'failed':sum(not n['passed'] for n in newresults),'validator_errors':0,
             'reference_kernel_size_pairs':90,'reference_test_cases':180,'test_cases_per_kernel_source_size':2,
             'model_calls':0,'performance_measurements':0,'old_labels_modified':False,'formal_equivalence_proven':False,
             'by_condition':{},'by_form':{}}
    for field,label,keys in (('condition','by_condition',('P0','P1','P2')),('form','by_form',('C','IR'))):
        for key in keys:
            rr=[n for n in newresults if n[field]==key];summary[label][key]={'saved':len(rr),'passed':sum(n['passed'] for n in rr)}
    write(r/'summary.json',summary);write(r/'candidate-inventory.json',inv)
    write(r/'progress.json',{'completion':'ALL30_REVALIDATION_COMPLETE','candidates_completed':525,'baselines_completed':90,'script_sha256':validator_sha})
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=list(oldrows[0]));w.writeheader();w.writerows(oldrows)
    oldfiles['analysis/candidate-results.csv']=buf.getvalue().encode()
    oldfiles['analysis/SHA256SUMS']=''.join(m.hbytes(b)+'  '+n[len('analysis/'):]+'\n' for n,b in sorted(oldfiles.items())).encode()
    arc=root/'old.tgz'
    with tarfile.open(arc,'w:gz') as tf:
        for name,b in oldfiles.items():
            ti=tarfile.TarInfo(name);ti.size=len(b);tf.addfile(ti,io.BytesIO(b))
    return job,arc,validator_sha


class Units(unittest.TestCase):
    def test_bool_strict(self):
        for x in (0,1,'true',None):
            with self.assertRaises(m.AuditError):m.boolval(x)
    def test_duplicate_json(self):
        with self.assertRaises(m.AuditError):m.jloads('{"x":1,"x":2}')
    def test_nonfinite(self):
        with self.assertRaises(m.AuditError):m.jloads('{"x":NaN}')
    def test_positive(self):
        for x in (False,0,-1,float('nan'),float('inf')):
            with self.assertRaises(m.AuditError):m.positive(x)
    def test_path(self):
        for p in ('/root/a','../a','a/../../b','a\\b','a\nb','a//b'):
            with self.assertRaises(m.AuditError):m.safe_rel(p)
    def test_id(self):
        self.assertEqual(m.task_id('heat-3d__MEDIUM__IR__P1__s0'),('heat-3d','MEDIUM','IR','P1'))
        with self.assertRaises(m.AuditError):m.task_id('unknown__MEDIUM__IR__P1__s0')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);write(p/'source',b'x');(p/'alias').symlink_to(p/'source')
            with self.assertRaises(m.AuditError):m.local_file(p,'alias')
    def test_csvboolean(self):
        with self.assertRaises(m.AuditError):m.csvbool('')
    def test_gm(self):self.assertAlmostEqual(m.gm([2,.5]),1.)

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        cls.job,cls.arc,cls.valsha=fixture(cls.root)
        cls.old,cls.data=m.old_archive(cls.arc,m.sha(cls.arc))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def inspect(self):
        with patch.object(m,'VALIDATOR_SHA',self.valsha):return m.inspect_new(self.job)
    def test_full_525_recompute(self):
        s,n=self.inspect();self.assertEqual(len(n),525);self.assertEqual(sum(r['passed'] for r in n.values()),s['passed'])
    def test_full_526_crosswalk(self):
        s,n=self.inspect();rows,z=m.join_records(self.old,n,self.data)
        self.assertEqual(len(rows),526);self.assertEqual(sum(r['new_passed'] is None for r in rows),1)
        self.assertIn('old_not_pass__new_pass',z['overall_transitions'])
        self.assertIn('old_pass__new_not_pass',z['overall_transitions'])
        self.assertEqual(z['pairs'][0]['matched_requests'],166)
        self.assertEqual(z['pairs'][-3]['matched_requests'],180)
    def test_summary_tamper(self):
        p=self.job/'results/summary.json';b=p.read_bytes();x=m.jloads(b);x['passed']+=1;write(p,x)
        try:
            with self.assertRaises(m.AuditError):self.inspect()
        finally:p.write_bytes(b)
    def test_stdout_tamper(self):
        p=next((self.job/'results/results').rglob('*-run.stdout'));b=p.read_bytes();p.write_bytes(b+b'x')
        try:
            with self.assertRaises(m.AuditError):self.inspect()
        finally:p.write_bytes(b)
    def test_candidate_tamper(self):
        p=next((self.job/'results/extracted/candidates').rglob('candidate.c'));b=p.read_bytes();p.write_bytes(b+b'x')
        try:
            with self.assertRaises(m.AuditError):self.inspect()
        finally:p.write_bytes(b)
    def test_fresh_object_tamper(self):
        p=next((self.job/'results/results').rglob('generic-compile-result.o'));b=p.read_bytes();p.write_bytes(b+b'x')
        try:
            with self.assertRaises(m.AuditError):self.inspect()
        finally:p.write_bytes(b)
    def test_failure_blocks(self):
        p=self.job/'results/failure.json';write(p,{})
        try:
            with self.assertRaises(m.AuditError):self.inspect()
        finally:p.unlink()
    def test_old_object_mismatch(self):
        s,n=self.inspect();n=copy.deepcopy(n)
        tid=next(k for k,v in n.items() if v['_old_native_actual_sha256'])
        n[tid]['_old_native_actual_sha256']='0'*64
        with self.assertRaises(m.AuditError):m.join_records(self.old,n,self.data)
    def test_sources_not_recompiled(self):
        s,n=self.inspect()
        self.assertFalse(any('subprocess' in l for l in Path(m.__file__).read_text().splitlines()))
    def test_export_original_unchanged(self):
        before={p.relative_to(self.job).as_posix():m.sha(p) for p in self.job.rglob('*') if p.is_file()}
        original=m.old_archive
        with patch.object(m,'VALIDATOR_SHA',self.valsha),patch.object(m,'old_archive',lambda p:original(p,m.sha(p))):
            with __import__('contextlib').redirect_stdout(io.StringIO()):m.export(self.job,self.arc,self.root/'export')
        after={p.relative_to(self.job).as_posix():m.sha(p) for p in self.job.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        with tarfile.open(self.root/'export/revalidation-results.tgz') as t:
            names=t.getnames();self.assertIn('revalidation-results/candidate-crosswalk.jsonl',names)
            self.assertIn('revalidation-results/SHA256SUMS',names)
        with self.assertRaises(m.AuditError):m.export(self.job,self.arc,self.root/'export')

if __name__=='__main__':unittest.main(verbosity=2)
