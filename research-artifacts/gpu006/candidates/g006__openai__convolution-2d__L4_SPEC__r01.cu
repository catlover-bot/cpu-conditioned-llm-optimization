extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI - 1) && (j < _PB_NJ - 1) && (i > 0) && (j > 0))
	{
		int r0 = (i - 1) * NJ;
		int r1 = i * NJ;
		int r2 = (i + 1) * NJ;
		B[r1 + j] =
			0.2f * A[r0 + j - 1] +
			0.5f * A[r0 + j] +
			-0.8f * A[r0 + j + 1] +
			-0.3f * A[r1 + j - 1] +
			0.6f * A[r1 + j] +
			-0.9f * A[r1 + j + 1] +
			0.4f * A[r2 + j - 1] +
			0.7f * A[r2 + j] +
			0.10f * A[r2 + j + 1];
	}
}
