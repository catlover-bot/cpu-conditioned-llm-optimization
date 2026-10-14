# CPU-conditioned LLM optimization

This research studies how hardware information in a prompt changes generated code, launch settings, correctness, and performance. CPU optimization is the primary study; GPU004/005/006 extend the question to A40/L4 CUDA experiments. The comparisons concern information conditions within each model, with generation failures and valid performance results reported separately.

This publication branch contains current research code and selected lightweight evidence. Cohort notes distinguish candidate generation, fixed-candidate exploration, and reevaluation; their counts must not be summed as independent new generations.

| Area | Code and evidence |
| --- | --- |
| CPU framework, CLI, tests, contracts | [`src/cpucond/`](src/cpucond/), [`tests/`](tests/), [`configs/`](configs/), [`tools/research_protocols/`](tools/research_protocols/) |
| CPU prompts, reference/candidate code, atlas and LLM cohorts | [`research-artifacts/cpu/`](research-artifacts/cpu/) |
| GPU004 generation and numerical evaluation | [`tools/research_protocols/gpu004/`](tools/research_protocols/gpu004/), [`research-artifacts/gpu004/`](research-artifacts/gpu004/) |
| GPU005 A40/L4 reevaluation | [`tools/research_protocols/gpu005/`](tools/research_protocols/gpu005/), [`research-artifacts/gpu005/`](research-artifacts/gpu005/) |
| GPU006 fixed experiment and L4 results | [`tools/research_protocols/gpu006/`](tools/research_protocols/gpu006/), [`runs/gpu006-cloud180-v1/`](runs/gpu006-cloud180-v1/), [`research-artifacts/gpu006/`](research-artifacts/gpu006/) |

GPU006 covers **270 requests, 255 saved candidates, and 15 generation-invalid requests**. L4 processing is complete; 253 candidate slots have valid performance evidence. New candidates' **A40 evaluation was not performed**. Finite correctness testing is not a formal equivalence proof, and L4-only results do not establish adaptation in both GPU directions.

## Offline use

Use Python 3.12 or later. The inventory check uses only the standard library:

```bash
python3 -B tools/verify_publication.py
python3 -B research-artifacts/cpu/offline_summary.py
python3 -B -m tools.research_protocols.gpu005.analyze
python3 -B tools/research_protocols/gpu006/reanalyze.py --check
```

These commands verify the file inventory and recompute saved CPU/GPU004/GPU005/GPU006 summaries, without APIs, compilation, or server access. See the cohort README files for offline recomputation from included tables, provenance, and limitations. CPU development tests use the `dev` extra from `pyproject.toml`; the exact inspected test selection and this publication's actual results are recorded in [`docs/publication-validation.json`](docs/publication-validation.json). Historical test counts in experiment records are separate from those checks.

**L4 usage has ended.** Normal analysis requires no server connection. Historical execution code is preserved for inspection; any public sample configurations and differences from fixed-hash originals are documented beside the code. Do not treat old operational instructions as an available server or as evidence of a new run.

Large raw archives, model weights, builds, raw API responses, bulk timing/PTX/cubin, credentials, and account operation records are outside this Git publication. The original local data and the verified six-archive GPU006 preservation set remain separate. See [`docs/data-availability.md`](docs/data-availability.md) for scope and reference hashes, and [`docs/publication-method.md`](docs/publication-method.md) for source commits and public-copy provenance. Third-party sources retain their original licenses; no project-wide license is introduced here.
