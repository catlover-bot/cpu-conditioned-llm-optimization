#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_2mm(int ni, int nj, int nk, int nl,
  double alpha,
  double beta,
  double tmp[ ni + 0][nj + 0],
  double A[ ni + 0][nk + 0],
  double B[ nk + 0][nj + 0],
  double C[ nj + 0][nl + 0],
  double D[ ni + 0][nl + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < ni; i++)
    for (j = 0; j < nj; j++)
      {
        double t = 0.0;
        for (k = 0; k < nk; ++k)
          t += alpha * A[i][k] * B[k][j];
        tmp[i][j] = t;
      }
  for (i = 0; i < ni; i++)
    for (j = 0; j < nl; j++)
      {
        double d = D[i][j] * beta;
        for (k = 0; k < nj; ++k)
          d += tmp[i][k] * C[k][j];
        D[i][j] = d;
      }
#pragma endscop
}
