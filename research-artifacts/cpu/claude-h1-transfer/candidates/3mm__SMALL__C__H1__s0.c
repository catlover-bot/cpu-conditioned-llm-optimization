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
      double * restrict Ei = E[i];
      double * restrict Bk = B[k];
      for (j = 0; j < nj; j++)
        Ei[j] += a * Bk[j];
    }
  }
  for (i = 0; i < nj; i++) {
    for (j = 0; j < nl; j++)
      F[i][j] = 0.0;
    for (k = 0; k < nm; ++k) {
      double c = C[i][k];
      double * restrict Fi = F[i];
      double * restrict Dk = D[k];
      for (j = 0; j < nl; j++)
        Fi[j] += c * Dk[j];
    }
  }
  for (i = 0; i < ni; i++) {
    for (j = 0; j < nl; j++)
      G[i][j] = 0.0;
    for (k = 0; k < nj; ++k) {
      double e = E[i][k];
      double * restrict Gi = G[i];
      double * restrict Fk = F[k];
      for (j = 0; j < nl; j++)
        Gi[j] += e * Fk[j];
    }
  }
#pragma endscop
}
