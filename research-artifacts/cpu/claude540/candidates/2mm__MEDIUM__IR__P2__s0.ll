; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_2mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, double noundef %alpha, double noundef %beta, ptr noundef %tmp, ptr noundef %A, ptr noundef %B, ptr noundef %C, ptr noundef %D) #0 {
entry:
  %cmp.ni = icmp sgt i32 %ni, 0
  br i1 %cmp.ni, label %check.nj1, label %for.end37

check.nj1:
  %cmp.nj1 = icmp sgt i32 %nj, 0
  br label %outer1.preheader

outer1.preheader:
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %ni64 = sext i32 %ni to i64
  br label %for.i1

for.i1:                                            ; preds = %outer1.preheader, %for.inc35
  %i1 = phi i32 [ 0, %outer1.preheader ], [ %inc36, %for.inc35 ]
  br i1 %cmp.nj1, label %for.j1.preheader, label %for.inc35

for.j1.preheader:
  %i1.64 = sext i32 %i1 to i64
  %tmp.row.off = mul nsw i64 %i1.64, %nj64
  %tmp.row = getelementptr inbounds double, ptr %tmp, i64 %tmp.row.off
  %A.row.off = mul nsw i64 %i1.64, %nk64
  %A.row = getelementptr inbounds double, ptr %A, i64 %A.row.off
  br label %for.j1

for.j1:                                            ; preds = %for.j1.preheader, %for.inc32
  %j1 = phi i32 [ 0, %for.j1.preheader ], [ %inc33, %for.inc32 ]
  %j1.64 = sext i32 %j1 to i64
  %tmp.elt = getelementptr inbounds double, ptr %tmp.row, i64 %j1.64
  store double 0.000000e+00, ptr %tmp.elt, align 8
  %cmp.nk = icmp sgt i32 %nk, 0
  br i1 %cmp.nk, label %for.k1.preheader, label %for.inc32

for.k1.preheader:
  br label %for.k1

for.k1:                                            ; preds = %for.k1.preheader, %for.k1
  %k1 = phi i32 [ 0, %for.k1.preheader ], [ %inc.k1, %for.k1 ]
  %k1.64 = sext i32 %k1 to i64
  %A.elt = getelementptr inbounds double, ptr %A.row, i64 %k1.64
  %a.val = load double, ptr %A.elt, align 8
  %mul.alpha = fmul double %alpha, %a.val
  %B.row.off = mul nsw i64 %k1.64, %nj64
  %B.row = getelementptr inbounds double, ptr %B, i64 %B.row.off
  %B.elt = getelementptr inbounds double, ptr %B.row, i64 %j1.64
  %b.val = load double, ptr %B.elt, align 8
  %mul26 = fmul double %mul.alpha, %b.val
  %tmp.cur = load double, ptr %tmp.elt, align 8
  %add31 = fadd double %tmp.cur, %mul26
  store double %add31, ptr %tmp.elt, align 8
  %inc.k1 = add nsw i32 %k1, 1
  %cmp.k1 = icmp slt i32 %inc.k1, %nk
  br i1 %cmp.k1, label %for.k1, label %for.end.k1, !llvm.loop !6

for.end.k1:
  br label %for.inc32

for.inc32:                                         ; preds = %for.j1, %for.end.k1
  %inc33 = add nsw i32 %j1, 1
  %cmp.j1 = icmp slt i32 %inc33, %nj
  br i1 %cmp.j1, label %for.j1, label %for.end34, !llvm.loop !8

for.end34:
  br label %for.inc35

for.inc35:                                         ; preds = %for.i1, %for.end34
  %inc36 = add nsw i32 %i1, 1
  %cmp.i1 = icmp slt i32 %inc36, %ni
  br i1 %cmp.i1, label %for.i1, label %for.end37, !llvm.loop !9

for.end37:                                         ; preds = %entry, %for.inc35
  %cmp.ni2 = icmp sgt i32 %ni, 0
  br i1 %cmp.ni2, label %check.nl2, label %for.end74

check.nl2:
  %cmp.nl2 = icmp sgt i32 %nl, 0
  br label %outer2.preheader

outer2.preheader:
  %nl64 = sext i32 %nl to i64
  %nj264 = sext i32 %nj to i64
  br label %for.i2

for.i2:                                            ; preds = %outer2.preheader, %for.inc72
  %i2 = phi i32 [ 0, %outer2.preheader ], [ %inc73, %for.inc72 ]
  br i1 %cmp.nl2, label %for.j2.preheader, label %for.inc72

for.j2.preheader:
  %i2.64 = sext i32 %i2 to i64
  %D.row.off = mul nsw i64 %i2.64, %nl64
  %D.row = getelementptr inbounds double, ptr %D, i64 %D.row.off
  %tmp2.row.off = mul nsw i64 %i2.64, %nj264
  %tmp2.row = getelementptr inbounds double, ptr %tmp, i64 %tmp2.row.off
  br label %for.j2

for.j2:                                            ; preds = %for.j2.preheader, %for.inc69
  %j2 = phi i32 [ 0, %for.j2.preheader ], [ %inc70, %for.inc69 ]
  %j2.64 = sext i32 %j2 to i64
  %D.elt = getelementptr inbounds double, ptr %D.row, i64 %j2.64
  %d.val = load double, ptr %D.elt, align 8
  %mul48 = fmul double %d.val, %beta
  store double %mul48, ptr %D.elt, align 8
  %cmp.nj2 = icmp sgt i32 %nj, 0
  br i1 %cmp.nj2, label %for.k2.preheader, label %for.inc69

for.k2.preheader:
  br label %for.k2

for.k2:                                            ; preds = %for.k2.preheader, %for.k2
  %k2 = phi i32 [ 0, %for.k2.preheader ], [ %inc.k2, %for.k2 ]
  %k2.64 = sext i32 %k2 to i64
  %tmp2.elt = getelementptr inbounds double, ptr %tmp2.row, i64 %k2.64
  %tmp2.val = load double, ptr %tmp2.elt, align 8
  %C.row.off = mul nsw i64 %k2.64, %nl64
  %C.row = getelementptr inbounds double, ptr %C, i64 %C.row.off
  %C.elt = getelementptr inbounds double, ptr %C.row, i64 %j2.64
  %c.val = load double, ptr %C.elt, align 8
  %mul60 = fmul double %tmp2.val, %c.val
  %D.cur = load double, ptr %D.elt, align 8
  %add65 = fadd double %D.cur, %mul60
  store double %add65, ptr %D.elt, align 8
  %inc.k2 = add nsw i32 %k2, 1
  %cmp.k2 = icmp slt i32 %inc.k2, %nj
  br i1 %cmp.k2, label %for.k2, label %for.end.k2, !llvm.loop !10

for.end.k2:
  br label %for.inc69

for.inc69:                                         ; preds = %for.j2, %for.end.k2
  %inc70 = add nsw i32 %j2, 1
  %cmp.j2 = icmp slt i32 %inc70, %nl
  br i1 %cmp.j2, label %for.j2, label %for.end71, !llvm.loop !11

for.end71:
  br label %for.inc72

for.inc72:                                         ; preds = %for.i2, %for.end71
  %inc73 = add nsw i32 %i2, 1
  %cmp.i2 = icmp slt i32 %inc73, %ni
  br i1 %cmp.i2, label %for.i2, label %for.end74, !llvm.loop !12

for.end74:                                         ; preds = %entry, %for.inc72
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
!12 = distinct !{!12, !7}
