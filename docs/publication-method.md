# Publication provenance and scope

This branch assembles current local research files on a fresh checkout of the public repository's `main`. It does not merge the research branch history. The source checkout, its index and local commits, and the finalized local backup directories are retained separately.

- Source repository: `catlover-bot/cpu-conditioned-llm-optimization`.
- Source branch: `goal/0059-final-llm-prompts`.
- Source HEAD: `b2fb75f2a530f0e603237ca8aecaee7727145b2b`.
- Fresh publication base (`origin/main`): `b624bee741fc08a2f41f62053bee91326fb7a2ab`.
- Publication branch: `publish/local-research-20261014`.
- No unpublished commits were found across local branches after checking the remote heads. Important experiment code and results did exist outside tracked history, including ignored `runs/` and `external-results/`.

`docs/publication-manifest.json` enumerates every published file except itself. Each entry records the published byte count and SHA-256 and, where applicable, the original source path and hash. Paths are relative to the original repository; archive members are identified separately. A transformed public copy has its own hash. Source hashes identify provenance and are not claims that a public copy can replace a pinned original dependency.

The CPU framework keeps its existing `src/`, `tests/`, `configs/`, and `tools/research_protocols/` structure. Selected experiment resources are included explicitly even when their source directory was ignored. Cohort documents distinguish new generations from reevaluations of previously generated candidates. The publication manifest also records omitted categories and the corresponding reasons.

Embedded resources were inspected as data, without running their code. Review includes decoded base64/gzip payloads and safe inspection of archive members. Private connection settings and account operation records are excluded or replaced in documented public copies. Scientific hardware descriptions, numerical contracts, model settings, and measured results are retained where supported by source records. Any limitations of a transformed historical runner are stated with that runner.

Publication checks are offline: file inventories and hashes, syntax/structure, selected unit tests, and recomputation from saved lightweight evidence. No new model generation, provider API requests, compilation experiments, GPU execution, or connection to an ended L4 server is part of publication. Test results in older experiment documents are historical; the current publication's checks are recorded separately in `docs/publication-validation.json`.

No GitHub Actions workflow existed in the checked source or its tracked history. This branch introduces no workflow, LFS configuration, release upload, repository visibility change, or project-wide license. Included third-party material retains its own license and attribution.

The inventory verifier checks published bytes; it cannot prove numerical equivalence, reproduce excluded raw measurements, or establish that historical remote environments still exist. GPU correctness checks used finite input sets. GPU006's new candidates were evaluated on L4, and their A40 performance remains unmeasured.
