; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer1.preheader, label %outer2.check

outer1.preheader:
  %n64 = sext i32 %n to i64
  br label %outer1

outer1:                                           ; preds = %outer1.preheader, %outer1.latch
  %i1 = phi i64 [ 0, %outer1.preheader ], [ %i1.next, %outer1.latch ]
  %x1elem.ptr = getelementptr inbounds double, ptr %x1, i64 %i1
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %i1
  %rowoff1 = mul nsw i64 %i1, %n64
  %Arowbase1 = getelementptr inbounds double, ptr %A, i64 %rowoff1
  %x1v.init = load double, ptr %x1elem.ptr, align 8
  br label %inner1

inner1:                                           ; preds = %outer1, %inner1
  %j1 = phi i64 [ 0, %outer1 ], [ %j1.next, %inner1 ]
  %acc1 = phi double [ %x1v.init, %outer1 ], [ %add15, %inner1 ]
  %Aptr1 = getelementptr inbounds double, ptr %Arowbase1, i64 %j1
  %Aval1 = load double, ptr %Aptr1, align 8
  %y1ptr = getelementptr inbounds double, ptr %y_1, i64 %j1
  %y1val = load double, ptr %y1ptr, align 8
  %mul1 = fmul double %Aval1, %y1val
  %add15 = fadd double %acc1, %mul1
  %j1.next = add nuw nsw i64 %j1, 1
  %cmp.inner1 = icmp slt i64 %j1.next, %n64
  br i1 %cmp.inner1, label %inner1, label %outer1.latch

outer1.latch:                                     ; preds = %inner1
  store double %add15, ptr %x1elem.ptr, align 8
  %i1.next = add nuw nsw i64 %i1, 1
  %cmp.outer1 = icmp slt i64 %i1.next, %n64
  br i1 %cmp.outer1, label %outer1, label %outer2.check

outer2.check:                                     ; preds = %entry, %outer1.latch
  br i1 %cmp.n, label %outer2.preheader, label %exit

outer2.preheader:
  %n64.2 = sext i32 %n to i64
  br label %outer2

outer2:                                           ; preds = %outer2.preheader, %outer2.latch
  %i2 = phi i64 [ 0, %outer2.preheader ], [ %i2.next, %outer2.latch ]
  %x2elem.ptr = getelementptr inbounds double, ptr %x2, i64 %i2
  %x2v.init = load double, ptr %x2elem.ptr, align 8
  br label %inner2

inner2:                                           ; preds = %outer2, %inner2
  %j2 = phi i64 [ 0, %outer2 ], [ %j2.next, %inner2 ]
  %acc2 = phi double [ %x2v.init, %outer2 ], [ %add36, %inner2 ]
  %rowoff2 = mul nsw i64 %j2, %n64.2
  %Arowbase2 = getelementptr inbounds double, ptr %A, i64 %rowoff2
  %Aptr2 = getelementptr inbounds double, ptr %Arowbase2, i64 %i2
  %Aval2 = load double, ptr %Aptr2, align 8
  %y2ptr = getelementptr inbounds double, ptr %y_2, i64 %j2
  %y2val = load double, ptr %y2ptr, align 8
  %mul2 = fmul double %Aval2, %y2val
  %add36 = fadd double %acc2, %mul2
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp.inner2 = icmp slt i64 %j2.next, %n64.2
  br i1 %cmp.inner2, label %inner2, label %outer2.latch

outer2.latch:                                     ; preds = %inner2
  store double %add36, ptr %x2elem.ptr, align 8
  %i2.next = add nuw nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %n64.2
  br i1 %cmp.outer2, label %outer2, label %exit

exit:                                             ; preds = %outer2.check, %outer2.latch
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
