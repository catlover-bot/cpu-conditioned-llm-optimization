#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_symm(int m, int n,
   double alpha,
   double beta,
   double C[ m + 0][n + 0],
   double A[ m + 0][m + 0],
   double B[ m + 0][n + 0])
{
  int i, j, k;

#pragma scop
   for (i = 0; i < m; i++) {
      double *Ai = A[i];
      double *Bi = B[i];
      double *Ci = C[i];

      // Initialize temp2 accumulator array for this i, one per j
      // We fuse the k-loop across j by processing j in an inner loop
      // but keep exact same accumulation order (k outer isn't possible
      // due to per-j temp2), so we process j and for each j do k loop,
      // but restructure memory access pattern for speed while preserving
      // exact FP operation order.

      for (j = 0; j < n; j++) {
        double temp2 = 0.0;
        double bij = Bi[j];
        for (k = 0; k < i; k++) {
           C[k][j] += alpha * bij * Ai[k];
           temp2 += B[k][j] * Ai[k];
        }
        Ci[j] = beta * Ci[j] + alpha * bij * Ai[i] + alpha * temp2;
      }
   }
#pragma endscop
}
