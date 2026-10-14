#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_seidel_2d(int tsteps,
        int n,
        double A[n + 0][n + 0])
{
  int t, i, j;
#pragma scop
  for (t = 0; t <= tsteps - 1; t++) {
    for (i = 1; i <= n - 2; i++) {
      double sum;
      for (j = 1; j <= n - 2; j++) {
        sum = A[i-1][j-1] + A[i-1][j] + A[i-1][j+1]
            + A[i][j-1] + A[i][j] + A[i][j+1]
            + A[i+1][j-1] + A[i+1][j] + A[i+1][j+1];
        A[i][j] = sum / 9.0;
      }
    }
  }
#pragma endscop
}
