extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI) && (j < _PB_NJ))
	{
		DATA_TYPE acc = c[i * NJ + j] * beta;
		int k;
		const DATA_TYPE *arow = a + i * NK;
		for(k = 0; k < _PB_NK; k++)
		{
			acc += alpha * arow[k] * b[k * NJ + j];
		}
		c[i * NJ + j] = acc;
	}
}
