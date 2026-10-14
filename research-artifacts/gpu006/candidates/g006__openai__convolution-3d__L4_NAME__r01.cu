extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;

	c11 = +2;  c21 = +5;  c31 = -8;
	c12 = -3;  c22 = +6;  c32 = -9;
	c13 = +4;  c23 = +7;  c33 = +10;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) && (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int plane = NK * NJ;
		int base = i * plane + j * NK + k;
		DATA_TYPE a_im_jm_km = A[(i - 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE a_ip_jm_km = A[(i + 1) * plane + (j - 1) * NK + (k - 1)];
		DATA_TYPE a_i_jm_k = A[i * plane + (j - 1) * NK + k];
		DATA_TYPE a_i_j_k = A[base];
		DATA_TYPE a_i_jp_k = A[i * plane + (j + 1) * NK + k];
		DATA_TYPE a_im_jm_kp = A[(i - 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE a_ip_jm_kp = A[(i + 1) * plane + (j - 1) * NK + (k + 1)];
		DATA_TYPE a_im_j_kp = A[(i - 1) * plane + j * NK + (k + 1)];
		DATA_TYPE a_ip_j_kp = A[(i + 1) * plane + j * NK + (k + 1)];
		DATA_TYPE a_im_jp_kp = A[(i - 1) * plane + (j + 1) * NK + (k + 1)];
		DATA_TYPE a_ip_jp_kp = A[(i + 1) * plane + (j + 1) * NK + (k + 1)];

		B[base] = c11 * a_im_jm_km + c13 * a_ip_jm_km
		        + c21 * a_im_jm_km + c23 * a_ip_jm_km
		        + c31 * a_im_jm_km + c33 * a_ip_jm_km
		        + c12 * a_i_jm_k + c22 * a_i_j_k
		        + c32 * a_i_jp_k + c11 * a_im_jm_kp
		        + c13 * a_ip_jm_kp + c21 * a_im_j_kp
		        + c23 * a_ip_j_kp + c31 * a_im_jp_kp
		        + c33 * a_ip_jp_kp;
	}
}
