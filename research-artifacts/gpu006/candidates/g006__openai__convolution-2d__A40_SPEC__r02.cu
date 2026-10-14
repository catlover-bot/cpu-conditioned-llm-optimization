extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE *A, DATA_TYPE *B)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI - 1) && (j < _PB_NJ - 1) && (i > 0) && (j > 0))
	{
		int p = i * NJ + j;
		DATA_TYPE r =
			0.2f * A[p - NJ - 1] +
			0.5f * A[p - NJ] +
			-0.8f * A[p - NJ + 1] +
			-0.3f * A[p - 1] +
			0.6f * A[p] +
			-0.9f * A[p + 1] +
			0.4f * A[p + NJ - 1] +
			0.7f * A[p + NJ] +
			0.10f * A[p + NJ + 1];
		B[p] = r;
	}
}
