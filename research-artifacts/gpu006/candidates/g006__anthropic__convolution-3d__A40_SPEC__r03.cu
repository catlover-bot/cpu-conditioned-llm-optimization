extern "C" __global__ void kernel(int ni, int nj, int nk, DATA_TYPE* A, DATA_TYPE* B, int i)
{
	int k = blockIdx.x * blockDim.x + threadIdx.x;
	int j = blockIdx.y * blockDim.y + threadIdx.y;

	DATA_TYPE c11, c12, c13, c21, c22, c23, c31, c32, c33;

	c11 = +2;  c21 = +5;  c31 = -8;
	c12 = -3;  c22 = +6;  c32 = -9;
	c13 = +4;  c23 = +7;  c33 = +10;


	if ((i < (_PB_NI-1)) && (j < (_PB_NJ-1)) &&  (k < (_PB_NK-1)) && (i > 0) && (j > 0) && (k > 0))
	{
		int base = i*(NK * NJ) + j*NK + k;
		int im1 = (i - 1)*(NK * NJ);
		int ip1 = (i + 1)*(NK * NJ);
		int i0  = i*(NK * NJ);
		int jm1 = (j - 1)*NK;
		int j0  = j*NK;
		int jp1 = (j + 1)*NK;
		int km1 = k - 1;
		int k0  = k;
		int kp1 = k + 1;

		DATA_TYPE a_im1_jm1_km1 = A[im1 + jm1 + km1];
		DATA_TYPE a_ip1_jm1_km1 = A[ip1 + jm1 + km1];

		B[base] = c11 * a_im1_jm1_km1  +  c13 * a_ip1_jm1_km1
			     +   c21 * a_im1_jm1_km1  +  c23 * a_ip1_jm1_km1
			     +   c31 * a_im1_jm1_km1  +  c33 * a_ip1_jm1_km1
			     +   c12 * A[i0 + jm1 + k0]  +  c22 * A[i0 + j0 + k0]
			     +   c32 * A[i0 + jp1 + k0]  +  c11 * A[im1 + jm1 + kp1]
			     +   c13 * A[ip1 + jm1 + kp1]  +  c21 * A[im1 + j0 + kp1]
			     +   c23 * A[ip1 + j0 + kp1]  +  c31 * A[im1 + jp1 + kp1]
			     +   c33 * A[ip1 + jp1 + kp1];
	}
}
