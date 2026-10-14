extern "C" __global__ void kernel(int ni, int nj, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE *a, DATA_TYPE *c)
{
	int j = blockIdx.x * blockDim.x + threadIdx.x;
	int i = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < _PB_NI) && (j < _PB_NI))
	{
		DATA_TYPE v = c[i * NI + j] * beta;
		for (int k = 0; k < _PB_NJ; k++)
		{
			v += alpha * a[i * NJ + k] * a[j * NJ + k];
		}
		c[i * NI + j] = v;
	}
}
