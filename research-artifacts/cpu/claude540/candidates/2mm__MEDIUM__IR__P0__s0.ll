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

  %icmp.i.0 = icmp slt i32 0, %ni
  br i1 %icmp.i.0, label %outer1.preheader, label %for.end37

outer1.preheader:
  %jcond0 = icmp slt i32 0, %nj
  %kcond0 = icmp slt i32 0, %nk
  br label %outer1.head

outer1.head:                                      ; preds = %outer1.preheader, %outer1.latch
  %i.1 = phi i64 [ 0, %outer1.preheader ], [ %i.1.next, %outer1.latch ]
  br i1 %jcond0, label %inner1.preheader, label %outer1.latch

inner1.preheader:
  %tmp.row1 = mul nsw i64 %i.1, %nj64
  %tmp.rowptr1 = getelementptr inbounds double, ptr %tmp, i64 %tmp.row1
  %A.row = mul nsw i64 %i.1, %nk64
  %A.rowptr = getelementptr inbounds double, ptr %A, i64 %A.row
  br label %inner1.head

inner1.head:                                      ; preds = %inner1.preheader, %inner1.latch
  %j.1 = phi i64 [ 0, %inner1.preheader ], [ %j.1.next, %inner1.latch ]
  %tmp.elt1 = getelementptr inbounds double, ptr %tmp.rowptr1, i64 %j.1
  store double 0.000000e+00, ptr %tmp.elt1, align 8
  br i1 %kcond0, label %kloop.preheader, label %inner1.latch

kloop.preheader:
  br label %kloop

kloop:                                            ; preds = %kloop.preheader, %kloop
  %k.1 = phi i64 [ 0, %kloop.preheader ], [ %k.1.next, %kloop ]
  %acc = phi double [ 0.000000e+00, %kloop.preheader ], [ %add31, %kloop ]
  %A.elt = getelementptr inbounds double, ptr %A.rowptr, i64 %k.1
  %aval = load double, ptr %A.elt, align 8
  %mul = fmul double %alpha, %aval
  %B.row = mul nsw i64 %k.1, %nj64
  %B.rowptr = getelementptr inbounds double, ptr %B, i64 %B.row
  %B.elt = getelementptr inbounds double, ptr %B.rowptr, i64 %j.1
  %bval = load double, ptr %B.elt, align 8
  %mul26 = fmul double %mul, %bval
  %add31 = fadd double %acc, %mul26
  %k.1.next = add nsw i64 %k.1, 1
  %kcond = icmp slt i64 %k.1.next, %nk64
  br i1 %kcond, label %kloop, label %kloop.exit

kloop.exit:
  store double %add31, ptr %tmp.elt1, align 8
  br label %inner1.latch

inner1.latch:                                     ; preds = %inner1.head, %kloop.exit
  %j.1.next = add nsw i64 %j.1, 1
  %jcond = icmp slt i64 %j.1.next, %nj64
  br i1 %jcond, label %inner1.head, label %outer1.latch

outer1.latch:                                     ; preds = %outer1.head, %inner1.latch
  %i.1.next = add nsw i64 %i.1, 1
  %icond = icmp slt i64 %i.1.next, %ni64
  br i1 %icond, label %outer1.head, label %for.end37

for.end37:                                        ; preds = %outer1.latch, %entry
  %icmp.i2.0 = icmp slt i32 0, %ni
  br i1 %icmp.i2.0, label %outer2.preheader, label %for.end74

outer2.preheader:
  %lcond0 = icmp slt i32 0, %nl
  %jcond2_0 = icmp slt i32 0, %nj
  br label %outer2.head

outer2.head:                                      ; preds = %outer2.preheader, %outer2.latch
  %i.2 = phi i64 [ 0, %outer2.preheader ], [ %i.2.next, %outer2.latch ]
  br i1 %lcond0, label %inner2.preheader, label %outer2.latch

inner2.preheader:
  %D.row = mul nsw i64 %i.2, %nl64
  %D.rowptr = getelementptr inbounds double, ptr %D, i64 %D.row
  %tmp.row2 = mul nsw i64 %i.2, %nj64
  %tmp.rowptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmp.row2
  br label %inner2.head

inner2.head:                                      ; preds = %inner2.preheader, %inner2.latch
  %l.2 = phi i64 [ 0, %inner2.preheader ], [ %l.2.next, %inner2.latch ]
  %D.elt = getelementptr inbounds double, ptr %D.rowptr, i64 %l.2
  %dval = load double, ptr %D.elt, align 8
  %mul48 = fmul double %dval, %beta
  store double %mul48, ptr %D.elt, align 8
  br i1 %jcond2_0, label %kloop2.preheader, label %inner2.latch

kloop2.preheader:
  br label %kloop2

kloop2:                                           ; preds = %kloop2.preheader, %kloop2
  %k.2 = phi i64 [ 0, %kloop2.preheader ], [ %k.2.next, %kloop2 ]
  %acc2 = phi double [ %mul48, %kloop2.preheader ], [ %add65, %kloop2 ]
  %tmp.elt2 = getelementptr inbounds double, ptr %tmp.rowptr2, i64 %k.2
  %tval = load double, ptr %tmp.elt2, align 8
  %C.row = mul nsw i64 %k.2, %nl64
  %C.rowptr = getelementptr inbounds double, ptr %C, i64 %C.row
  %C.elt = getelementptr inbounds double, ptr %C.rowptr, i64 %l.2
  %cval = load double, ptr %C.elt, align 8
  %mul60 = fmul double %tval, %cval
  %add65 = fadd double %acc2, %mul60
  %k.2.next = add nsw i64 %k.2, 1
  %kcond2 = icmp slt i64 %k.2.next, %nj64
  br i1 %kcond2, label %kloop2, label %kloop2.exit

kloop2.exit:
  store double %add65, ptr %D.elt, align 8
  br label %inner2.latch

inner2.latch:                                     ; preds = %inner2.head, %kloop2.exit
  %l.2.next = add nsw i64 %l.2, 1
  %lcond = icmp slt i64 %l.2.next, %nl64
  br i1 %lcond, label %inner2.head, label %outer2.latch

outer2.latch:                                     ; preds = %outer2.head, %inner2.latch
  %i.2.next = add nsw i64 %i.2, 1
  %icond2 = icmp slt i64 %i.2.next, %ni64
  br i1 %icond2, label %outer2.head, label %for.end74

for.end74:                                        ; preds = %outer2.latch, %for.end37
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
