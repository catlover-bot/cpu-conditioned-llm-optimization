extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;

		DATA_TYPE v0 = A[base - plane - NK - 1];
		DATA_TYPE v1 = A[base + plane - NK - 1];
		DATA_TYPE v2 = A[base - NK];
		DATA_TYPE v3 = A[base];
		DATA_TYPE v4 = A[base + NK];
		DATA_TYPE v5 = A[base - plane - NK + 1];
		DATA_TYPE v6 = A[base + plane - NK + 1];
		DATA_TYPE v7 = A[base - plane + 1];
		DATA_TYPE v8 = A[base + plane + 1];
		DATA_TYPE v9 = A[base - plane + NK + 1];
		DATA_TYPE v10 = A[base + plane + NK + 1];

		DATA_TYPE r = 2.0f * v0 + 4.0f * v1;
		r = r + 5.0f * v0;
		r = r + 7.0f * v1;
		r = r + -8.0f * v0;
		r = r + 10.0f * v1;
		r = r + -3.0f * v2;
		r = r + 6.0f * v3;
		r = r + -9.0f * v4;
		r = r + 2.0f * v5;
		r = r + 4.0f * v6;
		r = r + 5.0f * v7;
		r = r + 7.0f * v8;
		r = r + -8.0f * v9;
		r = r + 10.0f * v10;

		B[base] = r;
	}
}
