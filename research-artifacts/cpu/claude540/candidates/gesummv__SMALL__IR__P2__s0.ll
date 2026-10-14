; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.outer = icmp sgt i32 %n, 0
  br i1 %cmp.outer, label %for.body.preheader, label %for.end46

for.body.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.inc44, %for.body.preheader
  %i = phi i32 [ 0, %for.body.preheader ], [ %inc45, %for.inc44 ]
  %i64 = sext i32 %i to i64

  %cmp.inner = icmp sgt i32 %n, 0
  br i1 %cmp.inner, label %for.body11.preheader, label %for.end.loop0

for.body11.preheader:
  %Arow = getelementptr inbounds double, ptr %A, i64 %i64, i64 0
  %Arowbase = mul nsw i64 %i64, %n64
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arowbase
  %Browbase = mul nsw i64 %i64, %n64
  %Browptr = getelementptr inbounds double, ptr %B, i64 %Browbase
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %j = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]
  %j64 = sext i32 %j to i64

  %arrayidx15 = getelementptr inbounds double, ptr %Arowptr, i64 %j64
  %a.val = load double, ptr %arrayidx15, align 8
  %arrayidx17 = getelementptr inbounds double, ptr %x, i64 %j64
  %x.val = load double, ptr %arrayidx17, align 8
  %mul = fmul double %a.val, %x.val
  %add20 = fadd double %mul, %tmp_acc

  %arrayidx26 = getelementptr inbounds double, ptr %Browptr, i64 %j64
  %b.val = load double, ptr %arrayidx26, align 8
  %mul29 = fmul double %b.val, %x.val
  %add32 = fadd double %mul29, %y_acc

  %inc = add nsw i32 %j, 1
  %cmp10 = icmp slt i32 %inc, %n
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  %tmp_final = phi double [ %add20, %for.body11 ]
  %y_final = phi double [ %add32, %for.body11 ]
  br label %for.end

for.end.loop0:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.end.loop0
  %tmp_res = phi double [ %tmp_final, %for.end.loopexit ], [ 0.000000e+00, %for.end.loop0 ]
  %y_res = phi double [ %y_final, %for.end.loopexit ], [ 0.000000e+00, %for.end.loop0 ]

  %arrayidx.tmp.store = getelementptr inbounds double, ptr %tmp, i64 %i64
  store double %tmp_res, ptr %arrayidx.tmp.store, align 8

  %mul37 = fmul double %alpha, %tmp_res
  %mul40 = fmul double %beta, %y_res
  %add41 = fadd double %mul37, %mul40
  %arrayidx43 = getelementptr inbounds double, ptr %y, i64 %i64
  store double %add41, ptr %arrayidx43, align 8

  br label %for.inc44

for.inc44:                                        ; preds = %for.end
  %inc45 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc45, %n
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
