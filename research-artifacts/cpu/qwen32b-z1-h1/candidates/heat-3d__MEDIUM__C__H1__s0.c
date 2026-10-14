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
                for (k = 1; k < n-1; k++) {
                    double a_i_j_k = A[i][j][k];
                    B[i][j][k] = 0.125 * (A[i+1][j][k] - 2.0 * a_i_j_k + A[i-1][j][k])
                                 + 0.125 * (A[i][j+1][k] - 2.0 * a_i_j_k + A[i][j-1][k])
                                 + 0.125 * (A[i][j][k+1] - 2.0 * a_i_j_k + A[i][j][k-1])
                                 + a_i_j_k;
                }
            }
        }
        for (i = 1; i < n-1; i++) {
           for (j = 1; j < n-1; j++) {
               for (k = 1; k < n-1; k++) {
                   double b_i_j_k = B[i][j][k];
                   A[i][j][k] = 0.125 * (B[i+1][j][k] - 2.0 * b_i_j_k + B[i-1][j][k])
                                + 0.125 * (B[i][j+1][k] - 2.0 * b_i_j_k + B[i][j-1][k])
                                + 0.125 * (B[i][j][k+1] - 2.0 * b_i_j_k + B[i][j][k-1])
                                + b_i_j_k;
               }
           }
       }
    }
#pragma endscop
}
