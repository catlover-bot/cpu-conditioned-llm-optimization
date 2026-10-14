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
		const int planeM = base - (NK*NJ);
		const int planeP = base + (NK*NJ);

		DATA_TYPE a_m1_m1_m1 = A[planeM - NK - 1];
		DATA_TYPE a_p1_m1_m1 = A[planeP - NK - 1];
		DATA_TYPE a_0_m1_0   = A[base   - NK];
		DATA_TYPE a_0_0_0    = A[base];
		DATA_TYPE a_0_p1_0   = A[base   + NK];
		DATA_TYPE a_m1_m1_p1 = A[planeM - NK + 1];
		DATA_TYPE a_p1_m1_p1 = A[planeP - NK + 1];
		DATA_TYPE a_m1_0_p1  = A[planeM + 1];
		DATA_TYPE a_p1_0_p1  = A[planeP + 1];
		DATA_TYPE a_m1_p1_p1 = A[planeM + NK + 1];
		DATA_TYPE a_p1_p1_p1 = A[planeP + NK + 1];

		B[base] = c11 * a_m1_m1_m1 + c13 * a_p1_m1_m1
			+ c21 * a_m1_m1_m1 + c23 * a_p1_m1_m1
			+ c31 * a_m1_m1_m1 + c33 * a_p1_m1_m1
			+ c12 * a_0_m1_0   + c22 * a_0_0_0
			+ c32 * a_0_p1_0   + c11 * a_m1_m1_p1
			+ c13 * a_p1_m1_p1 + c21 * a_m1_0_p1
			+ c23 * a_p1_0_p1  + c31 * a_m1_p1_p1
			+ c33 * a_p1_p1_p1;
	}
}
