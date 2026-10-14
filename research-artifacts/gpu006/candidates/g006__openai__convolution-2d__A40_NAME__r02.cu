extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI-1) && (j < _PB_NJ-1) && (i > 0) && (j > 0))
	{
		int p0 = (i - 1) * NJ + (j - 1);
		int p1 = i * NJ + (j - 1);
		int p2 = (i + 1) * NJ + (j - 1);

		B[i * NJ + j] =
			0.2f * A[p0] + 0.5f * A[p0 + 1] + -0.8f * A[p0 + 2]
			+ -0.3f * A[p1] + 0.6f * A[p1 + 1] + -0.9f * A[p1 + 2]
			+ 0.4f * A[p2] + 0.7f * A[p2 + 1] + 0.10f * A[p2 + 2];
	}
}
