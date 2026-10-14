#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_seidel_2d(int tsteps,
        int n,
        double A[ n + 0][n + 0])
{
  int t, i, j;
#pragma scop
  for (t = 0; t <= tsteps - 1; t++) {
    for (i = 1; i <= n - 2; i++) {
      double *A_i = A[i];
      double *A_im1 = A[i-1];
      double *A_ip1 = A[i+1];
      for (j = 1; j <= n - 2; j++) {
        A_i[j] = (A_im1[j-1] + A_im1[j] + A_im1[j+1]
                  + A_i[j-1] + A_i[j] + A_i[j+1]
                  + A_ip1[j-1] + A_ip1[j] + A_ip1[j+1]) / 9.0;
      }
    }
  }
#pragma endscop
}
