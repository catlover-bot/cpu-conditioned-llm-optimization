; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %second.check

outer.preheader:
  %n64 = zext i32 %n to i64
  br label %for.i.body

for.i.body:
  %i = phi i64 [ 0, %outer.preheader ], [ %inc.i, %for.i.inc ]
  %x1.elem = getelementptr inbounds double, ptr %x1, i64 %i
  %x1.val0 = load double, ptr %x1.elem, align 8
  %row.off = mul nsw i64 %i, %n64
  %row.ptr = getelementptr inbounds double, ptr %A, i64 %row.off
  br label %for.j.body

for.j.body:
  %j = phi i64 [ 0, %for.i.body ], [ %inc.j, %for.j.body ]
  %acc = phi double [ %x1.val0, %for.i.body ], [ %add15, %for.j.body ]
  %a.elem = getelementptr inbounds double, ptr %row.ptr, i64 %j
  %a.val = load double, ptr %a.elem, align 8
  %y1.elem = getelementptr inbounds double, ptr %y_1, i64 %j
  %y1.val = load double, ptr %y1.elem, align 8
  %mul = fmul double %a.val, %y1.val
  %add15 = fadd double %acc, %mul
  %inc.j = add nuw nsw i64 %j, 1
  %cmp.j = icmp slt i64 %inc.j, %n64
  br i1 %cmp.j, label %for.j.body, label %for.j.end

for.j.end:
  store double %add15, ptr %x1.elem, align 8
  br label %for.i.inc

for.i.inc:
  %inc.i = add nuw nsw i64 %i, 1
  %cmp.i = icmp slt i64 %inc.i, %n64
  br i1 %cmp.i, label %for.i.body, label %second.check

second.check:
  %cmp.n2 = icmp sgt i32 %n, 0
  br i1 %cmp.n2, label %outer2.preheader, label %for.end44

outer2.preheader:
  %n64b = zext i32 %n to i64
  br label %for.i2.body

for.i2.body:
  %i2 = phi i64 [ 0, %outer2.preheader ], [ %inc.i2, %for.i2.inc ]
  %x2.elem = getelementptr inbounds double, ptr %x2, i64 %i2
  %x2.val0 = load double, ptr %x2.elem, align 8
  br label %for.j2.body

for.j2.body:
  %j2 = phi i64 [ 0, %for.i2.body ], [ %inc.j2, %for.j2.body ]
  %acc2 = phi double [ %x2.val0, %for.i2.body ], [ %add36, %for.j2.body ]
  %a.row.off = mul nsw i64 %j2, %n64b
  %a.row.ptr = getelementptr inbounds double, ptr %A, i64 %a.row.off
  %a2.elem = getelementptr inbounds double, ptr %a.row.ptr, i64 %i2
  %a2.val = load double, ptr %a2.elem, align 8
  %y2.elem = getelementptr inbounds double, ptr %y_2, i64 %j2
  %y2.val = load double, ptr %y2.elem, align 8
  %mul35 = fmul double %a2.val, %y2.val
  %add36 = fadd double %acc2, %mul35
  %inc.j2 = add nuw nsw i64 %j2, 1
  %cmp.j2 = icmp slt i64 %inc.j2, %n64b
  br i1 %cmp.j2, label %for.j2.body, label %for.j2.end

for.j2.end:
  store double %add36, ptr %x2.elem, align 8
  br label %for.i2.inc

for.i2.inc:
  %inc.i2 = add nuw nsw i64 %i2, 1
  %cmp.i2 = icmp slt i64 %inc.i2, %n64b
  br i1 %cmp.i2, label %for.i2.body, label %for.end44

for.end44:
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
