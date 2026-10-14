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
      double top = rm1[0], mid = r0[0], bot = rp1[0];
      for (j = 1; j <= n - 2; j++) {
        double topn = rm1[j+1];
        double midn = r0[j+1];
        double botn = rp1[j+1];
        r0[j] = (top + rm1[j] + topn
            + mid + r0[j] + midn
            + bot + rp1[j] + botn) / 9.0;
        top = topn;
        mid = midn;
        bot = botn;
      }
    }
#pragma endscop
}
