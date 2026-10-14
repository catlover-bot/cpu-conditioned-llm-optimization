extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < _PB_N)
    {
        DATA_TYPE t = tmp[i];
        DATA_TYPE v = y[i];
        int base = i * N;
        for (int j = 0; j < _PB_N; ++j)
        {
            t += A[base + j] * x[j];
            v += B[base + j] * x[j];
        }
        tmp[i] = t;
        y[i] = alpha * t + beta * v;
    }
}
