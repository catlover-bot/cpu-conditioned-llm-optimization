"""Exact-token Batch reservation and a separately persisted, scope-bound approval."""
from __future__ import annotations
import datetime as dt, decimal
from common import Blocked, canonical, digest, require, utc, write_once, read, parse

D = decimal.Decimal
M = D(1000000)
MARGIN = D("0.20")

def money(value):
    try:
        out = D(str(value))
    except decimal.InvalidOperation:
        raise Blocked("Budget must be a finite positive USD amount")
    require(out.is_finite() and out > 0, "Budget must be a finite positive USD amount")
    return out

def make_quote(context, preflights, evidence):
    require(set(preflights) == {"openai", "anthropic"}, "Both providers must pass preflight")
    supports = evidence.get("public_parameter_support", {})
    require(not evidence.get("explicitly_unsupported_parameters") and "unsupported" not in supports.values(),
            "EXPLICIT_API_UNSUPPORTED: fixed parameters conflict with official evidence; zero submissions")
    if evidence.get("parameters_verified") is not True:
        require(context.get("execution_manifest", {}).get("mode") == "pilot_first_batch"
                and supports.get("openai") in ("documented", "unverified")
                and supports.get("anthropic") == "documented",
                "Fixed API parameters require the explicit pilot-first approval path")
    stamp = dt.datetime.fromisoformat(evidence["verified_at"].replace("Z", "+00:00"))
    require(stamp.tzinfo is not None, "Price timestamp must have timezone")
    age = (dt.datetime.now(dt.timezone.utc) - stamp).total_seconds()
    require(-300 <= age <= 86400, "Official rates require fresh verification (within 24 hours)")
    require(evidence.get("sources"), "Official pricing sources missing")
    rates = evidence["rates"]
    rows = []
    total = D(0)
    for provider in ("openai", "anthropic"):
        pf = preflights[provider]
        model = context["scope"]["models"][provider]
        rate = rates[provider]
        require(pf["model"] == model and rate["model"] == model, "Model mismatch in quote")
        tokens = pf["input_tokens"]
        ids = [r["id"] for r in context["plan"]["requests"] if r["provider"] == provider]
        require(len(ids) == 90 and set(tokens) == set(ids), "Exact input token coverage differs")
        require(all(type(n) is int and n > 0 for n in tokens.values()), "Input count must be provider-native")
        inp = money(rate["input_usd_per_mtok"])
        out = money(rate["output_usd_per_mtok"])
        # Reserve every capped output and charge all inputs uncached. No cache benefit presumed.
        input_multiplier = money(rate.get("input_reservation_multiplier", 1))
        threshold = rate.get("long_context_threshold_tokens")
        long_ids = {rid for rid, count in tokens.items() if threshold is not None and count > threshold}
        long_in = money(rate.get("long_context_input_multiplier", 1))
        long_out = money(rate.get("long_context_output_multiplier", 1))
        input_cost = sum((D(count) * inp * input_multiplier * (long_in if rid in long_ids else D(1)) / M for rid, count in tokens.items()), D(0))
        output_cost = sum((D(8192) * out * (long_out if rid in long_ids else D(1)) / M for rid in ids), D(0))
        subtotal = input_cost + output_cost
        total += subtotal
        rows.append({"provider": provider, "model": model, "requests": 90, "input_tokens": sum(tokens.values()),
                     "max_output_tokens": 90 * 8192, "input_reservation_multiplier": str(input_multiplier),
                     "long_context_request_ids": sorted(long_ids), "input_usd_per_mtok": str(inp),
                     "output_usd_per_mtok": str(out), "input_reserved_usd": str(input_cost),
                     "output_reserved_usd": str(output_cost), "subtotal_usd": str(subtotal)})
    reserved = (total * (D(1) + MARGIN)).quantize(D("0.000001"), rounding=decimal.ROUND_CEILING)
    quote = {"schema": "gpu006-cloud180-quote-v1", "created_at": utc(),
            "scope": context["scope"], "scope_sha256": context["scope_sha256"],
            "providers": rows, "official_evidence": evidence,
            "token_count_evidence": {p: preflights[p] for p in preflights},
            "full_input_uncached": True, "cache_discount_assumed": False,
            "region": "provider default/global; no regional premium parameter in fixed draft",
            "safety_margin_fraction": str(MARGIN), "base_reserved_usd": str(total),
            "reserved_usd": str(reserved), "proposed_unapproved_budget_usd": "10",
            "proposed_budget_sufficient": reserved <= D(10),
            "excluded": ["existing GPU rental", "tax", "FX", "any extra service calls"],
            "trials": [1, 2, 3], "requests": 180, "per_request_max_output_tokens": 8192}

    if "execution_manifest" in context:
        quote.update(execution_manifest=context["execution_manifest"],
                     execution_manifest_sha256=context["execution_manifest_sha256"],
                     submission_procedure="GPT first fixed request as Batch pilot, then remaining GPT89 and Claude90 after native API acceptance",
                     api_compatibility_evidence={
                         "public_documentation": {"status": "documented" if evidence.get("parameters_verified") is True else "unverified",
                                                  "parameters_verified": evidence.get("parameters_verified") is True,
                                                  "provider_support": supports},
                         "historical_exact_setting_acceptance": {"status": "not_verified", "records": []},
                         "current_account_request_acceptance": {"status": "not_yet_tested",
                                                                "pilot_custom_id": context["execution_manifest"]["pilot"]["custom_id"]}})
    return quote

APPROVAL_PHRASE = "SUBMIT GPU006 CLOUD180 ALL 3 TRIALS"
PILOT_APPROVAL_PHRASE = APPROVAL_PHRASE + " PILOT FIRST"

def required_phrase(quote):
    return PILOT_APPROVAL_PHRASE if "execution_manifest" in quote else APPROVAL_PHRASE


def approve(run_dir, quote, limit, phrase):
    require(phrase == required_phrase(quote), "Explicit new paid submission and pilot-first approval missing")
    ceiling = money(limit)
    require(D(quote["reserved_usd"]) <= ceiling, "Reservation exceeds user total limit; zero submissions")
    approval = {"schema": "gpu006-cloud180-approval-v1", "approved_at": utc(),
                "scope_sha256": quote["scope_sha256"], "scope": quote["scope"],
                "quote_sha256": digest(canonical(quote)), "quote": quote,
                "total_limit_usd": str(ceiling), "reserved_usd": quote["reserved_usd"],
                "approval_phrase": phrase, "all_three_trials_authorized_together": True,
                "automatic_generation_retry_authorized": False}
    if "execution_manifest" in quote:
        approval.update(execution_manifest_sha256=quote["execution_manifest_sha256"],
                        pilot_first_submission_authorized=True,
                        pilot_custom_id=quote["execution_manifest"]["pilot"]["custom_id"],
                        candidate_quality_does_not_gate_continuation=True)
    data = canonical(approval)
    name = digest(data) + ".json"
    write_once(run_dir / "approvals" / name, data)
    return {"path": "approvals/" + name, "sha256": digest(data)}

def validate_approval(run_dir, reference, context):
    require(isinstance(reference, dict), "New paid budget not approved; zero submissions")
    # Reference is generated by approve; only content-addressed local approval paths.
    name = reference.get("sha256", "")
    require(len(name) == 64 and all(c in "0123456789abcdef" for c in name), "Malformed approval reference")
    require(reference.get("path") == "approvals/" + name + ".json", "Unsafe approval path")
    data = read(run_dir / reference["path"])
    require(digest(data) == name, "Approval bytes changed")
    approval = parse(data)
    require(approval["approval_phrase"] == required_phrase(approval["quote"]), "New submission procedure approval missing")
    require(approval["scope_sha256"] == context["scope_sha256"] and approval["scope"] == context["scope"], "Approval scope mismatch")
    require(approval["all_three_trials_authorized_together"] is True, "All three trials not approved")
    quote = approval["quote"]
    require(digest(canonical(quote)) == approval["quote_sha256"] and quote["scope"] == context["scope"], "Quoted scope changed")
    if "execution_manifest" in context:
        require(quote.get("execution_manifest") == context["execution_manifest"]
                and quote.get("execution_manifest_sha256") == context["execution_manifest_sha256"]
                and approval.get("execution_manifest_sha256") == context["execution_manifest_sha256"]
                and approval.get("pilot_first_submission_authorized") is True
                and approval.get("pilot_custom_id") == context["execution_manifest"]["pilot"]["custom_id"],
                "Pilot execution manifest/procedure not authorized")
    require(D(quote["reserved_usd"]) <= money(approval["total_limit_usd"]), "Approved reservation exceeds limit")
    return approval
