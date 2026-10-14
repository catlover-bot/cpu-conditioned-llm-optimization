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

  ; ===================== E = A * B  (ni x nj), k over nk =====================
  %loop1.cond1 = and i1 %ni.pos, %nj.pos
  %loop1.run = and i1 %loop1.cond1, %nk.pos
  br i1 %ni.pos, label %e.i.preheader, label %e.i.end

e.i.preheader:
  br label %e.i.head

e.i.head:
  %e.i = phi i64 [0, %e.i.preheader], [%e.i.next, %e.i.latch]
  br i1 %nj.pos, label %e.j.preheader, label %e.i.latch

e.j.preheader:
  %e.Arow = mul nsw i64 %e.i, %nk64
  %e.Aptr.row = getelementptr inbounds double, ptr %A, i64 %e.Arow
  %e.Erow = mul nsw i64 %e.i, %nj64
  %e.Eptr.row = getelementptr inbounds double, ptr %E, i64 %e.Erow
  br label %e.j.head

e.j.head:
  %e.j = phi i64 [0, %e.j.preheader], [%e.j.next, %e.j.latch]
  %e.Eptr = getelementptr inbounds double, ptr %e.Eptr.row, i64 %e.j
  store double 0.000000e+00, ptr %e.Eptr, align 8
  br i1 %nk.pos, label %e.k.preheader, label %e.j.latch

e.k.preheader:
  br label %e.k.body

e.k.body:
  %e.k = phi i64 [0, %e.k.preheader], [%e.k.next, %e.k.body]
  %e.sum = phi double [0.000000e+00, %e.k.preheader], [%e.add, %e.k.body]
  %e.Aptr = getelementptr inbounds double, ptr %e.Aptr.row, i64 %e.k
  %e.a = load double, ptr %e.Aptr, align 8
  %e.Brow = mul nsw i64 %e.k, %nj64
  %e.Bptr.row = getelementptr inbounds double, ptr %B, i64 %e.Brow
  %e.Bptr = getelementptr inbounds double, ptr %e.Bptr.row, i64 %e.j
  %e.b = load double, ptr %e.Bptr, align 8
  %e.mul = fmul double %e.a, %e.b
  %e.add = fadd double %e.sum, %e.mul
  %e.k.next = add nsw i64 %e.k, 1
  %e.k.cmp = icmp slt i64 %e.k.next, %nk64
  br i1 %e.k.cmp, label %e.k.body, label %e.k.exit

e.k.exit:
  store double %e.add, ptr %e.Eptr, align 8
  br label %e.j.latch

e.j.latch:
  %e.j.next = add nsw i64 %e.j, 1
  %e.j.cmp = icmp slt i64 %e.j.next, %nj64
  br i1 %e.j.cmp, label %e.j.head, label %e.i.latch

e.i.latch:
  %e.i.next = add nsw i64 %e.i, 1
  %e.i.cmp = icmp slt i64 %e.i.next, %ni64
  br i1 %e.i.cmp, label %e.i.head, label %e.i.end

e.i.end:
  br label %f.i.check

  ; ===================== F = C * D  (nj x nl), k over nm =====================
f.i.check:
  br i1 %nj.pos, label %f.i.preheader, label %f.i.end

f.i.preheader:
  br label %f.i.head

f.i.head:
  %f.i = phi i64 [0, %f.i.preheader], [%f.i.next, %f.i.latch]
  br i1 %nl.pos, label %f.j.preheader, label %f.i.latch

f.j.preheader:
  %f.Crow = mul nsw i64 %f.i, %nm64
  %f.Cptr.row = getelementptr inbounds double, ptr %C, i64 %f.Crow
  %f.Frow = mul nsw i64 %f.i, %nl64
  %f.Fptr.row = getelementptr inbounds double, ptr %F, i64 %f.Frow
  br label %f.j.head

f.j.head:
  %f.j = phi i64 [0, %f.j.preheader], [%f.j.next, %f.j.latch]
  %f.Fptr = getelementptr inbounds double, ptr %f.Fptr.row, i64 %f.j
  store double 0.000000e+00, ptr %f.Fptr, align 8
  br i1 %nm.pos, label %f.k.preheader, label %f.j.latch

f.k.preheader:
  br label %f.k.body

f.k.body:
  %f.k = phi i64 [0, %f.k.preheader], [%f.k.next, %f.k.body]
  %f.sum = phi double [0.000000e+00, %f.k.preheader], [%f.add, %f.k.body]
  %f.Cptr = getelementptr inbounds double, ptr %f.Cptr.row, i64 %f.k
  %f.c = load double, ptr %f.Cptr, align 8
  %f.Drow = mul nsw i64 %f.k, %nl64
  %f.Dptr.row = getelementptr inbounds double, ptr %D, i64 %f.Drow
  %f.Dptr = getelementptr inbounds double, ptr %f.Dptr.row, i64 %f.j
  %f.d = load double, ptr %f.Dptr, align 8
  %f.mul = fmul double %f.c, %f.d
  %f.add = fadd double %f.sum, %f.mul
  %f.k.next = add nsw i64 %f.k, 1
  %f.k.cmp = icmp slt i64 %f.k.next, %nm64
  br i1 %f.k.cmp, label %f.k.body, label %f.k.exit

f.k.exit:
  store double %f.add, ptr %f.Fptr, align 8
  br label %f.j.latch

f.j.latch:
  %f.j.next = add nsw i64 %f.j, 1
  %f.j.cmp = icmp slt i64 %f.j.next, %nl64
  br i1 %f.j.cmp, label %f.j.head, label %f.i.latch

f.i.latch:
  %f.i.next = add nsw i64 %f.i, 1
  %f.i.cmp = icmp slt i64 %f.i.next, %nj64
  br i1 %f.i.cmp, label %f.i.head, label %f.i.end

f.i.end:
  br label %g.i.check

  ; ===================== G = E * F  (ni x nl), k over nj =====================
g.i.check:
  br i1 %ni.pos, label %g.i.preheader, label %g.i.end

g.i.preheader:
  br label %g.i.head

g.i.head:
  %g.i = phi i64 [0, %g.i.preheader], [%g.i.next, %g.i.latch]
  br i1 %nl.pos, label %g.j.preheader, label %g.i.latch

g.j.preheader:
  %g.Erow = mul nsw i64 %g.i, %nj64
  %g.Eptr.row = getelementptr inbounds double, ptr %E, i64 %g.Erow
  %g.Grow = mul nsw i64 %g.i, %nl64
  %g.Gptr.row = getelementptr inbounds double, ptr %G, i64 %g.Grow
  br label %g.j.head

g.j.head:
  %g.j = phi i64 [0, %g.j.preheader], [%g.j.next, %g.j.latch]
  %g.Gptr = getelementptr inbounds double, ptr %g.Gptr.row, i64 %g.j
  store double 0.000000e+00, ptr %g.Gptr, align 8
  br i1 %nj.pos, label %g.k.preheader, label %g.j.latch

g.k.preheader:
  br label %g.k.body

g.k.body:
  %g.k = phi i64 [0, %g.k.preheader], [%g.k.next, %g.k.body]
  %g.sum = phi double [0.000000e+00, %g.k.preheader], [%g.add, %g.k.body]
  %g.Eptr = getelementptr inbounds double, ptr %g.Eptr.row, i64 %g.k
  %g.e = load double, ptr %g.Eptr, align 8
  %g.Frow = mul nsw i64 %g.k, %nl64
  %g.Fptr.row = getelementptr inbounds double, ptr %F, i64 %g.Frow
  %g.Fptr = getelementptr inbounds double, ptr %g.Fptr.row, i64 %g.j
  %g.f = load double, ptr %g.Fptr, align 8
  %g.mul = fmul double %g.e, %g.f
  %g.add = fadd double %g.sum, %g.mul
  %g.k.next = add nsw i64 %g.k, 1
  %g.k.cmp = icmp slt i64 %g.k.next, %nj64
  br i1 %g.k.cmp, label %g.k.body, label %g.k.exit

g.k.exit:
  store double %g.add, ptr %g.Gptr, align 8
  br label %g.j.latch

g.j.latch:
  %g.j.next = add nsw i64 %g.j, 1
  %g.j.cmp = icmp slt i64 %g.j.next, %nl64
  br i1 %g.j.cmp, label %g.j.head, label %g.i.latch

g.i.latch:
  %g.i.next = add nsw i64 %g.i, 1
  %g.i.cmp = icmp slt i64 %g.i.next, %ni64
  br i1 %g.i.cmp, label %g.i.head, label %g.i.end

g.i.end:
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
