#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_gemver(int n,
     double alpha,
     double beta,
     double A[ n + 0][n + 0],
     double u1[ n + 0],
     double v1[ n + 0],
     double u2[ n + 0],
     double v2[ n + 0],
     double w[ n + 0],
     double x[ n + 0],
     double y[ n + 0],
     double z[ n + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < n; i++) {
    double temp1 = u1[i];
    double temp2 = u2[i];
    for (j = 0; j < n; j++)
      A[i][j] = A[i][j] + temp1 * v1[j] + temp2 * v2[j];
  }
  for (i = 0; i < n; i++) {
    double temp = 0.0;
    for (j = 0; j < n; j++)
      temp = temp + beta * A[j][i] * y[j];
    x[i] = x[i] + temp;
  }
  for (i = 0; i < n; i++)
    x[i] = x[i] + z[i];
  for (i = 0; i < n; i++) {
    double temp = 0.0;
    for (j = 0; j < n; j++)
      temp = temp + alpha * A[i][j] * x[j];
    w[i] = w[i] + temp;
  }
#pragma endscop
}
