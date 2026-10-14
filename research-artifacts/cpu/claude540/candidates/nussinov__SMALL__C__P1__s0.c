#include <math.h>
#include <stdint.h>
#include <stddef.h>
typedef char base;

__attribute__((noinline)) void kernel_nussinov(int n, base seq[ n + 0],
      int table[ n + 0][n + 0])
{
  int i, j, k;
#pragma scop
 for (i = n-1; i >= 0; i--) {
  int *row_i = table[i];
  for (j=i+1; j<n; j++) {
   int cur = row_i[j];
   if (j-1>=0) {
      int v = row_i[j-1];
      if (v > cur) cur = v;
   }
   if (i+1<n) {
      int v = table[i+1][j];
      if (v > cur) cur = v;
   }
   if (j-1>=0 && i+1<n) {
     if (i<j-1) {
        int v = table[i+1][j-1] + (((seq[i])+(seq[j])) == 3 ? 1 : 0);
        if (v > cur) cur = v;
     } else {
        int v = table[i+1][j-1];
        if (v > cur) cur = v;
     }
   }
   for (k=i+1; k<j; k++) {
      int v = row_i[k] + table[k+1][j];
      if (v > cur) cur = v;
   }
   row_i[j] = cur;
  }
 }
#pragma endscop
}
