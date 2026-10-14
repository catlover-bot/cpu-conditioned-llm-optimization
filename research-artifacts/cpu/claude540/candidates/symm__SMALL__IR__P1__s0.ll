; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.mn = icmp sle i32 %m, 0
  %cmp.nn = icmp sle i32 %n, 0
  %skip = or i1 %cmp.mn, %cmp.nn
  br i1 %skip, label %for.end61, label %preheader

preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc60, %for.inc59 ]
  %i64 = phi i64 [ 0, %preheader ], [ %i64.next, %for.inc59 ]
  %cmp = icmp slt i32 %i, %m
  br i1 %cmp, label %for.body, label %for.end61

for.body:                                         ; preds = %for.cond
  %Arow = mul nsw i64 %i64, %m64
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arow
  %Brow.i = mul nsw i64 %i64, %n64
  %Browptr.i = getelementptr inbounds double, ptr %B, i64 %Brow.i
  %Crow.i = mul nsw i64 %i64, %n64
  %Crowptr.i = getelementptr inbounds double, ptr %C, i64 %Crow.i
  %Aii.ptr = getelementptr inbounds double, ptr %Arowptr, i64 %i64
  %Aii = load double, ptr %Aii.ptr, align 8
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc56, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc57, %for.inc56 ]
  %j64 = phi i64 [ 0, %for.body ], [ %j64.next, %for.inc56 ]
  %cmp7 = icmp slt i32 %j, %n
  br i1 %cmp7, label %for.body8, label %for.end58

for.body8:                                        ; preds = %for.cond6
  %Bij.ptr = getelementptr inbounds double, ptr %Browptr.i, i64 %j64
  %Bij = load double, ptr %Bij.ptr, align 8
  %Cij.ptr = getelementptr inbounds double, ptr %Crowptr.i, i64 %j64
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc, %for.body8
  %k = phi i32 [ 0, %for.body8 ], [ %inc, %for.inc ]
  %k64 = phi i64 [ 0, %for.body8 ], [ %k64.next, %for.inc ]
  %temp2 = phi double [ 0.000000e+00, %for.body8 ], [ %add33, %for.inc ]
  %cmp10 = icmp slt i32 %k, %i
  br i1 %cmp10, label %for.body11, label %for.end

for.body11:                                       ; preds = %for.cond9
  %mul = fmul double %alpha, %Bij
  %Aik.ptr = getelementptr inbounds double, ptr %Arowptr, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %mul18 = fmul double %mul, %Aik
  %Crow.k = mul nsw i64 %k64, %n64
  %Ckrowptr = getelementptr inbounds double, ptr %C, i64 %Crow.k
  %Ckj.ptr = getelementptr inbounds double, ptr %Ckrowptr, i64 %j64
  %Ckj = load double, ptr %Ckj.ptr, align 8
  %add23 = fadd double %Ckj, %mul18
  store double %add23, ptr %Ckj.ptr, align 8
  %Brow.k = mul nsw i64 %k64, %n64
  %Bkrowptr = getelementptr inbounds double, ptr %B, i64 %Brow.k
  %Bkj.ptr = getelementptr inbounds double, ptr %Bkrowptr, i64 %j64
  %Bkj = load double, ptr %Bkj.ptr, align 8
  %mul32 = fmul double %Bkj, %Aik
  %add33 = fadd double %temp2, %mul32
  br label %for.inc

for.inc:                                          ; preds = %for.body11
  %inc = add nsw i32 %k, 1
  %k64.next = add nsw i64 %k64, 1
  br label %for.cond9, !llvm.loop !6

for.end:                                          ; preds = %for.cond9
  %temp2.final = phi double [ %temp2, %for.cond9 ]
  %Cij = load double, ptr %Cij.ptr, align 8
  %mul38 = fmul double %beta, %Cij
  %mul43 = fmul double %alpha, %Bij
  %mul48 = fmul double %mul43, %Aii
  %add49 = fadd double %mul38, %mul48
  %mul50 = fmul double %alpha, %temp2.final
  %add51 = fadd double %add49, %mul50
  store double %add51, ptr %Cij.ptr, align 8
  br label %for.inc56

for.inc56:                                        ; preds = %for.end
  %inc57 = add nsw i32 %j, 1
  %j64.next = add nsw i64 %j64, 1
  br label %for.cond6, !llvm.loop !8

for.end58:                                        ; preds = %for.cond6
  br label %for.inc59

for.inc59:                                        ; preds = %for.end58
  %inc60 = add nsw i32 %i, 1
  %i64.next = add nsw i64 %i64, 1
  br label %for.cond, !llvm.loop !9

for.end61:                                        ; preds = %for.cond, %entry
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
