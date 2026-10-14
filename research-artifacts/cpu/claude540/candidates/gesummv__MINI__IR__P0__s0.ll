; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.outer = icmp sgt i32 %n, 0
  br i1 %cmp.outer, label %for.outer.preheader, label %for.end46

for.outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc44, %for.outer.preheader
  %i = phi i32 [ 0, %for.outer.preheader ], [ %inc45, %for.inc44 ]
  %i64 = sext i32 %i to i64

  %arrayidx.tmp.i = getelementptr inbounds double, ptr %tmp, i64 %i64
  store double 0.000000e+00, ptr %arrayidx.tmp.i, align 8
  %arrayidx.y.i = getelementptr inbounds double, ptr %y, i64 %i64
  store double 0.000000e+00, ptr %arrayidx.y.i, align 8

  %Arow = mul nsw i64 %i64, %n64
  %Abase = getelementptr inbounds double, ptr %A, i64 %Arow
  %Brow = mul nsw i64 %i64, %n64
  %Bbase = getelementptr inbounds double, ptr %B, i64 %Brow

  %cmp.inner = icmp sgt i32 %n, 0
  br i1 %cmp.inner, label %for.body11.preheader, label %for.end

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %j = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]
  %j64 = sext i32 %j to i64

  %arrayidx15 = getelementptr inbounds double, ptr %Abase, i64 %j64
  %a.val = load double, ptr %arrayidx15, align 8
  %arrayidx17 = getelementptr inbounds double, ptr %x, i64 %j64
  %x.val = load double, ptr %arrayidx17, align 8
  %mul = fmul double %a.val, %x.val
  %add20 = fadd double %mul, %tmp.acc

  %arrayidx26 = getelementptr inbounds double, ptr %Bbase, i64 %j64
  %b.val = load double, ptr %arrayidx26, align 8
  %mul29 = fmul double %b.val, %x.val
  %add32 = fadd double %mul29, %y.acc

  %inc = add nsw i32 %j, 1
  %cmp10 = icmp slt i32 %inc, %n
  br i1 %cmp10, label %for.body11, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:
  %tmp.final = phi double [ %add20, %for.body11 ]
  %y.final = phi double [ %add32, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %tmp.res = phi double [ 0.000000e+00, %for.body ], [ %tmp.final, %for.end.loopexit ]
  %y.res = phi double [ 0.000000e+00, %for.body ], [ %y.final, %for.end.loopexit ]

  store double %tmp.res, ptr %arrayidx.tmp.i, align 8
  store double %y.res, ptr %arrayidx.y.i, align 8

  %mul37 = fmul double %alpha, %tmp.res
  %mul40 = fmul double %beta, %y.res
  %add41 = fadd double %mul37, %mul40
  store double %add41, ptr %arrayidx.y.i, align 8
  br label %for.inc44

for.inc44:                                        ; preds = %for.end
  %inc45 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc45, %n
  br i1 %cmp, label %for.body, label %for.end46.loopexit, !llvm.loop !8

for.end46.loopexit:
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
