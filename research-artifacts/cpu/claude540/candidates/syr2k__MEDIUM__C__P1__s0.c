#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_syr2k(int n, int m,
    double alpha,
    double beta,
    double C[ n + 0][n + 0],
    double A[ n + 0][m + 0],
    double B[ n + 0][m + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;

    double * restrict Ci = C[i];
    const double * restrict Ai = A[i];
    const double * restrict Bi = B[i];

    for (k = 0; k < m; k++) {
      double aik_alpha = alpha * Ai[k];
      double bik_alpha = alpha * Bi[k];
      const double * restrict Ak = A[0] + k; // not directly usable due to stride m
      for (j = 0; j <= i; j++) {
        Ci[j] += A[j][k]*alpha*Bi[k] + B[j][k]*alpha*Ai[k];
      }
    }
  }
#pragma endscop
}
