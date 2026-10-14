; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.outer = icmp slt i32 0, %n
  br i1 %cmp.outer, label %for.cond.preheader, label %for.end46

for.cond.preheader:                               ; preds = %entry
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc44, %for.cond.preheader
  %i.02 = phi i32 [ 0, %for.cond.preheader ], [ %inc45, %for.inc44 ]
  %i64 = sext i32 %i.02 to i64
  %arrayidx.tmp = getelementptr inbounds double, ptr %tmp, i64 %i64
  %arrayidx.y = getelementptr inbounds double, ptr %y, i64 %i64
  %row.A = mul nsw i64 %i64, %n64
  %rowptr.A = getelementptr inbounds double, ptr %A, i64 %row.A
  %row.B = mul nsw i64 %i64, %n64
  %rowptr.B = getelementptr inbounds double, ptr %B, i64 %row.B

  %cmp.inner = icmp slt i32 0, %n
  br i1 %cmp.inner, label %for.body11.preheader, label %for.end.loopexit0

for.body11.preheader:                             ; preds = %for.body
  br label %for.body11

for.body11:                                       ; preds = %for.body11.preheader, %for.body11
  %j.01 = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]
  %j64 = sext i32 %j.01 to i64

  %arrayidx15 = getelementptr inbounds double, ptr %rowptr.A, i64 %j64
  %a.val = load double, ptr %arrayidx15, align 8
  %arrayidx17 = getelementptr inbounds double, ptr %x, i64 %j64
  %x.val = load double, ptr %arrayidx17, align 8
  %mul = fmul double %a.val, %x.val
  %add20 = fadd double %mul, %tmp.acc

  %arrayidx26 = getelementptr inbounds double, ptr %rowptr.B, i64 %j64
  %b.val = load double, ptr %arrayidx26, align 8
  %mul29 = fmul double %b.val, %x.val
  %add32 = fadd double %mul29, %y.acc

  %inc = add nsw i32 %j.01, 1
  %cmp10 = icmp slt i32 %inc, %n
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body11
  store double %add20, ptr %arrayidx.tmp, align 8
  store double %add32, ptr %arrayidx.y, align 8
  br label %for.end

for.end.loopexit0:                                ; preds = %for.body
  store double 0.000000e+00, ptr %arrayidx.tmp, align 8
  store double 0.000000e+00, ptr %arrayidx.y, align 8
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.end.loopexit0
  %tmp.final = load double, ptr %arrayidx.tmp, align 8
  %mul37 = fmul double %alpha, %tmp.final
  %y.final = load double, ptr %arrayidx.y, align 8
  %mul40 = fmul double %beta, %y.final
  %add41 = fadd double %mul37, %mul40
  store double %add41, ptr %arrayidx.y, align 8
  br label %for.inc44

for.inc44:                                        ; preds = %for.end
  %inc45 = add nsw i32 %i.02, 1
  %cmp.next = icmp slt i32 %inc45, %n
  br i1 %cmp.next, label %for.body, label %for.end46.loopexit

for.end46.loopexit:                               ; preds = %for.inc44
  br label %for.end46

for.end46:                                        ; preds = %for.end46.loopexit, %entry
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
