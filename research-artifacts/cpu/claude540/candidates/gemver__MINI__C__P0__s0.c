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
    double u1i = u1[i];
    double u2i = u2[i];
    double *Ai = A[i];
    for (j = 0; j < n; j++)
      Ai[j] = Ai[j] + u1i * v1[j] + u2i * v2[j];
  }

  for (i = 0; i < n; i++) {
    double acc = x[i];
    for (j = 0; j < n; j++)
      acc = acc + beta * A[j][i] * y[j];
    x[i] = acc;
  }

  for (i = 0; i < n; i++)
    x[i] = x[i] + z[i];

  for (i = 0; i < n; i++) {
    double acc = w[i];
    double *Ai = A[i];
    for (j = 0; j < n; j++)
      acc = acc + alpha * Ai[j] * x[j];
    w[i] = acc;
  }
#pragma endscop
}
