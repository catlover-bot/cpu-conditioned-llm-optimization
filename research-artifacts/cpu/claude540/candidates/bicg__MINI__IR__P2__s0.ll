; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp_n = icmp slt i32 %n, 1
  br i1 %cmp_n, label %init.s.end, label %init.s.preheader

init.s.preheader:
  %n64 = zext i32 %n to i64
  br label %init.s.body

init.s.body:
  %i0 = phi i64 [ 0, %init.s.preheader ], [ %i0.next, %init.s.body ]
  %gep0 = getelementptr inbounds double, ptr %s, i64 %i0
  store double 0.000000e+00, ptr %gep0, align 8
  %i0.next = add nuw nsw i64 %i0, 1
  %done0 = icmp eq i64 %i0.next, %n64
  br i1 %done0, label %init.s.end, label %init.s.body

init.s.end:
  %cmp_m0 = icmp slt i32 %m, 1
  br i1 %cmp_m0, label %for.end42, label %outer.preheader

outer.preheader:
  %m64 = zext i32 %m to i64
  %n64b = zext i32 %n to i64
  br label %for.body8

for.body8:
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %for.inc40 ]
  %qgep = getelementptr inbounds double, ptr %q, i64 %i
  store double 0.000000e+00, ptr %qgep, align 8

  %rgep = getelementptr inbounds double, ptr %r, i64 %i
  %rval = load double, ptr %rgep, align 8

  %arow_off = mul nsw i64 %i, %m64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow_off

  %cmp_m1 = icmp slt i32 %m, 1
  br i1 %cmp_m1, label %for.end39, label %inner.preheader

inner.preheader:
  br label %for.body13

for.body13:
  %j = phi i64 [ 0, %inner.preheader ], [ %j.next, %for.body13 ]
  %qacc = phi double [ 0.000000e+00, %inner.preheader ], [ %qadd34, %for.body13 ]

  %sgep = getelementptr inbounds double, ptr %s, i64 %j
  %sval = load double, ptr %sgep, align 8

  %aelemgep = getelementptr inbounds double, ptr %arow, i64 %j
  %aval = load double, ptr %aelemgep, align 8

  %mul = fmul double %rval, %aval
  %sadd = fadd double %sval, %mul
  store double %sadd, ptr %sgep, align 8

  %pgep = getelementptr inbounds double, ptr %p, i64 %j
  %pval = load double, ptr %pgep, align 8
  %mul33 = fmul double %aval, %pval
  %qadd34 = fadd double %qacc, %mul33

  %j.next = add nuw nsw i64 %j, 1
  %donej = icmp eq i64 %j.next, %n64b
  br i1 %donej, label %for.end39, label %for.body13

for.end39:
  %qfinal = phi double [ 0.000000e+00, %for.body8 ], [ %qadd34, %for.body13 ]
  store double %qfinal, ptr %qgep, align 8
  br label %for.inc40

for.inc40:
  %i.next = add nuw nsw i64 %i, 1
  %donei = icmp eq i64 %i.next, %m64
  br i1 %donei, label %for.end42, label %for.body8

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
