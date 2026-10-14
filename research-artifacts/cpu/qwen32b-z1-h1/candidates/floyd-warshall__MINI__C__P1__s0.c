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
        for (j = 0; j < n; j++)
        {
          int temp = path[i][k] + path[k][j];
          if (path[i][j] > temp)
            path[i][j] = temp;
        }
    }
#pragma endscop
}
