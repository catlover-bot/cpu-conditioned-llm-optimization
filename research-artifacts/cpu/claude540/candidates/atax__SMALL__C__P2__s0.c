#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_atax(int m, int n,
   double A[ m + 0][n + 0],
   double x[ n + 0],
   double y[ n + 0],
   double tmp[ m + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < n; i++)
    y[i] = 0;
  for (i = 0; i < m; i++)
    {
      double sum = 0.0;
      double *Ai = A[i];
      for (j = 0; j < n; j++)
        sum = sum + Ai[j] * x[j];
      tmp[i] = sum;
      for (j = 0; j < n; j++)
        y[j] = y[j] + Ai[j] * sum;
    }
#pragma endscop
}
