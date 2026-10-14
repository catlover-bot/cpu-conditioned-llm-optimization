import unittest, tempfile, pathlib, hashlib, json, importlib.util, math
import goal0081_ir_and_regression as m

class Units(unittest.TestCase):
 def test_duplicate(self):
  with self.assertRaises(m.Blocked): m.parse_json('{"a":1,"a":2}')
 def test_nonfinite(self):
  with self.assertRaises(m.Blocked):m.parse_json('{"a":NaN}')
 def test_path_escape(self):
  with tempfile.TemporaryDirectory() as t:
   for p in ('../z','/etc/passwd','a/../../z'):
    with self.assertRaises(m.Blocked):m.regular(t,p)
 def test_symlink(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);(p/'a').write_text('x');(p/'b').symlink_to(p/'a')
   with self.assertRaises(m.Blocked):m.regular(p,'b')
 def test_atomic_json(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t)/'deep/r.json';m.write(p,{'x':3});self.assertEqual(m.load(p),{'x':3});self.assertEqual(len(list(p.parent.iterdir())),1)
 def test_manifest(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);(p/'a').write_text('abc');(p/'SHA256SUMS').write_text(m.digest(p/'a')+'  a\n');self.assertEqual(len(m.verify_manifest(p)),1)
   (p/'a').write_text('x')
   with self.assertRaises(m.Blocked):m.verify_manifest(p)
 def test_dedup_manifest(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);l='0'*64+'  a\n';(p/'SHA256SUMS').write_text(l+l)
   with self.assertRaises(m.Blocked):m.manifest(p)
 def test_expected_hashes(self):self.assertEqual(len(m.VALIDATOR_SHA),64);self.assertEqual(len(m.CROSSWALK_SHA),64)
 def test_mvt_counterexample(self):
  x=1.0;a=2.0**53;b=-a
  self.assertEqual((x+a)+b,0.0);self.assertEqual(x+(0.0+a+b),1.0)
 def test_verifier_result_preserved(self):
  class Box:
   def call(self,argv,inputs,stem,timeout):
    self.argv=argv;pathlib.Path(stem).with_suffix('.stderr').write_text('Instruction does not dominate all uses!')
    return {'state':'exit_nonzero','returncode':1},b'',{}
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'a.ll';src.write_text('bad');box=Box();x=m.verify_ir(box,'/usr/bin/opt-18',src,p/'verify')
   self.assertFalse(x['passed']);self.assertIn('-passes=verify',box.argv);self.assertEqual(src.read_text(),'bad')
 def test_verifier_timeout_blocks(self):
  class Box:
   def call(self,argv,inputs,stem,timeout):
    pathlib.Path(stem).with_suffix('.stderr').write_text('');return {'state':'timeout','returncode':None},b'',{}
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'a.ll';src.write_text('x')
   with self.assertRaises(m.Blocked):m.verify_ir(Box(),'opt',src,p/'verify')
 def test_verifier_crash_blocks(self):
  class Box:
   def call(self,argv,inputs,stem,timeout):
    pathlib.Path(stem).with_suffix('.stderr').write_text('');return {'state':'exit_nonzero','returncode':-11},b'',{}
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'a.ll';src.write_text('x')
   with self.assertRaises(m.Blocked):m.verify_ir(Box(),'opt',src,p/'verify')
 def test_explicit_broken_module_abort(self):
  class Box:
   def call(self,argv,inputs,stem,timeout):
    pathlib.Path(stem).with_suffix('.stderr').write_text('Instruction does not dominate all uses!\nLLVM ERROR: Broken module found')
    return {'state':'exit_nonzero','returncode':-6},b'',{}
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'a.ll';src.write_text('x')
   self.assertFalse(m.verify_ir(Box(),'opt',src,p/'verify')['passed'])
 def test_missing_opt_blocks(self):
  from unittest.mock import patch
  with patch.object(m.shutil,'which',return_value=None):
   with self.assertRaises(m.Blocked):m.find_opt()
 def test_signature_preserves_per_request_denominator(self):
  self.assertEqual(set(m.ROOTS),{'P0','P1','P2'})
 def test_original_mismatch_blocks(self):
  from unittest.mock import patch
  row={'condition':'P0','kernel':'k','size':'MINI'}
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);pkg=p/'job/work';(pkg/'inputs/k/MINI').mkdir(parents=True);(pkg/'utilities').mkdir()
   for name in ('inputs/k/MINI/driver.c','inputs/k/MINI/kernel.c','utilities/polybench.c','utilities/polybench.h'):(pkg/name).write_text('a')
   (pkg/'SHA256SUMS').write_text(''.join(m.digest(pkg/n)+'  '+n+'\n' for n in ('inputs/k/MINI/driver.c','inputs/k/MINI/kernel.c','utilities/polybench.c','utilities/polybench.h')))
   ref=p/'ref.c';ref.write_text('b')
   with patch.dict(m.ROOTS,{'P0':p/'job'}),patch.object(m,'source',return_value=ref):
    with self.assertRaises(m.Blocked):m.official_inputs(row,None,p/'out')

if __name__=='__main__':unittest.main(verbosity=2)
