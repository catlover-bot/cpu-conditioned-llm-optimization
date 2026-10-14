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
      double *Ai = A[i];

      for (j = 0; j < n; j++)
         Ci[j] = beta * Ci[j] + alpha * Bi[j] * Ai[i];

      for (k = 0; k < i; k++) {
         double aik = Ai[k];
         double alpha_aik = alpha * aik;
         double *Ck = C[k];
         double *Bk = B[k];

         for (j = 0; j < n; j++) {
            Ck[j] += alpha * Bi[j] * aik;
            Ci[j] += alpha_aik * Bk[j];
         }
      }
   }
#pragma endscop
}
