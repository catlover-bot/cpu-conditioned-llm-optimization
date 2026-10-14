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
      double *rcur = A[i];
      double *rnext = A[i+1];
      double a0 = rprev[0], a1 = rprev[1];
      double b0 = rcur[0], b1 = rcur[1];
      double c0 = rnext[0], c1 = rnext[1];
      for (j = 1; j <= n - 2; j++) {
        double a2 = rprev[j+1];
        double b2 = rcur[j+1];
        double c2 = rnext[j+1];
        rcur[j] = (a0 + a1 + a2 + b0 + b1 + b2 + c0 + c1 + c2) / 9.0;
        a0 = a1; a1 = a2;
        b0 = b1; b1 = rcur[j];
        c0 = c1; c1 = c2;
      }
    }
#pragma endscop
}
