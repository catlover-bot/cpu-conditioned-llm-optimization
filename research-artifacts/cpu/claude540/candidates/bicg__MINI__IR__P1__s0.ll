; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %init.s.preheader, label %check.m

init.s.preheader:
  %n64 = sext i32 %n to i64
  br label %init.s.body

init.s.body:
  %iv1 = phi i64 [ 0, %init.s.preheader ], [ %iv1.next, %init.s.body ]
  %arrayidx.s = getelementptr inbounds double, ptr %s, i64 %iv1
  store double 0.000000e+00, ptr %arrayidx.s, align 8
  %iv1.next = add nuw nsw i64 %iv1, 1
  %cond1 = icmp eq i64 %iv1.next, %n64
  br i1 %cond1, label %check.m, label %init.s.body

check.m:
  %cmp_m0 = icmp sgt i32 %m, 0
  br i1 %cmp_m0, label %outer.preheader, label %for.end42

outer.preheader:
  %m64 = sext i32 %m to i64
  br label %outer.body

outer.body:
  %i.iv = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.inc ]
  %arrayidx.q = getelementptr inbounds double, ptr %q, i64 %i.iv
  store double 0.000000e+00, ptr %arrayidx.q, align 8
  br i1 %cmp_m0, label %inner.preheader, label %outer.inc

inner.preheader:
  %rowbase = mul nsw i64 %i.iv, %m64
  %rowptr = getelementptr inbounds double, ptr %A, i64 %rowbase
  %r_i_ptr = getelementptr inbounds double, ptr %r, i64 %i.iv
  %r_i = load double, ptr %r_i_ptr, align 8
  br label %inner.body

inner.body:
  %j.iv = phi i64 [ 0, %inner.preheader ], [ %j.next, %inner.body ]
  %q_acc = phi double [ 0.000000e+00, %inner.preheader ], [ %q_new, %inner.body ]
  %arrayidx.s2 = getelementptr inbounds double, ptr %s, i64 %j.iv
  %s_val = load double, ptr %arrayidx.s2, align 8
  %arrayidx.A = getelementptr inbounds double, ptr %rowptr, i64 %j.iv
  %A_val = load double, ptr %arrayidx.A, align 8
  %mul1 = fmul double %r_i, %A_val
  %add1 = fadd double %s_val, %mul1
  store double %add1, ptr %arrayidx.s2, align 8
  %arrayidx.p = getelementptr inbounds double, ptr %p, i64 %j.iv
  %p_val = load double, ptr %arrayidx.p, align 8
  %mul2 = fmul double %A_val, %p_val
  %q_new = fadd double %q_acc, %mul2
  %j.next = add nuw nsw i64 %j.iv, 1
  %cond2 = icmp eq i64 %j.next, %m64
  br i1 %cond2, label %inner.exit, label %inner.body

inner.exit:
  store double %q_new, ptr %arrayidx.q, align 8
  br label %outer.inc

outer.inc:
  %i.next = add nuw nsw i64 %i.iv, 1
  %condo = icmp eq i64 %i.next, %n64
  br i1 %condo, label %for.end42, label %outer.body

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
