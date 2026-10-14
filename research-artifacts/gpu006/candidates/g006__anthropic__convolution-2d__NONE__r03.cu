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
		int rowm = (i - 1) * NJ;
		int row0 = i * NJ;
		int rowp = (i + 1) * NJ;

		B[row0 + j] =  c11 * A[rowm + (j - 1)]  + c21 * A[rowm + j] + c31 * A[rowm + (j + 1)]
			+ c12 * A[row0 + (j - 1)]  + c22 * A[row0 + j] +  c32 * A[row0 + (j + 1)]
			+ c13 * A[rowp + (j - 1)]  + c23 * A[rowp + j] +  c33 * A[rowp + (j + 1)];
	}
}
