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

  for (i = 0; i < ni; i++) {
    for (j = 0; j < nj; j++)
      tmp[i][j] = 0.0;
    for (k = 0; k < nk; ++k) {
      double a_ik_alpha = alpha * A[i][k];
      double *Bk = B[k];
      double *tmpi = tmp[i];
      for (j = 0; j < nj; j++)
        tmpi[j] += a_ik_alpha * Bk[j];
    }
  }

  for (i = 0; i < ni; i++) {
    double *Di = D[i];
    for (j = 0; j < nl; j++)
      Di[j] *= beta;
    double *tmpi = tmp[i];
    for (k = 0; k < nj; ++k) {
      double t = tmpi[k];
      double *Ck = C[k];
      for (j = 0; j < nl; j++)
        Di[j] += t * Ck[j];
    }
  }
}
