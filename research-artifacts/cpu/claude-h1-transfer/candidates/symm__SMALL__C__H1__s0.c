#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_symm(int m, int n,
   double alpha,
   double beta,
   double C[ m + 0][n + 0],
   double A[ m + 0][m + 0],
   double B[ m + 0][n + 0])
{
  int i, j, k;
  double temp2;
#pragma scop
   for (i = 0; i < m; i++) {
      double *Ci = C[i];
      double *Bi = B[i];
      double *Ai = A[i];
      for (j = 0; j < n; j++ )
      {
        double alpha_Bij = alpha * Bi[j];
        temp2 = 0;
        for (k = 0; k < i; k++) {
           C[k][j] += alpha_Bij * Ai[k];
           temp2 += B[k][j] * Ai[k];
        }
        Ci[j] = beta * Ci[j] + alpha_Bij * Ai[i] + alpha * temp2;
     }
   }
#pragma endscop
}
