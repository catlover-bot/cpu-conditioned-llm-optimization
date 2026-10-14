; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sle i32 %n, 2
  %cmp.t = icmp sle i32 %tsteps, 0
  %skip = or i1 %cmp.n, %cmp.t
  br i1 %skip, label %for.end217, label %preheader

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1.64 = sext i32 %nm1 to i64
  br label %for.cond

for.cond:
  %t = phi i32 [ 1, %preheader ], [ %inc216, %for.inc215 ]
  br label %for.body.i.outer

for.body.i.outer:
  %i = phi i64 [ 1, %for.cond ], [ %i.next, %for.inc104 ]
  %ip1 = add nsw i64 %i, 1
  %im1 = add nsw i64 %i, -1
  %i_base  = mul nsw i64 %i, %n64
  %i_base  = mul nsw i64 %i_base, %n64
  %ip1_base = mul nsw i64 %ip1, %n64
  %ip1_base2 = mul nsw i64 %ip1_base, %n64
  %im1_base = mul nsw i64 %im1, %n64
  %im1_base2 = mul nsw i64 %im1_base, %n64
  br label %for.body.j.outer

for.body.j.outer:
  %j = phi i64 [ 1, %for.body.i.outer ], [ %j.next, %for.inc101 ]
  %jp1 = add nsw i64 %j, 1
  %jm1 = add nsw i64 %j, -1
  %j_off  = mul nsw i64 %j, %n64
  %jp1_off = mul nsw i64 %jp1, %n64
  %jm1_off = mul nsw i64 %jm1, %n64
  %row_c  = add nsw i64 %i_base, %j_off
  %row_ip1 = add nsw i64 %ip1_base2, %j_off
  %row_im1 = add nsw i64 %im1_base2, %j_off
  %row_jp1 = add nsw i64 %i_base, %jp1_off
  %row_jm1 = add nsw i64 %i_base, %jm1_off
  %ptrA_c   = getelementptr inbounds double, ptr %A, i64 %row_c
  %ptrA_ip1 = getelementptr inbounds double, ptr %A, i64 %row_ip1
  %ptrA_im1 = getelementptr inbounds double, ptr %A, i64 %row_im1
  %ptrA_jp1 = getelementptr inbounds double, ptr %A, i64 %row_jp1
  %ptrA_jm1 = getelementptr inbounds double, ptr %A, i64 %row_jm1
  %ptrB_c   = getelementptr inbounds double, ptr %B, i64 %row_c
  br label %for.body.k

for.body.k:
  %k = phi i64 [ 1, %for.body.j.outer ], [ %k.next, %for.body.k ]
  %kp1 = add nsw i64 %k, 1
  %km1 = add nsw i64 %k, -1

  %a_ip1_c = getelementptr inbounds double, ptr %ptrA_ip1, i64 %k
  %v_ip1_c = load double, ptr %a_ip1_c, align 8
  %a_c_c = getelementptr inbounds double, ptr %ptrA_c, i64 %k
  %v_c_c = load double, ptr %a_c_c, align 8
  %mul_a = fmul double 2.000000e+00, %v_c_c
  %sub_a = fsub double %v_ip1_c, %mul_a
  %a_im1_c = getelementptr inbounds double, ptr %ptrA_im1, i64 %k
  %v_im1_c = load double, ptr %a_im1_c, align 8
  %add_a = fadd double %sub_a, %v_im1_c
  %term1 = fmul double 1.250000e-01, %add_a

  %a_c_jp1 = getelementptr inbounds double, ptr %ptrA_jp1, i64 %k
  %v_c_jp1 = load double, ptr %a_c_jp1, align 8
  %v_c_c2 = load double, ptr %a_c_c, align 8
  %mul_b = fmul double 2.000000e+00, %v_c_c2
  %sub_b = fsub double %v_c_jp1, %mul_b
  %a_c_jm1 = getelementptr inbounds double, ptr %ptrA_jm1, i64 %k
  %v_c_jm1 = load double, ptr %a_c_jm1, align 8
  %add_b = fadd double %sub_b, %v_c_jm1
  %term2 = fmul double 1.250000e-01, %add_b

  %sum12 = fadd double %term1, %term2

  %a_c_kp1 = getelementptr inbounds double, ptr %ptrA_c, i64 %kp1
  %v_c_kp1 = load double, ptr %a_c_kp1, align 8
  %v_c_c3 = load double, ptr %a_c_c, align 8
  %mul_c = fmul double 2.000000e+00, %v_c_c3
  %sub_c = fsub double %v_c_kp1, %mul_c
  %a_c_km1 = getelementptr inbounds double, ptr %ptrA_c, i64 %km1
  %v_c_km1 = load double, ptr %a_c_km1, align 8
  %add_c = fadd double %sub_c, %v_c_km1
  %term3 = fmul double 1.250000e-01, %add_c

  %sum123 = fadd double %sum12, %term3

  %v_c_c4 = load double, ptr %a_c_c, align 8
  %result = fadd double %sum123, %v_c_c4

  %b_out = getelementptr inbounds double, ptr %ptrB_c, i64 %k
  store double %result, ptr %b_out, align 8

  %k.next = add nsw i64 %k, 1
  %cmp.k = icmp slt i64 %k.next, %nm1.64
  br i1 %cmp.k, label %for.body.k, label %for.end.k, !llvm.loop !6

for.end.k:
  br label %for.inc101

for.inc101:
  %j.next = add nsw i64 %j, 1
  %cmp.j = icmp slt i64 %j.next, %nm1.64
  br i1 %cmp.j, label %for.body.j.outer, label %for.end103, !llvm.loop !8

for.end103:
  br label %for.inc104

for.inc104:
  %i.next = add nsw i64 %i, 1
  %cmp.i = icmp slt i64 %i.next, %nm1.64
  br i1 %cmp.i, label %for.body.i.outer, label %for.end106, !llvm.loop !9

for.end106:
  br label %for.body2.i.outer

for.body2.i.outer:
  %i2 = phi i64 [ 1, %for.end106 ], [ %i2.next, %for.inc212 ]
  %i2p1 = add nsw i64 %i2, 1
  %i2m1 = add nsw i64 %i2, -1
  %i2_base  = mul nsw i64 %i2, %n64
  %i2_base  = mul nsw i64 %i2_base, %n64
  %i2p1_base = mul nsw i64 %i2p1, %n64
  %i2p1_base2 = mul nsw i64 %i2p1_base, %n64
  %i2m1_base = mul nsw i64 %i2m1, %n64
  %i2m1_base2 = mul nsw i64 %i2m1_base, %n64
  br label %for.body2.j.outer

for.body2.j.outer:
  %j2 = phi i64 [ 1, %for.body2.i.outer ], [ %j2.next, %for.inc209 ]
  %j2p1 = add nsw i64 %j2, 1
  %j2m1 = add nsw i64 %j2, -1
  %j2_off  = mul nsw i64 %j2, %n64
  %j2p1_off = mul nsw i64 %j2p1, %n64
  %j2m1_off = mul nsw i64 %j2m1, %n64
  %row2_c  = add nsw i64 %i2_base, %j2_off
  %row2_ip1 = add nsw i64 %i2p1_base2, %j2_off
  %row2_im1 = add nsw i64 %i2m1_base2, %j2_off
  %row2_jp1 = add nsw i64 %i2_base, %j2p1_off
  %row2_jm1 = add nsw i64 %i2_base, %j2m1_off
  %ptrB2_c   = getelementptr inbounds double, ptr %B, i64 %row2_c
  %ptrB2_ip1 = getelementptr inbounds double, ptr %B, i64 %row2_ip1
  %ptrB2_im1 = getelementptr inbounds double, ptr %B, i64 %row2_im1
  %ptrB2_jp1 = getelementptr inbounds double, ptr %B, i64 %row2_jp1
  %ptrB2_jm1 = getelementptr inbounds double, ptr %B, i64 %row2_jm1
  %ptrA2_c   = getelementptr inbounds double, ptr %A, i64 %row2_c
  br label %for.body2.k

for.body2.k:
  %k2 = phi i64 [ 1, %for.body2.j.outer ], [ %k2.next, %for.body2.k ]
  %k2p1 = add nsw i64 %k2, 1
  %k2m1 = add nsw i64 %k2, -1

  %b_ip1_c = getelementptr inbounds double, ptr %ptrB2_ip1, i64 %k2
  %vb_ip1_c = load double, ptr %b_ip1_c, align 8
  %b_c_c = getelementptr inbounds double, ptr %ptrB2_c, i64 %k2
  %vb_c_c = load double, ptr %b_c_c, align 8
  %mul2_a = fmul double 2.000000e+00, %vb_c_c
  %sub2_a = fsub double %vb_ip1_c, %mul2_a
  %b_im1_c = getelementptr inbounds double, ptr %ptrB2_im1, i64 %k2
  %vb_im1_c = load double, ptr %b_im1_c, align 8
  %add2_a = fadd double %sub2_a, %vb_im1_c
  %term2_1 = fmul double 1.250000e-01, %add2_a

  %b_c_jp1 = getelementptr inbounds double, ptr %ptrB2_jp1, i64 %k2
  %vb_c_jp1 = load double, ptr %b_c_jp1, align 8
  %vb_c_c2 = load double, ptr %b_c_c, align 8
  %mul2_b = fmul double 2.000000e+00, %vb_c_c2
  %sub2_b = fsub double %vb_c_jp1, %mul2_b
  %b_c_jm1 = getelementptr inbounds double, ptr %ptrB2_jm1, i64 %k2
  %vb_c_jm1 = load double, ptr %b_c_jm1, align 8
  %add2_b = fadd double %sub2_b, %vb_c_jm1
  %term2_2 = fmul double 1.250000e-01, %add2_b

  %sum2_12 = fadd double %term2_1, %term2_2

  %b_c_kp1 = getelementptr inbounds double, ptr %ptrB2_c, i64 %k2p1
  %vb_c_kp1 = load double, ptr %b_c_kp1, align 8
  %vb_c_c3 = load double, ptr %b_c_c, align 8
  %mul2_c = fmul double 2.000000e+00, %vb_c_c3
  %sub2_c = fsub double %vb_c_kp1, %mul2_c
  %b_c_km1 = getelementptr inbounds double, ptr %ptrB2_c, i64 %k2m1
  %vb_c_km1 = load double, ptr %b_c_km1, align 8
  %add2_c = fadd double %sub2_c, %vb_c_km1
  %term2_3 = fmul double 1.250000e-01, %add2_c

  %sum2_123 = fadd double %sum2_12, %term2_3

  %vb_c_c4 = load double, ptr %b_c_c, align 8
  %result2 = fadd double %sum2_123, %vb_c_c4

  %a_out = getelementptr inbounds double, ptr %ptrA2_c, i64 %k2
  store double %result2, ptr %a_out, align 8

  %k2.next = add nsw i64 %k2, 1
  %cmp2.k = icmp slt i64 %k2.next, %nm1.64
  br i1 %cmp2.k, label %for.body2.k, label %for.end2.k, !llvm.loop !10

for.end2.k:
  br label %for.inc209

for.inc209:
  %j2.next = add nsw i64 %j2, 1
  %cmp2.j = icmp slt i64 %j2.next, %nm1.64
  br i1 %cmp2.j, label %for.body2.j.outer, label %for.end211, !llvm.loop !11

for.end211:
  br label %for.inc212

for.inc212:
  %i2.next = add nsw i64 %i2, 1
  %cmp2.i = icmp slt i64 %i2.next, %nm1.64
  br i1 %cmp2.i, label %for.body2.i.outer, label %for.end214, !llvm.loop !12

for.end214:
  br label %for.inc215

for.inc215:
  %inc216 = add nsw i32 %t, 1
  %cmp.t2 = icmp sle i32 %inc216, 40
  br i1 %cmp.t2, label %for.cond, label %for.end217, !llvm.loop !13

for.end217:
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
