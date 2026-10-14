; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_lu(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %preheader, label %for.end57

preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc55, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc56, %for.inc55 ]
  %cmp = icmp slt i32 %i, %n
  br i1 %cmp, label %for.body, label %for.end57

for.body:                                         ; preds = %for.cond
  %i64 = zext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irow.off
  %cmp3.0 = icmp slt i32 0, %i
  br i1 %cmp3.0, label %for.body4.lr, label %for.end28

for.body4.lr:                                     ; preds = %for.body
  br label %for.body4

for.body4:                                        ; preds = %for.inc26, %for.body4.lr
  %j = phi i32 [ 0, %for.body4.lr ], [ %inc27, %for.inc26 ]
  %j64 = zext i32 %j to i64
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %arrayidx17 = getelementptr inbounds double, ptr %irow, i64 %j64
  %cmp6.0 = icmp slt i32 0, %j
  br i1 %cmp6.0, label %for.body7.lr, label %for.end

for.body7.lr:                                     ; preds = %for.body4
  %init_ij = load double, ptr %arrayidx17, align 8
  br label %for.body7

for.body7:                                        ; preds = %for.body7, %for.body7.lr
  %k = phi i32 [ 0, %for.body7.lr ], [ %inc, %for.body7 ]
  %sum = phi double [ %init_ij, %for.body7.lr ], [ %sub, %for.body7 ]
  %k64 = zext i32 %k to i64
  %arrayidx9 = getelementptr inbounds double, ptr %irow, i64 %k64
  %v_ik = load double, ptr %arrayidx9, align 8
  %arrayidx13 = getelementptr inbounds double, ptr %jrow, i64 %k64
  %v_kj = load double, ptr %arrayidx13, align 8
  %mul = fmul double %v_ik, %v_kj
  %sub = fsub double %sum, %mul
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body7
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body4
  %final_ij = phi double [ %init_ij, %for.body4 ], [ %sub, %for.end.loopexit ]
  %ajj.ptr = getelementptr inbounds double, ptr %jrow, i64 %j64
  %ajj = load double, ptr %ajj.ptr, align 8
  %div = fdiv double %final_ij, %ajj
  store double %div, ptr %arrayidx17, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j, 1
  %cmp3 = icmp slt i32 %inc27, %i
  br i1 %cmp3, label %for.body4, label %for.end28.loopexit

for.end28.loopexit:                               ; preds = %for.inc26
  br label %for.end28

for.end28:                                        ; preds = %for.end28.loopexit, %for.body
  %cmp30.0 = icmp slt i32 %i, %n
  br i1 %cmp30.0, label %for.body31.lr, label %for.end54

for.body31.lr:                                    ; preds = %for.end28
  %cmp33.0 = icmp slt i32 0, %i
  br label %for.body31

for.body31:                                       ; preds = %for.inc52, %for.body31.lr
  %j2 = phi i32 [ %i, %for.body31.lr ], [ %inc53, %for.inc52 ]
  %j2_64 = zext i32 %j2 to i64
  %arrayidx47 = getelementptr inbounds double, ptr %irow, i64 %j2_64
  br i1 %cmp33.0, label %for.body34.lr, label %for.end51

for.body34.lr:                                    ; preds = %for.body31
  %init_ij2 = load double, ptr %arrayidx47, align 8
  br label %for.body34

for.body34:                                       ; preds = %for.body34, %for.body34.lr
  %k2 = phi i32 [ 0, %for.body34.lr ], [ %inc50, %for.body34 ]
  %sum2 = phi double [ %init_ij2, %for.body34.lr ], [ %sub48, %for.body34 ]
  %k2_64 = zext i32 %k2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %irow, i64 %k2_64
  %v_ik2 = load double, ptr %arrayidx38, align 8
  %krow.off2 = mul nsw i64 %k2_64, %n64
  %krow2 = getelementptr inbounds double, ptr %A, i64 %krow.off2
  %arrayidx42 = getelementptr inbounds double, ptr %krow2, i64 %j2_64
  %v_kj2 = load double, ptr %arrayidx42, align 8
  %mul43 = fmul double %v_ik2, %v_kj2
  %sub48 = fsub double %sum2, %mul43
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.body34, label %for.end51.loopexit

for.end51.loopexit:                               ; preds = %for.body34
  br label %for.end51

for.end51:                                         ; preds = %for.end51.loopexit, %for.body31
  %final_ij2 = phi double [ %init_ij2, %for.body31 ], [ %sub48, %for.end51.loopexit ]
  store double %final_ij2, ptr %arrayidx47, align 8
  br label %for.inc52

for.inc52:                                        ; preds = %for.end51
  %inc53 = add nsw i32 %j2, 1
  %cmp30 = icmp slt i32 %inc53, %n
  br i1 %cmp30, label %for.body31, label %for.end54.loopexit

for.end54.loopexit:                               ; preds = %for.inc52
  br label %for.end54

for.end54:                                        ; preds = %for.end54.loopexit, %for.end28
  br label %for.inc55

for.inc55:                                        ; preds = %for.end54
  %inc56 = add nsw i32 %i, 1
  br label %for.cond

for.end57:                                        ; preds = %for.cond, %entry
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
