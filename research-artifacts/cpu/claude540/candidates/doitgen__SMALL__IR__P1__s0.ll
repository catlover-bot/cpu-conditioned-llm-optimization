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
  %np64 = zext i32 %np to i64
  %nq64 = zext i32 %nq to i64
  %stride_r = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:
  %r = phi i32 [ 0, %preheader ], [ %inc49, %for.inc48 ]
  br i1 %cmp.nq0, label %for.body.q.check, label %for.inc48

for.body.q.check:
  br i1 %cmp.np0, label %for.body, label %for.inc48

for.body:
  br label %for.cond6

for.cond6:
  %q = phi i32 [ 0, %for.body ], [ %inc46, %for.inc45 ]
  %r64 = sext i32 %r to i64
  %q64 = sext i32 %q to i64
  %rbase = mul nsw i64 %r64, %stride_r
  %qoff = mul nsw i64 %q64, %np64
  %Abase64 = add i64 %rbase, %qoff
  %Abaseptr = getelementptr inbounds double, ptr %A, i64 %Abase64

  br label %for.body8

for.body8:
  %p = phi i32 [ 0, %for.cond6 ], [ %inc29, %for.inc28 ]
  %sumidx = sext i32 %p to i64
  %sumptr = getelementptr inbounds double, ptr %sum, i64 %sumidx
  store double 0.000000e+00, ptr %sumptr, align 8
  br i1 %cmp.np0, label %for.body14.preheader, label %for.end

for.body14.preheader:
  br label %for.cond12

for.cond12:
  %s = phi i32 [ 0, %for.body14.preheader ], [ %inc, %for.cond12 ]
  %acc = phi double [ 0.000000e+00, %for.body14.preheader ], [ %add27, %for.cond12 ]
  %s64 = sext i32 %s to i64
  %Aelptr = getelementptr inbounds double, ptr %Abaseptr, i64 %s64
  %Aval = load double, ptr %Aelptr, align 8
  %Crow64 = mul nsw i64 %s64, %np64
  %Crowptr = getelementptr inbounds double, ptr %C4, i64 %Crow64
  %p64 = sext i32 %p to i64
  %Celptr = getelementptr inbounds double, ptr %Crowptr, i64 %p64
  %Cval = load double, ptr %Celptr, align 8
  %mul = fmul double %Aval, %Cval
  %add27 = fadd double %acc, %mul
  %inc = add nsw i32 %s, 1
  %cmp13 = icmp slt i32 %inc, %np
  br i1 %cmp13, label %for.cond12, label %for.end.loopexit

for.end.loopexit:
  store double %add27, ptr %sumptr, align 8
  br label %for.end

for.end:
  br label %for.inc28

for.inc28:
  %inc29 = add nsw i32 %p, 1
  %cmp10 = icmp slt i32 %inc29, %np
  br i1 %cmp10, label %for.body8, label %for.end30

for.end30:
  br i1 %cmp.np0, label %for.body33.preheader, label %for.end44

for.body33.preheader:
  br label %for.body33

for.body33:
  %p2 = phi i32 [ 0, %for.body33.preheader ], [ %inc43, %for.body33 ]
  %sumidx2 = sext i32 %p2 to i64
  %sumptr2 = getelementptr inbounds double, ptr %sum, i64 %sumidx2
  %sumval = load double, ptr %sumptr2, align 8
  %p264 = sext i32 %p2 to i64
  %Adstptr = getelementptr inbounds double, ptr %Abaseptr, i64 %p264
  store double %sumval, ptr %Adstptr, align 8
  %inc43 = add nsw i32 %p2, 1
  %cmp32 = icmp slt i32 %inc43, %np
  br i1 %cmp32, label %for.body33, label %for.end44

for.end44:
  br label %for.inc45

for.inc45:
  %inc46 = add nsw i32 %q, 1
  %cmp7 = icmp slt i32 %inc46, %nq
  br i1 %cmp7, label %for.cond6, label %for.end47

for.end47:
  br label %for.inc48

for.inc48:
  %inc49 = add nsw i32 %r, 1
  %cmp = icmp slt i32 %inc49, %nr
  br i1 %cmp, label %for.cond, label %for.end50.loopexit

for.end50.loopexit:
  br label %for.end50

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
