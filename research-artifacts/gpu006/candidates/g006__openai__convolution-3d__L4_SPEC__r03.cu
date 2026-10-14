extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

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

		B[base] = 2 * a0 + 4 * a1
		        + 5 * a0 + 7 * a1
		        - 8 * a0 + 10 * a1
		        - 3 * a2 + 6 * a3
		        - 9 * a4 + 2 * a5
		        + 4 * a6 + 5 * a7
		        + 7 * a8 - 8 * a9
		        + 10 * a10;
	}
}
