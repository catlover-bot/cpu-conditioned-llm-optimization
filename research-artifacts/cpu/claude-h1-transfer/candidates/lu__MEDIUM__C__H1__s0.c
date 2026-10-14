#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_lu(int n,
        double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
    double * restrict Ai = A[i];
    for (j = 0; j < i; j++) {
       double s = Ai[j];
       for (k = 0; k < j; k++) {
          s -= Ai[k] * A[k][j];
       }
       Ai[j] = s / A[j][j];
    }
    for (j = i; j < n; j++) {
       double s = Ai[j];
       for (k = 0; k < i; k++) {
          s -= Ai[k] * A[k][j];
       }
       Ai[j] = s;
    }
  }
#pragma endscop
}
