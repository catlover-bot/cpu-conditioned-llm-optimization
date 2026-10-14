#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_doitgen(int nr, int nq, int np,
      double A[ nr + 0][nq + 0][np + 0],
      double C4[ np + 0][np + 0],
      double sum[ np + 0])
{
  int r, q, p, s;
#pragma scop
  for (r = 0; r < nr; r++)
    for (q = 0; q < nq; q++) {
      for (p = 0; p < np; p++) {
        double temp_sum = 0.0;
        for (s = 0; s < np; s++)
          temp_sum += A[r][q][s] * C4[s][p];
        sum[p] = temp_sum;
      }
      for (p = 0; p < np; p++)
        A[r][q][p] = sum[p];
    }
#pragma endscop
}
