extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;

    if ((i < (_PB_NI - 1)) && (j < (_PB_NJ - 1)) && (k < (_PB_NK - 1)) &&
        (i > 0) && (j > 0) && (k > 0))
    {
        int plane = NK * NJ;
        int out = i * plane + j * NK + k;

        DATA_TYPE a0 = A[(i - 1) * plane + (j - 1) * NK + (k - 1)];
        DATA_TYPE a1 = A[(i + 1) * plane + (j - 1) * NK + (k - 1)];
        DATA_TYPE a2 = A[i * plane + (j - 1) * NK + k];
        DATA_TYPE a3 = A[i * plane + j * NK + k];
        DATA_TYPE a4 = A[i * plane + (j + 1) * NK + k];
        DATA_TYPE a5 = A[(i - 1) * plane + (j - 1) * NK + (k + 1)];
        DATA_TYPE a6 = A[(i + 1) * plane + (j - 1) * NK + (k + 1)];
        DATA_TYPE a7 = A[(i - 1) * plane + j * NK + (k + 1)];
        DATA_TYPE a8 = A[(i + 1) * plane + j * NK + (k + 1)];
        DATA_TYPE a9 = A[(i - 1) * plane + (j + 1) * NK + (k + 1)];
        DATA_TYPE a10 = A[(i + 1) * plane + (j + 1) * NK + (k + 1)];

        B[out] = 2.0f * a0 + 4.0f * a1
               + 5.0f * a0 + 7.0f * a1
               - 8.0f * a0 + 10.0f * a1
               - 3.0f * a2 + 6.0f * a3
               - 9.0f * a4 + 2.0f * a5
               + 4.0f * a6 + 5.0f * a7
               + 7.0f * a8 - 8.0f * a9
               + 10.0f * a10;
    }
}
