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
      R[k][k] = sqrt(nrm);

      double rkk = R[k][k];
      for (i = 0; i < m; i++)
        Q[i][k] = A[i][k] / rkk;

      int nrem = n - (k + 1);
      if (nrem > 0)
        {
          double *restrict Rk = &R[k][0];
          for (j = k + 1; j < n; j++)
            Rk[j] = 0.0;

          for (i = 0; i < m; i++)
            {
              double qik = Q[i][k];
              double *restrict Ai = &A[i][0];
              double *restrict Rkp = &R[k][0];
              for (j = k + 1; j < n; j++)
                Rkp[j] += qik * Ai[j];
            }

          for (i = 0; i < m; i++)
            {
              double qik = Q[i][k];
              double *restrict Ai = &A[i][0];
              double *restrict Rkp = &R[k][0];
              for (j = k + 1; j < n; j++)
                Ai[j] = Ai[j] - qik * Rkp[j];
            }
        }
    }
#pragma endscop
}
