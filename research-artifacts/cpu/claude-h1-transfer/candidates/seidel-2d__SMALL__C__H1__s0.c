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
      double *Am1 = A[i-1];
      double *A0 = A[i];
      double *Ap1 = A[i+1];
      double am1_prev = Am1[0];
      double am1_cur = Am1[1];
      double a0_prev = A0[0];
      double a0_cur = A0[1];
      double ap1_prev = Ap1[0];
      double ap1_cur = Ap1[1];
      for (j = 1; j <= n - 2; j++) {
        double am1_next = Am1[j+1];
        double ap1_next = Ap1[j+1];
        double a0_next = A0[j+1];
        double val = (am1_prev + am1_cur + am1_next
            + a0_prev + a0_cur + a0_next
            + ap1_prev + ap1_cur + ap1_next) / 9.0;
        A0[j] = val;

        am1_prev = am1_cur;
        am1_cur = am1_next;
        ap1_prev = ap1_cur;
        ap1_cur = ap1_next;
        a0_prev = val;
        a0_cur = a0_next;
      }
    }
#pragma endscop
}
