; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syr2k(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %outer.preheader, label %for.end51

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc49, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc50, %for.inc49 ]
  %i64 = sext i32 %i to i64
  %crow_off = mul nsw i64 %i64, %n64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow_off
  %arow_off = mul nsw i64 %i64, %m64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow_off
  %brow_off = mul nsw i64 %i64, %m64
  %brow = getelementptr inbounds double, ptr %B, i64 %brow_off

  ; inner loop 1: j = 0..i, C[i][j] *= beta
  %jcount1 = add nsw i32 %i, 1
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.cond
  %j1 = phi i32 [ 0, %for.cond ], [ %inc1, %for.body8 ]
  %j1_64 = sext i32 %j1 to i64
  %cptr1 = getelementptr inbounds double, ptr %crow, i64 %j1_64
  %cval1 = load double, ptr %cptr1, align 8
  %mulv = fmul double %cval1, %beta
  store double %mulv, ptr %cptr1, align 8
  %inc1 = add nsw i32 %j1, 1
  %cmp1 = icmp slt i32 %inc1, %jcount1
  br i1 %cmp1, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8
  %cmp_m = icmp sgt i32 %m, 0
  br i1 %cmp_m, label %for.cond11.preheader, label %for.end48

for.cond11.preheader:
  br label %for.cond11

for.cond11:                                       ; preds = %for.inc46, %for.cond11.preheader
  %k = phi i32 [ 0, %for.cond11.preheader ], [ %inc47, %for.inc46 ]
  %k64 = sext i32 %k to i64
  %aptr_ik = getelementptr inbounds double, ptr %arow, i64 %k64
  %aval_ik = load double, ptr %aptr_ik, align 8
  %bptr_ik = getelementptr inbounds double, ptr %brow, i64 %k64
  %bval_ik = load double, ptr %bptr_ik, align 8
  br label %for.body16

for.body16:                                       ; preds = %for.body16, %for.cond11
  %j2 = phi i32 [ 0, %for.cond11 ], [ %inc44, %for.body16 ]
  %j2_64 = sext i32 %j2 to i64
  %ajrow_off = mul nsw i64 %j2_64, %m64
  %ajrow = getelementptr inbounds double, ptr %A, i64 %ajrow_off
  %aptr_jk = getelementptr inbounds double, ptr %ajrow, i64 %k64
  %aval_jk = load double, ptr %aptr_jk, align 8
  %mul21 = fmul double %aval_jk, %alpha
  %mul26 = fmul double %mul21, %bval_ik

  %bjrow_off = mul nsw i64 %j2_64, %m64
  %bjrow = getelementptr inbounds double, ptr %B, i64 %bjrow_off
  %bptr_jk = getelementptr inbounds double, ptr %bjrow, i64 %k64
  %bval_jk = load double, ptr %bptr_jk, align 8
  %mul31 = fmul double %bval_jk, %alpha
  %mul36 = fmul double %mul31, %aval_ik

  %add37 = fadd double %mul26, %mul36

  %cptr2 = getelementptr inbounds double, ptr %crow, i64 %j2_64
  %cval2 = load double, ptr %cptr2, align 8
  %add42 = fadd double %cval2, %add37
  store double %add42, ptr %cptr2, align 8

  %inc44 = add nsw i32 %j2, 1
  %cmp15 = icmp sle i32 %inc44, %i
  br i1 %cmp15, label %for.body16, label %for.inc46

for.inc46:                                        ; preds = %for.body16
  %inc47 = add nsw i32 %k, 1
  %cmp12 = icmp slt i32 %inc47, %m
  br i1 %cmp12, label %for.cond11, label %for.end48

for.end48:                                        ; preds = %for.inc46, %for.end
  br label %for.inc49

for.inc49:                                        ; preds = %for.end48
  %inc50 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc50, %n
  br i1 %cmp, label %for.cond, label %for.end51

for.end51:                                        ; preds = %for.inc49, %entry
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
