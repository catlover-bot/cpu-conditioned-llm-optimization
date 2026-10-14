"""Offline regressions on the actual immutable 270-request cohort. No CUDA required."""
from __future__ import annotations
import copy, json, pathlib, shutil, sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import Blocked, REPO, PLAN_SHA, canonical, digest, read, validate_inputs, write_once, utc
from public_fixture_context import validate_inputs
from budget import APPROVAL_PHRASE, approve, make_quote, validate_approval
from controller import Controller

def fixture_evidence():
    return {"verified_at": utc(), "parameters_verified": True,
            "sources": [{"url": "https://official.example/test-fixture", "sha256": "0" * 64}],
            "rates": {"openai": {"model": "gpt-5.6-terra", "input_usd_per_mtok": "1", "output_usd_per_mtok": "6"},
                      "anthropic": {"model": "claude-sonnet-5", "input_usd_per_mtok": "1", "output_usd_per_mtok": "5"}}}

def fixture_counts(ctx):
    return {p: {"provider": p, "model": ctx["scope"]["models"][p], "permission": {"fixture_only": True},
                "input_tokens": {r["id"]: 2048 for r in ctx["plan"]["requests"] if r["provider"] == p}, "raw_evidence": []}
            for p in ("openai", "anthropic")}

def ready(ctx):
    return {"ready": True, "plan_sha256": PLAN_SHA, "target_sha256": ctx["scope"]["target_sha256"],
            "candidate_execution_uid": 65534, "checkpoint_archives_verified": True, "current_environment_verified": True, "SIMULATED_GPU": True}

class FixtureProvider:
    def __init__(self, provider, ctx):
        self.provider, self.ctx = provider, ctx
        self.create_calls = []
        self.records = {}
        self.raise_after_accept = False
        self.download_fail_once = False
        self.reorder = True
        self.duplicate = False
        self.missing = False
        self.results_count = 0

    def submit(self, payload, metadata):
        bid = ("batch_fixture_" if self.provider == "openai" else "msgbatch_fixture_") + str(len(self.create_calls) + 1)
        reqs = [json.loads(x) for x in payload.splitlines()] if self.provider == "openai" else json.loads(payload)["requests"]
        remote = {"id": bid, "metadata": metadata, "status": "completed", "processing_status": "ended"}
        self.create_calls.append((payload, metadata))
        self.records[bid] = (remote, reqs)
        if self.raise_after_accept:
            raise OSError("fixture disconnect after provider accepted")
        return remote

    def retrieve(self, bid):
        return self.records[bid][0]

    def verify_batch(self, remote, payload, metadata):
        return remote["metadata"] == metadata

    def results(self, remote):
        self.results_count += 1
        if self.download_fail_once:
            self.download_fail_once = False
            raise OSError("fixture interrupted GET")
        requests = self.records[remote["id"]][1]
        rows = []
        for index, request in enumerate(requests):
            rid = request["custom_id"]
            # Every provider fixture preserves original request ID.
            if self.provider == "openai":
                body = {"id": "resp-" + rid, "status": "completed", "model": "gpt-5.6-terra",
                        "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": '{"block":[32,8]}\nCUDA FIXTURE'}]}],
                        "usage": {"input_tokens": 13, "output_tokens": 17, "total_tokens": 30}}
                row = {"custom_id": rid, "error": None, "response": {"status_code": 200, "body": body}}
            else:
                body = {"id": "msg-" + rid, "type": "message", "model": "claude-sonnet-5", "stop_reason": "end_turn",
                        "content": [{"type": "text", "text": '{"block":[32,8]}\nCUDA FIXTURE'}],
                        "usage": {"input_tokens": 13, "output_tokens": 17}}
                row = {"custom_id": rid, "result": {"type": "succeeded", "message": body}}
            rows.append(row)
        if self.reorder:
            rows.reverse()
        if self.missing:
            rows.pop()
        if self.duplicate:
            rows.append(rows[0])
        return [("responses.jsonl", b"".join(canonical(row) for row in rows))]

class ControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = validate_inputs()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gpu006-controller-test-")
        self.root = pathlib.Path(self.temp.name) / "gpu006-cloud180-v1"
        self.clients = {p: FixtureProvider(p, self.ctx) for p in ("openai", "anthropic")}
        self.controller = Controller(self.root, self.ctx, self.clients)
        self.quote = make_quote(self.ctx, fixture_counts(self.ctx), fixture_evidence())

    def tearDown(self):
        self.temp.cleanup()

    def authorize(self):
        reference = approve(self.root, self.quote, "20", APPROVAL_PHRASE)
        self.controller.set_approval(reference)

    def test_actual_270_and_exact_six_drafts(self):
        self.assertEqual(len(self.ctx["plan"]["requests"]), 270)
        self.assertEqual(len(self.ctx["batches"]), 6)
        self.assertEqual(sum(len(b["ids"]) for b in self.ctx["batches"]), 180)
        for b in self.ctx["batches"]:
            self.assertEqual(len(set(b["ids"])), 30)
            self.assertEqual(digest(b["payload"]), b["body_sha256"])

    def test_unapproved_zero_paid_calls(self):
        with self.assertRaises(Blocked):
            self.controller.submit_pending(ready(self.ctx))
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_ten_dollars_is_only_proposal_and_over_limit_zero_calls(self):
        self.assertGreater(float(self.quote["reserved_usd"]), 10)
        with self.assertRaises(Blocked):
            approve(self.root, self.quote, "10", APPROVAL_PHRASE)
        self.assertIsNone(self.controller.state["approval"])
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_missing_explicit_phrase_and_nonfinite_budget(self):
        for limit, phrase in [("20", "yes"), ("NaN", APPROVAL_PHRASE), ("Infinity", APPROVAL_PHRASE), ("-1", APPROVAL_PHRASE)]:
            with self.subTest(limit=limit, phrase=phrase), self.assertRaises(Blocked):
                approve(self.root, self.quote, limit, phrase)

    def test_no_native_token_guess_or_qwen_substitution(self):
        pf = fixture_counts(self.ctx)
        pf["openai"]["input_tokens"].pop(next(iter(pf["openai"]["input_tokens"])))
        with self.assertRaises(Blocked):
            make_quote(self.ctx, pf, fixture_evidence())

    def test_unverified_rates_or_parameters_block(self):
        for field, value in [("parameters_verified", False), ("sources", []), ("verified_at", "2000-01-01T00:00:00+00:00")]:
            evidence = fixture_evidence()
            evidence[field] = value
            with self.subTest(field=field), self.assertRaises(Blocked):
                make_quote(self.ctx, fixture_counts(self.ctx), evidence)

    def test_mismatched_scope_or_actual_body_rejected(self):
        self.authorize()
        altered = copy.deepcopy(self.ctx)
        altered["scope"]["models"]["openai"] = "other-model"
        with self.assertRaises(Blocked):
            validate_approval(self.root, self.controller.state["approval"], altered)
        altered = copy.deepcopy(self.ctx)
        altered["scope_sha256"] = "0" * 64
        with self.assertRaises(Blocked):
            Controller(self.root, altered, self.clients)

    def test_incomplete_real_readiness_zero_paid_calls(self):
        self.authorize()
        with self.assertRaises(Blocked):
            self.controller.submit_pending({"ready": False})
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_submit_once_and_resume_all_three_trials(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        resumed = Controller(self.root, self.ctx, self.clients)
        resumed.submit_pending(ready(self.ctx))
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [3, 3])
        self.assertTrue(all(e["batch_id"] for e in resumed.state["batches"].values()))
        self.assertEqual(len(list((self.root / "state/intents").glob("*.json"))), 6)

    def test_partial_success_unknown_stops_without_recreating_success(self):
        self.authorize()
        self.clients["anthropic"].raise_after_accept = True
        with self.assertRaisesRegex(Blocked, "SUBMISSION_UNKNOWN"):
            self.controller.submit_pending(ready(self.ctx))
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [1, 1])
        resumed = Controller(self.root, self.ctx, self.clients)
        with self.assertRaisesRegex(Blocked, "SUBMISSION_UNKNOWN"):
            resumed.submit_pending(ready(self.ctx))
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [1, 1])

    def test_crash_after_persisted_intent_never_resends(self):
        self.authorize()
        entry = next(iter(self.controller.state["batches"].values()))
        entry["status"] = "SUBMISSION_INTENT"
        self.controller.save()
        with self.assertRaisesRegex(Blocked, "SUBMISSION_UNKNOWN"):
            Controller(self.root, self.ctx, self.clients).submit_pending(ready(self.ctx))
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_reconcile_provider_evidence_then_only_pending_submit(self):
        self.authorize()
        self.clients["anthropic"].raise_after_accept = True
        with self.assertRaises(Blocked):
            self.controller.submit_pending(ready(self.ctx))
        self.clients["anthropic"].raise_after_accept = False
        self.controller.reconcile("anthropic-trial-01", "msgbatch_fixture_1")
        self.controller.submit_pending(ready(self.ctx))
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [3, 3])

    def test_shuffled_results_180_exact_ids_and_immutable_raw(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        result = self.controller.collect_once()
        self.assertEqual([x["id"] for x in result], self.ctx["scope"]["ids"])
        self.assertEqual(len(result), 180)
        self.assertEqual(set(x["generation_status"] for x in result), {"saved"})
        for b in self.ctx["batches"]:
            raw = self.root / "raw" / b["key"] / "responses.jsonl"
            self.assertEqual(read(raw), self.clients[b["provider"]].results(self.clients[b["provider"]].records[self.controller.state["batches"][b["key"]]["batch_id"]][0])[0][1])

    def test_duplicate_custom_id_blocks_collection_never_resubmit(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        self.clients["openai"].duplicate = True
        with self.assertRaisesRegex(Blocked, "Duplicate"):
            self.controller.collect_once()
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [3, 3])

    def test_missing_ids_remain_in_original_slots(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        self.clients["anthropic"].missing = True
        result = self.controller.collect_once()
        self.assertEqual(len(result), 180)
        self.assertEqual(sum(x["generation_status"] == "missing_result" for x in result), 3)

    def test_collection_interrupted_get_resumes_without_create(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        self.clients["anthropic"].download_fail_once = True
        with self.assertRaises(OSError):
            self.controller.collect_once()
        resumed = Controller(self.root, self.ctx, self.clients)
        result = resumed.collect_once()
        self.assertEqual(len(result), 180)
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [3, 3])

    def test_watch_collect_cannot_create_pending_batch(self):
        self.assertIsNone(self.controller.collect_once())
        with self.assertRaises(Blocked):
            self.controller.watch(interval=1)
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_saved_accepted_post_after_ledger_crash_recovers_without_new_create(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        key = "openai-trial-01"
        entry = self.controller.state["batches"][key]
        original = read(self.root / "state/submission-responses" / (key + ".json"))
        entry["status"], entry["batch_id"] = "SUBMISSION_INTENT", None
        self.controller.save()
        # Provider current GET can evolve after the accepted POST record.
        self.clients["openai"].records["batch_fixture_1"][0]["status"] = "in_progress"
        resumed = Controller(self.root, self.ctx, self.clients)
        resumed.submit_pending(ready(self.ctx))
        self.assertEqual(resumed.state["batches"][key]["batch_id"], "batch_fixture_1")
        self.assertEqual([len(p.create_calls) for p in self.clients.values()], [3, 3])
        self.assertEqual(read(self.root / "state/submission-responses" / (key + ".json")), original)

    def test_manual_reconciliation_preserves_accepted_post_and_stores_current_get(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        key = "openai-trial-01"
        original = read(self.root / "state/submission-responses" / (key + ".json"))
        self.controller.state["batches"][key]["status"] = "SUBMISSION_UNKNOWN"
        self.clients["openai"].records["batch_fixture_1"][0]["status"] = "in_progress"
        self.controller.reconcile(key, "batch_fixture_1")
        self.assertEqual(read(self.root / "state/submission-responses" / (key + ".json")), original)
        self.assertEqual(len(list((self.root / "state/reconciliation-responses" / key).glob("*.json"))), 1)

    @unittest.skip("Private worker deployment binding omitted; public numerical/data checks cover the published projection")
    def test_controller_worker_bridge_missing_errors_and_parser_identity(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        self.clients["anthropic"].missing = True
        collected = self.controller.collect_once()
        import worker
        bridge = worker.WorkerBridge(self.root, REPO)
        # Actual fixed parser and immutable raw hash checks, but no GPU/subprocess.
        payload = worker.worker_payload(collected, bridge.cfg)
        self.assertEqual(len(payload), 180)
        self.assertEqual(sum(x["generation_status"] == "missing_result" for x in payload), 3)
        self.assertEqual(sum(x["generation_status"] == "invalid_generation" for x in payload), 177)
        self.assertTrue(all("raw_response_path" not in x and "candidate_text" not in x for x in payload))

    @unittest.skip("Private worker deployment binding omitted; public numerical/data checks cover the published projection")
    def test_provider_format_and_model_anomaly_terminal_statuses_reach_worker(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        collected = self.controller.collect_once()
        import worker
        bridge = worker.WorkerBridge(self.root, REPO)
        for state in ("format_rejected", "model_mismatch", "api_error", "expired", "canceled", "incomplete"):
            items = copy.deepcopy(collected)
            items[0]["generation_status"] = state
            items[0]["candidate_text"] = None
            with self.subTest(state=state):
                payload = worker.worker_payload(items, bridge.cfg)
                self.assertEqual(payload[0]["generation_status"], state)
                self.assertNotIn("source", payload[0])

    def test_existing_remote_batch_missing_from_local_ledger_stops_create(self):
        self.authorize()
        metadata = {"gpu006_scope": self.ctx["scope_sha256"], "gpu006_batch": "openai-trial-01",
                    "gpu006_body": self.ctx["batches"][0]["body_sha256"], "gpu006_intent": "fixture"}
        self.clients["openai"].list_batches = lambda: [{"id": "batch-prior", "metadata": metadata}]
        with self.assertRaisesRegex(Blocked, "Existing provider Batch"):
            self.controller.submit_pending(ready(self.ctx))
        self.assertEqual(self.controller.state["batches"]["openai-trial-01"]["status"], "SUBMISSION_UNKNOWN")
        self.assertEqual(sum(len(p.create_calls) for p in self.clients.values()), 0)

    def test_raw_tampering_rejected_and_evidence_without_ledger_blocks(self):
        self.authorize()
        self.controller.submit_pending(ready(self.ctx))
        self.clients["openai"].duplicate = True
        with self.assertRaises(Blocked):
            self.controller.collect_once()
        artifact = self.root / self.controller.state["batches"]["openai-trial-01"]["raw_artifacts"][0]["path"]
        artifact.write_bytes(b"modified")
        with self.assertRaisesRegex(Blocked, "response changed"):
            self.controller.collect_once()
        self.controller.state_path.unlink()
        with self.assertRaisesRegex(Blocked, "Prior cloud evidence"):
            Controller(self.root, self.ctx, self.clients)

@unittest.skip("Private original deployment bundle is omitted; fixed public plan/draft/hash checks run separately")
class InputTamperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="gpu006-input-test-")
        cls.root = pathlib.Path(cls.temp.name)
        source = REPO / "runs/gpu006-target-info-v1"
        shutil.copytree(source / "inputs", cls.root / "runs/gpu006-target-info-v1/inputs")
        for name in ("prepared-inputs.tar.gz", "prepared-inputs-receipt.json"):
            target = cls.root / "runs/gpu006-target-info-v1" / name
            shutil.copy2(source / name, target)
        dest = cls.root / "runs/gpu006-tools-v1"
        dest.mkdir(parents=True)
        shutil.copy2(REPO / "runs/gpu006-tools-v1/cudacond_gpu006_prepare_l4_v1.py", dest)
        cls.plan_path = cls.root / "runs/gpu006-target-info-v1/inputs/plan.json"
        cls.original_plan = read(cls.plan_path)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def tearDown(self):
        self.plan_path.write_bytes(self.original_plan)

    def test_id_model_numerical_contract_and_prompt_tampering(self):
        for field in ("id", "model", "messages"):
            plan = json.loads(self.original_plan)
            plan["requests"][0][field] = "tampered"
            self.plan_path.write_bytes(canonical(plan))
            with self.subTest(field=field), self.assertRaisesRegex(Blocked, "SHA-256"):
                validate_inputs(self.root)
        plan = json.loads(self.original_plan)
        plan["numerical_contract"]["strict_semantics"] = "relaxed tolerance"
        self.plan_path.write_bytes(canonical(plan))
        with self.assertRaises(Blocked):
            validate_inputs(self.root)

    def test_draft_url_body_output_limit_tampering(self):
        path = self.root / "runs/gpu006-target-info-v1/inputs/drafts/trial-01/openai-requests-NOT-SUBMITTED.jsonl"
        original = read(path)
        try:
            for field, value in [("url", "/v1/chat/completions"), ("model", "alternative"), ("max_output_tokens", 1024)]:
                lines = [json.loads(x) for x in original.splitlines()]
                if field == "url":
                    lines[0][field] = value
                else:
                    lines[0]["body"][field] = value
                path.write_bytes(b"".join(canonical(x) for x in lines))
                with self.subTest(field=field), self.assertRaises(Exception):
                    validate_inputs(self.root)
        finally:
            path.write_bytes(original)

if __name__ == "__main__":
    unittest.main(verbosity=2)
