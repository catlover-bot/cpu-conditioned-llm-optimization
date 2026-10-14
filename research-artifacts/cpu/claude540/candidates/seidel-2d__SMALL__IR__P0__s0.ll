; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.outer = icmp sgt i32 %tsteps, 0
  br i1 %cmp.outer, label %check.n, label %for.end73

check.n:
  %n64 = sext i32 %n to i64
  %cmp.n = icmp sgt i32 %n, 2
  br i1 %cmp.n, label %t.preheader, label %for.end73

t.preheader:
  %nm2 = add nsw i32 %n, -2
  br label %for.body

for.body:                                         ; preds = %for.inc71, %t.preheader
  %t = phi i32 [ 0, %t.preheader ], [ %inc72, %for.inc71 ]
  br label %for.body5

for.body5:                                        ; preds = %for.inc68, %for.body
  %i = phi i32 [ 1, %for.body ], [ %inc69, %for.inc68 ]
  %i64 = sext i32 %i to i64
  %im1_64 = add nsw i64 %i64, -1
  %ip1_64 = add nsw i64 %i64, 1
  %rowbase.im1 = mul nsw i64 %im1_64, %n64
  %rowbase.i = mul nsw i64 %i64, %n64
  %rowbase.ip1 = mul nsw i64 %ip1_64, %n64
  %rowptr.im1 = getelementptr inbounds double, ptr %A, i64 %rowbase.im1
  %rowptr.i = getelementptr inbounds double, ptr %A, i64 %rowbase.i
  %rowptr.ip1 = getelementptr inbounds double, ptr %A, i64 %rowbase.ip1
  br label %for.body9

for.body9:                                        ; preds = %for.body9, %for.body5
  %j = phi i32 [ 1, %for.body5 ], [ %inc, %for.body9 ]
  %j64 = sext i32 %j to i64
  %jm1_64 = add nsw i64 %j64, -1
  %jp1_64 = add nsw i64 %j64, 1

  %p1 = getelementptr inbounds double, ptr %rowptr.im1, i64 %jm1_64
  %v1 = load double, ptr %p1, align 8
  %p2 = getelementptr inbounds double, ptr %rowptr.im1, i64 %j64
  %v2 = load double, ptr %p2, align 8
  %a1 = fadd double %v1, %v2
  %p3 = getelementptr inbounds double, ptr %rowptr.im1, i64 %jp1_64
  %v3 = load double, ptr %p3, align 8
  %a2 = fadd double %a1, %v3
  %p4 = getelementptr inbounds double, ptr %rowptr.i, i64 %jm1_64
  %v4 = load double, ptr %p4, align 8
  %a3 = fadd double %a2, %v4
  %p5 = getelementptr inbounds double, ptr %rowptr.i, i64 %j64
  %v5 = load double, ptr %p5, align 8
  %a4 = fadd double %a3, %v5
  %p6 = getelementptr inbounds double, ptr %rowptr.i, i64 %jp1_64
  %v6 = load double, ptr %p6, align 8
  %a5 = fadd double %a4, %v6
  %p7 = getelementptr inbounds double, ptr %rowptr.ip1, i64 %jm1_64
  %v7 = load double, ptr %p7, align 8
  %a6 = fadd double %a5, %v7
  %p8 = getelementptr inbounds double, ptr %rowptr.ip1, i64 %j64
  %v8 = load double, ptr %p8, align 8
  %a7 = fadd double %a6, %v8
  %p9 = getelementptr inbounds double, ptr %rowptr.ip1, i64 %jp1_64
  %v9 = load double, ptr %p9, align 8
  %a8 = fadd double %a7, %v9

  %div = fdiv double %a8, 9.000000e+00
  store double %div, ptr %p5, align 8

  %inc = add nsw i32 %j, 1
  %cmp8 = icmp sle i32 %inc, %nm2
  br i1 %cmp8, label %for.body9, label %for.inc68, !llvm.loop !6

for.inc68:                                        ; preds = %for.body9
  %inc69 = add nsw i32 %i, 1
  %cmp4 = icmp sle i32 %inc69, %nm2
  br i1 %cmp4, label %for.body5, label %for.inc71, !llvm.loop !8

for.inc71:                                        ; preds = %for.inc68
  %inc72 = add nsw i32 %t, 1
  %cmp = icmp slt i32 %inc72, %tsteps
  br i1 %cmp, label %for.body, label %for.end73, !llvm.loop !9

for.end73:                                        ; preds = %for.inc71, %check.n, %entry
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
