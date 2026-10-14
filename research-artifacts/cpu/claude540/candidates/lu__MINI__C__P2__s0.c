#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_lu(int n,
        double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
    for (j = 0; j <i; j++) {
       double *Ai = A[i];
       double sum = Ai[j];
       for (k = 0; k < j; k++) {
          sum -= Ai[k] * A[k][j];
       }
       Ai[j] = sum / A[j][j];
    }
   for (j = i; j < n; j++) {
       double *Ai = A[i];
       double sum = Ai[j];
       for (k = 0; k < i; k++) {
          sum -= Ai[k] * A[k][j];
       }
       Ai[j] = sum;
    }
  }
#pragma endscop
}
