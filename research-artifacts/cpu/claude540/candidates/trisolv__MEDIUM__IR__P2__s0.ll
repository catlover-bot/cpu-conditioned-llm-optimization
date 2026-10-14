; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trisolv(i32 noundef %n, ptr noundef %L, ptr noundef %x, ptr noundef %b) #0 {
entry:
  %cmp28 = icmp sgt i32 %n, 0
  br i1 %cmp28, label %for.body.preheader, label %for.end27

for.body.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:
  %i.032 = phi i32 [ 0, %for.body.preheader ], [ %inc26, %for.inc25 ]
  %idxprom = sext i32 %i.032 to i64
  %arrayidx = getelementptr inbounds double, ptr %b, i64 %idxprom
  %bi = load double, ptr %arrayidx, align 8
  %arrayidx5 = getelementptr inbounds double, ptr %x, i64 %idxprom
  store double %bi, ptr %arrayidx5, align 8
  %cmp729 = icmp sgt i32 %i.032, 0
  br i1 %cmp729, label %for.body8.preheader, label %for.end

for.body8.preheader:
  %rowoff = mul nsw i64 %idxprom, %n64
  %rowptr = getelementptr inbounds double, ptr %L, i64 %rowoff
  br label %for.body8

for.body8:
  %j.030 = phi i32 [ 0, %for.body8.preheader ], [ %inc, %for.body8 ]
  %idxprom11 = sext i32 %j.030 to i64
  %arrayidx12 = getelementptr inbounds double, ptr %rowptr, i64 %idxprom11
  %Lij = load double, ptr %arrayidx12, align 8
  %arrayidx14 = getelementptr inbounds double, ptr %x, i64 %idxprom11
  %xj = load double, ptr %arrayidx14, align 8
  %mul = fmul double %Lij, %xj
  %xi.cur = load double, ptr %arrayidx5, align 8
  %sub = fsub double %xi.cur, %mul
  store double %sub, ptr %arrayidx5, align 8
  %inc = add nsw i32 %j.030, 1
  %cmp7 = icmp slt i32 %inc, %i.032
  br i1 %cmp7, label %for.body8, label %for.end

for.end:
  %xi.final = load double, ptr %arrayidx5, align 8
  %diagoff = mul nsw i64 %idxprom, %n64
  %diagbase = getelementptr inbounds double, ptr %L, i64 %diagoff
  %diagptr = getelementptr inbounds double, ptr %diagbase, i64 %idxprom
  %diag = load double, ptr %diagptr, align 8
  %div = fdiv double %xi.final, %diag
  store double %div, ptr %arrayidx5, align 8
  br label %for.inc25

for.inc25:
  %inc26 = add nsw i32 %i.032, 1
  %cmp = icmp slt i32 %inc26, %n
  br i1 %cmp, label %for.body, label %for.end27.loopexit

for.end27.loopexit:
  br label %for.end27

for.end27:
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
