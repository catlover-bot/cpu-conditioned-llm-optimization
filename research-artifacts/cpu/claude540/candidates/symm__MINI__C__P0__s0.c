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
      double *Arow = A[i];
      double *Brow = B[i];
      double *Crow = C[i];

      for (j = 0; j < n; j++)
         Crow[j] = beta * Crow[j] + alpha * Brow[j] * Arow[i];

      for (k = 0; k < i; k++) {
         double aik = Arow[k];
         double *Crow_k = C[k];
         double *Brow_k = B[k];
         double a_bik = alpha * aik;
         for (j = 0; j < n; j++) {
            Crow_k[j] += alpha * Brow[j] * aik;
            Crow[j] += a_bik * Brow_k[j];
         }
      }
   }
#pragma endscop
}
