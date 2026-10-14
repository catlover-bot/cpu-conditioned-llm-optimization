extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
	int i = blockIdx.x * blockDim.x + threadIdx.x;

	if (i < _PB_N)
	{
		DATA_TYPE tmp_local = tmp[i];
		DATA_TYPE y_local = y[i];
		int rowBase = i * N;
		int j;
		for(j = 0; j < _PB_N; j++)
		{
			DATA_TYPE xj = x[j];
			tmp_local += A[rowBase + j] * xj;
			y_local += B[rowBase + j] * xj;
		}
		tmp[i] = tmp_local;
		y[i] = alpha * tmp_local + beta * y_local;
	}
}
