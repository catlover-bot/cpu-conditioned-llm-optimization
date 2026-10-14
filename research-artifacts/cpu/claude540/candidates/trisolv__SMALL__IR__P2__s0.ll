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

for.body:                                         ; preds = %for.inc25, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc26, %for.inc25 ]
  %i64 = sext i32 %i to i64
  %arrayidx.b = getelementptr inbounds double, ptr %b, i64 %i64
  %bval = load double, ptr %arrayidx.b, align 8
  %arrayidx.x = getelementptr inbounds double, ptr %x, i64 %i64
  store double %bval, ptr %arrayidx.x, align 8

  %row.off = mul nsw i64 %i64, %n64
  %row.ptr = getelementptr inbounds double, ptr %L, i64 %row.off

  %cmp.j = icmp sgt i32 %i, 0
  br i1 %cmp.j, label %for.body8.preheader, label %for.end

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body8.preheader
  %j = phi i32 [ 0, %for.body8.preheader ], [ %inc, %for.body8 ]
  %j64 = sext i32 %j to i64
  %arrayidx12 = getelementptr inbounds double, ptr %row.ptr, i64 %j64
  %lval = load double, ptr %arrayidx12, align 8
  %arrayidx14 = getelementptr inbounds double, ptr %x, i64 %j64
  %xjval = load double, ptr %arrayidx14, align 8
  %mul = fmul double %lval, %xjval
  %xival = load double, ptr %arrayidx.x, align 8
  %sub = fsub double %xival, %mul
  store double %sub, ptr %arrayidx.x, align 8
  %inc = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc, %i
  br i1 %cmp7, label %for.body8, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %xi.final = load double, ptr %arrayidx.x, align 8
  %arrayidx22 = getelementptr inbounds double, ptr %row.ptr, i64 %i64
  %diag = load double, ptr %arrayidx22, align 8
  %div = fdiv double %xi.final, %diag
  store double %div, ptr %arrayidx.x, align 8
  br label %for.inc25

for.inc25:                                        ; preds = %for.end
  %inc26 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc26, %n
  br i1 %cmp, label %for.body, label %for.end27.loopexit, !llvm.loop !8

for.end27.loopexit:
  br label %for.end27

for.end27:                                        ; preds = %for.end27.loopexit, %entry
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
