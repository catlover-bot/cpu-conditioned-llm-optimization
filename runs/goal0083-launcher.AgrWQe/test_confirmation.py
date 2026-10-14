#!/usr/bin/env python3
from pathlib import Path
import collections, hashlib, importlib.util, json, math, os, random, shutil, subprocess, sys, tempfile, unittest
import confirmation as C

class UnitTests(unittest.TestCase):
 def test_complete_payload(self):
  p=json.loads((Path(__file__).parent/'plan.json').read_text());self.assertEqual(len(p['instances']),90);self.assertEqual(sum(len(x['candidates']) for x in p['instances']),351)
 def test_exact_ledger(self):
  p=json.loads((Path(__file__).parent/'plan.json').read_text());self.assertEqual(collections.Counter(x['condition'] for x in p['requests']),{'P0':166,'P1':180,'P2':180})
 def test_positive_reject(self):
  for x in (0,-1,True,math.nan,math.inf):
   with self.assertRaises(C.Blocked):C.positive(x)
 def test_geomean(self): self.assertAlmostEqual(C.gmean([2,8]),4)
 def test_timing_parser(self):self.assertEqual(C.parse_time(b'CPUCOND83_BATCH 8 200\n',8),200)
 def test_bad_timing(self):
  for raw in (b'CPUCOND83_BATCH 9 2\n',b'CPUCOND83_BATCH 8 0\n',b'CPUCOND83_BATCH 8 2\nextra',b''):
   with self.assertRaises(C.Blocked):C.parse_time(raw,8)
 def test_balanced_positions(self):
  for n in range(2,10):
   keys=[str(i) for i in range(n)];orders=C.choose_schedule(keys,7)
   self.assertGreaterEqual(len(orders),8)
   for key in keys:
    counts=collections.Counter(o.index(key) for o in orders);self.assertEqual(len(set(counts.values())),1)
 def test_reverse_order_balance(self):
  keys=list('abcde');orders=C.choose_schedule(keys,8)
  for a in keys:
   for b in keys:
    if a!=b:self.assertEqual(sum(o.index(a)<o.index(b) for o in orders),len(orders)//2)
 def test_schedule_deterministic(self):self.assertEqual(C.choose_schedule(list('abcd'),2),C.choose_schedule(list('dcba'),2))
 def test_schedule_duplicates(self):
  with self.assertRaises(C.Blocked):C.choose_schedule(['x','x'],1)
 def test_source_not_modified(self):
  p=Path(__file__).parent/'inputs/gemm/MINI/driver.c';raw=p.read_bytes();C.timing_driver(raw.decode(),'kernel_gemm');self.assertEqual(raw,p.read_bytes())
 def test_timer_not_initialization(self):
  s=C.timing_driver((Path(__file__).parent/'inputs/gemm/MINI/driver.c').read_text(),'kernel_gemm')
  interval=s.split('unsigned long long start=cpucond83_clock();')[1].split('unsigned long long end=cpucond83_clock();')[0]
  self.assertIn('kernel_gemm',interval);self.assertNotIn('init_array',interval);self.assertNotIn('print_array',interval)
 def test_dual_baseline(self):
  for n in ('reference_C','reference_IR'):self.assertIn(n,Path(C.__file__).read_text())
 def rounds(self,ratio=2):
  return [{'round':r,'complete_block_target':8,'rows':[{'times_ns':{'a':200,'b':200/ratio,'identity-control':200}} for _ in range(8)]} for r in range(2)]
 def test_paired_ratio_direction(self):self.assertEqual(C.quality_for_pair(self.rounds(),'a','b')['ratio'],2)
 def test_identity_actual_observations(self):self.assertTrue(C.quality_for_pair(self.rounds(),'a','identity-control',True)['valid'])
 def test_same_binary_ratio(self):
  q=C.quality_for_pair(self.rounds(),'a','a');self.assertEqual(q['ratio'],1);self.assertTrue(q['equal_executable'])
 def test_missing_not_success(self):
  rs=self.rounds();del rs[0]['rows'][0]['times_ns']['b'];self.assertFalse(C.quality_for_pair(rs,'a','b')['valid'])
 def test_round_shift(self):
  rs=self.rounds()
  for r in rs[1]['rows']:r['times_ns']['b']=80
  self.assertIn('between_round_ratio_change',C.quality_for_pair(rs,'a','b')['warnings'])
 def test_identity_shift(self):self.assertFalse(C.quality_for_pair(self.rounds(),'a','b',True)['valid'])
 def test_variability(self):self.assertGreater(C.variability([1,1,3,3,5,5]),.1)
 def test_equal_binary_does_not_create_independent_draws(self):
  p={'id':'x','aliases':{'reference_C':'a','reference_IR':'b','some__MINI__C__P1__s0':'b'},'classes':{'a':{},'b':{}},'variants':{
   'reference_C':{'label':'reference_C','form':'C','is_reference':True,'source_sha256':'s','ready':True,'errors':[],'object_sha256':'o','binary_sha256':'a'},
   'reference_IR':{'label':'reference_IR','form':'IR','is_reference':True,'source_sha256':'s','ready':True,'errors':[],'object_sha256':'o','binary_sha256':'b'},
   'some__MINI__C__P1__s0':{'label':'some__MINI__C__P1__s0','form':'C','is_reference':False,'source_sha256':'s','ready':True,'errors':[],'object_sha256':'o','binary_sha256':'b'}}}
  r=C.summarize_group(p,{'k':1,'classes_excluded':{}},self.rounds())
  self.assertEqual(r['variants']['some__MINI__C__P1__s0']['speedup_vs_original_c'],2)
 def test_no_model_call_in_control(self):
  s=Path(C.__file__).read_text();self.assertNotIn('api/generate',s);self.assertNotIn('model_state()',s)
 def test_unit_prefix(self):
  self.assertIsNotNone(__import__('re').fullmatch(r'cpucond69-[A-Za-z0-9-]+\.service','cpucond69-confirm83-test.service'))
 def test_safe_path(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_text('x')
   with self.assertRaises(Exception):C.safe(Path(d),'../x')
 def test_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';C.put(p,'old')
   with self.assertRaises(FileExistsError):C.put(p,'new')
   self.assertEqual(p.read_text(),'old')

class FlowTests(unittest.TestCase):
 def test_second_round_does_not_repeat_failed_executable(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as td:
   p={'id':'sample','aliases':{'reference_C':'a','reference_IR':'a'},'classes':{'a':{'program':'A'},'b':{'program':'B'}}}
   cal={'k':1,'classes_excluded':{}};calls=[]
   def fake(box,program,stem,k):
    calls.append(program)
    if program=='B':raise C.B.CandidateFailure('synthetic timeout')
    return 100
   with patch.object(C,'run_timed',fake):
    r0=C.measure_round(None,p,cal,Path(td),0)
    C.measure_round(None,p,cal,Path(td),1,r0['classes_failed'])
   self.assertEqual(calls.count('B'),1)
 def test_all_526_denominators_preserved_on_export(self):
  plan=json.loads((Path(__file__).parent/'plan.json').read_text());groups={}
  for g in plan['instances']:
   groups[g['id']]={'variants':{},'paired_condition_comparisons':[]}
   for c in g['candidates']:
    groups[g['id']]['variants'][c['id']]={'is_reference':False,'form':c['form'],'status':'measured','measurement_valid':True,'ir_path_valid':True,'speedup_vs_original_c':1.1,'speedup_vs_unchanged_ir':1.01}
  with tempfile.TemporaryDirectory() as td:
   result=C.export_report(plan,Path(td),groups)
   self.assertEqual(result['candidate_measurement_quality_passed'],351)
   rows=[json.loads(x) for x in (Path(td)/'candidate-results.jsonl').read_text().splitlines()]
   self.assertEqual(len(rows),526)
   self.assertEqual(sum(r['eligible_before_confirmation'] for r in rows),351)
   ps=result['paired_comparisons']
   self.assertEqual(ps['P1_vs_P0/ALL']['paired_request_count'],166)
   self.assertEqual(ps['P2_vs_P1/ALL']['paired_request_count'],180)
 def test_all_351_sources_identical_to_ledger(self):
  root=Path(__file__).parent;plan=json.loads((root/'plan.json').read_text());index={r['id']:r for r in plan['requests']}
  for group in plan['instances']:
   for c in group['candidates']:
    self.assertEqual(C.sha(root/c['source']['path']),index[c['id']]['source_sha256'])
 def test_missing_five_historical_times_still_included(self):
  p=json.loads((Path(__file__).parent/'plan.json').read_text());candidates={c['id'] for g in p['instances'] for c in g['candidates']}
  missing={r['id'] for r in p['requests'] if r['eligible_under_recorded_checks'] and not r['historical_timing_available']}
  self.assertEqual(len(missing),5);self.assertTrue(missing<=candidates)
 def test_frozen_protocol(self):
  p=json.loads((Path(__file__).parent/'protocol.json').read_text())
  self.assertIsNone(p['total_timeout']);self.assertEqual(p['rounds'],C.ROUNDS);self.assertEqual(p['batch_calibration']['target_ns'],C.TARGET_NS);self.assertEqual(p['batch_calibration']['max_K'],C.MAX_K)

class SyntheticIntegration(unittest.TestCase):
 """Only self-authored tiny numerical functions are compiled/executed here.
 No stored generated candidates are run outside the production sandbox.
 """
 def test_timer_modes_reset_and_dedup(self):
  compiler=shutil.which('clang-18') or shutil.which('clang')
  if not compiler:self.skipTest('no clang for synthetic compile')
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);driver='''#include <stdio.h>
#include <stdlib.h>
static void init_array(double *a){*a=3.0;}
static void print_array(double *a){fwrite(a,1,sizeof(*a),stdout);}
void kernel_test(double *a);
int main(int argc,char**argv){double a;init_array(&a);kernel_test(&a);print_array(&a);return 0;}
'''
   for name,source in [('driver.c',C.timing_driver(driver,'kernel_test')),('clock.c',C.CLOCK_SOURCE),('kernel.c','void kernel_test(double*a){*a=*a*2.0;}')]:
    (d/name).write_text(source)
    result=subprocess.run([compiler,'-std=gnu11','-O3','-fno-fast-math','-ffp-contract=off','-fno-lto','-c',str(d/name),'-o',str(d/(name+'.o'))],capture_output=True,timeout=30)
    self.assertEqual(result.returncode,0,result.stderr.decode())
   for name in ('one','two'):
    subprocess.run([compiler,*[str(d/(x+'.o')) for x in ('driver.c','clock.c','kernel.c')],'-no-pie','-lm','-o',str(d/name)],check=True,capture_output=True,timeout=30)
   self.assertEqual(C.sha(d/'one'),C.sha(d/'two'))
   import struct
   for k in (1,8,64):
    raw=subprocess.check_output([str(d/'one'),str(k),'check'],timeout=10)
    self.assertEqual(raw,struct.pack('d',6.0))
    raw=subprocess.check_output([str(d/'one'),str(k)],timeout=10)
    self.assertGreater(C.parse_time(raw,k),0)

if __name__=='__main__':unittest.main(verbosity=2)
