; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp0 = icmp sgt i32 %n, 0
  br i1 %cmp0, label %preheader, label %for.end46

preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.end, %preheader
  %i = phi i64 [ 0, %preheader ], [ %inc45, %for.end ]

  %row_off = mul nsw i64 %i, %n64
  %A_row = getelementptr inbounds double, ptr %A, i64 %row_off
  %B_row = getelementptr inbounds double, ptr %B, i64 %row_off

  %cmpj = icmp sgt i32 %n, 0
  br i1 %cmpj, label %for.body11.preheader, label %for.end

for.body11.preheader:
  br label %for.body11

for.body11:                                       ; preds = %for.body11, %for.body11.preheader
  %j = phi i64 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]

  %arrayidx15 = getelementptr inbounds double, ptr %A_row, i64 %j
  %a_val = load double, ptr %arrayidx15, align 8
  %arrayidx17 = getelementptr inbounds double, ptr %x, i64 %j
  %x_val = load double, ptr %arrayidx17, align 8
  %mul = fmul double %a_val, %x_val
  %add20 = fadd double %mul, %tmp_acc

  %arrayidx26 = getelementptr inbounds double, ptr %B_row, i64 %j
  %b_val = load double, ptr %arrayidx26, align 8
  %mul29 = fmul double %b_val, %x_val
  %add32 = fadd double %mul29, %y_acc

  %inc = add nsw i64 %j, 1
  %cmpj2 = icmp slt i64 %inc, %n64
  br i1 %cmpj2, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  %tmp_final = phi double [ %add20, %for.body11 ]
  %y_final = phi double [ %add32, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %tmp_val = phi double [ 0.000000e+00, %for.body ], [ %tmp_final, %for.end.loopexit ]
  %y_val = phi double [ 0.000000e+00, %for.body ], [ %y_final, %for.end.loopexit ]

  %arrayidx_tmp = getelementptr inbounds double, ptr %tmp, i64 %i
  store double %tmp_val, ptr %arrayidx_tmp, align 8

  %mul37 = fmul double %alpha, %tmp_val
  %mul40 = fmul double %beta, %y_val
  %add41 = fadd double %mul37, %mul40

  %arrayidx43 = getelementptr inbounds double, ptr %y, i64 %i
  store double %add41, ptr %arrayidx43, align 8

  %inc45 = add nsw i64 %i, 1
  %cmp = icmp slt i64 %inc45, %n64
  br i1 %cmp, label %for.body, label %for.end46

for.end46:                                        ; preds = %for.end, %entry
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
