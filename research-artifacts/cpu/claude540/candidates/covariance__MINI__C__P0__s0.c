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
      cov[i][j] = 0.0;

  for (k = 0; k < n; k++)
    for (i = 0; i < m; i++)
      {
        double di = data[k][i];
        double *covi = cov[i];
        const double *dk = data[k];
        for (j = i; j < m; j++)
          covi[j] += di * dk[j];
      }

  for (i = 0; i < m; i++)
    for (j = i; j < m; j++)
      {
        cov[i][j] /= (float_n - 1.0);
        cov[j][i] = cov[i][j];
      }
#pragma endscop
}
