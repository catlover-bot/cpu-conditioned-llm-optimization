; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_2mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, double noundef %alpha, double noundef %beta, ptr noundef %tmp, ptr noundef %A, ptr noundef %B, ptr noundef %C, ptr noundef %D) #0 {
entry:
  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64

  %ni_pos = icmp sgt i32 %ni, 0
  %nj_pos = icmp sgt i32 %nj, 0
  %nk_pos = icmp sgt i32 %nk, 0
  %nl_pos = icmp sgt i32 %nl, 0

  br label %loop1.i.cond

loop1.i.cond:
  %i1 = phi i64 [ 0, %entry ], [ %i1.next, %loop1.i.inc ]
  %cmp.i1 = icmp slt i64 %i1, %ni64
  br i1 %cmp.i1, label %loop1.i.body, label %loop1.end

loop1.i.body:
  %tmp.row1 = mul nsw i64 %i1, %nj64
  %tmp.rowptr1 = getelementptr inbounds double, ptr %tmp, i64 %tmp.row1
  %A.row1 = mul nsw i64 %i1, %nk64
  %A.rowptr1 = getelementptr inbounds double, ptr %A, i64 %A.row1
  br i1 %nj_pos, label %loop1.j.cond, label %loop1.i.inc

loop1.j.cond:
  %j1 = phi i64 [ 0, %loop1.i.body ], [ %j1.next, %loop1.j.inc ]
  %cmp.j1 = icmp slt i64 %j1, %nj64
  br i1 %cmp.j1, label %loop1.j.body, label %loop1.i.inc

loop1.j.body:
  %tmp.elem1 = getelementptr inbounds double, ptr %tmp.rowptr1, i64 %j1
  store double 0.000000e+00, ptr %tmp.elem1, align 8
  br i1 %nk_pos, label %loop1.k.preheader, label %loop1.j.inc

loop1.k.preheader:
  br label %loop1.k.cond

loop1.k.cond:
  %k1 = phi i64 [ 0, %loop1.k.preheader ], [ %k1.next, %loop1.k.body ]
  %cmp.k1 = icmp slt i64 %k1, %nk64
  br i1 %cmp.k1, label %loop1.k.body, label %loop1.j.inc

loop1.k.body:
  %A.elem1 = getelementptr inbounds double, ptr %A.rowptr1, i64 %k1
  %A.val1 = load double, ptr %A.elem1, align 8
  %mulAB1 = fmul double %alpha, %A.val1
  %B.row1 = mul nsw i64 %k1, %nj64
  %B.rowptr1 = getelementptr inbounds double, ptr %B, i64 %B.row1
  %B.elem1 = getelementptr inbounds double, ptr %B.rowptr1, i64 %j1
  %B.val1 = load double, ptr %B.elem1, align 8
  %mul1 = fmul double %mulAB1, %B.val1
  %tmp.cur1 = load double, ptr %tmp.elem1, align 8
  %add1 = fadd double %tmp.cur1, %mul1
  store double %add1, ptr %tmp.elem1, align 8
  %k1.next = add nsw i64 %k1, 1
  br label %loop1.k.cond, !llvm.loop !6

loop1.j.inc:
  %j1.next = add nsw i64 %j1, 1
  br label %loop1.j.cond, !llvm.loop !8

loop1.i.inc:
  %i1.next = add nsw i64 %i1, 1
  br label %loop1.i.cond, !llvm.loop !9

loop1.end:
  br label %loop2.i.cond

loop2.i.cond:
  %i2 = phi i64 [ 0, %loop1.end ], [ %i2.next, %loop2.i.inc ]
  %cmp.i2 = icmp slt i64 %i2, %ni64
  br i1 %cmp.i2, label %loop2.i.body, label %loop2.end

loop2.i.body:
  %D.row2 = mul nsw i64 %i2, %nl64
  %D.rowptr2 = getelementptr inbounds double, ptr %D, i64 %D.row2
  %tmp.row2 = mul nsw i64 %i2, %nj64
  %tmp.rowptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmp.row2
  br i1 %nl_pos, label %loop2.j.cond, label %loop2.i.inc

loop2.j.cond:
  %j2 = phi i64 [ 0, %loop2.i.body ], [ %j2.next, %loop2.j.inc ]
  %cmp.j2 = icmp slt i64 %j2, %nl64
  br i1 %cmp.j2, label %loop2.j.body, label %loop2.i.inc

loop2.j.body:
  %D.elem2 = getelementptr inbounds double, ptr %D.rowptr2, i64 %j2
  %D.val2 = load double, ptr %D.elem2, align 8
  %mulD2 = fmul double %D.val2, %beta
  store double %mulD2, ptr %D.elem2, align 8
  br i1 %nj_pos, label %loop2.k.preheader, label %loop2.j.inc

loop2.k.preheader:
  br label %loop2.k.cond

loop2.k.cond:
  %k2 = phi i64 [ 0, %loop2.k.preheader ], [ %k2.next, %loop2.k.body ]
  %cmp.k2 = icmp slt i64 %k2, %nj64
  br i1 %cmp.k2, label %loop2.k.body, label %loop2.j.inc

loop2.k.body:
  %tmp.elem2 = getelementptr inbounds double, ptr %tmp.rowptr2, i64 %k2
  %tmp.val2 = load double, ptr %tmp.elem2, align 8
  %C.row2 = mul nsw i64 %k2, %nl64
  %C.rowptr2 = getelementptr inbounds double, ptr %C, i64 %C.row2
  %C.elem2 = getelementptr inbounds double, ptr %C.rowptr2, i64 %j2
  %C.val2 = load double, ptr %C.elem2, align 8
  %mul2 = fmul double %tmp.val2, %C.val2
  %D.cur2 = load double, ptr %D.elem2, align 8
  %add2 = fadd double %D.cur2, %mul2
  store double %add2, ptr %D.elem2, align 8
  %k2.next = add nsw i64 %k2, 1
  br label %loop2.k.cond, !llvm.loop !10

loop2.j.inc:
  %j2.next = add nsw i64 %j2, 1
  br label %loop2.j.cond, !llvm.loop !11

loop2.i.inc:
  %i2.next = add nsw i64 %i2, 1
  br label %loop2.i.cond, !llvm.loop !12

loop2.end:
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
