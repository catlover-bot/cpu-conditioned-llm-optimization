"""Deterministic prompt rendering from an explicit allowlist of inputs only."""

from __future__ import annotations

import hashlib

from .models import ExecutionContract, PromptCPUContext


CPU_SECTION_HEADER = "\n## Additional CPU specification\n"


def render_prompt(
    source: str,
    context: PromptCPUContext,
    contract: ExecutionContract = ExecutionContract(),
) -> str:
    """Render a local prompt; neither host observation nor build settings are read.

    Source and contract are intentionally disclosed verbatim. A caller supplying
    CPU information inside either is explicitly disclosing it in both conditions.
    'none' means no *additional* CPU specification, not total ISA/ABI blindness.
    """
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a nonempty C source string")
    if type(context) is not PromptCPUContext:
        raise TypeError("context must be a PromptCPUContext")
    if type(contract) is not ExecutionContract:
        raise TypeError("contract must be an ExecutionContract")
    common = (
        "Optimize the supplied C kernel while preserving its execution contract.\n"
        "\n## Common execution contract\n"
        + contract.abi
        + "\n\n## Common correctness contract\n"
        + contract.correctness
        + "\n\n## Common output format\n"
        + contract.output_format
        + "\n\n## Input C source (verbatim)\n"
        + "<source>\n"
        + source
        + "\n</source>\n"
    )
    if context.mode == "spec":
        return common + CPU_SECTION_HEADER + context.specification + "\n"
    return common


def prompt_hash(prompt: str) -> str:
    """SHA-256 of the exact UTF-8 bytes saved as the prompt artifact."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
