; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_3mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, i32 noundef %nm, ptr noundef %E, ptr noundef %A, ptr noundef %B, ptr noundef %F, ptr noundef %C, ptr noundef %D, ptr noundef %G) #0 {
entry:
  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64
  %nm64 = sext i32 %nm to i64

  %ni.pos = icmp sgt i32 %ni, 0
  %nj.pos = icmp sgt i32 %nj, 0
  %nk.pos = icmp sgt i32 %nk, 0
  %nl.pos = icmp sgt i32 %nl, 0
  %nm.pos = icmp sgt i32 %nm, 0

  ; ---------- Loop 1: E = A*B ----------
  %l1.cond = and i1 %ni.pos, %nj.pos
  br i1 %l1.cond, label %l1.i.preheader, label %loop2.entry

l1.i.preheader:
  br label %l1.i

l1.i:
  %i1 = phi i64 [ 0, %l1.i.preheader ], [ %i1.next, %l1.i.latch ]
  %Erow.base = mul nsw i64 %i1, %nj64
  %Erow.ptr = getelementptr inbounds double, ptr %E, i64 %Erow.base
  %Arow.base = mul nsw i64 %i1, %nk64
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.base
  br label %l1.j

l1.j:
  %j1 = phi i64 [ 0, %l1.i ], [ %j1.next, %l1.j.latch ]
  %Eij.ptr = getelementptr inbounds double, ptr %Erow.ptr, i64 %j1
  store double 0.000000e+00, ptr %Eij.ptr, align 8
  br i1 %nk.pos, label %l1.k.preheader, label %l1.j.latch

l1.k.preheader:
  br label %l1.k

l1.k:
  %k1 = phi i64 [ 0, %l1.k.preheader ], [ %k1.next, %l1.k ]
  %acc1 = phi double [ 0.000000e+00, %l1.k.preheader ], [ %add34, %l1.k ]
  %Aik.ptr = getelementptr inbounds double, ptr %Arow.ptr, i64 %k1
  %aval = load double, ptr %Aik.ptr, align 8
  %Bk.base = mul nsw i64 %k1, %nj64
  %Bkrow.ptr = getelementptr inbounds double, ptr %B, i64 %Bk.base
  %Bkj.ptr = getelementptr inbounds double, ptr %Bkrow.ptr, i64 %j1
  %bval = load double, ptr %Bkj.ptr, align 8
  %mul1 = fmul double %aval, %bval
  %add34 = fadd double %acc1, %mul1
  %k1.next = add nuw nsw i64 %k1, 1
  %k1.done = icmp eq i64 %k1.next, %nk64
  br i1 %k1.done, label %l1.k.exit, label %l1.k

l1.k.exit:
  store double %add34, ptr %Eij.ptr, align 8
  br label %l1.j.latch

l1.j.latch:
  %j1.next = add nuw nsw i64 %j1, 1
  %j1.done = icmp eq i64 %j1.next, %nj64
  br i1 %j1.done, label %l1.i.latch, label %l1.j

l1.i.latch:
  %i1.next = add nuw nsw i64 %i1, 1
  %i1.done = icmp eq i64 %i1.next, %ni64
  br i1 %i1.done, label %loop2.entry, label %l1.i

  ; ---------- Loop 2: F = C*D ----------
loop2.entry:
  %l2.cond = and i1 %nj.pos, %nl.pos
  br i1 %l2.cond, label %l2.i.preheader, label %loop3.entry

l2.i.preheader:
  br label %l2.i

l2.i:
  %i2 = phi i64 [ 0, %l2.i.preheader ], [ %i2.next, %l2.i.latch ]
  %Frow.base = mul nsw i64 %i2, %nl64
  %Frow.ptr = getelementptr inbounds double, ptr %F, i64 %Frow.base
  %Crow.base = mul nsw i64 %i2, %nm64
  %Crow.ptr = getelementptr inbounds double, ptr %C, i64 %Crow.base
  br label %l2.j

l2.j:
  %j2 = phi i64 [ 0, %l2.i ], [ %j2.next, %l2.j.latch ]
  %Fij.ptr = getelementptr inbounds double, ptr %Frow.ptr, i64 %j2
  store double 0.000000e+00, ptr %Fij.ptr, align 8
  br i1 %nm.pos, label %l2.k.preheader, label %l2.j.latch

l2.k.preheader:
  br label %l2.k

l2.k:
  %k2 = phi i64 [ 0, %l2.k.preheader ], [ %k2.next, %l2.k ]
  %acc2 = phi double [ 0.000000e+00, %l2.k.preheader ], [ %add67, %l2.k ]
  %Cik.ptr = getelementptr inbounds double, ptr %Crow.ptr, i64 %k2
  %cval = load double, ptr %Cik.ptr, align 8
  %Dk.base = mul nsw i64 %k2, %nl64
  %Dkrow.ptr = getelementptr inbounds double, ptr %D, i64 %Dk.base
  %Dkj.ptr = getelementptr inbounds double, ptr %Dkrow.ptr, i64 %j2
  %dval = load double, ptr %Dkj.ptr, align 8
  %mul2 = fmul double %cval, %dval
  %add67 = fadd double %acc2, %mul2
  %k2.next = add nuw nsw i64 %k2, 1
  %k2.done = icmp eq i64 %k2.next, %nm64
  br i1 %k2.done, label %l2.k.exit, label %l2.k

l2.k.exit:
  store double %add67, ptr %Fij.ptr, align 8
  br label %l2.j.latch

l2.j.latch:
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.done = icmp eq i64 %j2.next, %nl64
  br i1 %j2.done, label %l2.i.latch, label %l2.j

l2.i.latch:
  %i2.next = add nuw nsw i64 %i2, 1
  %i2.done = icmp eq i64 %i2.next, %nj64
  br i1 %i2.done, label %loop3.entry, label %l2.i

  ; ---------- Loop 3: G = E*F ----------
loop3.entry:
  %l3.cond = and i1 %ni.pos, %nl.pos
  br i1 %l3.cond, label %l3.i.preheader, label %exit

l3.i.preheader:
  br label %l3.i

l3.i:
  %i3 = phi i64 [ 0, %l3.i.preheader ], [ %i3.next, %l3.i.latch ]
  %Grow.base = mul nsw i64 %i3, %nl64
  %Grow.ptr = getelementptr inbounds double, ptr %G, i64 %Grow.base
  %Erow3.base = mul nsw i64 %i3, %nj64
  %Erow3.ptr = getelementptr inbounds double, ptr %E, i64 %Erow3.base
  br label %l3.j

l3.j:
  %j3 = phi i64 [ 0, %l3.i ], [ %j3.next, %l3.j.latch ]
  %Gij.ptr = getelementptr inbounds double, ptr %Grow.ptr, i64 %j3
  store double 0.000000e+00, ptr %Gij.ptr, align 8
  br i1 %nj.pos, label %l3.k.preheader, label %l3.j.latch

l3.k.preheader:
  br label %l3.k

l3.k:
  %k3 = phi i64 [ 0, %l3.k.preheader ], [ %k3.next, %l3.k ]
  %acc3 = phi double [ 0.000000e+00, %l3.k.preheader ], [ %add103, %l3.k ]
  %Eik.ptr = getelementptr inbounds double, ptr %Erow3.ptr, i64 %k3
  %eval = load double, ptr %Eik.ptr, align 8
  %Fk.base = mul nsw i64 %k3, %nl64
  %Fkrow.ptr = getelementptr inbounds double, ptr %F, i64 %Fk.base
  %Fkj.ptr = getelementptr inbounds double, ptr %Fkrow.ptr, i64 %j3
  %fval = load double, ptr %Fkj.ptr, align 8
  %mul3 = fmul double %eval, %fval
  %add103 = fadd double %acc3, %mul3
  %k3.next = add nuw nsw i64 %k3, 1
  %k3.done = icmp eq i64 %k3.next, %nj64
  br i1 %k3.done, label %l3.k.exit, label %l3.k

l3.k.exit:
  store double %add103, ptr %Gij.ptr, align 8
  br label %l3.j.latch

l3.j.latch:
  %j3.next = add nuw nsw i64 %j3, 1
  %j3.done = icmp eq i64 %j3.next, %nl64
  br i1 %j3.done, label %l3.i.latch, label %l3.j

l3.i.latch:
  %i3.next = add nuw nsw i64 %i3, 1
  %i3.done = icmp eq i64 %i3.next, %ni64
  br i1 %i3.done, label %exit, label %l3.i

exit:
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
