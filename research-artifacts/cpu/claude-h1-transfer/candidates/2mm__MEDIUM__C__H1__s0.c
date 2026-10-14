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
    {
      for (j = 0; j < nj; j++)
        tmp[i][j] = 0.0;

      for (k = 0; k < nk; ++k)
        {
          double aik = alpha * A[i][k];
          double * restrict tmp_row = tmp[i];
          double * restrict B_row = B[k];
          for (j = 0; j < nj; j++)
            tmp_row[j] += aik * B_row[j];
        }
    }

  for (i = 0; i < ni; i++)
    {
      double * restrict D_row = D[i];
      for (j = 0; j < nl; j++)
        D_row[j] *= beta;

      for (k = 0; k < nj; ++k)
        {
          double tik = tmp[i][k];
          double * restrict C_row = C[k];
          for (j = 0; j < nl; j++)
            D_row[j] += tik * C_row[j];
        }
    }
#pragma endscop
}
