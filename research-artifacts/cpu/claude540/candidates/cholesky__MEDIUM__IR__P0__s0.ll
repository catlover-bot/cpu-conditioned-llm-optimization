; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_cholesky(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end59

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc57, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc58, %for.inc57 ]
  %i64 = sext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds double, ptr %A, i64 %irow.off
  %cmp3.entry = icmp slt i32 0, %i
  br i1 %cmp3.entry, label %for.body4.preheader, label %for.end28

for.body4.preheader:
  br label %for.body4

for.body4:                                        ; preds = %for.inc26, %for.body4.preheader
  %j = phi i32 [ 0, %for.body4.preheader ], [ %inc27, %for.inc26 ]
  %j64 = sext i32 %j to i64
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %cmp6.entry = icmp slt i32 0, %j
  br i1 %cmp6.entry, label %for.body7.preheader, label %for.end

for.body7.preheader:
  br label %for.body7

for.body7:                                        ; preds = %for.body7, %for.body7.preheader
  %k = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %k64 = sext i32 %k to i64
  %arrayidx9 = getelementptr inbounds double, ptr %irow, i64 %k64
  %v1 = load double, ptr %arrayidx9, align 8
  %arrayidx13 = getelementptr inbounds double, ptr %jrow, i64 %k64
  %v2 = load double, ptr %arrayidx13, align 8
  %mul = fmul double %v1, %v2
  %arrayidx17 = getelementptr inbounds double, ptr %irow, i64 %j64
  %v3 = load double, ptr %arrayidx17, align 8
  %sub = fsub double %v3, %mul
  store double %sub, ptr %arrayidx17, align 8
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.body7, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body4
  %arrayidx21 = getelementptr inbounds double, ptr %jrow, i64 %j64
  %jj = load double, ptr %arrayidx21, align 8
  %arrayidx25 = getelementptr inbounds double, ptr %irow, i64 %j64
  %ij = load double, ptr %arrayidx25, align 8
  %div = fdiv double %ij, %jj
  store double %div, ptr %arrayidx25, align 8
  br label %for.inc26

for.inc26:                                        ; preds = %for.end
  %inc27 = add nsw i32 %j, 1
  %cmp3 = icmp slt i32 %inc27, %i
  br i1 %cmp3, label %for.body4, label %for.end28.loopexit, !llvm.loop !8

for.end28.loopexit:
  br label %for.end28

for.end28:                                        ; preds = %for.end28.loopexit, %for.body
  %cmp30.entry = icmp slt i32 0, %i
  br i1 %cmp30.entry, label %for.body31.preheader, label %for.end48

for.body31.preheader:
  br label %for.body31

for.body31:                                       ; preds = %for.body31, %for.body31.preheader
  %k2 = phi i32 [ 0, %for.body31.preheader ], [ %inc47, %for.body31 ]
  %k2_64 = sext i32 %k2 to i64
  %arrayidx35 = getelementptr inbounds double, ptr %irow, i64 %k2_64
  %vik = load double, ptr %arrayidx35, align 8
  %mul40 = fmul double %vik, %vik
  %arrayidx44 = getelementptr inbounds double, ptr %irow, i64 %i64
  %vii = load double, ptr %arrayidx44, align 8
  %sub45 = fsub double %vii, %mul40
  store double %sub45, ptr %arrayidx44, align 8
  %inc47 = add nsw i32 %k2, 1
  %cmp30 = icmp slt i32 %inc47, %i
  br i1 %cmp30, label %for.body31, label %for.end48.loopexit, !llvm.loop !9

for.end48.loopexit:
  br label %for.end48

for.end48:                                        ; preds = %for.end48.loopexit, %for.end28
  %arrayidx52 = getelementptr inbounds double, ptr %irow, i64 %i64
  %diagv = load double, ptr %arrayidx52, align 8
  %call = call double @sqrt(double noundef %diagv) #2
  store double %call, ptr %arrayidx52, align 8
  br label %for.inc57

for.inc57:                                        ; preds = %for.end48
  %inc58 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc58, %n
  br i1 %cmp, label %for.body, label %for.end59.loopexit, !llvm.loop !10

for.end59.loopexit:
  br label %for.end59

for.end59:                                         ; preds = %for.end59.loopexit, %entry
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
