#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_cholesky(int n,
       double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
     for (j = 0; j < i; j++) {
        double *Ai = A[i];
        double *Aj = A[j];
        double sum = Ai[j];
        for (k = 0; k < j; k++) {
           sum -= Ai[k] * Aj[k];
        }
        Ai[j] = sum / Aj[j];
     }
     {
        double *Ai = A[i];
        double sum = Ai[i];
        for (k = 0; k < i; k++) {
           sum -= Ai[k] * Ai[k];
        }
        Ai[i] = sqrt(sum);
     }
  }
#pragma endscop
}
