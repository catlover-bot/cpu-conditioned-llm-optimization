#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_jacobi_2d(int tsteps,
       int n,
       double A[ n + 0][n + 0],
       double B[ n + 0][n + 0])
{
  int t, i, j;
#pragma scop
  for (t = 0; t < tsteps; t++)
    {
      for (i = 1; i < n - 1; i++)
        {
          double *A_i = A[i];
          double *A_ip1 = A[i + 1];
          double *A_im1 = A[i - 1];
          double *B_i = B[i];
          for (j = 1; j < n - 1; j++)
            B_i[j] = 0.2 * (A_i[j] + A_i[j-1] + A_i[j+1] + A_ip1[j] + A_im1[j]);
        }
      for (i = 1; i < n - 1; i++)
        {
          double *A_i = A[i];
          double *A_ip1 = A[i + 1];
          double *A_im1 = A[i - 1];
          double *B_i = B[i];
          double *B_ip1 = B[i + 1];
          double *B_im1 = B[i - 1];
          for (j = 1; j < n - 1; j++)
            A_i[j] = 0.2 * (B_i[j] + B_i[j-1] + B_i[j+1] + B_ip1[j] + B_im1[j]);
        }
    }
#pragma endscop
}
