extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;

	c11 = +2;  c21 = +5;  c31 = -8;
	c12 = -3;  c22 = +6;  c32 = -9;
	c13 = +4;  c23 = +7;  c33 = +10;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;
		DATA_TYPE a0 = A[(i - 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE a1 = A[(i + 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE a2 = A[(i + 0) * plane + (j - 1) * NK + (k + 0)];
		DATA_TYPE a3 = A[(i + 0) * plane + (j + 0) * NK + (k + 0)];
		DATA_TYPE a4 = A[(i + 0) * plane + (j + 1) * NK + (k + 0)];
		DATA_TYPE a5 = A[(i - 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE a6 = A[(i + 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE a7 = A[(i - 1) * plane + (j + 0) * NK + (k + 1)];
		DATA_TYPE a8 = A[(i + 1) * plane + (j + 0) * NK + (k + 1)];
		DATA_TYPE a9 = A[(i - 1) * plane + (j + 1) * NK + (k + 1)];
		DATA_TYPE a10 = A[(i + 1) * plane + (j + 1) * NK + (k + 1)];

		B[base] = c11 * a0 + c13 * a1
			+ c21 * a0 + c23 * a1
			+ c31 * a0 + c33 * a1
			+ c12 * a2 + c22 * a3
			+ c32 * a4 + c11 * a5
			+ c13 * a6 + c21 * a7
			+ c23 * a8 + c31 * a9
			+ c33 * a10;
	}
}
