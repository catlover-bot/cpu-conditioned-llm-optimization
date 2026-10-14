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
      double tmp_acc = 0.0;
      double y_acc = 0.0;
      const double *Ai = A[i];
      const double *Bi = B[i];
      for (j = 0; j < n; j++)
 {
   tmp_acc = Ai[j] * x[j] + tmp_acc;
   y_acc = Bi[j] * x[j] + y_acc;
 }
      tmp[i] = tmp_acc;
      y[i] = alpha * tmp_acc + beta * y_acc;
    }
#pragma endscop
}
