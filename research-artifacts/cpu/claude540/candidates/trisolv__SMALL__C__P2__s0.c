#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_trisolv(int n,
      double L[ n + 0][n + 0],
      double x[ n + 0],
      double b[ n + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < n; i++)
    {
      double sum = b[i];
      const double *Li = L[i];
      for (j = 0; j < i; j++)
        sum -= Li[j] * x[j];
      x[i] = sum / Li[i];
    }
#pragma endscop
}
