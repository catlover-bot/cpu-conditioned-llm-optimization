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
      for(i = 0; i < n; i++) {
        int pik = path[i][k];
        int * restrict prow = path[i];
        int * restrict krow = path[k];
        for (j = 0; j < n; j++) {
          int sum = pik + krow[j];
          int cur = prow[j];
          prow[j] = cur < sum ? cur : sum;
        }
      }
    }
#pragma endscop
}
