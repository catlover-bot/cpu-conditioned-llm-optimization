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
    double Aii = A[i][i];

    if (n > 0) {
      for (k = 0; k < i; k++) {
        double *Crow_k = C[k];
        double *Brow_k = B[k];
        double a_ik = A[i][k];
        double alpha_a_ik = alpha * a_ik;
        for (j = 0; j < n; j++) {
          Crow_k[j] += alpha * Brow_i[j] * a_ik;
        }
      }
    }

    for (j = 0; j < n; j++) {
      double temp2 = 0;
      for (k = 0; k < i; k++) {
        temp2 += B[k][j] * A[i][k];
      }
      Crow_i[j] = beta * Crow_i[j] + alpha * Brow_i[j] * Aii + alpha * temp2;
    }
  }
#pragma endscop
}
