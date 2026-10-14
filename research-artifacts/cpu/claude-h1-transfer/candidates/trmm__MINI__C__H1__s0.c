#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_trmm(int m, int n,
   double alpha,
   double A[ m + 0][m + 0],
   double B[ m + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < m; i++) {
    for (k = i+1; k < m; k++) {
      double a = A[k][i];
      for (j = 0; j < n; j++)
        B[i][j] += a * B[k][j];
    }
    for (j = 0; j < n; j++)
      B[i][j] = alpha * B[i][j];
  }
#pragma endscop
}
