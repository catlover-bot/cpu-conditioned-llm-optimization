# Final experiment protocol v1.3

This amendment changes only the physical Haswell host.

The original Xeon E3-1240 v3 server was terminated by the provider after
the prepaid balance expired. Its incomplete 59+/90 final-atlas run is
invalid and will not be combined with replacement-host measurements.

Replacement host:
- Intel Xeon E3-1241 v3
- Haswell
- family 6, model 60, stepping 3
- 4 cores / 8 hardware threads before SMT disable
- 3.5 GHz base clock
- 32 KiB L1D/core
- 32 KiB L1I/core
- 256 KiB L2/core
- 8 MiB shared L3
- 64-byte cache line
- AVX / AVX2 / FMA

No final candidate performance on the replacement host was observed before
this amendment.

The dataset, 30x3 scope, 1,580 candidate IDs, 4,740 candidate-instance
pairs, correctness contract, measurement rules, and LLM conditions are
unchanged.
