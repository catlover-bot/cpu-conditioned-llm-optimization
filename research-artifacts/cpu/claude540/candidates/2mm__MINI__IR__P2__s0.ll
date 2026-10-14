; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_2mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, double noundef %alpha, double noundef %beta, ptr noundef %tmp, ptr noundef %A, ptr noundef %B, ptr noundef %C, ptr noundef %D) #0 {
entry:
  %cmp.ni.pos = icmp sgt i32 %ni, 0
  br i1 %cmp.ni.pos, label %check.nj1, label %for.end37

check.nj1:
  %cmp.nj.pos = icmp sgt i32 %nj, 0
  br label %preheader1

preheader1:
  %nj64 = zext i32 %nj to i64
  %nk64 = zext i32 %nk to i64
  %ni64 = zext i32 %ni to i64
  %nl64 = zext i32 %nl to i64
  %cmp.nk.pos = icmp sgt i32 %nk, 0
  br label %outer1.header

outer1.header:                                    ; preds = %preheader1, %outer1.inc
  %i1 = phi i32 [ 0, %preheader1 ], [ %i1.next, %outer1.inc ]
  %i1.64 = zext i32 %i1 to i64
  br i1 %cmp.nj.pos, label %inner1.j.preheader, label %outer1.inc

inner1.j.preheader:
  %tmp.row1 = mul nsw i64 %i1.64, %nj64
  %A.row = mul nsw i64 %i1.64, %nk64
  br label %inner1.j.header

inner1.j.header:                                  ; preds = %inner1.j.preheader, %inner1.j.inc
  %j1 = phi i32 [ 0, %inner1.j.preheader ], [ %j1.next, %inner1.j.inc ]
  %j1.64 = zext i32 %j1 to i64
  %tmp.idx1 = add nsw i64 %tmp.row1, %j1.64
  %tmp.ptr1 = getelementptr inbounds double, ptr %tmp, i64 %tmp.idx1
  store double 0.000000e+00, ptr %tmp.ptr1, align 8
  br i1 %cmp.nk.pos, label %inner1.k.preheader, label %inner1.j.inc

inner1.k.preheader:
  br label %inner1.k.body

inner1.k.body:                                    ; preds = %inner1.k.preheader, %inner1.k.body
  %k1 = phi i32 [ 0, %inner1.k.preheader ], [ %k1.next, %inner1.k.body ]
  %k1.64 = zext i32 %k1 to i64
  %A.idx = add nsw i64 %A.row, %k1.64
  %A.ptr = getelementptr inbounds double, ptr %A, i64 %A.idx
  %A.val = load double, ptr %A.ptr, align 8
  %mulA = fmul double %alpha, %A.val
  %B.row = mul nsw i64 %k1.64, %nj64
  %B.idx = add nsw i64 %B.row, %j1.64
  %B.ptr = getelementptr inbounds double, ptr %B, i64 %B.idx
  %B.val = load double, ptr %B.ptr, align 8
  %mulAB = fmul double %mulA, %B.val
  %tmp.cur = load double, ptr %tmp.ptr1, align 8
  %sum = fadd double %tmp.cur, %mulAB
  store double %sum, ptr %tmp.ptr1, align 8
  %k1.next = add nsw i32 %k1, 1
  %k1.cond = icmp slt i32 %k1.next, %nk
  br i1 %k1.cond, label %inner1.k.body, label %inner1.j.inc, !llvm.loop !6

inner1.j.inc:                                     ; preds = %inner1.k.body, %inner1.j.header
  %j1.next = add nsw i32 %j1, 1
  %j1.cond = icmp slt i32 %j1.next, %nj
  br i1 %j1.cond, label %inner1.j.header, label %outer1.inc, !llvm.loop !8

outer1.inc:                                       ; preds = %inner1.j.inc, %outer1.header
  %i1.next = add nsw i32 %i1, 1
  %i1.cond = icmp slt i32 %i1.next, %ni
  br i1 %i1.cond, label %outer1.header, label %for.end37, !llvm.loop !9

for.end37:                                        ; preds = %outer1.inc, %entry
  %cmp2.ni.pos = icmp sgt i32 %ni, 0
  br i1 %cmp2.ni.pos, label %check.nl2, label %for.end74

check.nl2:
  %cmp2.nl.pos = icmp sgt i32 %nl, 0
  br label %preheader2

preheader2:
  %nl64.2 = zext i32 %nl to i64
  %nj64.2 = zext i32 %nj to i64
  %cmp2.nj.pos = icmp sgt i32 %nj, 0
  br label %outer2.header

outer2.header:                                    ; preds = %preheader2, %outer2.inc
  %i2 = phi i32 [ 0, %preheader2 ], [ %i2.next, %outer2.inc ]
  %i2.64 = zext i32 %i2 to i64
  br i1 %cmp2.nl.pos, label %inner2.j.preheader, label %outer2.inc

inner2.j.preheader:
  %D.row = mul nsw i64 %i2.64, %nl64.2
  %tmp.row2 = mul nsw i64 %i2.64, %nj64.2
  br label %inner2.j.header

inner2.j.header:                                  ; preds = %inner2.j.preheader, %inner2.j.inc
  %j2 = phi i32 [ 0, %inner2.j.preheader ], [ %j2.next, %inner2.j.inc ]
  %j2.64 = zext i32 %j2 to i64
  %D.idx1 = add nsw i64 %D.row, %j2.64
  %D.ptr1 = getelementptr inbounds double, ptr %D, i64 %D.idx1
  %D.val1 = load double, ptr %D.ptr1, align 8
  %mulD = fmul double %D.val1, %beta
  store double %mulD, ptr %D.ptr1, align 8
  br i1 %cmp2.nj.pos, label %inner2.k.preheader, label %inner2.j.inc

inner2.k.preheader:
  br label %inner2.k.body

inner2.k.body:                                    ; preds = %inner2.k.preheader, %inner2.k.body
  %k2 = phi i32 [ 0, %inner2.k.preheader ], [ %k2.next, %inner2.k.body ]
  %k2.64 = zext i32 %k2 to i64
  %tmp.idx2 = add nsw i64 %tmp.row2, %k2.64
  %tmp.ptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmp.idx2
  %tmp.val2 = load double, ptr %tmp.ptr2, align 8
  %C.row = mul nsw i64 %k2.64, %nl64.2
  %C.idx = add nsw i64 %C.row, %j2.64
  %C.ptr = getelementptr inbounds double, ptr %C, i64 %C.idx
  %C.val = load double, ptr %C.ptr, align 8
  %mulTC = fmul double %tmp.val2, %C.val
  %D.cur = load double, ptr %D.ptr1, align 8
  %sumD = fadd double %D.cur, %mulTC
  store double %sumD, ptr %D.ptr1, align 8
  %k2.next = add nsw i32 %k2, 1
  %k2.cond = icmp slt i32 %k2.next, %nj
  br i1 %k2.cond, label %inner2.k.body, label %inner2.j.inc, !llvm.loop !10

inner2.j.inc:                                     ; preds = %inner2.k.body, %inner2.j.header
  %j2.next = add nsw i32 %j2, 1
  %j2.cond = icmp slt i32 %j2.next, %nl
  br i1 %j2.cond, label %inner2.j.header, label %outer2.inc, !llvm.loop !11

outer2.inc:                                       ; preds = %inner2.j.inc, %outer2.header
  %i2.next = add nsw i32 %i2, 1
  %i2.cond = icmp slt i32 %i2.next, %ni
  br i1 %i2.cond, label %outer2.header, label %for.end74, !llvm.loop !12

for.end74:                                        ; preds = %outer2.inc, %for.end37
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
