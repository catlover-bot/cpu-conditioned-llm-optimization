extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < NI) && (j < NI))
	{
		DATA_TYPE acc = c[i * NI + j] * beta;

		const DATA_TYPE *ai = a + i * NJ;
		const DATA_TYPE *aj = a + j * NJ;
		const DATA_TYPE *bi = b + i * NJ;
		const DATA_TYPE *bj = b + j * NJ;

		int k;
		for (k = 0; k < NJ; k++)
		{
			acc += alpha * ai[k] * bj[k] + alpha * bi[k] * aj[k];
		}

		c[i * NI + j] = acc;
	}
}
