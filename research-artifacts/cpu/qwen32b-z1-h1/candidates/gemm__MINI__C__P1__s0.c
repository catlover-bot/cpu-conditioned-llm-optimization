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
    for (j = 0; j < nj; j++) {
      C[i][j] *= beta;
      double acc = 0.0;
      for (k = 0; k < nk; k++) {
        acc += A[i][k] * B[k][j];
      }
      C[i][j] += alpha * acc;
    }
  }
#pragma endscop
}
