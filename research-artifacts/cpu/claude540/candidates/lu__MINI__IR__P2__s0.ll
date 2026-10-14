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
  br label %for.cond

for.cond:                                         ; preds = %for.inc55, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc56, %for.inc55 ]
  %i64 = sext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irow.off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body.preheader, label %for.end28

for.body.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc26, %for.body.preheader
  %j = phi i32 [ 0, %for.body.preheader ], [ %inc27, %for.inc26 ]
  %j64 = sext i32 %j to i64
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body7.preheader, label %for.end

for.body7.preheader:
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %arrayidx17.pre = getelementptr inbounds double, ptr %irow, i64 %j64
  br label %for.body7

for.body7:                                         ; preds = %for.body7, %for.body7.preheader
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %acc = phi double [ 0.0, %for.body7.preheader ], [ %sub, %for.body7 ]
  %k64 = sext i32 %k to i64
  %arrayidx9 = getelementptr inbounds double, ptr %irow, i64 %k64
  %v1 = load double, ptr %arrayidx9, align 8
  %arrayidx13 = getelementptr inbounds double, ptr %jrow, i64 %k64
  %v2 = load double, ptr %arrayidx13, align 8
  %mul = fmul double %v1, %v2
  %orig = load double, ptr %arrayidx17.pre, align 8
  %sub = fsub double %orig, %mul
  store double %sub, ptr %arrayidx17.pre, align 8
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %arrayidx21 = getelementptr inbounds double, ptr %irow, i64 %j64
  %diag = load double, ptr %arrayidx21, align 8
  %arrayidx25 = getelementptr inbounds double, ptr %irow, i64 %j64
  %numer = load double, ptr %arrayidx25, align 8
  %div = fdiv double %numer, %diag
  store double %div, ptr %arrayidx25, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j, 1
  %cmp2 = icmp slt i32 %inc27, %i
  br i1 %cmp2, label %for.body, label %for.end28.loopexit

for.end28.loopexit:
  br label %for.end28

for.end28:                                        ; preds = %for.end28.loopexit, %for.cond
  %cmp.j2 = icmp slt i32 %i, %n
  br i1 %cmp.j2, label %for.body31.preheader, label %for.end54

for.body31.preheader:
  br label %for.body31

for.body31:                                        ; preds = %for.inc52, %for.body31.preheader
  %j2 = phi i32 [ %i, %for.body31.preheader ], [ %inc53, %for.inc52 ]
  %j2.64 = sext i32 %j2 to i64
  %cmp.k2 = icmp sgt i32 %i, 0
  br i1 %cmp.k2, label %for.body34.preheader, label %for.end51

for.body34.preheader:
  %arrayidx47.pre = getelementptr inbounds double, ptr %irow, i64 %j2.64
  br label %for.body34

for.body34:                                        ; preds = %for.body34, %for.body34.preheader
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc50, %for.body34 ]
  %k2.64 = sext i32 %k2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %irow, i64 %k2.64
  %v3 = load double, ptr %arrayidx38, align 8
  %krow.off = mul nsw i64 %k2.64, %n64
  %krow = getelementptr inbounds double, ptr %A, i64 %krow.off
  %arrayidx42 = getelementptr inbounds double, ptr %krow, i64 %j2.64
  %v4 = load double, ptr %arrayidx42, align 8
  %mul43 = fmul double %v3, %v4
  %orig2 = load double, ptr %arrayidx47.pre, align 8
  %sub48 = fsub double %orig2, %mul43
  store double %sub48, ptr %arrayidx47.pre, align 8
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.body34, label %for.end51.loopexit

for.end51.loopexit:
  br label %for.end51

for.end51:                                        ; preds = %for.end51.loopexit, %for.body31
  br label %for.inc52

for.inc52:                                        ; preds = %for.end51
  %inc53 = add nsw i32 %j2, 1
  %cmp30 = icmp slt i32 %inc53, %n
  br i1 %cmp30, label %for.body31, label %for.end54.loopexit

for.end54.loopexit:
  br label %for.end54

for.end54:                                        ; preds = %for.end54.loopexit, %for.end28
  br label %for.inc55

for.inc55:                                        ; preds = %for.end54
  %inc56 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc56, %n
  br i1 %cmp, label %for.cond, label %for.end57.loopexit

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
