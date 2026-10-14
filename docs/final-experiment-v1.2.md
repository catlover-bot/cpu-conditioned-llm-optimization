# Final experiment protocol v1.2

v1.2 does not change the frozen performance scope, candidate space,
hardware conditions, LLM conditions, or resource decision.

Main exhaustive atlas:
- PolyBench/C 4.2.1-beta
- 30 kernels
- MINI / SMALL / MEDIUM
- 90 instances
- 1,580 candidate IDs across kernels
- 4,740 candidate-instance pairs

Correctness evidence is explicitly separated:

1. Main 30x3 gate
   - official PolyBench initializer
   - exact lossless values for every official live-out array
   - O0 oracle
   - generic O3, native O3 -march=native, ASan/UBSan
   - candidates failing the gate are never timed

2. Six-kernel stress supplement
   - full state
   - readonly inputs
   - cancellation, signed zero, subnormals and full-mantissa finite inputs
   - reused as stronger supplementary correctness evidence

No formal equivalence is claimed.

The batch measurement is also fixed before final candidate timing:
each repetition calls the original init_array outside the timed region,
then times only the kernel with CLOCK_MONOTONIC_RAW. K is calibrated from
the reference only to >=5 ms. Identity-control failure is the only trigger
for the preregistered 20 ms whole-instance escalation.
