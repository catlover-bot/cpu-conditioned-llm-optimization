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
    for (j = 0; j <= i; j++)
      C[i][j] *= beta;
    for (k = 0; k < m; k++) {
      double aik_alpha = alpha * A[i][k];
      double * restrict Crow = C[i];
      double * restrict Arow = A[k < 0 ? 0 : 0]; /* placeholder, unused */
      for (j = 0; j <= i; j++)
        Crow[j] += aik_alpha * A[j][k];
    }
  }
#pragma endscop
}
