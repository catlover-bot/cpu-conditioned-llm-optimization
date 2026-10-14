; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_doitgen(i32 noundef %nr, i32 noundef %nq, i32 noundef %np, ptr noundef %A, ptr noundef %C4, ptr noundef %sum) #0 {
entry:
  %nr64 = sext i32 %nr to i64
  %nq64 = sext i32 %nq to i64
  %np64 = sext i32 %np to i64

  %cmp.r0 = icmp slt i32 0, %nr
  br i1 %cmp.r0, label %r.preheader, label %for.end50

r.preheader:
  %npnp = mul nuw nsw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %r.preheader
  %r = phi i32 [ 0, %r.preheader ], [ %inc49, %for.inc48 ]
  %r64 = phi i64 [ 0, %r.preheader ], [ %r64.next, %for.inc48 ]

  %cmp.q0 = icmp slt i32 0, %nq
  br i1 %cmp.q0, label %q.preheader, label %for.end47

q.preheader:
  %r.base = mul nsw i64 %r64, %npnp
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc45, %q.preheader
  %q = phi i32 [ 0, %q.preheader ], [ %inc46, %for.inc45 ]
  %q64 = phi i64 [ 0, %q.preheader ], [ %q64.next, %for.inc45 ]

  %cmp.p0 = icmp slt i32 0, %np
  br i1 %cmp.p0, label %p.preheader, label %for.end44

p.preheader:
  %q.off = mul nsw i64 %q64, %np64
  %rq.base = add nsw i64 %r.base, %q.off
  %A.rq = getelementptr inbounds double, ptr %A, i64 %rq.base
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc28, %p.preheader
  %p = phi i32 [ 0, %p.preheader ], [ %inc29, %for.inc28 ]
  %p64 = phi i64 [ 0, %p.preheader ], [ %p64.next, %for.inc28 ]

  %arrayidx.sum = getelementptr inbounds double, ptr %sum, i64 %p64
  store double 0.000000e+00, ptr %arrayidx.sum, align 8

  %cmp.s0 = icmp slt i32 0, %np
  br i1 %cmp.s0, label %s.preheader, label %for.end

s.preheader:
  br label %for.cond12

for.cond12:                                       ; preds = %for.inc, %s.preheader
  %s64 = phi i64 [ 0, %s.preheader ], [ %s64.next, %for.inc ]

  %arrayidx20 = getelementptr inbounds double, ptr %A.rq, i64 %s64
  %valA = load double, ptr %arrayidx20, align 8

  %s.off = mul nsw i64 %s64, %np64
  %arrayidx22 = getelementptr inbounds double, ptr %C4, i64 %s.off
  %arrayidx24 = getelementptr inbounds double, ptr %arrayidx22, i64 %p64
  %valC = load double, ptr %arrayidx24, align 8

  %mul = fmul double %valA, %valC

  %sumval = load double, ptr %arrayidx.sum, align 8
  %add27 = fadd double %sumval, %mul
  store double %add27, ptr %arrayidx.sum, align 8

  %s64.next = add nuw nsw i64 %s64, 1
  %scmp = icmp slt i64 %s64.next, %np64
  br i1 %scmp, label %for.cond12, label %for.end, !llvm.loop !6

for.end:                                          ; preds = %for.cond12, %for.cond9
  br label %for.inc28

for.inc28:                                        ; preds = %for.end
  %p64.next = add nuw nsw i64 %p64, 1
  %inc29 = add nsw i32 %p, 1
  %pcmp = icmp slt i32 %inc29, %np
  br i1 %pcmp, label %for.cond9, label %for.end30, !llvm.loop !8

for.end30:                                        ; preds = %for.inc28
  br label %for.cond31

for.cond31:                                       ; preds = %for.inc42, %for.end30
  %p2 = phi i32 [ 0, %for.end30 ], [ %inc43, %for.inc42 ]
  %p2_64 = phi i64 [ 0, %for.end30 ], [ %p2_64.next, %for.inc42 ]

  %cmp32 = icmp slt i32 %p2, %np
  br i1 %cmp32, label %for.body33, label %for.end44

for.body33:                                       ; preds = %for.cond31
  %arrayidx35 = getelementptr inbounds double, ptr %sum, i64 %p2_64
  %sumval2 = load double, ptr %arrayidx35, align 8

  %arrayidx41 = getelementptr inbounds double, ptr %A.rq, i64 %p2_64
  store double %sumval2, ptr %arrayidx41, align 8

  br label %for.inc42

for.inc42:                                        ; preds = %for.body33
  %p2_64.next = add nuw nsw i64 %p2_64, 1
  %inc43 = add nsw i32 %p2, 1
  br label %for.cond31, !llvm.loop !9

for.end44:                                        ; preds = %for.cond31
  br label %for.inc45

for.inc45:                                        ; preds = %for.end44
  %q64.next = add nuw nsw i64 %q64, 1
  %inc46 = add nsw i32 %q, 1
  %qcmp = icmp slt i32 %inc46, %nq
  br i1 %qcmp, label %for.cond6, label %for.end47, !llvm.loop !10

for.end47:                                        ; preds = %for.inc45, %for.cond6
  br label %for.inc48

for.inc48:                                        ; preds = %for.end47
  %r64.next = add nuw nsw i64 %r64, 1
  %inc49 = add nsw i32 %r, 1
  %rcmp = icmp slt i32 %inc49, %nr
  br i1 %rcmp, label %for.cond, label %for.end50, !llvm.loop !11

for.end50:                                        ; preds = %for.inc48, %entry
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
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
