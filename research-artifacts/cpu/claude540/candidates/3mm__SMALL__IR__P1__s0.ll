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

  %ni_pos = icmp sgt i32 %ni, 0
  %nj_pos = icmp sgt i32 %nj, 0
  %nk_pos = icmp sgt i32 %nk, 0
  %nl_pos = icmp sgt i32 %nl, 0
  %nm_pos = icmp sgt i32 %nm, 0

  ; ===================== E = A*B  (ni x nj), inner nk =====================
  %loop1.cond = and i1 %ni_pos, %nj_pos
  br i1 %loop1.cond, label %e.i.preheader, label %e.done

e.i.preheader:
  br label %e.i.head

e.i.head:
  %e.i = phi i64 [0, %e.i.preheader], [%e.i.next, %e.i.latch]
  %e.i.rowA = mul nsw i64 %e.i, %nk64
  %e.i.rowE = mul nsw i64 %e.i, %nj64
  br label %e.j.head

e.j.head:
  %e.j = phi i64 [0, %e.i.head], [%e.j.next, %e.j.latch]
  %e.eptr = getelementptr inbounds double, ptr %E, i64 %e.i.rowE
  %e.eptr2 = getelementptr inbounds double, ptr %e.eptr, i64 %e.j
  store double 0.000000e+00, ptr %e.eptr2, align 8
  br i1 %nk_pos, label %e.k.preheader, label %e.j.latch

e.k.preheader:
  %e.aptr = getelementptr inbounds double, ptr %A, i64 %e.i.rowA
  br label %e.k.head

e.k.head:
  %e.k = phi i64 [0, %e.k.preheader], [%e.k.next, %e.k.head]
  %e.aelem = getelementptr inbounds double, ptr %e.aptr, i64 %e.k
  %e.aval = load double, ptr %e.aelem, align 8
  %e.brow = mul nsw i64 %e.k, %nj64
  %e.bptr = getelementptr inbounds double, ptr %B, i64 %e.brow
  %e.belem = getelementptr inbounds double, ptr %e.bptr, i64 %e.j
  %e.bval = load double, ptr %e.belem, align 8
  %e.mul = fmul double %e.aval, %e.bval
  %e.old = load double, ptr %e.eptr2, align 8
  %e.new = fadd double %e.old, %e.mul
  store double %e.new, ptr %e.eptr2, align 8
  %e.k.next = add nsw i64 %e.k, 1
  %e.k.exit = icmp eq i64 %e.k.next, %nk64
  br i1 %e.k.exit, label %e.j.latch, label %e.k.head

e.j.latch:
  %e.j.next = add nsw i64 %e.j, 1
  %e.j.exit = icmp eq i64 %e.j.next, %nj64
  br i1 %e.j.exit, label %e.i.latch, label %e.j.head

e.i.latch:
  %e.i.next = add nsw i64 %e.i, 1
  %e.i.exit = icmp eq i64 %e.i.next, %ni64
  br i1 %e.i.exit, label %e.done, label %e.i.head

e.done:
  ; ===================== F = C*D  (nj x nl), inner nm =====================
  %loop2.cond = and i1 %nj_pos, %nl_pos
  br i1 %loop2.cond, label %f.i.preheader, label %f.done

f.i.preheader:
  br label %f.i.head

f.i.head:
  %f.i = phi i64 [0, %f.i.preheader], [%f.i.next, %f.i.latch]
  %f.i.rowC = mul nsw i64 %f.i, %nm64
  %f.i.rowF = mul nsw i64 %f.i, %nl64
  br label %f.j.head

f.j.head:
  %f.j = phi i64 [0, %f.i.head], [%f.j.next, %f.j.latch]
  %f.fptr = getelementptr inbounds double, ptr %F, i64 %f.i.rowF
  %f.fptr2 = getelementptr inbounds double, ptr %f.fptr, i64 %f.j
  store double 0.000000e+00, ptr %f.fptr2, align 8
  br i1 %nm_pos, label %f.k.preheader, label %f.j.latch

f.k.preheader:
  %f.cptr = getelementptr inbounds double, ptr %C, i64 %f.i.rowC
  br label %f.k.head

f.k.head:
  %f.k = phi i64 [0, %f.k.preheader], [%f.k.next, %f.k.head]
  %f.celem = getelementptr inbounds double, ptr %f.cptr, i64 %f.k
  %f.cval = load double, ptr %f.celem, align 8
  %f.drow = mul nsw i64 %f.k, %nl64
  %f.dptr = getelementptr inbounds double, ptr %D, i64 %f.drow
  %f.delem = getelementptr inbounds double, ptr %f.dptr, i64 %f.j
  %f.dval = load double, ptr %f.delem, align 8
  %f.mul = fmul double %f.cval, %f.dval
  %f.old = load double, ptr %f.fptr2, align 8
  %f.new = fadd double %f.old, %f.mul
  store double %f.new, ptr %f.fptr2, align 8
  %f.k.next = add nsw i64 %f.k, 1
  %f.k.exit = icmp eq i64 %f.k.next, %nm64
  br i1 %f.k.exit, label %f.j.latch, label %f.k.head

f.j.latch:
  %f.j.next = add nsw i64 %f.j, 1
  %f.j.exit = icmp eq i64 %f.j.next, %nl64
  br i1 %f.j.exit, label %f.i.latch, label %f.j.head

f.i.latch:
  %f.i.next = add nsw i64 %f.i, 1
  %f.i.exit = icmp eq i64 %f.i.next, %nj64
  br i1 %f.i.exit, label %f.done, label %f.i.head

f.done:
  ; ===================== G = E*F  (ni x nl), inner nj =====================
  %loop3.cond = and i1 %ni_pos, %nl_pos
  br i1 %loop3.cond, label %g.i.preheader, label %g.done

g.i.preheader:
  br label %g.i.head

g.i.head:
  %g.i = phi i64 [0, %g.i.preheader], [%g.i.next, %g.i.latch]
  %g.i.rowE = mul nsw i64 %g.i, %nj64
  %g.i.rowG = mul nsw i64 %g.i, %nl64
  br label %g.j.head

g.j.head:
  %g.j = phi i64 [0, %g.i.head], [%g.j.next, %g.j.latch]
  %g.gptr = getelementptr inbounds double, ptr %G, i64 %g.i.rowG
  %g.gptr2 = getelementptr inbounds double, ptr %g.gptr, i64 %g.j
  store double 0.000000e+00, ptr %g.gptr2, align 8
  br i1 %nj_pos, label %g.k.preheader, label %g.j.latch

g.k.preheader:
  %g.eptr = getelementptr inbounds double, ptr %E, i64 %g.i.rowE
  br label %g.k.head

g.k.head:
  %g.k = phi i64 [0, %g.k.preheader], [%g.k.next, %g.k.head]
  %g.eelem = getelementptr inbounds double, ptr %g.eptr, i64 %g.k
  %g.eval = load double, ptr %g.eelem, align 8
  %g.frow = mul nsw i64 %g.k, %nl64
  %g.fptr = getelementptr inbounds double, ptr %F, i64 %g.frow
  %g.felem = getelementptr inbounds double, ptr %g.fptr, i64 %g.j
  %g.fval = load double, ptr %g.felem, align 8
  %g.mul = fmul double %g.eval, %g.fval
  %g.old = load double, ptr %g.gptr2, align 8
  %g.new = fadd double %g.old, %g.mul
  store double %g.new, ptr %g.gptr2, align 8
  %g.k.next = add nsw i64 %g.k, 1
  %g.k.exit = icmp eq i64 %g.k.next, %nj64
  br i1 %g.k.exit, label %g.j.latch, label %g.k.head

g.j.latch:
  %g.j.next = add nsw i64 %g.j, 1
  %g.j.exit = icmp eq i64 %g.j.next, %nl64
  br i1 %g.j.exit, label %g.i.latch, label %g.j.head

g.i.latch:
  %g.i.next = add nsw i64 %g.i, 1
  %g.i.exit = icmp eq i64 %g.i.next, %ni64
  br i1 %g.i.exit, label %g.done, label %g.i.head

g.done:
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
