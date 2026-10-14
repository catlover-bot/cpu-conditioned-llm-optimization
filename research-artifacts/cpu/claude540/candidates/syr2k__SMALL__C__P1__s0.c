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

    double * restrict Crow = C[i];
    double * restrict Arow = A[i];
    double * restrict Brow = B[i];

    for (k = 0; k < m; k++) {
      double aik = Arow[k];
      double bik = Brow[k];
      double aik_alpha = aik * alpha;
      double bik_alpha = bik * alpha;
      for (j = 0; j <= i; j++) {
        Crow[j] += A[j][k]*alpha*bik + B[j][k]*alpha*aik;
      }
    }
  }
#pragma endscop
}
