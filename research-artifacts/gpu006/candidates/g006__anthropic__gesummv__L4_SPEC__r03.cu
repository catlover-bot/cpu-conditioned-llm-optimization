extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
	int i = blockIdx.x * blockDim.x + threadIdx.x;

	if (i < _PB_N)
	{
		DATA_TYPE tmp_val = tmp[i];
		DATA_TYPE y_val = y[i];
		int rowOff = i * N;
		int j;
		for(j = 0; j < _PB_N; j++)
		{
			DATA_TYPE xj = x[j];
			tmp_val += A[rowOff + j] * xj;
			y_val += B[rowOff + j] * xj;
		}
		tmp[i] = tmp_val;
		y[i] = alpha * tmp_val + beta * y_val;
	}
}
