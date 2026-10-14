#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_3mm(int ni, int nj, int nk, int nl, int nm,
  double E[ ni + 0][nj + 0],
  double A[ ni + 0][nk + 0],
  double B[ nk + 0][nj + 0],
  double F[ nj + 0][nl + 0],
  double C[ nj + 0][nm + 0],
  double D[ nm + 0][nl + 0],
  double G[ ni + 0][nl + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < ni; i++)
    for (j = 0; j < nj; j++)
      {
        double sum = 0.0;
        for (k = 0; k < nk; ++k)
          sum += A[i][k] * B[k][j];
        E[i][j] = sum;
      }
  for (i = 0; i < nj; i++)
    for (j = 0; j < nl; j++)
      {
        double sum = 0.0;
        for (k = 0; k < nm; ++k)
          sum += C[i][k] * D[k][j];
        F[i][j] = sum;
      }
  for (i = 0; i < ni; i++)
    for (j = 0; j < nl; j++)
      {
        double sum = 0.0;
        for (k = 0; k < nj; ++k)
          sum += E[i][k] * F[k][j];
        G[i][j] = sum;
      }
#pragma endscop
}
