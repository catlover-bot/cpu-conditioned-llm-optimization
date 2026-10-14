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
      for (j = k + 1; j < n; j++)
 {
   double sum = 0.0;
   for (i = 0; i < m; i++)
     sum += Q[i][k] * A[i][j];
   R[k][j] = sum;
   for (i = 0; i < m; i++)
     A[i][j] = A[i][j] - Q[i][k] * sum;
 }
    }
#pragma endscop
}
