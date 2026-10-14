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
    double Cij = C[i][i] * beta;
    for (j = 0; j < i; j++)
      C[i][j] *= beta;
    for (k = 0; k < m; k++) {
      double Aik = A[i][k] * alpha;
      double Bik = B[i][k] * alpha;
      for (j = 0; j < i; j++)
        C[i][j] += A[j][k] * Bik + B[j][k] * Aik;
      Cij += A[i][k] * Bik + B[i][k] * Aik;
    }
    C[i][i] = Cij;
  }
#pragma endscop
}
