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
        int* path_i = path[i];
        int path_ik = path_i[k];
        for (j = 0; j < n; j++)
        {
          int path_kj = path[k][j];
          int new_value = path_ik + path_kj;
          path_i[j] = path_i[j] < new_value ? path_i[j] : new_value;
        }
      }
    }
#pragma endscop
}
