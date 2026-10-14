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

  %cmp.r = icmp slt i32 0, %nr
  br i1 %cmp.r, label %r.preheader, label %for.end50

r.preheader:
  %npnq = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %r.preheader
  %r = phi i64 [ 0, %r.preheader ], [ %r.inc, %for.inc48 ]

  %cmp.q = icmp slt i32 0, %nq
  br i1 %cmp.q, label %q.preheader, label %for.end47

q.preheader:
  %A.r.off = mul nsw i64 %r, %npnq
  %A.r.ptr = getelementptr inbounds double, ptr %A, i64 %A.r.off
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc45, %q.preheader
  %q = phi i64 [ 0, %q.preheader ], [ %q.inc, %for.inc45 ]

  %A.q.off = mul nsw i64 %q, %np64
  %A.rq.ptr = getelementptr inbounds double, ptr %A.r.ptr, i64 %A.q.off

  %cmp.p1 = icmp slt i32 0, %np
  br i1 %cmp.p1, label %p1.preheader, label %for.end30

p1.preheader:
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc28, %p1.preheader
  %p = phi i64 [ 0, %p1.preheader ], [ %p.inc, %for.inc28 ]

  %sum.p.ptr = getelementptr inbounds double, ptr %sum, i64 %p
  store double 0.000000e+00, ptr %sum.p.ptr, align 8

  %cmp.s = icmp slt i32 0, %np
  br i1 %cmp.s, label %s.preheader, label %for.end

s.preheader:
  br label %for.cond12

for.cond12:                                       ; preds = %for.inc, %s.preheader
  %s = phi i64 [ 0, %s.preheader ], [ %s.inc, %for.inc ]

  %A.elem.ptr = getelementptr inbounds double, ptr %A.rq.ptr, i64 %s
  %aval = load double, ptr %A.elem.ptr, align 8

  %C4.s.off = mul nsw i64 %s, %np64
  %C4.s.ptr = getelementptr inbounds double, ptr %C4, i64 %C4.s.off
  %C4.elem.ptr = getelementptr inbounds double, ptr %C4.s.ptr, i64 %p
  %cval = load double, ptr %C4.elem.ptr, align 8

  %mul = fmul double %aval, %cval

  %sumval = load double, ptr %sum.p.ptr, align 8
  %add27 = fadd double %sumval, %mul
  store double %add27, ptr %sum.p.ptr, align 8

  %s.inc = add nsw i64 %s, 1
  %s.cmp = icmp slt i64 %s.inc, %np64
  br i1 %s.cmp, label %for.cond12, label %for.end, !llvm.loop !6

for.end:                                          ; preds = %for.cond12, %for.cond9
  br label %for.inc28

for.inc28:                                        ; preds = %for.end
  %p.inc = add nsw i64 %p, 1
  %p.cmp = icmp slt i64 %p.inc, %np64
  br i1 %p.cmp, label %for.cond9, label %for.end30, !llvm.loop !8

for.end30:                                        ; preds = %for.inc28, %for.cond6
  %cmp.p2 = icmp slt i32 0, %np
  br i1 %cmp.p2, label %p2.preheader, label %for.end44

p2.preheader:
  br label %for.cond31

for.cond31:                                       ; preds = %for.inc42, %p2.preheader
  %p2 = phi i64 [ 0, %p2.preheader ], [ %p2.inc, %for.inc42 ]

  %sum.p2.ptr = getelementptr inbounds double, ptr %sum, i64 %p2
  %sumval2 = load double, ptr %sum.p2.ptr, align 8

  %A.wr.ptr = getelementptr inbounds double, ptr %A.rq.ptr, i64 %p2
  store double %sumval2, ptr %A.wr.ptr, align 8

  %p2.inc = add nsw i64 %p2, 1
  %p2.cmp = icmp slt i64 %p2.inc, %np64
  br i1 %p2.cmp, label %for.cond31, label %for.end44, !llvm.loop !9

for.end44:                                        ; preds = %for.cond31, %for.end30
  br label %for.inc45

for.inc45:                                        ; preds = %for.end44
  %q.inc = add nsw i64 %q, 1
  %q.cmp = icmp slt i64 %q.inc, %nq64
  br i1 %q.cmp, label %for.cond6, label %for.end47, !llvm.loop !10

for.end47:                                        ; preds = %for.inc45, %for.cond
  br label %for.inc48

for.inc48:                                        ; preds = %for.end47
  %r.inc = add nsw i64 %r, 1
  %r.cmp = icmp slt i64 %r.inc, %nr64
  br i1 %r.cmp, label %for.cond, label %for.end50, !llvm.loop !11

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
