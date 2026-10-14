; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.tsteps = icmp sgt i32 %tsteps, 0
  %and.cond = and i1 %cmp.n, %cmp.tsteps
  br i1 %and.cond, label %precompute, label %for.end246

precompute:
  %n64 = sext i32 %n to i64
  %conv = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %conv
  %DY = fdiv double 1.000000e+00, %conv
  %conv10 = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %conv10

  %mulB1DT = fmul double 2.000000e+00, %DT
  %mulDXDX = fmul double %DX, %DX
  %mul1 = fdiv double %mulB1DT, %mulDXDX

  %mulB2DT = fmul double 1.000000e+00, %DT
  %mulDYDY = fmul double %DY, %DY
  %mul2 = fdiv double %mulB2DT, %mulDYDY

  %fneg.mul1 = fneg double %mul1
  %a = fdiv double %fneg.mul1, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fadd double 0.000000e+00, %a

  %fneg.mul2 = fneg double %mul2
  %d = fdiv double %fneg.mul2, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fadd double 0.000000e+00, %d

  %nm1 = sub nsw i32 %n, 1
  %nm1_64 = sext i32 %nm1 to i64
  %nm2 = sub nsw i32 %n, 2
  %nm2_64 = sext i32 %nm2 to i64

  ; precompute f/e, a/e... no, keep exact same expr order per element, just cache invariant scalars
  %mul.d2 = fmul double 2.000000e+00, %d
  %add.d2 = fadd double 1.000000e+00, %mul.d2
  %mul.a2 = fmul double 2.000000e+00, %a
  %add.a2 = fadd double 1.000000e+00, %mul.a2
  %fneg.f = fneg double %f
  %fneg.d = fneg double %d
  %fneg.a = fneg double %a
  %fneg.c = fneg double %c

  br label %for.t

for.t:
  %t = phi i32 [ 1, %precompute ], [ %inc245, %for.inc244 ]
  br label %for.i1

for.i1:
  %i1 = phi i32 [ 1, %for.t ], [ %inc128, %for.end126 ]
  %i1_64 = sext i32 %i1 to i64

  ; v[0][i] = 1.0
  %v_row0 = getelementptr inbounds double, ptr %v, i64 0
  %v0i.ptr = getelementptr inbounds double, ptr %v_row0, i64 %i1_64
  store double 1.000000e+00, ptr %v0i.ptr, align 8

  ; p[i][0] = 0.0
  %p_i_off = mul nsw i64 %i1_64, %n64
  %p_row.ptr = getelementptr inbounds double, ptr %p, i64 %p_i_off
  store double 0.000000e+00, ptr %p_row.ptr, align 8

  ; q[i][0] = v[0][i]
  %v0i.val = load double, ptr %v0i.ptr, align 8
  %q_row.ptr = getelementptr inbounds double, ptr %q, i64 %p_i_off
  store double %v0i.val, ptr %q_row.ptr, align 8

  br label %for.j1

for.j1:
  %j1 = phi i32 [ 1, %for.i1 ], [ %inc.j1, %for.j1.body ]
  %cmp.j1 = icmp slt i32 %j1, %nm1
  br i1 %cmp.j1, label %for.j1.body, label %for.j1.end

for.j1.body:
  %j1_64 = sext i32 %j1 to i64
  %jm1_64 = add nsw i64 %j1_64, -1

  %p_row_i.ptr = getelementptr inbounds double, ptr %p_row.ptr, i64 %jm1_64
  %p_ijm1 = load double, ptr %p_row_i.ptr, align 8
  %t0 = fmul double %a, %p_ijm1
  %t1 = fadd double %t0, %b
  %div50 = fdiv double %fneg.c, %t1
  %p_ij.ptr = getelementptr inbounds double, ptr %p_row.ptr, i64 %j1_64
  store double %div50, ptr %p_ij.ptr, align 8

  %u_row_j.off = mul nsw i64 %j1_64, %n64
  %u_row_j.ptr = getelementptr inbounds double, ptr %u, i64 %u_row_j.off
  %im1_64 = add nsw i64 %i1_64, -1
  %u_j_im1.ptr = getelementptr inbounds double, ptr %u_row_j.ptr, i64 %im1_64
  %u_j_im1 = load double, ptr %u_j_im1.ptr, align 8
  %mul61 = fmul double %fneg.d, %u_j_im1

  %u_j_i.ptr = getelementptr inbounds double, ptr %u_row_j.ptr, i64 %i1_64
  %u_j_i = load double, ptr %u_j_i.ptr, align 8
  %mul68 = fmul double %add.d2, %u_j_i
  %add69 = fadd double %mul61, %mul68

  %ip1_64 = add nsw i64 %i1_64, 1
  %u_j_ip1.ptr = getelementptr inbounds double, ptr %u_row_j.ptr, i64 %ip1_64
  %u_j_ip1 = load double, ptr %u_j_ip1.ptr, align 8
  %mul75 = fmul double %f, %u_j_ip1
  %sub76 = fsub double %add69, %mul75

  %q_row_i.ptr = getelementptr inbounds double, ptr %q_row.ptr, i64 %jm1_64
  %q_ijm1 = load double, ptr %q_row_i.ptr, align 8
  %mul82 = fmul double %a, %q_ijm1
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %p_ijm1
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90
  %q_ij.ptr = getelementptr inbounds double, ptr %q_row.ptr, i64 %j1_64
  store double %div91, ptr %q_ij.ptr, align 8

  %inc.j1 = add nsw i32 %j1, 1
  br label %for.j1

for.j1.end:
  ; v[n-1][i] = 1.0
  %v_rowlast.off = mul nsw i64 %nm1_64, %n64
  %v_rowlast.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowlast.off
  %v_last_i.ptr = getelementptr inbounds double, ptr %v_rowlast.ptr, i64 %i1_64
  store double 1.000000e+00, ptr %v_last_i.ptr, align 8

  br label %for.j2

for.j2:
  %j2 = phi i32 [ %nm2, %for.j1.end ], [ %dec.j2, %for.j2.body ]
  %cmp.j2 = icmp sge i32 %j2, 1
  br i1 %cmp.j2, label %for.j2.body, label %for.end126

for.j2.body:
  %j2_64 = sext i32 %j2 to i64
  %p_ij2.ptr = getelementptr inbounds double, ptr %p_row.ptr, i64 %j2_64
  %p_ij2 = load double, ptr %p_ij2.ptr, align 8

  %jp1_64 = add nsw i64 %j2_64, 1
  %v_rowjp1.off = mul nsw i64 %jp1_64, %n64
  %v_rowjp1.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowjp1.off
  %v_jp1_i.ptr = getelementptr inbounds double, ptr %v_rowjp1.ptr, i64 %i1_64
  %v_jp1_i = load double, ptr %v_jp1_i.ptr, align 8

  %mul115 = fmul double %p_ij2, %v_jp1_i

  %q_ij2.ptr = getelementptr inbounds double, ptr %q_row.ptr, i64 %j2_64
  %q_ij2 = load double, ptr %q_ij2.ptr, align 8
  %add120 = fadd double %mul115, %q_ij2

  %v_rowj.off = mul nsw i64 %j2_64, %n64
  %v_rowj.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowj.off
  %v_j_i.ptr = getelementptr inbounds double, ptr %v_rowj.ptr, i64 %i1_64
  store double %add120, ptr %v_j_i.ptr, align 8

  %dec.j2 = add nsw i32 %j2, -1
  br label %for.j2

for.end126:
  %inc128 = add nsw i32 %i1, 1
  %cmp23.next = icmp slt i32 %inc128, %nm1
  br i1 %cmp23.next, label %for.i1, label %for.i2.pre

for.i2.pre:
  br label %for.i2

for.i2:
  %i2 = phi i32 [ 1, %for.i2.pre ], [ %inc242, %for.end240 ]
  %i2_64 = sext i32 %i2 to i64

  ; u[i][0] = 1.0
  %u_row_i2.off = mul nsw i64 %i2_64, %n64
  %u_row_i2.ptr = getelementptr inbounds double, ptr %u, i64 %u_row_i2.off
  store double 1.000000e+00, ptr %u_row_i2.ptr, align 8

  ; p[i][0] = 0.0
  %p_row_i2.off = mul nsw i64 %i2_64, %n64
  %p_row_i2.ptr = getelementptr inbounds double, ptr %p, i64 %p_row_i2.off
  store double 0.000000e+00, ptr %p_row_i2.ptr, align 8

  ; q[i][0] = u[i][0]
  %u_row_i2.val = load double, ptr %u_row_i2.ptr, align 8
  %q_row_i2.ptr = getelementptr inbounds double, ptr %q, i64 %p_row_i2.off
  store double %u_row_i2.val, ptr %q_row_i2.ptr, align 8

  br label %for.j3

for.j3:
  %j3 = phi i32 [ 1, %for.i2 ], [ %inc.j3, %for.j3.body ]
  %cmp.j3 = icmp slt i32 %j3, %nm1
  br i1 %cmp.j3, label %for.j3.body, label %for.j3.end

for.j3.body:
  %j3_64 = sext i32 %j3 to i64
  %jm1_3_64 = add nsw i64 %j3_64, -1

  %p_row_i2_jm1.ptr = getelementptr inbounds double, ptr %p_row_i2.ptr, i64 %jm1_3_64
  %p_i2_jm1 = load double, ptr %p_row_i2_jm1.ptr, align 8
  %t2 = fmul double %d, %p_i2_jm1
  %t3 = fadd double %t2, %e
  %div160 = fdiv double %fneg.f, %t3
  %p_i2_j.ptr = getelementptr inbounds double, ptr %p_row_i2.ptr, i64 %j3_64
  store double %div160, ptr %p_i2_j.ptr, align 8

  %im1_3_64 = add nsw i64 %i2_64, -1
  %v_rowim1.off = mul nsw i64 %im1_3_64, %n64
  %v_rowim1.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowim1.off
  %v_im1_j.ptr = getelementptr inbounds double, ptr %v_rowim1.ptr, i64 %j3_64
  %v_im1_j = load double, ptr %v_im1_j.ptr, align 8
  %mul171 = fmul double %fneg.a, %v_im1_j

  %v_rowi.off = mul nsw i64 %i2_64, %n64
  %v_rowi.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowi.off
  %v_i_j.ptr = getelementptr inbounds double, ptr %v_rowi.ptr, i64 %j3_64
  %v_i_j = load double, ptr %v_i_j.ptr, align 8
  %mul178 = fmul double %add.a2, %v_i_j
  %add179 = fadd double %mul171, %mul178

  %ip1_3_64 = add nsw i64 %i2_64, 1
  %v_rowip1.off = mul nsw i64 %ip1_3_64, %n64
  %v_rowip1.ptr = getelementptr inbounds double, ptr %v, i64 %v_rowip1.off
  %v_ip1_j.ptr = getelementptr inbounds double, ptr %v_rowip1.ptr, i64 %j3_64
  %v_ip1_j = load double, ptr %v_ip1_j.ptr, align 8
  %mul185 = fmul double %c, %v_ip1_j
  %sub186 = fsub double %add179, %mul185

  %q_row_i2_jm1.ptr = getelementptr inbounds double, ptr %q_row_i2.ptr, i64 %jm1_3_64
  %q_i2_jm1 = load double, ptr %q_row_i2_jm1.ptr, align 8
  %mul192 = fmul double %d, %q_i2_jm1
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %p_i2_jm1
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200
  %q_i2_j.ptr = getelementptr inbounds double, ptr %q_row_i2.ptr, i64 %j3_64
  store double %div201, ptr %q_i2_j.ptr, align 8

  %inc.j3 = add nsw i32 %j3, 1
  br label %for.j3

for.j3.end:
  ; u[i][n-1] = 1.0
  %u_row_i2_last.ptr = getelementptr inbounds double, ptr %u_row_i2.ptr, i64 %nm1_64
  store double 1.000000e+00, ptr %u_row_i2_last.ptr, align 8

  br label %for.j4

for.j4:
  %j4 = phi i32 [ %nm2, %for.j3.end ], [ %dec.j4, %for.j4.body ]
  %cmp.j4 = icmp sge i32 %j4, 1
  br i1 %cmp.j4, label %for.j4.body, label %for.end240

for.j4.body:
  %j4_64 = sext i32 %j4 to i64
  %p_i2_j4.ptr = getelementptr inbounds double, ptr %p_row_i2.ptr, i64 %j4_64
  %p_i2_j4 = load double, ptr %p_i2_j4.ptr, align 8

  %jp1_4_64 = add nsw i64 %j4_64, 1
  %u_row_i2_jp1.ptr = getelementptr inbounds double, ptr %u_row_i2.ptr, i64 %jp1_4_64
  %u_i2_jp1 = load double, ptr %u_row_i2_jp1.ptr, align 8

  %mul228 = fmul double %p_i2_j4, %u_i2_jp1

  %q_i2_j4.ptr = getelementptr inbounds double, ptr %q_row_i2.ptr, i64 %j4_64
  %q_i2_j4 = load double, ptr %q_i2_j4.ptr, align 8
  %add233 = fadd double %mul228, %q_i2_j4

  %u_row_i2_j4.ptr = getelementptr inbounds double, ptr %u_row_i2.ptr, i64 %j4_64
  store double %add233, ptr %u_row_i2_j4.ptr, align 8

  %dec.j4 = add nsw i32 %j4, -1
  br label %for.j4

for.end240:
  %inc242 = add nsw i32 %i2, 1
  %cmp130.next = icmp slt i32 %inc242, %nm1
  br i1 %cmp130.next, label %for.i2, label %for.inc244

for.inc244:
  %inc245 = add nsw i32 %t, 1
  %cmp.t.next = icmp sle i32 %inc245, %tsteps
  br i1 %cmp.t.next, label %for.t, label %for.end246

for.end246:
  ret void
}

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
