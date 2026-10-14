#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_bicg(int m, int n,
   double A[ n + 0][m + 0],
   double s[ m + 0],
   double q[ n + 0],
   double p[ m + 0],
   double r[ n + 0])
{
  int i, j;
#pragma scop
  for (i = 0; i < m; i++)
    s[i] = 0;
  for (i = 0; i < n; i++)
    {
      double q_temp = 0.0;
      for (j = 0; j < m; j++)
 {
   s[j] = s[j] + r[i] * A[i][j];
   q_temp = q_temp + A[i][j] * p[j];
 }
      q[i] = q_temp;
    }
#pragma endscop
}
