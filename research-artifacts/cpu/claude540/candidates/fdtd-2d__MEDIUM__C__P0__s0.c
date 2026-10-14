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
      double fict_t = _fict_[t];
      for (j = 0; j < ny; j++)
 ey[0][j] = fict_t;
      for (i = 1; i < nx; i++) {
 double *ey_i = ey[i];
 double *hz_i = hz[i];
 double *hz_im1 = hz[i-1];
 for (j = 0; j < ny; j++)
   ey_i[j] = ey_i[j] - 0.5*(hz_i[j]-hz_im1[j]);
      }
      for (i = 0; i < nx; i++) {
 double *ex_i = ex[i];
 double *hz_i = hz[i];
 for (j = 1; j < ny; j++)
   ex_i[j] = ex_i[j] - 0.5*(hz_i[j]-hz_i[j-1]);
      }
      for (i = 0; i < nx - 1; i++) {
 double *hz_i = hz[i];
 double *ex_i = ex[i];
 double *ey_i = ey[i];
 double *ey_ip1 = ey[i+1];
 for (j = 0; j < ny - 1; j++)
   hz_i[j] = hz_i[j] - 0.7* (ex_i[j+1] - ex_i[j] +
           ey_ip1[j] - ey_i[j]);
      }
    }
#pragma endscop
}
