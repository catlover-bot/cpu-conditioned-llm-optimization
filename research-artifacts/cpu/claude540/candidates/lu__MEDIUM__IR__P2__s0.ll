; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_lu(i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end57

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:
  %i = phi i32 [ 0, %outer.preheader ], [ %inc56, %for.inc55 ]
  %i64 = sext i32 %i to i64
  %rowi.off = mul nsw i64 %i64, %n64
  %rowi = getelementptr inbounds double, ptr %A, i64 %rowi.off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body, label %for.end28

for.body:
  br label %for.cond2

for.cond2:
  %j = phi i32 [ 0, %for.body ], [ %inc27, %for.inc26 ]
  %j64 = sext i32 %j to i64
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body4, label %for.end

for.body4:
  br label %for.cond5

for.cond5:
  %k = phi i32 [ 0, %for.body4 ], [ %inc, %for.cond5 ]
  %k64 = sext i32 %k to i64
  %arrayidx9 = getelementptr inbounds double, ptr %rowi, i64 %k64
  %aik = load double, ptr %arrayidx9, align 8
  %rowk.off = mul nsw i64 %k64, %n64
  %rowk = getelementptr inbounds double, ptr %A, i64 %rowk.off
  %arrayidx13 = getelementptr inbounds double, ptr %rowk, i64 %j64
  %akj = load double, ptr %arrayidx13, align 8
  %mul = fmul double %aik, %akj
  %arrayidx17 = getelementptr inbounds double, ptr %rowi, i64 %j64
  %aij = load double, ptr %arrayidx17, align 8
  %sub = fsub double %aij, %mul
  store double %sub, ptr %arrayidx17, align 8
  %inc = add nsw i32 %k, 1
  %cmp6 = icmp slt i32 %inc, %j
  br i1 %cmp6, label %for.cond5, label %for.end, !llvm.loop !6

for.end:
  %arrayidx21 = getelementptr inbounds double, ptr %rowi, i64 %j64
  %ajj_load = getelementptr inbounds double, ptr %A, i64 %j64
  %rowj.off = mul nsw i64 %j64, %n64
  %rowj = getelementptr inbounds double, ptr %A, i64 %rowj.off
  %arrayidx19 = getelementptr inbounds double, ptr %rowj, i64 %j64
  %ajj = load double, ptr %arrayidx19, align 8
  %aij2 = load double, ptr %arrayidx21, align 8
  %div = fdiv double %aij2, %ajj
  store double %div, ptr %arrayidx21, align 8
  br label %for.inc26

for.inc26:
  %inc27 = add nsw i32 %j, 1
  %cmp3 = icmp slt i32 %inc27, %i
  br i1 %cmp3, label %for.cond2, label %for.end28, !llvm.loop !8

for.end28:
  br label %for.cond29

for.cond29:
  %j2 = phi i32 [ %i, %for.end28 ], [ %inc53, %for.inc52 ]
  %j264 = sext i32 %j2 to i64
  %cmp.n2 = icmp slt i32 %j2, %n
  br i1 %cmp.n2, label %for.body31, label %for.end54

for.body31:
  %cmp.k2 = icmp sgt i32 %i, 0
  br i1 %cmp.k2, label %for.body34.preheader, label %for.end51

for.body34.preheader:
  br label %for.cond32

for.cond32:
  %k2 = phi i32 [ 0, %for.body34.preheader ], [ %inc50, %for.cond32 ]
  %k264 = sext i32 %k2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %rowi, i64 %k264
  %aik2 = load double, ptr %arrayidx38, align 8
  %rowk2.off = mul nsw i64 %k264, %n64
  %rowk2 = getelementptr inbounds double, ptr %A, i64 %rowk2.off
  %arrayidx42 = getelementptr inbounds double, ptr %rowk2, i64 %j264
  %akj2 = load double, ptr %arrayidx42, align 8
  %mul43 = fmul double %aik2, %akj2
  %arrayidx47 = getelementptr inbounds double, ptr %rowi, i64 %j264
  %aij3 = load double, ptr %arrayidx47, align 8
  %sub48 = fsub double %aij3, %mul43
  store double %sub48, ptr %arrayidx47, align 8
  %inc50 = add nsw i32 %k2, 1
  %cmp33 = icmp slt i32 %inc50, %i
  br i1 %cmp33, label %for.cond32, label %for.end51, !llvm.loop !9

for.end51:
  br label %for.inc52

for.inc52:
  %inc53 = add nsw i32 %j2, 1
  br label %for.cond29, !llvm.loop !10

for.end54:
  br label %for.inc55

for.inc55:
  %inc56 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc56, %n
  br i1 %cmp, label %for.cond, label %for.end57.loopexit, !llvm.loop !11

for.end57.loopexit:
  br label %for.end57

for.end57:
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
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
