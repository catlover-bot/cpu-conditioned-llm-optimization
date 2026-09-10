# Goal 003.2: explicit objective and schema-constrained response

This is a new, prospective development pilot. Original answers, labels and scores
are not changed. The original prompt hashes remain reproducible under the legacy
protocol. No existing decoder/parser rule is relaxed.

Two changes are made together: (1) explicitly minimize single-thread kernel
execution time under the unchanged numerical/compiler contract; (2) pass a
per-request JSON schema to Ollama's `format`, and disclose that schema in the
prompt. The request ID is required and bound to its size/trial pair; every one of
the five options remains allowed. This is not an answer key. Both none and spec
use the same schema, options, model, seed and ordering for corresponding pairs.

Comparing this pilot to the old pilot cannot isolate the effects of wording and
structured decoding. Correct JSON is not evidence of good optimization. The
labels are still tied to presentation positions, so `option_01` preference and
first-position preference cannot be separated here. These limitations apply even
if the valid-answer rate improves. A factorial study and independent label/order
permutations would be separate experiments, not a reinterpretation of this one.

Model digest, runtime, temperature, context and output budgets, trial seeds,
compiler-default generic target, candidate sources, measurement configuration and
CPU observation are preserved. A currently verified Ollama PID may be fixed in
the NEW protocol; an old protocol's PID is never edited. No model downloads,
service starts, cloud requests, Git pushes or response repairs are performed.

The 20 new research requests are preceded by 20 one-output-token technical
preflights. The latter are not research answers. New model payloads contain no
old responses, timings or measured rankings. Import uses the unchanged strict
parser; the first acquired response, including an invalid one, remains primary.
No validity-driven retry occurs. Resume retains acquired bytes.

Commands, run from the repository root after applying/committing the patch:

```bash
.venv/bin/python -m cpucond.selection_followup prepare \
  --source-pilot runs/goal0031-recovery/local/20260910T093049.843744Z-00595f7b \
  --output runs/goal0032-explicit-selection
.venv/bin/python -m cpucond.selection_followup run <printed_pilot_directory>
.venv/bin/python -m cpucond.selection_followup summary <printed_pilot_directory>
```

Preparation records `followup-state.json` outside the immutable pilot. Repeating
prepare for the same output reuses that declared pilot rather than silently
creating another cohort. `run` reuses any already acquired answers and completed
score, and unloads before freezing and independently measuring. A partial/failed
run is retained. Schema rejection, server mismatch or failed artifact checks stop
the pipeline instead of silently falling back to JSON-only decoding.

Model weights live outside the repository. All run data remain under ignored
`runs/`. Run output is `development_smoke`, `publishable_benchmark=false`.

Ollama reference (accessed 2026-09-10):
https://docs.ollama.com/capabilities/structured-outputs
https://docs.ollama.com/api/generate
