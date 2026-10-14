; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_3mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, i32 noundef %nm, ptr noundef %E, ptr noundef %A, ptr noundef %B, ptr noundef %F, ptr noundef %C, ptr noundef %D, ptr noundef %G) #0 {
entry:
  %add = add nsw i32 %ni, 0
  %0 = zext i32 %add to i64
  %add1 = add nsw i32 %nj, 0
  %1 = zext i32 %add1 to i64
  %add3 = add nsw i32 %nk, 0
  %2 = zext i32 %add3 to i64
  %add5 = add nsw i32 %nj, 0
  %3 = zext i32 %add5 to i64
  %add7 = add nsw i32 %nl, 0
  %4 = zext i32 %add7 to i64
  %add9 = add nsw i32 %nm, 0
  %5 = zext i32 %add9 to i64
  %add11 = add nsw i32 %nl, 0
  %6 = zext i32 %add11 to i64

  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64
  %nm64 = sext i32 %nm to i64

  %ni.pos = icmp sgt i64 %ni64, 0
  %nj.pos = icmp sgt i64 %nj64, 0
  %nk.pos = icmp sgt i64 %nk64, 0
  %nl.pos = icmp sgt i64 %nl64, 0
  %nm.pos = icmp sgt i64 %nm64, 0

  ; ---------- Loop nest 1: E = A * B ----------
  %l1.cond1 = and i1 %ni.pos, %nj.pos
  br i1 %l1.cond1, label %l1.i.preheader, label %l1.end

l1.i.preheader:
  br label %l1.i.head

l1.i.head:
  %l1.i = phi i64 [ 0, %l1.i.preheader ], [ %l1.i.next, %l1.i.latch ]
  %l1.Arow = getelementptr inbounds double, ptr %A, i64 %l1.i.mul2
  br label %l1.j.head

l1.i.mul2 = mul nsw i64 %l1.i, %2

l1.j.head:
  %l1.j = phi i64 [ 0, %l1.i.head ], [ %l1.j.next, %l1.j.latch ]
  %l1.Erow = getelementptr inbounds double, ptr %E, i64 %l1.i.mul1
  %l1.Eelem = getelementptr inbounds double, ptr %l1.Erow, i64 %l1.j
  store double 0.000000e+00, ptr %l1.Eelem, align 8
  br i1 %nk.pos, label %l1.k.preheader, label %l1.k.end

l1.i.mul1 = mul nsw i64 %l1.i, %1

l1.k.preheader:
  br label %l1.k.head

l1.k.head:
  %l1.k = phi i64 [ 0, %l1.k.preheader ], [ %l1.k.next, %l1.k.head ]
  %l1.sum = phi double [ 0.000000e+00, %l1.k.preheader ], [ %l1.sum.next, %l1.k.head ]
  %l1.Aelem = getelementptr inbounds double, ptr %l1.Arow, i64 %l1.k
  %l1.Aval = load double, ptr %l1.Aelem, align 8
  %l1.Brow = getelementptr inbounds double, ptr %B, i64 %l1.k.mul
  %l1.Belem = getelementptr inbounds double, ptr %l1.Brow, i64 %l1.j
  %l1.Bval = load double, ptr %l1.Belem, align 8
  %l1.mul = fmul double %l1.Aval, %l1.Bval
  %l1.sum.next = fadd double %l1.sum, %l1.mul
  %l1.k.next = add nsw i64 %l1.k, 1
  %l1.k.cmp = icmp slt i64 %l1.k.next, %nk64
  br i1 %l1.k.cmp, label %l1.k.head, label %l1.k.exit

l1.k.mul = mul nsw i64 %l1.k, %3

l1.k.exit:
  store double %l1.sum.next, ptr %l1.Eelem, align 8
  br label %l1.j.latch

l1.k.end:
  br label %l1.j.latch

l1.j.latch:
  %l1.j.next = add nsw i64 %l1.j, 1
  %l1.j.cmp = icmp slt i64 %l1.j.next, %nj64
  br i1 %l1.j.cmp, label %l1.j.head, label %l1.i.latch

l1.i.latch:
  %l1.i.next = add nsw i64 %l1.i, 1
  %l1.i.cmp = icmp slt i64 %l1.i.next, %ni64
  br i1 %l1.i.cmp, label %l1.i.head, label %l1.end

l1.end:
  ; ---------- Loop nest 2: F = C * D ----------
  %l2.cond1 = and i1 %nj.pos, %nl.pos
  br i1 %l2.cond1, label %l2.i.preheader, label %l2.end

l2.i.preheader:
  br label %l2.i.head

l2.i.head:
  %l2.i = phi i64 [ 0, %l2.i.preheader ], [ %l2.i.next, %l2.i.latch ]
  %l2.Crow = getelementptr inbounds double, ptr %C, i64 %l2.i.mul2
  br label %l2.j.head

l2.i.mul2 = mul nsw i64 %l2.i, %5

l2.j.head:
  %l2.j = phi i64 [ 0, %l2.i.head ], [ %l2.j.next, %l2.j.latch ]
  %l2.Frow = getelementptr inbounds double, ptr %F, i64 %l2.i.mul1
  %l2.Felem = getelementptr inbounds double, ptr %l2.Frow, i64 %l2.j
  store double 0.000000e+00, ptr %l2.Felem, align 8
  br i1 %nm.pos, label %l2.k.preheader, label %l2.k.end

l2.i.mul1 = mul nsw i64 %l2.i, %4

l2.k.preheader:
  br label %l2.k.head

l2.k.head:
  %l2.k = phi i64 [ 0, %l2.k.preheader ], [ %l2.k.next, %l2.k.head ]
  %l2.sum = phi double [ 0.000000e+00, %l2.k.preheader ], [ %l2.sum.next, %l2.k.head ]
  %l2.Celem = getelementptr inbounds double, ptr %l2.Crow, i64 %l2.k
  %l2.Cval = load double, ptr %l2.Celem, align 8
  %l2.Drow = getelementptr inbounds double, ptr %D, i64 %l2.k.mul
  %l2.Delem = getelementptr inbounds double, ptr %l2.Drow, i64 %l2.j
  %l2.Dval = load double, ptr %l2.Delem, align 8
  %l2.mul = fmul double %l2.Cval, %l2.Dval
  %l2.sum.next = fadd double %l2.sum, %l2.mul
  %l2.k.next = add nsw i64 %l2.k, 1
  %l2.k.cmp = icmp slt i64 %l2.k.next, %nm64
  br i1 %l2.k.cmp, label %l2.k.head, label %l2.k.exit

l2.k.mul = mul nsw i64 %l2.k, %6

l2.k.exit:
  store double %l2.sum.next, ptr %l2.Felem, align 8
  br label %l2.j.latch

l2.k.end:
  br label %l2.j.latch

l2.j.latch:
  %l2.j.next = add nsw i64 %l2.j, 1
  %l2.j.cmp = icmp slt i64 %l2.j.next, %nl64
  br i1 %l2.j.cmp, label %l2.j.head, label %l2.i.latch

l2.i.latch:
  %l2.i.next = add nsw i64 %l2.i, 1
  %l2.i.cmp = icmp slt i64 %l2.i.next, %nj64
  br i1 %l2.i.cmp, label %l2.i.head, label %l2.end

l2.end:
  ; ---------- Loop nest 3: G = E * F ----------
  %l3.cond1 = and i1 %ni.pos, %nl.pos
  br i1 %l3.cond1, label %l3.i.preheader, label %l3.end

l3.i.preheader:
  br label %l3.i.head

l3.i.head:
  %l3.i = phi i64 [ 0, %l3.i.preheader ], [ %l3.i.next, %l3.i.latch ]
  %l3.Erow = getelementptr inbounds double, ptr %E, i64 %l3.i.mul2
  br label %l3.j.head

l3.i.mul2 = mul nsw i64 %l3.i, %1

l3.j.head:
  %l3.j = phi i64 [ 0, %l3.i.head ], [ %l3.j.next, %l3.j.latch ]
  %l3.Grow = getelementptr inbounds double, ptr %G, i64 %l3.i.mul1
  %l3.Gelem = getelementptr inbounds double, ptr %l3.Grow, i64 %l3.j
  store double 0.000000e+00, ptr %l3.Gelem, align 8
  br i1 %nj.pos, label %l3.k.preheader, label %l3.k.end

l3.i.mul1 = mul nsw i64 %l3.i, %0

l3.k.preheader:
  br label %l3.k.head

l3.k.head:
  %l3.k = phi i64 [ 0, %l3.k.preheader ], [ %l3.k.next, %l3.k.head ]
  %l3.sum = phi double [ 0.000000e+00, %l3.k.preheader ], [ %l3.sum.next, %l3.k.head ]
  %l3.Eelem = getelementptr inbounds double, ptr %l3.Erow, i64 %l3.k
  %l3.Eval = load double, ptr %l3.Eelem, align 8
  %l3.Frow = getelementptr inbounds double, ptr %F, i64 %l3.k.mul
  %l3.Felem = getelementptr inbounds double, ptr %l3.Frow, i64 %l3.j
  %l3.Fval = load double, ptr %l3.Felem, align 8
  %l3.mul = fmul double %l3.Eval, %l3.Fval
  %l3.sum.next = fadd double %l3.sum, %l3.mul
  %l3.k.next = add nsw i64 %l3.k, 1
  %l3.k.cmp = icmp slt i64 %l3.k.next, %nj64
  br i1 %l3.k.cmp, label %l3.k.head, label %l3.k.exit

l3.k.mul = mul nsw i64 %l3.k, %4

l3.k.exit:
  store double %l3.sum.next, ptr %l3.Gelem, align 8
  br label %l3.j.latch

l3.k.end:
  br label %l3.j.latch

l3.j.latch:
  %l3.j.next = add nsw i64 %l3.j, 1
  %l3.j.cmp = icmp slt i64 %l3.j.next, %nl64
  br i1 %l3.j.cmp, label %l3.j.head, label %l3.i.latch

l3.i.latch:
  %l3.i.next = add nsw i64 %l3.i, 1
  %l3.i.cmp = icmp slt i64 %l3.i.next, %ni64
  br i1 %l3.i.cmp, label %l3.i.head, label %l3.end

l3.end:
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
