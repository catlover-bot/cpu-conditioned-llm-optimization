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
      int * restrict prow = path[k];
      for(i = 0; i < n; i++)
 {
   int * restrict irow = path[i];
   int pik = irow[k];
   for (j = 0; j < n; j++)
     {
       int cand = pik + prow[j];
       irow[j] = irow[j] < cand ? irow[j] : cand;
     }
 }
    }
#pragma endscop
}
