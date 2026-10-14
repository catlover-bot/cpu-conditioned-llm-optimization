#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_seidel_2d(int tsteps,
        int n,
        double A[ n + 0][n + 0])
{
  int t, i, j;
#pragma scop
  for (t = 0; t <= tsteps - 1; t++)
    for (i = 1; i<= n - 2; i++) {
      double *rprev = A[i-1];
      double *rcur  = A[i];
      double *rnext = A[i+1];
      for (j = 1; j <= n - 2; j++)
 rcur[j] = (rprev[j-1] + rprev[j] + rprev[j+1]
     + rcur[j-1] + rcur[j] + rcur[j+1]
     + rnext[j-1] + rnext[j] + rnext[j+1])/9.0;
    }
#pragma endscop
}
