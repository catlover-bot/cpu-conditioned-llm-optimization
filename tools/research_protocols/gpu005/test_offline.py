"""Publication checks only: no historical runtime modules are executed."""
import ast
import hashlib
import json
import subprocess
import sys
import tarfile
import unittest
from pathlib import Path
from .analyze import DEFAULT_ROOT,candidate_integrity,read_json,rows,summarize

REPO=Path(__file__).resolve().parents[3]
PROTOCOLS=REPO/"tools/research_protocols"

def literal_assignments(path):
    out={}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node,ast.Assign):
            try:value=ast.literal_eval(node.value)
            except (ValueError,TypeError):continue
            for target in node.targets:
                if isinstance(target,ast.Name):out[target.id]=value
    return out

class OfflinePublicationTests(unittest.TestCase):
    def test_primary_is_one_90_slot_trial_not_completed_270_plan(self):
        result=summarize()
        self.assertEqual(result["gpu004"]["candidate_slots"],90)
        self.assertEqual(result["gpu004"]["trials"],[1])
        self.assertEqual(result["gpu004"]["generation_status_counts"],{"saved":85,"invalid_generation":5})
        self.assertFalse(result["gpu004"]["historical_prior_270_plan_complete"])
        self.assertEqual(result["gpu004"]["csv_rows"],175)
    def test_gpu005_uses_same_sources_and_zero_new_generation(self):
        result=summarize()
        for profile,summary in result["gpu005"].items():
            self.assertEqual(summary["source_slots"],90)
            self.assertEqual(summary["target_candidate_slots"],85)
            self.assertEqual(summary["unique_measured_ids"],85)
            self.assertEqual(summary["new_generation_calls"],0)
            self.assertEqual(summary["coverage_rows"],90)
            self.assertEqual(summary["result_rows"],340)
            self.assertFalse(summary["formal_equivalence_proven"])
            self.assertFalse(summary["selection_used_confirmation"])
    def test_all_published_candidate_bytes_and_blocks_match_primary_evidence(self):
        source={r["id"]:r for r in read_json(DEFAULT_ROOT/"gpu004/outcomes.json")}
        candidates=candidate_integrity()
        self.assertEqual(len(candidates),85)
        for item in candidates:
            self.assertEqual(item["block"],source[item["id"]]["block"])
            self.assertEqual(item["source_sha256"],source[item["id"]]["source_sha256"])
    def test_control_validity_matches_observed_summary_without_remeasurement(self):
        result=summarize()["gpu005"]
        self.assertEqual(result["a40"]["control_cells"],176)
        self.assertEqual(result["a40"]["valid_control_cells"],176)
        self.assertEqual(result["l4"]["control_cells"],176)
        self.assertEqual(result["l4"]["valid_control_cells"],174)
        for profile in result:
            self.assertEqual(result[profile]["valid_control_cells"],result[profile]["declared_valid_control_cells"])
    def test_all_public_dependency_and_asset_pins_match_actual_callsite_targets(self):
        edges=[("gpu004/pilot.py","A_SHA","gpu004/assets.py"),
               ("gpu004/numeric_core.py","PILOT_SHA","gpu004/pilot.py"),
               ("gpu004/multimodel.py","CORE_SHA","gpu004/numeric_core.py"),
               ("gpu004/batch_budget.py","BASE_SHA","gpu004/multimodel.py"),
               ("gpu004/sanitizer_recovery.py","BASE_SHA","gpu004/multimodel.py"),
               ("gpu004/sanitizer_recovery.py","FIX_OLD_RUNNER_SHA","gpu004/batch_budget.py"),
               ("gpu005/portability.py","CORE_SHA","gpu004/numeric_core.py"),
               ("gpu005/posix_recovery.py","BASE_SHA","gpu005/portability.py")]
        for owner,key,target in edges:
            with self.subTest(owner=owner,key=key):
                self.assertEqual(literal_assignments(PROTOCOLS/owner)[key],hashlib.sha256((PROTOCOLS/target).read_bytes()).hexdigest())
        source=PROTOCOLS/"gpu004/data/source-bundle.json"
        for owner in ("gpu004/multimodel.py","gpu005/portability.py"):
            self.assertEqual(literal_assignments(PROTOCOLS/owner)["SOURCE_SHA"],hashlib.sha256(source.read_bytes()).hexdigest())
        registry=PROTOCOLS/"gpu004/data/registry.json"
        self.assertEqual(literal_assignments(PROTOCOLS/"gpu004/multimodel.py")["REGISTRY_SHA"],hashlib.sha256(registry.read_bytes()).hexdigest())
    def test_original_numeric_symbols_are_verbatim_and_strict_flags_retained(self):
        provenance=read_json(DEFAULT_ROOT/"gpu005/publication-provenance.json")
        self.assertEqual(len(provenance["preserved_numerical_symbols"]),27)
        for item in provenance["preserved_numerical_symbols"]:
            group="gpu005" if item["module"]=="portability" else "gpu004"
            path=PROTOCOLS/group/(item["module"]+".py");text=path.read_text();lines=text.splitlines()
            node=next(n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==item["symbol"])
            raw="\n".join(lines[node.lineno-1:node.end_lineno]).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item["original_and_public_source_sha256"])
        options=literal_assignments(PROTOCOLS/"gpu004/pilot.py")["NVRTC_OPTIONS"]
        for flag in ("--fmad=false","--ftz=false","--prec-div=true","--prec-sqrt=true"):
            self.assertIn(flag,options)
    def test_public_primary_support_bundle_and_third_party_license(self):
        path=PROTOCOLS/"gpu004/data/primary-summary.tar.gz"
        receipt=literal_assignments(PROTOCOLS/"gpu005/portability.py")["PRIMARY_RECEIPT"]
        self.assertEqual(path.stat().st_size,receipt["bytes"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),receipt["sha256"])
        with tarfile.open(path,"r:gz") as tf:
            values={}
            for member in tf:
                self.assertTrue(member.isfile());self.assertNotIn("..",Path(member.name).parts)
                self.assertNotIn(member.name,values);values[member.name]=tf.extractfile(member).read()
        manifest=values.pop("CHECKPOINT_SHA256.json")
        self.assertEqual(hashlib.sha256(manifest).hexdigest(),receipt["manifest_sha256"])
        self.assertEqual(json.loads(manifest),{n:hashlib.sha256(b).hexdigest() for n,b in values.items()})
        self.assertEqual(len(values),receipt["files"])
        self.assertIn("University of Delaware",(DEFAULT_ROOT/"gpu004/licenses/PolyBench-ACC-LICENSE").read_text())
        self.assertIn("OHIO STATE UNIVERSITY",(DEFAULT_ROOT/"gpu004/licenses/PolyBench-ACC-LICENSE").read_text())
    def test_real_offline_cli_reads_only_published_data(self):
        cp=subprocess.run([sys.executable,"-B","-m","tools.research_protocols.gpu005.analyze"],
                          cwd=REPO,capture_output=True,text=True,timeout=30)
        self.assertEqual(cp.returncode,0,cp.stderr)
        result=json.loads(cp.stdout)
        self.assertEqual(result["gpu004"]["candidate_slots"],90)
        self.assertEqual(result["gpu005"]["l4"]["new_generation_calls"],0)

if __name__=="__main__":
    unittest.main()
