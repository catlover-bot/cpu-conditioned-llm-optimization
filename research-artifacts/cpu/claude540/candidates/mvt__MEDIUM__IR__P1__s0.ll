; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end44

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %outer.preheader, %for.inc18
  %i = phi i32 [ 0, %outer.preheader ], [ %inc19, %for.inc18 ]
  %i64 = sext i32 %i to i64
  %x1.elem = getelementptr inbounds double, ptr %x1, i64 %i64
  %x1.val0 = load double, ptr %x1.elem, align 8
  %row.off = mul nsw i64 %i64, %n64
  %A.row = getelementptr inbounds double, ptr %A, i64 %row.off
  br label %for.body8

for.body8:                                        ; preds = %for.body, %for.body8
  %j = phi i32 [ 0, %for.body ], [ %inc, %for.body8 ]
  %acc = phi double [ %x1.val0, %for.body ], [ %add15, %for.body8 ]
  %j64 = sext i32 %j to i64
  %A.elem = getelementptr inbounds double, ptr %A.row, i64 %j64
  %A.val = load double, ptr %A.elem, align 8
  %y1.elem = getelementptr inbounds double, ptr %y_1, i64 %j64
  %y1.val = load double, ptr %y1.elem, align 8
  %mul = fmul double %A.val, %y1.val
  %add15 = fadd double %acc, %mul
  %inc = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc, %n
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body8
  store double %add15, ptr %x1.elem, align 8
  br label %for.inc18

for.inc18:                                        ; preds = %for.end.loopexit
  %inc19 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc19, %n
  br i1 %cmp, label %for.body, label %for.end20

for.end20:                                        ; preds = %for.inc18
  br label %outer2.preheader

outer2.preheader:
  br label %for.body23

for.body23:                                       ; preds = %outer2.preheader, %for.inc42
  %i2 = phi i32 [ 0, %outer2.preheader ], [ %inc43, %for.inc42 ]
  %i2_64 = sext i32 %i2 to i64
  %x2.elem = getelementptr inbounds double, ptr %x2, i64 %i2_64
  %x2.val0 = load double, ptr %x2.elem, align 8
  br label %for.body26

for.body26:                                       ; preds = %for.body23, %for.body26
  %j2 = phi i32 [ 0, %for.body23 ], [ %inc40, %for.body26 ]
  %acc2 = phi double [ %x2.val0, %for.body23 ], [ %add36, %for.body26 ]
  %j2_64 = sext i32 %j2 to i64
  %row2.off = mul nsw i64 %j2_64, %n64
  %A2.row = getelementptr inbounds double, ptr %A, i64 %row2.off
  %A2.elem = getelementptr inbounds double, ptr %A2.row, i64 %i2_64
  %A2.val = load double, ptr %A2.elem, align 8
  %y2.elem = getelementptr inbounds double, ptr %y_2, i64 %j2_64
  %y2.val = load double, ptr %y2.elem, align 8
  %mul35 = fmul double %A2.val, %y2.val
  %add36 = fadd double %acc2, %mul35
  %inc40 = add nsw i32 %j2, 1
  %cmp25 = icmp slt i32 %inc40, %n
  br i1 %cmp25, label %for.body26, label %for.end41.loopexit

for.end41.loopexit:                               ; preds = %for.body26
  store double %add36, ptr %x2.elem, align 8
  br label %for.inc42

for.inc42:                                        ; preds = %for.end41.loopexit
  %inc43 = add nsw i32 %i2, 1
  %cmp22 = icmp slt i32 %inc43, %n
  br i1 %cmp22, label %for.body23, label %for.end44

for.end44:                                        ; preds = %entry, %for.inc42
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
