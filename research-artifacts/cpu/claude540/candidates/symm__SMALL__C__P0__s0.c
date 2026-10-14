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
      double *Crow = C[i];
      double *Brow = B[i];
      double *Arow = A[i];
      for (j = 0; j < n; j++ )
      {
        double bij = Brow[j];
        temp2 = 0;
        for (k = 0; k < i; k++) {
           C[k][j] += alpha*bij * Arow[k];
           temp2 += B[k][j] * Arow[k];
        }
        Crow[j] = beta * Crow[j] + alpha*bij * Arow[i] + alpha * temp2;
     }
   }
#pragma endscop
}
