#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_mvt(int n,
  double x1[ n + 0],
  double x2[ n + 0],
  double y_1[ n + 0],
  double y_2[ n + 0],
  double A[ n + 0][n + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < n; i++) {
    double acc = x1[i];
    double *Ai = A[i];
    for (j = 0; j < n; j++)
      acc = acc + Ai[j] * y_1[j];
    x1[i] = acc;
  }
  for (i = 0; i < n; i++) {
    double acc = x2[i];
    for (j = 0; j < n; j++)
      acc = acc + A[j][i] * y_2[j];
    x2[i] = acc;
  }
#pragma endscop
}
