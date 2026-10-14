# GPU004 primary generation cohort

This is the historical first balanced tranche: 90 unique slots across three providers, six tasks and five P0/S1/S2/W1/W2 information conditions, with trial 1 only. The original broader 270-request plan was **not completed**. The checked primary outcome data contain 85 saved, numerically accepted candidates and five invalid generations. The 175 CSV rows are 170 candidate-size measurements plus five terminal generation failures, rather than 175 generated programs.

The exact saved CUDA bytes and launch BLOCK values are in [candidate-index.json](candidate-index.json) and `candidates/`. [plan.json](plan.json) retains the actual prompts, settings and numerical protocol with operational metadata omitted. Historical UTC values and completion flags describe that run; they are not evidence of a new execution during this publication.

The plaintext research implementations are in `tools/research_protocols/gpu004/`: numerical core, lower-level strict worker, inference support, multimodel protocol, Batch controller and sanitizer recovery. Source pack and third-party provenance are inspected; adapted/upstream originals and the PolyBench/ACC and underlying PolyBench licenses are included under `originals/` and `licenses/`. No project-wide license has been changed.

The public executor copies use sample allocation fields and freshly pinned plaintext dependencies. They are not byte-identical to the original deployment runners. Twenty-seven numerical, validation, timing and selection symbols across the shared core/worker and GPU005 implementation retain their exact original source bytes; see [GPU005 publication provenance](../gpu005/publication-provenance.json). Historical private cache, approval and repair-prefix bindings are intentionally not reissued. The public legacy runtime/repair entrypoints are not advertised as ready to run.

Use local saved data only:

```sh
python -B -m tools.research_protocols.gpu005.analyze
python -B -m unittest tools.research_protocols.gpu005.test_offline -v
```

The former L4 allocation is ended. These commands perform no network request, generation, GPU job, CUDA build or performance measurement. Raw API envelopes, account ledgers/approval state, compiled artifacts and raw timing archives remain outside normal Git. Validation was finite testing, not a formal equivalence proof.
