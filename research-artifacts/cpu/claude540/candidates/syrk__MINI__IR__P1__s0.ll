; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %outer.preheader, label %for.end38

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp_m = icmp sgt i32 %m, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %crow_off = mul nsw i64 %i64, %n64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow_off
  %arow_off = mul nsw i64 %i64, %m64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow_off

  ; inner loop 1: for j in 0..=i : C[i][j] *= beta
  br label %for.cond4

for.cond4:                                        ; preds = %for.inc, %for.cond
  %j1 = phi i32 [ 0, %for.cond ], [ %inc, %for.inc ]
  %cmp5 = icmp sle i32 %j1, %i
  br i1 %cmp5, label %for.body6, label %for.end

for.body6:                                        ; preds = %for.cond4
  %j1_64 = sext i32 %j1 to i64
  %cptr1 = getelementptr inbounds double, ptr %crow, i64 %j1_64
  %cval1 = load double, ptr %cptr1, align 8
  %mul = fmul double %cval1, %beta
  store double %mul, ptr %cptr1, align 8
  br label %for.inc

for.inc:                                          ; preds = %for.body6
  %inc = add nsw i32 %j1, 1
  br label %for.cond4, !llvm.loop !6

for.end:                                          ; preds = %for.cond4
  br i1 %cmp_m, label %for.cond9.preheader, label %for.end35

for.cond9.preheader:
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc33, %for.cond9.preheader
  %k = phi i32 [ 0, %for.cond9.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %arow, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %alpha_aik = fmul double %alpha, %aik
  br label %for.cond12

for.cond12:                                       ; preds = %for.inc30, %for.cond9
  %j2 = phi i32 [ 0, %for.cond9 ], [ %inc31, %for.inc30 ]
  %cmp13 = icmp sle i32 %j2, %i
  br i1 %cmp13, label %for.body14, label %for.end32

for.body14:                                       ; preds = %for.cond12
  %j2_64 = sext i32 %j2 to i64
  %ajrow_off = mul nsw i64 %j2_64, %m64
  %ajrow = getelementptr inbounds double, ptr %A, i64 %ajrow_off
  %ajk.ptr = getelementptr inbounds double, ptr %ajrow, i64 %k64
  %ajk = load double, ptr %ajk.ptr, align 8
  %mul24 = fmul double %alpha_aik, %ajk
  %cptr2 = getelementptr inbounds double, ptr %crow, i64 %j2_64
  %cval2 = load double, ptr %cptr2, align 8
  %add29 = fadd double %cval2, %mul24
  store double %add29, ptr %cptr2, align 8
  br label %for.inc30

for.inc30:                                        ; preds = %for.body14
  %inc31 = add nsw i32 %j2, 1
  br label %for.cond12, !llvm.loop !8

for.end32:                                        ; preds = %for.cond12
  br label %for.inc33

for.inc33:                                        ; preds = %for.end32
  %inc34 = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc34, %m
  br i1 %cmp10, label %for.cond9, label %for.end35.loopexit, !llvm.loop !9

for.end35.loopexit:
  br label %for.end35

for.end35:                                        ; preds = %for.end35.loopexit, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc37, %n
  br i1 %cmp, label %for.cond, label %for.end38.loopexit, !llvm.loop !10

for.end38.loopexit:
  br label %for.end38

for.end38:                                        ; preds = %for.end38.loopexit, %entry
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
!10 = distinct !{!10, !7}
