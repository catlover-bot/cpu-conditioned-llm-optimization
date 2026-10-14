; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.t = icmp sgt i32 %tsteps, 0
  br i1 %cmp.t, label %tloop.preheader, label %for.end37

tloop.preheader:
  %sub.n1 = sub nsw i32 %n, 1
  %cmp.inner = icmp slt i32 1, %sub.n1
  %trip64 = sext i32 %sub.n1 to i64
  br label %for.body

for.body:
  %t = phi i32 [ 0, %tloop.preheader ], [ %inc36, %for.inc35 ]
  br i1 %cmp.inner, label %loop1.preheader, label %for.end

loop1.preheader:
  br label %loop1.body

loop1.body:
  %i64.1 = phi i64 [ 1, %loop1.preheader ], [ %inc.1, %loop1.body ]
  %im1.1 = add nsw i64 %i64.1, -1
  %ptr.am1 = getelementptr inbounds double, ptr %A, i64 %im1.1
  %a.m1 = load double, ptr %ptr.am1, align 8
  %ptr.a0 = getelementptr inbounds double, ptr %A, i64 %i64.1
  %a.0 = load double, ptr %ptr.a0, align 8
  %s1 = fadd double %a.m1, %a.0
  %ip1.1 = add nsw i64 %i64.1, 1
  %ptr.ap1 = getelementptr inbounds double, ptr %A, i64 %ip1.1
  %a.p1 = load double, ptr %ptr.ap1, align 8
  %s2 = fadd double %s1, %a.p1
  %mul1 = fmul double 3.333300e-01, %s2
  %ptr.b0 = getelementptr inbounds double, ptr %B, i64 %i64.1
  store double %mul1, ptr %ptr.b0, align 8
  %inc.1 = add nsw i64 %i64.1, 1
  %cmp.1 = icmp slt i64 %inc.1, %trip64
  br i1 %cmp.1, label %loop1.body, label %for.end

for.end:
  br i1 %cmp.inner, label %loop2.preheader, label %for.end34

loop2.preheader:
  br label %loop2.body

loop2.body:
  %i64.2 = phi i64 [ 1, %loop2.preheader ], [ %inc.2, %loop2.body ]
  %im1.2 = add nsw i64 %i64.2, -1
  %ptr.bm1 = getelementptr inbounds double, ptr %B, i64 %im1.2
  %b.m1 = load double, ptr %ptr.bm1, align 8
  %ptr.b0b = getelementptr inbounds double, ptr %B, i64 %i64.2
  %b.0 = load double, ptr %ptr.b0b, align 8
  %t1 = fadd double %b.m1, %b.0
  %ip1.2 = add nsw i64 %i64.2, 1
  %ptr.bp1 = getelementptr inbounds double, ptr %B, i64 %ip1.2
  %b.p1 = load double, ptr %ptr.bp1, align 8
  %t2 = fadd double %t1, %b.p1
  %mul2 = fmul double 3.333300e-01, %t2
  %ptr.a0b = getelementptr inbounds double, ptr %A, i64 %i64.2
  store double %mul2, ptr %ptr.a0b, align 8
  %inc.2 = add nsw i64 %i64.2, 1
  %cmp.2 = icmp slt i64 %inc.2, %trip64
  br i1 %cmp.2, label %loop2.body, label %for.end34

for.end34:
  br label %for.inc35

for.inc35:
  %inc36 = add nsw i32 %t, 1
  %cmp.t2 = icmp slt i32 %inc36, %tsteps
  br i1 %cmp.t2, label %for.body, label %for.end37

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
