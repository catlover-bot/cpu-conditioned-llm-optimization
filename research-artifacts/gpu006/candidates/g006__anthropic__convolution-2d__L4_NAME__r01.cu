extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;

	c11 = +0.2;  c21 = +0.5;  c31 = -0.8;
	c12 = -0.3;  c22 = +0.6;  c32 = -0.9;
	c13 = +0.4;  c23 = +0.7;  c33 = +0.10;

	if ((i < _PB_NI-1) && (j < _PB_NJ-1) && (i > 0) && (j > 0))
	{
		int base = i * NJ + j;
		int rowU = base - NJ;
		int rowM = base;
		int rowD = base + NJ;

		DATA_TYPE au_l = A[rowU - 1];
		DATA_TYPE au_m = A[rowU];
		DATA_TYPE au_r = A[rowU + 1];
		DATA_TYPE am_l = A[rowM - 1];
		DATA_TYPE am_m = A[rowM];
		DATA_TYPE am_r = A[rowM + 1];
		DATA_TYPE ad_l = A[rowD - 1];
		DATA_TYPE ad_m = A[rowD];
		DATA_TYPE ad_r = A[rowD + 1];

		B[base] =  c11 * au_l  + c21 * au_m + c31 * au_r
			+ c12 * am_l  + c22 * am_m +  c32 * am_r
			+ c13 * ad_l  + c23 * ad_m +  c33 * ad_r;
	}
}
