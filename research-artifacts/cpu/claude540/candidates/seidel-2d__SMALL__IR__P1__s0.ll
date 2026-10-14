; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.t = icmp sgt i32 %tsteps, 0
  br i1 %cmp.t, label %check.n, label %for.end73

check.n:
  %n64 = sext i32 %n to i64
  %n.sub2 = sub nsw i32 %n, 2
  %cmp.n = icmp sge i32 %n.sub2, 1
  br i1 %cmp.n, label %t.preheader, label %for.end73

t.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc71, %t.preheader
  %t = phi i32 [ 0, %t.preheader ], [ %inc72, %for.inc71 ]
  br label %for.body2

for.body2:                                        ; preds = %for.end, %for.body
  %i = phi i32 [ 1, %for.body ], [ %inc69, %for.end ]
  %i64 = sext i32 %i to i64
  %im1_64 = add nsw i64 %i64, -1
  %ip1_64 = add nsw i64 %i64, 1
  %rowm1 = mul nsw i64 %im1_64, %n64
  %row0  = mul nsw i64 %i64, %n64
  %rowp1 = mul nsw i64 %ip1_64, %n64
  %rowm1.ptr = getelementptr inbounds double, ptr %A, i64 %rowm1
  %row0.ptr  = getelementptr inbounds double, ptr %A, i64 %row0
  %rowp1.ptr = getelementptr inbounds double, ptr %A, i64 %rowp1
  br label %for.body9

for.body9:                                         ; preds = %for.body9, %for.body2
  %j = phi i32 [ 1, %for.body2 ], [ %inc, %for.body9 ]
  %j64 = sext i32 %j to i64
  %jm1_64 = add nsw i64 %j64, -1
  %jp1_64 = add nsw i64 %j64, 1

  %a0 = getelementptr inbounds double, ptr %rowm1.ptr, i64 %jm1_64
  %v0 = load double, ptr %a0, align 8
  %a1 = getelementptr inbounds double, ptr %rowm1.ptr, i64 %j64
  %v1 = load double, ptr %a1, align 8
  %add19 = fadd double %v0, %v1
  %a2 = getelementptr inbounds double, ptr %rowm1.ptr, i64 %jp1_64
  %v2 = load double, ptr %a2, align 8
  %add26 = fadd double %add19, %v2

  %a3 = getelementptr inbounds double, ptr %row0.ptr, i64 %jm1_64
  %v3 = load double, ptr %a3, align 8
  %add32 = fadd double %add26, %v3
  %a4 = getelementptr inbounds double, ptr %row0.ptr, i64 %j64
  %v4 = load double, ptr %a4, align 8
  %add37 = fadd double %add32, %v4
  %a5 = getelementptr inbounds double, ptr %row0.ptr, i64 %jp1_64
  %v5 = load double, ptr %a5, align 8
  %add43 = fadd double %add37, %v5

  %a6 = getelementptr inbounds double, ptr %rowp1.ptr, i64 %jm1_64
  %v6 = load double, ptr %a6, align 8
  %add50 = fadd double %add43, %v6
  %a7 = getelementptr inbounds double, ptr %rowp1.ptr, i64 %j64
  %v7 = load double, ptr %a7, align 8
  %add56 = fadd double %add50, %v7
  %a8 = getelementptr inbounds double, ptr %rowp1.ptr, i64 %jp1_64
  %v8 = load double, ptr %a8, align 8
  %add63 = fadd double %add56, %v8

  %div = fdiv double %add63, 9.000000e+00
  store double %div, ptr %a4, align 8

  %inc = add nsw i32 %j, 1
  %cmp8 = icmp sgt i32 %inc, %n.sub2
  br i1 %cmp8, label %for.end, label %for.body9, !llvm.loop !6

for.end:                                         ; preds = %for.body9
  %inc69 = add nsw i32 %i, 1
  %cmp4 = icmp sgt i32 %inc69, %n.sub2
  br i1 %cmp4, label %for.end70, label %for.body2, !llvm.loop !8

for.end70:                                        ; preds = %for.end
  %inc72 = add nsw i32 %t, 1
  %cmp = icmp slt i32 %inc72, %tsteps
  br i1 %cmp, label %for.body, label %for.end73, !llvm.loop !9

for.end73:                                        ; preds = %for.end70, %check.n, %entry
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
