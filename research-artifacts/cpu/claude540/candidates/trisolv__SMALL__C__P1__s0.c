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
      double *Li = L[i];
      j = 0;
      for (; j + 4 <= i; j += 4)
        {
          sum -= Li[j] * x[j];
          sum -= Li[j+1] * x[j+1];
          sum -= Li[j+2] * x[j+2];
          sum -= Li[j+3] * x[j+3];
        }
      for (; j < i; j++)
        sum -= Li[j] * x[j];
      x[i] = sum / Li[i];
    }
#pragma endscop
}
