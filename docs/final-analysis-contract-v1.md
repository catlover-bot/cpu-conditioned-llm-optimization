# Final analysis contract v1

This analysis contract is frozen before inspecting the final candidate
speedups and before any final LLM scoring.

## Performance estimate

For each measured machine-code representative:

1. Compute paired speedup as reference batch time divided by candidate batch time.
2. Take the median of the 8 paired speedups within each session.
3. Combine the two session medians with their geometric mean.

Identity has speedup exactly 1.0. Candidate IDs whose native kernel bytes are
identical to identity also receive speedup exactly 1.0. The noisy identity
measurement is used only as a measurement-quality control.

Candidate IDs producing identical kernel function bytes inherit the score of
their measured machine-code representative.

## Validity

Correctness-rejected candidates are not performance-valid and are excluded
from the oracle.

A representative invalidated by the preregistered measurement-quality rule,
and every candidate ID aliased to it, is excluded from the oracle.

These finite checks do not establish formal equivalence.

## Oracle and regret

The oracle is the maximum speedup among correctness-admitted,
measurement-valid candidates for each physical host / kernel / size instance.

Oracle regret for a valid selected candidate is:

    1 - selected_speedup / oracle_speedup

A correctness-invalid or measurement-invalid selection receives regret 1.0.

Near-oracle means within 1 percent multiplicatively of the oracle:

    selected_speedup >= oracle_speedup / 1.01

A candidate is faster than reference only when its estimated speedup is
strictly greater than 1.0.

A machine-code no-op selection is a non-identity source candidate whose
kernel function bytes are identical to identity.

## Cross-CPU separability

After the second physical CPU atlas is available, report:

- Jaccard distance between the two CPUs' near-oracle candidate sets.
- Symmetric oracle-transfer regret.

For A -> B transfer, evaluate all source candidate IDs in A's oracle set on B
and use the best valid one. If none is valid on B, transfer regret is 1.0.
The symmetric score is the mean of A -> B and B -> A.

## Anti-peeking

These rules are fixed before hidden-oracle extraction and before final LLM
evaluation.
