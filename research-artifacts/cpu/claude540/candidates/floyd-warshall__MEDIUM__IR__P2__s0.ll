; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_floyd_warshall(i32 noundef %n, ptr noundef %path) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end42

preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc40, %preheader
  %k = phi i32 [ 0, %preheader ], [ %inc41, %for.inc40 ]
  %k64 = zext i32 %k to i64
  %krow = mul nsw i64 %k64, %n64
  %krowptr = getelementptr inbounds i32, ptr %path, i64 %krow
  br label %for.body

for.body:                                         ; preds = %for.cond
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc37, %for.body
  %i = phi i32 [ 0, %for.body ], [ %inc38, %for.inc37 ]
  %cmp3 = icmp slt i32 %i, %n
  br i1 %cmp3, label %for.body4, label %for.end39

for.body4:                                        ; preds = %for.cond2
  %i64 = sext i32 %i to i64
  %irow = mul nsw i64 %i64, %n64
  %irowptr = getelementptr inbounds i32, ptr %path, i64 %irow
  %ikptr = getelementptr inbounds i32, ptr %irowptr, i64 %k64
  %ik = load i32, ptr %ikptr, align 4
  br label %for.cond5

for.cond5:                                        ; preds = %for.inc, %for.body4
  %j = phi i32 [ 0, %for.body4 ], [ %inc, %for.inc ]
  %cmp6 = icmp slt i32 %j, %n
  br i1 %cmp6, label %for.body7, label %for.end

for.body7:                                        ; preds = %for.cond5
  %j64 = sext i32 %j to i64
  %ijptr = getelementptr inbounds i32, ptr %irowptr, i64 %j64
  %ij = load i32, ptr %ijptr, align 4
  %kjptr = getelementptr inbounds i32, ptr %krowptr, i64 %j64
  %kj = load i32, ptr %kjptr, align 4
  %add18 = add nsw i32 %ik, %kj
  %cmp19 = icmp slt i32 %ij, %add18
  %cond = select i1 %cmp19, i32 %ij, i32 %add18
  store i32 %cond, ptr %ijptr, align 4
  br label %for.inc

for.inc:                                          ; preds = %for.body7
  %inc = add nsw i32 %j, 1
  br label %for.cond5, !llvm.loop !6

for.end:                                          ; preds = %for.cond5
  br label %for.inc37

for.inc37:                                        ; preds = %for.end
  %inc38 = add nsw i32 %i, 1
  br label %for.cond2, !llvm.loop !8

for.end39:                                        ; preds = %for.cond2
  br label %for.inc40

for.inc40:                                        ; preds = %for.end39
  %inc41 = add nsw i32 %k, 1
  %cmp.k = icmp slt i32 %inc41, %n
  br i1 %cmp.k, label %for.cond, label %for.end42.loopexit, !llvm.loop !9

for.end42.loopexit:                               ; preds = %for.inc40
  br label %for.end42

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
