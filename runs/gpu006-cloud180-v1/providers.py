"""GPU006 single-attempt stdlib Batch transports. Controller owns approval/state."""
from __future__ import annotations
import dataclasses
import datetime as dt
import hashlib
import html
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request

MODELS = {"openai": "gpt-5.6-terra", "anthropic": "claude-sonnet-5"}
ORIGINS = {"openai": "https://api.openai.com", "anthropic": "https://api.anthropic.com"}
MAX_RESPONSE = 64 * 1024 * 1024

class ProviderError(RuntimeError):
    """Only safe local error codes; never server error text or credentials."""
    def __init__(self, code: str, status: int | None = None):
        self.code = code if re.fullmatch(r"[a-z0-9_]+", code) else "provider_error"
        self.status = status
        super().__init__("provider request blocked: " + self.code +
                         (f" (HTTP {status})" if status is not None else ""))

class SubmissionUnknown(ProviderError):
    """Create acceptance uncertain: persist SUBMISSION_UNKNOWN; never resend."""

@dataclasses.dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: dict = dataclasses.field(repr=False)
    body: bytes | None = dataclasses.field(default=None, repr=False)
    timeout: float = 60

@dataclasses.dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes = dataclasses.field(repr=False)
    headers: dict = dataclasses.field(default_factory=dict, repr=False)

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def http_transport(request: HttpRequest) -> HttpResponse:
    """One verified-TLS attempt; no redirects forwarding authentication."""
    req = urllib.request.Request(request.url, data=request.body,
                                 headers=request.headers, method=request.method)
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=request.timeout) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ProviderError("response_too_large")
            return HttpResponse(response.status, raw, dict(response.headers))
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        raise ProviderError("http_error", status) from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise ProviderError("transport_error") from None

def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def strict_json(raw: bytes):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ProviderError("duplicate_json_key")
            out[key] = value
        return out
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, TypeError, UnicodeError):
        raise ProviderError("malformed_json") from None

def validate_request(provider: str, row: dict) -> dict:
    if provider not in MODELS or not isinstance(row, dict):
        raise ProviderError("provider_or_request_mismatch")
    identifier = row.get("custom_id")
    if not isinstance(identifier, str) or not re.fullmatch(
        r"g006__" + provider + r"__(?:gemm|gesummv|syrk|syr2k|convolution-2d|convolution-3d)__(?:NONE|A40_NAME|L4_NAME|A40_SPEC|L4_SPEC)__r0[123]", identifier):
        raise ProviderError("custom_id_mismatch")
    if provider == "openai":
        if set(row) != {"body", "custom_id", "method", "url"} or row["method"] != "POST" or row["url"] != "/v1/responses":
            raise ProviderError("draft_endpoint_mismatch")
        body = row["body"]
        expected = {"model": MODELS[provider], "max_output_tokens": 8192,
                    "reasoning": {"effort": "none"}, "temperature": .2, "top_p": .9,
                    "tools": [], "tool_choice": "none", "store": False,
                    "stream": False, "truncation": "disabled"}
        if not isinstance(body, dict) or set(body) != set(expected) | {"input"} or any(body[k] != v for k, v in expected.items()):
            raise ProviderError("fixed_settings_mismatch")
        messages = body["input"]
    else:
        if set(row) != {"custom_id", "params"}:
            raise ProviderError("draft_schema_mismatch")
        body = row["params"]
        expected = {"model": MODELS[provider], "max_tokens": 8192,
                    "thinking": {"type": "disabled"}, "stream": False}
        if not isinstance(body, dict) or set(body) != set(expected) | {"system", "messages"} or any(body[k] != v for k, v in expected.items()):
            raise ProviderError("fixed_settings_mismatch")
        if not isinstance(body["system"], str):
            raise ProviderError("prompt_schema_mismatch")
        messages = body["messages"]
    if not isinstance(messages, list) or not messages or any(
        not isinstance(m, dict) or set(m) != {"role", "content"} or
        m["role"] not in ("system", "user") or not isinstance(m["content"], str) for m in messages):
        raise ProviderError("prompt_schema_mismatch")
    return body

def draft_rows(provider: str, payload: bytes) -> list[dict]:
    if provider == "openai":
        rows = [strict_json(line) for line in payload.splitlines() if line.strip()]
    else:
        obj = strict_json(payload)
        if not isinstance(obj, dict) or set(obj) != {"requests"}:
            raise ProviderError("draft_schema_mismatch")
        rows = obj["requests"]
    if not isinstance(rows, list) or not rows:
        raise ProviderError("empty_batch")
    ids = []
    for row in rows:
        validate_request(provider, row)
        ids.append(row["custom_id"])
    if len(set(ids)) != len(ids):
        raise ProviderError("duplicate_custom_id")
    return rows

class Provider:
    def __init__(self, provider: str, key: str, transport=None):
        if provider not in MODELS:
            raise ProviderError("unsupported_provider")
        if not isinstance(key, str) or not key or any(ord(c) < 33 or ord(c) > 126 for c in key):
            raise ProviderError("invalid_key_input")
        self.provider, self._key = provider, key
        self._transport = transport or http_transport
        self.last_response = None

    def __repr__(self):
        return f"Provider({self.provider!r}, key=<hidden>)"

    def _raw(self, method, path, body=None, content_type="application/json", creating=False):
        # No synchronous generation endpoint is present in this allowlist.
        reads = r"/v1/(?:models/[A-Za-z0-9_.-]+|(?:messages/)?batches(?:/[A-Za-z0-9_-]+)?|files/[A-Za-z0-9_-]+/content|messages/batches/[A-Za-z0-9_-]+/results)(?:\?[^#]*)?"
        writes = {"/v1/responses/input_tokens", "/v1/messages/count_tokens",
                  "/v1/files", "/v1/batches", "/v1/messages/batches"}
        if not ((method == "GET" and re.fullmatch(reads, path)) or (method == "POST" and path in writes)):
            raise ProviderError("endpoint_not_allowed")
        headers = {"Content-Type": content_type, "Accept": "application/json"}
        if self.provider == "openai":
            headers["Authorization"] = "Bearer " + self._key
        else:
            headers.update({"x-api-key": self._key, "anthropic-version": "2023-06-01"})
        try:
            response = self._transport(HttpRequest(method, ORIGINS[self.provider] + path, headers, body))
            if not isinstance(response, HttpResponse):
                raise ProviderError("invalid_transport_response")
            if not 200 <= response.status < 300:
                raise ProviderError("http_error", response.status)
            if self._key.encode() in response.body:
                raise ProviderError("secret_echo_blocked")
            self.last_response = response.body
            return response.body
        except ProviderError as exc:
            if creating and (exc.status is None or exc.status >= 500 or exc.status in (408, 409)):
                raise SubmissionUnknown(exc.code, exc.status) from None
            raise
        except Exception:
            if creating:
                raise SubmissionUnknown("transport_error") from None
            raise ProviderError("transport_error") from None

    def _json(self, method, path, value=None, creating=False):
        raw = self._raw(method, path, canonical(value) if value is not None else None, creating=creating)
        try:
            obj = strict_json(raw)
            if not isinstance(obj, dict):
                raise ProviderError("response_schema_mismatch")
            return obj
        except ProviderError as exc:
            if creating:
                raise SubmissionUnknown(exc.code) from None
            raise

    def preflight(self, requests: list[dict]) -> dict:
        """GET model and count every exact prompt; never generate a candidate."""
        bodies = [validate_request(self.provider, row) for row in requests]
        ids = [row["custom_id"] for row in requests]
        if not ids or len(set(ids)) != len(ids):
            raise ProviderError("empty_or_duplicate_preflight")
        model = MODELS[self.provider]
        info = self._json("GET", "/v1/models/" + model)
        if info.get("id") != model:
            raise ProviderError("model_permission_mismatch")
        if self.provider == "anthropic":
            caps = info.get("capabilities") or {}
            if caps.get("batch", {}).get("supported") is not True or caps.get("thinking", {}).get("types", {}).get("disabled", {}).get("supported") is not True:
                raise ProviderError("model_capabilities_mismatch")
            if type(info.get("max_tokens")) is not int or info["max_tokens"] < 8192:
                raise ProviderError("model_output_limit_mismatch")
        evidence, counts = [{"kind": "model", "body": info}], {}
        for identifier, body in zip(ids, bodies):
            # Count schema projection excludes generation-only controls. Nothing
            # is removed from the actual frozen draft submitted to Batch.
            fields = ("model", "input", "reasoning", "tools", "tool_choice", "truncation") if self.provider == "openai" else ("model", "system", "messages", "thinking")
            counted = {k: body[k] for k in fields}
            path = "/v1/responses/input_tokens" if self.provider == "openai" else "/v1/messages/count_tokens"
            result = self._json("POST", path, counted)
            count = result.get("input_tokens")
            if type(count) is not int or count <= 0:
                raise ProviderError("invalid_input_token_count")
            if self.provider == "openai" and result.get("object") != "response.input_tokens":
                raise ProviderError("token_count_response_mismatch")
            maximum = 922000 if self.provider == "openai" else info.get("max_input_tokens")
            if type(maximum) is not int or count + 8192 > maximum:
                raise ProviderError("input_context_limit_exceeded")
            counts[identifier] = count
            evidence.append({"kind": "input_tokens", "custom_id": identifier, "body": result,
                             "count_body_sha256": hashlib.sha256(canonical(counted)).hexdigest()})
        return {"provider": self.provider, "model": model, "input_tokens": counts,
                "permission": {"model_retrievable": True, "token_count_authorized": True,
                               "batch_create_permission_not_probed": True},
                "raw_evidence": evidence}

    def submit(self, payload: bytes, metadata: dict) -> dict:
        rows = draft_rows(self.provider, payload)
        if len(rows) not in (1, 29, 30) or len({r["custom_id"][-3:] for r in rows}) != 1:
            raise ProviderError("frozen_trial_batch_scope_mismatch")
        if self.provider == "openai":
            boundary = "gpu006" + secrets.token_hex(16)
            multipart = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n"
                         f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"gpu006.jsonl\"\r\n"
                         "Content-Type: application/jsonl\r\n\r\n").encode() + payload + f"\r\n--{boundary}--\r\n".encode()
            # Upload does not start generation; orphan uploads are harmless.
            uploaded = strict_json(self._raw("POST", "/v1/files", multipart,
                                  "multipart/form-data; boundary=" + boundary))
            if not isinstance(uploaded, dict) or not re.fullmatch(r"file-[A-Za-z0-9_-]+", uploaded.get("id", "")):
                raise ProviderError("file_upload_response_mismatch")
            batch = self._json("POST", "/v1/batches", {"input_file_id": uploaded["id"],
                "endpoint": "/v1/responses", "completion_window": "24h", "metadata": metadata}, creating=True)
        else:
            raw = self._raw("POST", "/v1/messages/batches", payload, creating=True)
            try:
                batch = strict_json(raw)
            except ProviderError:
                raise SubmissionUnknown("malformed_create_response") from None
        if not isinstance(batch, dict) or not self._valid_batch_id(batch.get("id")):
            raise SubmissionUnknown("missing_batch_id")
        return batch

    def _valid_batch_id(self, identifier):
        return isinstance(identifier, str) and bool(re.fullmatch(
            r"batch_[A-Za-z0-9_-]+" if self.provider == "openai" else r"msgbatch_[A-Za-z0-9_-]+", identifier))

    def retrieve(self, batch_id: str) -> dict:
        if not self._valid_batch_id(batch_id):
            raise ProviderError("invalid_batch_id")
        path = "/v1/batches/" if self.provider == "openai" else "/v1/messages/batches/"
        batch = self._json("GET", path + batch_id)
        if batch.get("id") != batch_id:
            raise ProviderError("retrieved_batch_id_mismatch")
        return batch

    def list_batches(self) -> list[dict]:
        path = "/v1/batches" if self.provider == "openai" else "/v1/messages/batches"
        batches, cursor, seen = [], None, set()
        for _ in range(1000):
            query = {"limit": 100}
            if cursor:
                query["after" if self.provider == "openai" else "after_id"] = cursor
            page = self._json("GET", path + "?" + urllib.parse.urlencode(query))
            data = page.get("data")
            if not isinstance(data, list) or any(not isinstance(b, dict) or not self._valid_batch_id(b.get("id")) for b in data):
                raise ProviderError("batch_list_schema_mismatch")
            batches.extend(data)
            if not page.get("has_more"):
                return batches
            cursor = page.get("last_id") or (data[-1]["id"] if data else None)
            if not cursor or cursor in seen:
                raise ProviderError("batch_list_pagination_mismatch")
            seen.add(cursor)
        raise ProviderError("batch_list_limit_exceeded")

    def results(self, batch: dict) -> list[tuple[str, bytes]]:
        if not self._valid_batch_id(batch.get("id")):
            raise ProviderError("invalid_batch_id")
        files = []
        if self.provider == "openai":
            for kind in ("output", "error"):
                identifier = batch.get(kind + "_file_id")
                if identifier:
                    if not isinstance(identifier, str) or not re.fullmatch(r"file-[A-Za-z0-9_-]+", identifier):
                        raise ProviderError("invalid_result_file_id")
                    files.append((kind + ".jsonl", self._raw("GET", "/v1/files/" + identifier + "/content")))
        else:
            url = batch.get("results_url")
            if url:
                parsed = urllib.parse.urlsplit(url)
                path = "/v1/messages/batches/" + batch["id"] + "/results"
                if parsed.scheme != "https" or parsed.netloc != "api.anthropic.com" or parsed.path != path or parsed.query or parsed.fragment:
                    raise ProviderError("untrusted_results_url")
                files.append(("results.jsonl", self._raw("GET", path)))
        return files

    def verify_batch(self, batch: dict, payload: bytes, metadata: dict) -> bool:
        """Read-only reconciliation; IDs alone never prove an OpenAI body."""
        rows = draft_rows(self.provider, payload)
        if not self._valid_batch_id(batch.get("id")):
            return False
        if self.provider == "openai":
            if batch.get("endpoint") != "/v1/responses" or batch.get("metadata") != metadata:
                return False
            identifier = batch.get("input_file_id")
            if not isinstance(identifier, str) or not re.fullmatch(r"file-[A-Za-z0-9_-]+", identifier):
                return False
            return self._raw("GET", "/v1/files/" + identifier + "/content") == payload
        # Anthropic does not expose metadata/request-body downloads. Evidence is
        # narrower: ended exact IDs + exact-model success; local intent binds body.
        if batch.get("processing_status") != "ended":
            return False
        found, successes = [], 0
        for _, raw in self.results(batch):
            for line in raw.splitlines():
                if not line.strip():
                    continue
                item = strict_json(line)
                found.append(item.get("custom_id"))
                result = item.get("result", {})
                if result.get("type") == "succeeded":
                    if result.get("message", {}).get("model") != MODELS[self.provider]:
                        return False
                    successes += 1
        return successes > 0 and len(found) == len(rows) and len(set(found)) == len(found) and set(found) == {r["custom_id"] for r in rows}

def assess_api_acceptance(provider: str, row: dict | None, expected_request: dict,
                          batch_id: str, body_sha256: str | None = None,
                          terminal_batch: dict | None = None) -> dict:
    """Assess native request acceptance, never candidate format or GPU quality.

    Expected hashes identify the local frozen request. The caller must separately
    verify the remote Batch input/metadata binding before using this assessment.
    Missing returned settings stay unknown even after a native request succeeds.
    """
    expected = validate_request(provider, expected_request)
    prefix = "batch_" if provider == "openai" else "msgbatch_"
    if not isinstance(batch_id, str) or not re.fullmatch(prefix + r"[A-Za-z0-9_-]+", batch_id):
        raise ProviderError("invalid_acceptance_batch_id")
    if body_sha256 is not None and (not isinstance(body_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", body_sha256)):
        raise ProviderError("invalid_acceptance_body_hash")
    out = {"schema": "gpu006-api-acceptance-v1", "provider": provider, "status": "unknown",
           "accepted": False, "native_request_accepted": None,
           "custom_id": expected_request["custom_id"], "returned_custom_id": None,
           "batch_id": batch_id, "batch_request_id": None, "provider_request_id": None,
           "provider_response_id": None, "returned_model": None,
           "request": expected_request,
           "request_body_sha256": hashlib.sha256(canonical(expected)).hexdigest(),
           "submission_body_sha256": body_sha256, "settings": {}, "errors": [],
           "reason_codes": [], "candidate_status_used": False,
           "body_binding_scope": "expected frozen body; caller verifies remote Batch input binding",
           "parameter_influence": "not assessed"}

    def safe_field(value):
        return value if isinstance(value, str) and len(value) <= 256 and re.fullmatch(r"[A-Za-z0-9_.\[\]-]+", value) else None

    def setting(name, present, returned, wanted):
        if not present or returned is None:
            status = "unknown"
        elif type(returned) is not type(wanted) and not (type(returned) in (int, float) and type(wanted) in (int, float)):
            status = "mismatch"
        else:
            status = "match" if returned == wanted else "mismatch"
        out["settings"][name] = {"expected": wanted, "returned": returned if present else None,
                                "present": present, "status": status}

    fields = ("reasoning", "temperature", "top_p", "max_output_tokens") if provider == "openai" else ("thinking", "max_tokens")
    for field in fields:
        if field in ("reasoning", "thinking"):
            subkey = "effort" if field == "reasoning" else "type"
            setting(field + "." + subkey, False, None, expected[field][subkey])
            out["settings"][field + "." + subkey]["returned_object"] = None
        else:
            setting(field, False, None, expected[field])

    def parse_error(error, scope):
        if not error or not isinstance(error, dict):
            return
        code, param = safe_field(error.get("code")), safe_field(error.get("param"))
        kind = safe_field(error.get("type"))
        line = error.get("line")
        out["errors"].append({"scope": scope, "code": code, "param": param, "type": kind,
                              "line": line if type(line) is int else None})

    def classify_errors():
        fixed = set(expected) | {"reasoning.effort", "thinking.type"}
        for error in out["errors"]:
            param = error["param"] or ""
            # References sometimes qualify the parameter with the request body.
            param = re.sub(r"^(?:requests\[\d+\]\.params\.|body\.)", "", param)
            error_class = error["code"] or error["type"]
            if param in fixed and error_class in {
                "unsupported_parameter", "unsupported_value", "invalid_parameter", "invalid_value",
                "invalid_type", "invalid_request_error", "invalid_request", "validation_error",
                "parameter_not_supported"}:
                out.update(status="fixed_parameter_rejected", native_request_accepted=False)
                out["reason_codes"].append("explicit_fixed_parameter_error")
                return out
        out.update(status="other_api_error", native_request_accepted=False)
        out["reason_codes"].append("native_api_error")
        return out

    if row is None:
        # Only a single-request failed Batch can map an unscoped Batch validation
        # error to the expected pilot. Creation alone is never acceptance proof.
        if isinstance(terminal_batch, dict) and terminal_batch.get("id") == batch_id and terminal_batch.get("status") == "failed":
            counts = terminal_batch.get("request_counts")
            counts = counts if isinstance(counts, dict) else {}
            container = terminal_batch.get("errors")
            errors = container.get("data") if isinstance(container, dict) else []
            total = counts.get("total")
            single_count = total is None or type(total) is int and total in (0, 1)
            scoped = single_count and isinstance(errors, list) and errors and all(isinstance(error, dict) for error in errors) and (
                total == 1 and all(error.get("line") in (None, 1) for error in errors)
                or all(error.get("line") == 1 for error in errors))
            if scoped:
                for error in errors:
                    parse_error(error, "single_request_batch_validation")
                if out["errors"]:
                    return classify_errors()
        out["reason_codes"].append("no_native_request_result")
        return out
    if not isinstance(row, dict):
        out["reason_codes"].append("invalid_native_result")
        return out
    out["returned_custom_id"] = row.get("custom_id")
    out["batch_request_id"] = row.get("id")
    if row.get("custom_id") != expected_request["custom_id"]:
        out["reason_codes"].append("custom_id_mismatch")
        return out
    if provider == "openai":
        response = row.get("response") or {}
        if not isinstance(response, dict):
            out["reason_codes"].append("invalid_native_response")
            return out
        out["provider_request_id"] = response.get("request_id")
        parse_error(row.get("error"), "batch_request")
        body = response.get("body")
        if isinstance(body, dict):
            parse_error(body.get("error"), "native_response")
        if any(error and not isinstance(error, dict) for error in (
                row.get("error"), body.get("error") if isinstance(body, dict) else None)):
            out["reason_codes"].append("unparseable_native_error")
            return out
        if out["errors"]:
            # Expiration/cancellation says nothing about fixed parameter support.
            if any(error["code"] in ("batch_expired", "batch_cancelled", "batch_canceled") for error in out["errors"]):
                out["reason_codes"].append("request_not_executed")
                return out
            return classify_errors()
        if type(response.get("status_code")) is not int or response.get("status_code") != 200 or not isinstance(body, dict):
            code = response.get("status_code")
            if type(code) is int and 400 <= code <= 599:
                out.update(status="other_api_error", native_request_accepted=False)
                out["reason_codes"].append("native_http_error")
            else:
                out["reason_codes"].append("no_successful_native_http_result")
            return out
        native_success = body.get("status") in ("completed", "incomplete")
        fields = ("reasoning", "temperature", "top_p", "max_output_tokens")
    else:
        result = row.get("result") or {}
        if not isinstance(result, dict):
            out["reason_codes"].append("invalid_native_result")
            return out
        if result.get("type") == "errored":
            parse_error(result.get("error"), "batch_request")
            return classify_errors() if out["errors"] else out
        body = result.get("message")
        if result.get("type") != "succeeded" or not isinstance(body, dict):
            out["reason_codes"].append("no_successful_native_result")
            return out
        native_success = body.get("type") == "message"
        fields = ("thinking", "max_tokens")
    out.update(provider_response_id=body.get("id"), returned_model=body.get("model"))
    for field in fields:
        if field in ("reasoning", "thinking"):
            subkey = "effort" if field == "reasoning" else "type"
            value = body.get(field)
            present = isinstance(value, dict) and subkey in value
            setting(field + "." + subkey, present, value.get(subkey) if isinstance(value, dict) else None, expected[field][subkey])
            # Preserve the actual native object; extra fields do not imply that
            # the requested effort/type was rejected or influenced the output.
            out["settings"][field + "." + subkey]["returned_object"] = value if field in body else None
            if field in body and value is not None and not isinstance(value, dict):
                out["settings"][field + "." + subkey].update(present=True, returned=value, status="mismatch")
        else:
            setting(field, field in body, body.get(field), expected[field])
    if body.get("model") != expected["model"]:
        out["reason_codes"].append("returned_model_mismatch")
        return out
    if any(value["status"] == "mismatch" for value in out["settings"].values()):
        out["native_request_accepted"] = bool(native_success)
        out["reason_codes"].append("returned_fixed_parameter_mismatch")
        return out
    if not native_success or not isinstance(body.get("id"), str) or not body["id"]:
        out["reason_codes"].append("no_native_response_acceptance_proof")
        return out
    out.update(status="accepted", accepted=True, native_request_accepted=True)
    out["reason_codes"].append("native_request_succeeded_with_fixed_model")
    return out

def normalize_result(provider: str, row: dict) -> dict:
    if provider not in MODELS or not isinstance(row, dict) or not isinstance(row.get("custom_id"), str):
        raise ProviderError("invalid_result_row")
    out = {"id": row["custom_id"], "generation_status": "api_error", "candidate_text": None,
           "usage": {}, "raw_usage": None, "provider_response_id": None, "model": None,
           "provider_anomaly": False}

    def response_fields(body):
        if not isinstance(body, dict):
            raise ProviderError("invalid_result_body")
        out.update({"provider_response_id": body.get("id"), "model": body.get("model")})
        raw = body.get("usage")
        if raw is not None and not isinstance(raw, dict):
            raise ProviderError("usage_schema_mismatch")
        out["raw_usage"] = raw
        usage = raw if raw is not None else {}
        if provider == "openai":
            details = usage.get("input_tokens_details")
            output_details = usage.get("output_tokens_details")
            if details is not None and not isinstance(details, dict):
                raise ProviderError("usage_schema_mismatch")
            if output_details is not None and not isinstance(output_details, dict):
                raise ProviderError("usage_schema_mismatch")
            details, output_details = details or {}, output_details or {}
            cached = details.get("cached_tokens")
            creation = details.get("cache_write_tokens")
            reasoning = output_details.get("reasoning_tokens")
        else:
            cached = usage.get("cache_read_input_tokens")
            creation = usage.get("cache_creation_input_tokens")
            reasoning = usage.get("reasoning_tokens")
        out["usage"] = {"input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                        "cached_input_tokens": cached, "cache_creation_input_tokens": creation,
                        "reasoning_tokens": reasoning}
        if any(v is not None and (type(v) is not int or v < 0) for v in out["usage"].values()):
            raise ProviderError("usage_schema_mismatch")
        output = out["usage"]["output_tokens"]
        if output is not None and output > 8192:
            raise ProviderError("result_output_limit_mismatch")
        if out["model"] != MODELS[provider]:
            out.update({"generation_status": "model_mismatch", "provider_anomaly": True})
            return False
        return True

    if provider == "openai":
        error = row.get("error")
        if error:
            code = error.get("code") if isinstance(error, dict) else None
            out["generation_status"] = "expired" if code == "batch_expired" else "canceled" if code in ("batch_cancelled", "batch_canceled") else "api_error"
            return out
        response = row.get("response") or {}
        if not isinstance(response, dict):
            raise ProviderError("invalid_result_body")
        body = response.get("body") or {}
        if response.get("status_code") != 200 or not isinstance(body, dict):
            return out
        if not response_fields(body):
            return out
        if body.get("status") != "completed" or body.get("error") or body.get("incomplete_details"):
            out["generation_status"] = "incomplete"
            return out
        items = body.get("output")
        if not isinstance(items, list):
            out["generation_status"] = "format_rejected"
            return out
        texts = []
        for item in items:
            if not isinstance(item, dict):
                out["generation_status"] = "format_rejected"
                return out
            if item.get("type") == "reasoning":
                continue
            if item.get("type") != "message" or item.get("role") != "assistant" or item.get("status") not in (None, "completed"):
                out["generation_status"] = "format_rejected"
                return out
            contents = item.get("content")
            if not isinstance(contents, list):
                out["generation_status"] = "format_rejected"
                return out
            for content in contents:
                if not isinstance(content, dict) or content.get("type") != "output_text" or not isinstance(content.get("text"), str):
                    out["generation_status"] = "format_rejected"
                    return out
                texts.append(content["text"])
    else:
        result = row.get("result") or {}
        if not isinstance(result, dict):
            raise ProviderError("invalid_result_body")
        state = result.get("type")
        if state != "succeeded":
            out["generation_status"] = {"expired": "expired", "canceled": "canceled", "errored": "api_error"}.get(state, "api_error")
            return out
        body = result.get("message") or {}
        if not response_fields(body):
            return out
        if body.get("type") != "message":
            out["generation_status"] = "format_rejected"
            return out
        if body.get("stop_reason") != "end_turn":
            out["generation_status"] = "incomplete"
            return out
        contents = body.get("content")
        if not isinstance(contents, list):
            out["generation_status"] = "format_rejected"
            return out
        texts = []
        for content in contents:
            if not isinstance(content, dict) or content.get("type") != "text" or not isinstance(content.get("text"), str):
                out["generation_status"] = "format_rejected"
                return out
            texts.append(content["text"])
    # The pinned common response_text accepts exactly one text part.
    # Multiple parts/messages cannot be combined into a salvaged candidate.
    if len(texts) != 1 or not texts[0].strip():
        out["generation_status"] = "format_rejected"
        return out
    out.update({"generation_status": "saved", "candidate_text": texts[0]})
    return out

def refresh_official_evidence(transport=None) -> dict:
    """Fresh public evidence; native acceptance requires an approved Batch pilot."""
    urls = {
        "openai_model": "https://developers.openai.com/api/docs/models/gpt-5.6-terra.md",
        "openai_batch": "https://developers.openai.com/api/docs/guides/batch.md",
        "openai_schema": "https://developers.openai.com/api/reference/python/resources/responses/methods/create",
        "openai_compatibility": "https://developers.openai.com/api/docs/guides/latest-model/gpt-5.6.md",
        "openai_latest": "https://developers.openai.com/api/docs/guides/latest-model.md",
        "openai_batch_schema": "https://developers.openai.com/api/reference/resources/batches/methods/create",
        "anthropic_model": "https://platform.claude.com/docs/en/models/sonnet-5/overview",
        "anthropic_pricing": "https://platform.claude.com/docs/en/about-claude/pricing",
        "anthropic_thinking": "https://platform.claude.com/docs/en/build-with-claude/thinking",
    }
    documents, sources = {}, []
    fetch = transport or http_transport
    for kind, url in urls.items():
        try:
            response = fetch(HttpRequest("GET", url, {"User-Agent": "Mozilla/5.0", "Accept": "text/html, text/markdown"}, timeout=30))
            if response.status != 200:
                raise ProviderError("official_docs_unavailable", response.status)
            text = response.body.decode("utf-8")
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("official_docs_unavailable") from None
        if "<html" in text.lower():
            text = html.unescape(re.sub(r"<[^>]+>", " ", text))
        documents[kind] = text
        sources.append({"kind": kind, "url": url, "sha256": hashlib.sha256(response.body).hexdigest(), "bytes": len(response.body)})
    om = documents["openai_model"]
    if not re.search(r"Model ID:\s*\x60gpt-5\.6-terra\x60", om) or not re.search(r"Reasoning\.effort supports:[^\n]*\bnone\b", om):
        raise ProviderError("official_model_settings_mismatch")
    def rate(metric):
        m = re.search(r"\|\s*" + re.escape(metric) + r"\s*\|\s*\$([0-9.]+)\s*\|\s*1M tokens\s*\|", om)
        if not m:
            raise ProviderError("official_rate_unverified")
        return float(m.group(1))
    inp, cached, output = rate("Input"), rate("Cached input"), rate("Output")
    cache_write = re.search(r"Cache writes are billed at ([0-9.]+)x the uncached input token rate", om)
    long_context = re.search(r"Prompts with >([0-9.]+)K input tokens are priced at ([0-9.]+)x input and ([0-9.]+)x output for the full request", om)
    if not cache_write or not long_context:
        raise ProviderError("official_rate_modifiers_unverified")
    cw = float(cache_write[1])
    threshold, li, lo = int(float(long_context[1]) * 1000), float(long_context[2]), float(long_context[3])
    if min(inp, output, cached, cw, li, lo) <= 0 or threshold <= 0:
        raise ProviderError("official_rate_modifiers_unverified")
    if "50%" not in documents["openai_batch"] or "/v1/responses" not in documents["openai_batch"]:
        raise ProviderError("official_batch_support_unverified")
    schema = documents["openai_schema"]
    if any(field not in schema for field in ("temperature", "top_p", "max_output_tokens", "tool_choice", "truncation", "store", "stream", "reasoning")):
        raise ProviderError("official_parameters_unverified")
    ap = documents["anthropic_pricing"]
    batch = ap.split("### Batch processing", 1)
    if len(batch) != 2:
        raise ProviderError("official_rate_unverified")
    match = re.search(r"\|\s*Claude Sonnet 5\s*\|\s*\$([0-9.]+)\s*/\s*MTok\s*\|\s*\$([0-9.]+)\s*/\s*MTok", batch[1])
    if not match or not re.search(r"(?<![A-Za-z0-9_-])claude-sonnet-5(?![A-Za-z0-9_-])", documents["anthropic_model"]):
        raise ProviderError("official_rate_or_model_unverified")
    ain, aout = float(match[1]), float(match[2])
    base_row = re.search(r"\|\s*Claude Sonnet 5\s*\|[^\n]+", batch[0])
    caching = re.findall(r"\$([0-9.]+)\s*/\s*MTok", base_row.group()) if base_row else []
    if len(caching) != 5 or "stack with other pricing modifiers" not in ap:
        raise ProviderError("official_cache_applicability_unverified")
    # Standard pricing table columns: input, 5m write, 1h write, read, output.
    acached = float(caching[3]) / 2
    thinking = documents["anthropic_thinking"]
    off = thinking.find("On Claude Sonnet 5,")
    example = thinking[off:off+1500] if off >= 0 else ""
    thinking_documented = bool(re.search(r'"model":\s*"claude-sonnet-5"', example) and re.search(r'"thinking":\s*\{\s*"type":\s*"disabled"\s*\}', example))
    thinking_unsupported = bool(re.search(r"disabled.{0,50}(?:not supported|unsupported)|(?:not supported|unsupported).{0,50}disabled", example, re.I))
    anthropic_support = "unsupported" if thinking_unsupported else "documented" if thinking_documented else "unverified"
    # Generic schema fields, exact-family statements, and another current
    # family's compatibility rules are different kinds of public evidence.
    guide = documents["openai_compatibility"]
    compatibility = re.search(r"(?is)#{2,4}\s+GPT-5\.6 parameter compatibility\s*\n(.*?)(?=\n#{1,4}\s|\Z)", guide)
    section = compatibility[1] if compatibility else ""
    negative = r"not\s+supported|unsupported|cannot\s+be\s+used|returns?\s+(?:a\s+)?400|reject(?:ed|s)?"
    def sampling_support(parameter):
        statements = re.split(r"(?<=[.!?])\s+|\n", om + "\n" + section)
        for statement in statements:
            if parameter not in statement or not re.search(negative, statement, re.I):
                continue
            # A restriction at a non-none effort is not a contradiction of this
            # frozen none request. Never infer incompatibility from that clause.
            non_none = re.search(r"(?:not|other\s+than)\s+[\"'`]*none|effort[^\n]{0,30}\b(?:low|medium|high|xhigh|max)\b", statement, re.I)
            if non_none:
                continue
            if "reasoning" not in statement.lower() or re.search(r"(?:reasoning(?:\.effort)?|effort).{0,80}\bnone\b", statement, re.I):
                return "unsupported"
        for statement in re.split(r"(?<=[.!?])\s+|\n", om + "\n" + section):
            if parameter in statement and not re.search(negative, statement, re.I) and re.search(r"\bsupported\b|\brequire\b|\brequires\b", statement, re.I) and re.search(r"reasoning(?:\.effort|\s+effort).{0,100}\bnone\b", statement, re.I):
                return "documented"
        return "unverified"
    sampling_states = {parameter: sampling_support(parameter) for parameter in ("temperature", "top_p")}
    sampling_verified = all(state == "documented" for state in sampling_states.values())
    openai_support = ("unsupported" if "unsupported" in sampling_states.values()
                      else "documented" if sampling_verified else "unverified")
    public_support = {"openai": openai_support, "anthropic": anthropic_support}
    title_match = re.search(r"(?m)^#\s+([^\n]+)", documents["openai_latest"])
    latest_title = title_match[1].strip() if title_match else None
    unverified = [MODELS["openai"] + ": " + parameter + " with reasoning.effort=none"
                  for parameter, state in sampling_states.items() if state == "unverified"]
    unsupported = [MODELS["openai"] + ": " + parameter + " with reasoning.effort=none"
                   for parameter, state in sampling_states.items() if state == "unsupported"]
    if anthropic_support == "unverified":
        unverified.append(MODELS["anthropic"] + ": thinking.type=disabled")
    elif anthropic_support == "unsupported":
        unsupported.append(MODELS["anthropic"] + ": thinking.type=disabled")
    rates = {
        "openai": {"model": MODELS["openai"], "input_usd_per_mtok": inp/2, "output_usd_per_mtok": output/2,
                   "cached_input_usd_per_mtok": cached/2, "cache_write_input_usd_per_mtok": inp*cw/2,
                   "input_reservation_multiplier": max(1.0,cw),
                   "long_context_threshold_tokens": threshold, "long_context_input_multiplier": li,
                   "long_context_output_multiplier": lo},
        "anthropic": {"model": MODELS["anthropic"], "input_usd_per_mtok": ain,
                      "output_usd_per_mtok": aout, "cached_input_usd_per_mtok": acached,
                      "cache_write_5m_input_usd_per_mtok": float(caching[1])/2,
                      "cache_write_1h_input_usd_per_mtok": float(caching[2])/2,
                      "input_reservation_multiplier": 1.0}}
    facts = [
        {"source_kind":"openai_model", "fact":"The requested model supports reasoning effort none. Standard token prices and full-request long-context/cache-write modifiers were parsed from this model's current page."},
        {"source_kind":"openai_batch", "fact":"Responses requests are accepted in Batch with half the synchronous rate."},
        {"source_kind":"openai_schema", "fact":"The generic Responses schema exposes every frozen parameter; this alone does not prove the named model accepts sampling controls."},
        {"source_kind":"openai_compatibility", "fact":"Exact-family sampling compatibility " + ("documented." if openai_support == "documented" else "explicitly unsupported in a model-specific statement." if openai_support == "unsupported" else "not established by this fetched guide; fixed sampling controls remain unverified.")},
        {"source_kind":"anthropic_pricing", "fact":"The exact Sonnet 5 Batch row and standard caching row were parsed; default global routing applies and caching discounts are not reserved."},
        {"source_kind":"anthropic_thinking", "fact":"Sonnet 5 disabled-thinking public support is " + anthropic_support + "; only the named model's explicit statement or example is used."},
        {"source_kind":"openai_latest", "fact":"The latest-model guide title is " + (latest_title or "unknown") + "; another family's rules do not establish Terra parameter compatibility."},
        {"source_kind":"openai_batch_schema", "fact":"Native Batch validation errors expose code, line, and parameter; creation itself does not establish per-request API acceptance."},
    ]
    return {"schema":"gpu006-official-api-evidence-v1", "verified_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "sources":sources, "supporting_facts":facts, "rates":rates, "parameters_verified":sampling_verified and thinking_documented and not thinking_unsupported,
            "public_parameter_support":public_support, "latest_model_document_title":latest_title,
            "explicitly_unsupported_parameters":unsupported,
            "pilot_required_for_unverified_parameters":bool(unverified),
            "parameter_verification":{"openai_generic_schema":True, "openai_reasoning_none":True,
                                      "openai_model_sampling_at_none":sampling_verified, "anthropic_thinking_disabled":thinking_documented and not thinking_unsupported,
                                      "openai_sampling_controls":sampling_states},
            "unverified_parameters":unverified,
            "parameter_verification_scope":"Public documentation only. Undocumented GPT controls may be quoted only with an approval-bound Batch pilot; native request acceptance is recorded separately. No synchronous probe or claim of parameter influence.",
            "routing":"first-party default global endpoints; no regional or priority settings",
            "cache_assumptions":"No cache discount reserved. OpenAI cache-write input multiplier reserved; Anthropic drafts do not enable caching.",
            "permission_checks_executed":False, "token_counts_executed":False, "paid_generation_calls":0}
