# GPU005 saved-source portability and launch selection

GPU005 reevaluates the **same 85 saved GPU004 candidates** from the historical 90-slot first-trial cohort. It makes zero new generation calls and preserves the five primary invalid generations in each 90-row coverage table. These are additional measurements of existing sources, not another set of generated candidates. The historical A40/V100 prompt-condition labels remain unchanged when sources run on L4.

The `a40/` and `l4/` folders each include 340 comparison rows for 85 measured IDs, the 90-slot coverage, 176 control cells, frozen launch selection, protocol and hardware/toolchain facts. A40 has 176 valid control cells; L4 has 174. The included results preserve those validity decisions. Selection uses exploration only; confirmation is separate. The L4 POSIX storage recovery changed storage/permissions handling, not the numerical contract. No selective remeasurement or new experiment occurred during publication.

The exact candidates and third-party originals/licenses are shared with [GPU004](../gpu004/README.md), and [cohort-provenance.json](cohort-provenance.json) records this reuse. [publication-provenance.json](publication-provenance.json) distinguishes original source/archive hashes from public-copy hashes and lists 27 verbatim numerical/validation/timing/search symbols.

Actual research implementations are in `tools/research_protocols/gpu005/portability.py` and `posix_recovery.py`, with the shared plain numerical worker in `tools/research_protocols/gpu004/`. Public samples omit actual endpoints, host keys, Pod IDs and GPU instance UUIDs while retaining hardware facts and measured values. Plaintext code dependencies have updated, verified public SHA256 pins; original research-data identities remain separately recorded. Legacy cache/authorization/full-evidence and repair bindings need the private originals and a newly verified allocation; these historical entrypoints were not run or represented as a ready replay.

Offline inspection:

```sh
python -B -m tools.research_protocols.gpu005.analyze
python -B -m unittest tools.research_protocols.gpu005.test_offline -v
```

Only local lightweight artifacts are read. The L4 allocation is ended. UTC/completion fields are historical, and finite numerical checks are not formal equivalence proofs. Full archives, raw API responses, compiled PTX/cubin/runtime binaries, operational ledgers and approvals are retained locally, excluded from normal Git, and have not been modified.
