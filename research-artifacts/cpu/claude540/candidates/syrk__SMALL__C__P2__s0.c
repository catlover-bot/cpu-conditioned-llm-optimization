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
    int jlim = i + 1;

    for (k = 0; k < m; k++) {
      double aik_alpha = alpha * Ai[k];
      double *Ak = A[k >= 0 ? 0 : 0]; // placeholder, replaced below
      (void)Ak;
      const double *Acol; // A[j][k] access, A is row-major [n][m]
      for (j = 0; j < jlim; j++) {
        Ci[j] += aik_alpha * A[j][k];
      }
    }
  }
#pragma endscop
}
