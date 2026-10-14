"""Public data checks use saved bytes only; no compiler, GPU or provider calls."""
import ast,hashlib,unittest
from pathlib import Path
import reanalyze
import numeric_core
import numeric_support
class PublicDataTests(unittest.TestCase):
    def test_actual270_source_hashes_failures_and_aggregate_values(self):
        result=reanalyze.check()
        self.assertEqual((result['planned_slots'],result['saved_candidates'],result['invalid_generation']),(270,255,15))
        self.assertEqual(result['all_l4_quality_valid_candidates'],253)
        self.assertEqual(len(result['within_model_contrasts']),24)
    def test_plaintext_numerical_projection_has_no_embedded_bootstrap(self):
        for module in (numeric_core,numeric_support):
            source=Path(module.__file__).read_text();ast.parse(source)
            self.assertNotIn('PILOT_EMBED',source);self.assertNotIn('A_EMBED',source)
    def test_recorded_reference_shapes_and_pure_expression_definitions(self):
        for task in numeric_core.TASKS:
            self.assertEqual(len(numeric_core.shapes(task)),5)
            source=numeric_core.baseline_source(task)
            self.assertIn('kernel',source)
            replay=numeric_core.cpu_emulator_source(task,numeric_core.small_shapes(task)[0],source)
            self.assertIn('extern "C" void emulate',replay)
    def test_candidate_blocks_match_fixed_protocol(self):
        protocol=reanalyze.data('protocol.json')
        for row in reanalyze.data('candidates.json'):
            self.assertIn(row['block'],protocol['allowed_blocks'][row['task']])
if __name__=='__main__':unittest.main()
