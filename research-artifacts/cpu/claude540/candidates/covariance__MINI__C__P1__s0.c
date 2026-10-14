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
    {
      double *row = data[i];
      for (j = 0; j < m; j++)
        row[j] -= mean[j];
    }
  for (i = 0; i < m; i++)
    for (j = i; j < m; j++)
      {
        double sum = 0.0;
        for (k = 0; k < n; k++)
          sum += data[k][i] * data[k][j];
        sum /= (float_n - 1.0);
        cov[i][j] = sum;
        cov[j][i] = sum;
      }
#pragma endscop
}
