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
  for (i = 0; i < ni; i++) {
    for (j = 0; j < nj; j++)
      E[i][j] = 0.0;
    for (k = 0; k < nk; ++k) {
      double a = A[i][k];
      for (j = 0; j < nj; j++)
        E[i][j] += a * B[k][j];
    }
  }
  for (i = 0; i < nj; i++) {
    for (j = 0; j < nl; j++)
      F[i][j] = 0.0;
    for (k = 0; k < nm; ++k) {
      double c = C[i][k];
      for (j = 0; j < nl; j++)
        F[i][j] += c * D[k][j];
    }
  }
  for (i = 0; i < ni; i++)
    for (j = 0; j < nl; j++)
      {
 G[i][j] = 0.0;
 for (k = 0; k < nj; ++k)
   G[i][j] += E[i][k] * F[k][j];
      }
#pragma endscop
}
