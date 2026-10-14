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
		int base_im1_jm1_km1 = (i - 1)*(NK * NJ) + (j - 1)*NK + (k - 1);
		int base_ip1_jm1_km1 = (i + 1)*(NK * NJ) + (j - 1)*NK + (k - 1);
		DATA_TYPE a_im1_jm1_km1 = A[base_im1_jm1_km1];
		DATA_TYPE a_ip1_jm1_km1 = A[base_ip1_jm1_km1];

		B[i*(NK * NJ) + j*NK + k] = c11 * a_im1_jm1_km1  +  c13 * a_ip1_jm1_km1
					     +   c21 * a_im1_jm1_km1  +  c23 * a_ip1_jm1_km1
					     +   c31 * a_im1_jm1_km1  +  c33 * a_ip1_jm1_km1
					     +   c12 * A[(i + 0)*(NK * NJ) + (j - 1)*NK + (k + 0)]  +  c22 * A[(i + 0)*(NK * NJ) + (j + 0)*NK + (k + 0)]   
					     +   c32 * A[(i + 0)*(NK * NJ) + (j + 1)*NK + (k + 0)]  +  c11 * A[(i - 1)*(NK * NJ) + (j - 1)*NK + (k + 1)]  
					     +   c13 * A[(i + 1)*(NK * NJ) + (j - 1)*NK + (k + 1)]  +  c21 * A[(i - 1)*(NK * NJ) + (j + 0)*NK + (k + 1)]  
					     +   c23 * A[(i + 1)*(NK * NJ) + (j + 0)*NK + (k + 1)]  +  c31 * A[(i - 1)*(NK * NJ) + (j + 1)*NK + (k + 1)]  
					     +   c33 * A[(i + 1)*(NK * NJ) + (j + 1)*NK + (k + 1)];
	}
}
