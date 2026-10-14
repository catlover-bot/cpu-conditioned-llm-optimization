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
    double *Ai = A[i];
    double *Bi = B[i];
    double *Ci = C[i];
    double Aii = Ai[i];

    for (j = 0; j < n; j++) {
      double b_ij = Bi[j];
      double temp2 = 0.0;
      double a_ij_alpha = alpha * b_ij;

      for (k = 0; k < i; k++) {
        double aik = Ai[k];
        C[k][j] += a_ij_alpha * aik;
        temp2 += B[k][j] * aik;
      }
      Ci[j] = beta * Ci[j] + a_ij_alpha * Aii + alpha * temp2;
    }
  }
#pragma endscop
}
