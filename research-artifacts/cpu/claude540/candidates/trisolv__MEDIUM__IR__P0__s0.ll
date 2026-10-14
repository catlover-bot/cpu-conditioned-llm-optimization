; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trisolv(i32 noundef %n, ptr noundef %L, ptr noundef %x, ptr noundef %b) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end27

preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %preheader, %for.end
  %i.02 = phi i64 [ 0, %preheader ], [ %inc26, %for.end ]
  %bptr = getelementptr inbounds double, ptr %b, i64 %i.02
  %bval = load double, ptr %bptr, align 8
  %xptr.i = getelementptr inbounds double, ptr %x, i64 %i.02
  store double %bval, ptr %xptr.i, align 8

  %rowoff = mul nsw i64 %i.02, %n64
  %rowptr = getelementptr inbounds double, ptr %L, i64 %rowoff

  %cmp7 = icmp sgt i64 %i.02, 0
  br i1 %cmp7, label %for.body8, label %for.end

for.body8:                                         ; preds = %preheader.j, %for.body
  %j.01 = phi i64 [ 0, %for.body ], [ %inc, %for.body8 ]
  %Lptr = getelementptr inbounds double, ptr %rowptr, i64 %j.01
  %Lval = load double, ptr %Lptr, align 8
  %xjptr = getelementptr inbounds double, ptr %x, i64 %j.01
  %xjval = load double, ptr %xjptr, align 8
  %mul = fmul double %Lval, %xjval
  %curx = load double, ptr %xptr.i, align 8
  %sub = fsub double %curx, %mul
  store double %sub, ptr %xptr.i, align 8
  %inc = add nuw nsw i64 %j.01, 1
  %cmp7.2 = icmp slt i64 %inc, %i.02
  br i1 %cmp7.2, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8, %for.body
  %xval = load double, ptr %xptr.i, align 8
  %diagptr = getelementptr inbounds double, ptr %rowptr, i64 %i.02
  %diagval = load double, ptr %diagptr, align 8
  %div = fdiv double %xval, %diagval
  store double %div, ptr %xptr.i, align 8
  %inc26 = add nuw nsw i64 %i.02, 1
  %cmp.exit = icmp slt i64 %inc26, %n64
  br i1 %cmp.exit, label %for.body, label %for.end27.loopexit

for.end27.loopexit:
  br label %for.end27

for.end27:                                         ; preds = %for.end27.loopexit, %entry
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
