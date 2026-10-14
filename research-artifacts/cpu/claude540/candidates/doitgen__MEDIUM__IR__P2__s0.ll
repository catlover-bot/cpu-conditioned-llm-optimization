; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_doitgen(i32 noundef %nr, i32 noundef %nq, i32 noundef %np, ptr noundef %A, ptr noundef %C4, ptr noundef %sum) #0 {
entry:
  %cmp.nr = icmp sgt i32 %nr, 0
  br i1 %cmp.nr, label %preheader, label %for.end50

preheader:
  %cmp.nq = icmp sgt i32 %nq, 0
  %cmp.np = icmp sgt i32 %np, 0
  %nq64 = zext i32 %nq to i64
  %np64 = zext i32 %np to i64
  %nqnp = mul nuw i64 %nq64, %np64
  br label %for.r

for.r:                                            ; preds = %preheader, %for.r.inc
  %r = phi i32 [ 0, %preheader ], [ %r.inc, %for.r.inc ]
  br i1 %cmp.nq, label %for.q, label %for.r.inc

for.q:                                             ; preds = %for.r, %for.q.inc
  %q = phi i32 [ 0, %for.r ], [ %q.inc, %for.q.inc ]

  ; base pointer for A[r][q][*]  =  A + (r*nqnp + q*np) * 8 bytes
  %r64 = sext i32 %r to i64
  %q64 = sext i32 %q to i64
  %rbase = mul nsw i64 %r64, %nqnp
  %qoff = mul nsw i64 %q64, %np64
  %rowoff = add nsw i64 %rbase, %qoff
  %Arow = getelementptr inbounds double, ptr %A, i64 %rowoff

  br i1 %cmp.np, label %for.p.init, label %for.q.inc

for.p.init:
  br i1 %cmp.np, label %for.p, label %for.q.inc

for.p:                                             ; preds = %for.p.init, %for.p.inc
  %p = phi i32 [ 0, %for.p.init ], [ %p.inc, %for.p.inc ]
  %p64 = sext i32 %p to i64
  %sum.p.ptr = getelementptr inbounds double, ptr %sum, i64 %p64
  store double 0.000000e+00, ptr %sum.p.ptr, align 8

  br i1 %cmp.np, label %for.s, label %for.p.inc

for.s:                                             ; preds = %for.p, %for.s
  %s = phi i32 [ 0, %for.p ], [ %s.inc, %for.s ]
  %acc = phi double [ 0.000000e+00, %for.p ], [ %add27, %for.s ]

  %s64 = sext i32 %s to i64
  %Aval.ptr = getelementptr inbounds double, ptr %Arow, i64 %s64
  %Aval = load double, ptr %Aval.ptr, align 8

  %C4rowoff = mul nsw i64 %s64, %np64
  %C4row = getelementptr inbounds double, ptr %C4, i64 %C4rowoff
  %C4val.ptr = getelementptr inbounds double, ptr %C4row, i64 %p64
  %C4val = load double, ptr %C4val.ptr, align 8

  %mul = fmul double %Aval, %C4val
  %add27 = fadd double %acc, %mul

  %s.inc = add nsw i32 %s, 1
  %cmp.s = icmp slt i32 %s.inc, %np
  br i1 %cmp.s, label %for.s, label %for.s.end

for.s.end:
  store double %add27, ptr %sum.p.ptr, align 8
  br label %for.p.inc

for.p.inc:                                         ; preds = %for.p, %for.s.end
  %p.inc = add nsw i32 %p, 1
  %cmp.p.inc = icmp slt i32 %p.inc, %np
  br i1 %cmp.p.inc, label %for.p, label %for.q.inc

for.q.inc:                                         ; preds = %for.q, %for.p.init, %for.p.inc
  br i1 %cmp.np, label %for.p2.init, label %for.q.inc.after

for.p2.init:
  br label %for.p2

for.p2:                                            ; preds = %for.p2.init, %for.p2.inc
  %p2 = phi i32 [ 0, %for.p2.init ], [ %p2.inc, %for.p2.inc ]
  %p264 = sext i32 %p2 to i64
  %sum.p2.ptr = getelementptr inbounds double, ptr %sum, i64 %p264
  %sumval = load double, ptr %sum.p2.ptr, align 8
  %Adst.ptr = getelementptr inbounds double, ptr %Arow, i64 %p264
  store double %sumval, ptr %Adst.ptr, align 8

  %p2.inc = add nsw i32 %p2, 1
  %cmp.p2 = icmp slt i32 %p2.inc, %np
  br i1 %cmp.p2, label %for.p2, label %for.q.inc.after

for.q.inc.after:                                   ; preds = %for.q.inc, %for.p2
  %q.inc = add nsw i32 %q, 1
  %cmp.q.inc = icmp slt i32 %q.inc, %nq
  br i1 %cmp.q.inc, label %for.q, label %for.r.inc

for.r.inc:                                         ; preds = %for.r, %for.q.inc.after
  %r.inc = add nsw i32 %r, 1
  %cmp.r.inc = icmp slt i32 %r.inc, %nr
  br i1 %cmp.r.inc, label %for.r, label %for.end50

for.end50:                                         ; preds = %for.r.inc, %entry
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
