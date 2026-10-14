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
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc55, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc56, %for.inc55 ]
  %i64 = sext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irow.off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body4.preheader, label %for.end28

for.body4.preheader:
  br label %for.body4

for.body4:                                        ; preds = %for.end, %for.body4.preheader
  %j = phi i32 [ 0, %for.body4.preheader ], [ %inc27, %for.end ]
  %j64 = sext i32 %j to i64
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %ij.ptr = getelementptr inbounds double, ptr %irow, i64 %j64
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body7.preheader, label %for.end

for.body7.preheader:
  br label %for.body7

for.body7:                                        ; preds = %for.body7, %for.body7.preheader
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc.k, %for.body7 ]
  %acc = phi double [ 0.0, %for.body7.preheader ], [ %sub, %for.body7 ]
  %k64 = sext i32 %k to i64
  %ik.ptr = getelementptr inbounds double, ptr %irow, i64 %k64
  %ik.val = load double, ptr %ik.ptr, align 8
  %krow.off = mul nsw i64 %k64, %n64
  %krow = getelementptr inbounds double, ptr %A, i64 %krow.off
  %kj.ptr = getelementptr inbounds double, ptr %krow, i64 %j64
  %kj.val = load double, ptr %kj.ptr, align 8
  %mul = fmul double %ik.val, %kj.val
  br label %dummy.unused
dummy.unused:
  br label %after.dummy
after.dummy:
  %inc.k = add nsw i32 %k, 1
  %cmp.k = icmp slt i32 %inc.k, %j
  %ij.load = load double, ptr %ij.ptr, align 8
  %sub = fsub double %ij.load, %mul
  store double %sub, ptr %ij.ptr, align 8
  br i1 %cmp.k, label %for.body7, label %for.end

for.end:                                          ; preds = %after.dummy, %for.body4
  %jj.ptr = getelementptr inbounds double, ptr %jrow, i64 %j64
  %jj.val = load double, ptr %jj.ptr, align 8
  %ij.val2 = load double, ptr %ij.ptr, align 8
  %div = fdiv double %ij.val2, %jj.val
  store double %div, ptr %ij.ptr, align 8
  %inc27 = add nsw i32 %j, 1
  %cmp.j = icmp slt i32 %inc27, %i
  br i1 %cmp.j, label %for.body4, label %for.end28

for.end28:                                        ; preds = %for.end, %for.body
  %cmp.j2 = icmp slt i32 %i, %n
  br i1 %cmp.j2, label %for.body31.preheader, label %for.end54

for.body31.preheader:
  br label %for.body31

for.body31:                                       ; preds = %for.inc52, %for.body31.preheader
  %j2 = phi i32 [ %i, %for.body31.preheader ], [ %inc53, %for.inc52 ]
  %j2.64 = sext i32 %j2 to i64
  %ij2.ptr = getelementptr inbounds double, ptr %irow, i64 %j2.64
  %cmp.k2.1 = icmp sgt i32 %i, 0
  br i1 %cmp.k2.1, label %for.body34.preheader, label %for.inc52

for.body34.preheader:
  br label %for.body34

for.body34:                                       ; preds = %for.body34, %for.body34.preheader
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc.k2, %for.body34 ]
  %k2.64 = sext i32 %k2 to i64
  %ik2.ptr = getelementptr inbounds double, ptr %irow, i64 %k2.64
  %ik2.val = load double, ptr %ik2.ptr, align 8
  %k2row.off = mul nsw i64 %k2.64, %n64
  %k2row = getelementptr inbounds double, ptr %A, i64 %k2row.off
  %k2j2.ptr = getelementptr inbounds double, ptr %k2row, i64 %j2.64
  %k2j2.val = load double, ptr %k2j2.ptr, align 8
  %mul43 = fmul double %ik2.val, %k2j2.val
  %ij2.load = load double, ptr %ij2.ptr, align 8
  %sub48 = fsub double %ij2.load, %mul43
  store double %sub48, ptr %ij2.ptr, align 8
  %inc.k2 = add nsw i32 %k2, 1
  %cmp.k2 = icmp slt i32 %inc.k2, %i
  br i1 %cmp.k2, label %for.body34, label %for.inc52

for.inc52:                                        ; preds = %for.body34, %for.body31
  %inc53 = add nsw i32 %j2, 1
  %cmp.j3 = icmp slt i32 %inc53, %n
  br i1 %cmp.j3, label %for.body31, label %for.end54

for.end54:                                        ; preds = %for.inc52, %for.end28
  %inc56 = add nsw i32 %i, 1
  %cmp.i = icmp slt i32 %inc56, %n
  br i1 %cmp.i, label %for.body, label %for.end57.loopexit

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
