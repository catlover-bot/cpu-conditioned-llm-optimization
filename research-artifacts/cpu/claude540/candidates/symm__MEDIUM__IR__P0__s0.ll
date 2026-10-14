; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.mn = icmp sle i32 %m, 0
  %cmp.nn = icmp sle i32 %n, 0
  %skip.outer = or i1 %cmp.mn, %cmp.nn
  br i1 %skip.outer, label %for.end61, label %preheader

preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc60, %for.inc59 ]
  %i64 = sext i32 %i to i64
  %Arow.off = mul nsw i64 %i64, %m64
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arow.off
  %Brow.i.off = mul nsw i64 %i64, %n64
  %Brow.i = getelementptr inbounds double, ptr %B, i64 %Brow.i.off
  %Crow.i = getelementptr inbounds double, ptr %C, i64 %Brow.i.off
  ; Aii
  %Aii.ptr = getelementptr inbounds double, ptr %Arow, i64 %i64
  %Aii = load double, ptr %Aii.ptr, align 8
  br label %for.body8

for.body8:                                        ; preds = %for.inc56, %for.cond
  %j = phi i32 [ 0, %for.cond ], [ %inc57, %for.inc56 ]
  %j64 = sext i32 %j to i64
  br i1 %cmp.mn, label %for.end, label %for.body11.ph

for.body11.ph:
  br label %for.body11

for.body11:                                       ; preds = %for.body11.ph, %for.body11
  %k = phi i32 [ 0, %for.body11.ph ], [ %inc, %for.body11 ]
  %temp2 = phi double [ 0.000000e+00, %for.body11.ph ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64

  %Bij.ptr = getelementptr inbounds double, ptr %Brow.i, i64 %j64
  %Bij = load double, ptr %Bij.ptr, align 8
  %mul = fmul double %alpha, %Bij

  %Aik.ptr = getelementptr inbounds double, ptr %Arow, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %mul18 = fmul double %mul, %Aik

  %Crow.k.off = mul nsw i64 %k64, %m64
  %Ckj.ptr = getelementptr inbounds double, ptr %C, i64 %Crow.k.off
  %Ckj.ptr2 = getelementptr inbounds double, ptr %Ckj.ptr, i64 %j64
  %Ckj = load double, ptr %Ckj.ptr2, align 8
  %add23 = fadd double %Ckj, %mul18
  store double %add23, ptr %Ckj.ptr2, align 8

  %Brow.k.off = mul nsw i64 %k64, %n64
  %Bkj.ptr = getelementptr inbounds double, ptr %B, i64 %Brow.k.off
  %Bkj.ptr2 = getelementptr inbounds double, ptr %Bkj.ptr, i64 %j64
  %Bkj = load double, ptr %Bkj.ptr2, align 8
  %mul32 = fmul double %Bkj, %Aik
  %add33 = fadd double %temp2, %mul32

  %inc = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc, %i
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  %add33.lcssa = phi double [ %add33, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2.final = phi double [ 0.000000e+00, %for.body8 ], [ %add33.lcssa, %for.end.loopexit ]

  %Cij.ptr = getelementptr inbounds double, ptr %Crow.i, i64 %j64
  %Cij = load double, ptr %Cij.ptr, align 8
  %mul38 = fmul double %beta, %Cij

  %Bij2.ptr = getelementptr inbounds double, ptr %Brow.i, i64 %j64
  %Bij2 = load double, ptr %Bij2.ptr, align 8
  %mul43 = fmul double %alpha, %Bij2

  %mul48 = fmul double %mul43, %Aii
  %add49 = fadd double %mul38, %mul48

  %mul50 = fmul double %alpha, %temp2.final
  %add51 = fadd double %add49, %mul50

  store double %add51, ptr %Cij.ptr, align 8

  br label %for.inc56

for.inc56:                                        ; preds = %for.end
  %inc57 = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc57, %n
  br i1 %cmp7, label %for.body8, label %for.end58

for.end58:                                        ; preds = %for.inc56
  br label %for.inc59

for.inc59:                                        ; preds = %for.end58
  %inc60 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc60, %m
  br i1 %cmp, label %for.cond, label %for.end61.loopexit

for.end61.loopexit:
  br label %for.end61

for.end61:                                        ; preds = %for.end61.loopexit, %entry
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
