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
    double temp1 = 0.0;
    double temp2 = 0.0;
    for (j = 0; j < n; j++) {
      temp1 = temp1 + A[i][j] * y_1[j];
      temp2 = temp2 + A[j][i] * y_2[j];
    }
    x1[i] = x1[i] + temp1;
    x2[i] = x2[i] + temp2;
  }
#pragma endscop
}
