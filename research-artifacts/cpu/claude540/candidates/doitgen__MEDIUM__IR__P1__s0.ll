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
  %cmp.nq0 = icmp sgt i32 %nq, 0
  %cmp.np0 = icmp sgt i32 %np, 0
  %nq64 = sext i32 %nq to i64
  %np64 = sext i32 %np to i64
  %nr64 = sext i32 %nr to i64
  %rq_stride = mul nsw i64 %nq64, %np64
  br label %for.r

for.r:
  %r = phi i64 [ 0, %preheader ], [ %r.inc, %for.r.latch ]
  br i1 %cmp.nq0, label %for.q.preheader, label %for.r.latch

for.q.preheader:
  %A_r_base = mul nsw i64 %r, %rq_stride
  br label %for.q

for.q:
  %q = phi i64 [ 0, %for.q.preheader ], [ %q.inc, %for.q.latch ]
  br i1 %cmp.np0, label %for.p1.preheader, label %for.q.latch

for.p1.preheader:
  %A_rq_base = mul nsw i64 %q, %np64
  %A_row_off = add nsw i64 %A_r_base, %A_rq_base
  %A_row_ptr = getelementptr inbounds double, ptr %A, i64 %A_row_off
  br label %for.p1

for.p1:
  %p1 = phi i64 [ 0, %for.p1.preheader ], [ %p1.inc, %for.inc28 ]
  %sum.p1 = getelementptr inbounds double, ptr %sum, i64 %p1
  store double 0.000000e+00, ptr %sum.p1, align 8
  br i1 %cmp.np0, label %for.s.preheader, label %for.inc28

for.s.preheader:
  br label %for.s

for.s:
  %s = phi i64 [ 0, %for.s.preheader ], [ %s.inc, %for.s ]
  %sumval = phi double [ 0.000000e+00, %for.s.preheader ], [ %add27, %for.s ]
  %A_elem_ptr = getelementptr inbounds double, ptr %A_row_ptr, i64 %s
  %aval = load double, ptr %A_elem_ptr, align 8
  %C4_s_off = mul nsw i64 %s, %np64
  %C4_row_ptr = getelementptr inbounds double, ptr %C4, i64 %C4_s_off
  %C4_elem_ptr = getelementptr inbounds double, ptr %C4_row_ptr, i64 %p1
  %cval = load double, ptr %C4_elem_ptr, align 8
  %mul = fmul double %aval, %cval
  %add27 = fadd double %sumval, %mul
  %s.inc = add nsw i64 %s, 1
  %cmp.s = icmp slt i64 %s.inc, %np64
  br i1 %cmp.s, label %for.s, label %for.s.exit

for.s.exit:
  store double %add27, ptr %sum.p1, align 8
  br label %for.inc28

for.inc28:
  %p1.inc = add nsw i64 %p1, 1
  %cmp.p1 = icmp slt i64 %p1.inc, %np64
  br i1 %cmp.p1, label %for.p1, label %for.q.latch

for.q.latch:
  br i1 %cmp.np0, label %for.p2.preheader, label %for.q.inc

for.p2.preheader:
  br label %for.p2

for.p2:
  %p2 = phi i64 [ 0, %for.p2.preheader ], [ %p2.inc, %for.p2 ]
  %sum.p2 = getelementptr inbounds double, ptr %sum, i64 %p2
  %sumv2 = load double, ptr %sum.p2, align 8
  %A_elem2_ptr = getelementptr inbounds double, ptr %A_row_ptr, i64 %p2
  store double %sumv2, ptr %A_elem2_ptr, align 8
  %p2.inc = add nsw i64 %p2, 1
  %cmp.p2 = icmp slt i64 %p2.inc, %np64
  br i1 %cmp.p2, label %for.p2, label %for.q.inc

for.q.inc:
  %q.inc = add nsw i64 %q, 1
  %cmp.q = icmp slt i64 %q.inc, %nq64
  br i1 %cmp.q, label %for.q, label %for.r.latch

for.r.latch:
  %r.inc = add nsw i64 %r, 1
  %cmp.r = icmp slt i64 %r.inc, %nr64
  br i1 %cmp.r, label %for.r, label %for.end50

for.end50:
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
