#ifndef CPUCOND_KERNEL_H
#define CPUCOND_KERNEL_H

#include <stddef.h>

/* Independent, hand-written gemm_smoke fixture; not a PolyBench kernel.
 * a, b and c address distinct, contiguous row-major n-by-n double matrices.
 * Each call replaces all c elements with a*b, accumulating each dot product
 * in increasing k order. The smoke contract requires IEEE-754 binary64.
 */
#if defined(__GNUC__) || defined(__clang__)
#define CPUCOND_NOINLINE __attribute__((noinline))
#else
#define CPUCOND_NOINLINE
#endif

CPUCOND_NOINLINE void kernel(size_t n, const double *a, const double *b, double *c);

#endif
