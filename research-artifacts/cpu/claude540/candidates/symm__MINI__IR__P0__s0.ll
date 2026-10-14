; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end61

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.n = icmp sgt i32 %n, 0
  br label %for.cond.i

for.cond.i:
  %i = phi i32 [ 0, %outer.preheader ], [ %inc60, %for.inc59 ]
  br i1 %cmp.n, label %for.body8.preheader, label %for.inc59

for.body8.preheader:
  %i64 = sext i32 %i to i64
  %A.row.i = mul nsw i64 %i64, %m64
  %A.rowptr.i = getelementptr inbounds double, ptr %A, i64 %A.row.i
  %B.row.i = mul nsw i64 %i64, %n64
  %B.rowptr.i = getelementptr inbounds double, ptr %B, i64 %B.row.i
  %C.row.i = mul nsw i64 %i64, %n64
  %C.rowptr.i = getelementptr inbounds double, ptr %C, i64 %C.row.i
  %A.diag.ptr = getelementptr inbounds double, ptr %A.rowptr.i, i64 %i64
  %A.diag.val = load double, ptr %A.diag.ptr, align 8
  br label %for.body8

for.body8:
  %j = phi i32 [ 0, %for.body8.preheader ], [ %inc57, %for.inc56 ]
  %j64 = sext i32 %j to i64
  %B.ij.ptr = getelementptr inbounds double, ptr %B.rowptr.i, i64 %j64
  %C.ij.ptr = getelementptr inbounds double, ptr %C.rowptr.i, i64 %j64
  br label %for.cond9

for.cond9:
  %k = phi i32 [ 0, %for.body8 ], [ %inc, %for.inc ]
  %temp2 = phi double [ 0.000000e+00, %for.body8 ], [ %add33, %for.inc ]
  %cmp10 = icmp slt i32 %k, %i
  br i1 %cmp10, label %for.body11, label %for.end

for.body11:
  %k64 = sext i32 %k to i64
  %B.ij.val = load double, ptr %B.ij.ptr, align 8
  %mul = fmul double %alpha, %B.ij.val
  %A.ik.ptr = getelementptr inbounds double, ptr %A.rowptr.i, i64 %k64
  %A.ik.val = load double, ptr %A.ik.ptr, align 8
  %mul18 = fmul double %mul, %A.ik.val
  %C.krow = mul nsw i64 %k64, %n64
  %C.krowptr = getelementptr inbounds double, ptr %C, i64 %C.krow
  %C.kj.ptr = getelementptr inbounds double, ptr %C.krowptr, i64 %j64
  %C.kj.val = load double, ptr %C.kj.ptr, align 8
  %add23 = fadd double %C.kj.val, %mul18
  store double %add23, ptr %C.kj.ptr, align 8
  %B.krow = mul nsw i64 %k64, %n64
  %B.krowptr = getelementptr inbounds double, ptr %B, i64 %B.krow
  %B.kj.ptr = getelementptr inbounds double, ptr %B.krowptr, i64 %j64
  %B.kj.val = load double, ptr %B.kj.ptr, align 8
  %mul32 = fmul double %B.kj.val, %A.ik.val
  %add33 = fadd double %temp2, %mul32
  br label %for.inc

for.inc:
  %inc = add nsw i32 %k, 1
  br label %for.cond9, !llvm.loop !6

for.end:
  %C.ij.val = load double, ptr %C.ij.ptr, align 8
  %mul38 = fmul double %beta, %C.ij.val
  %B.ij.val2 = load double, ptr %B.ij.ptr, align 8
  %mul43 = fmul double %alpha, %B.ij.val2
  %mul48 = fmul double %mul43, %A.diag.val
  %add49 = fadd double %mul38, %mul48
  %mul50 = fmul double %alpha, %temp2
  %add51 = fadd double %add49, %mul50
  store double %add51, ptr %C.ij.ptr, align 8
  br label %for.inc56

for.inc56:
  %inc57 = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc57, %n
  br i1 %cmp7, label %for.body8, label %for.inc59, !llvm.loop !8

for.inc59:
  %inc60 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc60, %m
  br i1 %cmp, label %for.cond.i, label %for.end61, !llvm.loop !9

for.end61:
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
