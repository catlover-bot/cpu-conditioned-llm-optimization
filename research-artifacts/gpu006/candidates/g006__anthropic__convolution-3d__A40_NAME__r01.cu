extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) &&  (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		const DATA_TYPE c11 = +2,  c21 = +5,  c31 = -8;
		const DATA_TYPE c12 = -3,  c22 = +6,  c32 = -9;
		const DATA_TYPE c13 = +4,  c23 = +7,  c33 = +10;

		const int base = i*(NK*NJ) + j*NK + k;
		const int stride_i = NK*NJ;
		const int stride_j = NK;

		DATA_TYPE a_im1_jm1_km1 = A[base - stride_i - stride_j - 1];
		DATA_TYPE a_ip1_jm1_km1 = A[base + stride_i - stride_j - 1];
		DATA_TYPE a_im0_jm1_km0 = A[base - stride_j];
		DATA_TYPE a_im0_jm0_km0 = A[base];
		DATA_TYPE a_im0_jp1_km0 = A[base + stride_j];
		DATA_TYPE a_im1_jm1_kp1 = A[base - stride_i - stride_j + 1];
		DATA_TYPE a_ip1_jm1_kp1 = A[base + stride_i - stride_j + 1];
		DATA_TYPE a_im1_jm0_kp1 = A[base - stride_i + 1];
		DATA_TYPE a_ip1_jm0_kp1 = A[base + stride_i + 1];
		DATA_TYPE a_im1_jp1_kp1 = A[base - stride_i + stride_j + 1];
		DATA_TYPE a_ip1_jp1_kp1 = A[base + stride_i + stride_j + 1];

		B[base] = c11 * a_im1_jm1_km1  +  c13 * a_ip1_jm1_km1
			     +   c21 * a_im1_jm1_km1  +  c23 * a_ip1_jm1_km1
			     +   c31 * a_im1_jm1_km1  +  c33 * a_ip1_jm1_km1
			     +   c12 * a_im0_jm1_km0  +  c22 * a_im0_jm0_km0
			     +   c32 * a_im0_jp1_km0  +  c11 * a_im1_jm1_kp1
			     +   c13 * a_ip1_jm1_kp1  +  c21 * a_im1_jm0_kp1
			     +   c23 * a_ip1_jm0_kp1  +  c31 * a_im1_jp1_kp1
			     +   c33 * a_ip1_jp1_kp1;
	}
}
