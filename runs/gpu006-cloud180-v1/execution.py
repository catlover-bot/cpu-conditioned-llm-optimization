"""Operational Batch partition only; the pinned 270-request experiment is unchanged."""
from __future__ import annotations
from collections import Counter
from common import PLAN_SHA, canonical, digest, parse, read, require, write_once
from providers import canonical as native_body_bytes

PILOT_KEY = "openai-pilot"
MODE = "pilot_first_batch"

def build_execution(context):
    originals = context["batches"]
    first_id = next(r["id"] for r in context["plan"]["requests"] if r["provider"] == "openai")
    original = next(b for b in originals if first_id in b["ids"])
    lines = original["payload"].splitlines(keepends=True)
    require(len(lines) == len(original["requests"]) == 30, "Original pilot trial size changed")
    position = original["ids"].index(first_id)
    require(parse(lines[position]) == original["requests"][position], "Pilot raw line differs")
    pilot_payload = lines[position]
    remainder_payload = b"".join(line for index, line in enumerate(lines) if index != position)
    def subset(key, payload, rows):
        return {"key": key, "provider": "openai", "trial": original["trial"],
                "ids": [row["custom_id"] for row in rows], "payload": payload,
                "requests": rows, "body_sha256": digest(payload),
                "source_batch_key": original["key"]}
    pilot = subset(PILOT_KEY, pilot_payload, [original["requests"][position]])
    remainder = subset(original["key"] + "-remainder", remainder_payload,
                       [row for index, row in enumerate(original["requests"]) if index != position])
    batches = [pilot, remainder]
    # Provider grouping preserves each provider's fixed request order.
    for provider in ("openai", "anthropic"):
        batches.extend(dict(b, source_batch_key=b["key"]) for b in originals
                       if b["provider"] == provider and b["key"] != original["key"])
    ids = [rid for b in batches for rid in b["ids"]]
    require(len(ids) == len(set(ids)) == 180 and set(ids) == set(context["scope"]["ids"]),
            "Operational partition changes original 180 IDs")
    require(Counter(b["provider"] for b in batches) == {"openai": 4, "anthropic": 3},
            "Operational provider partition changed")
    require([rid for b in batches if b["provider"] == "openai" for rid in b["ids"]] ==
            [r["id"] for r in context["plan"]["requests"] if r["provider"] == "openai"],
            "GPT fixed request order changed")
    require(first_id not in remainder["ids"] and len(remainder["ids"]) == 29,
            "Pilot ID appears in remaining 89 requests")
    manifest = {"schema": "gpu006-cloud180-execution-manifest-v2", "mode": MODE,
                "fixed_plan_sha256": PLAN_SHA, "fixed_scope_sha256": context["scope_sha256"],
                "fixed_scope": context["scope"],
                "pilot": {"batch_key": PILOT_KEY, "custom_id": first_id,
                          "request_body_sha256": digest(native_body_bytes(pilot["requests"][0]["body"])),
                          "submission_body_sha256": pilot["body_sha256"],
                          "request_body_hash_encoding": "provider canonical native JSON, without trailing newline",
                          "source_batch_key": original["key"]},
                "operational_batches": [{k: b[k] for k in
                                        ("key", "provider", "trial", "ids", "body_sha256", "source_batch_key")}
                                       for b in batches],
                "submission_order_keys": [b["key"] for b in batches],
                "total_requests": 180, "gpt_requests": 90, "claude_requests": 90,
                "trials": [1, 2, 3], "max_output_tokens": 8192,
                "operation_change": "Split first fixed GPT request into a one-request Batch; no request/body/settings changes",
                "continuation_gate": "native request acceptance only; independent of candidate format, correctness or performance",
                "pilot_result_included_in_experiment": True,
                "synchronous_generation": False, "automatic_paid_retry": False,
                "compatibility_evidence_states": ["public_documentation", "historical_exact_setting_acceptance",
                                                  "current_account_request_acceptance"]}
    configured = dict(context, batches=batches, source_batches=originals,
                      execution_manifest=manifest, execution_manifest_sha256=digest(canonical(manifest)))
    return configured

def configure_execution(context, run_dir, create=False):
    """Only unapproved, wholly unsubmitted legacy state may adopt the new split."""
    path = run_dir / "execution-manifest.json"
    configured = build_execution(context)
    if path.exists():
        require(parse(read(path)) == configured["execution_manifest"], "Operational manifest changed")
        return configured
    ledger_path = run_dir / "state/ledger.json"
    if ledger_path.exists():
        ledger = parse(read(ledger_path))
        # A historical approved/sent six-batch run keeps its exact partition.
        if ledger.get("approval") is not None or any(e["status"] != "PENDING" or e.get("batch_id")
                                                    for e in ledger["batches"].values()):
            return context
    if not create:
        return context
    for name in ("approvals", "raw", "state/intents", "state/submission-responses"):
        location = run_dir / name
        require(not location.exists() or not any(location.iterdir()),
                "Existing paid artifacts prevent adopting the pilot partition")
    write_once(path, canonical(configured["execution_manifest"]))
    return configured
