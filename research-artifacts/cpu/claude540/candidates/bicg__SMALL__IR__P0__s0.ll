; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %init.s.preheader, label %init.s.done

init.s.preheader:
  %m64 = zext i32 %m to i64
  br label %init.s.body

init.s.body:
  %iv1 = phi i64 [ 0, %init.s.preheader ], [ %iv1.next, %init.s.body ]
  %sptr = getelementptr inbounds double, ptr %s, i64 %iv1
  store double 0.000000e+00, ptr %sptr, align 8
  %iv1.next = add nuw nsw i64 %iv1, 1
  %cond1 = icmp eq i64 %iv1.next, %m64
  br i1 %cond1, label %init.s.done, label %init.s.body

init.s.done:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end42

outer.preheader:
  %n64 = zext i32 %n to i64
  %m64b = zext i32 %m to i64
  br label %outer.body

outer.body:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.inc ]
  %qptr.i = getelementptr inbounds double, ptr %q, i64 %i
  store double 0.000000e+00, ptr %qptr.i, align 8
  %cmp.inner = icmp sgt i32 %m, 0
  br i1 %cmp.inner, label %inner.preheader, label %outer.inc

inner.preheader:
  %Arow = mul nsw i64 %i, %m64b
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arow
  %rval = load double, ptr getelementptr inbounds (double, ptr null, i64 0), align 8
  br label %inner.body

inner.body:
  %j = phi i64 [ 0, %inner.preheader ], [ %j.next, %inner.body ]

  %sptr.j = getelementptr inbounds double, ptr %s, i64 %j
  %sval = load double, ptr %sptr.j, align 8

  %rptr.i = getelementptr inbounds double, ptr %r, i64 %i
  %rval.i = load double, ptr %rptr.i, align 8

  %Aptr = getelementptr inbounds double, ptr %Arowptr, i64 %j
  %Aval = load double, ptr %Aptr, align 8

  %mul1 = fmul double %rval.i, %Aval
  %add1 = fadd double %sval, %mul1
  store double %add1, ptr %sptr.j, align 8

  %qval = load double, ptr %qptr.i, align 8
  %pptr.j = getelementptr inbounds double, ptr %p, i64 %j
  %pval = load double, ptr %pptr.j, align 8
  %mul2 = fmul double %Aval, %pval
  %add2 = fadd double %qval, %mul2
  store double %add2, ptr %qptr.i, align 8

  %j.next = add nuw nsw i64 %j, 1
  %cond.inner = icmp eq i64 %j.next, %m64b
  br i1 %cond.inner, label %outer.inc, label %inner.body

outer.inc:
  %i.next = add nuw nsw i64 %i, 1
  %cond.outer = icmp eq i64 %i.next, %n64
  br i1 %cond.outer, label %for.end42, label %outer.body

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
