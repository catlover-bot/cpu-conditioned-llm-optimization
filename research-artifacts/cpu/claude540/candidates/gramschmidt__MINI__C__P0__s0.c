#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_gramschmidt(int m, int n,
   double A[ m + 0][n + 0],
   double R[ n + 0][n + 0],
   double Q[ m + 0][n + 0])
{
  int i, j, k;
  double nrm;
#pragma scop
  for (k = 0; k < n; k++)
    {
      nrm = 0.0;
      for (i = 0; i < m; i++)
        nrm += A[i][k] * A[i][k];
      double Rkk = sqrt(nrm);
      R[k][k] = Rkk;
      double invRkk = 1.0 / Rkk;
      for (i = 0; i < m; i++)
        Q[i][k] = A[i][k] * invRkk;

      int nrem = n - (k + 1);
      double *Ak = &A[0][k];
      double *Qk = &Q[0][k];

      for (j = k + 1; j < n; j++)
        {
          double sum = 0.0;
          for (i = 0; i < m; i++)
            sum += Q[i][k] * A[i][j];
          R[k][j] = sum;
        }

      for (j = k + 1; j < n; j++)
        {
          double Rkj = R[k][j];
          for (i = 0; i < m; i++)
            A[i][j] = A[i][j] - Q[i][k] * Rkj;
        }
    }
#pragma endscop
}
