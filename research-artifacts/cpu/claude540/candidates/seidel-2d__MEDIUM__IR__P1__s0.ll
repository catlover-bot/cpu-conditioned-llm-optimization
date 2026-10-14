; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end73

preheader:
  %n64 = zext i32 %n to i64
  %nm2 = add nsw i32 %n, -2
  br label %for.cond

for.cond:                                         ; preds = %for.inc71, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc72, %for.inc71 ]
  br label %for.body

for.body:                                         ; preds = %for.cond
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc68, %for.body
  %i = phi i32 [ 1, %for.body ], [ %inc69, %for.inc68 ]
  %i64 = sext i32 %i to i64
  %im1_64 = add nsw i64 %i64, -1
  %ip1_64 = add nsw i64 %i64, 1
  %rowim1_off = mul nsw i64 %im1_64, %n64
  %rowi_off = mul nsw i64 %i64, %n64
  %rowip1_off = mul nsw i64 %ip1_64, %n64
  %rowim1 = getelementptr inbounds double, ptr %A, i64 %rowim1_off
  %rowi = getelementptr inbounds double, ptr %A, i64 %rowi_off
  %rowip1 = getelementptr inbounds double, ptr %A, i64 %rowip1_off
  br label %for.cond6

for.cond6:                                        ; preds = %for.body9, %for.cond2
  %j = phi i32 [ 1, %for.cond2 ], [ %inc, %for.body9 ]
  %cmp8 = icmp sle i32 %j, %nm2
  br i1 %cmp8, label %for.body9, label %for.end

for.body9:                                        ; preds = %for.cond6
  %j64 = sext i32 %j to i64
  %jm1_64 = add nsw i64 %j64, -1
  %jp1_64 = add nsw i64 %j64, 1

  %p_im1_jm1 = getelementptr inbounds double, ptr %rowim1, i64 %jm1_64
  %v_im1_jm1 = load double, ptr %p_im1_jm1, align 8
  %p_im1_j = getelementptr inbounds double, ptr %rowim1, i64 %j64
  %v_im1_j = load double, ptr %p_im1_j, align 8
  %add19 = fadd double %v_im1_jm1, %v_im1_j
  %p_im1_jp1 = getelementptr inbounds double, ptr %rowim1, i64 %jp1_64
  %v_im1_jp1 = load double, ptr %p_im1_jp1, align 8
  %add26 = fadd double %add19, %v_im1_jp1

  %p_i_jm1 = getelementptr inbounds double, ptr %rowi, i64 %jm1_64
  %v_i_jm1 = load double, ptr %p_i_jm1, align 8
  %add32 = fadd double %add26, %v_i_jm1
  %p_i_j = getelementptr inbounds double, ptr %rowi, i64 %j64
  %v_i_j = load double, ptr %p_i_j, align 8
  %add37 = fadd double %add32, %v_i_j
  %p_i_jp1 = getelementptr inbounds double, ptr %rowi, i64 %jp1_64
  %v_i_jp1 = load double, ptr %p_i_jp1, align 8
  %add43 = fadd double %add37, %v_i_jp1

  %p_ip1_jm1 = getelementptr inbounds double, ptr %rowip1, i64 %jm1_64
  %v_ip1_jm1 = load double, ptr %p_ip1_jm1, align 8
  %add50 = fadd double %add43, %v_ip1_jm1
  %p_ip1_j = getelementptr inbounds double, ptr %rowip1, i64 %j64
  %v_ip1_j = load double, ptr %p_ip1_j, align 8
  %add56 = fadd double %add50, %v_ip1_j
  %p_ip1_jp1 = getelementptr inbounds double, ptr %rowip1, i64 %jp1_64
  %v_ip1_jp1 = load double, ptr %p_ip1_jp1, align 8
  %add63 = fadd double %add56, %v_ip1_jp1

  %div = fdiv double %add63, 9.000000e+00
  store double %div, ptr %p_i_j, align 8

  %inc = add nsw i32 %j, 1
  br label %for.cond6, !llvm.loop !6

for.end:                                          ; preds = %for.cond6
  br label %for.inc68

for.inc68:                                        ; preds = %for.end
  %inc69 = add nsw i32 %i, 1
  %cmp4 = icmp sle i32 %inc69, %nm2
  br i1 %cmp4, label %for.cond2, label %for.end70, !llvm.loop !8

for.end70:                                        ; preds = %for.inc68
  br label %for.inc71

for.inc71:                                        ; preds = %for.end70
  %inc72 = add nsw i32 %t, 1
  %cmp.loop = icmp slt i32 %inc72, %tsteps
  br i1 %cmp.loop, label %for.cond, label %for.end73, !llvm.loop !9

for.end73:                                        ; preds = %for.inc71, %entry
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
