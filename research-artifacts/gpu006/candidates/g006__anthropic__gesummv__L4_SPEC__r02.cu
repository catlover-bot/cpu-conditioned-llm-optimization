extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
	int i = blockIdx.x * blockDim.x + threadIdx.x;

	if (i < _PB_N)
	{
		DATA_TYPE tmp_val = 0.0f;
		DATA_TYPE y_val = 0.0f;
		int rowBase = i * N;
		int j;
		for(j = 0; j < _PB_N; j++)
		{
			DATA_TYPE xj = x[j];
			tmp_val += A[rowBase + j] * xj;
			y_val += B[rowBase + j] * xj;
		}
		tmp[i] = tmp_val;
		y[i] = alpha * tmp_val + beta * y_val;
	}
}
