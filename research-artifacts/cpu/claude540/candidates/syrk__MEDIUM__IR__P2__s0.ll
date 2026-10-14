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
  br label %for.body

for.body:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %irow_c = mul nsw i64 %i64, %n64
  %irow_a = mul nsw i64 %i64, %m64
  %crow_i_ptr = getelementptr inbounds double, ptr %C, i64 %irow_c
  %arow_i_ptr = getelementptr inbounds double, ptr %A, i64 %irow_a
  ; j loop bound is i (inclusive), so count = i+1
  %jcount = add nsw i32 %i, 1
  br label %for.body6

for.body6:                                        ; preds = %for.body6, %for.body
  %j1 = phi i32 [ 0, %for.body ], [ %inc, %for.body6 ]
  %j1_64 = sext i32 %j1 to i64
  %cptr1 = getelementptr inbounds double, ptr %crow_i_ptr, i64 %j1_64
  %cval1 = load double, ptr %cptr1, align 8
  %mulb = fmul double %cval1, %beta
  store double %mulb, ptr %cptr1, align 8
  %inc = add nsw i32 %j1, 1
  %cmp5 = icmp slt i32 %inc, %jcount
  br i1 %cmp5, label %for.body6, label %for.end

for.end:                                          ; preds = %for.body6
  br i1 %cmp_m, label %for.body11.preheader, label %for.end35

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.end32, %for.body11.preheader
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc34, %for.end32 ]
  %k64 = sext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %arow_i_ptr, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %alpha_aik = fmul double %alpha, %aik
  br label %for.body14

for.body14:                                       ; preds = %for.body14, %for.body11
  %j2 = phi i32 [ 0, %for.body11 ], [ %inc31, %for.body14 ]
  %j2_64 = sext i32 %j2 to i64
  %jrow_a = mul nsw i64 %j2_64, %m64
  %ajk.ptr = getelementptr inbounds double, ptr %A, i64 %jrow_a
  %ajk.ptr2 = getelementptr inbounds double, ptr %ajk.ptr, i64 %k64
  %ajk = load double, ptr %ajk.ptr2, align 8
  %mul24 = fmul double %alpha_aik, %ajk
  %cij.ptr = getelementptr inbounds double, ptr %crow_i_ptr, i64 %j2_64
  %cij = load double, ptr %cij.ptr, align 8
  %add29 = fadd double %cij, %mul24
  store double %add29, ptr %cij.ptr, align 8
  %inc31 = add nsw i32 %j2, 1
  %cmp13 = icmp slt i32 %inc31, %jcount
  br i1 %cmp13, label %for.body14, label %for.end32

for.end32:                                        ; preds = %for.body14
  %inc34 = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc34, %m
  br i1 %cmp10, label %for.body11, label %for.end35

for.end35:                                        ; preds = %for.end32, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc37, %n
  br i1 %cmp, label %for.body, label %for.end38

for.end38:                                        ; preds = %for.inc36, %entry
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
