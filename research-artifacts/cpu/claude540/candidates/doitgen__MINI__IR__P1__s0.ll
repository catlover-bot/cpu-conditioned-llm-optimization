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
  br i1 %run2, label %preheader, label %for.end50

preheader:
  %nq64 = zext i32 %nq to i64
  %np64 = zext i32 %np to i64
  %nqnp = mul nuw i64 %nq64, %np64
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %preheader
  %r = phi i32 [ 0, %preheader ], [ %inc49, %for.inc48 ]
  %r64 = zext i32 %r to i64
  %Aroff = mul nsw i64 %r64, %nqnp
  br label %for.body8

for.body8:                                        ; preds = %for.cond, %for.end47
  %q = phi i32 [ 0, %for.cond ], [ %inc46, %for.end47 ]
  %q64 = zext i32 %q to i64
  %qoff = mul nsw i64 %q64, %np64
  %Arqoff = add nsw i64 %Aroff, %qoff
  %Arow.base = getelementptr inbounds double, ptr %A, i64 %Arqoff
  br label %for.body11

for.body11:                                       ; preds = %for.body8, %for.inc28
  %p = phi i32 [ 0, %for.body8 ], [ %inc29, %for.inc28 ]
  %p64.0 = zext i32 %p to i64
  %sum.p.ptr = getelementptr inbounds double, ptr %sum, i64 %p64.0
  store double 0.000000e+00, ptr %sum.p.ptr, align 8
  br label %for.body14

for.body14:                                       ; preds = %for.body11, %for.body14
  %s = phi i32 [ 0, %for.body11 ], [ %inc, %for.body14 ]
  %s64 = zext i32 %s to i64
  %Aval.ptr = getelementptr inbounds double, ptr %Arow.base, i64 %s64
  %Aval = load double, ptr %Aval.ptr, align 8
  %C4soff = mul nsw i64 %s64, %np64
  %C4row.base = getelementptr inbounds double, ptr %C4, i64 %C4soff
  %C4val.ptr = getelementptr inbounds double, ptr %C4row.base, i64 %p64.0
  %C4val = load double, ptr %C4val.ptr, align 8
  %mul = fmul double %Aval, %C4val
  %sumcur = load double, ptr %sum.p.ptr, align 8
  %add27 = fadd double %sumcur, %mul
  store double %add27, ptr %sum.p.ptr, align 8
  %inc = add nsw i32 %s, 1
  %cmp13 = icmp slt i32 %inc, %np
  br i1 %cmp13, label %for.body14, label %for.end

for.end:                                          ; preds = %for.body14
  %inc29 = add nsw i32 %p, 1
  %cmp10 = icmp slt i32 %inc29, %np
  br i1 %cmp10, label %for.body11, label %for.end30

for.inc28:                                        ; no predecessors
  br label %for.body11

for.end30:                                        ; preds = %for.end
  br label %for.body33

for.body33:                                       ; preds = %for.end30, %for.body33
  %p2 = phi i32 [ 0, %for.end30 ], [ %inc43, %for.body33 ]
  %p2.64 = zext i32 %p2 to i64
  %sum2.ptr = getelementptr inbounds double, ptr %sum, i64 %p2.64
  %sumval = load double, ptr %sum2.ptr, align 8
  %Adst.ptr = getelementptr inbounds double, ptr %Arow.base, i64 %p2.64
  store double %sumval, ptr %Adst.ptr, align 8
  %inc43 = add nsw i32 %p2, 1
  %cmp32 = icmp slt i32 %inc43, %np
  br i1 %cmp32, label %for.body33, label %for.end44

for.end44:                                        ; preds = %for.body33
  br label %for.end47

for.end47:                                        ; preds = %for.end44
  %inc46 = add nsw i32 %q, 1
  %cmp7 = icmp slt i32 %inc46, %nq
  br i1 %cmp7, label %for.body8, label %for.inc48

for.inc48:                                        ; preds = %for.end47
  %inc49 = add nsw i32 %r, 1
  %cmp = icmp slt i32 %inc49, %nr
  br i1 %cmp, label %for.cond, label %for.end50.loopexit

for.end50.loopexit:                               ; preds = %for.inc48
  br label %for.end50

for.end50:                                        ; preds = %for.end50.loopexit, %entry
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
