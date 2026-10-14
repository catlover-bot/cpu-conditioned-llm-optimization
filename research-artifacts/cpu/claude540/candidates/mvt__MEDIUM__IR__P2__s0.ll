; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader1, label %for.end20

preheader1:
  %n64 = sext i32 %n to i64
  br label %for.body.outer1

for.body.outer1:                                  ; preds = %for.inc18, %preheader1
  %i1 = phi i64 [ 0, %preheader1 ], [ %inc19, %for.inc18 ]
  %x1addr = getelementptr inbounds double, ptr %x1, i64 %i1
  %x1val0 = load double, ptr %x1addr, align 8
  %Arowoff = mul nsw i64 %i1, %n64
  %Arow = getelementptr inbounds double, ptr %A, i64 %Arowoff
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body.outer1
  %j1 = phi i64 [ 0, %for.body.outer1 ], [ %inc.j1, %for.body8 ]
  %acc1 = phi double [ %x1val0, %for.body.outer1 ], [ %add15, %for.body8 ]
  %Aptr1 = getelementptr inbounds double, ptr %Arow, i64 %j1
  %Aval1 = load double, ptr %Aptr1, align 8
  %y1ptr = getelementptr inbounds double, ptr %y_1, i64 %j1
  %y1val = load double, ptr %y1ptr, align 8
  %mul1 = fmul double %Aval1, %y1val
  %add15 = fadd double %acc1, %mul1
  %inc.j1 = add nuw nsw i64 %j1, 1
  %cmp7 = icmp slt i64 %inc.j1, %n64
  br i1 %cmp7, label %for.body8, label %for.end.inner1

for.end.inner1:                                   ; preds = %for.body8
  store double %add15, ptr %x1addr, align 8
  br label %for.inc18

for.inc18:                                        ; preds = %for.end.inner1
  %inc19 = add nuw nsw i64 %i1, 1
  %cmp = icmp slt i64 %inc19, %n64
  br i1 %cmp, label %for.body.outer1, label %for.end20

for.end20:                                        ; preds = %for.inc18, %entry
  br i1 %cmp.n, label %preheader2, label %for.end44

preheader2:
  %n64.2 = sext i32 %n to i64
  br label %for.body.outer2

for.body.outer2:                                  ; preds = %for.inc42, %preheader2
  %i2 = phi i64 [ 0, %preheader2 ], [ %inc43, %for.inc42 ]
  %x2addr = getelementptr inbounds double, ptr %x2, i64 %i2
  %x2val0 = load double, ptr %x2addr, align 8
  br label %for.body26

for.body26:                                       ; preds = %for.body26, %for.body.outer2
  %j2 = phi i64 [ 0, %for.body.outer2 ], [ %inc.j2, %for.body26 ]
  %acc2 = phi double [ %x2val0, %for.body.outer2 ], [ %add36, %for.body26 ]
  %Arowoff2 = mul nsw i64 %j2, %n64.2
  %Aptr2 = getelementptr inbounds double, ptr %A, i64 %Arowoff2
  %Aptr2i = getelementptr inbounds double, ptr %Aptr2, i64 %i2
  %Aval2 = load double, ptr %Aptr2i, align 8
  %y2ptr = getelementptr inbounds double, ptr %y_2, i64 %j2
  %y2val = load double, ptr %y2ptr, align 8
  %mul2 = fmul double %Aval2, %y2val
  %add36 = fadd double %acc2, %mul2
  %inc.j2 = add nuw nsw i64 %j2, 1
  %cmp25 = icmp slt i64 %inc.j2, %n64.2
  br i1 %cmp25, label %for.body26, label %for.end.inner2

for.end.inner2:                                   ; preds = %for.body26
  store double %add36, ptr %x2addr, align 8
  br label %for.inc42

for.inc42:                                        ; preds = %for.end.inner2
  %inc43 = add nuw nsw i64 %i2, 1
  %cmp22 = icmp slt i64 %inc43, %n64.2
  br i1 %cmp22, label %for.body.outer2, label %for.end44

for.end44:                                        ; preds = %for.inc42, %for.end20
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
