# Final CPU-conditioned LLM optimization protocol v1

This document freezes the final experimental design before the final physical-CPU
atlas is collected.

## Main study

PolyBench/C 4.2.1-beta, all 30 kernels, all five standard dataset sizes.
At least two physical microarchitectures: Intel Haswell and AMD Zen 2.

The candidate set consists only of identity or one Clang loop hint applied to one
syntactic loop:

- unroll_count: 2, 4, 8, 16
- interleave_count: 2, 4, 8
- vectorize_width: 2, 4, 8

No arbitrary LLM source rewriting is permitted in the main experiment.

Candidates must pass the full-state correctness gate before timing.

The main LLM experiment compares P0/P1/P2 without performance feedback.
The measured physical-CPU atlas is hidden from the models and used only for scoring.

Models: local Qwen baseline plus one fixed GPT, Claude, and Gemini model.
Exact proprietary model IDs are frozen immediately before the offline LLM phase;
changing a model does not require rerunning CPU measurements.

Primary analysis is within-model P0 vs P1 vs P2, using oracle regret and
CPU-specific oracle separability in addition to speedup.
