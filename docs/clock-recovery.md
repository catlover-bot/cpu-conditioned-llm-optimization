# Clock-order recovery for the local pilot

This recovery fixes orchestration/auditing. It does not change candidate code,
compiler settings, generation parameters, response parsing, or kernel timers.

## Evidence and scope

The reviewed source pilot is
`runs/goal0031/local/20260910T014659.110114Z-f1bfd156`.
Its saved `frozen_utc` is `2026-09-10T02:05:59.104474+00:00`, while
`score.json` records `started_utc=2026-09-10T02:05:57.757554+00:00`.
This is an apparent reversal of 1.346920 seconds. The files do not identify the
OS-level cause of the wall-clock adjustment. The original chronology cannot be
retroactively proved by inventing monotonic timestamps.

The old score pointer was written before the final audit. When that audit
failed, the attempt was marked failed but the completed pointer remained.
Neither that pointer nor the old attempt is repaired in place.

## Procedure

After committing the reviewed code and passing the local tests:

```bash
.venv/bin/python -m cpucond pilot recover-local \
  --source-pilot runs/goal0031/local/20260910T014659.110114Z-f1bfd156 \
  --output runs/goal0031-recovery
```

`--prepare-only` copies and audits without making HTTP calls or measurements.
The full operation additionally requires the original verified Ollama server
and model metadata to remain accessible. It sends an unload request with no
prompt; it never requests a model answer. A missing/replaced server is an error,
not authorization to change the protocol or fabricate isolation evidence.

The source protocol, prompts, raw answers, import records, and acquisition bytes
are copied unchanged. A lineage record binds their hashes and the source
freeze/failed-score snapshots. Only the new runner snapshot and provenance are
changed. Both local-preflight and local-run reject a recovered cohort.

A fresh unload is appended, followed by a NEW freeze and NEW measurements.
Their same-boot monotonic clock values establish event order. UTC readings are
retained unchanged, including regression warnings. Partial clock evidence,
different boots, and reversed monotonic order are errors. A legacy record with
only UTC remains subject to the original strict UTC checks.

This is the same 20 LLM observations, not 20 new independent answers. The seven
invalid answers remain invalid. The source failed score is not used for policy
ranking. A recovery must not be repeated to select a preferred speed result.

The final score is audited before publishing `score.json`; a prepublication
failure leaves only the failed attempt and no completed pointer. New failures
are saved rather than silently deleted. The original source tree is rehashed at
the end to detect modifications.

## Limitations

Matching boot IDs and monotonic readings is local process-order evidence, not
proof of a physically isolated machine. Unload checks coordinate this runner,
not unrelated software. `development_smoke` and `publishable_benchmark=false`
remain in force. Live WSL execution, full source evidence, and the original
runtime are required to complete the actual recovery.
