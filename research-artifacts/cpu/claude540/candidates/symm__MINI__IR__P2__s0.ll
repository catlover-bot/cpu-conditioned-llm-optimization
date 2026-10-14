; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m0 = icmp sgt i32 %m, 0
  br i1 %cmp.m0, label %preheader, label %for.end61

preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc60, %for.inc59 ]
  %cmp.n0 = icmp sgt i32 %n, 0
  br i1 %cmp.n0, label %for.body, label %for.inc59

for.body:                                         ; preds = %for.cond
  %i64 = sext i32 %i to i64
  %Bi.row = mul nsw i64 %i64, %n64
  %Bi.ptr = getelementptr inbounds double, ptr %B, i64 %Bi.row
  %Ai.row = mul nsw i64 %i64, %m64
  %Ai.ptr = getelementptr inbounds double, ptr %A, i64 %Ai.row
  %Ci.row = mul nsw i64 %i64, %n64
  %Ci.ptr = getelementptr inbounds double, ptr %C, i64 %Ci.row
  %Aii.ptr = getelementptr inbounds double, ptr %Ai.ptr, i64 %i64
  %Aii = load double, ptr %Aii.ptr, align 8
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc56, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc57, %for.inc56 ]
  %cmp7 = icmp slt i32 %j, %n
  br i1 %cmp7, label %for.body8, label %for.end58

for.body8:                                        ; preds = %for.cond6
  %j64 = sext i32 %j to i64
  %cmp.k0 = icmp sgt i32 %i, 0
  br i1 %cmp.k0, label %for.body11.preheader, label %for.end

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.body11.preheader, %for.body11
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %temp2.k = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64

  %Bij.ptr = getelementptr inbounds double, ptr %Bi.ptr, i64 %j64
  %Bij = load double, ptr %Bij.ptr, align 8
  %mul = fmul double %alpha, %Bij

  %Aik.ptr = getelementptr inbounds double, ptr %Ai.ptr, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %mul18 = fmul double %mul, %Aik

  %Ckj.row = mul nsw i64 %k64, %n64
  %Ckj.ptr0 = getelementptr inbounds double, ptr %C, i64 %Ckj.row
  %Ckj.ptr = getelementptr inbounds double, ptr %Ckj.ptr0, i64 %j64
  %Ckj = load double, ptr %Ckj.ptr, align 8
  %add23 = fadd double %Ckj, %mul18
  store double %add23, ptr %Ckj.ptr, align 8

  %Bkj.row = mul nsw i64 %k64, %n64
  %Bkj.ptr0 = getelementptr inbounds double, ptr %B, i64 %Bkj.row
  %Bkj.ptr = getelementptr inbounds double, ptr %Bkj.ptr0, i64 %j64
  %Bkj = load double, ptr %Bkj.ptr, align 8

  %mul32 = fmul double %Bkj, %Aik
  %add33 = fadd double %temp2.k, %mul32

  %inc = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc, %i
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  %temp2.final = phi double [ %add33, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2 = phi double [ 0.000000e+00, %for.body8 ], [ %temp2.final, %for.end.loopexit ]

  %Cij.ptr = getelementptr inbounds double, ptr %Ci.ptr, i64 %j64
  %Cij = load double, ptr %Cij.ptr, align 8
  %mul38 = fmul double %beta, %Cij

  %Bij2.ptr = getelementptr inbounds double, ptr %Bi.ptr, i64 %j64
  %Bij2 = load double, ptr %Bij2.ptr, align 8
  %mul43 = fmul double %alpha, %Bij2

  %mul48 = fmul double %mul43, %Aii
  %add49 = fadd double %mul38, %mul48

  %mul50 = fmul double %alpha, %temp2
  %add51 = fadd double %add49, %mul50

  store double %add51, ptr %Cij.ptr, align 8

  br label %for.inc56

for.inc56:                                        ; preds = %for.end
  %inc57 = add nsw i32 %j, 1
  br label %for.cond6, !llvm.loop !8

for.end58:                                        ; preds = %for.cond6
  br label %for.inc59

for.inc59:                                        ; preds = %for.end58, %for.cond
  %inc60 = add nsw i32 %i, 1
  %cmp.mi = icmp slt i32 %inc60, %m
  br i1 %cmp.mi, label %for.cond, label %for.end61.loopexit, !llvm.loop !9

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
