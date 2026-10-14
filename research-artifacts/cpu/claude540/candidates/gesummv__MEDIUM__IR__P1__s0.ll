; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end46

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc44, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc45, %for.inc44 ]

  %arow.base = mul nsw i64 %i, %n64
  %Arow = getelementptr inbounds double, ptr %A, i64 %arow.base
  %Brow = getelementptr inbounds double, ptr %B, i64 %arow.base

  %cmp.inner = icmp sgt i32 %n, 0
  br i1 %cmp.inner, label %for.body11.preheader, label %for.end.zero

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %j = phi i64 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]

  %arrayidx15 = getelementptr inbounds double, ptr %Arow, i64 %j
  %a.val = load double, ptr %arrayidx15, align 8
  %arrayidx17 = getelementptr inbounds double, ptr %x, i64 %j
  %x.val = load double, ptr %arrayidx17, align 8
  %mul = fmul double %a.val, %x.val
  %add20 = fadd double %mul, %tmp.acc

  %arrayidx26 = getelementptr inbounds double, ptr %Brow, i64 %j
  %b.val = load double, ptr %arrayidx26, align 8
  %mul29 = fmul double %b.val, %x.val
  %add32 = fadd double %mul29, %y.acc

  %inc = add nsw i64 %j, 1
  %cmp10 = icmp slt i64 %inc, %n64
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  %tmp.final = phi double [ %add20, %for.body11 ]
  %y.final = phi double [ %add32, %for.body11 ]
  br label %for.end

for.end.zero:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.end.zero
  %tmp.res = phi double [ %tmp.final, %for.end.loopexit ], [ 0.000000e+00, %for.end.zero ]
  %y.res = phi double [ %y.final, %for.end.loopexit ], [ 0.000000e+00, %for.end.zero ]

  %arrayidx36 = getelementptr inbounds double, ptr %tmp, i64 %i
  store double %tmp.res, ptr %arrayidx36, align 8

  %mul37 = fmul double %alpha, %tmp.res
  %mul40 = fmul double %beta, %y.res
  %add41 = fadd double %mul37, %mul40

  %arrayidx43 = getelementptr inbounds double, ptr %y, i64 %i
  store double %add41, ptr %arrayidx43, align 8

  br label %for.inc44

for.inc44:                                        ; preds = %for.end
  %inc45 = add nsw i64 %i, 1
  %cmp = icmp slt i64 %inc45, %n64
  br i1 %cmp, label %for.body, label %for.end46.loopexit

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
