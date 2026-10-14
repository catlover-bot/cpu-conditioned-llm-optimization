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
      double *Ai = A[i];
      double acc = 0.0;
      j = 0;
      for (; j + 4 <= n; j += 4)
        {
          acc = acc + Ai[j] * x[j];
          acc = acc + Ai[j+1] * x[j+1];
          acc = acc + Ai[j+2] * x[j+2];
          acc = acc + Ai[j+3] * x[j+3];
        }
      for (; j < n; j++)
        acc = acc + Ai[j] * x[j];
      tmp[i] = acc;

      double tmpi = tmp[i];
      for (j = 0; j < n; j++)
        y[j] = y[j] + Ai[j] * tmpi;
    }
#pragma endscop
}
