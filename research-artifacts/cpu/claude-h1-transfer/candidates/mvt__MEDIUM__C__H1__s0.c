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
    double sum = x1[i];
    double *Ai = A[i];
    for (j = 0; j < n; j++)
      sum = sum + Ai[j] * y_1[j];
    x1[i] = sum;
  }
  for (j = 0; j < n; j++) {
    double *Aj = A[j];
    double y2j = y_2[j];
    for (i = 0; i < n; i++)
      x2[i] = x2[i] + Aj[i] * y2j;
  }
#pragma endscop
}
