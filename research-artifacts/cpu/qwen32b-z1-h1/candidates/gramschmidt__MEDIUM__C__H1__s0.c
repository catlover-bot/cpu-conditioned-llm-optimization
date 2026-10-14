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
      for (i = 0; i < m; i++)
        Q[i][k] = A[i][k] / R[k][k];
      for (j = k + 1; j < n; j++)
 {
   R[k][j] = 0.0;
   for (i = 0; i < m; i++)
     R[k][j] += Q[i][k] * A[i][j];
   for (i = 0; i < m; i++)
     A[i][j] -= Q[i][k] * R[k][j];
 }
    }
#pragma endscop
}
