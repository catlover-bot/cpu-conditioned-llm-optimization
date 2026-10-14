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
      for (i = 1; i < n - 1; i++) {
        double *Bi = B[i];
        double *Aim1 = A[i-1];
        double *Ai = A[i];
        double *Aip1 = A[i+1];
        for (j = 1; j < n - 1; j++)
          Bi[j] = 0.2 * (Ai[j] + Ai[j-1] + Ai[j+1] + Aip1[j] + Aim1[j]);
      }
      for (i = 1; i < n - 1; i++) {
        double *Ai = A[i];
        double *Bim1 = B[i-1];
        double *Bi = B[i];
        double *Bip1 = B[i+1];
        for (j = 1; j < n - 1; j++)
          Ai[j] = 0.2 * (Bi[j] + Bi[j-1] + Bi[j+1] + Bip1[j] + Bim1[j]);
      }
    }
#pragma endscop
}
