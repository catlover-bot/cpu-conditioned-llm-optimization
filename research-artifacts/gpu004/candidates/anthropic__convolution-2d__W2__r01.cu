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
		int rowm = (i - 1) * NJ + j;
		int row0 = i * NJ + j;
		int rowp = (i + 1) * NJ + j;

		DATA_TYPE am1 = A[rowm - 1];
		DATA_TYPE am0 = A[rowm];
		DATA_TYPE am2 = A[rowm + 1];
		DATA_TYPE a01 = A[row0 - 1];
		DATA_TYPE a00 = A[row0];
		DATA_TYPE a02 = A[row0 + 1];
		DATA_TYPE ap1 = A[rowp - 1];
		DATA_TYPE ap0 = A[rowp];
		DATA_TYPE ap2 = A[rowp + 1];

		B[row0] =  c11 * am1  + c21 * am0 + c31 * am2
			+ c12 * a01  + c22 * a00 +  c32 * a02
			+ c13 * ap1  + c23 * ap0 +  c33 * ap2;
	}
}
