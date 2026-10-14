extern "C" __global__ void kernel(int n, DATA_TYPE alpha, DATA_TYPE beta, DATA_TYPE* A, DATA_TYPE* B, DATA_TYPE* tmp, DATA_TYPE* x, DATA_TYPE* y)
{
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < _PB_N)
    {
        DATA_TYPE t = tmp[i];
        DATA_TYPE r = y[i];
        int base = i * N;
        for (int j = 0; j < _PB_N; ++j)
        {
            DATA_TYPE xv = x[j];
            t += A[base + j] * xv;
            r += B[base + j] * xv;
        }
        tmp[i] = t;
        y[i] = alpha * t + beta * r;
    }
}
