extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	const DATA_TYPE c11 = +2,  c21 = +5,  c31 = -8;
	const DATA_TYPE c12 = -3,  c22 = +6,  c32 = -9;
	const DATA_TYPE c13 = +4,  c23 = +7,  c33 = +10;

	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) &&  (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int base_im1 = (i - 1)*(NK * NJ);
		int base_i   = i*(NK * NJ);
		int base_ip1 = (i + 1)*(NK * NJ);

		int jm1 = (j - 1)*NK;
		int j0  = j*NK;
		int jp1 = (j + 1)*NK;

		int km1 = k - 1;
		int k0  = k;
		int kp1 = k + 1;

		DATA_TYPE a_im1_jm1_km1 = A[base_im1 + jm1 + km1];
		DATA_TYPE a_ip1_jm1_km1 = A[base_ip1 + jm1 + km1];

		B[base_i + j0 + k] = c11 * a_im1_jm1_km1  +  c13 * a_ip1_jm1_km1
				     +   c21 * a_im1_jm1_km1  +  c23 * a_ip1_jm1_km1
				     +   c31 * a_im1_jm1_km1  +  c33 * a_ip1_jm1_km1
				     +   c12 * A[base_i + jm1 + k0]  +  c22 * A[base_i + j0 + k0]
				     +   c32 * A[base_i + jp1 + k0]  +  c11 * A[base_im1 + jm1 + kp1]
				     +   c13 * A[base_ip1 + jm1 + kp1]  +  c21 * A[base_im1 + j0 + kp1]
				     +   c23 * A[base_ip1 + j0 + kp1]  +  c31 * A[base_im1 + jp1 + kp1]
				     +   c33 * A[base_ip1 + jp1 + kp1];
	}
}
