; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_cholesky(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end59

preheader:
  %n64 = zext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc57, %preheader
  %i.02 = phi i32 [ 0, %preheader ], [ %inc58, %for.inc57 ]
  %idxprom.i = sext i32 %i.02 to i64
  %irow.off = mul nsw i64 %idxprom.i, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irow.off
  %cmp3.z = icmp sgt i32 %i.02, 0
  br i1 %cmp3.z, label %for.body4.ph, label %for.end28

for.body4.ph:
  br label %for.body4

for.body4:                                        ; preds = %for.inc26, %for.body4.ph
  %j.01 = phi i32 [ 0, %for.body4.ph ], [ %inc27, %for.inc26 ]
  %idxprom10 = sext i32 %j.01 to i64
  %jrow.off = mul nsw i64 %idxprom10, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %cmp6.z = icmp sgt i32 %j.01, 0
  br i1 %cmp6.z, label %for.body7.ph, label %for.end

for.body7.ph:
  %j.i64 = zext i32 %j.01 to i64
  br label %for.body7

for.body7:                                        ; preds = %for.body7, %for.body7.ph
  %k.03 = phi i64 [ 0, %for.body7.ph ], [ %k.next, %for.body7 ]
  %arrayidx9 = getelementptr inbounds double, ptr %irow, i64 %k.03
  %v1 = load double, ptr %arrayidx9, align 8
  %arrayidx13 = getelementptr inbounds double, ptr %jrow, i64 %k.03
  %v2 = load double, ptr %arrayidx13, align 8
  %mul = fmul double %v1, %v2
  %arrayidx17 = getelementptr inbounds double, ptr %irow, i64 %idxprom10
  %v3 = load double, ptr %arrayidx17, align 8
  %sub = fsub double %v3, %mul
  store double %sub, ptr %arrayidx17, align 8
  %k.next = add nuw nsw i64 %k.03, 1
  %cmp6.loop = icmp slt i64 %k.next, %j.i64
  br i1 %cmp6.loop, label %for.body7, label %for.end

for.end:                                          ; preds = %for.body7, %for.body4
  %arrayidx21 = getelementptr inbounds double, ptr %jrow, i64 %idxprom10
  %vd = load double, ptr %arrayidx21, align 8
  %arrayidx25 = getelementptr inbounds double, ptr %irow, i64 %idxprom10
  %vn = load double, ptr %arrayidx25, align 8
  %div = fdiv double %vn, %vd
  store double %div, ptr %arrayidx25, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j.01, 1
  %cmp3.loop = icmp slt i32 %inc27, %i.02
  br i1 %cmp3.loop, label %for.body4, label %for.end28

for.end28:                                        ; preds = %for.inc26, %for.body
  br i1 %cmp3.z, label %for.body31.ph, label %for.end48

for.body31.ph:
  %i.i64 = zext i32 %i.02 to i64
  br label %for.body31

for.body31:                                       ; preds = %for.body31, %for.body31.ph
  %k2.03 = phi i64 [ 0, %for.body31.ph ], [ %k2.next, %for.body31 ]
  %arrayidx35 = getelementptr inbounds double, ptr %irow, i64 %k2.03
  %w1 = load double, ptr %arrayidx35, align 8
  %mul40 = fmul double %w1, %w1
  %arrayidx44 = getelementptr inbounds double, ptr %irow, i64 %idxprom.i
  %w3 = load double, ptr %arrayidx44, align 8
  %sub45 = fsub double %w3, %mul40
  store double %sub45, ptr %arrayidx44, align 8
  %k2.next = add nuw nsw i64 %k2.03, 1
  %cmp30.loop = icmp slt i64 %k2.next, %i.i64
  br i1 %cmp30.loop, label %for.body31, label %for.end48

for.end48:                                        ; preds = %for.body31, %for.end28
  %arrayidx52 = getelementptr inbounds double, ptr %irow, i64 %idxprom.i
  %diagv = load double, ptr %arrayidx52, align 8
  %call = call double @sqrt(double noundef %diagv) #2
  store double %call, ptr %arrayidx52, align 8
  br label %for.inc57

for.inc57:                                        ; preds = %for.end48
  %inc58 = add nsw i32 %i.02, 1
  %cmp.loop = icmp slt i32 %inc58, %n
  br i1 %cmp.loop, label %for.body, label %for.end59

for.end59:                                        ; preds = %for.inc57, %entry
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
