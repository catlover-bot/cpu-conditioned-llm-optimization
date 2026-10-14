extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;
		DATA_TYPE c11 = +2, c12 = -3, c13 = +4;
		DATA_TYPE c21 = +5, c22 = +6, c23 = +7;
		DATA_TYPE c31 = -8, c32 = -9, c33 = +10;

		B[base] = c11 * A[base - plane - NK - 1] + c13 * A[base + plane - NK - 1]
		        + c21 * A[base - plane - NK - 1] + c23 * A[base + plane - NK - 1]
		        + c31 * A[base - plane - NK - 1] + c33 * A[base + plane - NK - 1]
		        + c12 * A[base - NK] + c22 * A[base]
		        + c32 * A[base + NK] + c11 * A[base - plane - NK + 1]
		        + c13 * A[base + plane - NK + 1] + c21 * A[base - plane + 1]
		        + c23 * A[base + plane + 1] + c31 * A[base - plane + NK + 1]
		        + c33 * A[base + plane + NK + 1];
	}
}
