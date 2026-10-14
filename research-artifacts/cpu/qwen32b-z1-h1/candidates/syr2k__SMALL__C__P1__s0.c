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
      double temp1 = A[j][k] * alpha;
      double temp2 = B[j][k] * alpha;
      for (j = 0; j <= i; j++)
        C[i][j] += temp1 * B[i][k] + temp2 * A[i][k];
    }
  }
#pragma endscop
}
