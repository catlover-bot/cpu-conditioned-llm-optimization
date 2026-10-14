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
      double *rp = A[i-1];
      double *rc = A[i];
      double *rn = A[i+1];
      double a0 = rp[0], a1 = rp[1];
      double b0 = rc[0], b1 = rc[1];
      double c0 = rn[0], c1 = rn[1];
      for (j = 1; j <= n - 2; j++) {
        double a2 = rp[j+1];
        double b2 = rc[j+1];
        double c2 = rn[j+1];
        double v = (a0 + a1 + a2 + b0 + b1 + b2 + c0 + c1 + c2) / 9.0;
        rc[j] = v;
        a0 = a1; a1 = a2;
        b0 = b1; b1 = v;
        c0 = c1; c1 = c2;
      }
    }
#pragma endscop
}
