#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_covariance(int m, int n,
         double float_n,
         double data[ n + 0][m + 0],
         double cov[ m + 0][m + 0],
         double mean[ m + 0])
{
  int i, j, k;
#pragma scop
  for (j = 0; j < m; j++)
    {
      mean[j] = 0.0;
      for (i = 0; i < n; i++)
        mean[j] += data[i][j];
      mean[j] /= float_n;
    }
  for (i = 0; i < n; i++)
    for (j = 0; j < m; j++)
      data[i][j] -= mean[j];
  for (i = 0; i < m; i++)
    for (j = i; j < m; j++)
      {
        double sum = 0.0;
        const double *di = data[0] + i;
        const double *dj = data[0] + j;
        for (k = 0; k < n; k++)
          sum += di[(size_t)k * m] * dj[(size_t)k * m];
        sum /= (float_n - 1.0);
        cov[i][j] = sum;
        cov[j][i] = sum;
      }
#pragma endscop
}
