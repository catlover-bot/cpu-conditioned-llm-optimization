"""Preregistered, local-only Ollama acquisition; model text is never executed.

The raw generation API receives one explicitly rendered ChatML input. Technical
preflights and first experimental answers have separate append-only directories.
Neither selection validity nor measured kernel performance changes generation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from http.client import IncompleteRead
import ipaddress
import json
import os
from pathlib import Path
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


SCHEMA = "cpucond.ollama-local.v1"
SYSTEM = ("Choose one supplied option using only the supplied task. Return exactly the JSON object "
          "specified by the task, without Markdown or additional text. Do not use tools or prior answers.")
CHAT_TEMPLATE = ("<|im_start|>system\n{system}<|im_end|>\n"
                 "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n")
DEFAULT_OPTIONS = {"temperature": 0.2, "num_ctx": 16384, "num_predict": 512,
                   "num_gpu": 0, "num_thread": 8, "num_batch": 512,
                   "top_k": 40, "top_p": 0.9, "min_p": 0.0,
                   "repeat_penalty": 1.0, "repeat_last_n": 64, "typical_p": 1.0,
                   "presence_penalty": 0.0, "frequency_penalty": 0.0,
                   "num_keep": 4, "use_mmap": True, "draft_num_predict": 4,
                   "stop": ["<|im_end|>", "<|endoftext|>"]}
DEFAULT_SEEDS = [31001, 31002, 31003, 31004, 31005]
USAGE_FIELDS = ("prompt_eval_count", "prompt_eval_cached_count", "eval_count", "total_duration",
                "load_duration", "prompt_eval_duration", "eval_duration")
OFFICIAL_SIMPLE_TEMPLATE_SUFFIX = ("{{- else }}\n{{- if .System }}<|im_start|>system\n"
    "{{ .System }}<|im_end|>\n{{ end }}{{ if .Prompt }}<|im_start|>user\n"
    "{{ .Prompt }}<|im_end|>\n{{ end }}<|im_start|>assistant\n"
    "{{ end }}{{ .Response }}{{ if .Response }}<|im_end|>{{ end }}")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value if isinstance(value, bytes) else _json(value))


def _read(path):
    return json.loads(Path(path).read_bytes())


def _endpoint(value):
    parsed = urlsplit(value)
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Ollama endpoint must use a numeric loopback address") from exc
    if (parsed.scheme != "http" or not address.is_loopback or not port or
            parsed.username or parsed.password or parsed.path not in ("", "/") or
            parsed.query or parsed.fragment):
        raise ValueError("Ollama endpoint must be an HTTP loopback origin with explicit port")
    return value.rstrip("/")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Ollama redirects are forbidden")


class APIError(RuntimeError):
    def __init__(self, message, *, raw=None, status=None):
        super().__init__(message)
        self.raw = raw
        self.status = status


class OllamaClient:
    """No DNS, proxy, redirect, remote host, or tool-capable client path."""

    def __init__(self, endpoint, timeout=1800):
        self.endpoint = _endpoint(endpoint)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("HTTP timeout must be positive")
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _call(self, path, payload=None):
        if path not in ("/api/version", "/api/tags", "/api/show", "/api/ps", "/api/generate"):
            raise ValueError("unsupported Ollama API operation")
        request = Request(self.endpoint + path, data=None if payload is None else _json(payload),
                          headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            raise APIError(f"HTTP {exc.code}", raw=exc.read(), status=exc.code) from exc
        except IncompleteRead as exc:
            raise APIError("incomplete HTTP response", raw=exc.partial) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise APIError(f"{type(exc).__name__}: {exc}") from exc
        try:
            parsed = json.loads(raw)
        except (UnicodeDecodeError, ValueError) as exc:
            raise APIError("API returned invalid JSON", raw=raw, status=200) from exc
        if type(parsed) is not dict:
            raise APIError("API response must be one object", raw=raw, status=200)
        return raw, parsed

    def get(self, path):
        return self._call(path)

    def post(self, path, payload):
        return self._call(path, payload)


def server_evidence(endpoint, pid):
    """Inspect the actual serving process, its environment and owned listener."""
    endpoint = _endpoint(endpoint)
    parsed = urlsplit(endpoint)
    process = Path("/proc") / str(int(pid))
    if int(pid) <= 0:
        raise ValueError("invalid server PID")
    environment = {}
    for item in (process / "environ").read_bytes().split(b"\0"):
        if b"=" in item:
            key, value = item.split(b"=", 1)
            if key in (b"OLLAMA_NO_CLOUD", b"OLLAMA_HOST", b"OLLAMA_NUM_PARALLEL", b"OLLAMA_MAX_LOADED_MODELS"):
                environment[key.decode()] = value.decode("utf-8", errors="strict")
    if environment.get("OLLAMA_NO_CLOUD") != "1":
        raise ValueError("serving process does not have OLLAMA_NO_CLOUD=1")
    if environment.get("OLLAMA_NUM_PARALLEL") != "1":
        raise ValueError("serving process must fix OLLAMA_NUM_PARALLEL=1")
    cmdline = (process / "cmdline").read_bytes().split(b"\0")
    if b"serve" not in cmdline:
        raise ValueError("PID is not an Ollama serve process")
    executable = str((process / "exe").resolve(strict=True))
    if not Path(executable).name.startswith("ollama"):
        raise ValueError("server executable is not Ollama")
    inodes = set()
    for fd in (process / "fd").iterdir():
        try:
            target = os.readlink(fd)
        except (FileNotFoundError, PermissionError):
            continue
        if target.startswith("socket:["):
            inodes.add(target[8:-1])
    listeners = []
    for filename, family in (("tcp", socket.AF_INET), ("tcp6", socket.AF_INET6)):
        for line in (process / "net" / filename).read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] != "0A" or fields[9] not in inodes:
                continue
            host_hex, port_hex = fields[1].split(":")
            raw = bytes.fromhex(host_hex)
            raw = raw[::-1] if family == socket.AF_INET else b"".join(raw[i:i + 4][::-1] for i in range(0, 16, 4))
            host = socket.inet_ntop(family, raw)
            if not ipaddress.ip_address(host).is_loopback:
                raise ValueError("Ollama process owns a non-loopback listener")
            listeners.append({"address": host, "port": int(port_hex, 16)})
    if {"address": parsed.hostname, "port": parsed.port} not in listeners:
        raise ValueError("endpoint is not an owned loopback listener of the inspected process")
    return {"checked_utc": _now(), "pid": int(pid), "executable": executable,
            "executable_sha256": _sha(Path(executable).read_bytes()),
            "environment": environment, "listeners": listeners,
            "verification": "actual /proc serving-process environment and owned listening socket"}


def build_local_config(*, endpoint, model, digest, ollama_version, model_show, server_pid,
                       provenance, selection_reason, options=None, seeds=None):
    config = {"schema_version": SCHEMA, "endpoint": _endpoint(endpoint), "model": model,
              "model_digest": digest, "ollama_version": ollama_version,
              "server_pid": server_pid, "model_show": model_show,
              "model_show_sha256": _sha(_json(model_show)), "provenance": provenance,
              "selection_reason": selection_reason, "system": SYSTEM,
              "render_template": CHAT_TEMPLATE, "options": DEFAULT_OPTIONS if options is None else options,
              "seeds": DEFAULT_SEEDS if seeds is None else seeds, "stream": False,
              "raw": True, "format": "json", "keep_alive": "10m",
              "context_special_token_reserve": 32,
              "context_method": "UTF-8 byte upper bound for pinned GPT-2 byte-level BPE plus 32 special-token reserve; not an exact token count",
              "template_equivalence": "The explicit rendering matches the official Qwen template's no-Suffix/no-Messages branch with nonempty System/Prompt and empty Response. Raw mode prevents an additional hidden template.",
              "seed_limitations": "Paired fixed seeds do not guarantee exact reproducibility across runtime, hardware, or scheduling.",
              "preflight_policy": "All 20 prompts, same rendering and options except num_predict=1; technical responses never imported.",
              "retry_policy": "First acquired content is final even when invalid or truncated; transport failures are retained and retried only on explicit resume.",
              "protocol_change": "New local acquisition protocol adds fixed raw ChatML rendering, JSON output mode, model, seed and resource settings to unchanged blind tasks."}
    config = json.loads(_json(config))
    validate_config(config)
    return config


def validate_config(config):
    if config.get("schema_version") != SCHEMA:
        raise ValueError("unsupported local LLM protocol")
    _endpoint(config["endpoint"])
    if (config.get("render_template") != CHAT_TEMPLATE or config.get("system") != SYSTEM or
            config.get("raw") is not True or config.get("stream") is not False or config.get("format") != "json"):
        raise ValueError("local generation must use fixed independent raw ChatML and JSON output mode")
    if config.get("context_special_token_reserve") != 32:
        raise ValueError("context special-token reserve changed")
    options = config["options"]
    if set(options) != set(DEFAULT_OPTIONS):
        raise ValueError("generation options must explicitly fix every preregistered field")
    if options["num_gpu"] != 0:
        raise ValueError("this local pilot protocol requires CPU inference")
    if any(type(options[key]) is not int or options[key] <= 0 for key in ("num_ctx", "num_predict", "num_thread", "num_batch")):
        raise ValueError("context, output and CPU resources must be positive integers")
    seeds = config["seeds"]
    if not isinstance(seeds, list) or len(seeds) != 5 or len(set(seeds)) != 5 or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("exactly five distinct nonnegative seeds must be preregistered")
    if _sha(_json(config["model_show"])) != config["model_show_sha256"]:
        raise ValueError("saved Ollama model-show hash differs")
    info = config["model_show"].get("model_info", {})
    if info.get("general.architecture") != "qwen2" or info.get("tokenizer.ggml.model") != "gpt2":
        raise ValueError("context bound requires verified Qwen2 GPT-2 byte-level BPE metadata")
    if info.get("qwen2.context_length", 0) < options["num_ctx"]:
        raise ValueError("configured context exceeds model context limit")
    if not isinstance(config["model_digest"], str) or len(config["model_digest"].removeprefix("sha256:")) != 64:
        raise ValueError("model must be pinned by full digest")
    if not config["selection_reason"] or not isinstance(config["provenance"], dict):
        raise ValueError("model selection and distribution/license provenance are required")
    template = config["model_show"].get("template", "")
    if not template.endswith(OFFICIAL_SIMPLE_TEMPLATE_SUFFIX):
        raise ValueError("model's official simple ChatML template does not match the fixed raw rendering")


validate_local_config = validate_config


def render_chat(system, prompt):
    if any(marker in system or marker in prompt for marker in ("<|im_start|>", "<|im_end|>")):
        raise ValueError("source input contains a ChatML control delimiter")
    return CHAT_TEMPLATE.format(system=system, prompt=prompt)


def build_payload(config, request, prompt, *, preflight=False):
    validate_config(config)
    if _sha(prompt.encode("utf-8")) != request["prompt_sha256"]:
        raise ValueError("prompt hash differs from sealed request")
    options = {**config["options"], "seed": config["seeds"][request["trial"] - 1]}
    if preflight:
        options["num_predict"] = 1
    return {"model": config["model"], "prompt": render_chat(config["system"], prompt),
            "raw": True, "stream": False, "format": config["format"],
            "keep_alive": config["keep_alive"], "options": options}


def context_bound(config, request, prompt):
    payload = build_payload(config, request, prompt)
    rendered_bytes = len(payload["prompt"].encode("utf-8"))
    upper = rendered_bytes + config["context_special_token_reserve"]
    total = upper + config["options"]["num_predict"]
    if total > config["options"]["num_ctx"]:
        raise ValueError(f"context insufficient for complete input and output: {request['request_key']}: {total} > {config['options']['num_ctx']}")
    return {"request_key": request["request_key"], "prompt_sha256": request["prompt_sha256"],
            "rendered_input_sha256": _sha(payload["prompt"].encode("utf-8")),
            "rendered_utf8_bytes": rendered_bytes, "input_token_upper_bound": upper,
            "reserved_output_tokens": config["options"]["num_predict"],
            "required_context_upper_bound": total, "configured_context": config["options"]["num_ctx"],
            "method": config["context_method"], "exact_token_count": None,
            "proof": "GPT-2 byte-level BPE starts with one symbol per UTF-8 byte; merges cannot increase symbol count. Special delimiters compress to tokens; 32 additional tokens conservatively reserve automatic special tokens."}


def _context(directory):
    from .selection import check_static
    directory = Path(directory).resolve()
    check_static(directory)
    pilot = _read(directory / "pilot.json")
    protocol = _read(directory / "protocol.json")
    if pilot["cohort"] != "real" or protocol.get("acquisition_backend") != "ollama_local":
        raise ValueError("local acquisition requires a separate real ollama_local cohort")
    config = protocol["local_llm"]
    validate_config(config)
    return directory, pilot, protocol, config


def verify_runtime(config, client):
    evidence = server_evidence(config["endpoint"], config["server_pid"])
    raw_version, version = client.get("/api/version")
    if version.get("version") != config["ollama_version"]:
        raise ValueError("Ollama version changed from the preregistered runtime")
    raw_tags, tags = client.get("/api/tags")
    model = next((item for item in tags.get("models", []) if item.get("name") == config["model"]), None)
    if model is None or model.get("digest") != config["model_digest"]:
        raise ValueError("local model tag no longer resolves to the preregistered digest")
    raw_show, show = client.post("/api/show", {"model": config["model"]})
    if _sha(_json(show)) != config["model_show_sha256"]:
        raise ValueError("model template, parameters or metadata changed")
    return {"checked_utc": _now(), "server": evidence, "version": version, "model": model,
            "model_show_sha256": _sha(_json(show)),
            "api_sha256": {"version": _sha(raw_version), "tags": _sha(raw_tags), "show": _sha(raw_show)}}


def verify_loaded(config, client):
    raw, ps = client.get("/api/ps")
    models = ps.get("models", [])
    model = next((item for item in models if item.get("digest") == config["model_digest"]), None)
    if model is None:
        raise ValueError("selected model is absent from Ollama's loaded-model evidence")
    if len(models) != 1 or model.get("size_vram") != 0:
        raise ValueError("local CPU-only, one-model inference condition was not observed")
    if model.get("context_length") != config["options"]["num_ctx"]:
        raise ValueError("loaded model context differs from preregistered context")
    return raw, {"checked_utc": _now(), "device": "CPU", "api_ps": ps,
                 "interpretation": "Ollama /api/ps reports zero GPU allocation with num_gpu=0; model size is runtime-reported allocation, not measured process RSS."}


def runner_processes(server_pid):
    """Inspect descendants of this verified server; no process is killed."""
    records = {}
    for process in Path("/proc").iterdir():
        if not process.name.isdigit():
            continue
        try:
            fields = dict(line.split(":", 1) for line in (process / "status").read_text().splitlines() if ":" in line)
            records[int(process.name)] = {"pid": int(process.name), "parent_pid": int(fields["PPid"].strip()),
                                          "name": fields["Name"].strip()}
        except (OSError, KeyError, ValueError):
            continue
    descendants = {int(server_pid)}
    while True:
        found = {pid for pid, item in records.items() if item["parent_pid"] in descendants}
        new = found - descendants
        if not new:
            break
        descendants.update(new)
    return [records[pid] for pid in sorted(descendants - {int(server_pid)}) if pid in records]


def _next_attempt(parent):
    parent.mkdir(parents=True, exist_ok=True)
    entries = sorted(parent.iterdir())
    if any(path.is_symlink() or not path.is_dir() or path.name != f"attempt-{i:04d}" for i, path in enumerate(entries, 1)):
        raise ValueError("unexpected acquisition-attempt sequence")
    path = parent / f"attempt-{len(entries) + 1:04d}"
    path.mkdir()
    return path


def _capture(folder, client, payload, request, *, kind, expected_input_tokens=None):
    _save(folder / "payload.json", payload)
    started = _now()
    _save(folder / "started.json", {"kind": kind, "request_key": request["request_key"],
          "request_id": request["request_id"], "prompt_sha256": request["prompt_sha256"],
          "payload_sha256": _sha(_json(payload)), "started_utc": started,
          "expected_prompt_eval_count": expected_input_tokens})
    begin = time.monotonic()
    try:
        raw, result = client.post("/api/generate", payload)
        _save(folder / "api-response.raw.json", raw)
        if isinstance(result.get("response"), str):
            _save(folder / "response.raw", result["response"].encode("utf-8"))
            state = "acquired"
        else:
            state = "generation_failure"
        outcome = {"state": state, "obtained_utc": _now(), "wall_seconds": time.monotonic() - begin,
                   "timeout": False,
                   "api_response_sha256": _sha(raw), "error": result.get("error"),
                   "done": result.get("done"), "done_reason": result.get("done_reason"),
                   "output_truncated": result.get("done_reason") == "length" or result.get("done") is False,
                   "usage": {key: result[key] for key in USAGE_FIELDS if key in result}}
        if state == "acquired":
            outcome["response_sha256"] = _sha(result["response"].encode("utf-8"))
            if expected_input_tokens is not None:
                outcome["expected_prompt_eval_count"] = expected_input_tokens
                outcome["context_mismatch"] = result.get("prompt_eval_count") != expected_input_tokens
    except APIError as exc:
        if exc.raw is not None:
            _save(folder / "api-response.raw.json", exc.raw)
        outcome = {"state": "transport_failure" if exc.status != 200 else "generation_failure",
                   "obtained_utc": _now(), "wall_seconds": time.monotonic() - begin,
                   "error": str(exc), "http_status": exc.status,
                   "api_response_sha256": None if exc.raw is None else _sha(exc.raw),
                   "timeout": "timed out" in str(exc).lower() or "timeout" in str(exc).lower()}
    _save(folder / "outcome.json", outcome)
    return outcome


def _recover_attempt(folder):
    """Recover saved API bytes after interruption; never request another answer."""
    if (folder / "outcome.json").exists():
        return _read(folder / "outcome.json")
    outcome = {"state": "transport_failure", "obtained_utc": None, "recovered_utc": _now(), "wall_seconds": None,
               "error": "interrupted attempt; no complete API response was saved", "timeout": None,
               "recovered_after_interruption": True}
    api = folder / "api-response.raw.json"
    if api.exists():
        raw = api.read_bytes()
        outcome["api_response_sha256"] = _sha(raw)
        try:
            result = json.loads(raw)
            if isinstance(result.get("response"), str):
                content = result["response"].encode("utf-8")
                if (folder / "response.raw").exists():
                    if (folder / "response.raw").read_bytes() != content:
                        raise ValueError("saved response differs from API original")
                else:
                    _save(folder / "response.raw", content)
                outcome.update(state="acquired", error=None, response_sha256=_sha(content),
                    done=result.get("done"), done_reason=result.get("done_reason"),
                    output_truncated=result.get("done_reason") == "length" or result.get("done") is False,
                    usage={key: result[key] for key in USAGE_FIELDS if key in result})
                expected = _read(folder / "started.json").get("expected_prompt_eval_count")
                if expected is not None:
                    outcome["expected_prompt_eval_count"] = expected
                    outcome["context_mismatch"] = result.get("prompt_eval_count") != expected
            else:
                outcome.update(state="generation_failure", error=result.get("error", "API content missing"))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            outcome.update(state="generation_failure", error="saved API response is invalid JSON")
    _save(folder / "outcome.json", outcome)
    return outcome


def _metadata(config, request, folder, outcome):
    return {"cohort": "real", "acquisition_method": "api_export",
            "model_identifier": config["model"] + "@" + config["model_digest"],
            "obtained_at": outcome["obtained_utc"], "prompt_hash": request["prompt_sha256"],
            "generation_settings": _read(folder / "payload.json")["options"],
            "usage": {**outcome["usage"], "done": outcome.get("done"), "done_reason": outcome.get("done_reason"),
                      "output_truncated": outcome.get("output_truncated"), "context_mismatch": outcome.get("context_mismatch", False)},
            "acquisition_source": f"Local Ollama {config['ollama_version']}; {config['endpoint']}; {folder.name}",
            "missing_reasons": {} if outcome["obtained_utc"] is not None else {"obtained_at": "Interrupted before reception timestamp was saved; recovery timestamp is recorded separately."},
            "blinding": {"independent_session": True, "no_tools": True,
            "no_prior_results": True, "limitations": ["Adapter payload and local runtime evidence are auditable; developer previously saw this task. No claim of an unseen benchmark or physical host isolation."]}}


def _import_captured(directory, config, request, folder, outcome):
    from .selection_responses import collect_responses, import_response
    if not (folder / "metadata.json").exists():
        _save(folder / "metadata.json", _metadata(config, request, folder, outcome))
    existing = [item for item in collect_responses(directory)["attempts"] if item["request_key"] == request["request_key"]]
    if existing:
        if len(existing) != 1 or existing[0]["raw_response_sha256"] != outcome["response_sha256"]:
            raise ValueError("local request has a conflicting imported answer")
        result = existing[0]
    else:
        result = import_response(directory, request["request_key"], folder / "response.raw", folder / "metadata.json")
    if not (folder / "import.json").exists():
        _save(folder / "import.json", {"imported_utc": _now(), "attempt_id": result["attempt_id"],
              "raw_response_sha256": result["raw_response_sha256"], "status": result["status"],
              "invalid_reason": result["invalid_reason"]})
    return result


def _load_preflight(directory, protocol, config):
    path = directory / "local-acquisition" / "preflight.json"
    if not path.exists():
        raise ValueError("all 20 technical preflights must pass before actual answers")
    saved = _read(path)
    if saved["protocol_sha256"] != _sha((directory / "protocol.json").read_bytes()) or not saved["passed"]:
        raise ValueError("preflight does not match this protocol")
    if [row["request_key"] for row in saved["requests"]] != [row["request_key"] for row in protocol["requests"]]:
        raise ValueError("preflight does not cover all 20 requests")
    for row, request in zip(saved["requests"], protocol["requests"]):
        prompt = (directory / request["prompt_path"]).read_text(encoding="utf-8")
        if row["bound"] != context_bound(config, request, prompt):
            raise ValueError("preflight context bound changed")
        folder = directory / row["attempt_path"]
        if (folder / "payload.json").read_bytes() != _json(build_payload(config, request, prompt, preflight=True)):
            raise ValueError("technical preflight payload differs from fixed complete input")
        if _sha((folder / "api-response.raw.json").read_bytes()) != row["api_response_sha256"]:
            raise ValueError("technical preflight original changed")
        api = _read(folder / "api-response.raw.json")
        if (type(api.get("prompt_eval_count")) is not int or api["prompt_eval_count"] <= 0 or
                api["prompt_eval_count"] != row["prompt_eval_count"] or
                api["prompt_eval_count"] > row["bound"]["input_token_upper_bound"]):
            raise ValueError("technical preflight count differs from API original or context bound")
    if _sha((directory / saved["loaded_ps_path"]).read_bytes()) != saved["loaded_ps_sha256"]:
        raise ValueError("preflight loaded-model original changed")
    return saved


def preflight_local(directory, *, timeout=1800):
    from .execution_gate import execution_gate
    from .selection import mutation_lock
    directory = Path(directory).resolve()
    with execution_gate("inference"), mutation_lock(directory):
        directory, pilot, protocol, config = _context(directory)
        if (directory / "freeze.json").exists():
            raise ValueError("local answers already frozen")
        if (directory / "local-acquisition/preflight.json").exists():
            return _load_preflight(directory, protocol, config)
        client = OllamaClient(config["endpoint"], timeout)
        runtime = verify_runtime(config, client)
        bounds = [context_bound(config, item, (directory / item["prompt_path"]).read_text(encoding="utf-8")) for item in protocol["requests"]]
        rows = []
        for request, bound in zip(protocol["requests"], bounds):
            parent = directory / "local-acquisition" / "technical-preflight" / request["request_key"]
            completed = []
            if parent.exists():
                for old in sorted(parent.iterdir()):
                    outcome = _recover_attempt(old)
                    if outcome["state"] == "acquired":
                        completed.append((old, outcome))
            if completed:
                folder, outcome = completed[0]
            else:
                folder = _next_attempt(parent)
                payload = build_payload(config, request, (directory / request["prompt_path"]).read_text(encoding="utf-8"), preflight=True)
                outcome = _capture(folder, client, payload, request, kind="technical_preflight_not_experimental")
            actual = outcome.get("usage", {}).get("prompt_eval_count")
            if outcome["state"] != "acquired" or type(actual) is not int or actual <= 0 or actual > bound["input_token_upper_bound"]:
                raise ValueError(f"technical preflight failed or contradicts context bound: {request['request_key']}")
            rows.append({"request_key": request["request_key"], "bound": bound, "prompt_eval_count": actual,
                         "attempt_path": str(folder.relative_to(directory)), "api_response_sha256": outcome["api_response_sha256"]})
        result = {"passed": True, "completed_utc": _now(), "protocol_sha256": _sha((directory / "protocol.json").read_bytes()),
                  "runtime": runtime, "requests": rows,
                  "interpretation": "Full rendered input plus reserved output fits a conservative tokenizer bound for every request; API token counts corroborate, but are not inferred from character counts. Technical outputs are excluded."}
        raw_ps, loaded = verify_loaded(config, client)
        completion = _next_attempt(directory / "local-acquisition/preflight-completions")
        _save(completion / "loaded-ps.raw.json", raw_ps)
        _save(completion / "loaded-runtime.json", loaded)
        result["loaded_runtime"] = loaded
        result["loaded_ps_sha256"] = _sha(raw_ps)
        result["loaded_ps_path"] = str((completion / "loaded-ps.raw.json").relative_to(directory))
        _save(directory / "local-acquisition/preflight.json", result)
        return result


def run_local(directory, *, limit=None, timeout=1800):
    from .execution_gate import execution_gate
    from .selection import mutation_lock, pilot_status, write_json, _status_from
    from .selection_responses import collect_responses
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError("request limit must be a positive integer")
    directory = Path(directory).resolve()
    with execution_gate("inference"), mutation_lock(directory):
        directory, pilot, protocol, config = _context(directory)
        if (directory / "freeze.json").exists():
            raise ValueError("local answers already frozen")
        preflight = _load_preflight(directory, protocol, config)
        client = OllamaClient(config["endpoint"], timeout)
        runtime = verify_runtime(config, client)
        session = _next_attempt(directory / "local-acquisition/sessions")
        _save(session / "runtime.json", runtime)
        count, rows = 0, []
        for request, verified in zip(protocol["requests"], preflight["requests"]):
            parent = directory / "local-acquisition/requests" / request["request_key"]
            terminal = None
            if parent.exists():
                for folder in sorted(parent.iterdir()):
                    outcome = _recover_attempt(folder)
                    if outcome["state"] in ("acquired", "generation_failure"):
                        if terminal:
                            raise ValueError("multiple acquired answers for one local request")
                        terminal = (folder, outcome)
            if terminal:
                folder, outcome = terminal
            else:
                if limit is not None and count >= limit:
                    continue
                folder = _next_attempt(parent)
                payload = build_payload(config, request, (directory / request["prompt_path"]).read_text(encoding="utf-8"))
                outcome = _capture(folder, client, payload, request, kind="actual_local_llm_answer",
                                   expected_input_tokens=verified["prompt_eval_count"])
                count += 1
                if outcome["state"] == "acquired" and not (session / "loaded-runtime.json").exists():
                    raw_ps, loaded = verify_loaded(config, client)
                    _save(session / "loaded-ps.raw.json", raw_ps)
                    _save(session / "loaded-runtime.json", loaded)
            row = {"request_key": request["request_key"], "state": outcome["state"], "attempt_path": str(folder.relative_to(directory))}
            if outcome["state"] == "acquired":
                try:
                    imported = _import_captured(directory, config, request, folder, outcome)
                    row.update(import_status=imported["status"], output_truncated=outcome["output_truncated"])
                except (ValueError, OSError) as exc:
                    error_folder = _next_attempt(folder / "import-failures")
                    _save(error_folder / "error.json", {"occurred_utc": _now(), "error": str(exc)})
                    row.update(import_status="import_failure", error=str(exc))
                actual = outcome.get("usage", {}).get("prompt_eval_count")
                if actual != verified["prompt_eval_count"] and terminal is None:
                    _save(session / f"context-failure-{request['request_key']}.json", {"expected_prompt_eval_count": verified["prompt_eval_count"], "actual_prompt_eval_count": actual})
                    rows.append(row)
                    break
            rows.append(row)
        result = {"completed_utc": _now(), "new_api_requests": count, "requests": rows}
        _save(session / "session.json", result)
        pilot["llm_api_called"] = True
        pilot["status"] = _status_from(pilot, collect_responses(directory))
        write_json(directory / "pilot.json", pilot)
        return {**result, "pilot": pilot_status(directory)}


def assert_collection_complete(directory):
    directory, _, protocol, _ = _context(directory)
    rows = []
    for request in protocol["requests"]:
        parent = directory / "local-acquisition/requests" / request["request_key"]
        attempts = sorted(parent.iterdir()) if parent.exists() else []
        if not attempts or any(not (item / "outcome.json").exists() for item in attempts):
            raise ValueError("all 20 local requests must be attempted before freeze; resume remaining requests")
        outcomes = [_read(item / "outcome.json") for item in attempts]
        rows.append({"request_key": request["request_key"], "state": outcomes[-1]["state"], "attempt_count": len(attempts)})
    manifest = {str(path.relative_to(directory)): _sha(path.read_bytes()) for path in
                sorted((directory / "local-acquisition").rglob("*")) if path.is_file()}
    return {"all_requests_attempted": True, "requests": rows, "artifact_sha256": manifest}


def unload_local(directory, *, timeout=1800):
    from .execution_gate import execution_gate
    from .selection import mutation_lock
    directory = Path(directory).resolve()
    with execution_gate("inference"), mutation_lock(directory):
        directory, _, _, config = _context(directory)
        if (directory / "freeze.json").exists():
            raise ValueError("unload must be recorded before freeze; frozen acquisition evidence is immutable")
        client = OllamaClient(config["endpoint"], timeout)
        runtime = verify_runtime(config, client)
        folder = _next_attempt(directory / "local-acquisition/unloads")
        payload = {"model": config["model"], "keep_alive": 0}
        _save(folder / "payload.json", payload)
        raw, response = client.post("/api/generate", payload)
        _save(folder / "api-response.raw.json", raw)
        raw_ps, ps = client.get("/api/ps")
        _save(folder / "ps.raw.json", raw_ps)
        if ps.get("models") != []:
            raise ValueError("Ollama still has loaded models after unload")
        deadline = time.monotonic() + 10
        runners = runner_processes(config["server_pid"])
        while runners and time.monotonic() < deadline:
            time.sleep(0.1)
            runners = runner_processes(config["server_pid"])
        if runners:
            _save(folder / "remaining-runner-processes.json", runners)
            raise ValueError("Ollama runner processes have not exited after unload")
        evidence = {"checked_utc": _now(), "runtime": runtime, "models": [],
                    "runner_processes": runners,
                    "api_response_sha256": _sha(raw), "ps_sha256": _sha(raw_ps),
                    "interpretation": "No model loaded in verified Ollama server; existing warmup, load checks and quality warnings still apply."}
        _save(folder / "evidence.json", evidence)
        return {**evidence, "evidence_path": str((folder / "evidence.json").relative_to(directory))}


def assert_unloaded(directory):
    directory, _, _, config = _context(directory)
    parent = directory / "local-acquisition/unloads"
    if not parent.exists():
        raise ValueError("recorded local model unload is required before kernel measurement")
    candidates = sorted(parent.glob("attempt-*/evidence.json"))
    if not candidates:
        raise ValueError("no successful local model unload was recorded")
    evidence_path = candidates[-1]
    evidence = _read(evidence_path)
    if _sha((evidence_path.parent / "ps.raw.json").read_bytes()) != evidence["ps_sha256"]:
        raise ValueError("unload evidence changed")
    client = OllamaClient(config["endpoint"], 30)
    runtime = verify_runtime(config, client)
    raw, ps = client.get("/api/ps")
    if ps.get("models") != []:
        raise ValueError("inference model is loaded; kernel measurement is forbidden")
    runners = runner_processes(config["server_pid"])
    if runners:
        raise ValueError("Ollama runner process exists; kernel measurement is forbidden")
    return {"checked_utc": _now(), "models": [], "runtime": runtime,
            "runner_processes": runners,
            "current_ps_sha256": _sha(raw), "unload_evidence_path": str(evidence_path.relative_to(directory)),
            "unload_evidence_sha256": _sha(evidence_path.read_bytes()),
            "limitation": "Unload and runner gate do not prove a quiet physical host; preserve ordinary measurement quality checks."}


def audit_local(directory):
    """Read-only reconstruction of saved payloads, originals, imports and state."""
    from .selection_responses import collect_responses
    directory, _, protocol, config = _context(directory)
    if not (directory / "local-acquisition/preflight.json").exists():
        if (directory / "local-acquisition/requests").exists() or collect_responses(directory)["counts"]["received"]:
            raise ValueError("experimental acquisition exists without a completed technical preflight")
        return {"passed": True, "errors": [], "stage": "awaiting_preflight",
                "cohort": "real", "acquisition_backend": "ollama_local"}
    _load_preflight(directory, protocol, config)
    imported = collect_responses(directory)
    import_rows = {row["request_key"]: row for row in imported["requests"]}
    rows = []
    for request in protocol["requests"]:
        parent = directory / "local-acquisition/requests" / request["request_key"]
        folders = sorted(parent.iterdir()) if parent.exists() else []
        acquired = 0
        for index, folder in enumerate(folders, 1):
            if folder.name != f"attempt-{index:04d}" or folder.is_symlink():
                raise ValueError("acquisition attempts changed sequence")
            expected = build_payload(config, request, (directory / request["prompt_path"]).read_text(encoding="utf-8"))
            if (folder / "payload.json").read_bytes() != _json(expected):
                raise ValueError("saved payload differs from independent preregistered prompt/settings")
            outcome = _read(folder / "outcome.json")
            if outcome.get("api_response_sha256"):
                api_raw = (folder / "api-response.raw.json").read_bytes()
                if _sha(api_raw) != outcome["api_response_sha256"]:
                    raise ValueError("raw API response hash changed")
            if outcome["state"] == "acquired":
                acquired += 1
                raw = (folder / "response.raw").read_bytes()
                api = json.loads(api_raw)
                if raw != api["response"].encode("utf-8") or _sha(raw) != outcome["response_sha256"]:
                    raise ValueError("original model answer differs from raw API response")
                imported_hash = import_rows[request["request_key"]]["raw_response_sha256"]
                if imported_hash != _sha(raw):
                    if imported_hash is not None or not list((folder / "import-failures").glob("attempt-*/error.json")):
                        raise ValueError("acquired raw model answer was not imported unchanged")
                if _read(folder / "metadata.json") != _metadata(config, request, folder, outcome):
                    raise ValueError("acquisition metadata changed")
        if acquired > 1:
            raise ValueError("multiple acquired responses for one local request")
        rows.append({"request_key": request["request_key"], "api_attempts": len(folders),
                     "acquired": acquired, "import_status": import_rows[request["request_key"]]["status"]})
    return {"passed": True, "errors": [], "requests": rows, "counts": imported["counts"],
            "cohort": "real", "acquisition_backend": "ollama_local"}
