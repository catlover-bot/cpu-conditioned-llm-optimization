#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_lu(int n,
        double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
    for (j = 0; j < i; j++) {
      double sum = 0.0;
      for (k = 0; k < j; k++) {
        sum += A[i][k] * A[k][j];
      }
      A[i][j] = (A[i][j] - sum) / A[j][j];
    }
    for (j = i; j < n; j++) {
      double sum = 0.0;
      for (k = 0; k < i; k++) {
        sum += A[i][k] * A[k][j];
      }
      A[i][j] -= sum;
    }
  }
#pragma endscop
}
