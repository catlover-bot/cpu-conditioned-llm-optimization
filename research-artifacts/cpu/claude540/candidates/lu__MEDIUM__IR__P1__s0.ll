; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_lu(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end57

preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc55, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc56, %for.inc55 ]
  %cmp = icmp slt i32 %i, %n
  br i1 %cmp, label %for.body, label %for.end57.loopexit

for.body:                                         ; preds = %for.cond
  %i64 = sext i32 %i to i64
  %irowoff = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irowoff
  %cmp3.first = icmp slt i32 0, %i
  br i1 %cmp3.first, label %for.body4.preheader, label %for.end28

for.body4.preheader:
  br label %for.body4

for.body4:                                         ; preds = %for.body4.preheader, %for.end
  %j = phi i32 [ 0, %for.body4.preheader ], [ %inc27, %for.end ]
  %j64 = sext i32 %j to i64
  %jrowoff = mul nsw i64 %j64, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrowoff
  %aij.ptr = getelementptr inbounds double, ptr %irow, i64 %j64
  %cmp6.first = icmp slt i32 0, %j
  br i1 %cmp6.first, label %for.body7.preheader, label %for.end

for.body7.preheader:
  br label %for.body7

for.body7:                                         ; preds = %for.body7.preheader, %for.body7
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %k64 = sext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %irow, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %akj.ptr = getelementptr inbounds double, ptr %jrow, i64 %k64
  %akj = load double, ptr %akj.ptr, align 8
  %mul = fmul double %aik, %akj
  %cur = load double, ptr %aij.ptr, align 8
  %sub = fsub double %cur, %mul
  store double %sub, ptr %aij.ptr, align 8
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body4
  %ajj.ptr = getelementptr inbounds double, ptr %jrow, i64 %j64
  %ajj = load double, ptr %ajj.ptr, align 8
  %aij.val = load double, ptr %aij.ptr, align 8
  %div = fdiv double %aij.val, %ajj
  store double %div, ptr %aij.ptr, align 8
  %inc27 = add nsw i32 %j, 1
  %cmp3 = icmp slt i32 %inc27, %i
  br i1 %cmp3, label %for.body4, label %for.end28.loopexit

for.end28.loopexit:
  br label %for.end28

for.end28:                                        ; preds = %for.end28.loopexit, %for.body
  %cmp30.first = icmp slt i32 %i, %n
  br i1 %cmp30.first, label %for.body31.preheader, label %for.end54

for.body31.preheader:
  br label %for.body31

for.body31:                                         ; preds = %for.body31.preheader, %for.inc52
  %j2 = phi i32 [ %i, %for.body31.preheader ], [ %inc53, %for.inc52 ]
  %j2.64 = sext i32 %j2 to i64
  %aij2.ptr = getelementptr inbounds double, ptr %irow, i64 %j2.64
  %cmp33.first = icmp slt i32 0, %i
  br i1 %cmp33.first, label %for.body34.preheader, label %for.inc52

for.body34.preheader:
  br label %for.body34

for.body34:                                         ; preds = %for.body34.preheader, %for.body34
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc50, %for.body34 ]
  %k2.64 = sext i32 %k2 to i64
  %aik2.ptr = getelementptr inbounds double, ptr %irow, i64 %k2.64
  %aik2 = load double, ptr %aik2.ptr, align 8
  %k2rowoff = mul nsw i64 %k2.64, %n64
  %k2row = getelementptr inbounds double, ptr %A, i64 %k2rowoff
  %akj2.ptr = getelementptr inbounds double, ptr %k2row, i64 %j2.64
  %akj2 = load double, ptr %akj2.ptr, align 8
  %mul43 = fmul double %aik2, %akj2
  %cur2 = load double, ptr %aij2.ptr, align 8
  %sub48 = fsub double %cur2, %mul43
  store double %sub48, ptr %aij2.ptr, align 8
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.body34, label %for.inc52.loopexit

for.inc52.loopexit:
  br label %for.inc52

for.inc52:                                        ; preds = %for.inc52.loopexit, %for.body31
  %inc53 = add nsw i32 %j2, 1
  %cmp30 = icmp slt i32 %inc53, %n
  br i1 %cmp30, label %for.body31, label %for.end54.loopexit

for.end54.loopexit:
  br label %for.end54

for.end54:                                        ; preds = %for.end54.loopexit, %for.end28
  %inc56 = add nsw i32 %i, 1
  br label %for.cond

for.end57.loopexit:
  br label %for.end57

for.end57:                                        ; preds = %for.end57.loopexit, %entry
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
