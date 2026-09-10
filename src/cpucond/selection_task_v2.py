"""Versioned task clarification. Legacy prompt bytes remain reproducible."""
from copy import deepcopy

PROMPT_REVISION = "goal0032-explicit-latency-v1"
LOCAL_SCHEMA = "cpucond.ollama-local.v2"
FORMAT = "cpucond-selection-response-schema-v1"
TASK = (
    "Select the supplied C kernel expected to have the LOWEST KERNEL EXECUTION TIME "
    "for one single-threaded invocation at the stated input size, under the stated "
    "compiler and target execution conditions, while satisfying the correctness contract. "
    "Minimize elapsed time inside kernel only: exclude compilation, process launch, "
    "array initialization and output serialization. Do not optimize source-code length, "
    "readability or response-generation time. Option labels and presentation position "
    "are identifiers, not performance recommendations. Use only this prompt; do not "
    "execute code, search, use tools, consult past results or read other trial answers. "
    "Return the required JSON fields. This is a development diagnostic, not free-form "
    "code optimization or an unseen benchmark."
)


def response_schema(request):
    """Request ID binds the pair, never a winning candidate; all options are allowed."""
    rid = request["request_id"]
    mapping = request["option_mapping"]
    if not isinstance(rid, str) or not rid:
        raise ValueError("schema requires a nonempty request_id")
    if not isinstance(mapping, dict) or not mapping or any(not isinstance(k, str) for k in mapping):
        raise ValueError("schema requires explicit option identifiers")
    return {
        "type": "object",
        "properties": {
            "request_id": {"type": "string", "enum": [rid]},
            "selected_option_id": {"type": "string", "enum": list(mapping)},
            "rationale_short": {"type": "string", "maxLength": 500},
        },
        "required": ["request_id", "selected_option_id"],
        "additionalProperties": False,
    }


def clarify_payload(payload, mapping):
    result = deepcopy(payload)
    result["task"] = TASK
    result["output_format"]["json_schema"] = response_schema(
        {"request_id": payload["request_id"], "option_mapping": mapping})
    return result


def local_config_v2(original, server_pid):
    result = deepcopy(original)
    result.update(schema_version=LOCAL_SCHEMA, format=FORMAT, server_pid=server_pid)
    result["protocol_change"] = (
        "New prospective pilot: explicit minimum-kernel-latency objective and "
        "per-request schema-constrained decoding. Both changes apply to none and spec. "
        "Old answers/labels are not edited. An old/new difference cannot isolate "
        "the effects of objective wording and structured decoding. Position and "
        "option-label preference remain confounded. Model/options/seeds are inherited."
    )
    return result
