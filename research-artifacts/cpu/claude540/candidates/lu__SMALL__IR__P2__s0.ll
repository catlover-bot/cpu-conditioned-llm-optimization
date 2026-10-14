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
  %rowi.off = mul nsw i64 %i64, %n64
  %rowi = getelementptr inbounds double, ptr %A, i64 %rowi.off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body2.preheader, label %for.end28

for.body2.preheader:
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc26, %for.body2.preheader
  %j = phi i32 [ 0, %for.body2.preheader ], [ %inc27, %for.inc26 ]
  %j64 = sext i32 %j to i64
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body7.preheader, label %for.end

for.body7.preheader:
  %Aij.ptr.pre = getelementptr inbounds double, ptr %rowi, i64 %j64
  br label %for.body7

for.body7:                                        ; preds = %for.body7, %for.body7.preheader
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %acc = phi double [ 0.0, %for.body7.preheader ], [ %sub, %for.body7 ]
  %k64 = sext i32 %k to i64
  %Aik.ptr = getelementptr inbounds double, ptr %rowi, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %rowk.off = mul nsw i64 %k64, %n64
  %rowk = getelementptr inbounds double, ptr %A, i64 %rowk.off
  %Akj.ptr = getelementptr inbounds double, ptr %rowk, i64 %j64
  %Akj = load double, ptr %Akj.ptr, align 8
  %mul = fmul double %Aik, %Akj
  %sub = fsub double %acc, %mul
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.body7.exit

for.body7.exit:
  %Aij.final.k = load double, ptr %Aij.ptr.pre, align 8
  %sub.final.k = fadd double %Aij.final.k, %sub
  store double %sub.final.k, ptr %Aij.ptr.pre, align 8
  br label %for.end

for.end:                                          ; preds = %for.body7.exit, %for.cond2
  %Ajj.off = mul nsw i64 %j64, %n64
  %Ajj.row = getelementptr inbounds double, ptr %A, i64 %Ajj.off
  %Ajj.ptr = getelementptr inbounds double, ptr %Ajj.row, i64 %j64
  %Ajj = load double, ptr %Ajj.ptr, align 8
  %Aij.ptr = getelementptr inbounds double, ptr %rowi, i64 %j64
  %Aij = load double, ptr %Aij.ptr, align 8
  %div = fdiv double %Aij, %Ajj
  store double %div, ptr %Aij.ptr, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j, 1
  %cmp3 = icmp slt i32 %inc27, %i
  br i1 %cmp3, label %for.cond2, label %for.end28.loopexit

for.end28.loopexit:
  br label %for.end28

for.end28:                                        ; preds = %for.end28.loopexit, %for.cond
  %cmp.j2 = icmp slt i32 %i, %n
  br i1 %cmp.j2, label %for.body31.preheader, label %for.end54

for.body31.preheader:
  br label %for.cond29

for.cond29:                                       ; preds = %for.inc52, %for.body31.preheader
  %j2 = phi i32 [ %i, %for.body31.preheader ], [ %inc53, %for.inc52 ]
  %j2.64 = sext i32 %j2 to i64
  %cmp.k2 = icmp sgt i32 %i, 0
  br i1 %cmp.k2, label %for.body34.preheader, label %for.inc52

for.body34.preheader:
  %Aij2.ptr.pre = getelementptr inbounds double, ptr %rowi, i64 %j2.64
  br label %for.body34

for.body34:                                       ; preds = %for.body34, %for.body34.preheader
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc50, %for.body34 ]
  %acc2 = phi double [ 0.0, %for.body34.preheader ], [ %sub48, %for.body34 ]
  %k2.64 = sext i32 %k2 to i64
  %Aik2.ptr = getelementptr inbounds double, ptr %rowi, i64 %k2.64
  %Aik2 = load double, ptr %Aik2.ptr, align 8
  %rowk2.off = mul nsw i64 %k2.64, %n64
  %rowk2 = getelementptr inbounds double, ptr %A, i64 %rowk2.off
  %Akj2.ptr = getelementptr inbounds double, ptr %rowk2, i64 %j2.64
  %Akj2 = load double, ptr %Akj2.ptr, align 8
  %mul43 = fmul double %Aik2, %Akj2
  %sub48 = fsub double %acc2, %mul43
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.body34, label %for.body34.exit

for.body34.exit:
  %Aij2.final = load double, ptr %Aij2.ptr.pre, align 8
  %sub48.final = fadd double %Aij2.final, %sub48
  store double %sub48.final, ptr %Aij2.ptr.pre, align 8
  br label %for.inc52

for.inc52:                                        ; preds = %for.body34.exit, %for.cond29
  %inc53 = add nsw i32 %j2, 1
  %cmp30 = icmp slt i32 %inc53, %n
  br i1 %cmp30, label %for.cond29, label %for.end54.loopexit

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
