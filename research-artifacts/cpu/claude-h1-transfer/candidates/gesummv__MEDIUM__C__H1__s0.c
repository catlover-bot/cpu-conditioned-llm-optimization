#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_gesummv(int n,
      double alpha,
      double beta,
      double A[ n + 0][n + 0],
      double B[ n + 0][n + 0],
      double tmp[ n + 0],
      double x[ n + 0],
      double y[ n + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < n; i++)
    {
      double tmp_i = 0.0;
      double y_i = 0.0;
      double *Ai = A[i];
      double *Bi = B[i];
      for (j = 0; j < n; j++)
 {
   tmp_i = Ai[j] * x[j] + tmp_i;
   y_i = Bi[j] * x[j] + y_i;
 }
      tmp[i] = tmp_i;
      y[i] = alpha * tmp_i + beta * y_i;
    }
#pragma endscop
}
