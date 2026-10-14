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
      double *Crow_i = C[i];
      double *Brow_i = B[i];
      for (j = 0; j < n; j++) {
         double temp2 = 0;
         double alpha_Bij = alpha * Brow_i[j];
         for (k = 0; k < i; k++) {
            double Aik = A[i][k];
            C[k][j] += alpha_Bij * Aik;
            temp2 += B[k][j] * Aik;
         }
         Crow_i[j] = beta * Crow_i[j] + alpha_Bij * A[i][i] + alpha * temp2;
      }
   }
#pragma endscop
}
