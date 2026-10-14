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
      double *row_prev = A[i-1];
      double *row_cur  = A[i];
      double *row_next = A[i+1];
      for (j = 1; j <= n - 2; j++)
 row_cur[j] = (row_prev[j-1] + row_prev[j] + row_prev[j+1]
     + row_cur[j-1] + row_cur[j] + row_cur[j+1]
     + row_next[j-1] + row_next[j] + row_next[j+1])/9.0;
    }
#pragma endscop
}
