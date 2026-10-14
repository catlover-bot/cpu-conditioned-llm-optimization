# Data availability

This Git branch publishes research code and selected lightweight results for the CPU study and GPU004/005/006. It is not a complete backup of every local research artifact.

The original local research tree and both finalized copies of `cpucond-l4-20261013T215322Z` are retained separately: one in the Linux backup directory and one in the Windows `ResearchBackups` directory. Publication does not edit their manifest, checksums, receipts, or archive contents. Their absolute personal paths and private server bindings are not part of this repository.

## Finalized GPU006 preservation set

The finalized set contains six TAR archives totaling **899,901,440 bytes**. The finalization record reports `complete: true`; the checksum list has 25 entries per copy. The public reference file at `research-artifacts/gpu006/backup-reference.json` lists original archive byte counts and SHA-256 hashes. These identify the separately preserved originals, not sanitized public copies.

| Original metadata file | SHA-256 |
| --- | --- |
| `manifest.json` | `c6942ccd6b2a3d2cf9c5ecd3973cf0c30298c9ca9674563b6aeabd13cff69a3b` |
| `BACKUP_FINALIZATION.json` | `13e32f5d66d3800ea33aa232d1a7b0628c6fbc5db94dab4ba59c720e49e2ce26` |
| `SHA256SUMS` | `fa84c0b57ebc342dfa0f4ed24a54c7767b1bf3b96ae81821bd6ef92597007dd6` |

The preservation set includes local GPU006 research and results, remote result checkpoints, and reproduction resources, plus the final small repair archives. Its scope is defined by its original manifest. It does not establish that every CPU experiment or every older GPU artifact is included in those six archives. Other local CPU results and preservation archives remain in the original research storage.

## Included and omitted material

The publication inventory identifies selected code, tests, numerical contracts, prompts, small reference/candidate sources, third-party licenses, and per-task/condition/trial summaries. Cohort notes explain which results are new generations and which reevaluate existing candidates. Public copies that omit operational metadata have distinct hashes and documented transformations.

Large backup TARs, model weights, build trees, runtime caches, bulk PTX/cubin and raw timing logs, raw provider responses, account/billing approvals and ledgers, credentials, private connection settings, process locks, and temporary files are excluded from ordinary Git history. No original is deleted as a result of this selection. No Git LFS or GitHub Release upload is used.

Offline commands in the README operate on included lightweight evidence. Reproducing every original numerical or timing result would additionally require the separately held raw data and a suitable fresh environment. L4 usage has ended; no old server connection is required or attempted. GPU006 new candidates' A40 results remain unmeasured, and finite correctness tests are not a formal equivalence proof.
