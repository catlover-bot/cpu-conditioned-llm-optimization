; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end20

outer.preheader:
  %n64 = sext i32 %n to i64

  br label %for.body

for.body:                                         ; preds = %for.inc18, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc19, %for.inc18 ]
  %xi.ptr = getelementptr inbounds double, ptr %x1, i64 %i
  %rowoff = mul nsw i64 %i, %n64
  %row.ptr = getelementptr inbounds double, ptr %A, i64 %rowoff
  %xi.init = load double, ptr %xi.ptr, align 8
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body
  %j = phi i64 [ 0, %for.body ], [ %inc, %for.body8 ]
  %acc = phi double [ %xi.init, %for.body ], [ %add15, %for.body8 ]
  %arrayidx12 = getelementptr inbounds double, ptr %row.ptr, i64 %j
  %a.val = load double, ptr %arrayidx12, align 8
  %arrayidx14 = getelementptr inbounds double, ptr %y_1, i64 %j
  %y.val = load double, ptr %arrayidx14, align 8
  %mul = fmul double %a.val, %y.val
  %add15 = fadd double %acc, %mul
  %inc = add nsw i64 %j, 1
  %cmp7 = icmp slt i64 %inc, %n64
  br i1 %cmp7, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8
  store double %add15, ptr %xi.ptr, align 8
  br label %for.inc18

for.inc18:                                        ; preds = %for.end, %for.body
  %inc19 = add nsw i64 %i, 1
  %cmp.outer = icmp slt i64 %inc19, %n64
  br i1 %cmp.outer, label %for.body, label %for.end20.loopexit

for.end20.loopexit:
  br label %for.end20

for.end20:                                         ; preds = %for.end20.loopexit, %entry
  %cmp2.n = icmp sgt i32 %n, 0
  br i1 %cmp2.n, label %outer2.preheader, label %for.end44

outer2.preheader:
  %n64b = sext i32 %n to i64
  br label %for.body23

for.body23:                                        ; preds = %for.inc42, %outer2.preheader
  %i2 = phi i64 [ 0, %outer2.preheader ], [ %inc43, %for.inc42 ]
  %x2i.ptr = getelementptr inbounds double, ptr %x2, i64 %i2
  %x2i.init = load double, ptr %x2i.ptr, align 8
  br label %for.body26

for.body26:                                        ; preds = %for.body26, %for.body23
  %j2 = phi i64 [ 0, %for.body23 ], [ %inc40, %for.body26 ]
  %acc2 = phi double [ %x2i.init, %for.body23 ], [ %add36, %for.body26 ]
  %rowoff2 = mul nsw i64 %j2, %n64b
  %row2.ptr = getelementptr inbounds double, ptr %A, i64 %rowoff2
  %arrayidx32 = getelementptr inbounds double, ptr %row2.ptr, i64 %i2
  %a2.val = load double, ptr %arrayidx32, align 8
  %arrayidx34 = getelementptr inbounds double, ptr %y_2, i64 %j2
  %y2.val = load double, ptr %arrayidx34, align 8
  %mul35 = fmul double %a2.val, %y2.val
  %add36 = fadd double %acc2, %mul35
  %inc40 = add nsw i64 %j2, 1
  %cmp25 = icmp slt i64 %inc40, %n64b
  br i1 %cmp25, label %for.body26, label %for.end41

for.end41:                                         ; preds = %for.body26
  store double %add36, ptr %x2i.ptr, align 8
  br label %for.inc42

for.inc42:                                         ; preds = %for.end41, %for.body23
  %inc43 = add nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %inc43, %n64b
  br i1 %cmp.outer2, label %for.body23, label %for.end44.loopexit

for.end44.loopexit:
  br label %for.end44

for.end44:                                          ; preds = %for.end44.loopexit, %for.end20
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
