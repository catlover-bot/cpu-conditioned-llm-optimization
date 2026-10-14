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
    for (k = 0; k < m; k++) {
      double aik_alpha = A[i][k]*alpha;
      double bik_alpha = B[i][k]*alpha;
      double *Ck = C[i];
      const double *Ak = A[0] + k;
      const double *Bk = B[0] + k;
      for (j = 0; j <= i; j++)
        {
          Ck[j] += Ak[(size_t)j * m]*alpha*B[i][k] + Bk[(size_t)j * m]*alpha*A[i][k];
        }
    }
  }
#pragma endscop
}
