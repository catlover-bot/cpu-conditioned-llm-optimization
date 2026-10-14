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
  for (j=i+1; j<n; j++) {
   int max_val = table[i][j];
   if (j-1>=0)
      max_val = (max_val >= table[i][j-1]) ? max_val : table[i][j-1];
   if (i+1<n)
      max_val = (max_val >= table[i+1][j]) ? max_val : table[i+1][j];
   if (j-1>=0 && i+1<n) {
     int diag_val = table[i+1][j-1];
     if (i<j-1 && ((seq[i] + seq[j]) == 3))
        diag_val += 1;
     max_val = (max_val >= diag_val) ? max_val : diag_val;
   }
   for (k=i+1; k<j; k++) {
      int split_val = table[i][k] + table[k+1][j];
      max_val = (max_val >= split_val) ? max_val : split_val;
   }
   table[i][j] = max_val;
  }
 }
#pragma endscop
}
