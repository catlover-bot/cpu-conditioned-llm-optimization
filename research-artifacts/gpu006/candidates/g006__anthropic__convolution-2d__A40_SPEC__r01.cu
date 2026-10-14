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

		DATA_TYPE au0 = A[rowU - 1];
		DATA_TYPE au1 = A[rowU];
		DATA_TYPE au2 = A[rowU + 1];
		DATA_TYPE am0 = A[rowM - 1];
		DATA_TYPE am1 = A[rowM];
		DATA_TYPE am2 = A[rowM + 1];
		DATA_TYPE ad0 = A[rowD - 1];
		DATA_TYPE ad1 = A[rowD];
		DATA_TYPE ad2 = A[rowD + 1];

		B[base] =  c11 * au0  + c21 * au1 + c31 * au2
			+ c12 * am0  + c22 * am1 +  c32 * am2
			+ c13 * ad0  + c23 * ad1 +  c33 * ad2;
	}
}
