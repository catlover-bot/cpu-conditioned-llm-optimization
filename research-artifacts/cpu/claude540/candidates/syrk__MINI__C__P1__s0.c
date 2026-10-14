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

    double *Ci = C[i];
    double *Ai = A[i];
    int jmax = i;

    for (k = 0; k < m; k++) {
      double aik = Ai[k];
      double alpha_aik = alpha * aik;
      double *Ak_col_base = &A[0][k];
      int stride = m;

      j = 0;
      for (; j <= jmax - 3; j += 4) {
        Ci[j]   += alpha_aik * A[j][k];
        Ci[j+1] += alpha_aik * A[j+1][k];
        Ci[j+2] += alpha_aik * A[j+2][k];
        Ci[j+3] += alpha_aik * A[j+3][k];
      }
      for (; j <= jmax; j++) {
        Ci[j] += alpha_aik * A[j][k];
      }
    }
  }
#pragma endscop
}
