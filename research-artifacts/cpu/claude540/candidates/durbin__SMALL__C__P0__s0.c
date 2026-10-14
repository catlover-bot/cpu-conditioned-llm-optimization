#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_durbin(int n,
     double r[ n + 0],
     double y[ n + 0])
{
 double z[120];
 double alpha;
 double beta;
 double sum;
 int i,k;
#pragma scop
 y[0] = -r[0];
 beta = 1.0;
 alpha = -r[0];
 for (k = 1; k < n; k++) {
   beta = (1-alpha*alpha)*beta;
   sum = 0.0;
   for (i=0; i<k; i++) {
      sum += r[k-i-1]*y[i];
   }
   alpha = - (r[k] + sum)/beta;
   int half = k >> 1;
   for (i=0; i<half; i++) {
      double yi = y[i];
      double yj = y[k-i-1];
      z[i] = yi + alpha*yj;
      z[k-i-1] = yj + alpha*yi;
   }
   if (k & 1) {
      double ym = y[half];
      z[half] = ym + alpha*ym;
   }
   for (i=0; i<k; i++) {
     y[i] = z[i];
   }
   y[k] = alpha;
 }
#pragma endscop
}
