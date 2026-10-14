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
  %np64 = zext i32 %np to i64
  %nq64 = zext i32 %nq to i64
  %qstride = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %preheader
  %r = phi i32 [ 0, %preheader ], [ %inc49, %for.inc48 ]
  br i1 %cmp.nq, label %for.body, label %for.inc48

for.body:                                         ; preds = %for.cond
  %r64 = sext i32 %r to i64
  %rbase = mul nsw i64 %r64, %qstride
  %Arbase = getelementptr inbounds double, ptr %A, i64 %rbase
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc45, %for.body
  %q = phi i32 [ 0, %for.body ], [ %inc46, %for.inc45 ]
  br i1 %cmp.np, label %for.body8, label %for.inc45

for.body8:                                        ; preds = %for.cond6
  %q64 = sext i32 %q to i64
  %qoff = mul nsw i64 %q64, %np64
  %Aqbase = getelementptr inbounds double, ptr %Arbase, i64 %qoff
  ; zero-init sum[0..np)
  br label %init.loop

init.loop:
  %ip = phi i32 [ 0, %for.body8 ], [ %ip.inc, %init.loop ]
  %ip64 = sext i32 %ip to i64
  %init.ptr = getelementptr inbounds double, ptr %sum, i64 %ip64
  store double 0.000000e+00, ptr %init.ptr, align 8
  %ip.inc = add nsw i32 %ip, 1
  %init.cmp = icmp slt i32 %ip.inc, %np
  br i1 %init.cmp, label %init.loop, label %for.cond9.preheader

for.cond9.preheader:
  br label %for.cond9

for.cond9:                                         ; preds = %for.inc28, %for.cond9.preheader
  %p = phi i32 [ 0, %for.cond9.preheader ], [ %inc29, %for.inc28 ]
  br i1 %cmp.np, label %for.body11, label %for.end30

for.body11:                                       ; preds = %for.cond9
  %p64.11 = sext i32 %p to i64
  %sum.ptr.11 = getelementptr inbounds double, ptr %sum, i64 %p64.11
  br label %for.cond12

for.cond12:                                       ; preds = %for.inc, %for.body11
  %s = phi i32 [ 0, %for.body11 ], [ %inc, %for.inc ]
  %acc = phi double [ 0.000000e+00, %for.body11 ], [ %add27, %for.inc ]
  br i1 %cmp.np, label %check.s, label %for.end.store

check.s:
  %s.cmp = icmp slt i32 %s, %np
  br i1 %s.cmp, label %for.body14, label %for.end.store

for.body14:                                       ; preds = %check.s
  %s64 = sext i32 %s to i64
  %Asp = getelementptr inbounds double, ptr %Aqbase, i64 %s64
  %aval = load double, ptr %Asp, align 8
  %C4rowoff = mul nsw i64 %s64, %np64
  %C4row = getelementptr inbounds double, ptr %C4, i64 %C4rowoff
  %C4p = getelementptr inbounds double, ptr %C4row, i64 %p64.11
  %cval = load double, ptr %C4p, align 8
  %mul = fmul double %aval, %cval
  %add27 = fadd double %acc, %mul
  br label %for.inc

for.inc:                                          ; preds = %for.body14
  %inc = add nsw i32 %s, 1
  br label %for.cond12, !llvm.loop !6

for.end.store:
  store double %acc, ptr %sum.ptr.11, align 8
  br label %for.inc28

for.inc28:                                        ; preds = %for.end.store
  %inc29 = add nsw i32 %p, 1
  %cmp.p28 = icmp slt i32 %inc29, %np
  br i1 %cmp.p28, label %for.cond9, label %for.end30, !llvm.loop !8

for.end30:                                        ; preds = %for.cond9, %for.cond9.preheader
  br i1 %cmp.np, label %for.body33.preheader, label %for.end44

for.body33.preheader:
  br label %for.body33

for.body33:                                        ; preds = %for.inc42, %for.body33.preheader
  %p2 = phi i32 [ 0, %for.body33.preheader ], [ %inc43, %for.inc42 ]
  %p2_64 = sext i32 %p2 to i64
  %sum.ptr.33 = getelementptr inbounds double, ptr %sum, i64 %p2_64
  %sval = load double, ptr %sum.ptr.33, align 8
  %Aqp = getelementptr inbounds double, ptr %Aqbase, i64 %p2_64
  store double %sval, ptr %Aqp, align 8
  %inc43 = add nsw i32 %p2, 1
  %cmp.p33 = icmp slt i32 %inc43, %np
  br i1 %cmp.p33, label %for.body33, label %for.end44, !llvm.loop !9

for.end44:                                        ; preds = %for.body33, %for.end30
  br label %for.inc45

for.inc45:                                        ; preds = %for.end44, %for.cond6
  %inc46 = add nsw i32 %q, 1
  %cmp.q45 = icmp slt i32 %inc46, %nq
  br i1 %cmp.q45, label %for.cond6, label %for.inc48, !llvm.loop !10

for.inc48:                                         ; preds = %for.inc45, %for.cond
  %inc49 = add nsw i32 %r, 1
  %cmp.r48 = icmp slt i32 %inc49, %nr
  br i1 %cmp.r48, label %for.cond, label %for.end50, !llvm.loop !11

for.end50:                                         ; preds = %for.inc48, %entry
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
