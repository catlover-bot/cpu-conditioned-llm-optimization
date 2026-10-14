# Claude Sonnet 5 CPU-conditioning: Stage 13 statistical analysis

Primary analysis uses the strict matched set: identical `kernel × size × representation` groups for which P0, P1, and P2 all passed Stage-11 correctness and Stage-12 measurement-quality gates.

- Strict matched groups: **94**
- Valid performance measurements overall: **388/395**

## Primary paired contrasts

| Contrast | GM ratio | Effect | 95% paired-bootstrap CI | Wins-Ties-Losses | Sign p | Holm p |
|---|---:|---:|---:|---:|---:|---:|
| P1 / P0 | 1.0688x | +6.88% | [1.0114, 1.1421] | 53-0-41 | 0.256442 | 0.538995 |
| P2 / P0 | 1.0412x | +4.12% | [0.9944, 1.0996] | 54-0-40 | 0.179665 | 0.538995 |
| P2 / P1 | 0.9741x | -2.59% | [0.9163, 1.0181] | 50-0-44 | 0.606296 | 0.606296 |

## Kernel-balanced robustness

| Contrast | Kernel-balanced GM ratio | Effect | 95% kernel-bootstrap CI | LOKO range |
|---|---:|---:|---:|---:|
| P1 / P0 | 1.0663x | +6.63% | [1.0069, 1.1596] | [1.0363, 1.0743] |
| P2 / P0 | 1.0462x | +4.62% | [0.9839, 1.1450] | [1.0058, 1.0576] |
| P2 / P1 | 0.9811x | -1.89% | [0.9281, 1.0231] | [0.9699, 0.9925] |

## Interpretation guardrails

- A ratio above 1 means the numerator condition produced faster correct-and-measurement-valid candidates on the matched set.
- Bootstrap intervals and sign tests quantify sampling uncertainty within this benchmark set; they do not turn the finite correctness validation into a formal proof.
- Form/size/kernel analyses are exploratory and should not replace the strict matched primary analysis.
- Kernel-balanced and leave-one-kernel-out analyses are included because multiple sizes/forms from one kernel are not fully independent.

