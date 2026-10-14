#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_fdtd_2d(int tmax,
      int nx,
      int ny,
      double ex[ nx + 0][ny + 0],
      double ey[ nx + 0][ny + 0],
      double hz[ nx + 0][ny + 0],
      double _fict_[ tmax + 0])
{
  int t, i, j;
#pragma scop
  for(t = 0; t < tmax; t++)
    {
      for (j = 0; j < ny; j++)
 ey[0][j] = _fict_[t];
      for (i = 1; i < nx; i++) {
 double * restrict ey_i = ey[i];
 const double * restrict hz_i = hz[i];
 const double * restrict hz_im1 = hz[i-1];
 for (j = 0; j < ny; j++)
   ey_i[j] = ey_i[j] - 0.5*(hz_i[j]-hz_im1[j]);
      }
      for (i = 0; i < nx; i++) {
 double * restrict ex_i = ex[i];
 const double * restrict hz_i = hz[i];
 for (j = 1; j < ny; j++)
   ex_i[j] = ex_i[j] - 0.5*(hz_i[j]-hz_i[j-1]);
      }
      for (i = 0; i < nx - 1; i++) {
 double * restrict hz_i = hz[i];
 const double * restrict ex_i = ex[i];
 const double * restrict ey_i = ey[i];
 const double * restrict ey_ip1 = ey[i+1];
 for (j = 0; j < ny - 1; j++)
   hz_i[j] = hz_i[j] - 0.7* (ex_i[j+1] - ex_i[j] +
           ey_ip1[j] - ey_i[j]);
      }
    }
#pragma endscop
}
