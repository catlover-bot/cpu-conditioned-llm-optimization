; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.ni = icmp sgt i32 %ni, 0
  br i1 %cmp.ni, label %outer.preheader, label %for.end40

outer.preheader:
  %cmp.nj.pre = icmp sgt i32 %nj, 0
  %cmp.nk.pre = icmp sgt i32 %nk, 0
  %ni64 = zext i32 %ni to i64
  %nj64 = zext i32 %nj to i64
  %nk64 = zext i32 %nk to i64
  br label %for.body

for.body:
  %i = phi i32 [ 0, %outer.preheader ], [ %inc39, %for.inc38 ]
  %i64 = zext i32 %i to i64
  %crow_off = mul nsw i64 %i64, %nj64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow_off
  %arow_off = mul nsw i64 %i64, %nk64
  %arow = getelementptr inbounds double, ptr %A, i64 %arow_off

  br i1 %cmp.nj.pre, label %for.body8.preheader, label %for.end

for.body8.preheader:
  br label %for.body8

for.body8:
  %j1 = phi i64 [ 0, %for.body8.preheader ], [ %inc.j1, %for.body8 ]
  %arrayidx10 = getelementptr inbounds double, ptr %crow, i64 %j1
  %cval = load double, ptr %arrayidx10, align 8
  %mul = fmul double %cval, %beta
  store double %mul, ptr %arrayidx10, align 8
  %inc.j1 = add nuw nsw i64 %j1, 1
  %cmp7 = icmp slt i64 %inc.j1, %nj64
  br i1 %cmp7, label %for.body8, label %for.end

for.end:
  br i1 %cmp.nk.pre, label %for.body13.preheader, label %for.end37

for.body13.preheader:
  br label %for.body13

for.body13:
  %k = phi i64 [ 0, %for.body13.preheader ], [ %inc36, %for.inc35 ]
  %arrayidx20 = getelementptr inbounds double, ptr %arow, i64 %k
  %aval = load double, ptr %arrayidx20, align 8
  %mul21 = fmul double %alpha, %aval
  %brow_off = mul nsw i64 %k, %nj64
  %brow = getelementptr inbounds double, ptr %B, i64 %brow_off

  br i1 %cmp.nj.pre, label %for.body16.preheader, label %for.end34

for.body16.preheader:
  br label %for.body16

for.body16:
  %j2 = phi i64 [ 0, %for.body16.preheader ], [ %inc.j2, %for.body16 ]
  %arrayidx25 = getelementptr inbounds double, ptr %brow, i64 %j2
  %bval = load double, ptr %arrayidx25, align 8
  %mul26 = fmul double %mul21, %bval
  %arrayidx30 = getelementptr inbounds double, ptr %crow, i64 %j2
  %cval2 = load double, ptr %arrayidx30, align 8
  %add31 = fadd double %cval2, %mul26
  store double %add31, ptr %arrayidx30, align 8
  %inc.j2 = add nuw nsw i64 %j2, 1
  %cmp15 = icmp slt i64 %inc.j2, %nj64
  br i1 %cmp15, label %for.body16, label %for.end34

for.end34:
  br label %for.inc35

for.inc35:
  %inc36 = add nuw nsw i64 %k, 1
  %cmp12 = icmp slt i64 %inc36, %nk64
  br i1 %cmp12, label %for.body13, label %for.end37

for.end37:
  br label %for.inc38

for.inc38:
  %inc39 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc39, %ni
  br i1 %cmp, label %for.body, label %for.end40.loopexit

for.end40.loopexit:
  br label %for.end40

for.end40:
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
