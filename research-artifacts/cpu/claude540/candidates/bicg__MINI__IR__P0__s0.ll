; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp.m0 = icmp sgt i32 %m, 0
  br i1 %cmp.m0, label %init.s.preheader, label %check.n

init.s.preheader:
  %m64 = zext i32 %m to i64
  br label %init.s.body

init.s.body:
  %i0 = phi i64 [ 0, %init.s.preheader ], [ %i0.next, %init.s.body ]
  %s.gep0 = getelementptr inbounds double, ptr %s, i64 %i0
  store double 0.000000e+00, ptr %s.gep0, align 8
  %i0.next = add nuw nsw i64 %i0, 1
  %cmp0 = icmp slt i64 %i0.next, %m64
  br i1 %cmp0, label %init.s.body, label %check.n

check.n:
  %cmp.n0 = icmp sgt i32 %n, 0
  br i1 %cmp.n0, label %outer.preheader, label %for.end42

outer.preheader:
  %n64 = zext i32 %n to i64
  %m64b = zext i32 %m to i64
  %cmp.m0b = icmp sgt i32 %m, 0
  br label %outer.body

outer.body:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.latch ]
  %q.gep = getelementptr inbounds double, ptr %q, i64 %i
  store double 0.000000e+00, ptr %q.gep, align 8
  br i1 %cmp.m0b, label %inner.preheader, label %outer.latch

inner.preheader:
  %r.gep = getelementptr inbounds double, ptr %r, i64 %i
  %r.val = load double, ptr %r.gep, align 8
  %A.rowbase = mul nsw i64 %i, %m64b
  %A.row = getelementptr inbounds double, ptr %A, i64 %A.rowbase
  br label %inner.body

inner.body:
  %j = phi i64 [ 0, %inner.preheader ], [ %j.next, %inner.body ]
  %q.acc = phi double [ 0.000000e+00, %inner.preheader ], [ %q.acc.next, %inner.body ]
  %s.gep = getelementptr inbounds double, ptr %s, i64 %j
  %s.val = load double, ptr %s.gep, align 8
  %A.gep = getelementptr inbounds double, ptr %A.row, i64 %j
  %A.val = load double, ptr %A.gep, align 8
  %mul1 = fmul double %r.val, %A.val
  %add1 = fadd double %s.val, %mul1
  store double %add1, ptr %s.gep, align 8
  %p.gep = getelementptr inbounds double, ptr %p, i64 %j
  %p.val = load double, ptr %p.gep, align 8
  %mul2 = fmul double %A.val, %p.val
  %add2 = fadd double %q.acc, %mul2
  %j.next = add nuw nsw i64 %j, 1
  %cmp1 = icmp slt i64 %j.next, %m64b
  br i1 %cmp1, label %inner.body, label %inner.exit

inner.exit:
  store double %add2, ptr %q.gep, align 8
  br label %outer.latch

outer.latch:
  %i.next = add nuw nsw i64 %i, 1
  %cmp2 = icmp slt i64 %i.next, %n64
  br i1 %cmp2, label %outer.body, label %for.end42

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
