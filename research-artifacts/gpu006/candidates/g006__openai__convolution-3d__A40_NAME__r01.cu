extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
    int k = blockIdx.x * blockDim.x + threadIdx.x;
    int j = blockIdx.y * blockDim.y + threadIdx.y;

    if ((i < (_PB_NI - 1)) && (j < (_PB_NJ - 1)) && (k < (_PB_NK - 1)) &&
        (i > 0) && (j > 0) && (k > 0))
    {
        int plane = NK * NJ;
        int base = i * plane + j * NK + k;

        DATA_TYPE a_im_jm_km = A[base - plane - NK - 1];
        DATA_TYPE a_ip_jm_km = A[base + plane - NK - 1];
        DATA_TYPE a_i_jm_k  = A[base - NK];
        DATA_TYPE a_i_j_k   = A[base];
        DATA_TYPE a_i_jp_k  = A[base + NK];
        DATA_TYPE a_im_jm_kp = A[base - plane - NK + 1];
        DATA_TYPE a_ip_jm_kp = A[base + plane - NK + 1];
        DATA_TYPE a_im_j_kp  = A[base - plane + 1];
        DATA_TYPE a_ip_j_kp  = A[base + plane + 1];
        DATA_TYPE a_im_jp_kp = A[base - plane + NK + 1];
        DATA_TYPE a_ip_jp_kp = A[base + plane + NK + 1];

        DATA_TYPE r = 2.0f * a_im_jm_km;
        r = r + 4.0f * a_ip_jm_km;
        r = r + 5.0f * a_im_jm_km;
        r = r + 7.0f * a_ip_jm_km;
        r = r + (-8.0f) * a_im_jm_km;
        r = r + 10.0f * a_ip_jm_km;
        r = r + (-3.0f) * a_i_jm_k;
        r = r + 6.0f * a_i_j_k;
        r = r + (-9.0f) * a_i_jp_k;
        r = r + 2.0f * a_im_jm_kp;
        r = r + 4.0f * a_ip_jm_kp;
        r = r + 5.0f * a_im_j_kp;
        r = r + 7.0f * a_ip_j_kp;
        r = r + (-8.0f) * a_im_jp_kp;
        r = r + 10.0f * a_ip_jp_kp;

        B[base] = r;
    }
}
