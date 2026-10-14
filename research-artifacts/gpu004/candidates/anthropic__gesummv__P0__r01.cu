extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
	int i = blockIdx.x * blockDim.x + threadIdx.x;

	if (i < _PB_N)
	{
		DATA_TYPE tmp_sum = tmp[i];
		DATA_TYPE y_sum = y[i];
		int rowOff = i * N;
		int j;
		for(j = 0; j < _PB_N; j++)
		{
			DATA_TYPE xj = x[j];
			tmp_sum += A[rowOff + j] * xj;
			y_sum += B[rowOff + j] * xj;
		}
		tmp[i] = tmp_sum;
		y[i] = alpha * tmp_sum + beta * y_sum;
	}
}
