; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_floyd_warshall(i32 noundef %n, ptr noundef %path) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %outer.preheader, label %for.end42

outer.preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc40, %outer.preheader
  %k = phi i32 [ 0, %outer.preheader ], [ %inc41, %for.inc40 ]
  %k64 = zext i32 %k to i64
  %krow = mul nsw i64 %k64, %n64
  %krowptr = getelementptr inbounds i32, ptr %path, i64 %krow
  br label %for.body4.preheader

for.body4.preheader:
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc37, %for.body4.preheader
  %i = phi i32 [ 0, %for.body4.preheader ], [ %inc38, %for.inc37 ]
  %i64 = zext i32 %i to i64
  %irow = mul nsw i64 %i64, %n64
  %irowptr = getelementptr inbounds i32, ptr %path, i64 %irow
  %ik.ptr = getelementptr inbounds i32, ptr %irowptr, i64 %k64
  %ik.val = load i32, ptr %ik.ptr, align 4
  br i1 %cmp_n, label %for.body7.preheader, label %for.end39

for.body7.preheader:
  br label %for.body7

for.body7:                                         ; preds = %for.body7.preheader, %for.body7
  %j = phi i32 [ 0, %for.body7.preheader ], [ %inc, %for.body7 ]
  %j64 = zext i32 %j to i64

  %ij.ptr = getelementptr inbounds i32, ptr %irowptr, i64 %j64
  %ij.val = load i32, ptr %ij.ptr, align 4

  %kj.ptr = getelementptr inbounds i32, ptr %krowptr, i64 %j64
  %kj.val = load i32, ptr %kj.ptr, align 4

  %sum = add nsw i32 %ik.val, %kj.val
  %cmp19 = icmp slt i32 %ij.val, %sum
  %sel = select i1 %cmp19, i32 %ij.val, i32 %sum

  store i32 %sel, ptr %ij.ptr, align 4

  %inc = add nsw i32 %j, 1
  %cmp6 = icmp slt i32 %inc, %n
  br i1 %cmp6, label %for.body7, label %for.end39

for.end39.loopexit:
  br label %for.end39

for.end39:                                         ; preds = %for.body7, %for.cond2
  %inc38 = add nsw i32 %i, 1
  %cmp3 = icmp slt i32 %inc38, %n
  br i1 %cmp3, label %for.cond2, label %for.end42.loopexit

for.end42.loopexit:
  %inc41 = add nsw i32 %k, 1
  %cmp = icmp slt i32 %inc41, %n
  br i1 %cmp, label %for.cond, label %for.end42

for.inc37:
  br label %for.cond2

for.inc40:
  br label %for.cond

for.end42:                                         ; preds = %for.end42.loopexit, %entry
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
