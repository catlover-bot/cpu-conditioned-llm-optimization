"""Fixture tests: no API keys, network, CUDA, subprocesses, or paid calls."""
import collections
import copy
import json
import pathlib
import unittest
from unittest import mock
import providers as P

ROOT = pathlib.Path(__file__).resolve().parents[2]
DRAFTS = ROOT / "runs/gpu006-target-info-v1/inputs/drafts"
KEY = "fixture-only-secret-never-a-real-api-key"

def payload(provider, trial=1):
    ext = "jsonl" if provider == "openai" else "json"
    return (DRAFTS / f"trial-{trial:02d}" / f"{provider}-requests-NOT-SUBMITTED.{ext}").read_bytes()

def response(value, status=200):
    return P.HttpResponse(status, P.canonical(value))

class Queue:
    def __init__(self, values):
        self.values = list(values)
        self.calls = []
    def __call__(self, request):
        self.calls.append(request)
        if not self.values:
            raise AssertionError("Unexpected HTTP call")
        value = self.values.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value(request) if callable(value) else value

def model(provider):
    obj = {"id": P.MODELS[provider]}
    if provider == "anthropic":
        obj.update(max_tokens=128000, max_input_tokens=1000000, capabilities={
            "batch": {"supported": True},
            "thinking": {"types": {"disabled": {"supported": True}}}})
    return obj

def success(provider, identifier=None):
    identifier = identifier or P.draft_rows(provider, payload(provider))[0]["custom_id"]
    text = '{"block":[32,8]}\nextern "C" __global__ void kernel() {}'
    if provider == "openai":
        return {"custom_id": identifier, "error": None, "response": {"status_code": 200, "body": {
            "id": "resp_fixture", "model": P.MODELS[provider], "status": "completed",
            "error": None, "incomplete_details": None, "usage": {
                "input_tokens": 100, "output_tokens": 30,
                "input_tokens_details": {"cached_tokens": 20, "cache_write_tokens": 10},
                "output_tokens_details": {"reasoning_tokens": 0}},
            "output": [{"type": "message", "role": "assistant", "status": "completed",
                        "content": [{"type": "output_text", "text": text}]}]}}}
    return {"custom_id": identifier, "result": {"type": "succeeded", "message": {
        "id": "msg_fixture", "type": "message", "model": P.MODELS[provider], "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 30, "cache_read_input_tokens": 20,
                  "cache_creation_input_tokens": 10},
        "content": [{"type": "text", "text": text}]}}}

def fixtures_documents():
    return {
        "openai_model": 'Model ID: \x60gpt-5.6-terra\x60\nReasoning.effort supports: none, low.\n- Prompts with >272K input tokens are priced at 2x input and 1.5x output for the full request.\n- Cache writes are billed at 1.25x the uncached input token rate.\n| Input | $2 | 1M tokens |\n| Cached input | $0.2 | 1M tokens |\n| Output | $12 | 1M tokens |',
        "openai_batch": "50% lower cost /v1/responses",
        "openai_schema": "temperature top_p max_output_tokens tool_choice truncation store stream reasoning",
        "openai_compatibility": "### GPT-5.6 parameter compatibility\nFixture-only statement: temperature and top_p require reasoning effort none.\n",
        "openai_latest": "# Using GPT-6\n GPT-6 parameter rules at reasoning effort none. temperature top_p",
        "openai_batch_schema": "Batch errors expose code line param; creation is not request acceptance.",
        "anthropic_model": "claude-sonnet-5",
        "anthropic_pricing": "| Claude Sonnet 5 | $2 / MTok | $2.50 / MTok | $4 / MTok | $0.20 / MTok | $10 / MTok |\nThese stack with other pricing modifiers.\n### Batch processing\n| Claude Sonnet 5 | $1 / MTok | $5 / MTok |",
        "anthropic_thinking": 'On Claude Sonnet 5, fixture-only example: {"model":"claude-sonnet-5","thinking":{"type":"disabled"}}',
    }

def docs_transport(documents):
    def call(request):
        if "gpt-5.6-terra.md" in request.url: kind = "openai_model"
        elif "guides/batch.md" in request.url: kind = "openai_batch"
        elif "responses/methods/create" in request.url: kind = "openai_schema"
        elif "latest-model/gpt-5.6.md" in request.url: kind = "openai_compatibility"
        elif "guides/latest-model.md" in request.url: kind = "openai_latest"
        elif "batches/methods/create" in request.url: kind = "openai_batch_schema"
        elif "sonnet-5/overview" in request.url: kind = "anthropic_model"
        elif "about-claude/pricing" in request.url: kind = "anthropic_pricing"
        else: kind = "anthropic_thinking"
        assert request.method == "GET"
        assert not any(k.lower() in ("authorization", "x-api-key") for k in request.headers)
        return P.HttpResponse(200, documents[kind].encode())
    return call

class RealDraftTests(unittest.TestCase):
    def test_all_270_ids_models_and_cloud_arms(self):
        plan = json.loads((ROOT / "runs/gpu006-target-info-v1/inputs/plan.json").read_bytes())
        self.assertEqual(collections.Counter(r["provider"] for r in plan["requests"]), {"qwen":90,"openai":90,"anthropic":90})
        planned = {r["id"]:r for r in plan["requests"]}
        seen = set()
        for provider in P.MODELS:
            for trial in (1,2,3):
                rows = P.draft_rows(provider, payload(provider, trial))
                self.assertEqual(len(rows), 30)
                self.assertEqual(collections.Counter(r["custom_id"].split("__")[3] for r in rows),
                                 {arm:6 for arm in plan["information_conditions"]})
                for row in rows:
                    identifier = row["custom_id"]
                    self.assertNotIn(identifier, seen)
                    seen.add(identifier)
                    p = planned[identifier]
                    body = P.validate_request(provider,row)
                    self.assertEqual(body["model"],p["model"])
                    msgs = body["input"] if provider == "openai" else [{"role":"system","content":body["system"]}]+body["messages"]
                    self.assertEqual(msgs,p["messages"])
                    self.assertEqual(trial,p["trial"])
        self.assertEqual(len(seen),180)

    def test_model_setting_endpoint_mutations_refused(self):
        for provider in P.MODELS:
            row = P.draft_rows(provider,payload(provider))[0]
            bodykey = "body" if provider == "openai" else "params"
            for mutation in ("model","limit","thinking","extra"):
                bad=copy.deepcopy(row)
                if mutation == "model": bad[bodykey]["model"]="different-model"
                elif mutation == "limit": bad[bodykey]["max_output_tokens" if provider=="openai" else "max_tokens"]=1024
                elif mutation == "thinking": bad[bodykey]["reasoning" if provider=="openai" else "thinking"]={}
                else: bad[bodykey]["new_option"]=True
                with self.assertRaises(P.ProviderError): P.validate_request(provider,bad)
        bad=copy.deepcopy(P.draft_rows("openai",payload("openai"))[0]);bad["url"]="/v1/chat/completions"
        with self.assertRaises(P.ProviderError): P.validate_request("openai",bad)

    def test_duplicate_custom_id_and_duplicate_json_key_refused(self):
        row=P.draft_rows("openai",payload("openai"))[0]
        with self.assertRaises(P.ProviderError):P.draft_rows("openai",P.canonical(row)+b"\n"+P.canonical(row))
        with self.assertRaises(P.ProviderError):P.strict_json(b'{"id":1,"id":2}')

class PreflightTests(unittest.TestCase):
    def test_all_real_180_counted_without_synchronous_generation(self):
        for provider in P.MODELS:
            rows=sum((P.draft_rows(provider,payload(provider,t)) for t in (1,2,3)),[])
            count={"input_tokens":1234}
            if provider=="openai":count["object"]="response.input_tokens"
            q=Queue([response(model(provider))]+[response(count) for _ in rows])
            out=P.Provider(provider,KEY,q).preflight(rows)
            self.assertEqual(set(out["input_tokens"]),{r["custom_id"] for r in rows})
            self.assertEqual(len(out["input_tokens"]),90)
            self.assertEqual(len(q.calls),91)
            self.assertTrue(out["permission"]["batch_create_permission_not_probed"])
            self.assertTrue(q.calls[0].url.endswith("/v1/models/"+P.MODELS[provider]))
            for request,row in zip(q.calls[1:],rows):
                self.assertIn("tokens",request.url)
                counted=P.strict_json(request.body)
                body=P.validate_request(provider,row)
                self.assertEqual(counted["model"],body["model"])
                self.assertEqual(counted["input" if provider=="openai" else "messages"],body["input" if provider=="openai" else "messages"])
                self.assertNotIn("max_output_tokens",counted);self.assertNotIn("max_tokens",counted)
                if provider=="anthropic":self.assertEqual(counted["thinking"],{"type":"disabled"})

    def test_permission_failure_no_post(self):
        q=Queue([P.ProviderError("http_error",403)])
        with self.assertRaises(P.ProviderError):P.Provider("openai",KEY,q).preflight(P.draft_rows("openai",payload("openai")))
        self.assertEqual(len(q.calls),1);self.assertEqual(q.calls[0].method,"GET")

    def test_wrong_model_or_missing_disabled_capability_refused(self):
        for change in ("id","batch","thinking"):
            obj=model("anthropic")
            if change=="id":obj["id"]="claude-sonnet-5-5"
            elif change=="batch":obj["capabilities"]["batch"]["supported"]=False
            else:obj["capabilities"]["thinking"]["types"]["disabled"]["supported"]=False
            q=Queue([response(obj)])
            with self.assertRaises(P.ProviderError):P.Provider("anthropic",KEY,q).preflight(P.draft_rows("anthropic",payload("anthropic")))
            self.assertEqual(len(q.calls),1)

    def test_invalid_count_and_context_refused(self):
        for count in (True,-1,0,1000001):
            q=Queue([response(model("anthropic")),response({"input_tokens":count})])
            with self.assertRaises(P.ProviderError):P.Provider("anthropic",KEY,q).preflight(P.draft_rows("anthropic",payload("anthropic"))[:1])
            self.assertEqual(len(q.calls),2)

    def test_sync_generation_centrally_disallowed(self):
        q=Queue([])
        for provider,path in (("openai","/v1/responses"),("openai","/v1/chat/completions"),("anthropic","/v1/messages")):
            with self.assertRaises(P.ProviderError):P.Provider(provider,KEY,q)._raw("POST",path,b"{}")
        self.assertEqual(q.calls,[])

class SubmissionTests(unittest.TestCase):
    def test_openai_upload_preserves_exact_bytes_and_metadata(self):
        raw=payload("openai");meta={"gpu006_scope":"fixture","gpu006_body":"hash","gpu006_batch":"openai-trial-01","gpu006_intent":"intent"}
        q=Queue([response({"id":"file-fixture"}),response({"id":"batch_fixture"})])
        got=P.Provider("openai",KEY,q).submit(raw,meta)
        self.assertEqual(got["id"],"batch_fixture");self.assertEqual(len(q.calls),2)
        self.assertIn(raw,q.calls[0].body)
        created=P.strict_json(q.calls[1].body)
        self.assertEqual(created["metadata"],meta);self.assertEqual(created["endpoint"],"/v1/responses")
        self.assertEqual(created["completion_window"],"24h")

    def test_anthropic_exact_payload_single_create(self):
        raw=payload("anthropic");q=Queue([response({"id":"msgbatch_fixture"})])
        P.Provider("anthropic",KEY,q).submit(raw,{})
        self.assertEqual(len(q.calls),1);self.assertEqual(q.calls[0].body,raw)
        self.assertTrue(q.calls[0].url.endswith("/v1/messages/batches"))

    def test_six_real_batches_only(self):
        for provider in P.MODELS:
            for t in (1,2,3):
                batchid="batch_fixture" if provider=="openai" else "msgbatch_fixture"
                q=Queue(([response({"id":"file-fixture"})] if provider=="openai" else [])+[response({"id":batchid})])
                P.Provider(provider,KEY,q).submit(payload(provider,t),{})
                self.assertEqual(sum(c.url.endswith("/batches") for c in q.calls),1)

    def test_ambiguous_create_transport_http_server_and_missing_id_never_retry(self):
        errors=[TimeoutError("untrusted "+KEY),P.ProviderError("http_error",503),
                P.HttpResponse(200,b"not JSON"),response({}),response([],200)]
        for provider in P.MODELS:
            for error in errors:
                q=Queue(([response({"id":"file-fixture"})] if provider=="openai" else [])+[error])
                with self.assertRaises(P.SubmissionUnknown) as cm:P.Provider(provider,KEY,q).submit(payload(provider),{})
                self.assertNotIn(KEY,str(cm.exception))
                self.assertEqual(len(q.calls),2 if provider=="openai" else 1)

    def test_definite_http_rejection_not_unknown(self):
        q=Queue([P.HttpResponse(400,b'{"error":"'+KEY.encode()+b'"}')])
        with self.assertRaises(P.ProviderError) as cm:P.Provider("anthropic",KEY,q).submit(payload("anthropic"),{})
        self.assertNotIsInstance(cm.exception,P.SubmissionUnknown);self.assertNotIn(KEY,str(cm.exception));self.assertEqual(len(q.calls),1)

    def test_upload_failure_has_not_started_a_batch(self):
        q=Queue([TimeoutError("untrusted")])
        with self.assertRaises(P.ProviderError) as cm:P.Provider("openai",KEY,q).submit(payload("openai"),{})
        self.assertNotIsInstance(cm.exception,P.SubmissionUnknown);self.assertEqual(len(q.calls),1)

    def test_invalid_operational_size_or_mixed_trial_batch_refused_without_calls(self):
        rows=P.draft_rows("anthropic",payload("anthropic"))
        for bad in (rows[:2],rows[:28],rows[:29]+P.draft_rows("anthropic",payload("anthropic",2))[:1]):
            q=Queue([])
            with self.assertRaises(P.ProviderError):P.Provider("anthropic",KEY,q).submit(P.canonical({"requests":bad}),{})
            self.assertEqual(q.calls,[])

    def test_approved_operational_1_29_30_shapes_preserve_exact_draft_requests(self):
        for provider in P.MODELS:
            original=payload(provider)
            rows=P.draft_rows(provider,original)
            for number in (1,29,30):
                if provider=="openai":
                    sent=b"".join(original.splitlines(keepends=True)[:number]) if number==1 else b"".join(original.splitlines(keepends=True)[-number:])
                else:
                    sent=P.canonical({"requests":rows[:number] if number==1 else rows[-number:]})
                identifier="batch_fixture" if provider=="openai" else "msgbatch_fixture"
                q=Queue(([response({"id":"file-fixture"})] if provider=="openai" else [])+[response({"id":identifier})])
                P.Provider(provider,KEY,q).submit(sent,{"gpu006_batch":"approved-fixture"})
                self.assertEqual(len(P.draft_rows(provider,sent)),number)
                if provider=="openai":self.assertIn(sent,q.calls[0].body)
                else:self.assertEqual(q.calls[0].body,sent)
                self.assertEqual(sum(c.url.endswith("/batches") for c in q.calls),1)

    def test_secrets_not_in_request_repr_provider_repr_or_errors(self):
        obj=P.Provider("openai",KEY,Queue([]))
        self.assertNotIn(KEY,repr(obj))
        req=P.HttpRequest("POST","https://api.openai.com/v1/batches",{"Authorization":KEY},KEY.encode())
        self.assertNotIn(KEY,repr(req))

class RecoveryAndResultTests(unittest.TestCase):
    def test_retrieve_download_get_only_raw_unchanged(self):
        raw=b'{"custom_id":"fixture","raw":"spacing"} \n'
        q=Queue([response({"id":"batch_fixture","output_file_id":"file-out","error_file_id":"file-err"}),
                 P.HttpResponse(200,raw),P.HttpResponse(200,b"")])
        obj=P.Provider("openai",KEY,q); batch=obj.retrieve("batch_fixture")
        files=obj.results(batch)
        self.assertEqual(files,[("output.jsonl",raw),("error.jsonl",b"")])
        self.assertTrue(all(c.method=="GET" for c in q.calls))

    def test_interrupted_collect_can_repeat_get_without_create(self):
        batch={"id":"batch_fixture","output_file_id":"file-out"}
        q=Queue([TimeoutError("downloading"),P.HttpResponse(200,b"raw\n")])
        obj=P.Provider("openai",KEY,q)
        with self.assertRaises(P.ProviderError):obj.results(batch)
        self.assertEqual(obj.results(batch),[("output.jsonl",b"raw\n")])
        self.assertEqual([c.method for c in q.calls],["GET","GET"])

    def test_anthropic_untrusted_result_urls_rejected_without_key_leak(self):
        for url in ("http://api.anthropic.com/v1/messages/batches/msgbatch_fixture/results",
                    "https://evil.example/v1/messages/batches/msgbatch_fixture/results",
                    "https://api.anthropic.com@evil.example/a","https://api.anthropic.com/v1/messages/batches/msgbatch_other/results"):
            q=Queue([])
            with self.assertRaises(P.ProviderError):P.Provider("anthropic",KEY,q).results({"id":"msgbatch_fixture","results_url":url})
            self.assertEqual(q.calls,[])

    def test_openai_reconciliation_checks_metadata_and_exact_input(self):
        meta={"gpu006_scope":"scope"}
        batch={"id":"batch_fixture","endpoint":"/v1/responses","metadata":meta,"input_file_id":"file-input"}
        q=Queue([P.HttpResponse(200,payload("openai"))])
        self.assertTrue(P.Provider("openai",KEY,q).verify_batch(batch,payload("openai"),meta))
        bad=copy.deepcopy(batch);bad["metadata"]={}
        q=Queue([])
        self.assertFalse(P.Provider("openai",KEY,q).verify_batch(bad,payload("openai"),meta));self.assertEqual(q.calls,[])

    def test_anthropic_reconciliation_requires_complete_exact_unique_ids(self):
        rows=P.draft_rows("anthropic",payload("anthropic"))
        items=[success("anthropic",r["custom_id"]) for r in reversed(rows)]
        batch={"id":"msgbatch_fixture","processing_status":"ended","results_url":"https://api.anthropic.com/v1/messages/batches/msgbatch_fixture/results"}
        for fixture,expected in ((items,True),(items[:-1],False),(items[:-1]+[items[0]],False)):
            q=Queue([P.HttpResponse(200,b"\n".join(P.canonical(x) for x in fixture)+b"\n")])
            self.assertEqual(P.Provider("anthropic",KEY,q).verify_batch(batch,payload("anthropic"),{}),expected)
            self.assertTrue(all(c.method=="GET" for c in q.calls))

    def test_list_batches_pagination_read_only(self):
        for provider,prefix in (("openai","batch_"),("anthropic","msgbatch_")):
            q=Queue([response({"data":[{"id":prefix+"one"}],"has_more":True,"last_id":prefix+"one"}),
                     response({"data":[{"id":prefix+"two"}],"has_more":False})])
            self.assertEqual(len(P.Provider(provider,KEY,q).list_batches()),2)
            self.assertTrue(all(c.method=="GET" for c in q.calls))
            self.assertIn("after="+prefix+"one" if provider=="openai" else "after_id="+prefix+"one",q.calls[1].url)

    def test_success_usage_text_and_order_independent_ids(self):
        for provider in P.MODELS:
            rows=P.draft_rows(provider,payload(provider))
            normalized=[P.normalize_result(provider,success(provider,r["custom_id"])) for r in reversed(rows)]
            mapped={r["id"]:r for r in normalized}
            self.assertEqual(set(mapped),{r["custom_id"] for r in rows})
            self.assertTrue(all(r["generation_status"]=="saved" for r in mapped.values()))
            sample=next(iter(mapped.values()));self.assertIn("extern",sample["candidate_text"])
            self.assertEqual(sample["usage"]["cached_input_tokens"],20)
            self.assertTrue(sample["raw_usage"])
            if provider=="openai":
                self.assertEqual(sample["raw_usage"]["input_tokens_details"]["cache_write_tokens"],10)
                self.assertIn("output_tokens_details",sample["raw_usage"])
            else:self.assertEqual(sample["raw_usage"]["cache_read_input_tokens"],20)
            self.assertEqual(sample["usage"]["cache_creation_input_tokens"],10)

    def test_expired_canceled_api_errors_kept_on_original_id(self):
        for provider in P.MODELS:
            identifier=P.draft_rows(provider,payload(provider))[0]["custom_id"]
            for state in ("expired","canceled","api_error"):
                if provider=="openai":
                    item={"custom_id":identifier,"error":{"code":{"expired":"batch_expired","canceled":"batch_canceled","api_error":"request_error"}[state]},"response":None}
                else:item={"custom_id":identifier,"result":{"type":{"api_error":"errored"}.get(state,state)}}
                out=P.normalize_result(provider,item)
                self.assertEqual(out["id"],identifier);self.assertEqual(out["generation_status"],state)
                self.assertIsNone(out["candidate_text"])

    def test_output_limit_stop_is_incomplete_not_saved(self):
        for provider in P.MODELS:
            item=success(provider)
            if provider=="openai":item["response"]["body"]["status"]="incomplete";item["response"]["body"]["incomplete_details"]={"reason":"max_output_tokens"}
            else:item["result"]["message"]["stop_reason"]="max_tokens"
            got=P.normalize_result(provider,item)
            self.assertEqual(got["generation_status"],"incomplete")
            self.assertIsNone(got["candidate_text"]);self.assertEqual(got["usage"]["output_tokens"],30)

    def test_refusal_tool_calls_and_unknown_model_not_salvaged(self):
        for provider in P.MODELS:
            item=success(provider)
            body=item["response"]["body"] if provider=="openai" else item["result"]["message"]
            body["model"]="different-model"
            got=P.normalize_result(provider,item)
            self.assertEqual(got["id"],item["custom_id"])
            self.assertEqual(got["generation_status"],"model_mismatch")
            self.assertTrue(got["provider_anomaly"]);self.assertIsNone(got["candidate_text"])
            item=success(provider)
            if provider=="openai":item["response"]["body"]["output"][0]["content"]=[{"type":"refusal","refusal":"no"}]
            else:item["result"]["message"]["content"]=[{"type":"tool_use","name":"unexpected"}]
            self.assertEqual(P.normalize_result(provider,item)["generation_status"],"format_rejected")

    def test_wrong_usage_type_not_coerced(self):
        item=success("anthropic");item["result"]["message"]["usage"]["output_tokens"]=True
        with self.assertRaises(P.ProviderError):P.normalize_result("anthropic",item)

    def test_missing_usage_and_optional_counters_remain_unknown(self):
        for provider in P.MODELS:
            for native in (None, {}, {"input_tokens":100,"output_tokens":30}):
                item=success(provider)
                body=item["response"]["body"] if provider=="openai" else item["result"]["message"]
                if native is None:body.pop("usage")
                else:body["usage"]=native
                out=P.normalize_result(provider,item)
                self.assertEqual(out["generation_status"],"saved")
                self.assertEqual(out["raw_usage"],native)
                self.assertIsNone(out["usage"]["cached_input_tokens"])
                self.assertIsNone(out["usage"]["cache_creation_input_tokens"])
                self.assertIsNone(out["usage"]["reasoning_tokens"])
                self.assertEqual(out["usage"]["output_tokens"],30 if native else None)

    def test_only_reported_output_counts_checked_against_fixed_cap(self):
        for provider in P.MODELS:
            item=success(provider)
            body=item["response"]["body"] if provider=="openai" else item["result"]["message"]
            body["usage"]={"input_tokens":100}
            self.assertEqual(P.normalize_result(provider,item)["generation_status"],"saved")
            body["usage"]["output_tokens"]=8193
            with self.assertRaisesRegex(P.ProviderError,"result_output_limit_mismatch"):
                P.normalize_result(provider,item)

    def test_nonobject_content_remains_terminal_on_original_id(self):
        for provider in P.MODELS:
            item=success(provider)
            if provider=="openai":item["response"]["body"]["output"]=[None]
            else:item["result"]["message"]["content"]=[None]
            got=P.normalize_result(provider,item)
            self.assertEqual(got["id"],item["custom_id"])
            self.assertEqual(got["generation_status"],"format_rejected")
            self.assertIsNone(got["candidate_text"])


    def test_multiple_text_parts_are_not_concatenated_or_salvaged(self):
        for provider in P.MODELS:
            item=success(provider)
            body=item["response"]["body"] if provider=="openai" else item["result"]["message"]
            contents=body["output"][0]["content"] if provider=="openai" else body["content"]
            contents.append(copy.deepcopy(contents[0]))
            out=P.normalize_result(provider,item)
            self.assertEqual(out["id"],item["custom_id"])
            self.assertEqual(out["generation_status"],"format_rejected")
            self.assertIsNone(out["candidate_text"])
            self.assertEqual(out["raw_usage"],body["usage"])
        item=success("openai")
        item["response"]["body"]["output"].append(copy.deepcopy(item["response"]["body"]["output"][0]))
        out=P.normalize_result("openai",item)
        self.assertEqual(out["generation_status"],"format_rejected");self.assertIsNone(out["candidate_text"])

    def test_claude_message_body_type_required(self):
        for value in (None,"response",""):
            item=success("anthropic")
            body=item["result"]["message"]
            if value is None:body.pop("type")
            else:body["type"]=value
            got=P.normalize_result("anthropic",item)
            self.assertEqual(got["id"],item["custom_id"])
            self.assertEqual(got["generation_status"],"format_rejected")
            self.assertIsNone(got["candidate_text"])

    def test_text_acceptance_matches_actual_pinned_response_text(self):
        import ast, types
        original=ROOT/"tools/research_protocols/gpu006/legacy_response_text.py"
        source=original.read_text()
        function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=="response_text")
        def require(condition,message):
            if not condition:raise ValueError(message)
        namespace={"P":types.SimpleNamespace(require=require),"need":require}
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(original),"exec"),namespace)
        pinned=namespace["response_text"]
        cfg={"models":{provider:{"id":model} for provider,model in P.MODELS.items()}}
        fixtures=[]
        for provider in P.MODELS:
            item=success(provider);fixtures.append((provider,item))
            multiple=copy.deepcopy(item)
            body=multiple["response"]["body"] if provider=="openai" else multiple["result"]["message"]
            parts=body["output"][0]["content"] if provider=="openai" else body["content"]
            parts.append(copy.deepcopy(parts[0]));fixtures.append((provider,multiple))
            wrong=copy.deepcopy(item)
            body=wrong["response"]["body"] if provider=="openai" else wrong["result"]["message"]
            if provider=="openai":
                body["output"][0]["content"][0]["type"]="refusal"
                reasoning=copy.deepcopy(item);reasoning["response"]["body"]["output"].insert(0,{"type":"reasoning"})
                fixtures.append((provider,reasoning))
                duplicated=copy.deepcopy(item);duplicated["response"]["body"]["output"].append(copy.deepcopy(duplicated["response"]["body"]["output"][0]))
                fixtures.append((provider,duplicated))
            else:
                body.pop("type")
                thought=copy.deepcopy(item);thought["result"]["message"]["content"].insert(0,{"type":"thinking","thinking":"unexpected"})
                fixtures.append((provider,thought))
            fixtures.append((provider,wrong))
        for provider,item in fixtures:
            body=item["response"]["body"] if provider=="openai" else item["result"]["message"]
            try:expected=pinned(provider,body,cfg)
            except ValueError:expected=None
            got=P.normalize_result(provider,item)
            self.assertEqual(got["candidate_text"],expected)
            self.assertEqual(got["generation_status"],"saved" if expected is not None else "format_rejected")
            self.assertEqual(got["id"],item["custom_id"])


class ApiAcceptanceTests(unittest.TestCase):
    def request(self,provider="openai"):
        return P.draft_rows(provider,payload(provider))[0]

    def assess(self,item,provider="openai",terminal=None):
        return P.assess_api_acceptance(provider,item,self.request(provider),
                                      "batch_fixture" if provider=="openai" else "msgbatch_fixture",
                                      "0"*64,terminal)

    def test_exact_echoes_and_provider_ids_preserved_without_candidate_claim(self):
        row=success("openai");row["id"]="batch_req_fixture";row["response"]["request_id"]="req_fixture"
        body=row["response"]["body"]
        for field in ("reasoning","temperature","top_p","max_output_tokens"):
            body[field]=copy.deepcopy(self.request()["body"][field])
        got=self.assess(row)
        self.assertEqual(got["status"],"accepted");self.assertTrue(got["accepted"])
        self.assertEqual(got["batch_request_id"],"batch_req_fixture")
        self.assertEqual(got["provider_request_id"],"req_fixture")
        self.assertEqual(got["provider_response_id"],"resp_fixture")
        self.assertEqual(got["submission_body_sha256"],"0"*64)
        import hashlib
        self.assertEqual(got["request_body_sha256"],hashlib.sha256(P.canonical(self.request()["body"])).hexdigest())
        self.assertTrue(all(v["status"]=="match" for v in got["settings"].values()))
        self.assertFalse(got["candidate_status_used"]);self.assertEqual(got["parameter_influence"],"not assessed")

    def test_missing_and_null_echoes_unknown_while_native_request_is_accepted(self):
        for provider in P.MODELS:
            row=success(provider)
            got=self.assess(row,provider)
            self.assertEqual(got["status"],"accepted")
            self.assertTrue(all(v["status"]=="unknown" for v in got["settings"].values()))
            body=row["response"]["body"] if provider=="openai" else row["result"]["message"]
            for name in ("reasoning","temperature","top_p","max_output_tokens") if provider=="openai" else ("thinking","max_tokens"):
                body[name]=None
            got=self.assess(row,provider)
            self.assertEqual(got["status"],"accepted")
            self.assertTrue(all(v["status"]=="unknown" for v in got["settings"].values()))

    def test_format_failure_and_output_cap_incomplete_do_not_reject_api_acceptance(self):
        row=success("openai")
        row["response"]["body"]["output"][0]["content"].append({"type":"output_text","text":"second"})
        self.assertEqual(P.normalize_result("openai",row)["generation_status"],"format_rejected")
        self.assertEqual(self.assess(row)["status"],"accepted")
        row["response"]["body"]["status"]="incomplete"
        row["response"]["body"]["incomplete_details"]={"reason":"max_output_tokens"}
        self.assertEqual(P.normalize_result("openai",row)["generation_status"],"incomplete")
        self.assertEqual(self.assess(row)["status"],"accepted")

    def test_code_and_numeric_content_do_not_enter_acceptance_decision(self):
        row=success("openai");row["response"]["body"]["output"][0]["content"][0]["text"]="invalid CUDA/BLOCK/numerics"
        self.assertEqual(self.assess(row)["status"],"accepted")
        row["response"]["body"]["output"]=[]
        self.assertEqual(self.assess(row)["status"],"accepted")

    def test_explicit_fixed_parameter_error_is_separate_from_other_api_error(self):
        for param in ("temperature","body.top_p","reasoning.effort","max_output_tokens"):
            row={"custom_id":self.request()["custom_id"],"response":{"status_code":400,"request_id":"req_error",
                 "body":{"error":{"code":"unsupported_parameter","param":param,"message":"DO NOT COPY "+KEY}}}}
            got=self.assess(row)
            self.assertEqual(got["status"],"fixed_parameter_rejected");self.assertFalse(got["accepted"])
            self.assertNotIn(KEY,P.canonical(got).decode())
            self.assertEqual(got["provider_request_id"],"req_error")
        row={"custom_id":self.request()["custom_id"],"error":{"code":"rate_limit_exceeded","param":"temperature"}}
        self.assertEqual(self.assess(row)["status"],"other_api_error")
        row["error"]={"code":"unsupported_parameter","param":"unknown_option"}
        self.assertEqual(self.assess(row)["status"],"other_api_error")

    def test_terminal_single_pilot_parameter_validation_error_is_rejected(self):
        for counts,line in (({"total":1},None),({"total":0},1),({},1)):
            terminal={"id":"batch_fixture","status":"failed","request_counts":counts,
                      "errors":{"data":[{"code":"unsupported_value","param":"body.temperature","line":line}]}}
            got=self.assess(None,terminal=terminal)
            self.assertEqual(got["status"],"fixed_parameter_rejected")
            self.assertEqual(got["custom_id"],self.request()["custom_id"])
            self.assertTrue(all(v["status"]=="unknown" for v in got["settings"].values()))
        terminal["request_counts"]={"total":29}
        self.assertEqual(self.assess(None,terminal=terminal)["status"],"unknown")
        terminal["request_counts"]={"total":1};terminal["id"]="batch_other"
        self.assertEqual(self.assess(None,terminal=terminal)["status"],"unknown")

    def test_batch_creation_and_count_are_not_request_acceptance_proof(self):
        for row in (None,{"id":"batch_fixture","status":"validating"},{"input_tokens":123}):
            self.assertEqual(self.assess(row)["status"],"unknown")
        terminal={"id":"batch_fixture","status":"completed","request_counts":{"completed":1,"total":1}}
        self.assertEqual(self.assess(None,terminal=terminal)["status"],"unknown")

    def test_expired_canceled_or_missing_results_remain_unknown(self):
        for code in ("batch_expired","batch_canceled","batch_cancelled"):
            got=self.assess({"custom_id":self.request()["custom_id"],"error":{"code":code}})
            self.assertEqual(got["status"],"unknown");self.assertFalse(got["accepted"])

    def test_native_http_error_without_structured_error_is_other_api_error(self):
        for code in (400,401,403,429,500):
            got=self.assess({"custom_id":self.request()["custom_id"],"response":{"status_code":code,"body":{}}})
            self.assertEqual(got["status"],"other_api_error")
            self.assertFalse(got["native_request_accepted"])

    def test_echo_mismatch_is_explicit_and_cannot_pass_pilot(self):
        for key,value in (("temperature",1.0),("top_p",0.1),("max_output_tokens",True),("reasoning",{"effort":"high"})):
            row=success("openai");row["response"]["body"][key]=value
            got=self.assess(row)
            self.assertEqual(got["status"],"unknown");self.assertFalse(got["accepted"])
            target="reasoning.effort" if key=="reasoning" else key
            self.assertEqual(got["settings"][target]["status"],"mismatch")
            self.assertIn("returned_fixed_parameter_mismatch",got["reason_codes"])

    def test_model_id_response_id_and_custom_id_must_match_request_evidence(self):
        row=success("openai");row["response"]["body"]["model"]="different-model"
        self.assertEqual(self.assess(row)["status"],"unknown")
        row=success("openai");row["response"]["body"].pop("id")
        self.assertEqual(self.assess(row)["status"],"unknown")
        row=success("openai");row["custom_id"]="other-id"
        self.assertEqual(self.assess(row)["status"],"unknown")

    def test_native_failed_status_without_success_proof_is_unknown(self):
        row=success("openai");row["response"]["body"]["status"]="failed"
        self.assertEqual(self.assess(row)["status"],"unknown")

    def test_malformed_native_error_or_http_status_cannot_pass_pilot(self):
        for place in ("batch","response"):
            row=success("openai")
            if place=="batch":row["error"]="malformed error"
            else:row["response"]["body"]["error"]="malformed error"
            self.assertEqual(self.assess(row)["status"],"unknown")
        for value in (200.0,"200"):
            row=success("openai");row["response"]["status_code"]=value
            self.assertEqual(self.assess(row)["status"],"unknown")

    def test_assessment_scope_argument_errors_are_safe(self):
        for batchid,hashvalue in (("invalid","0"*64),("batch_fixture","bad"),("batch_fixture",5)):
            with self.assertRaises(P.ProviderError):
                P.assess_api_acceptance("openai",success("openai"),self.request(),batchid,hashvalue)

class OfficialEvidenceTests(unittest.TestCase):
    def test_current_named_rates_hashed_and_no_authenticated_calls(self):
        got=P.refresh_official_evidence(docs_transport(fixtures_documents()))
        self.assertEqual(len(got["sources"]),9);self.assertTrue(got["parameters_verified"])
        self.assertEqual(got["rates"]["openai"]["output_usd_per_mtok"],6)
        self.assertEqual(got["rates"]["anthropic"]["output_usd_per_mtok"],5)
        self.assertTrue(all(len(x["sha256"])==64 for x in got["sources"]))
        self.assertFalse(got["permission_checks_executed"]);self.assertFalse(got["token_counts_executed"])
        self.assertEqual(got["paid_generation_calls"],0)

    def test_undocumented_requested_models_fail_closed(self):
        for kind,bad in (("openai_model","Model ID: different-model"),("anthropic_model","claude-sonnet-5-5")):
            docs=fixtures_documents();docs[kind]=bad
            with self.assertRaises(P.ProviderError):P.refresh_official_evidence(docs_transport(docs))

    def test_changed_current_price_is_preserved_for_new_approval(self):
        docs=fixtures_documents()
        docs["anthropic_pricing"]=docs["anthropic_pricing"].replace("$5 / MTok", "$6 / MTok")
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertEqual(got["rates"]["anthropic"]["output_usd_per_mtok"],6)

    def test_generic_schema_does_not_prove_specific_sampling(self):
        docs=fixtures_documents();docs["openai_compatibility"]="Exact family guide lacks sampling rules"
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertFalse(got["parameters_verified"])
        self.assertTrue(got["unverified_parameters"])
        self.assertTrue(got["parameter_verification"]["openai_generic_schema"])

    def test_modifiers_are_parsed_and_missing_applicability_refused(self):
        docs=fixtures_documents()
        docs["openai_model"]=docs["openai_model"].replace("1.25x", "1.5x").replace(">272K", ">300K")
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertEqual(got["rates"]["openai"]["input_reservation_multiplier"],1.5)
        self.assertEqual(got["rates"]["openai"]["long_context_threshold_tokens"],300000)
        docs["openai_model"]=docs["openai_model"].replace("Cache writes are billed", "No described modifier")
        with self.assertRaises(P.ProviderError):P.refresh_official_evidence(docs_transport(docs))

    def test_explicit_unsupported_is_not_undocumented_or_false_positive_verified(self):
        docs=fixtures_documents()
        docs["openai_compatibility"]='### GPT-5.6 parameter compatibility\n temperature and top_p are not supported with reasoning effort none.\n'
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertFalse(got["parameters_verified"])
        self.assertEqual(got["public_parameter_support"]["openai"],"unsupported")
        self.assertEqual(len(got["explicitly_unsupported_parameters"]),2)
        self.assertFalse(got["unverified_parameters"])

    def test_non_none_restriction_does_not_claim_none_is_unsupported(self):
        docs=fixtures_documents()
        docs["openai_compatibility"]='### GPT-5.6 parameter compatibility\n When reasoning effort is not none, temperature and top_p are unsupported.\n'
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertEqual(got["public_parameter_support"]["openai"],"unverified")
        self.assertEqual(got["explicitly_unsupported_parameters"],[])

    def test_current_latest_other_family_rule_is_preserved_without_terra_inference(self):
        docs=fixtures_documents();docs["openai_compatibility"]="No model-specific statement."
        got=P.refresh_official_evidence(docs_transport(docs))
        self.assertEqual(got["latest_model_document_title"],"Using GPT-6")
        self.assertFalse(got["parameters_verified"])
        self.assertEqual(got["public_parameter_support"],{"openai":"unverified","anthropic":"documented"})
        self.assertEqual(got["explicitly_unsupported_parameters"],[])
        self.assertTrue(got["pilot_required_for_unverified_parameters"])
        self.assertTrue(any(s["url"].endswith("/latest-model.md") for s in got["sources"]))

    def test_claude_undocumented_or_explicit_unsupported_kept_distinct(self):
        for text,wanted in (("No Sonnet model-specific disabled example.","unverified"),
                            ('On Claude Sonnet 5, thinking disabled is not supported.',"unsupported")):
            docs=fixtures_documents();docs["anthropic_thinking"]=text
            got=P.refresh_official_evidence(docs_transport(docs))
            self.assertEqual(got["public_parameter_support"]["anthropic"],wanted)
            self.assertFalse(got["parameters_verified"])

    def test_unavailable_docs_block(self):
        with self.assertRaises(P.ProviderError):P.refresh_official_evidence(lambda req:P.HttpResponse(503,b"unavailable"))

if __name__=="__main__":
    unittest.main(verbosity=2)

