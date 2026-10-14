# GPU006: saved L4 cohort

The fixed cohort contains 270 requests:90 each for Qwen, GPT and Claude. Saved files establish 255 CUDA/BLOCK candidates and 15 generation-format failures. All 270 slots reached terminal processing. 253 candidates meet every recorded L4 measurement-quality condition; the two remaining saved candidates retain their invalid measurement flags. L4 evaluation has finished and the server is retired. New candidate A40 measurements were never performed.

The data are finite bitwise/Sanitizer tests and recorded timings, not a formal equivalence proof. CPU, GPU005 and this GPU006 cohort must be counted separately. Model generations occurred through different backends/dates; within-model condition contrasts retain matched task/trial/shape cells.

Run from the repository root, without network or a compiler:

```bash
python3 -B tools/research_protocols/gpu006/reanalyze.py --check
python3 -B -m unittest discover -s tools/research_protocols/gpu006 -p test_public_data.py
python3 -B -m unittest discover -s runs/gpu006-backup-v1 -p test_verify_backup.py
```

`slots.csv` keeps all 270 slots and explicit failures. `measurements.csv` keeps 1020 original/frozen-selection cells, including the two invalid cells. `paired-contrasts.csv` contains 800 matched comparisons. `compiled-identities.csv` preserves 1275 compiler-result hashes/options without PTX/cubin payloads. `candidates/` holds 255 exact saved CUDA files; `candidates.json` preserves their IDs, BLOCKs and SHA-256. `prompts.jsonl` holds the 270 exact research message sequences. `protocol.json` records models, conditions, seeds where configured, numerical contract, allowed BLOCKs and shapes.

`reference/` retains original and upstream CUDA plus original licenses and source manifests. Numerical worker definitions and the C oracle/helper are plaintext projections under `tools/research_protocols/gpu006/`; they contain no encoded legacy deployment bootstrap. GPU/compiler functions are preserved as source but are not called by public analysis/tests.

Generic Batch transport/controller and archival analysis source remains under `runs/gpu006-cloud180-v1/`. The public common module explicitly refuses private deployment validation. The exact pre-generation plan/drafts under `runs/gpu006-target-info-v1/inputs/` support offline transport fixtures; their pending flags describe the immutable design snapshot, not current experiment completion. No live runner/start launcher, private target configuration, billing approval, account ledger or raw provider response is published. Historical source pins remain provenance references; flattened/public copies do not claim the private originals' hashes or reconstruct their live deployment.

`backup-reference.json` identifies the finalized six local TARs and proof hashes. Both local copies are separately retained read-only; physical storage independence is not verified. The roughly 900MB TARs, model weights, runtime/build caches, PTX/cubin, raw timing/process logs, account/native response IDs and connection records are excluded from normal Git. The standalone backup verifier/auditor source is included for owners of those original archives; this publication alone does not supply the full private backup input.

Generic fixture checks:

```bash
python3 -B -m unittest discover -s runs/gpu006-cloud180-v1 -p test_providers.py
python3 -B -m unittest discover -s runs/gpu006-cloud180-v1 -p test_controller.py
python3 -B -m unittest discover -s runs/gpu006-cloud180-v1 -p test_pilot.py
```

The fixture-only target is a non-live sample and is not evidence of original deployment validation. Four controller tests requiring omitted private deployment bundles are explicitly skipped. The pilot format-failure regression retains API acceptance, terminal slot and no-repeat assertions; its private worker handoff is omitted. The original live CLI/worker suites require the private runner and are not part of this public test selection.
