extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI - 1) && (j < _PB_NJ - 1) && (i > 0) && (j > 0))
	{
		int row0 = (i - 1) * NJ;
		int row1 = i * NJ;
		int row2 = (i + 1) * NJ;

		DATA_TYPE t0 = 0.2f * A[row0 + j - 1] + 0.5f * A[row0 + j];
		DATA_TYPE t1 = t0 + -0.8f * A[row0 + j + 1];
		DATA_TYPE t2 = t1 + -0.3f * A[row1 + j - 1];
		DATA_TYPE t3 = t2 + 0.6f * A[row1 + j];
		DATA_TYPE t4 = t3 + -0.9f * A[row1 + j + 1];
		DATA_TYPE t5 = t4 + 0.4f * A[row2 + j - 1];
		DATA_TYPE t6 = t5 + 0.7f * A[row2 + j];
		B[row1 + j] = t6 + 0.10f * A[row2 + j + 1];
	}
}
