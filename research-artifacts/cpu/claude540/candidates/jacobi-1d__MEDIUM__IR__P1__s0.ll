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
  %tsteps64 = zext i32 %tsteps to i64
  %count64 = sub i64 %n64, 2
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %preheader
  %t.iv = phi i64 [ 0, %preheader ], [ %t.next, %for.inc35 ]

  br label %loop1.body

loop1.body:
  %i1.iv = phi i64 [ 1, %for.cond ], [ %i1.next, %loop1.body ]
  %im1.1 = add nsw i64 %i1.iv, -1
  %ap.im1 = getelementptr inbounds double, ptr %A, i64 %im1.1
  %a.im1 = load double, ptr %ap.im1, align 8
  %ap.i = getelementptr inbounds double, ptr %A, i64 %i1.iv
  %a.i = load double, ptr %ap.i, align 8
  %add8 = fadd double %a.im1, %a.i
  %ip1.1 = add nsw i64 %i1.iv, 1
  %ap.ip1 = getelementptr inbounds double, ptr %A, i64 %ip1.1
  %a.ip1 = load double, ptr %ap.ip1, align 8
  %add12 = fadd double %add8, %a.ip1
  %mul = fmul double 3.333300e-01, %add12
  %bp.i = getelementptr inbounds double, ptr %B, i64 %i1.iv
  store double %mul, ptr %bp.i, align 8
  %i1.next = add nsw i64 %i1.iv, 1
  %cmp1.done = icmp eq i64 %i1.next, %count64
  br i1 %cmp1.done, label %loop2.entry, label %loop1.body

loop2.entry:
  br label %loop2.body

loop2.body:
  %i2.iv = phi i64 [ 1, %loop2.entry ], [ %i2.next, %loop2.body ]
  %bm1.1 = add nsw i64 %i2.iv, -1
  %bp.im1 = getelementptr inbounds double, ptr %B, i64 %bm1.1
  %b.im1 = load double, ptr %bp.im1, align 8
  %bp.i2 = getelementptr inbounds double, ptr %B, i64 %i2.iv
  %b.i = load double, ptr %bp.i2, align 8
  %add24 = fadd double %b.im1, %b.i
  %bip1.1 = add nsw i64 %i2.iv, 1
  %bp.ip1 = getelementptr inbounds double, ptr %B, i64 %bip1.1
  %b.ip1 = load double, ptr %bp.ip1, align 8
  %add28 = fadd double %add24, %b.ip1
  %mul29 = fmul double 3.333300e-01, %add28
  %ap.i2 = getelementptr inbounds double, ptr %A, i64 %i2.iv
  store double %mul29, ptr %ap.i2, align 8
  %i2.next = add nsw i64 %i2.iv, 1
  %cmp2.done = icmp eq i64 %i2.next, %count64
  br i1 %cmp2.done, label %for.inc35, label %loop2.body

for.inc35:                                         ; preds = %loop2.body
  %t.next = add nuw nsw i64 %t.iv, 1
  %cmp.t.done = icmp eq i64 %t.next, %tsteps64
  br i1 %cmp.t.done, label %for.end37, label %for.cond

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
