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
  for (i = 0; i < ni; i++) {
    for (j = 0; j < nj; j++)
      tmp[i][j] = 0.0;
    for (k = 0; k < nk; ++k) {
      double a = alpha * A[i][k];
      double * restrict trow = tmp[i];
      const double * restrict brow = B[k];
      for (j = 0; j < nj; j++)
        trow[j] += a * brow[j];
    }
  }
  for (i = 0; i < ni; i++) {
    double * restrict drow = D[i];
    for (j = 0; j < nl; j++)
      drow[j] *= beta;
    for (k = 0; k < nj; ++k) {
      double t = tmp[i][k];
      const double * restrict crow = C[k];
      for (j = 0; j < nl; j++)
        drow[j] += t * crow[j];
    }
  }
#pragma endscop
}
