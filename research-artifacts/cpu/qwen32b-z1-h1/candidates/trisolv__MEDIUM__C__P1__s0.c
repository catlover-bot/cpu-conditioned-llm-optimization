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
      double xi = b[i];
      for (j = 0; j < i; j++)
        xi -= L[i][j] * x[j];
      x[i] = xi / L[i][i];
    }
#pragma endscop
}
