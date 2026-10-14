; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.t = icmp slt i32 0, %tsteps
  br i1 %cmp.t, label %for.t.preheader, label %for.end37

for.t.preheader:
  %sub1 = sub nsw i32 %n, 1
  %cmp.inner = icmp slt i32 1, %sub1
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %for.t.preheader
  %t.09 = phi i32 [ 0, %for.t.preheader ], [ %inc36, %for.inc35 ]
  br i1 %cmp.inner, label %for.body4.preheader, label %for.end

for.body4.preheader:
  br label %for.body4

for.body4:                                        ; preds = %for.body4.preheader, %for.body4
  %i.08 = phi i32 [ 1, %for.body4.preheader ], [ %inc, %for.body4 ]
  %idxprom.im1 = sext i32 %i.08 to i64
  %arrayidx.im1 = getelementptr inbounds double, ptr %A, i64 %idxprom.im1
  %v.im1 = load double, ptr %arrayidx.im1, align 8
  %idxprom.i = add nsw i64 %idxprom.im1, 1
  %arrayidx.i = getelementptr inbounds double, ptr %A, i64 %idxprom.i
  %v.i = load double, ptr %arrayidx.i, align 8
  %add8 = fadd double %v.im1, %v.i
  %idxprom.ip1 = add nsw i64 %idxprom.im1, 2
  %arrayidx.ip1 = getelementptr inbounds double, ptr %A, i64 %idxprom.ip1
  %v.ip1 = load double, ptr %arrayidx.ip1, align 8
  %add12 = fadd double %add8, %v.ip1
  %mul = fmul double 3.333300e-01, %add12
  %arrayidx14 = getelementptr inbounds double, ptr %B, i64 %idxprom.i
  store double %mul, ptr %arrayidx14, align 8
  %inc = add nsw i32 %i.08, 1
  %cmp3 = icmp slt i32 %inc, %sub1
  br i1 %cmp3, label %for.body4, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.cond
  br i1 %cmp.inner, label %for.body18.preheader, label %for.end34

for.body18.preheader:
  br label %for.body18

for.body18:                                       ; preds = %for.body18.preheader, %for.body18
  %i2.08 = phi i32 [ 1, %for.body18.preheader ], [ %inc33, %for.body18 ]
  %idxprom20.im1 = sext i32 %i2.08 to i64
  %arrayidx21 = getelementptr inbounds double, ptr %B, i64 %idxprom20.im1
  %v2.im1 = load double, ptr %arrayidx21, align 8
  %idxprom20.i = add nsw i64 %idxprom20.im1, 1
  %arrayidx23 = getelementptr inbounds double, ptr %B, i64 %idxprom20.i
  %v2.i = load double, ptr %arrayidx23, align 8
  %add24 = fadd double %v2.im1, %v2.i
  %idxprom20.ip1 = add nsw i64 %idxprom20.im1, 2
  %arrayidx27 = getelementptr inbounds double, ptr %B, i64 %idxprom20.ip1
  %v2.ip1 = load double, ptr %arrayidx27, align 8
  %add28 = fadd double %add24, %v2.ip1
  %mul29 = fmul double 3.333300e-01, %add28
  %arrayidx31 = getelementptr inbounds double, ptr %A, i64 %idxprom20.i
  store double %mul29, ptr %arrayidx31, align 8
  %inc33 = add nsw i32 %i2.08, 1
  %cmp17 = icmp slt i32 %inc33, %sub1
  br i1 %cmp17, label %for.body18, label %for.end34.loopexit, !llvm.loop !8

for.end34.loopexit:
  br label %for.end34

for.end34:                                        ; preds = %for.end34.loopexit, %for.end
  br label %for.inc35

for.inc35:                                        ; preds = %for.end34
  %inc36 = add nsw i32 %t.09, 1
  %cmp = icmp slt i32 %inc36, %tsteps
  br i1 %cmp, label %for.cond, label %for.end37.loopexit, !llvm.loop !9

for.end37.loopexit:
  br label %for.end37

for.end37:                                        ; preds = %for.end37.loopexit, %entry
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
