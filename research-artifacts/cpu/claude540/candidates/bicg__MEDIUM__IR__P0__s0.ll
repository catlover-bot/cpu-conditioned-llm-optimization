; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp.m0 = icmp sgt i32 %m, 0
  br i1 %cmp.m0, label %for.body.preheader, label %for.end

for.body.preheader:
  %m64 = zext i32 %m to i64
  br label %for.body

for.body:
  %iv1 = phi i64 [ 0, %for.body.preheader ], [ %iv1.next, %for.body ]
  %arrayidx = getelementptr inbounds double, ptr %s, i64 %iv1
  store double 0.000000e+00, ptr %arrayidx, align 8
  %iv1.next = add nuw nsw i64 %iv1, 1
  %exitcond1 = icmp eq i64 %iv1.next, %m64
  br i1 %exitcond1, label %for.end, label %for.body

for.end:
  %cmp.n0 = icmp sgt i32 %n, 0
  br i1 %cmp.n0, label %outer.preheader, label %for.end42

outer.preheader:
  %n64 = zext i32 %n to i64
  %m64b = zext i32 %m to i64
  %cmp.minner = icmp sgt i32 %m, 0
  br label %outer.body

outer.body:
  %i64v = phi i64 [ 0, %outer.preheader ], [ %i64v.next, %outer.latch ]
  %qidx = getelementptr inbounds double, ptr %q, i64 %i64v
  store double 0.000000e+00, ptr %qidx, align 8
  br i1 %cmp.minner, label %inner.preheader, label %outer.latch

inner.preheader:
  %rvalptr = getelementptr inbounds double, ptr %r, i64 %i64v
  %rval = load double, ptr %rvalptr, align 8
  %arow = mul nsw i64 %i64v, %m64b
  %arowptr = getelementptr inbounds double, ptr %A, i64 %arow
  br label %inner.body

inner.body:
  %j64 = phi i64 [ 0, %inner.preheader ], [ %j64.next, %inner.body ]
  %sptr = getelementptr inbounds double, ptr %s, i64 %j64
  %sval = load double, ptr %sptr, align 8
  %aij.ptr = getelementptr inbounds double, ptr %arowptr, i64 %j64
  %aij = load double, ptr %aij.ptr, align 8
  %mul1 = fmul double %rval, %aij
  %add1 = fadd double %sval, %mul1
  store double %add1, ptr %sptr, align 8
  %qcur = load double, ptr %qidx, align 8
  %pptr = getelementptr inbounds double, ptr %p, i64 %j64
  %pval = load double, ptr %pptr, align 8
  %mul2 = fmul double %aij, %pval
  %add2 = fadd double %qcur, %mul2
  store double %add2, ptr %qidx, align 8
  %j64.next = add nuw nsw i64 %j64, 1
  %exitcond2 = icmp eq i64 %j64.next, %m64b
  br i1 %exitcond2, label %outer.latch, label %inner.body

outer.latch:
  %i64v.next = add nuw nsw i64 %i64v, 1
  %exitcond3 = icmp eq i64 %i64v.next, %n64
  br i1 %exitcond3, label %for.end42, label %outer.body

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
