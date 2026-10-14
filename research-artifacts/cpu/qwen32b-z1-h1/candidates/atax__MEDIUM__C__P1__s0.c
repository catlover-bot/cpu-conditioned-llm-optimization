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
      double tmp_i = 0.0;
      for (j = 0; j < n; j++)
        tmp_i = tmp_i + A[i][j] * x[j];
      tmp[i] = tmp_i;
      for (j = 0; j < n; j++)
        y[j] = y[j] + A[i][j] * tmp_i;
    }
#pragma endscop
}
