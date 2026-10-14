; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_doitgen(i32 noundef %nr, i32 noundef %nq, i32 noundef %np, ptr noundef %A, ptr noundef %C4, ptr noundef %sum) #0 {
entry:
  %cmp.nr = icmp sgt i32 %nr, 0
  %cmp.nq = icmp sgt i32 %nq, 0
  %cmp.np = icmp sgt i32 %np, 0
  %run = and i1 %cmp.nr, %cmp.nq
  %run2 = and i1 %run, %cmp.np
  br i1 %run2, label %r.preheader, label %for.end50

r.preheader:
  %nq64 = zext i32 %nq to i64
  %np64 = zext i32 %np to i64
  %nrq = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %r.preheader
  %r = phi i32 [ 0, %r.preheader ], [ %inc49, %for.inc48 ]
  %r64 = zext i32 %r to i64
  %rbase = mul nsw i64 %r64, %nrq
  br label %q.preheader

q.preheader:
  br label %for.cond6

for.cond6:                                         ; preds = %for.inc45, %q.preheader
  %q = phi i32 [ 0, %q.preheader ], [ %inc46, %for.inc45 ]
  %q64 = zext i32 %q to i64
  %qmul = mul nsw i64 %q64, %np64
  %rq = add nsw i64 %rbase, %qmul
  %Abase = getelementptr inbounds double, ptr %A, i64 %rq

  ; initialize sum[0..np-1] to 0
  br label %init.cond

init.cond:
  %p0 = phi i32 [ 0, %for.cond6 ], [ %p0.inc, %init.body ]
  %cmp.init = icmp slt i32 %p0, %np
  br i1 %cmp.init, label %init.body, label %compute.p.preheader

init.body:
  %p0.64 = sext i32 %p0 to i64
  %sum.init.ptr = getelementptr inbounds double, ptr %sum, i64 %p0.64
  store double 0.000000e+00, ptr %sum.init.ptr, align 8
  %p0.inc = add nsw i32 %p0, 1
  br label %init.cond

compute.p.preheader:
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc28, %compute.p.preheader
  %p = phi i32 [ 0, %compute.p.preheader ], [ %inc29, %for.inc28 ]
  %cmp10 = icmp slt i32 %p, %np
  br i1 %cmp10, label %for.body11, label %for.end30

for.body11:                                       ; preds = %for.cond9
  %p64 = sext i32 %p to i64
  br label %for.cond12

for.cond12:                                        ; preds = %for.body14, %for.body11
  %s = phi i32 [ 0, %for.body11 ], [ %inc, %for.body14 ]
  %sumacc = phi double [ 0.000000e+00, %for.body11 ], [ %add27, %for.body14 ]
  %cmp13 = icmp slt i32 %s, %np
  br i1 %cmp13, label %for.body14, label %for.end

for.body14:                                       ; preds = %for.cond12
  %s64 = sext i32 %s to i64
  %arrayidx20 = getelementptr inbounds double, ptr %Abase, i64 %s64
  %aval = load double, ptr %arrayidx20, align 8
  %c4mul = mul nsw i64 %s64, %np64
  %arrayidx22 = getelementptr inbounds double, ptr %C4, i64 %c4mul
  %arrayidx24 = getelementptr inbounds double, ptr %arrayidx22, i64 %p64
  %cval = load double, ptr %arrayidx24, align 8
  %mul = fmul double %aval, %cval
  %add27 = fadd double %sumacc, %mul
  %inc = add nsw i32 %s, 1
  br label %for.cond12, !llvm.loop !6

for.end:                                          ; preds = %for.cond12
  %sum.ptr = getelementptr inbounds double, ptr %sum, i64 %p64
  store double %sumacc, ptr %sum.ptr, align 8
  br label %for.inc28

for.inc28:                                        ; preds = %for.end
  %inc29 = add nsw i32 %p, 1
  br label %for.cond9, !llvm.loop !8

for.end30:                                        ; preds = %for.cond9
  br label %for.cond31

for.cond31:                                       ; preds = %for.inc42, %for.end30
  %p2 = phi i32 [ 0, %for.end30 ], [ %inc43, %for.inc42 ]
  %cmp32 = icmp slt i32 %p2, %np
  br i1 %cmp32, label %for.body33, label %for.end44

for.body33:                                       ; preds = %for.cond31
  %p2.64 = sext i32 %p2 to i64
  %sum.ld.ptr = getelementptr inbounds double, ptr %sum, i64 %p2.64
  %sumval = load double, ptr %sum.ld.ptr, align 8
  %Awrite = getelementptr inbounds double, ptr %Abase, i64 %p2.64
  store double %sumval, ptr %Awrite, align 8
  br label %for.inc42

for.inc42:                                        ; preds = %for.body33
  %inc43 = add nsw i32 %p2, 1
  br label %for.cond31, !llvm.loop !9

for.end44:                                        ; preds = %for.cond31
  br label %for.inc45

for.inc45:                                        ; preds = %for.end44
  %inc46 = add nsw i32 %q, 1
  %cmp7 = icmp slt i32 %inc46, %nq
  br i1 %cmp7, label %for.cond6, label %for.end47, !llvm.loop !10

for.end47:                                        ; preds = %for.inc45
  br label %for.inc48

for.inc48:                                        ; preds = %for.end47
  %inc49 = add nsw i32 %r, 1
  %cmp = icmp slt i32 %inc49, %nr
  br i1 %cmp, label %for.cond, label %for.end50, !llvm.loop !11

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
