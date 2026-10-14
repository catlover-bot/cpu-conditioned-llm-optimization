; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp_t = icmp slt i32 0, %tsteps
  br i1 %cmp_t, label %preheader.t, label %for.end37

preheader.t:
  %sub_n1 = sub nsw i32 %n, 1
  %cmp_inner = icmp slt i32 1, %sub_n1
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %preheader.t
  %t = phi i32 [ 0, %preheader.t ], [ %inc36, %for.inc35 ]
  br i1 %cmp_inner, label %for.body4.preheader, label %for.end

for.body4.preheader:
  br label %for.body4

for.body4:                                        ; preds = %for.body4.preheader, %for.body4
  %i = phi i32 [ 1, %for.body4.preheader ], [ %inc, %for.body4 ]
  %idxprom.sub = sext i32 %i to i64
  %im1 = add nsw i32 %i, -1
  %idxprom.m1 = sext i32 %im1 to i64
  %arrayidx.m1 = getelementptr inbounds double, ptr %A, i64 %idxprom.m1
  %v0 = load double, ptr %arrayidx.m1, align 8
  %arrayidx.mid = getelementptr inbounds double, ptr %A, i64 %idxprom.sub
  %v1 = load double, ptr %arrayidx.mid, align 8
  %add8 = fadd double %v0, %v1
  %ip1 = add nsw i32 %i, 1
  %idxprom.p1 = sext i32 %ip1 to i64
  %arrayidx.p1 = getelementptr inbounds double, ptr %A, i64 %idxprom.p1
  %v2 = load double, ptr %arrayidx.p1, align 8
  %add12 = fadd double %add8, %v2
  %mul = fmul double 3.333300e-01, %add12
  %arrayidxB = getelementptr inbounds double, ptr %B, i64 %idxprom.sub
  store double %mul, ptr %arrayidxB, align 8
  %inc = add nsw i32 %i, 1
  %cmp3 = icmp slt i32 %inc, %sub_n1
  br i1 %cmp3, label %for.body4, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.cond
  br i1 %cmp_inner, label %for.body18.preheader, label %for.end34

for.body18.preheader:
  br label %for.body18

for.body18:                                       ; preds = %for.body18.preheader, %for.body18
  %i2 = phi i32 [ 1, %for.body18.preheader ], [ %inc33, %for.body18 ]
  %idxprom2.sub = sext i32 %i2 to i64
  %im1_2 = add nsw i32 %i2, -1
  %idxprom2.m1 = sext i32 %im1_2 to i64
  %arrayidx2.m1 = getelementptr inbounds double, ptr %B, i64 %idxprom2.m1
  %w0 = load double, ptr %arrayidx2.m1, align 8
  %arrayidx2.mid = getelementptr inbounds double, ptr %B, i64 %idxprom2.sub
  %w1 = load double, ptr %arrayidx2.mid, align 8
  %add24 = fadd double %w0, %w1
  %ip1_2 = add nsw i32 %i2, 1
  %idxprom2.p1 = sext i32 %ip1_2 to i64
  %arrayidx2.p1 = getelementptr inbounds double, ptr %B, i64 %idxprom2.p1
  %w2 = load double, ptr %arrayidx2.p1, align 8
  %add28 = fadd double %add24, %w2
  %mul29 = fmul double 3.333300e-01, %add28
  %arrayidxA = getelementptr inbounds double, ptr %A, i64 %idxprom2.sub
  store double %mul29, ptr %arrayidxA, align 8
  %inc33 = add nsw i32 %i2, 1
  %cmp17 = icmp slt i32 %inc33, %sub_n1
  br i1 %cmp17, label %for.body18, label %for.end34.loopexit

for.end34.loopexit:
  br label %for.end34

for.end34:                                        ; preds = %for.end34.loopexit, %for.end
  br label %for.inc35

for.inc35:                                        ; preds = %for.end34
  %inc36 = add nsw i32 %t, 1
  %cmp_t.next = icmp slt i32 %inc36, %tsteps
  br i1 %cmp_t.next, label %for.cond, label %for.end37

for.end37:                                        ; preds = %for.inc35, %entry
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
