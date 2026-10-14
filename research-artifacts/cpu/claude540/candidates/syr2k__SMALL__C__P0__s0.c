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
      double aik = alpha * Arow[k];
      double bik = alpha * Brow[k];
      for (j = 0; j <= i; j++) {
        Crow[j] += A[j][k]*bik + B[j][k]*aik;
      }
    }
  }
#pragma endscop
}
