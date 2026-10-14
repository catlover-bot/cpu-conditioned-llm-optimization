; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp47 = icmp sgt i32 %n, 0
  br i1 %cmp47, label %for.body.preheader, label %for.end46

for.body.preheader:
  %n64 = zext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.body.preheader, %for.inc44
  %i.048 = phi i64 [ 0, %for.body.preheader ], [ %inc45, %for.inc44 ]

  %tmp.i.ptr = getelementptr inbounds double, ptr %tmp, i64 %i.048
  store double 0.000000e+00, ptr %tmp.i.ptr, align 8
  %y.i.ptr = getelementptr inbounds double, ptr %y, i64 %i.048
  store double 0.000000e+00, ptr %y.i.ptr, align 8

  %cmp10.49 = icmp sgt i32 %n, 0
  br i1 %cmp10.49, label %for.body11.preheader, label %for.end

for.body11.preheader:
  %Arow = mul nsw i64 %i.048, %n64
  %Arowptr = getelementptr inbounds double, ptr %A, i64 %Arow
  %Browmul = mul nsw i64 %i.048, %n64
  %Browptr = getelementptr inbounds double, ptr %B, i64 %Browmul
  br label %for.body11

for.body11:                                       ; preds = %for.body11.preheader, %for.body11
  %j.050 = phi i64 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %tmp_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add20, %for.body11 ]
  %y_acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add32, %for.body11 ]

  %Aelt = getelementptr inbounds double, ptr %Arowptr, i64 %j.050
  %Aval = load double, ptr %Aelt, align 8
  %xelt = getelementptr inbounds double, ptr %x, i64 %j.050
  %xval = load double, ptr %xelt, align 8
  %mul = fmul double %Aval, %xval
  %add20 = fadd double %mul, %tmp_acc

  %Belt = getelementptr inbounds double, ptr %Browptr, i64 %j.050
  %Bval = load double, ptr %Belt, align 8
  %mul29 = fmul double %Bval, %xval
  %add32 = fadd double %mul29, %y_acc

  %inc = add nsw i64 %j.050, 1
  %cmp10 = icmp slt i64 %inc, %n64
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:
  store double %add20, ptr %tmp.i.ptr, align 8
  store double %add32, ptr %y.i.ptr, align 8
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %tmp_final = phi double [ 0.000000e+00, %for.body ], [ %add20, %for.end.loopexit ]
  %y_final = phi double [ 0.000000e+00, %for.body ], [ %add32, %for.end.loopexit ]

  %mul37 = fmul double %alpha, %tmp_final
  %mul40 = fmul double %beta, %y_final
  %add41 = fadd double %mul37, %mul40
  store double %add41, ptr %y.i.ptr, align 8
  br label %for.inc44

for.inc44:                                        ; preds = %for.end
  %inc45 = add nsw i64 %i.048, 1
  %cmp = icmp slt i64 %inc45, %n64
  br i1 %cmp, label %for.body, label %for.end46.loopexit

for.end46.loopexit:
  br label %for.end46

for.end46:                                         ; preds = %for.end46.loopexit, %entry
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
