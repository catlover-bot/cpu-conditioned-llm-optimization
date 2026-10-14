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
    double *Ci = C[i];
    for (j = 0; j <= i; j++)
      Ci[j] *= beta;
    for (k = 0; k < m; k++) {
      double Aik = A[i][k];
      for (j = 0; j <= i; j++)
        Ci[j] += alpha * Aik * A[j][k];
    }
  }
#pragma endscop
}
