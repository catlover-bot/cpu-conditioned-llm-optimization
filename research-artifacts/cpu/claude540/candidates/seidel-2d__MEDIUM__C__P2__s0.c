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
      double *restrict rm1 = A[i-1];
      double *restrict r0  = A[i];
      double *restrict rp1 = A[i+1];
      for (j = 1; j <= n - 2; j++)
 r0[j] = (rm1[j-1] + rm1[j] + rm1[j+1]
     + r0[j-1] + r0[j] + r0[j+1]
     + rp1[j-1] + rp1[j] + rp1[j+1])/9.0;
    }
#pragma endscop
}
