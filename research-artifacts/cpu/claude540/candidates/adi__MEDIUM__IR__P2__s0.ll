; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  br i1 %cmp.n, label %check.tsteps, label %for.end246.early

check.tsteps:
  %cmp.t0 = icmp sge i32 %tsteps, 1
  br i1 %cmp.t0, label %preheader, label %for.end246.early

for.end246.early:
  ret void

preheader:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm2 = sub nsw i32 %n, 2

  %convn = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %convn
  %DY = fdiv double 1.000000e+00, %convn
  %convt = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %convt

  %mul1.num = fmul double 2.000000e+00, %DT
  %DXDX = fmul double %DX, %DX
  %mul1 = fdiv double %mul1.num, %DXDX
  %mul2.num = fmul double 1.000000e+00, %DT
  %DYDY = fmul double %DY, %DY
  %mul2 = fdiv double %mul2.num, %DYDY

  %a.neg = fneg double %mul1
  %a = fdiv double %a.neg, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fadd double 0.000000e+00, %a
  %d.neg = fneg double %mul2
  %d = fdiv double %d.neg, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fadd double 0.000000e+00, %d

  br label %for.cond

for.cond:                                         ; preds = %for.inc244, %preheader
  %t = phi i32 [ 1, %preheader ], [ %inc245, %for.inc244 ]
  %cmp = icmp sle i32 %t, %tsteps
  br i1 %cmp, label %for.body, label %for.end246

for.body:                                         ; preds = %for.cond
  br label %for.cond23

for.cond23:                                       ; preds = %for.inc127, %for.body
  %i = phi i32 [ 1, %for.body ], [ %inc128, %for.inc127 ]
  %cmp24 = icmp slt i32 %i, %nm1
  br i1 %cmp24, label %for.body26, label %for.end129

for.body26:                                       ; preds = %for.cond23
  %i64 = sext i32 %i to i64
  ; v[0][i] = 1.0
  %v_row0 = getelementptr inbounds double, ptr %v, i64 0
  %v0i = getelementptr inbounds double, ptr %v_row0, i64 %i64
  store double 1.000000e+00, ptr %v0i, align 8

  ; p[i][0] = 0.0
  %p_rowi = getelementptr inbounds double, ptr %p, i64 %i64
  %p_rowi_off = mul nsw i64 %i64, %n64
  %p_rowi_base = getelementptr inbounds double, ptr %p, i64 %p_rowi_off
  store double 0.000000e+00, ptr %p_rowi_base, align 8

  ; q[i][0] = v[0][i]
  %v0i_val = load double, ptr %v0i, align 8
  %q_rowi_base = getelementptr inbounds double, ptr %q, i64 %p_rowi_off
  store double %v0i_val, ptr %q_rowi_base, align 8

  br label %for.cond37

for.cond37:                                       ; preds = %for.inc, %for.body26
  %j = phi i32 [ 1, %for.body26 ], [ %inc, %for.inc ]
  %cmp39 = icmp slt i32 %j, %nm1
  br i1 %cmp39, label %for.body41, label %for.end

for.body41:                                       ; preds = %for.cond37
  %j64 = sext i32 %j to i64
  %jm1_64 = sub nsw i64 %j64, 1
  %jp1 = add nsw i32 %j, 1
  %jp1_64 = sext i32 %jp1 to i64

  ; p[i][j-1]
  %p_i_jm1 = getelementptr inbounds double, ptr %p_rowi_base, i64 %jm1_64
  %p_i_jm1_val = load double, ptr %p_i_jm1, align 8

  %fneg42 = fneg double %c
  %mul48 = fmul double %a, %p_i_jm1_val
  %add49 = fadd double %mul48, %b
  %div50 = fdiv double %fneg42, %add49
  %p_i_j = getelementptr inbounds double, ptr %p_rowi_base, i64 %j64
  store double %div50, ptr %p_i_j, align 8

  ; u[j][i-1], u[j][i], u[j][i+1]
  %u_rowj_off = mul nsw i64 %j64, %n64
  %u_rowj_base = getelementptr inbounds double, ptr %u, i64 %u_rowj_off
  %im1 = sub nsw i32 %i, 1
  %im1_64 = sext i32 %im1 to i64
  %u_j_im1 = getelementptr inbounds double, ptr %u_rowj_base, i64 %im1_64
  %u_j_im1_val = load double, ptr %u_j_im1, align 8

  %fneg55 = fneg double %d
  %mul61 = fmul double %fneg55, %u_j_im1_val

  %mul62 = fmul double 2.000000e+00, %d
  %add63 = fadd double 1.000000e+00, %mul62

  %u_j_i = getelementptr inbounds double, ptr %u_rowj_base, i64 %i64
  %u_j_i_val = load double, ptr %u_j_i, align 8
  %mul68 = fmul double %add63, %u_j_i_val
  %add69 = fadd double %mul61, %mul68

  %ip1 = add nsw i32 %i, 1
  %ip1_64 = sext i32 %ip1 to i64
  %u_j_ip1 = getelementptr inbounds double, ptr %u_rowj_base, i64 %ip1_64
  %u_j_ip1_val = load double, ptr %u_j_ip1, align 8
  %mul75 = fmul double %f, %u_j_ip1_val
  %sub76 = fsub double %add69, %mul75

  ; q[i][j-1]
  %q_i_jm1 = getelementptr inbounds double, ptr %q_rowi_base, i64 %jm1_64
  %q_i_jm1_val = load double, ptr %q_i_jm1, align 8
  %mul82 = fmul double %a, %q_i_jm1_val
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %p_i_jm1_val
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90

  %q_i_j = getelementptr inbounds double, ptr %q_rowi_base, i64 %j64
  store double %div91, ptr %q_i_j, align 8

  br label %for.inc

for.inc:                                          ; preds = %for.body41
  %inc = add nsw i32 %j, 1
  br label %for.cond37, !llvm.loop !6

for.end:                                          ; preds = %for.cond37
  ; v[n-1][i] = 1.0
  %nm1_64 = sext i32 %nm1 to i64
  %v_rown1_off = mul nsw i64 %nm1_64, %n64
  %v_rown1_base = getelementptr inbounds double, ptr %v, i64 %v_rown1_off
  %v_n1_i = getelementptr inbounds double, ptr %v_rown1_base, i64 %i64
  store double 1.000000e+00, ptr %v_n1_i, align 8

  br label %for.cond102

for.cond102:                                      ; preds = %for.inc125, %for.end
  %j2 = phi i32 [ %nm2, %for.end ], [ %dec, %for.inc125 ]
  %cmp103 = icmp sge i32 %j2, 1
  br i1 %cmp103, label %for.body105, label %for.end126

for.body105:                                      ; preds = %for.cond102
  %j2_64 = sext i32 %j2 to i64

  %p_i_j2 = getelementptr inbounds double, ptr %p_rowi_base, i64 %j2_64
  %p_i_j2_val = load double, ptr %p_i_j2, align 8

  %j2p1 = add nsw i32 %j2, 1
  %j2p1_64 = sext i32 %j2p1 to i64
  %v_rowj2p1_off = mul nsw i64 %j2p1_64, %n64
  %v_rowj2p1_base = getelementptr inbounds double, ptr %v, i64 %v_rowj2p1_off
  %v_j2p1_i = getelementptr inbounds double, ptr %v_rowj2p1_base, i64 %i64
  %v_j2p1_i_val = load double, ptr %v_j2p1_i, align 8

  %mul115 = fmul double %p_i_j2_val, %v_j2p1_i_val

  %q_i_j2 = getelementptr inbounds double, ptr %q_rowi_base, i64 %j2_64
  %q_i_j2_val = load double, ptr %q_i_j2, align 8

  %add120 = fadd double %mul115, %q_i_j2_val

  %v_rowj2_off = mul nsw i64 %j2_64, %n64
  %v_rowj2_base = getelementptr inbounds double, ptr %v, i64 %v_rowj2_off
  %v_j2_i = getelementptr inbounds double, ptr %v_rowj2_base, i64 %i64
  store double %add120, ptr %v_j2_i, align 8

  br label %for.inc125

for.inc125:                                       ; preds = %for.body105
  %dec = add nsw i32 %j2, -1
  br label %for.cond102, !llvm.loop !8

for.end126:                                       ; preds = %for.cond102
  br label %for.inc127

for.inc127:                                       ; preds = %for.end126
  %inc128 = add nsw i32 %i, 1
  br label %for.cond23, !llvm.loop !9

for.end129:                                       ; preds = %for.cond23
  br label %for.cond130

for.cond130:                                      ; preds = %for.inc241, %for.end129
  %i2 = phi i32 [ 1, %for.end129 ], [ %inc242, %for.inc241 ]
  %cmp132 = icmp slt i32 %i2, %nm1
  br i1 %cmp132, label %for.body134, label %for.end243

for.body134:                                      ; preds = %for.cond130
  %i2_64 = sext i32 %i2 to i64

  ; u[i][0] = 1.0
  %u_rowi2_off = mul nsw i64 %i2_64, %n64
  %u_rowi2_base = getelementptr inbounds double, ptr %u, i64 %u_rowi2_off
  store double 1.000000e+00, ptr %u_rowi2_base, align 8

  ; p[i][0] = 0.0
  %p_rowi2_off = mul nsw i64 %i2_64, %n64
  %p_rowi2_base = getelementptr inbounds double, ptr %p, i64 %p_rowi2_off
  store double 0.000000e+00, ptr %p_rowi2_base, align 8

  ; q[i][0] = u[i][0]
  %u_i2_0_val = load double, ptr %u_rowi2_base, align 8
  %q_rowi2_base = getelementptr inbounds double, ptr %q, i64 %p_rowi2_off
  store double %u_i2_0_val, ptr %q_rowi2_base, align 8

  br label %for.cond147

for.cond147:                                      ; preds = %for.inc206, %for.body134
  %j3 = phi i32 [ 1, %for.body134 ], [ %inc207, %for.inc206 ]
  %cmp149 = icmp slt i32 %j3, %nm1
  br i1 %cmp149, label %for.body151, label %for.end208

for.body151:                                      ; preds = %for.cond147
  %j3_64 = sext i32 %j3 to i64
  %j3m1_64 = sub nsw i64 %j3_64, 1

  %p_i2_j3m1 = getelementptr inbounds double, ptr %p_rowi2_base, i64 %j3m1_64
  %p_i2_j3m1_val = load double, ptr %p_i2_j3m1, align 8

  %fneg152 = fneg double %f
  %mul158 = fmul double %d, %p_i2_j3m1_val
  %add159 = fadd double %mul158, %e
  %div160 = fdiv double %fneg152, %add159

  %p_i2_j3 = getelementptr inbounds double, ptr %p_rowi2_base, i64 %j3_64
  store double %div160, ptr %p_i2_j3, align 8

  %i2m1 = sub nsw i32 %i2, 1
  %i2m1_64 = sext i32 %i2m1 to i64
  %v_rowi2m1_off = mul nsw i64 %i2m1_64, %n64
  %v_rowi2m1_base = getelementptr inbounds double, ptr %v, i64 %v_rowi2m1_off
  %v_i2m1_j3 = getelementptr inbounds double, ptr %v_rowi2m1_base, i64 %j3_64
  %v_i2m1_j3_val = load double, ptr %v_i2m1_j3, align 8

  %fneg165 = fneg double %a
  %mul171 = fmul double %fneg165, %v_i2m1_j3_val

  %mul172 = fmul double 2.000000e+00, %a
  %add173 = fadd double 1.000000e+00, %mul172

  %v_rowi2_off = mul nsw i64 %i2_64, %n64
  %v_rowi2_base = getelementptr inbounds double, ptr %v, i64 %v_rowi2_off
  %v_i2_j3 = getelementptr inbounds double, ptr %v_rowi2_base, i64 %j3_64
  %v_i2_j3_val = load double, ptr %v_i2_j3, align 8
  %mul178 = fmul double %add173, %v_i2_j3_val
  %add179 = fadd double %mul171, %mul178

  %i2p1 = add nsw i32 %i2, 1
  %i2p1_64 = sext i32 %i2p1 to i64
  %v_rowi2p1_off = mul nsw i64 %i2p1_64, %n64
  %v_rowi2p1_base = getelementptr inbounds double, ptr %v, i64 %v_rowi2p1_off
  %v_i2p1_j3 = getelementptr inbounds double, ptr %v_rowi2p1_base, i64 %j3_64
  %v_i2p1_j3_val = load double, ptr %v_i2p1_j3, align 8
  %mul185 = fmul double %c, %v_i2p1_j3_val
  %sub186 = fsub double %add179, %mul185

  %q_i2_j3m1 = getelementptr inbounds double, ptr %q_rowi2_base, i64 %j3m1_64
  %q_i2_j3m1_val = load double, ptr %q_i2_j3m1, align 8
  %mul192 = fmul double %d, %q_i2_j3m1_val
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %p_i2_j3m1_val
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200

  %q_i2_j3 = getelementptr inbounds double, ptr %q_rowi2_base, i64 %j3_64
  store double %div201, ptr %q_i2_j3, align 8

  br label %for.inc206

for.inc206:                                       ; preds = %for.body151
  %inc207 = add nsw i32 %j3, 1
  br label %for.cond147, !llvm.loop !10

for.end208:                                       ; preds = %for.cond147
  ; u[i][n-1] = 1.0
  %u_i2_n1 = getelementptr inbounds double, ptr %u_rowi2_base, i64 %nm1_64
  store double 1.000000e+00, ptr %u_i2_n1, align 8

  br label %for.cond215

for.cond215:                                      ; preds = %for.inc238, %for.end208
  %j4 = phi i32 [ %nm2, %for.end208 ], [ %dec239, %for.inc238 ]
  %cmp216 = icmp sge i32 %j4, 1
  br i1 %cmp216, label %for.body218, label %for.end240

for.body218:                                      ; preds = %for.cond215
  %j4_64 = sext i32 %j4 to i64

  %p_i2_j4 = getelementptr inbounds double, ptr %p_rowi2_base, i64 %j4_64
  %p_i2_j4_val = load double, ptr %p_i2_j4, align 8

  %j4p1 = add nsw i32 %j4, 1
  %j4p1_64 = sext i32 %j4p1 to i64
  %u_i2_j4p1 = getelementptr inbounds double, ptr %u_rowi2_base, i64 %j4p1_64
  %u_i2_j4p1_val = load double, ptr %u_i2_j4p1, align 8

  %mul228 = fmul double %p_i2_j4_val, %u_i2_j4p1_val

  %q_i2_j4 = getelementptr inbounds double, ptr %q_rowi2_base, i64 %j4_64
  %q_i2_j4_val = load double, ptr %q_i2_j4, align 8

  %add233 = fadd double %mul228, %q_i2_j4_val

  %u_i2_j4 = getelementptr inbounds double, ptr %u_rowi2_base, i64 %j4_64
  store double %add233, ptr %u_i2_j4, align 8

  br label %for.inc238

for.inc238:                                       ; preds = %for.body218
  %dec239 = add nsw i32 %j4, -1
  br label %for.cond215, !llvm.loop !11

for.end240:                                       ; preds = %for.cond215
  br label %for.inc241

for.inc241:                                       ; preds = %for.end240
  %inc242 = add nsw i32 %i2, 1
  br label %for.cond130, !llvm.loop !12

for.end243:                                       ; preds = %for.cond130
  br label %for.inc244

for.inc244:                                       ; preds = %for.end243
  %inc245 = add nsw i32 %t, 1
  br label %for.cond, !llvm.loop !13

for.end246:                                       ; preds = %for.cond
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
