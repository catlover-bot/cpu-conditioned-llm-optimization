#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_adi(int tsteps, int n,
  double u[ n + 0][n + 0],
  double v[ n + 0][n + 0],
  double p[ n + 0][n + 0],
  double q[ n + 0][n + 0])
{
  int t, i, j;
  double DX, DY, DT;
  double B1, B2;
  double mul1, mul2;
  double a, b, c, d, e, f;
#pragma scop
  DX = 1.0/(double)n;
  DY = 1.0/(double)n;
  DT = 1.0/(double)tsteps;
  B1 = 2.0;
  B2 = 1.0;
  mul1 = B1 * DT / (DX * DX);
  mul2 = B2 * DT / (DY * DY);
  a = -mul1 / 2.0;
  b = 1.0 +mul1;
  c = a;
  d = -mul2 / 2.0;
  e = 1.0 +mul2;
  f = d;
 for (t=1; t<=tsteps; t++) {
    for (i=1; i<n-1; i++) {
      double *pi = p[i];
      double *qi = q[i];
      v[0][i] = 1.0;
      pi[0] = 0.0;
      qi[0] = v[0][i];
      double qprev = qi[0];
      double pprev = pi[0];
      for (j=1; j<n-1; j++) {
        double denom = a*pprev+b;
        double pj = -c / denom;
        double *uj = u[j];
        double qj = (-d*uj[i-1]+(1.0 +2.0*d)*uj[i] - f*uj[i+1]-a*qprev)/denom;
        pi[j] = pj;
        qi[j] = qj;
        pprev = pj;
        qprev = qj;
      }
      v[n-1][i] = 1.0;
      double vnext = v[n-1][i];
      for (j=n-2; j>=1; j--) {
        vnext = pi[j] * vnext + qi[j];
        v[j][i] = vnext;
      }
    }
    for (i=1; i<n-1; i++) {
      double *pi = p[i];
      double *qi = q[i];
      double *ui = u[i];
      double *vim1 = v[i-1];
      double *vi = v[i];
      double *vip1 = v[i+1];
      ui[0] = 1.0;
      pi[0] = 0.0;
      qi[0] = ui[0];
      double qprev = qi[0];
      double pprev = pi[0];
      for (j=1; j<n-1; j++) {
        double denom = d*pprev+e;
        double pj = -f / denom;
        double qj = (-a*vim1[j]+(1.0 +2.0*a)*vi[j] - c*vip1[j]-d*qprev)/denom;
        pi[j] = pj;
        qi[j] = qj;
        pprev = pj;
        qprev = qj;
      }
      ui[n-1] = 1.0;
      double unext = ui[n-1];
      for (j=n-2; j>=1; j--) {
        unext = pi[j] * unext + qi[j];
        ui[j] = unext;
      }
    }
  }
#pragma endscop
}
