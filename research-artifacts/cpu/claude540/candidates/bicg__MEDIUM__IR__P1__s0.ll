; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_bicg(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %s, ptr noundef %q, ptr noundef %p, ptr noundef %r) #0 {
entry:
  %cmp0 = icmp sgt i32 %n, 0
  br i1 %cmp0, label %init.s.preheader, label %check.q

init.s.preheader:
  %n64 = sext i32 %n to i64
  br label %init.s

init.s:
  %iv0 = phi i64 [ 0, %init.s.preheader ], [ %iv0.next, %init.s ]
  %arrayidx.s = getelementptr inbounds double, ptr %s, i64 %iv0
  store double 0.000000e+00, ptr %arrayidx.s, align 8
  %iv0.next = add nuw nsw i64 %iv0, 1
  %cmp0.loop = icmp slt i64 %iv0.next, %n64
  br i1 %cmp0.loop, label %init.s, label %check.q

check.q:
  %cmp1 = icmp sgt i32 %m, 0
  br i1 %cmp1, label %outer.preheader, label %for.end42

outer.preheader:
  %m64 = sext i32 %m to i64
  %n64b = sext i32 %n to i64
  %cmpInner = icmp sgt i32 %m, 0
  br label %for.body8

for.body8:
  %i.iv = phi i64 [ 0, %outer.preheader ], [ %i.iv.next, %for.inc40 ]
  %arrayidx10 = getelementptr inbounds double, ptr %q, i64 %i.iv
  store double 0.000000e+00, ptr %arrayidx10, align 8
  br i1 %cmpInner, label %inner.preheader, label %for.inc40

inner.preheader:
  %rowoff = mul nsw i64 %i.iv, %m64
  %rowptr = getelementptr inbounds double, ptr %A, i64 %rowoff
  %r_i_ptr = getelementptr inbounds double, ptr %r, i64 %i.iv
  %r_i = load double, ptr %r_i_ptr, align 8
  %q_i_ptr = getelementptr inbounds double, ptr %q, i64 %i.iv
  br label %for.body13

for.body13:
  %j.iv = phi i64 [ 0, %inner.preheader ], [ %j.iv.next, %for.body13 ]
  %q_i_acc = phi double [ 0.000000e+00, %inner.preheader ], [ %add34, %for.body13 ]
  %arrayidx15 = getelementptr inbounds double, ptr %s, i64 %j.iv
  %s_j = load double, ptr %arrayidx15, align 8
  %arrayidx21 = getelementptr inbounds double, ptr %rowptr, i64 %j.iv
  %A_ij = load double, ptr %arrayidx21, align 8
  %mul = fmul double %r_i, %A_ij
  %add22 = fadd double %s_j, %mul
  store double %add22, ptr %arrayidx15, align 8
  %arrayidx32 = getelementptr inbounds double, ptr %p, i64 %j.iv
  %p_j = load double, ptr %arrayidx32, align 8
  %mul33 = fmul double %A_ij, %p_j
  %add34 = fadd double %q_i_acc, %mul33
  %j.iv.next = add nuw nsw i64 %j.iv, 1
  %cmp12 = icmp slt i64 %j.iv.next, %m64
  br i1 %cmp12, label %for.body13, label %for.end39

for.end39:
  store double %add34, ptr %q_i_ptr, align 8
  br label %for.inc40

for.inc40:
  %i.iv.next = add nuw nsw i64 %i.iv, 1
  %cmp6 = icmp slt i64 %i.iv.next, %n64b
  br i1 %cmp6, label %for.body8, label %for.end42

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
