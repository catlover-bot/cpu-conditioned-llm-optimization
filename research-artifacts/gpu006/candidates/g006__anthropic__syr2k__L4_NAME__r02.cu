extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < NI) && (j < NI))
	{
		DATA_TYPE sum = c[i * NI + j] * beta;

		int k;
		for(k = 0; k < NJ; k++)
		{
			sum += alpha * a[i * NJ + k] * b[j * NJ + k] + alpha * b[i * NJ + k] * a[j * NJ + k];
		}

		c[i * NI + j] = sum;
	}
}
