; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader.s, label %check.m

preheader.s:
  %n64 = zext i32 %n to i64
  br label %loop.s

loop.s:
  %iv.s = phi i64 [ 0, %preheader.s ], [ %iv.s.next, %loop.s ]
  %gep.s = getelementptr inbounds double, ptr %s, i64 %iv.s
  store double 0.000000e+00, ptr %gep.s, align 8
  %iv.s.next = add nuw nsw i64 %iv.s, 1
  %cmp.s = icmp eq i64 %iv.s.next, %n64
  br i1 %cmp.s, label %check.m, label %loop.s

check.m:
  %cmp.m0 = icmp sgt i32 %m, 0
  br i1 %cmp.m0, label %outer.preheader, label %for.end42

outer.preheader:
  %m64 = zext i32 %m to i64
  br label %outer.loop

outer.loop:
  %i.iv = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.latch ]
  %q.gep = getelementptr inbounds double, ptr %q, i64 %i.iv
  store double 0.000000e+00, ptr %q.gep, align 8
  br i1 %cmp.n, label %inner.preheader, label %outer.latch

inner.preheader:
  %A.row = getelementptr inbounds double, ptr %A, i64 %i.iv, i64 0
  %r.elt.gep = getelementptr inbounds double, ptr %r, i64 %i.iv
  %r.elt = load double, ptr %r.elt.gep, align 8
  br label %inner.loop

inner.loop:
  %j.iv = phi i64 [ 0, %inner.preheader ], [ %j.next, %inner.loop ]
  %q.acc = phi double [ 0.000000e+00, %inner.preheader ], [ %q.add, %inner.loop ]
  %s.gep = getelementptr inbounds double, ptr %s, i64 %j.iv
  %s.val = load double, ptr %s.gep, align 8
  %A.gep = getelementptr inbounds double, ptr %A.row, i64 %j.iv
  %A.val = load double, ptr %A.gep, align 8
  %mul1 = fmul double %r.elt, %A.val
  %add1 = fadd double %s.val, %mul1
  store double %add1, ptr %s.gep, align 8
  %p.gep = getelementptr inbounds double, ptr %p, i64 %j.iv
  %p.val = load double, ptr %p.gep, align 8
  %mul2 = fmul double %A.val, %p.val
  %q.add = fadd double %q.acc, %mul2
  store double %q.add, ptr %q.gep, align 8
  %j.next = add nuw nsw i64 %j.iv, 1
  %n64.2 = zext i32 %n to i64
  %cmp.j = icmp eq i64 %j.next, %n64.2
  br i1 %cmp.j, label %outer.latch, label %inner.loop

outer.latch:
  %i.next = add nuw nsw i64 %i.iv, 1
  %m64.2 = zext i32 %m to i64
  %cmp.i = icmp eq i64 %i.next, %m64.2
  br i1 %cmp.i, label %for.end42, label %outer.loop

for.end42:
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
