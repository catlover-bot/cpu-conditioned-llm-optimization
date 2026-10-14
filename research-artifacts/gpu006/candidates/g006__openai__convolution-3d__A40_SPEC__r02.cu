extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;

		DATA_TYPE v0 = A[(i - 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE v1 = A[(i + 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE v2 = A[i * plane + (j - 1) * NK + k];
		DATA_TYPE v3 = A[i * plane + j * NK + k];
		DATA_TYPE v4 = A[i * plane + (j + 1) * NK + k];
		DATA_TYPE v5 = A[(i - 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE v6 = A[(i + 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE v7 = A[(i - 1) * plane + j * NK + (k + 1)];
		DATA_TYPE v8 = A[(i + 1) * plane + j * NK + (k + 1)];
		DATA_TYPE v9 = A[(i - 1) * plane + (j + 1) * NK + (k + 1)];
		DATA_TYPE v10 = A[(i + 1) * plane + (j + 1) * NK + (k + 1)];

		DATA_TYPE r = 2.0f * v0 + 4.0f * v1
		            + 5.0f * v0 + 7.0f * v1
		            + -8.0f * v0 + 10.0f * v1
		            + -3.0f * v2 + 6.0f * v3
		            + -9.0f * v4 + 2.0f * v5
		            + 4.0f * v6 + 5.0f * v7
		            + 7.0f * v8 + -8.0f * v9
		            + 10.0f * v10;
		B[base] = r;
	}
}
