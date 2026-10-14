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
      for (j = 0; j < n; j++ )
      {
        temp2 = 0;
        double Bij = B[i][j];
        double *Cj_row;
        for (k = 0; k < i; k++) {
           double aik = A[i][k];
           C[k][j] += alpha*Bij * aik;
           temp2 += B[k][j] * aik;
        }
        C[i][j] = beta * C[i][j] + alpha*Bij * A[i][i] + alpha * temp2;
        (void)Cj_row;
     }
   }
#pragma endscop
}
