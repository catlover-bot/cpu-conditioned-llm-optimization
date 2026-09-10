# Physical CPU experiment protocol v1

## Research question

Under a fixed correctness contract and a fixed compiler/evaluation protocol,
does additional CPU information improve an LLM's choice of an optimization
that is beneficial on the specified physical CPU?

This protocol does **not** treat faster-but-different numerical results as a
successful optimization.

## Prompt conditions

The main CPU-information factor is separated into:

- **P0 / no additional CPU description**:
  no CPU model/specification paragraph beyond the execution contract required
  for all candidates.
- **P1 / CPU identity**:
  CPU vendor/model and microarchitecture identity only.
- **P2 / verified static specification**:
  P1 plus verified cache hierarchy, cache-line information, supported ISA
  features relevant to the experiment, core/SMT topology, and memory/NUMA
  topology when actually observed or independently verified.

Measured target-program performance counters are **not** part of P2. They are
a separate future factor.

## Correctness gate

A candidate is benchmarkable only when:

1. it builds under the fixed compiler target;
2. the declared full output/state contract matches the reference for every
   predeclared validation case;
3. negative controls demonstrate that the validation path can reject known
   wrong transformations;
4. sanitizer or runtime failures are not converted into passes.

Passing finite tests is test-based evidence, not a proof of equivalence.

## Machine-code trace

For each benchmarkable candidate, save the exact executable/object hashes and
the measured kernel function bytes.

A source-level requested transformation and a machine-code transformation are
different events. If the measured function bytes equal the reference, report
the executable-code effect as "no observed function-byte change" rather than
claiming that the requested transformation survived compilation.

## Measurement gate

The identity candidate must have the same measured kernel function bytes as
the reference.

If identity/reference paired timings show predeclared instability, retain the
run but mark the affected performance result ineligible for the main
comparison. Do not rerun until a favorable result appears.

WSL measurements remain development-only. Main performance results are
collected on single-tenant physical CPU hosts.

## Initial physical hosts

Use two substantially different x86 microarchitectures for the first main
experiment:

1. Intel Haswell-class physical server.
2. AMD Zen 2 / Ryzen PRO 3600-class physical server.

A later third host may add Intel Ice Lake / AVX-512.

The same benchmark inputs, validation contract, candidate budget, model,
generation settings, and within-host compiler settings must be held fixed
across P0/P1/P2. Compiler settings may be host-specific, but must not change
between P0/P1/P2 on the same host.

## Scope

Initial CPU dataset:
- PolyBench/C 4.2.1-beta: the six already integrated kernels, then expand.
- TSVC2: diagnostic subset only after per-loop contracts are defined.

C, LLVM IR, and Assembly are separate representation experiments. The initial
physical-host study does not conflate them.

GPU experiments are a later, separate track.
