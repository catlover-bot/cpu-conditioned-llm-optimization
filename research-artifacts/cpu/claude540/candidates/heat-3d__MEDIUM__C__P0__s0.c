#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_heat_3d(int tsteps,
        int n,
        double A[ n + 0][n + 0][n + 0],
        double B[ n + 0][n + 0][n + 0])
{
  int t, i, j, k;
#pragma scop
    for (t = 1; t <= 100; t++) {
        for (i = 1; i < n-1; i++) {
            for (j = 1; j < n-1; j++) {
                double *Aim1 = &A[i-1][j][0];
                double *Ai   = &A[i][j][0];
                double *Aip1 = &A[i+1][j][0];
                double *Aijm1 = &A[i][j-1][0];
                double *Aijp1 = &A[i][j+1][0];
                double *Bi = &B[i][j][0];
                for (k = 1; k < n-1; k++) {
                    Bi[k] = 0.125 * (Aip1[k] - 2.0 * Ai[k] + Aim1[k])
                                 + 0.125 * (Aijp1[k] - 2.0 * Ai[k] + Aijm1[k])
                                 + 0.125 * (Ai[k+1] - 2.0 * Ai[k] + Ai[k-1])
                                 + Ai[k];
                }
            }
        }
        for (i = 1; i < n-1; i++) {
           for (j = 1; j < n-1; j++) {
                double *Bim1 = &B[i-1][j][0];
                double *Bi   = &B[i][j][0];
                double *Bip1 = &B[i+1][j][0];
                double *Bijm1 = &B[i][j-1][0];
                double *Bijp1 = &B[i][j+1][0];
                double *Ai = &A[i][j][0];
               for (k = 1; k < n-1; k++) {
                   Ai[k] = 0.125 * (Bip1[k] - 2.0 * Bi[k] + Bim1[k])
                                + 0.125 * (Bijp1[k] - 2.0 * Bi[k] + Bijm1[k])
                                + 0.125 * (Bi[k+1] - 2.0 * Bi[k] + Bi[k-1])
                                + Bi[k];
               }
           }
       }
    }
#pragma endscop
}
