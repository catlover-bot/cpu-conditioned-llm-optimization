; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trisolv(i32 noundef %n, ptr noundef %L, ptr noundef %x, ptr noundef %b) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end27

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:                                         ; preds = %for.end, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc26, %for.end ]
  %arrayidx.b = getelementptr inbounds double, ptr %b, i64 %i
  %bval = load double, ptr %arrayidx.b, align 8
  %arrayidx.x = getelementptr inbounds double, ptr %x, i64 %i
  store double %bval, ptr %arrayidx.x, align 8

  %rowoff = mul nsw i64 %i, %n64
  %rowptr = getelementptr inbounds double, ptr %L, i64 %rowoff

  %cmp.j = icmp sgt i64 %i, 0
  br i1 %cmp.j, label %for.body8, label %for.end

for.body8:                                        ; preds = %for.body8, %for.body
  %j = phi i64 [ 0, %for.body ], [ %inc, %for.body8 ]
  %arrayidx.L = getelementptr inbounds double, ptr %rowptr, i64 %j
  %Lval = load double, ptr %arrayidx.L, align 8
  %arrayidx.xj = getelementptr inbounds double, ptr %x, i64 %j
  %xjval = load double, ptr %arrayidx.xj, align 8
  %mul = fmul double %Lval, %xjval
  %cur = load double, ptr %arrayidx.x, align 8
  %sub = fsub double %cur, %mul
  store double %sub, ptr %arrayidx.x, align 8
  %inc = add nuw nsw i64 %j, 1
  %cmp.j2 = icmp slt i64 %inc, %i
  br i1 %cmp.j2, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8, %for.body
  %xival = load double, ptr %arrayidx.x, align 8
  %arrayidx.Ldiag = getelementptr inbounds double, ptr %rowptr, i64 %i
  %Ldiag = load double, ptr %arrayidx.Ldiag, align 8
  %div = fdiv double %xival, %Ldiag
  store double %div, ptr %arrayidx.x, align 8
  %inc26 = add nuw nsw i64 %i, 1
  %cmp.outer = icmp slt i64 %inc26, %n64
  br i1 %cmp.outer, label %for.body, label %for.end27

for.end27:                                        ; preds = %for.end, %entry
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
