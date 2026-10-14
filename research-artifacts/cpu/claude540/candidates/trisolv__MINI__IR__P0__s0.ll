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

for.body:                                         ; preds = %for.inc25, %outer.preheader
  %i = phi i64 [ 0, %outer.preheader ], [ %inc26, %for.inc25 ]
  %bi.ptr = getelementptr inbounds double, ptr %b, i64 %i
  %bi = load double, ptr %bi.ptr, align 8
  %xi.ptr = getelementptr inbounds double, ptr %x, i64 %i
  store double %bi, ptr %xi.ptr, align 8

  %row.off = mul nsw i64 %i, %n64
  %row.ptr = getelementptr inbounds double, ptr %L, i64 %row.off

  %cmp.inner = icmp sgt i64 %i, 0
  br i1 %cmp.inner, label %for.body8.preheader, label %for.end

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body8.preheader
  %j = phi i64 [ 0, %for.body8.preheader ], [ %inc, %for.body8 ]
  %lij.ptr = getelementptr inbounds double, ptr %row.ptr, i64 %j
  %lij = load double, ptr %lij.ptr, align 8
  %xj.ptr = getelementptr inbounds double, ptr %x, i64 %j
  %xj = load double, ptr %xj.ptr, align 8
  %mul = fmul double %lij, %xj
  %xi.cur = load double, ptr %xi.ptr, align 8
  %sub = fsub double %xi.cur, %mul
  store double %sub, ptr %xi.ptr, align 8
  %inc = add nuw nsw i64 %j, 1
  %cmp7 = icmp slt i64 %inc, %i
  br i1 %cmp7, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8, %for.body
  %xi.final = load double, ptr %xi.ptr, align 8
  %lii.ptr = getelementptr inbounds double, ptr %row.ptr, i64 %i
  %lii = load double, ptr %lii.ptr, align 8
  %div = fdiv double %xi.final, %lii
  store double %div, ptr %xi.ptr, align 8
  br label %for.inc25

for.inc25:                                        ; preds = %for.end
  %inc26 = add nuw nsw i64 %i, 1
  %cmp = icmp slt i64 %inc26, %n64
  br i1 %cmp, label %for.body, label %for.end27.loopexit

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
