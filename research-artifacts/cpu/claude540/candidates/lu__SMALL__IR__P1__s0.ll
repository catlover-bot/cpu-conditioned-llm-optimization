; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_lu(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end57

outer.preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc55, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc56, %for.inc55 ]
  %i64 = zext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow.ptr = getelementptr inbounds double, ptr %A, i64 %irow.off
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc26, %for.cond
  %j = phi i32 [ 0, %for.cond ], [ %inc27, %for.inc26 ]
  %cmp3 = icmp slt i32 %j, %i
  br i1 %cmp3, label %for.body4, label %for.end28

for.body4:                                        ; preds = %for.cond2
  %j64 = zext i32 %j to i64
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow.ptr = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %aij.ptr = getelementptr inbounds double, ptr %irow.ptr, i64 %j64
  %cmp6.pre = icmp slt i32 0, %j
  br i1 %cmp6.pre, label %for.body7.preheader, label %for.end

for.body7.preheader:
  br label %for.body7

for.body7:                                        ; preds = %for.body7.preheader, %for.body7
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %sum = phi double [ 0.0, %for.body7.preheader ], [ %sub, %for.body7 ]
  %k64 = zext i32 %k to i64
  %aik.ptr = getelementptr inbounds double, ptr %irow.ptr, i64 %k64
  %aik = load double, ptr %aik.ptr, align 8
  %akj.ptr = getelementptr inbounds double, ptr %jrow.ptr, i64 %k64
  %akj = load double, ptr %akj.ptr, align 8
  %mul = fmul double %aik, %akj
  %aij0 = load double, ptr %aij.ptr, align 8
  %sub = fsub double %aij0, %mul
  store double %sub, ptr %aij.ptr, align 8
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body4
  %ajj.ptr = getelementptr inbounds double, ptr %jrow.ptr, i64 %j64
  %ajj = load double, ptr %ajj.ptr, align 8
  %aij1 = load double, ptr %aij.ptr, align 8
  %div = fdiv double %aij1, %ajj
  store double %div, ptr %aij.ptr, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j, 1
  br label %for.cond2, !llvm.loop !8

for.end28:                                        ; preds = %for.cond2
  br label %for.cond29

for.cond29:                                       ; preds = %for.inc52, %for.end28
  %j2 = phi i32 [ %i, %for.end28 ], [ %inc53, %for.inc52 ]
  %cmp30 = icmp slt i32 %j2, %n
  br i1 %cmp30, label %for.body31, label %for.end54

for.body31:                                       ; preds = %for.cond29
  %j2_64 = zext i32 %j2 to i64
  %aij2.ptr = getelementptr inbounds double, ptr %irow.ptr, i64 %j2_64
  %cmp33.pre = icmp slt i32 0, %i
  br i1 %cmp33.pre, label %for.body34.preheader, label %for.inc52

for.body34.preheader:
  br label %for.body34

for.body34:                                       ; preds = %for.body34.preheader, %for.body34
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc50, %for.body34 ]
  %k2_64 = zext i32 %k2 to i64
  %aik2.ptr = getelementptr inbounds double, ptr %irow.ptr, i64 %k2_64
  %aik2 = load double, ptr %aik2.ptr, align 8
  %krow.off = mul nsw i64 %k2_64, %n64
  %krow.ptr = getelementptr inbounds double, ptr %A, i64 %krow.off
  %akj2.ptr = getelementptr inbounds double, ptr %krow.ptr, i64 %j2_64
  %akj2 = load double, ptr %akj2.ptr, align 8
  %mul43 = fmul double %aik2, %akj2
  %aij2.0 = load double, ptr %aij2.ptr, align 8
  %sub48 = fsub double %aij2.0, %mul43
  store double %sub48, ptr %aij2.ptr, align 8
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.body34, label %for.inc52.loopexit

for.inc52.loopexit:
  br label %for.inc52

for.inc52:                                        ; preds = %for.inc52.loopexit, %for.body31
  %inc53 = add nsw i32 %j2, 1
  br label %for.cond29, !llvm.loop !10

for.end54:                                        ; preds = %for.cond29
  br label %for.inc55

for.inc55:                                        ; preds = %for.end54
  %inc56 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc56, %n
  br i1 %cmp, label %for.cond, label %for.end57.loopexit, !llvm.loop !11

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
