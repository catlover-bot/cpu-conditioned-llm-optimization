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
      double ri = r[i];
      double qi = 0.0;
      double *Ai = A[i];
      j = 0;
      for (; j + 4 <= m; j += 4)
        {
          s[j]   = s[j]   + ri * Ai[j];
          qi = qi + Ai[j] * p[j];

          s[j+1] = s[j+1] + ri * Ai[j+1];
          qi = qi + Ai[j+1] * p[j+1];

          s[j+2] = s[j+2] + ri * Ai[j+2];
          qi = qi + Ai[j+2] * p[j+2];

          s[j+3] = s[j+3] + ri * Ai[j+3];
          qi = qi + Ai[j+3] * p[j+3];
        }
      for (; j < m; j++)
        {
          s[j] = s[j] + ri * Ai[j];
          qi = qi + Ai[j] * p[j];
        }
      q[i] = qi;
    }
#pragma endscop
}
