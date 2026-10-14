#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_gemm(int ni, int nj, int nk,
   double alpha,
   double beta,
   double C[ ni + 0][nj + 0],
   double A[ ni + 0][nk + 0],
   double B[ nk + 0][nj + 0])
{
  int i, j, k;
#pragma scop
  for (i = 0; i < ni; i++) {
    double * restrict Ci = C[i];
    for (j = 0; j < nj; j++)
      Ci[j] *= beta;
    for (k = 0; k < nk; k++) {
      double aik = alpha * A[i][k];
      const double * restrict Bk = B[k];
      int j2 = 0;
      int nj4 = nj - (nj % 4);
      for (; j2 < nj4; j2 += 4) {
        Ci[j2]   += aik * Bk[j2];
        Ci[j2+1] += aik * Bk[j2+1];
        Ci[j2+2] += aik * Bk[j2+2];
        Ci[j2+3] += aik * Bk[j2+3];
      }
      for (; j2 < nj; j2++)
        Ci[j2] += aik * Bk[j2];
    }
  }
#pragma endscop
}
