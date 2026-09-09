"""Offline selection tasks built only from explicitly supplied common inputs.

The selection exercise is diagnostic preparation, not an LLM experiment and
not a replacement for future unconstrained C optimization. Measured records,
compiler configuration, host observations, and correctness verdicts are not
accepted by this interface. Source and contract text are explicit disclosures;
the caller must not embed results into those inputs or the CPU specification.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import ExecutionContract, PromptCPUContext
from .prompts import CPU_SECTION_HEADER, prompt_hash
from .transformations import Candidate, FACTORS


SELECTION_TASK = (
    "Select one supplied C kernel option for the common execution contract. "
    "Consider its likely execution behavior and explain your reasoning. "
    "This is a diagnostic selection task; it does not replace future free-form "
    "C code optimization."
)
SELECTION_OUTPUT = (
    'Return one JSON object with only "option_id" and "reasoning". '
    '"option_id" must identify one supplied option; "reasoning" must be a string.'
)


def _common_payload(candidates: list[Candidate], contract: ExecutionContract) -> tuple[dict, dict]:
    if type(contract) is not ExecutionContract:
        raise TypeError("contract must be an ExecutionContract")
    if not isinstance(candidates, list) or any(type(item) is not Candidate for item in candidates):
        raise TypeError("candidates must be a list of Candidate source descriptors")
    if len({item.candidate_id for item in candidates}) != len(candidates):
        raise ValueError("candidate IDs must be unique")
    references = [item for item in candidates if item.candidate_id == "reference"]
    if len(references) != 1 or not references[0].source.strip():
        raise ValueError("one nonempty reference source is required")
    generated = [item for item in candidates if item.origin == "deterministic_generator"]
    if len(generated) != len(FACTORS) or {item.unroll_factor for item in generated} != set(FACTORS):
        raise ValueError("diagnostic options require exactly the five generated factors")
    generated.sort(key=lambda item: item.unroll_factor)
    if any(not isinstance(item.source, str) or not item.source.strip() for item in generated):
        raise ValueError("every diagnostic option requires nonempty source")
    option_mapping = {
        f"option_{index:02d}": item.candidate_id for index, item in enumerate(generated, 1)
    }
    # This is an explicit allowlist, never asdict(candidate) or a run-record dump.
    # In particular no role, origin, factor annotation, baseline, or control ID
    # is disclosed. The factor remains naturally visible in each source.
    payload = {
        "task": SELECTION_TASK,
        "reference_source": references[0].source,
        "contract": {"abi": contract.abi, "correctness": contract.correctness},
        "options": [
            {"option_id": option_id, "source": item.source}
            for option_id, item in zip(option_mapping, generated)
        ],
        "output_format": SELECTION_OUTPUT,
    }
    return payload, option_mapping


def write_diagnostic_prompts(
    directory: Path,
    candidates: list[Candidate],
    context_spec: str,
    contract: ExecutionContract,
) -> dict:
    """Save byte-identical common inputs in none/spec; paths are directory-relative.

    All validation precedes writes. Existing prompt files are never overwritten.
    The supplied CPU text is saved verbatim and hashed as UTF-8; only ``spec``
    appends that explicit description. CompilerTarget is deliberately absent.
    ``contract.output_format`` describes free-form generation in Goal 001 and is
    deliberately replaced by the same selection format in both conditions.
    """
    context = PromptCPUContext("spec", context_spec)
    payload, option_mapping = _common_payload(candidates, contract)
    common = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    contents = {
        "common_payload.json": common,
        "cpu_spec.txt": context.specification,
        "none.txt": common,
        "spec.txt": common + CPU_SECTION_HEADER + context.specification + "\n",
    }
    directory = Path(directory)
    if any((directory / name).exists() for name in contents):
        raise FileExistsError("diagnostic prompt artifacts already exist")
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        with (directory / name).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    common_hash = prompt_hash(common)
    cpu_hash = prompt_hash(context.specification)
    result = {
        "purpose": "offline_diagnostic_selection_preparation",
        "llm_calls": 0,
        "option_mapping": option_mapping,
        "common_payload": {"path": "common_payload.json", "sha256": common_hash},
        "cpu_spec": {"path": "cpu_spec.txt", "sha256": cpu_hash},
    }
    for mode in ("none", "spec"):
        result[mode] = {
            "path": f"{mode}.txt",
            "sha256": prompt_hash(contents[f"{mode}.txt"]),
            "common_payload_sha256": common_hash,
            "cpu_spec_sha256": cpu_hash if mode == "spec" else None,
        }
    return result
