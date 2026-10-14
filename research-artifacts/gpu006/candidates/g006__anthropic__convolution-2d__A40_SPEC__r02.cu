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
		int rowm = base - NJ;
		int rowp = base + NJ;

		DATA_TYPE a_m1_m1 = A[rowm - 1];
		DATA_TYPE a_m1_0  = A[rowm];
		DATA_TYPE a_m1_p1 = A[rowm + 1];
		DATA_TYPE a_0_m1  = A[base - 1];
		DATA_TYPE a_0_0   = A[base];
		DATA_TYPE a_0_p1  = A[base + 1];
		DATA_TYPE a_p1_m1 = A[rowp - 1];
		DATA_TYPE a_p1_0  = A[rowp];
		DATA_TYPE a_p1_p1 = A[rowp + 1];

		B[base] =  c11 * a_m1_m1  + c21 * a_m1_0 + c31 * a_m1_p1
			+ c12 * a_0_m1  + c22 * a_0_0 +  c32 * a_0_p1
			+ c13 * a_p1_m1  + c23 * a_p1_0 +  c33 * a_p1_p1;
	}
}
