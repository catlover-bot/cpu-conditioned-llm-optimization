#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_cholesky(int n,
       double A[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < n; i++) {
     double *Ai = A[i];
     for (j = 0; j < i; j++) {
        double *Aj = A[j];
        double sum = Ai[j];
        for (k = 0; k < j; k++) {
           sum -= Ai[k] * Aj[k];
        }
        Ai[j] = sum / Aj[j];
     }
     double diag = Ai[i];
     for (k = 0; k < i; k++) {
        diag -= Ai[k] * Ai[k];
     }
     Ai[i] = sqrt(diag);
  }
#pragma endscop
}
