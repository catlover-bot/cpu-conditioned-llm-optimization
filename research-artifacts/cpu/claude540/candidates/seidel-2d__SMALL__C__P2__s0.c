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
      double *rowm1 = A[i-1];
      double *row   = A[i];
      double *rowp1 = A[i+1];
      for (j = 1; j <= n - 2; j++)
 row[j] = (rowm1[j-1] + rowm1[j] + rowm1[j+1]
     + row[j-1] + row[j] + row[j+1]
     + rowp1[j-1] + rowp1[j] + rowp1[j+1])/9.0;
    }
#pragma endscop
}
