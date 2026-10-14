#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_cholesky(int n,
       double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
     double sum;
     for (j = 0; j < i; j++) {
        sum = 0.0;
        for (k = 0; k < j; k++) {
           sum += A[i][k] * A[j][k];
        }
        A[i][j] = (A[i][j] - sum) / A[j][j];
     }
     sum = 0.0;
     for (k = 0; k < i; k++) {
        sum += A[i][k] * A[i][k];
     }
     A[i][i] = sqrt(A[i][i] - sum);
  }
#pragma endscop
}
