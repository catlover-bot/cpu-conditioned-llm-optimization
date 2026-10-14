"""Pilot operational regressions on the actual pinned cohort; provider/GPU fixtures only."""
from __future__ import annotations
import contextlib, copy, io, json, pathlib, sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import REPO, Blocked, canonical, digest, parse, read, validate_inputs, write_once
from public_fixture_context import validate_inputs
from execution import PILOT_KEY, build_execution, configure_execution
from budget import PILOT_APPROVAL_PHRASE, APPROVAL_PHRASE, approve, make_quote
from controller import Controller
from providers import canonical as native_body_bytes
from test_controller import FixtureProvider, fixture_counts, fixture_evidence, ready

class PilotProvider(FixtureProvider):
    def __init__(self, provider, context):
        super().__init__(provider, context)
        self.mode = "accepted"
    def submit(self, payload, metadata):
        remote = super().submit(payload, metadata)
        if self.provider == "openai" and metadata["gpu006_batch"] == PILOT_KEY and self.mode == "batch_parameter_rejected":
            remote.update(status="failed", request_counts={"total":1,"completed":0,"failed":1},
                          errors={"data":[{"code":"unsupported_parameter","param":"temperature","line":1}]})
        return remote
    def results(self, remote):
        artifacts = super().results(remote)
        if self.provider != "openai" or remote["metadata"]["gpu006_batch"] != PILOT_KEY:
            return artifacts
        rows = [parse(line) for line in artifacts[0][1].splitlines()]
        if self.mode in ("missing", "batch_parameter_rejected"):
            rows=[]
        for row in rows:
            row["id"] = "batch_req_fixture"
            row["response"]["request_id"] = "req_fixture"
            body = row["response"]["body"]
            if self.mode == "parameter_rejected":
                row["response"].update(status_code=400,body={"error":{"type":"invalid_request_error","code":"unsupported_parameter","param":"temperature"}})
            elif self.mode == "other_api_error":
                row["response"].update(status_code=429,body={"error":{"type":"rate_limit_error","code":"rate_limit_exceeded"}})
            elif self.mode == "format_rejected":
                body["output"][0]["content"] = [{"type":"refusal","refusal":"fixture"}]
            elif self.mode == "incomplete":
                body.update(status="incomplete",incomplete_details={"reason":"max_output_tokens"})
            elif self.mode == "echo_mismatch":
                body["temperature"] = 1.0
            elif self.mode == "echo_match":
                body.update(reasoning={"effort":"none"},temperature=0.2,top_p=0.9,max_output_tokens=8192)
        return [("responses.jsonl",b"".join(canonical(row) for row in rows))]

class PilotFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=validate_inputs()
        cls.context=build_execution(cls.original)
    def setUp(self):
        output=contextlib.redirect_stdout(io.StringIO());output.__enter__();self.addCleanup(output.__exit__,None,None,None)
        self.temp=tempfile.TemporaryDirectory(prefix="gpu006-pilot-tests-")
        self.root=pathlib.Path(self.temp.name)/"gpu006-cloud180-v1"
        self.root.mkdir()
        write_once(self.root/"execution-manifest.json",canonical(self.context["execution_manifest"]))
        self.clients={p:PilotProvider(p,self.context) for p in ("openai","anthropic")}
        self.controller=Controller(self.root,self.context,self.clients)
        evidence=fixture_evidence()
        evidence.update(parameters_verified=False, public_parameter_support={"openai":"unverified","anthropic":"documented"},
                        explicitly_unsupported_parameters=[])
        self.quote=make_quote(self.context,fixture_counts(self.context),evidence)
    def tearDown(self):
        self.temp.cleanup()
    def authorize(self, limit="20", phrase=PILOT_APPROVAL_PHRASE):
        ref=approve(self.root,self.quote,limit,phrase)
        self.controller.set_approval(ref)
    def creates(self):
        return [len(c.create_calls) for c in self.clients.values()]
    def pilot(self,mode="accepted"):
        self.clients["openai"].mode=mode
        self.controller.submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[1,0])
        self.controller.watch(1,until_batch=PILOT_KEY)
        return self.controller.pilot_acceptance()

    def test_actual_manifest_is_only_a_partition_and_preserves_exact_bodies(self):
        self.assertEqual(self.context["scope"],self.original["scope"])
        self.assertEqual(self.context["scope_sha256"],self.original["scope_sha256"])
        expected={row["custom_id"]:row for batch in self.original["batches"] for row in batch["requests"]}
        actual=[row for batch in self.context["batches"] for row in batch["requests"]]
        self.assertEqual(len(actual),180)
        self.assertEqual({row["custom_id"]:row for row in actual},expected)
        pilot=self.context["batches"][0]
        first=next(row["id"] for row in self.original["plan"]["requests"] if row["provider"]=="openai")
        self.assertEqual(pilot["ids"],[first])
        original=next(b for b in self.original["batches"] if first in b["ids"])
        self.assertEqual(pilot["payload"],original["payload"].splitlines(keepends=True)[0])
        self.assertEqual(self.context["execution_manifest"]["pilot"]["request_body_sha256"],
                         digest(native_body_bytes(pilot["requests"][0]["body"])))
        remaining=[rid for b in self.context["batches"][1:] if b["provider"]=="openai" for rid in b["ids"]]
        self.assertEqual(len(remaining),89);self.assertNotIn(first,remaining)
        self.assertEqual([len(b["ids"]) for b in self.context["batches"]],[1,29,30,30,30,30,30])
        for row in actual:
            body=row.get("body",row.get("params"))
            self.assertEqual(body.get("max_output_tokens",body.get("max_tokens")),8192)

    def test_no_approval_over_limit_or_old_nonpilot_phrase_have_zero_creates(self):
        with self.assertRaisesRegex(Blocked,"not approved"):
            self.controller.submit_pending(ready(self.context))
        for limit,phrase in (("10",PILOT_APPROVAL_PHRASE),("20",APPROVAL_PHRASE)):
            with self.subTest(limit=limit,phrase=phrase),self.assertRaises(Blocked):
                self.authorize(limit,phrase)
        self.assertEqual(self.creates(),[0,0]);self.assertIsNone(self.controller.state["approval"])

    def test_public_docs_and_counts_never_prove_current_request_acceptance(self):
        self.assertEqual(self.quote["requests"],180)
        self.assertEqual(self.quote["api_compatibility_evidence"]["public_documentation"]["status"],"unverified")
        self.assertEqual(self.quote["api_compatibility_evidence"]["historical_exact_setting_acceptance"]["status"],"not_verified")
        self.assertEqual(self.quote["api_compatibility_evidence"]["current_account_request_acceptance"]["status"],"not_yet_tested")
        self.authorize()
        self.controller.submit_pending(ready(self.context))
        self.assertIsNone(self.controller.pilot_acceptance())
        self.controller.submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[1,0])
        with self.assertRaisesRegex(Blocked,"not confirmed"):
            self.controller.submit_pending(ready(self.context),only_keys={"openai-trial-01-remainder"})

    def test_actual_assessor_proof_hashes_match_manifest_then_all180_once(self):
        self.authorize();proof=self.pilot()
        self.assertEqual(proof["status"],"accepted")
        self.assertTrue(proof["actual_input_verified"])
        self.assertEqual(proof["batch_request_id"],"batch_req_fixture")
        self.assertEqual(proof["provider_request_id"],"req_fixture")
        self.assertEqual(proof["returned_model"],"gpt-5.6-terra")
        for key in ("request_body_sha256","submission_body_sha256"):
            self.assertEqual(proof[key],self.context["execution_manifest"]["pilot"][key])
        self.assertTrue(all(setting["status"]=="unknown" for setting in proof["settings"].values()))
        self.controller.submit_pending(ready(self.context))
        collected=self.controller.watch(1)
        self.assertEqual(self.creates(),[4,3])
        self.assertEqual([row["id"] for row in collected],self.original["scope"]["ids"])
        self.assertEqual(sum(row["id"]==proof["custom_id"] for row in collected),1)
        sent=[row["custom_id"] for payload,_ in self.clients["openai"].create_calls
              for line in payload.splitlines() for row in [parse(line)]]
        self.assertEqual(len(sent),len(set(sent)),90)
        self.assertEqual(sent,[r["id"] for r in self.original["plan"]["requests"] if r["provider"]=="openai"])
        resumed=Controller(self.root,self.context,self.clients)
        resumed.submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[4,3])

    def test_native_acceptance_of_format_failure_continues_without_candidate_salvage(self):
        self.authorize();proof=self.pilot("format_rejected")
        self.assertEqual(proof["status"],"accepted")
        self.assertFalse(proof["candidate_status_used"])
        self.controller.submit_pending(ready(self.context))
        collected=self.controller.watch(1)
        first=next(row for row in collected if row["id"]==proof["custom_id"])
        self.assertEqual(first["generation_status"],"format_rejected")
        self.assertIsNone(first["candidate_text"])
        # Private deployment worker handoff is omitted in this public fixture.
        self.assertEqual(self.creates(),[4,3])

    def test_max_output_incomplete_is_api_accepted_and_not_quality_gate(self):
        self.authorize();proof=self.pilot("incomplete")
        self.assertEqual(proof["status"],"accepted")
        self.controller.submit_pending(ready(self.context))
        collected=self.controller.watch(1)
        self.assertEqual(next(row for row in collected if row["id"]==proof["custom_id"])["generation_status"],"incomplete")
        self.assertEqual(self.creates(),[4,3])

    def test_fixed_parameter_rejection_or_other_api_error_are_distinct_and_stop_rest(self):
        for mode,status in (("parameter_rejected","fixed_parameter_rejected"),("batch_parameter_rejected","fixed_parameter_rejected"),("other_api_error","other_api_error")):
            with self.subTest(mode=mode):
                root=self.root/mode/"gpu006-cloud180-v1"
                clients={p:PilotProvider(p,self.context) for p in ("openai","anthropic")}
                clients["openai"].mode=mode
                controller=Controller(root,self.context,clients)
                controller.set_approval(approve(root,self.quote,"20",PILOT_APPROVAL_PHRASE))
                controller.submit_pending(ready(self.context));controller.watch(1,until_batch=PILOT_KEY)
                proof=controller.pilot_acceptance();self.assertEqual(proof["status"],status)
                with self.assertRaises(Blocked):controller.require_pilot_accepted()
                controller.submit_pending(ready(self.context))
                self.assertEqual([len(c.create_calls) for c in clients.values()],[1,0])
                self.assertEqual(sum(len(b["ids"]) for b in controller.state["batches"].values()
                                     if b["provider"]=="openai" and b["status"]=="PENDING"),89)

    def test_rejected_pilot_resume_creates_revision_proposal_without_new_submission(self):
        self.authorize();self.pilot("parameter_rejected")
        self.assertFalse((self.root/"state/api-revision-proposal.json").exists())
        resumed=Controller(self.root,self.context,self.clients)
        with self.assertRaisesRegex(Blocked,"FIXED_PARAMETER_REJECTED"):resumed.require_pilot_accepted()
        proposal=parse(read(self.root/"state/api-revision-proposal.json"))
        self.assertEqual(proposal["fields_requiring_review"],["temperature"])
        self.assertFalse(proposal["minimal_revision_proposals"][0]["automatic_application"])
        self.assertEqual(self.creates(),[1,0])

    def test_missing_native_result_and_conflicting_returned_setting_remain_unknown(self):
        for mode in ("missing","echo_mismatch"):
            with self.subTest(mode=mode):
                root=self.root/mode/"gpu006-cloud180-v1"
                clients={p:PilotProvider(p,self.context) for p in ("openai","anthropic")}
                clients["openai"].mode=mode
                controller=Controller(root,self.context,clients)
                controller.set_approval(approve(root,self.quote,"20",PILOT_APPROVAL_PHRASE))
                controller.submit_pending(ready(self.context));controller.watch(1,until_batch=PILOT_KEY)
                self.assertEqual(controller.pilot_acceptance()["status"],"unknown")
                with self.assertRaises(Blocked):controller.require_pilot_accepted()
                controller.submit_pending(ready(self.context))
                self.assertEqual([len(c.create_calls) for c in clients.values()],[1,0])

    def test_returned_echoes_are_compared_without_influence_claim(self):
        self.authorize();proof=self.pilot("echo_match")
        self.assertEqual(proof["status"],"accepted")
        self.assertTrue(all(setting["status"]=="match" for setting in proof["settings"].values()))
        self.assertEqual(proof["parameter_influence"],"not assessed")
        self.assertIn("not established",proof["parameter_influence_on_generated_content"])

    def test_unknown_submission_never_retries_and_reconciliation_keeps_pilot_once(self):
        self.authorize();self.clients["openai"].raise_after_accept=True
        with self.assertRaisesRegex(Blocked,"SUBMISSION_UNKNOWN"):self.controller.submit_pending(ready(self.context))
        resumed=Controller(self.root,self.context,self.clients)
        with self.assertRaisesRegex(Blocked,"SUBMISSION_UNKNOWN"):resumed.submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[1,0])
        self.clients["openai"].raise_after_accept=False
        resumed.reconcile(PILOT_KEY,"batch_fixture_1")
        resumed.watch(1,until_batch=PILOT_KEY);resumed.require_pilot_accepted()
        resumed.submit_pending(ready(self.context));self.assertEqual(self.creates(),[4,3])

    def test_interrupted_collection_then_resume_does_not_send_pilot_again(self):
        self.authorize();self.controller.submit_pending(ready(self.context))
        self.clients["openai"].download_fail_once=True
        with self.assertRaises(OSError):self.controller.collect_once()
        resumed=Controller(self.root,self.context,self.clients)
        resumed.submit_pending(ready(self.context));self.assertEqual(self.creates(),[1,0])
        resumed.watch(1,until_batch=PILOT_KEY);resumed.require_pilot_accepted()
        resumed.submit_pending(ready(self.context));collected=resumed.watch(1)
        self.assertEqual(len(collected),180);self.assertEqual(self.creates(),[4,3])

    def test_proof_saved_before_ledger_crash_recovers_without_new_create(self):
        self.authorize();self.pilot()
        original=read(self.root/"state/api-acceptance/openai-pilot.json")
        self.controller.state["pilot_acceptance"]=None
        self.controller.state["batches"][PILOT_KEY]["status"]="SUBMITTED"
        self.controller.save()
        resumed=Controller(self.root,self.context,self.clients)
        resumed.watch(1,until_batch=PILOT_KEY);resumed.require_pilot_accepted()
        self.assertEqual(read(self.root/"state/api-acceptance/openai-pilot.json"),original)
        self.assertEqual(self.creates(),[1,0])

    def test_raw_proof_tamper_and_missing_current_l4_recheck_stop_paid_continuation(self):
        self.authorize()
        stale=ready(self.context);stale.pop("current_environment_verified")
        with self.assertRaisesRegex(Blocked,"current preparation"):self.controller.submit_pending(stale)
        self.assertEqual(self.creates(),[0,0])
        proof=self.pilot()
        artifact=self.root/proof["raw_response_artifacts"][0]["path"]
        artifact.write_bytes(b"modified")
        with self.assertRaisesRegex(Blocked,"raw request evidence changed"):self.controller.submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[1,0])

    def test_duplicate_remote_pilot_cannot_replace_successful_original_batch_id(self):
        self.authorize();self.pilot()
        entry=self.controller.state["batches"][PILOT_KEY]
        original=copy.deepcopy(entry)
        self.clients["openai"].list_batches=lambda:[{"id":"batch_duplicate","metadata":entry["metadata"]}]
        with self.assertRaisesRegex(Blocked,"original ID retained"):
            self.controller.submit_pending(ready(self.context))
        self.assertEqual(self.controller.state["batches"][PILOT_KEY],original)
        self.assertEqual(self.creates(),[1,0])
        entry["status"]="SUBMISSION_UNKNOWN";self.controller.save()
        with self.assertRaisesRegex(Blocked,"cannot be replaced"):
            self.controller.reconcile(PILOT_KEY,"batch_duplicate")
        self.assertEqual(entry["batch_id"],original["batch_id"])

    def test_manifest_change_is_not_covered_by_existing_approval(self):
        self.authorize()
        changed=copy.deepcopy(self.context)
        changed["execution_manifest"]["pilot"]["custom_id"]="g006__openai__gemm__NONE__r01"
        with self.assertRaisesRegex(Blocked,"manifest"):
            Controller(self.root,changed,self.clients).submit_pending(ready(self.context))
        self.assertEqual(self.creates(),[0,0])

class ExecutionMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context=validate_inputs()
    def test_unapproved_unsubmitted_ledger_is_archived_before_seven_batch_adoption(self):
        with tempfile.TemporaryDirectory(prefix="gpu006-migration-test-") as td:
            root=pathlib.Path(td)/"gpu006-cloud180-v1"
            old=Controller(root,self.context,{})
            data=read(old.state_path)
            configured=configure_execution(self.context,root,create=True)
            changed=Controller(root,configured,{})
            self.assertEqual(len(changed.state["batches"]),7)
            self.assertEqual(read(root/"state/ledger-history"/(digest(data)+".json")),data)
            self.assertIsNone(changed.state["approval"])
    def test_already_authorized_legacy_partition_cannot_silently_change(self):
        with tempfile.TemporaryDirectory(prefix="gpu006-migration-test-") as td:
            root=pathlib.Path(td)/"gpu006-cloud180-v1"
            old=Controller(root,self.context,{})
            quote=make_quote(self.context,fixture_counts(self.context),fixture_evidence())
            old.set_approval(approve(root,quote,"20",APPROVAL_PHRASE))
            configured=configure_execution(self.context,root,create=True)
            self.assertNotIn("execution_manifest",configured)
            self.assertEqual(read(root/"state/ledger.json"),read(old.state_path))
            self.assertFalse((root/"execution-manifest.json").exists())

if __name__=="__main__":
    unittest.main(verbosity=2)
