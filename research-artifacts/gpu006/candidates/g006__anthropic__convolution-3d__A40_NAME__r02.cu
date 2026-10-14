extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) &&  (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		const DATA_TYPE c11 = +2,  c21 = +5,  c31 = -8;
		const DATA_TYPE c12 = -3,  c22 = +6,  c32 = -9;
		const DATA_TYPE c13 = +4,  c23 = +7,  c33 = +10;

		const int base = i*(NK * NJ) + j*NK + k;
		const DATA_TYPE a_im1_jm1_km1 = A[base - NK*NJ - NK - 1];
		const DATA_TYPE a_ip1_jm1_km1 = A[base + NK*NJ - NK - 1];
		const DATA_TYPE a_i_jm1_k    = A[base - NK];
		const DATA_TYPE a_i_j_k      = A[base];
		const DATA_TYPE a_i_jp1_k    = A[base + NK];
		const DATA_TYPE a_im1_jm1_kp1= A[base - NK*NJ - NK + 1];
		const DATA_TYPE a_ip1_jm1_kp1= A[base + NK*NJ - NK + 1];
		const DATA_TYPE a_im1_j_kp1  = A[base - NK*NJ + 1];
		const DATA_TYPE a_ip1_j_kp1  = A[base + NK*NJ + 1];
		const DATA_TYPE a_im1_jp1_kp1= A[base - NK*NJ + NK + 1];
		const DATA_TYPE a_ip1_jp1_kp1= A[base + NK*NJ + NK + 1];

		B[base] = c11 * a_im1_jm1_km1  +  c13 * a_ip1_jm1_km1
			     +   c21 * a_im1_jm1_km1  +  c23 * a_ip1_jm1_km1
			     +   c31 * a_im1_jm1_km1  +  c33 * a_ip1_jm1_km1
			     +   c12 * a_i_jm1_k      +  c22 * a_i_j_k
			     +   c32 * a_i_jp1_k      +  c11 * a_im1_jm1_kp1
			     +   c13 * a_ip1_jm1_kp1  +  c21 * a_im1_j_kp1
			     +   c23 * a_ip1_j_kp1    +  c31 * a_im1_jp1_kp1
			     +   c33 * a_ip1_jp1_kp1;
	}
}
