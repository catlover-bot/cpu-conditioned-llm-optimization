extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *b, DATA_TYPE *c)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < NI) && (j < NI))
	{
		DATA_TYPE value = c[i * NI + j] * beta;
		int k;
		for (k = 0; k < NJ; k++)
		{
			DATA_TYPE product1 = alpha * a[i * NJ + k] * b[j * NJ + k];
			DATA_TYPE product2 = alpha * b[i * NJ + k] * a[j * NJ + k];
			value += product1 + product2;
		}
		c[i * NI + j] = value;
	}
}
