# CPU research artifacts

This directory contains selected lightweight CPU evidence and original/candidate source. It is not a complete raw-data backup. Finite recorded validation is not a formal equivalence proof. Hardware-information conditions, source representation, inference backend and repeated evaluation cohorts remain separate.

Run from the repository root with Python3.12 or newer:

    PYTHONDONTWRITEBYTECODE=1 python3 research-artifacts/cpu/offline_summary.py

This command reads local CSV/JSON, checks identity/count joins, and recomputes Qwen14B geometric means from per-request speedups. It does not generate code, call a model/API, compile, benchmark, or connect to a server. The retired L4 server is unnecessary. Historical executors under runs/ and tools/research_protocols/ are source records; their default experiment/launch actions are not part of this offline command.

| Evidence directory | Original scope | Included terminal result scope | Interpretation |
| --- | --- | --- | --- |
| atlas/ | 30 kernels x 3 sizes = 90 instances, 4,740 fixed candidate rows per host | Haswell E3-1241v3 and Zen2 2 x EPYC7402 aggregate/machine-code summaries and hidden-oracle CSVs | Same non-LLM candidate space evaluated on two CPUs; rows are not LLM generations. |
| comparison/ |90 paired instances;4740 candidate IDs matched on each host | Instance/kernel CSVs and historical analysis source | Same candidate space; descriptive results do not establish statistical significance. |
| qwen14b-a40-inference/ |900 accounted CPU-candidate slots: 90 already-accounted CPU-inference prefix plus 810 A40-inference suffix |895 saved,804 correctness-eligible,758 valid performance; slot/backend-paired CSVs |Qwen2.5-Coder14B Q4_K_M generates CPU C/IR here. A40 labels inference hardware, not GPU-kernel evaluation. Re-exported evaluations do not add generation calls. |
| qwen32b-526-revalidation/ |526 earlier Qwen32B slots: P0=166,P1=180,P2=180;525 saved |Later read-only ledger admits351 recorded checks;346 historical timings and5 missing valid timings |Audit/recheck of earlier generations, not526 new calls. Historical generation snapshots preserve earlier labels/runtime caveats. |
| qwen32b-z1-h1/ |180 paired evaluation slots: 90 reused P1/Z1 C candidates from the earlier 526-slot ledger plus 90 H1 comparison candidates |144 correctness-eligible, 136 valid performance; 180 outcome records and 180 saved C candidates |Fresh paired timing of saved code, with zero new model calls in this export; not 180 independent new generations. All 90 reused IDs/source hashes are checked against the earlier ledger. |
| claude540/ |540 official requests;515 saved C/IR candidates,25 invalid generations |395 correctness-eligible,388 valid performance,7 invalid measurements; all validation/measurement projections and stage13 statistics |Archived native draft model is claude-sonnet-5; output cap4096,thinking disabled. Prepared bytes do not prove runtime parameter acceptance/influence. |
| claude-h1-transfer/ |Separate90-request wrong-CPU H1 generation |88 saved C candidates plus generation/failure summaries |This export reports no numerical/performance evaluation at its generation stage; do not borrow another cohort's results. |
| prompts/,input-corpus/ |540 logical prepared prompts;180 neutral C/IR documents for90 instances |Selected full prepared corpus/manifests |File counts are documents, not completed calls/trials. Planned three independent samples is planning metadata, not realized generations. |

Model/runtime and recorded condition/trial/task/dataset labels remain in historical plans/summaries. Candidate spaces differ between the atlas and the generation cohorts; their speedups cannot be pooled as one experiment. Performance statistics condition on valid subsets; failures remain in each full request denominator.

upstream/polybench-c-4.2.1-beta/ retains the small benchmark C/header sources, utilities, authors and original Ohio State University software license. Prepared C/IR prompts and candidate code retain that benchmark provenance. No new project-wide license is asserted.

Selected historical runners/dependencies retain their runs/... and tools/research_protocols/ layouts. Publication copies replace private paths/destinations/native account identifiers with samples: reserved192.0.2.1, researcher home paths, allzero GPU UUID and PUBLIC_HOST_KEY_FINGERPRINT. These are not functioning server settings. Embedded Python was decoded and parsed without execution before sanitization. Edited public module hashes differ from originals; old fixed binding checks identify archived bytes and cannot certify edited public modules. tools/research_protocols/manifest.json distinguishes original_source_sha256 and published_sha256.

Historical source/object/response/bundle hashes identify locally retained originals. They are not hashes of sanitized publication copies or evidence that omitted archives are present. Public terminal projections omit raw timing pairs, validation output/command records and native API responses; this branch cannot perform complete raw replay alone.

Large CPU exports, weights/runtime/build caches, compiled objects, raw timing/validation logs, API responses, billing approvals/operational ledgers and retired server wrappers remain excluded and are not deleted. GPU006 finalized backup scope is documented separately in docs/data-availability.md; it is not a backup of every historical CPU export.

The inspected 16-module CPU offline allowlist passed 402 tests against this publication source copy, with bytecode and pytest cache disabled. It excludes compiler/benchmark fixtures, including unmarked ones. Publication verification records the exact command and excluded modules; historical test totals are not reused.

Generation-count provenance: the original Qwen14B handoff assignment explicitly records a 90-slot existing CPU prefix and existing_candidates_regenerated=false; the 810 suffix rows record old_answers_reused=false. The exported 900 outcomes include that prefix once. Claude H1 generation/transfer summaries refer to the same 90-request H1 batch (88 saved, 2 invalid); a transfer copy is not another 90 generations. Its prepared request provenance uses the earlier Claude batch as a prompt template, which is not evidence of reused model responses. No generation totals are summed across these artifacts, and identical source hashes alone are not treated as proof of generation reuse.
