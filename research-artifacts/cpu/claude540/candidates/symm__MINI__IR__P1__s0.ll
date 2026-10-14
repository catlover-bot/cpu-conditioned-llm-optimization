; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %add1 = add nsw i32 %n, 0
  %n64 = zext i32 %add1 to i64
  %add3 = add nsw i32 %m, 0
  %m64 = zext i32 %add3 to i64

  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end61

outer.preheader:
  %cmp.n = icmp sgt i32 %n, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc60, %for.inc59 ]
  %i64 = sext i32 %i to i64
  %Coff_i = mul nsw i64 %i64, %n64
  %Crow_i = getelementptr inbounds double, ptr %C, i64 %Coff_i
  %Boff_i = mul nsw i64 %i64, %n64
  %Brow_i = getelementptr inbounds double, ptr %B, i64 %Boff_i
  %Aoff_i = mul nsw i64 %i64, %m64
  %Arow_i = getelementptr inbounds double, ptr %A, i64 %Aoff_i
  br i1 %cmp.n, label %for.body8.preheader, label %for.end58

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.end, %for.body8.preheader
  %j = phi i32 [ 0, %for.body8.preheader ], [ %inc57, %for.end ]
  %j64 = sext i32 %j to i64

  %cmp.k = icmp sgt i32 %i, 0
  br i1 %cmp.k, label %for.body11.preheader, label %for.end

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %temp2 = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64

  %Bij_ptr = getelementptr inbounds double, ptr %Brow_i, i64 %j64
  %Bij = load double, ptr %Bij_ptr, align 8
  %mul = fmul double %alpha, %Bij

  %Aik_ptr = getelementptr inbounds double, ptr %Arow_i, i64 %k64
  %Aik = load double, ptr %Aik_ptr, align 8
  %mul18 = fmul double %mul, %Aik

  %Coff_k = mul nsw i64 %k64, %n64
  %Crow_k = getelementptr inbounds double, ptr %C, i64 %Coff_k
  %Ckj_ptr = getelementptr inbounds double, ptr %Crow_k, i64 %j64
  %Ckj = load double, ptr %Ckj_ptr, align 8
  %add23 = fadd double %Ckj, %mul18
  store double %add23, ptr %Ckj_ptr, align 8

  %Boff_k = mul nsw i64 %k64, %n64
  %Brow_k = getelementptr inbounds double, ptr %B, i64 %Boff_k
  %Bkj_ptr = getelementptr inbounds double, ptr %Brow_k, i64 %j64
  %Bkj = load double, ptr %Bkj_ptr, align 8
  %mul32 = fmul double %Bkj, %Aik
  %add33 = fadd double %temp2, %mul32

  %inc = add nsw i32 %k, 1
  %cmp.k.next = icmp slt i32 %inc, %i
  br i1 %cmp.k.next, label %for.body11, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:                                 ; preds = %for.body11
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2.final = phi double [ 0.000000e+00, %for.body8 ], [ %add33, %for.end.loopexit ]

  %Cij_ptr = getelementptr inbounds double, ptr %Crow_i, i64 %j64
  %Cij = load double, ptr %Cij_ptr, align 8
  %mul38 = fmul double %beta, %Cij

  %Bij2_ptr = getelementptr inbounds double, ptr %Brow_i, i64 %j64
  %Bij2 = load double, ptr %Bij2_ptr, align 8
  %mul43 = fmul double %alpha, %Bij2

  %Aii_ptr = getelementptr inbounds double, ptr %Arow_i, i64 %i64
  %Aii = load double, ptr %Aii_ptr, align 8
  %mul48 = fmul double %mul43, %Aii
  %add49 = fadd double %mul38, %mul48

  %mul50 = fmul double %alpha, %temp2.final
  %add51 = fadd double %add49, %mul50

  store double %add51, ptr %Cij_ptr, align 8

  %inc57 = add nsw i32 %j, 1
  %cmp.n.next = icmp slt i32 %inc57, %n
  br i1 %cmp.n.next, label %for.body8, label %for.end58.loopexit, !llvm.loop !8

for.end58.loopexit:                               ; preds = %for.end
  br label %for.end58

for.end58:                                        ; preds = %for.end58.loopexit, %for.cond
  br label %for.inc59

for.inc59:                                        ; preds = %for.end58
  %inc60 = add nsw i32 %i, 1
  %cmp.m.next = icmp slt i32 %inc60, %m
  br i1 %cmp.m.next, label %for.cond, label %for.end61.loopexit, !llvm.loop !9

for.end61.loopexit:                               ; preds = %for.inc59
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
