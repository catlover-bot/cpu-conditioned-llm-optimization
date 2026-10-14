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
  %nqnp = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %preheader
  %r = phi i32 [ 0, %preheader ], [ %inc49, %for.inc48 ]
  br i1 %cmp.nq, label %for.body.q.preheader, label %for.inc48

for.body.q.preheader:
  %r64 = zext i32 %r to i64
  %rbase = mul nuw i64 %r64, %nqnp
  br label %for.cond6

for.cond6:                                         ; preds = %for.inc45, %for.body.q.preheader
  %q = phi i32 [ 0, %for.body.q.preheader ], [ %inc46, %for.inc45 ]
  br i1 %cmp.np, label %for.body.p1.preheader, label %for.inc45

for.body.p1.preheader:
  %q64 = zext i32 %q to i64
  %qbase = mul nuw i64 %q64, %np64
  %rq_base = add nuw i64 %rbase, %qbase
  %Arow = getelementptr inbounds double, ptr %A, i64 %rq_base
  br label %for.cond9

for.cond9:                                         ; preds = %for.inc28, %for.body.p1.preheader
  %p1 = phi i32 [ 0, %for.body.p1.preheader ], [ %inc29, %for.inc28 ]
  %p1.64 = zext i32 %p1 to i64
  %sum.p1 = getelementptr inbounds double, ptr %sum, i64 %p1.64
  store double 0.000000e+00, ptr %sum.p1, align 8
  br i1 %cmp.np, label %for.body14.preheader, label %for.end

for.body14.preheader:
  %C4col = getelementptr inbounds double, ptr %C4, i64 %p1.64
  br label %for.body14

for.body14:                                        ; preds = %for.body14.preheader, %for.body14
  %s = phi i32 [ 0, %for.body14.preheader ], [ %inc, %for.body14 ]
  %s64 = zext i32 %s to i64
  %acc = phi double [ 0.000000e+00, %for.body14.preheader ], [ %add27, %for.body14 ]
  %Aelt = getelementptr inbounds double, ptr %Arow, i64 %s64
  %aval = load double, ptr %Aelt, align 8
  %C4rowoff = mul nsw i64 %s64, %np64
  %C4elt = getelementptr inbounds double, ptr %C4col, i64 %C4rowoff
  %cval = load double, ptr %C4elt, align 8
  %mul = fmul double %aval, %cval
  %add27 = fadd double %acc, %mul
  %inc = add nsw i32 %s, 1
  %cmp13 = icmp slt i32 %inc, %np
  br i1 %cmp13, label %for.body14, label %for.end.loopexit

for.end.loopexit:
  store double %add27, ptr %sum.p1, align 8
  br label %for.end

for.end:                                           ; preds = %for.end.loopexit, %for.cond9
  br label %for.inc28

for.inc28:                                         ; preds = %for.end
  %inc29 = add nsw i32 %p1, 1
  %cmp10 = icmp slt i32 %inc29, %np
  br i1 %cmp10, label %for.cond9, label %for.end30

for.end30:                                         ; preds = %for.inc28, %for.cond6
  br i1 %cmp.np, label %for.body33.preheader, label %for.inc45

for.body33.preheader:
  %Arow2 = getelementptr inbounds double, ptr %A, i64 %rq_base
  br label %for.body33

for.body33:                                        ; preds = %for.body33.preheader, %for.body33
  %p2 = phi i32 [ 0, %for.body33.preheader ], [ %inc43, %for.body33 ]
  %p2.64 = zext i32 %p2 to i64
  %sum.p2 = getelementptr inbounds double, ptr %sum, i64 %p2.64
  %sumval = load double, ptr %sum.p2, align 8
  %Aelt2 = getelementptr inbounds double, ptr %Arow2, i64 %p2.64
  store double %sumval, ptr %Aelt2, align 8
  %inc43 = add nsw i32 %p2, 1
  %cmp32 = icmp slt i32 %inc43, %np
  br i1 %cmp32, label %for.body33, label %for.inc45.loopexit

for.inc45.loopexit:
  br label %for.inc45

for.inc45:                                         ; preds = %for.inc45.loopexit, %for.end30, %for.cond6
  %inc46 = add nsw i32 %q, 1
  %cmp7 = icmp slt i32 %inc46, %nq
  br i1 %cmp7, label %for.cond6, label %for.inc48.loopexit

for.inc48.loopexit:
  br label %for.inc48

for.inc48:                                         ; preds = %for.inc48.loopexit, %for.cond
  %inc49 = add nsw i32 %r, 1
  %cmp = icmp slt i32 %inc49, %nr
  br i1 %cmp, label %for.cond, label %for.end50.loopexit

for.end50.loopexit:
  br label %for.end50

for.end50:                                         ; preds = %for.end50.loopexit, %entry
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
