; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end37

preheader:
  %n64 = sext i32 %n to i64
  %upper64 = add nsw i64 %n64, -1
  %tsteps64 = zext i32 %tsteps to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %preheader
  %t.iv = phi i64 [ 0, %preheader ], [ %inc36, %for.inc35 ]
  br label %for.body4

for.body4:                                        ; preds = %for.cond, %for.body4
  %i.iv = phi i64 [ 1, %for.cond ], [ %inc, %for.body4 ]
  %im1 = add nsw i64 %i.iv, -1
  %arrayidx = getelementptr inbounds double, ptr %A, i64 %im1
  %v0 = load double, ptr %arrayidx, align 8
  %arrayidx7 = getelementptr inbounds double, ptr %A, i64 %i.iv
  %v1 = load double, ptr %arrayidx7, align 8
  %add8 = fadd double %v0, %v1
  %ip1 = add nsw i64 %i.iv, 1
  %arrayidx11 = getelementptr inbounds double, ptr %A, i64 %ip1
  %v2 = load double, ptr %arrayidx11, align 8
  %add12 = fadd double %add8, %v2
  %mul = fmul double 3.333300e-01, %add12
  %arrayidx14 = getelementptr inbounds double, ptr %B, i64 %i.iv
  store double %mul, ptr %arrayidx14, align 8
  %inc = add nsw i64 %i.iv, 1
  %cmp3 = icmp slt i64 %inc, %upper64
  br i1 %cmp3, label %for.body4, label %for.end

for.end:                                          ; preds = %for.body4
  br label %for.body18

for.body18:                                       ; preds = %for.end, %for.body18
  %j.iv = phi i64 [ 1, %for.end ], [ %inc33, %for.body18 ]
  %jm1 = add nsw i64 %j.iv, -1
  %arrayidx21 = getelementptr inbounds double, ptr %B, i64 %jm1
  %w0 = load double, ptr %arrayidx21, align 8
  %arrayidx23 = getelementptr inbounds double, ptr %B, i64 %j.iv
  %w1 = load double, ptr %arrayidx23, align 8
  %add24 = fadd double %w0, %w1
  %jp1 = add nsw i64 %j.iv, 1
  %arrayidx27 = getelementptr inbounds double, ptr %B, i64 %jp1
  %w2 = load double, ptr %arrayidx27, align 8
  %add28 = fadd double %add24, %w2
  %mul29 = fmul double 3.333300e-01, %add28
  %arrayidx31 = getelementptr inbounds double, ptr %A, i64 %j.iv
  store double %mul29, ptr %arrayidx31, align 8
  %inc33 = add nsw i64 %j.iv, 1
  %cmp17 = icmp slt i64 %inc33, %upper64
  br i1 %cmp17, label %for.body18, label %for.end34

for.end34:                                        ; preds = %for.body18
  br label %for.inc35

for.inc35:                                        ; preds = %for.end34
  %inc36 = add nsw i64 %t.iv, 1
  %cmp = icmp slt i64 %inc36, %tsteps64
  br i1 %cmp, label %for.cond, label %for.end37.loopexit

for.end37.loopexit:                               ; preds = %for.inc35
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
