#include <math.h>
#include <stdint.h>
#include <stddef.h>

__attribute__((noinline)) void kernel_deriche(int w, int h, float alpha,
       float imgIn[ w + 0][h + 0],
       float imgOut[ w + 0][h + 0],
       float y1[ w + 0][h + 0],
       float y2[ w + 0][h + 0]) {
    int i,j;
    float xm1, tm1, ym1, ym2;
    float xp1, xp2;
    float tp1, tp2;
    float yp1, yp2;
    float k;
    float a1, a2, a3, a4, a5, a6, a7, a8;
    float b1, b2, c1, c2;
#pragma scop
   k = (1.0f -expf(-alpha))*(1.0f -expf(-alpha))/(1.0f +2.0f*alpha*expf(-alpha)-expf(2.0f*alpha));
   a1 = a5 = k;
   a2 = a6 = k*expf(-alpha)*(alpha-1.0f);
   a3 = a7 = k*expf(-alpha)*(alpha+1.0f);
   a4 = a8 = -k*expf(-2.0f*alpha);
   b1 = powf(2.0f,-alpha);
   b2 = -expf(-2.0f*alpha);
   c1 = c2 = 1;
   for (i=0; i<w; i++) {
        ym1 = 0.0f;
        ym2 = 0.0f;
        xm1 = 0.0f;
        float *restrict row_in = imgIn[i];
        float *restrict row_y1 = y1[i];
        for (j=0; j<h; j++) {
            float cur = a1*row_in[j] + a2*xm1 + b1*ym1 + b2*ym2;
            row_y1[j] = cur;
            xm1 = row_in[j];
            ym2 = ym1;
            ym1 = cur;
        }
    }
    for (i=0; i<w; i++) {
        yp1 = 0.0f;
        yp2 = 0.0f;
        xp1 = 0.0f;
        xp2 = 0.0f;
        float *restrict row_in = imgIn[i];
        float *restrict row_y2 = y2[i];
        for (j=h-1; j>=0; j--) {
            float cur = a3*xp1 + a4*xp2 + b1*yp1 + b2*yp2;
            row_y2[j] = cur;
            xp2 = xp1;
            xp1 = row_in[j];
            yp2 = yp1;
            yp1 = cur;
        }
    }
    for (i=0; i<w; i++) {
        float *restrict row_y1 = y1[i];
        float *restrict row_y2 = y2[i];
        float *restrict row_out = imgOut[i];
        for (j=0; j<h; j++) {
            row_out[j] = c1 * (row_y1[j] + row_y2[j]);
        }
    }
    for (j=0; j<h; j++) {
        tm1 = 0.0f;
        ym1 = 0.0f;
        ym2 = 0.0f;
        for (i=0; i<w; i++) {
            float cur = a5*imgOut[i][j] + a6*tm1 + b1*ym1 + b2*ym2;
            y1[i][j] = cur;
            tm1 = imgOut[i][j];
            ym2 = ym1;
            ym1 = cur;
        }
    }
    for (j=0; j<h; j++) {
        tp1 = 0.0f;
        tp2 = 0.0f;
        yp1 = 0.0f;
        yp2 = 0.0f;
        for (i=w-1; i>=0; i--) {
            float cur = a7*tp1 + a8*tp2 + b1*yp1 + b2*yp2;
            y2[i][j] = cur;
            tp2 = tp1;
            tp1 = imgOut[i][j];
            yp2 = yp1;
            yp1 = cur;
        }
    }
    for (i=0; i<w; i++) {
        float *restrict row_y1 = y1[i];
        float *restrict row_y2 = y2[i];
        float *restrict row_out = imgOut[i];
        for (j=0; j<h; j++)
            row_out[j] = c2*(row_y1[j] + row_y2[j]);
    }
#pragma endscop
}
