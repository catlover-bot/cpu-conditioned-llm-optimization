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
    for (t = 1; t <= 40; t++) {
        for (i = 1; i < n-1; i++) {
            for (j = 1; j < n-1; j++) {
                double * restrict Bij = B[i][j];
                const double * restrict Aim1j = A[i-1][j];
                const double * restrict Aip1j = A[i+1][j];
                const double * restrict Aijm1 = A[i][j-1];
                const double * restrict Aijp1 = A[i][j+1];
                const double * restrict Aij = A[i][j];
                for (k = 1; k < n-1; k++) {
                    Bij[k] = 0.125 * (Aip1j[k] - 2.0 * Aij[k] + Aim1j[k])
                                 + 0.125 * (Aijp1[k] - 2.0 * Aij[k] + Aijm1[k])
                                 + 0.125 * (Aij[k+1] - 2.0 * Aij[k] + Aij[k-1])
                                 + Aij[k];
                }
            }
        }
        for (i = 1; i < n-1; i++) {
           for (j = 1; j < n-1; j++) {
                double * restrict Aij = A[i][j];
                const double * restrict Bim1j = B[i-1][j];
                const double * restrict Bip1j = B[i+1][j];
                const double * restrict Bijm1 = B[i][j-1];
                const double * restrict Bijp1 = B[i][j+1];
                const double * restrict Bij = B[i][j];
               for (k = 1; k < n-1; k++) {
                   Aij[k] = 0.125 * (Bip1j[k] - 2.0 * Bij[k] + Bim1j[k])
                                + 0.125 * (Bijp1[k] - 2.0 * Bij[k] + Bijm1[k])
                                + 0.125 * (Bij[k+1] - 2.0 * Bij[k] + Bij[k-1])
                                + Bij[k];
               }
           }
       }
    }
#pragma endscop
}
