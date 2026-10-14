; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end95

preheader:
  %n64 = zext i32 %n to i64

  br label %outer1.cond

outer1.cond:
  %i1 = phi i64 [ 0, %preheader ], [ %i1.next, %outer1.inc ]
  %cmp1 = icmp slt i64 %i1, %n64
  br i1 %cmp1, label %outer1.body, label %for.end32

outer1.body:
  %Arow1 = mul nsw i64 %i1, %n64
  %Arowptr1 = getelementptr inbounds double, ptr %A, i64 %Arow1
  %u1val = getelementptr inbounds double, ptr %u1, i64 %i1
  %u1v = load double, ptr %u1val, align 8
  %u2val = getelementptr inbounds double, ptr %u2, i64 %i1
  %u2v = load double, ptr %u2val, align 8
  br label %inner1.cond

inner1.cond:
  %j1 = phi i64 [ 0, %outer1.body ], [ %j1.next, %inner1.body ]
  %cmp2 = icmp slt i64 %j1, %n64
  br i1 %cmp2, label %inner1.body, label %for.end

inner1.body:
  %Aelem1 = getelementptr inbounds double, ptr %Arowptr1, i64 %j1
  %Aval1 = load double, ptr %Aelem1, align 8
  %v1elem = getelementptr inbounds double, ptr %v1, i64 %j1
  %v1val = load double, ptr %v1elem, align 8
  %mul1 = fmul double %u1v, %v1val
  %add1 = fadd double %Aval1, %mul1
  %v2elem = getelementptr inbounds double, ptr %v2, i64 %j1
  %v2val = load double, ptr %v2elem, align 8
  %mul2 = fmul double %u2v, %v2val
  %add2 = fadd double %add1, %mul2
  store double %add2, ptr %Aelem1, align 8
  %j1.next = add nsw i64 %j1, 1
  br label %inner1.cond, !llvm.loop !6

for.end:
  br label %outer1.inc

outer1.inc:
  %i1.next = add nsw i64 %i1, 1
  br label %outer1.cond, !llvm.loop !8

for.end32:
  br label %outer2.cond

outer2.cond:
  %i2 = phi i64 [ 0, %for.end32 ], [ %i2.next, %outer2.inc ]
  %cmp3 = icmp slt i64 %i2, %n64
  br i1 %cmp3, label %outer2.body, label %for.end57

outer2.body:
  %xelem2 = getelementptr inbounds double, ptr %x, i64 %i2
  %xval2.init = load double, ptr %xelem2, align 8
  br label %inner2.cond

inner2.cond:
  %j2 = phi i64 [ 0, %outer2.body ], [ %j2.next, %inner2.body ]
  %xacc = phi double [ %xval2.init, %outer2.body ], [ %xacc.next, %inner2.body ]
  %cmp4 = icmp slt i64 %j2, %n64
  br i1 %cmp4, label %inner2.body, label %for.end54

inner2.body:
  %Arow2 = mul nsw i64 %j2, %n64
  %Arowptr2 = getelementptr inbounds double, ptr %A, i64 %Arow2
  %Aelem2 = getelementptr inbounds double, ptr %Arowptr2, i64 %i2
  %Aval2 = load double, ptr %Aelem2, align 8
  %mul3 = fmul double %beta, %Aval2
  %yelem2 = getelementptr inbounds double, ptr %y, i64 %j2
  %yval2 = load double, ptr %yelem2, align 8
  %mul4 = fmul double %mul3, %yval2
  %xacc.next = fadd double %xacc, %mul4
  %j2.next = add nsw i64 %j2, 1
  br label %inner2.cond, !llvm.loop !9

for.end54:
  store double %xacc, ptr %xelem2, align 8
  br label %outer2.inc

outer2.inc:
  %i2.next = add nsw i64 %i2, 1
  br label %outer2.cond, !llvm.loop !10

for.end57:
  br label %loop3.cond

loop3.cond:
  %i3 = phi i64 [ 0, %for.end57 ], [ %i3.next, %loop3.body ]
  %cmp5 = icmp slt i64 %i3, %n64
  br i1 %cmp5, label %loop3.body, label %for.end70

loop3.body:
  %xelem3 = getelementptr inbounds double, ptr %x, i64 %i3
  %xval3 = load double, ptr %xelem3, align 8
  %zelem3 = getelementptr inbounds double, ptr %z, i64 %i3
  %zval3 = load double, ptr %zelem3, align 8
  %add3 = fadd double %xval3, %zval3
  store double %add3, ptr %xelem3, align 8
  %i3.next = add nsw i64 %i3, 1
  br label %loop3.cond, !llvm.loop !11

for.end70:
  br label %outer4.cond

outer4.cond:
  %i4 = phi i64 [ 0, %for.end70 ], [ %i4.next, %outer4.inc ]
  %cmp6 = icmp slt i64 %i4, %n64
  br i1 %cmp6, label %outer4.body, label %for.end95

outer4.body:
  %Arow4 = mul nsw i64 %i4, %n64
  %Arowptr4 = getelementptr inbounds double, ptr %A, i64 %Arow4
  %welem4 = getelementptr inbounds double, ptr %w, i64 %i4
  %wval4.init = load double, ptr %welem4, align 8
  br label %inner4.cond

inner4.cond:
  %j4 = phi i64 [ 0, %outer4.body ], [ %j4.next, %inner4.body ]
  %wacc = phi double [ %wval4.init, %outer4.body ], [ %wacc.next, %inner4.body ]
  %cmp7 = icmp slt i64 %j4, %n64
  br i1 %cmp7, label %inner4.body, label %for.end92

inner4.body:
  %Aelem4 = getelementptr inbounds double, ptr %Arowptr4, i64 %j4
  %Aval4 = load double, ptr %Aelem4, align 8
  %mul5 = fmul double %alpha, %Aval4
  %xelem4 = getelementptr inbounds double, ptr %x, i64 %j4
  %xval4 = load double, ptr %xelem4, align 8
  %mul6 = fmul double %mul5, %xval4
  %wacc.next = fadd double %wacc, %mul6
  %j4.next = add nsw i64 %j4, 1
  br label %inner4.cond, !llvm.loop !12

for.end92:
  store double %wacc, ptr %welem4, align 8
  br label %outer4.inc

outer4.inc:
  %i4.next = add nsw i64 %i4, 1
  br label %outer4.cond, !llvm.loop !13

for.end95:
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
!13 = distinct !{!13, !7}
