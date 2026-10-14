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
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc60, %for.inc59 ]
  %i64 = sext i32 %i to i64
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %for.body, label %for.end61.loopexit

for.body:                                         ; preds = %for.cond
  %B.row.i = getelementptr inbounds double, ptr %B, i64 %i64
  %Brow.off = mul nsw i64 %i64, %n64
  %B.row.i.ptr = getelementptr inbounds double, ptr %B, i64 %Brow.off
  %A.row.i.off = mul nsw i64 %i64, %m64
  %A.row.i.ptr = getelementptr inbounds double, ptr %A, i64 %A.row.i.off
  %C.row.i.off = mul nsw i64 %i64, %n64
  %C.row.i.ptr = getelementptr inbounds double, ptr %C, i64 %C.row.i.off
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc56, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc57, %for.inc56 ]
  %j64 = sext i32 %j to i64
  br label %for.body8

for.body8:                                        ; preds = %for.cond6
  %cmp.i0 = icmp sgt i32 %i, 0
  br i1 %cmp.i0, label %for.cond9.preheader, label %for.end

for.cond9.preheader:
  %Bij.ptr = getelementptr inbounds double, ptr %B.row.i.ptr, i64 %j64
  %Bij = load double, ptr %Bij.ptr, align 8
  %alphaBij = fmul double %alpha, %Bij
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.cond9.preheader
  %k = phi i32 [ 0, %for.cond9.preheader ], [ %inc, %for.body11 ]
  %temp2.acc = phi double [ 0.000000e+00, %for.cond9.preheader ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64

  %Aik.ptr = getelementptr inbounds double, ptr %A.row.i.ptr, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %mul = fmul double %alphaBij, %Aik

  %C.row.k.off = mul nsw i64 %k64, %n64
  %C.row.k.ptr = getelementptr inbounds double, ptr %C, i64 %C.row.k.off
  %Ckj.ptr = getelementptr inbounds double, ptr %C.row.k.ptr, i64 %j64
  %Ckj = load double, ptr %Ckj.ptr, align 8
  %add23 = fadd double %Ckj, %mul
  store double %add23, ptr %Ckj.ptr, align 8

  %B.row.k.off = mul nsw i64 %k64, %n64
  %B.row.k.ptr = getelementptr inbounds double, ptr %B, i64 %B.row.k.off
  %Bkj.ptr = getelementptr inbounds double, ptr %B.row.k.ptr, i64 %j64
  %Bkj = load double, ptr %Bkj.ptr, align 8

  %mul32 = fmul double %Bkj, %Aik
  %add33 = fadd double %temp2.acc, %mul32

  %inc = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc, %i
  br i1 %cmp10, label %for.body11, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:                                 ; preds = %for.body11
  %temp2.final = phi double [ %add33, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2 = phi double [ 0.000000e+00, %for.body8 ], [ %temp2.final, %for.end.loopexit ]

  %Cij.ptr = getelementptr inbounds double, ptr %C.row.i.ptr, i64 %j64
  %Cij = load double, ptr %Cij.ptr, align 8
  %mul38 = fmul double %beta, %Cij

  %Bij2.ptr = getelementptr inbounds double, ptr %B.row.i.ptr, i64 %j64
  %Bij2 = load double, ptr %Bij2.ptr, align 8
  %mul43 = fmul double %alpha, %Bij2

  %Aii.ptr = getelementptr inbounds double, ptr %A.row.i.ptr, i64 %i64
  %Aii = load double, ptr %Aii.ptr, align 8
  %mul48 = fmul double %mul43, %Aii
  %add49 = fadd double %mul38, %mul48

  %mul50 = fmul double %alpha, %temp2
  %add51 = fadd double %add49, %mul50

  store double %add51, ptr %Cij.ptr, align 8
  br label %for.inc56

for.inc56:                                        ; preds = %for.end
  %inc57 = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc57, %n
  br i1 %cmp7, label %for.cond6, label %for.inc59, !llvm.loop !8

for.inc59:                                        ; preds = %for.inc56
  %inc60 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc60, %m
  br i1 %cmp, label %for.cond, label %for.end61.loopexit2, !llvm.loop !9

for.end61.loopexit:                               ; preds = %for.cond
  br label %for.end61

for.end61.loopexit2:                              ; preds = %for.inc59
  br label %for.end61

for.end61:                                        ; preds = %for.end61.loopexit2, %for.end61.loopexit, %entry
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
