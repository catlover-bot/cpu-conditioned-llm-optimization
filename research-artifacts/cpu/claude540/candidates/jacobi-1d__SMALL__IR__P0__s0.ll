; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp_outer = icmp slt i32 0, %tsteps
  br i1 %cmp_outer, label %preheader, label %for.end37

preheader:
  %sub_n1 = sub nsw i32 %n, 1
  %inner_cond = icmp slt i32 1, %sub_n1
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc36, %for.inc35 ]
  br i1 %inner_cond, label %loop1.preheader, label %for.end

loop1.preheader:
  br label %loop1.body

loop1.body:                                       ; preds = %loop1.body, %loop1.preheader
  %i1 = phi i32 [ 1, %loop1.preheader ], [ %inc1, %loop1.body ]
  %idxprom.im1 = sext i32 %i1 to i64
  %sub5 = add nsw i64 %idxprom.im1, -1
  %arrayidx.im1 = getelementptr inbounds double, ptr %A, i64 %sub5
  %v.im1 = load double, ptr %arrayidx.im1, align 8
  %arrayidx.i = getelementptr inbounds double, ptr %A, i64 %idxprom.im1
  %v.i = load double, ptr %arrayidx.i, align 8
  %add8 = fadd double %v.im1, %v.i
  %idxprom.ip1 = add nsw i64 %idxprom.im1, 1
  %arrayidx.ip1 = getelementptr inbounds double, ptr %A, i64 %idxprom.ip1
  %v.ip1 = load double, ptr %arrayidx.ip1, align 8
  %add12 = fadd double %add8, %v.ip1
  %mul = fmul double 3.333300e-01, %add12
  %arrayidxB = getelementptr inbounds double, ptr %B, i64 %idxprom.im1
  store double %mul, ptr %arrayidxB, align 8
  %inc1 = add nsw i32 %i1, 1
  %cmp3.next = icmp slt i32 %inc1, %sub_n1
  br i1 %cmp3.next, label %loop1.body, label %for.end

for.end:                                          ; preds = %loop1.body, %for.cond
  br i1 %inner_cond, label %loop2.preheader, label %for.end34

loop2.preheader:
  br label %loop2.body

loop2.body:                                       ; preds = %loop2.body, %loop2.preheader
  %i2 = phi i32 [ 1, %loop2.preheader ], [ %inc2, %loop2.body ]
  %idxprom2.im1 = sext i32 %i2 to i64
  %sub19 = add nsw i64 %idxprom2.im1, -1
  %arrayidxB.im1 = getelementptr inbounds double, ptr %B, i64 %sub19
  %vB.im1 = load double, ptr %arrayidxB.im1, align 8
  %arrayidxB.i = getelementptr inbounds double, ptr %B, i64 %idxprom2.im1
  %vB.i = load double, ptr %arrayidxB.i, align 8
  %add24 = fadd double %vB.im1, %vB.i
  %idxprom2.ip1 = add nsw i64 %idxprom2.im1, 1
  %arrayidxB.ip1 = getelementptr inbounds double, ptr %B, i64 %idxprom2.ip1
  %vB.ip1 = load double, ptr %arrayidxB.ip1, align 8
  %add28 = fadd double %add24, %vB.ip1
  %mul29 = fmul double 3.333300e-01, %add28
  %arrayidxA = getelementptr inbounds double, ptr %A, i64 %idxprom2.im1
  store double %mul29, ptr %arrayidxA, align 8
  %inc2 = add nsw i32 %i2, 1
  %cmp17.next = icmp slt i32 %inc2, %sub_n1
  br i1 %cmp17.next, label %loop2.body, label %for.end34

for.end34:                                        ; preds = %loop2.body, %for.end
  br label %for.inc35

for.inc35:                                        ; preds = %for.end34
  %inc36 = add nsw i32 %t, 1
  %cmp_next = icmp slt i32 %inc36, %tsteps
  br i1 %cmp_next, label %for.cond, label %for.end37

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
