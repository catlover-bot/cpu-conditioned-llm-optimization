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
                double * restrict Bp = &B[i][j][0];
                const double * restrict Aim = &A[i-1][j][0];
                const double * restrict Aip = &A[i+1][j][0];
                const double * restrict Ajm = &A[i][j-1][0];
                const double * restrict Ajp = &A[i][j+1][0];
                const double * restrict Ac  = &A[i][j][0];
                for (k = 1; k < n-1; k++) {
                    Bp[k] = 0.125 * (Aip[k] - 2.0 * Ac[k] + Aim[k])
                                 + 0.125 * (Ajp[k] - 2.0 * Ac[k] + Ajm[k])
                                 + 0.125 * (Ac[k+1] - 2.0 * Ac[k] + Ac[k-1])
                                 + Ac[k];
                }
            }
        }
        for (i = 1; i < n-1; i++) {
           for (j = 1; j < n-1; j++) {
                double * restrict Ap = &A[i][j][0];
                const double * restrict Bim = &B[i-1][j][0];
                const double * restrict Bip = &B[i+1][j][0];
                const double * restrict Bjm = &B[i][j-1][0];
                const double * restrict Bjp = &B[i][j+1][0];
                const double * restrict Bc  = &B[i][j][0];
               for (k = 1; k < n-1; k++) {
                   Ap[k] = 0.125 * (Bip[k] - 2.0 * Bc[k] + Bim[k])
                                + 0.125 * (Bjp[k] - 2.0 * Bc[k] + Bjm[k])
                                + 0.125 * (Bc[k+1] - 2.0 * Bc[k] + Bc[k-1])
                                + Bc[k];
               }
           }
       }
    }
#pragma endscop
}
