extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;

		DATA_TYPE t;
		t = 2.0f * A[base - plane - NK - 1];
		t = t + 4.0f * A[base + plane - NK - 1];
		t = t + 5.0f * A[base - plane - NK - 1];
		t = t + 7.0f * A[base + plane - NK - 1];
		t = t + -8.0f * A[base - plane - NK - 1];
		t = t + 10.0f * A[base + plane - NK - 1];
		t = t + -3.0f * A[base - NK];
		t = t + 6.0f * A[base];
		t = t + -9.0f * A[base + NK];
		t = t + 2.0f * A[base - plane - NK + 1];
		t = t + 4.0f * A[base + plane - NK + 1];
		t = t + 5.0f * A[base - plane + 1];
		t = t + 7.0f * A[base + plane + 1];
		t = t + -8.0f * A[base - plane + NK + 1];
		t = t + 10.0f * A[base + plane + NK + 1];

		B[base] = t;
	}
}
