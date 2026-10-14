"""Crash-safe Batch orchestration. Only submit_pending creates paid batches."""
from __future__ import annotations
import secrets, time
from pathlib import Path
from common import PLAN_SHA, Blocked, atomic_json, canonical, digest, parse, read, require, safe, utc, write_once
from budget import validate_approval

TERMINAL = {
    "openai": {"completed", "failed", "expired", "cancelled"},
    "anthropic": {"ended"},
}

class Controller:
    def __init__(self, run_dir, context, providers):
        self.root = safe(run_dir)
        self.context = context
        self.providers = providers
        self.state_path = self.root / "state/ledger.json"
        if self.state_path.exists():
            self.state = parse(read(self.state_path))
            require(self.state["scope"] == context["scope"] and self.state["scope_sha256"] == context["scope_sha256"], "Existing ledger scope changed")
            expected_keys = {b["key"] for b in context["batches"]}
            if set(self.state["batches"]) != expected_keys and "execution_manifest" in context:
                originals = context["source_batches"]
                require(set(self.state["batches"]) == {b["key"] for b in originals}
                        and self.state["approval"] is None, "Only an unapproved original ledger can adopt pilot partition")
                for batch in originals:
                    entry = self.state["batches"][batch["key"]]
                    require(entry["status"] == "PENDING" and entry.get("batch_id") is None
                            and entry["ids"] == batch["ids"] and entry["body_sha256"] == batch["body_sha256"],
                            "Prior submitted or changed ledger cannot be repartitioned")
                for name in ("approvals", "raw", "state/intents", "state/submission-responses"):
                    path = safe(self.root / name)
                    require(not path.exists() or not any(path.iterdir()), "Prior paid evidence prevents ledger migration")
                old = read(self.state_path)
                write_once(self.root / "state/ledger-history" / (digest(old) + ".json"), old)
                self.state.update(batches={b["key"]: {"status": "PENDING", "batch_id": None,
                                  "body_sha256": b["body_sha256"], "ids": b["ids"],
                                  "provider": b["provider"], "trial": b["trial"]} for b in context["batches"]},
                                  execution_manifest_sha256=context["execution_manifest_sha256"],
                                  previous_unsubmitted_ledger_sha256=digest(old))
                self.save()
            require(set(self.state["batches"]) == expected_keys, "Existing ledger batch grid changed")
            if "execution_manifest" in context:
                require(self.state.get("execution_manifest_sha256") == context["execution_manifest_sha256"],
                        "Ledger operational manifest changed")
        else:
            for name in ("approvals", "raw", "state/intents", "state/submission-responses"):
                p = safe(self.root / name)
                require(not p.exists() or not any(p.iterdir()), "Prior cloud evidence without ledger; stop and reconcile")
            self.state = {"schema": "gpu006-cloud180-ledger-v1", "scope": context["scope"],
                          "scope_sha256": context["scope_sha256"], "created_at": utc(), "approval": None,
                          "batches": {b["key"]: {"status": "PENDING", "batch_id": None, "body_sha256": b["body_sha256"],
                                                "ids": b["ids"], "provider": b["provider"], "trial": b["trial"]}
                                      for b in context["batches"]}}
            if "execution_manifest" in context:
                self.state["execution_manifest_sha256"] = context["execution_manifest_sha256"]
            self.save()

    def save(self):
        self.state["updated_at"] = utc()
        atomic_json(self.state_path, self.state)

    def set_approval(self, reference):
        validate_approval(self.root, reference, self.context)
        require(self.state["approval"] is None or self.state["approval"] == reference, "Existing paid approval cannot be replaced")
        self.state["approval"] = reference
        self.save()

    def _require_known(self):
        uncertain = [key for key, entry in self.state["batches"].items()
                     if entry["status"] in ("SUBMISSION_INTENT", "SUBMISSION_UNKNOWN")]
        require(not uncertain, "SUBMISSION_UNKNOWN: provider reconciliation required for " + ", ".join(uncertain))

    def inspect_registry(self):
        """Read provider registries before a paid create; do not adopt unrelated runs."""
        self._require_known()
        for provider_name, provider in self.providers.items():
            if not hasattr(provider, "list_batches"):
                continue  # Injectable test doubles; real Provider always supports listing.
            registry = provider.list_batches()
            known = {entry["batch_id"] for entry in self.state["batches"].values() if entry["batch_id"]}
            matches = []
            for remote in registry:
                metadata = remote.get("metadata") or {}
                if provider_name == "openai" and metadata.get("gpu006_scope") == self.context["scope_sha256"]:
                    matches.append({"batch_id": remote.get("id"), "metadata": metadata})
                    if remote.get("id") not in known:
                        key = metadata.get("gpu006_batch")
                        require(key in self.state["batches"], "Unrecognized provider record for this scope; no submission")
                        entry = self.state["batches"][key]
                        if entry.get("batch_id") is not None:
                            conflict = {"checked_at": utc(), "key": key, "saved_batch_id": entry["batch_id"],
                                        "duplicate_batch_id": remote.get("id"), "duplicate_metadata": metadata,
                                        "action": "stop new creates; preserve original Batch ID and metadata"}
                            write_once(self.root / "state/registry-anomalies" / (digest(canonical(conflict)) + ".json"), canonical(conflict))
                            raise Blocked("Duplicate provider Batch conflicts with saved ID for " + key + "; original ID retained")
                        entry.update(status="SUBMISSION_UNKNOWN", metadata=metadata, discovered_batch_id=remote.get("id"),
                                     error_type="ProviderRecordMissingFromLedger")
                        self.save()
                        raise Blocked("Existing provider Batch found without local Batch ID: " + key + "; reconcile before creating")
            document = {"checked_at": utc(), "provider": provider_name, "records_checked": len(registry),
                        "matching_scope": matches, "known_batch_ids": sorted(x for x in known if x),
                        "anthropic_scope_lookup": "known local IDs and intents; provider has no submission metadata"}
            write_once(self.root / "state/registry-checks" / (digest(canonical(document)) + ".json"), canonical(document))
        return True

    def verify_existing_batches(self):
        self._require_known()
        for batch in self.context["batches"]:
            entry = self.state["batches"][batch["key"]]
            require(entry["body_sha256"] == batch["body_sha256"] and entry["ids"] == batch["ids"], "Ledger submission body/IDs changed")
            if entry["batch_id"]:
                observed = self.providers[batch["provider"]].retrieve(entry["batch_id"])
                require(observed.get("id") == entry["batch_id"], "Provider returned a different batch")
                if batch["provider"] == "openai":
                    require(observed.get("metadata") == entry["metadata"], "Provider batch metadata differs")
                write_once(self.root / "state/provider-status" / batch["key"] / (digest(canonical(observed)) + ".json"), canonical(observed))
        return True

    def submit_pending(self, readiness, only_keys=None):
        self.recover_saved_submissions()
        self._require_known()
        approval = validate_approval(self.root, self.state["approval"], self.context)
        require(readiness.get("ready") is True and readiness.get("plan_sha256") == PLAN_SHA
                and readiness.get("target_sha256") == self.context["scope"]["target_sha256"]
                and readiness.get("candidate_execution_uid") == 65534
                and readiness.get("checkpoint_archives_verified") is True
                and readiness.get("current_environment_verified") is True,
                "Real L4 evaluation path has not passed current preparation")
        self.inspect_registry()
        self.verify_existing_batches()
        permitted = set(self.state["batches"]) if only_keys is None else set(only_keys)
        require(permitted <= set(self.state["batches"]), "Unknown operational batch selection")
        manifest = self.context.get("execution_manifest")
        if manifest:
            pilot_key = manifest["pilot"]["batch_key"]
            proof = self.pilot_acceptance()
            if not proof or proof["status"] != "accepted":
                if only_keys is not None:
                    require(permitted <= {pilot_key}, "Pilot request API acceptance not confirmed; no remaining batches")
                permitted &= {pilot_key}
        for batch in self.context["batches"]:
            entry = self.state["batches"][batch["key"]]
            if batch["key"] not in permitted or entry["status"] != "PENDING":
                continue
            require(digest(batch["payload"]) == entry["body_sha256"], "Actual send bytes changed")
            intent_id = secrets.token_hex(16)
            metadata = {"gpu006_scope": self.context["scope_sha256"],
                        "gpu006_body": batch["body_sha256"], "gpu006_batch": batch["key"], "gpu006_intent": intent_id}
            if manifest:
                metadata.update(gpu006_execution=self.context["execution_manifest_sha256"],
                                gpu006_approval=self.state["approval"]["sha256"])
            intent = {"created_at": utc(), "intent_id": intent_id, "metadata": metadata,
                      "approval_sha256": self.state["approval"]["sha256"], "plan_sha256": PLAN_SHA,
                      "actual_body_sha256": digest(batch["payload"]), "ids": batch["ids"],
                      "provider": batch["provider"], "model": self.context["scope"]["models"][batch["provider"]]}
            write_once(self.root / "state/intents" / (batch["key"] + ".json"), canonical(intent))
            entry.update(status="SUBMISSION_INTENT", metadata=metadata, intent_id=intent_id)
            self.save()
            try:
                response = self.providers[batch["provider"]].submit(batch["payload"], metadata)
                require(isinstance(response.get("id"), str) and response["id"], "Submission returned no Batch ID")
                # Preserve accepted response before any following work.
                response_raw = getattr(self.providers[batch["provider"]], "last_response", None) or canonical(response)
                require(parse(response_raw) == response, "Raw create response mismatch")
                write_once(self.root / "state/submission-responses" / (batch["key"] + ".json"), response_raw)
                entry.update(status="SUBMITTED", batch_id=response["id"], submitted_at=utc())
                self.save()
            except BaseException as exc:
                # Even a KeyboardInterrupt is uncertain once intent is persisted.
                # No response details or credentials are put into the ledger.
                entry.update(status="SUBMISSION_UNKNOWN", error_type=type(exc).__name__)
                self.save()
                raise Blocked("SUBMISSION_UNKNOWN for " + batch["key"] + "; do not resubmit") from None
        return self.state

    def pilot_acceptance(self):
        manifest = self.context.get("execution_manifest")
        if not manifest or not self.state.get("pilot_acceptance"):
            return None
        ref = self.state["pilot_acceptance"]
        require(ref["path"] == "state/api-acceptance/" + manifest["pilot"]["batch_key"] + ".json",
                "Unsafe pilot acceptance evidence path")
        raw = read(self.root / ref["path"])
        require(digest(raw) == ref["sha256"], "Pilot acceptance evidence changed")
        proof = parse(raw)
        for artifact in [*proof["raw_response_artifacts"], proof["terminal_status_artifact"]]:
            require(digest(read(self.root / artifact["path"], 256 * 1024**2)) == artifact["sha256"],
                    "Pilot raw request evidence changed")
        expected = manifest["pilot"]
        require(proof["custom_id"] == expected["custom_id"]
                and proof["request_body_sha256"] == expected["request_body_sha256"]
                and proof["submission_body_sha256"] == expected["submission_body_sha256"]
                and proof["execution_manifest_sha256"] == self.context["execution_manifest_sha256"]
                and proof["batch_id"] == self.state["batches"][expected["batch_key"]]["batch_id"]
                and proof["actual_input_verified"] is True and proof["status"] == ref["status"],
                "Pilot proof does not bind the exact current request/body/Batch")
        return proof

    def revision_proposal(self, proof):
        if proof["status"] != "fixed_parameter_rejected":
            return None
        fields = sorted({e.get("param") for e in proof.get("errors", []) if e.get("param")})
        changes = []
        for error in proof.get("errors", []):
            field = error.get("param")
            if not field:
                continue
            changes.append({"field": field,
                            "proposed_operation": "omit only this unsupported parameter" if error.get("code") in ("unsupported_parameter", "parameter_not_supported")
                            else "review and replace only this rejected value with an explicitly supported value",
                            "automatic_application": False})
        proposal = {"schema": "gpu006-cloud180-fixed-parameter-revision-proposal-v1",
                    "status": "proposal_only_not_applied", "source_proof": self.state["pilot_acceptance"],
                    "fixed_plan_sha256": PLAN_SHA, "fields_requiring_review": fields,
                    "minimal_revision_proposals": changes,
                    "comparison_impact": "GPT generation conditions would differ from the fixed plan; do not combine them as unchanged GPU006 conditions",
                    "requires": "Separate plan revision and fresh approval; no automatic retry or replacement of failed pilot",
                    "fixed_plan_unchanged": True, "remaining_gpt_requests_not_submitted": 89}
        write_once(self.root / "state/api-revision-proposal.json", canonical(proposal))
        return proposal

    def require_pilot_accepted(self):
        proof = self.pilot_acceptance()
        require(proof is not None, "PILOT_ACCEPTANCE_UNKNOWN: no per-request response evidence")
        self.revision_proposal(proof)
        code = {"fixed_parameter_rejected": "FIXED_PARAMETER_REJECTED",
                "other_api_error": "PILOT_API_ERROR", "unknown": "PILOT_ACCEPTANCE_UNKNOWN"}.get(proof["status"], "PILOT_ACCEPTANCE_MISMATCH")
        require(proof["status"] == "accepted", code + ": see saved pilot request evidence and any state/api-revision-proposal.json; remaining requests not submitted")
        return proof

    def _record_pilot_acceptance(self, batch, entry, row, remote):
        manifest = self.context.get("execution_manifest")
        if not manifest or batch["key"] != manifest["pilot"]["batch_key"]:
            return
        if self.state.get("pilot_acceptance"):
            self.pilot_acceptance()
            return
        provider = self.providers["openai"]
        require(provider.verify_batch(remote, batch["payload"], entry["metadata"]),
                "Pilot remote input bytes/metadata differ; no API acceptance proof")
        saved_path = "state/api-acceptance/" + batch["key"] + ".json"
        if (self.root / saved_path).exists():
            saved_raw = read(self.root / saved_path)
            saved_proof = parse(saved_raw)
            require(saved_proof["raw_response_artifacts"] == entry["raw_artifacts"],
                    "Saved pilot proof refers to different raw request results")
            self.state["pilot_acceptance"] = {"path": saved_path, "sha256": digest(saved_raw), "status": saved_proof["status"]}
            self.pilot_acceptance()
            self.save()
            return
        from providers import assess_api_acceptance
        proof = assess_api_acceptance("openai", row, batch["requests"][0], entry["batch_id"],
                                      body_sha256=batch["body_sha256"], terminal_batch=remote)
        proof.update(schema="gpu006-cloud180-pilot-acceptance-v2", checked_at=utc(),
                     execution_manifest_sha256=self.context["execution_manifest_sha256"],
                     actual_input_verified=True,
                     public_documentation_is_separate=True,
                     historical_exact_setting_acceptance={"status": "not_verified", "records": []},
                     parameter_influence_on_generated_content="not established by API acceptance",
                     raw_response_artifacts=entry["raw_artifacts"],
                     terminal_status_artifact=entry["terminal_status_artifact"])
        path = "state/api-acceptance/" + batch["key"] + ".json"
        data = canonical(proof)
        write_once(self.root / path, data)
        self.state["pilot_acceptance"] = {"path": path, "sha256": digest(data), "status": proof["status"]}
        self.save()

    def recover_saved_submissions(self):
        """A saved accepted POST response contains the original ID; no new POST."""
        for batch in self.context["batches"]:
            key = batch["key"]
            entry = self.state["batches"][key]
            if entry["status"] not in ("SUBMISSION_UNKNOWN", "SUBMISSION_INTENT"):
                continue
            path = self.root / "state/submission-responses" / (key + ".json")
            if not path.exists() or batch["provider"] not in self.providers:
                continue
            saved_raw = read(path)
            accepted = parse(saved_raw)
            batch_id = accepted.get("id")
            require(isinstance(batch_id, str) and batch_id, "Saved accepted response has no original Batch ID")
            require(entry.get("batch_id") is None or entry["batch_id"] == batch_id,
                    "Saved successful Batch ID cannot be replaced during recovery")
            provider = self.providers[batch["provider"]]
            observed = provider.retrieve(batch_id)
            response_raw = getattr(provider, "last_response", None) or canonical(observed)
            require(parse(response_raw) == observed and observed.get("id") == batch_id, "Saved Batch ID lookup mismatch")
            if batch["provider"] == "openai":
                require(provider.verify_batch(observed, batch["payload"], entry["metadata"]), "Saved OpenAI input body/metadata mismatch")
            else:
                # Only a locally persisted accepted create response establishes
                # provenance before Anthropic results finish (no metadata API).
                for document in (accepted, observed):
                    counts = document.get("request_counts", {})
                    require(counts and all(type(v) is int and v >= 0 for v in counts.values())
                            and sum(counts.values()) == len(batch["ids"]), "Saved Anthropic accepted-count evidence mismatch")
            write_once(self.root / "state/recovery-responses" / key / (digest(response_raw) + ".json"), response_raw)
            entry.update(status="SUBMITTED", batch_id=batch_id, accepted_response_sha256=digest(saved_raw),
                         recovered_at=utc(), recovery="saved accepted POST ID verified by GET; zero new create calls")
            self.save()
        return self.state

    def reconcile(self, key, batch_id):
        require(key in self.state["batches"], "Unknown ledger batch key")
        entry = self.state["batches"][key]
        require(entry["status"] in ("SUBMISSION_UNKNOWN", "SUBMISSION_INTENT"), "Only uncertain intents can be reconciled")
        require(entry.get("batch_id") is None or entry["batch_id"] == batch_id,
                "Saved successful Batch ID cannot be replaced during reconciliation")
        batch = next(b for b in self.context["batches"] if b["key"] == key)
        provider = self.providers[batch["provider"]]
        remote = provider.retrieve(batch_id)
        response_raw = getattr(provider, "last_response", None) or canonical(remote)
        require(parse(response_raw) == remote, "Raw reconciliation response mismatch")
        require(remote.get("id") == batch_id, "Batch ID mismatch")
        require(provider.verify_batch(remote, batch["payload"], entry["metadata"]), "Provider evidence cannot identify original submission body; retained as unknown")
        # Current GET status evolves; preserve the original accepted POST artifact.
        write_once(self.root / "state/reconciliation-responses" / key / (digest(response_raw) + ".json"), response_raw)
        entry.update(status="SUBMITTED", batch_id=batch_id, reconciled_at=utc(), reconciliation="provider evidence; no new generation request")
        self.save()
        return entry

    def collect_once(self):
        self.recover_saved_submissions()
        self._require_known()
        from providers import normalize_result
        for batch in self.context["batches"]:
            key = batch["key"]
            entry = self.state["batches"][key]
            if entry["status"] == "PENDING" or entry["status"] == "COLLECTED":
                continue
            provider = self.providers[batch["provider"]]
            remote = provider.retrieve(entry["batch_id"])
            require(remote.get("id") == entry["batch_id"], "Provider returned a different Batch ID")
            if batch["provider"] == "openai":
                require(remote.get("metadata") == entry["metadata"], "Provider metadata mismatch")
            write_once(self.root / "state/provider-status" / key / (digest(canonical(remote)) + ".json"), canonical(remote))
            status = remote.get("status") if batch["provider"] == "openai" else remote.get("processing_status")
            entry["provider_status"] = status
            self.save()
            if status not in TERMINAL[batch["provider"]]:
                continue
            # Persist the exact terminal Batch response too, so IDs without a result
            # still have immutable provider evidence (never synthesize CUDA).
            status_raw = getattr(provider, "last_response", None) or canonical(remote)
            require(parse(status_raw) == remote, "Provider raw status mismatch")
            status_path = self.root / "raw" / key / ("status-" + digest(status_raw) + ".json")
            write_once(status_path, status_raw)
            entry["terminal_status_artifact"] = {"path": str(status_path.relative_to(self.root)), "sha256": digest(status_raw)}
            self.save()
            artifacts = entry.get("raw_artifacts")
            if artifacts is None:
                # Read-only downloads may safely resume. Never repeat a create request.
                artifacts = []
                for name, raw in provider.results(remote):
                    require(isinstance(name, str) and name and "/" not in name and "\\" not in name
                            and name not in (".", ".."), "Unsafe provider artifact name")
                    path = self.root / "raw" / key / name
                    write_once(path, raw)
                    artifacts.append({"path": str(path.relative_to(self.root)), "sha256": digest(raw)})
                entry["raw_artifacts"] = artifacts
                self.save()
            expected = set(batch["ids"])
            by_id = {}
            raw_rows = {}
            for artifact in artifacts:
                raw = read(self.root / artifact["path"], 256 * 1024**2)
                require(digest(raw) == artifact["sha256"], "Saved unmodified provider response changed")
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    row = parse(line)
                    rid = row.get("custom_id")
                    require(rid in expected, "Unexpected provider custom_id")
                    require(rid not in by_id, "Duplicate provider custom_id; no ordinal matching")
                    raw_rows[rid] = row
                    item = normalize_result(batch["provider"], row)
                    require(item["id"] == rid, "Normalized response ID mismatch")
                    item.update(raw_response_path=str(self.root / artifact["path"]),
                                raw_response_sha256=artifact["sha256"],
                                response_artifact=str(self.root / artifact["path"]),
                                requested_model=self.context["scope"]["models"][batch["provider"]])
                    returned_model = item.get("model")
                    if returned_model and returned_model != item["requested_model"]:
                        item["generation_status"] = "model_mismatch"
                        item.pop("candidate_text", None)
                    by_id[rid] = item
            for rid in batch["ids"]:
                if rid not in by_id:
                    reason = {"expired": "expired", "cancelled": "canceled", "failed": "api_error"}.get(status, "missing_result")
                    by_id[rid] = {"id": rid, "generation_status": reason, "provider_status": status, "usage": {},
                                  "raw_response_path": str(status_path), "raw_response_sha256": digest(status_raw),
                                  "requested_model": self.context["scope"]["models"][batch["provider"]]}
            if "execution_manifest" in self.context and batch["key"] == self.context["execution_manifest"]["pilot"]["batch_key"]:
                self._record_pilot_acceptance(batch, entry, raw_rows.get(batch["ids"][0]), remote)
            normalized = [by_id[rid] for rid in batch["ids"]]
            output = self.root / "results/normalized" / (key + ".json")
            write_once(output, canonical(normalized))
            entry.update(status="COLLECTED", normalized_path=str(output.relative_to(self.root)),
                         normalized_sha256=digest(canonical(normalized)), collected_at=utc())
            self.save()
        if all(e["status"] == "COLLECTED" for e in self.state["batches"].values()):
            items = []
            for batch in self.context["batches"]:
                entry = self.state["batches"][batch["key"]]
                raw = read(self.root / entry["normalized_path"])
                require(digest(raw) == entry["normalized_sha256"], "Normalized artifact changed")
                items.extend(parse(raw))
            require(len(items) == len({r["id"] for r in items}) == 180
                    and {r["id"] for r in items} == set(self.context["scope"]["ids"]), "Cloud180 ID coverage differs")
            # Preserve exact plan order, independent of result arrival order.
            indexed = {r["id"]: r for r in items}
            items = [indexed[rid] for rid in self.context["scope"]["ids"]]
            write_once(self.root / "results/collected.json", canonical(items))
            return items
        return None

    def snapshot(self):
        return {"batches": {k: {f: e.get(f) for f in ("status", "batch_id", "provider_status")} for k, e in self.state["batches"].items()},
                "generation_create_retries": 0, "paid_budget_approved": self.state["approval"] is not None,
                "pilot_acceptance": self.state.get("pilot_acceptance")}

    def watch(self, interval=30, until_batch=None):
        require(1 <= interval <= 60, "Poll interval must be 1..60 seconds")
        while True:
            result = self.collect_once()
            print(canonical(self.snapshot()).decode().strip(), flush=True)
            if result is not None:
                return result
            if until_batch is not None:
                require(until_batch in self.state["batches"], "Unknown watched pilot batch")
                entry = self.state["batches"][until_batch]
                if entry["status"] == "COLLECTED":
                    raw = read(self.root / entry["normalized_path"])
                    require(digest(raw) == entry["normalized_sha256"], "Pilot normalized results changed")
                    return parse(raw)
                require(entry["status"] != "PENDING", "Watch cannot submit a pending pilot")
            require(any(e["status"] != "PENDING" for e in self.state["batches"].values()), "No submitted batches; watch cannot submit")
            if all(e["status"] in ("PENDING", "COLLECTED") for e in self.state["batches"].values()):
                return None
            time.sleep(interval)
