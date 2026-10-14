#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_correlation(int m, int n,
   double float_n,
   double data[ n + 0][m + 0],
   double corr[ m + 0][m + 0],
   double mean[ m + 0],
   double stddev[ m + 0])
{
  int i, j, k;
  double eps = 0.1;
#pragma scop
  for (j = 0; j < m; j++)
    {
      mean[j] = 0.0;
      for (i = 0; i < n; i++)
 mean[j] += data[i][j];
      mean[j] /= float_n;
    }
   for (j = 0; j < m; j++)
    {
      stddev[j] = 0.0;
      for (i = 0; i < n; i++)
        stddev[j] += (data[i][j] - mean[j]) * (data[i][j] - mean[j]);
      stddev[j] /= float_n;
      stddev[j] = sqrt(stddev[j]);
      stddev[j] = stddev[j] <= eps ? 1.0 : stddev[j];
    }
  {
    double sqrt_float_n = sqrt(float_n);
    for (i = 0; i < n; i++)
      for (j = 0; j < m; j++)
        {
          data[i][j] -= mean[j];
          data[i][j] /= sqrt_float_n * stddev[j];
        }
  }
  for (i = 0; i < m-1; i++)
    {
      corr[i][i] = 1.0;
      for (j = i+1; j < m; j++)
        {
          double sum = 0.0;
          for (k = 0; k < n; k++)
            sum += (data[k][i] * data[k][j]);
          corr[i][j] = sum;
          corr[j][i] = sum;
        }
    }
  corr[m-1][m-1] = 1.0;
#pragma endscop
}
