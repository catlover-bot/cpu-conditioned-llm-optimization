; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.t0 = icmp sgt i32 %tsteps, 0
  br i1 %cmp.t0, label %check.n, label %for.end73

check.n:
  %n64 = sext i32 %n to i64
  %cmp.n = icmp sgt i32 %n, 2
  br i1 %cmp.n, label %t.preheader, label %for.end73

t.preheader:
  br label %for.body

for.body:
  %t = phi i32 [ 0, %t.preheader ], [ %inc72, %for.inc71 ]
  br label %for.body5

for.body5:
  %i = phi i32 [ 1, %for.body ], [ %inc69, %for.inc68 ]
  %i64 = sext i32 %i to i64
  %im1_64 = add nsw i64 %i64, -1
  %ip1_64 = add nsw i64 %i64, 1
  %rowim1 = mul nsw i64 %im1_64, %n64
  %rowi = mul nsw i64 %i64, %n64
  %rowip1 = mul nsw i64 %ip1_64, %n64
  %ptr.rowim1 = getelementptr inbounds double, ptr %A, i64 %rowim1
  %ptr.rowi = getelementptr inbounds double, ptr %A, i64 %rowi
  %ptr.rowip1 = getelementptr inbounds double, ptr %A, i64 %rowip1
  br label %for.body9

for.body9:
  %j = phi i32 [ 1, %for.body5 ], [ %inc, %for.body9 ]
  %j64 = sext i32 %j to i64
  %jm1_64 = add nsw i64 %j64, -1
  %jp1_64 = add nsw i64 %j64, 1

  %a00 = getelementptr inbounds double, ptr %ptr.rowim1, i64 %jm1_64
  %v00 = load double, ptr %a00, align 8
  %a01 = getelementptr inbounds double, ptr %ptr.rowim1, i64 %j64
  %v01 = load double, ptr %a01, align 8
  %s1 = fadd double %v00, %v01
  %a02 = getelementptr inbounds double, ptr %ptr.rowim1, i64 %jp1_64
  %v02 = load double, ptr %a02, align 8
  %s2 = fadd double %s1, %v02

  %a10 = getelementptr inbounds double, ptr %ptr.rowi, i64 %jm1_64
  %v10 = load double, ptr %a10, align 8
  %s3 = fadd double %s2, %v10
  %a11 = getelementptr inbounds double, ptr %ptr.rowi, i64 %j64
  %v11 = load double, ptr %a11, align 8
  %s4 = fadd double %s3, %v11
  %a12 = getelementptr inbounds double, ptr %ptr.rowi, i64 %jp1_64
  %v12 = load double, ptr %a12, align 8
  %s5 = fadd double %s4, %v12

  %a20 = getelementptr inbounds double, ptr %ptr.rowip1, i64 %jm1_64
  %v20 = load double, ptr %a20, align 8
  %s6 = fadd double %s5, %v20
  %a21 = getelementptr inbounds double, ptr %ptr.rowip1, i64 %j64
  %v21 = load double, ptr %a21, align 8
  %s7 = fadd double %s6, %v21
  %a22 = getelementptr inbounds double, ptr %ptr.rowip1, i64 %jp1_64
  %v22 = load double, ptr %a22, align 8
  %s8 = fadd double %s7, %v22

  %div = fdiv double %s8, 9.000000e+00
  store double %div, ptr %a11, align 8

  %inc = add nsw i32 %j, 1
  %sub7 = add nsw i32 %n, -2
  %cmp8 = icmp sle i32 %inc, %sub7
  br i1 %cmp8, label %for.body9, label %for.inc68, !llvm.loop !6

for.inc68:
  %inc69 = add nsw i32 %i, 1
  %sub3 = add nsw i32 %n, -2
  %cmp4 = icmp sle i32 %inc69, %sub3
  br i1 %cmp4, label %for.body5, label %for.inc71, !llvm.loop !8

for.inc71:
  %inc72 = add nsw i32 %t, 1
  %cmp = icmp slt i32 %inc72, %tsteps
  br i1 %cmp, label %for.body, label %for.end73, !llvm.loop !9

for.end73:
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
