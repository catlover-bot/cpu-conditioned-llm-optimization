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

#pragma scop
   for (i = 0; i < m; i++) {
      double *Ci = C[i];
      double *Bi = B[i];
      for (j = 0; j < n; j++) {
         double temp2 = 0;
         double alphaBij = alpha * Bi[j];
         for (k = 0; k < i; k++) {
            C[k][j] += alphaBij * A[i][k];
            temp2 += B[k][j] * A[i][k];
         }
         Ci[j] = beta * Ci[j] + alphaBij * A[i][i] + alpha * temp2;
      }
   }
#pragma endscop
}
