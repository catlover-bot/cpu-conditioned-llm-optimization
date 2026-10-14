; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %tsteps, 0
  %cmp.n2 = icmp sgt i32 n, 0
  ; Preserve original semantics precisely: fall back to straightforward
  ; but efficient scalar loop nest, avoiding redundant loads/stores by
  ; using SSA values instead of alloca round-tripping, while preserving
  ; exact floating point operation order.

  %n64 = sext i32 %n to i64
  %tsteps64 = sext i32 %tsteps to i64

  %nf = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %nf
  %DY = fdiv double 1.000000e+00, %nf
  %tstepsf = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %tstepsf

  %mul1.num = fmul double 2.000000e+00, %DT
  %mul1.den = fmul double %DX, %DX
  %mul1 = fdiv double %mul1.num, %mul1.den

  %mul2.num = fmul double 1.000000e+00, %DT
  %mul2.den = fmul double %DY, %DY
  %mul2 = fdiv double %mul2.num, %mul2.den

  %a.neg = fneg double %mul1
  %a = fdiv double %a.neg, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fdiv double %a.neg, 2.000000e+00
  %d.neg = fneg double %mul2
  %d = fdiv double %d.neg, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fdiv double %d.neg, 2.000000e+00

  br label %tloop.check

tloop.check:
  %t = phi i64 [1, %entry], [%t.next, %tloop.latch]
  %tcmp = icmp sle i64 %t, %tsteps64
  br i1 %tcmp, label %iloop.preheader, label %exit

iloop.preheader:
  br label %iloop.check

iloop.check:
  %i = phi i64 [1, %tloop.check], [%i.next, %iloop.latch]
  %nm1 = sub nsw i64 %n64, 1
  %icmp1 = icmp slt i64 %i, %nm1
  br i1 %icmp1, label %iloop.body, label %iloop.done

iloop.body:
  ; v[0][i] = 1.0
  %v_row0 = getelementptr inbounds double, ptr %v, i64 0
  %v0i = getelementptr inbounds double, ptr %v_row0, i64 %i
  store double 1.000000e+00, ptr %v0i, align 8

  ; p[i][0] = 0.0
  %p_rowi = getelementptr inbounds double, ptr %p, i64 %i, ! ""
  br label %skip_placeholder
skip_placeholder:
  %p_row_off = mul nsw i64 %i, %n64
  %p_row = getelementptr inbounds double, ptr %p, i64 %p_row_off
  store double 0.000000e+00, ptr %p_row, align 8

  ; q[i][0] = v[0][i]
  %v0i_load = load double, ptr %v0i, align 8
  %q_row_off = mul nsw i64 %i, %n64
  %q_row = getelementptr inbounds double, ptr %q, i64 %q_row_off
  store double %v0i_load, ptr %q_row, align 8

  br label %jloop1.check

jloop1.check:
  %j1 = phi i64 [1, %iloop.body], [%j1.next, %jloop1.latch]
  %nm1_j1 = sub nsw i64 %n64, 1
  %jcmp1 = icmp slt i64 %j1, %nm1_j1
  br i1 %jcmp1, label %jloop1.body, label %jloop1.done

jloop1.body:
  ; p[i][j] = -c / (a*p[i][j-1]+b)
  %jm1_1 = sub nsw i64 %j1, 1
  %p_arr_1 = getelementptr inbounds double, ptr %p, i64 %p_row_off
  %p_jm1_ptr = getelementptr inbounds double, ptr %p_arr_1, i64 %jm1_1
  %p_jm1 = load double, ptr %p_jm1_ptr, align 8
  %amulp = fmul double %a, %p_jm1
  %denom1 = fadd double %amulp, %b
  %cneg = fneg double %c
  %pij_val = fdiv double %cneg, %denom1
  %p_j_ptr = getelementptr inbounds double, ptr %p_arr_1, i64 %j1
  store double %pij_val, ptr %p_j_ptr, align 8

  ; q[i][j] = (-d*u[j][i-1] + (1+2*d)*u[j][i] - f*u[j][i+1] - a*q[i][j-1]) / (a*p[i][j-1] + b)
  %dneg = fneg double %d
  %u_row_j = mul nsw i64 %j1, %n64
  %u_row_j_ptr = getelementptr inbounds double, ptr %u, i64 %u_row_j
  %im1 = sub nsw i64 %i, 1
  %u_jim1_ptr = getelementptr inbounds double, ptr %u_row_j_ptr, i64 %im1
  %u_jim1 = load double, ptr %u_jim1_ptr, align 8
  %t1 = fmul double %dneg, %u_jim1

  %d2 = fmul double 2.000000e+00, %d
  %one_p_2d = fadd double 1.000000e+00, %d2
  %u_ji_ptr = getelementptr inbounds double, ptr %u_row_j_ptr, i64 %i
  %u_ji = load double, ptr %u_ji_ptr, align 8
  %t2 = fmul double %one_p_2d, %u_ji
  %sum12 = fadd double %t1, %t2

  %ip1 = add nsw i64 %i, 1
  %u_jip1_ptr = getelementptr inbounds double, ptr %u_row_j_ptr, i64 %ip1
  %u_jip1 = load double, ptr %u_jip1_ptr, align 8
  %t3 = fmul double %f, %u_jip1
  %sub_rhs = fsub double %sum12, %t3

  %q_arr_1 = getelementptr inbounds double, ptr %q, i64 %q_row_off
  %q_jm1_ptr = getelementptr inbounds double, ptr %q_arr_1, i64 %jm1_1
  %q_jm1 = load double, ptr %q_jm1_ptr, align 8
  %t4 = fmul double %a, %q_jm1
  %sub_rhs2 = fsub double %sub_rhs, %t4

  %denom2 = fadd double %amulp, %b
  %qij_val = fdiv double %sub_rhs2, %denom2
  %q_j_ptr = getelementptr inbounds double, ptr %q_arr_1, i64 %j1
  store double %qij_val, ptr %q_j_ptr, align 8

  br label %jloop1.latch

jloop1.latch:
  %j1.next = add nsw i64 %j1, 1
  br label %jloop1.check

jloop1.done:
  ; v[n-1][i] = 1.0
  %nm1_row = sub nsw i64 %n64, 1
  %v_row_last_off = mul nsw i64 %nm1_row, %n64
  %v_row_last = getelementptr inbounds double, ptr %v, i64 %v_row_last_off
  %v_last_i = getelementptr inbounds double, ptr %v_row_last, i64 %i
  store double 1.000000e+00, ptr %v_last_i, align 8

  %jstart = sub nsw i64 %n64, 2
  br label %jloop2.check

jloop2.check:
  %j2 = phi i64 [%jstart, %jloop1.done], [%j2.next, %jloop2.latch]
  %jcmp2 = icmp sge i64 %j2, 1
  br i1 %jcmp2, label %jloop2.body, label %jloop2.done

jloop2.body:
  %p_arr_2 = getelementptr inbounds double, ptr %p, i64 %p_row_off
  %p_j2_ptr = getelementptr inbounds double, ptr %p_arr_2, i64 %j2
  %p_j2 = load double, ptr %p_j2_ptr, align 8

  %jp1 = add nsw i64 %j2, 1
  %v_row_jp1_off = mul nsw i64 %jp1, %n64
  %v_row_jp1 = getelementptr inbounds double, ptr %v, i64 %v_row_jp1_off
  %v_jp1_i = getelementptr inbounds double, ptr %v_row_jp1, i64 %i
  %v_jp1_i_val = load double, ptr %v_jp1_i, align 8

  %mul_pv = fmul double %p_j2, %v_jp1_i_val

  %q_arr_2 = getelementptr inbounds double, ptr %q, i64 %q_row_off
  %q_j2_ptr = getelementptr inbounds double, ptr %q_arr_2, i64 %j2
  %q_j2 = load double, ptr %q_j2_ptr, align 8

  %vij_val = fadd double %mul_pv, %q_j2

  %v_row_j2_off = mul nsw i64 %j2, %n64
  %v_row_j2 = getelementptr inbounds double, ptr %v, i64 %v_row_j2_off
  %v_j2_i = getelementptr inbounds double, ptr %v_row_j2, i64 %i
  store double %vij_val, ptr %v_j2_i, align 8

  br label %jloop2.latch

jloop2.latch:
  %j2.next = add nsw i64 %j2, -1
  br label %jloop2.check

jloop2.done:
  br label %iloop.latch

iloop.latch:
  %i.next = add nsw i64 %i, 1
  br label %iloop.check

iloop.done:
  br label %iloop2.preheader

iloop2.preheader:
  br label %iloop2.check

iloop2.check:
  %i2 = phi i64 [1, %iloop.done], [%i2.next, %iloop2.latch]
  %nm1_2 = sub nsw i64 %n64, 1
  %icmp2 = icmp slt i64 %i2, %nm1_2
  br i1 %icmp2, label %iloop2.body, label %iloop2.done

iloop2.body:
  ; u[i][0] = 1.0
  %u_row_i2_off = mul nsw i64 %i2, %n64
  %u_row_i2 = getelementptr inbounds double, ptr %u, i64 %u_row_i2_off
  store double 1.000000e+00, ptr %u_row_i2, align 8

  ; p[i][0] = 0.0
  %p_row_i2_off = mul nsw i64 %i2, %n64
  %p_row_i2 = getelementptr inbounds double, ptr %p, i64 %p_row_i2_off
  store double 0.000000e+00, ptr %p_row_i2, align 8

  ; q[i][0] = u[i][0]
  %u_i2_0 = load double, ptr %u_row_i2, align 8
  %q_row_i2_off = mul nsw i64 %i2, %n64
  %q_row_i2 = getelementptr inbounds double, ptr %q, i64 %q_row_i2_off
  store double %u_i2_0, ptr %q_row_i2, align 8

  br label %jloop3.check

jloop3.check:
  %j3 = phi i64 [1, %iloop2.body], [%j3.next, %jloop3.latch]
  %nm1_j3 = sub nsw i64 %n64, 1
  %jcmp3 = icmp slt i64 %j3, %nm1_j3
  br i1 %jcmp3, label %jloop3.body, label %jloop3.done

jloop3.body:
  ; p[i][j] = -f / (d*p[i][j-1]+e)
  %jm1_3 = sub nsw i64 %j3, 1
  %p_arr_3 = getelementptr inbounds double, ptr %p, i64 %p_row_i2_off
  %p_jm1_3_ptr = getelementptr inbounds double, ptr %p_arr_3, i64 %jm1_3
  %p_jm1_3 = load double, ptr %p_jm1_3_ptr, align 8
  %dmulp = fmul double %d, %p_jm1_3
  %denom3 = fadd double %dmulp, %e
  %fneg = fneg double %f
  %pij3_val = fdiv double %fneg, %denom3
  %p_j3_ptr = getelementptr inbounds double, ptr %p_arr_3, i64 %j3
  store double %pij3_val, ptr %p_j3_ptr, align 8

  ; q[i][j] = (-a*v[i-1][j] + (1+2a)*v[i][j] - c*v[i+1][j] - d*q[i][j-1]) / (d*p[i][j-1]+e)
  %aneg = fneg double %a
  %im1_2 = sub nsw i64 %i2, 1
  %v_row_im1_off = mul nsw i64 %im1_2, %n64
  %v_row_im1 = getelementptr inbounds double, ptr %v, i64 %v_row_im1_off
  %v_im1_j = getelementptr inbounds double, ptr %v_row_im1, i64 %j3
  %v_im1_j_val = load double, ptr %v_im1_j, align 8
  %s1 = fmul double %aneg, %v_im1_j_val

  %a2 = fmul double 2.000000e+00, %a
  %one_p_2a = fadd double 1.000000e+00, %a2
  %v_row_i2_off_ = mul nsw i64 %i2, %n64
  %v_row_i2_ = getelementptr inbounds double, ptr %v, i64 %v_row_i2_off_
  %v_i2_j = getelementptr inbounds double, ptr %v_row_i2_, i64 %j3
  %v_i2_j_val = load double, ptr %v_i2_j, align 8
  %s2 = fmul double %one_p_2a, %v_i2_j_val
  %sum_s = fadd double %s1, %s2

  %ip1_2 = add nsw i64 %i2, 1
  %v_row_ip1_off = mul nsw i64 %ip1_2, %n64
  %v_row_ip1 = getelementptr inbounds double, ptr %v, i64 %v_row_ip1_off
  %v_ip1_j = getelementptr inbounds double, ptr %v_row_ip1, i64 %j3
  %v_ip1_j_val = load double, ptr %v_ip1_j, align 8
  %s3 = fmul double %c, %v_ip1_j_val
  %sub_s = fsub double %sum_s, %s3

  %q_arr_3 = getelementptr inbounds double, ptr %q, i64 %q_row_i2_off
  %q_jm1_3_ptr = getelementptr inbounds double, ptr %q_arr_3, i64 %jm1_3
  %q_jm1_3 = load double, ptr %q_jm1_3_ptr, align 8
  %s4 = fmul double %d, %q_jm1_3
  %sub_s2 = fsub double %sub_s, %s4

  %denom4 = fadd double %dmulp, %e
  %qij3_val = fdiv double %sub_s2, %denom4
  %q_j3_ptr = getelementptr inbounds double, ptr %q_arr_3, i64 %j3
  store double %qij3_val, ptr %q_j3_ptr, align 8

  br label %jloop3.latch

jloop3.latch:
  %j3.next = add nsw i64 %j3, 1
  br label %jloop3.check

jloop3.done:
  ; u[i][n-1] = 1.0
  %nm1_col = sub nsw i64 %n64, 1
  %u_row_i2_off2 = mul nsw i64 %i2, %n64
  %u_row_i2_2 = getelementptr inbounds double, ptr %u, i64 %u_row_i2_off2
  %u_last = getelementptr inbounds double, ptr %u_row_i2_2, i64 %nm1_col
  store double 1.000000e+00, ptr %u_last, align 8

  %jstart2 = sub nsw i64 %n64, 2
  br label %jloop4.check

jloop4.check:
  %j4 = phi i64 [%jstart2, %jloop3.done], [%j4.next, %jloop4.latch]
  %jcmp4 = icmp sge i64 %j4, 1
  br i1 %jcmp4, label %jloop4.body, label %jloop4.done

jloop4.body:
  %p_arr_4 = getelementptr inbounds double, ptr %p, i64 %p_row_i2_off
  %p_j4_ptr = getelementptr inbounds double, ptr %p_arr_4, i64 %j4
  %p_j4 = load double, ptr %p_j4_ptr, align 8

  %jp1_2 = add nsw i64 %j4, 1
  %u_row_i2_off3 = mul nsw i64 %i2, %n64
  %u_row_i2_3 = getelementptr inbounds double, ptr %u, i64 %u_row_i2_off3
  %u_jp1_ptr = getelementptr inbounds double, ptr %u_row_i2_3, i64 %jp1_2
  %u_jp1_val = load double, ptr %u_jp1_ptr, align 8

  %mul_pu = fmul double %p_j4, %u_jp1_val

  %q_arr_4 = getelementptr inbounds double, ptr %q, i64 %q_row_i2_off
  %q_j4_ptr = getelementptr inbounds double, ptr %q_arr_4, i64 %j4
  %q_j4 = load double, ptr %q_j4_ptr, align 8

  %uij_val = fadd double %mul_pu, %q_j4

  %u_row_i2_off4 = mul nsw i64 %i2, %n64
  %u_row_i2_4 = getelementptr inbounds double, ptr %u, i64 %u_row_i2_off4
  %u_j4_ptr = getelementptr inbounds double, ptr %u_row_i2_4, i64 %j4
  store double %uij_val, ptr %u_j4_ptr, align 8

  br label %jloop4.latch

jloop4.latch:
  %j4.next = add nsw i64 %j4, -1
  br label %jloop4.check

jloop4.done:
  br label %iloop2.latch

iloop2.latch:
  %i2.next = add nsw i64 %i2, 1
  br label %iloop2.check

iloop2.done:
  br label %tloop.latch

tloop.latch:
  %t.next = add nsw i64 %t, 1
  br label %tloop.check

exit:
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
