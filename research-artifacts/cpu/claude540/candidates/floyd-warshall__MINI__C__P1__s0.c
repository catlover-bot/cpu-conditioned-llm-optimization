#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_floyd_warshall(int n,
      int path[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
  for (k = 0; k < n; k++)
    {
      for(i = 0; i < n; i++)
        {
          int pik = path[i][k];
          int * restrict row_i = path[i];
          int * restrict row_k = path[k];
          for (j = 0; j < n; j++)
            {
              int sum = pik + row_k[j];
              int cur = row_i[j];
              row_i[j] = cur < sum ? cur : sum;
            }
        }
    }
#pragma endscop
}
