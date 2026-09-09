"""One deterministic family that interleaves independent GEMM outputs.

The existing reference is i -> j -> k. The family's common baseline is
``unroll_1``: i -> j blocks -> k, with a scalar remainder loop. A block owns
one accumulator per output column, and every accumulator sees exactly the
reference's increasing-k multiply/add sequence. Larger factors only increase
the number of independent columns in that same template; they never split a
single output's reduction. Comparing the family baseline to the reference is
distinct from comparing factors 2..16 to the family baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


FACTORS = (1, 2, 4, 8, 16)
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAMILY_DESCRIPTION = (
    "gemm_smoke independent output-column unrolling; reference loop order i-j-k; "
    "common generated baseline unroll_1 uses i-jblocks-k and scalar remainder; "
    "each output retains a single accumulator and increasing-k operations. "
    "Within the generated family only the block's output-column count changes."
)


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    unroll_factor: int | None
    origin: str
    role: str
    source: str
    comparison_baseline: str


def generate_unrolled(factor: int) -> str:
    """Generate the shared template for one supported integer factor.

    ``n - j >= factor`` avoids unsigned underflow/overflow: j starts at zero
    and only advances when the full block fits. The tail is the same scalar
    loop for every factor, including n smaller than the factor. No restrict,
    alignment, FP pragmas, or compiler tuning depends on the chosen factor.
    """
    if type(factor) is not int or factor not in FACTORS:
        raise ValueError(f"unroll factor must be one of {FACTORS}")
    lines = [
        '#include "kernel.h"',
        "",
        "/* Deterministically generated independent-output template. */",
        "CPUCOND_NOINLINE void kernel(size_t n, const double *a, const double *b, double *c)",
        "{",
        "    for (size_t i = 0; i < n; ++i) {",
        "        size_t j = 0;",
        f"        for (; n - j >= {factor}; j += {factor}) {{",
    ]
    lines.extend(f"            double sum_{lane} = 0.0;" for lane in range(factor))
    lines.append("            for (size_t k = 0; k < n; ++k) {")
    lines.extend(
        f"                sum_{lane} += a[i * n + k] * b[k * n + j + {lane}];"
        for lane in range(factor)
    )
    lines.append("            }")
    lines.extend(f"            c[i * n + j + {lane}] = sum_{lane};" for lane in range(factor))
    lines.extend([
        "        }",
        "        for (; j < n; ++j) {",
        "            double sum = 0.0;",
        "            for (size_t k = 0; k < n; ++k) {",
        "                sum += a[i * n + k] * b[k * n + j];",
        "            }",
        "            c[i * n + j] = sum;",
        "        }",
        "    }",
        "}",
        "",
    ])
    return "\n".join(lines)


def make_candidates() -> list[Candidate]:
    """Return the full predeclared candidate set, with controls kept intact."""
    reference = (FIXTURES / "reference.c").read_text(encoding="utf-8")
    candidates = [
        Candidate("reference", None, "handwritten_fixture", "reference", reference, "reference"),
        Candidate("identity", None, "handwritten_fixture", "identity_control", reference, "reference"),
    ]
    candidates.extend(
        Candidate(
            f"unroll_{factor}", factor, "deterministic_generator", "transformation",
            generate_unrolled(factor), "reference" if factor == 1 else "unroll_1",
        )
        for factor in FACTORS
    )
    candidates.append(Candidate(
        "deliberately_wrong", None, "handwritten_fixture", "negative_control",
        (FIXTURES / "deliberately_wrong.c").read_text(encoding="utf-8"), "reference",
    ))
    return candidates
