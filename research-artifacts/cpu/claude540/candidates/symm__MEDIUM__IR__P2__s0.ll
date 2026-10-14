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
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc60, %for.inc59 ]
  br i1 %cmp.n, label %for.body.j.preheader, label %for.inc59

for.body.j.preheader:
  %i64 = sext i32 %i to i64
  %A_row_off = mul nsw i64 %i64, %m64
  %A_row = getelementptr inbounds double, ptr %A, i64 %A_row_off
  %A_ii_ptr = getelementptr inbounds double, ptr %A_row, i64 %i64
  %A_ii = load double, ptr %A_ii_ptr, align 8
  %B_row_off = mul nsw i64 %i64, %n64
  %B_row = getelementptr inbounds double, ptr %B, i64 %B_row_off
  %cmp.k = icmp sgt i32 %i, 0
  br label %for.body8

for.body8:                                        ; preds = %for.end, %for.body.j.preheader
  %j = phi i32 [ 0, %for.body.j.preheader ], [ %inc57, %for.end ]
  br i1 %cmp.k, label %for.body11.preheader, label %for.end

for.body11.preheader:
  %j64 = sext i32 %j to i64
  %B_ij_ptr = getelementptr inbounds double, ptr %B_row, i64 %j64
  %B_ij = load double, ptr %B_ij_ptr, align 8
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %temp2.in = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64

  %mul = fmul double %alpha, %B_ij
  %A_ik_ptr = getelementptr inbounds double, ptr %A_row, i64 %k64
  %A_ik = load double, ptr %A_ik_ptr, align 8
  %mul18 = fmul double %mul, %A_ik

  %C_krow_off = mul nsw i64 %k64, %n64
  %C_row_k = getelementptr inbounds double, ptr %C, i64 %C_krow_off
  %C_kj_ptr = getelementptr inbounds double, ptr %C_row_k, i64 %j64
  %C_kj = load double, ptr %C_kj_ptr, align 8
  %add23 = fadd double %C_kj, %mul18
  store double %add23, ptr %C_kj_ptr, align 8

  %B_krow_off = mul nsw i64 %k64, %n64
  %B_row_k = getelementptr inbounds double, ptr %B, i64 %B_krow_off
  %B_kj_ptr = getelementptr inbounds double, ptr %B_row_k, i64 %j64
  %B_kj = load double, ptr %B_kj_ptr, align 8
  %mul32 = fmul double %B_kj, %A_ik
  %add33 = fadd double %temp2.in, %mul32

  %inc = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc, %i
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body11
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2 = phi double [ 0.000000e+00, %for.body8 ], [ %add33, %for.end.loopexit ]

  %C_irow_off = mul nsw i64 %i64, %n64
  %C_row_i = getelementptr inbounds double, ptr %C, i64 %C_irow_off
  %C_ij_ptr = getelementptr inbounds double, ptr %C_row_i, i64 %j64
  %C_ij = load double, ptr %C_ij_ptr, align 8
  %mul38 = fmul double %beta, %C_ij

  %B_ij2_ptr = getelementptr inbounds double, ptr %B_row, i64 %j64
  %B_ij2 = load double, ptr %B_ij2_ptr, align 8
  %mul43 = fmul double %alpha, %B_ij2
  %mul48 = fmul double %mul43, %A_ii
  %add49 = fadd double %mul38, %mul48

  %mul50 = fmul double %alpha, %temp2
  %add51 = fadd double %add49, %mul50

  store double %add51, ptr %C_ij_ptr, align 8

  %inc57 = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc57, %n
  br i1 %cmp7, label %for.body8, label %for.inc59.loopexit

for.inc59.loopexit:                               ; preds = %for.end
  br label %for.inc59

for.inc59:                                        ; preds = %for.inc59.loopexit, %for.cond
  %inc60 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc60, %m
  br i1 %cmp, label %for.cond, label %for.end61.loopexit

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
