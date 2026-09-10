"""Shared inert Ollama protocol fixture; no model or external service is used."""

import pytest


@pytest.fixture
def local_config():
    from cpucond.local_llm import build_local_config, OFFICIAL_SIMPLE_TEMPLATE_SUFFIX
    return build_local_config(
        endpoint="http://127.0.0.1:11434", model="qwen2.5-coder:3b-instruct-q4_K_M",
        digest="a" * 64, ollama_version="fixture-version", server_pid=12345,
        model_show={"model_info": {"general.architecture": "qwen2", "tokenizer.ggml.model": "gpt2",
                                   "qwen2.context_length": 32768},
                    "details": {"quantization_level": "Q4_K_M"},
                    "template": OFFICIAL_SIMPLE_TEMPLATE_SUFFIX, "license": "fixture license"},
        provenance={"runtime": "official distribution fixture", "model": "official model fixture"},
        selection_reason="Inert test fixture with fixed CPU options; no actual model is used.")
