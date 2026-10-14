#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_syrk(int n, int m,
   double alpha,
   double beta,
   double C[ n + 0][n + 0],
   double A[ n + 0][m + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
    double * restrict Ci = C[i];
    for (j = 0; j <= i; j++)
      Ci[j] *= beta;

    const double * restrict Ai = A[i];

    int j2 = 0;
    for (; j2 + 1 <= i; j2 += 2) {
      double acc0 = Ci[j2];
      double acc1 = Ci[j2 + 1];
      const double * restrict Aj0 = A[j2];
      const double * restrict Aj1 = A[j2 + 1];
      for (k = 0; k < m; k++) {
        double aik = Ai[k];
        acc0 += alpha * aik * Aj0[k];
        acc1 += alpha * aik * Aj1[k];
      }
      Ci[j2] = acc0;
      Ci[j2 + 1] = acc1;
    }
    for (j = j2; j <= i; j++) {
      double acc = Ci[j];
      const double * restrict Aj = A[j];
      for (k = 0; k < m; k++) {
        acc += alpha * Ai[k] * Aj[k];
      }
      Ci[j] = acc;
    }
  }
#pragma endscop
}
