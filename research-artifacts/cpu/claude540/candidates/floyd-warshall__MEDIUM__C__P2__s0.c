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
      int *pathk = path[k];
      for(i = 0; i < n; i++)
        {
          int *pathi = path[i];
          int pik = pathi[k];
          for (j = 0; j < n; j++)
            {
              int cand = pik + pathk[j];
              int cur = pathi[j];
              pathi[j] = cur < cand ? cur : cand;
            }
        }
    }
#pragma endscop
}
