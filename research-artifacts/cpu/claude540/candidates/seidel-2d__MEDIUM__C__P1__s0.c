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
      double top_prev = rm1[0];
      double mid_prev = r0[0];
      double bot_prev = rp1[0];
      double top_cur = rm1[1];
      double mid_cur = r0[1];
      double bot_cur = rp1[1];
      for (j = 1; j <= n - 2; j++) {
        double top_next = rm1[j+1];
        double bot_next = rp1[j+1];
        r0[j] = (top_prev + top_cur + top_next
                 + mid_prev + mid_cur + r0[j+1]
                 + bot_prev + bot_cur + bot_next)/9.0;
        top_prev = top_cur;
        top_cur = top_next;
        mid_prev = mid_cur;
        mid_cur = r0[j+1];
        bot_prev = bot_cur;
        bot_cur = bot_next;
      }
    }
#pragma endscop
}
