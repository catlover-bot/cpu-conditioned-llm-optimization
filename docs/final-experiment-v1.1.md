# Final CPU-conditioned experiment protocol v1.1

This revision changes only the exhaustive performance-size scope using a
reference-only resource feasibility rule fixed before any final candidate
timing.

## Main exhaustive atlas

- PolyBench/C 4.2.1-beta
- 30/30 kernels
- MINI, SMALL, MEDIUM
- 90 benchmark instances
- 1,580 candidate IDs across kernels
- 4,740 candidate-instance pairs

## Resource decision

The original v1 protocol proposed all five standard sizes.

Haswell reference-only preflight:
- 150 planned reference instances
- 120 completed
- 30 timed out at 10 seconds
- 0 ordinary failures
- five-size timed-kernel lower bound:
  177.122395 hours

The preregistered ordered resource rule selected the first feasible subset:
MINI + SMALL + MEDIUM.

Its reference-equivalent timed-kernel lower bound is:
0.399194 hours.

LARGE and EXTRALARGE are excluded from the exhaustive main atlas.
No candidate speedup, atlas rank, or LLM output was used for this decision.

All other v1 experimental conditions remain unchanged.
