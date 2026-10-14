; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp slt i32 1, %n
  br i1 %cmp.n, label %check.t, label %for.end37

check.t:
  %cmp.t0 = icmp slt i32 0, %tsteps
  br i1 %cmp.t0, label %for.cond.preheader, label %for.end37

for.cond.preheader:
  %sub.n = sub nsw i32 %n, 1
  %trip.count64 = zext i32 %sub.n to i64
  br label %for.body.outer

for.body.outer:
  %t.03 = phi i32 [ 0, %for.cond.preheader ], [ %inc36, %for.inc35 ]
  br label %for.body4.loop

for.body4.loop:
  %i.02 = phi i64 [ 1, %for.body.outer ], [ %inc.i, %for.body4.loop ]
  %im1 = add nsw i64 %i.02, -1
  %a.im1.ptr = getelementptr inbounds double, ptr %A, i64 %im1
  %a.im1 = load double, ptr %a.im1.ptr, align 8
  %a.i.ptr = getelementptr inbounds double, ptr %A, i64 %i.02
  %a.i = load double, ptr %a.i.ptr, align 8
  %add8 = fadd double %a.im1, %a.i
  %ip1 = add nsw i64 %i.02, 1
  %a.ip1.ptr = getelementptr inbounds double, ptr %A, i64 %ip1
  %a.ip1 = load double, ptr %a.ip1.ptr, align 8
  %add12 = fadd double %add8, %a.ip1
  %mul = fmul double 3.333300e-01, %add12
  %b.i.ptr = getelementptr inbounds double, ptr %B, i64 %i.02
  store double %mul, ptr %b.i.ptr, align 8
  %inc.i = add nsw i64 %i.02, 1
  %cmp3 = icmp slt i64 %inc.i, %trip.count64
  br i1 %cmp3, label %for.body4.loop, label %for.body18.preheader

for.body18.preheader:
  br label %for.body18.loop

for.body18.loop:
  %i2.02 = phi i64 [ 1, %for.body18.preheader ], [ %inc2.i, %for.body18.loop ]
  %b.im1.ptr = getelementptr inbounds double, ptr %B, i64 %i2.02
  %im1b = add nsw i64 %i2.02, -1
  %b.im1.ptr2 = getelementptr inbounds double, ptr %B, i64 %im1b
  %b.im1 = load double, ptr %b.im1.ptr2, align 8
  %b.i = load double, ptr %b.im1.ptr, align 8
  %add24 = fadd double %b.im1, %b.i
  %ip1b = add nsw i64 %i2.02, 1
  %b.ip1.ptr = getelementptr inbounds double, ptr %B, i64 %ip1b
  %b.ip1 = load double, ptr %b.ip1.ptr, align 8
  %add28 = fadd double %add24, %b.ip1
  %mul29 = fmul double 3.333300e-01, %add28
  %a.i2.ptr = getelementptr inbounds double, ptr %A, i64 %i2.02
  store double %mul29, ptr %a.i2.ptr, align 8
  %inc2.i = add nsw i64 %i2.02, 1
  %cmp17 = icmp slt i64 %inc2.i, %trip.count64
  br i1 %cmp17, label %for.body18.loop, label %for.inc35

for.inc35:
  %inc36 = add nsw i32 %t.03, 1
  %cmp.t = icmp slt i32 %inc36, %tsteps
  br i1 %cmp.t, label %for.body.outer, label %for.end37

for.end37:
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
