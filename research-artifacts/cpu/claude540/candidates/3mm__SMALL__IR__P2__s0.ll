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

  ; ---- E = A*B : (ni x nj) = (ni x nk) * (nk x nj) ----
  %cond1.0 = icmp sgt i32 %ni, 0
  br i1 %cond1.0, label %e.i.preheader, label %e.end

e.i.preheader:
  br label %e.i

e.i:
  %ei = phi i64 [ 0, %e.i.preheader ], [ %ei.next, %e.i.latch ]
  %cond1.1 = icmp sgt i32 %nj, 0
  br i1 %cond1.1, label %e.j.preheader, label %e.i.latch

e.j.preheader:
  %eirow_A = mul nsw i64 %ei, %nk64
  %eirow_A.ptr = getelementptr inbounds double, ptr %A, i64 %eirow_A
  %eirow_E = mul nsw i64 %ei, %nj64
  %eirow_E.ptr = getelementptr inbounds double, ptr %E, i64 %eirow_E
  br label %e.j

e.j:
  %ej = phi i64 [ 0, %e.j.preheader ], [ %ej.next, %e.j.latch ]
  %e.eptr = getelementptr inbounds double, ptr %eirow_E.ptr, i64 %ej
  store double 0.000000e+00, ptr %e.eptr, align 8
  %cond1.2 = icmp sgt i32 %nk, 0
  br i1 %cond1.2, label %e.k.preheader, label %e.j.latch

e.k.preheader:
  br label %e.k

e.k:
  %ek = phi i64 [ 0, %e.k.preheader ], [ %ek.next, %e.k ]
  %a.ptr = getelementptr inbounds double, ptr %eirow_A.ptr, i64 %ek
  %aval = load double, ptr %a.ptr, align 8
  %bkrow = mul nsw i64 %ek, %nj64
  %bkrow.ptr = getelementptr inbounds double, ptr %B, i64 %bkrow
  %b.ptr = getelementptr inbounds double, ptr %bkrow.ptr, i64 %ej
  %bval = load double, ptr %b.ptr, align 8
  %mulv = fmul double %aval, %bval
  %eold = load double, ptr %e.eptr, align 8
  %enew = fadd double %eold, %mulv
  store double %enew, ptr %e.eptr, align 8
  %ek.next = add nsw i64 %ek, 1
  %ekcmp = icmp slt i64 %ek.next, %nk64
  br i1 %ekcmp, label %e.k, label %e.j.latch

e.j.latch:
  %ej.next = add nsw i64 %ej, 1
  %ejcmp = icmp slt i64 %ej.next, %nj64
  br i1 %ejcmp, label %e.j, label %e.i.latch

e.i.latch:
  %ei.next = add nsw i64 %ei, 1
  %eicmp = icmp slt i64 %ei.next, %ni64
  br i1 %eicmp, label %e.i, label %e.end

e.end:
  ; ---- F = C*D : (nj x nl) = (nj x nm) * (nm x nl) ----
  %cond2.0 = icmp sgt i32 %nj, 0
  br i1 %cond2.0, label %f.i.preheader, label %f.end

f.i.preheader:
  br label %f.i

f.i:
  %fi = phi i64 [ 0, %f.i.preheader ], [ %fi.next, %f.i.latch ]
  %cond2.1 = icmp sgt i32 %nl, 0
  br i1 %cond2.1, label %f.j.preheader, label %f.i.latch

f.j.preheader:
  %firow_C = mul nsw i64 %fi, %nm64
  %firow_C.ptr = getelementptr inbounds double, ptr %C, i64 %firow_C
  %firow_F = mul nsw i64 %fi, %nl64
  %firow_F.ptr = getelementptr inbounds double, ptr %F, i64 %firow_F
  br label %f.j

f.j:
  %fj = phi i64 [ 0, %f.j.preheader ], [ %fj.next, %f.j.latch ]
  %f.fptr = getelementptr inbounds double, ptr %firow_F.ptr, i64 %fj
  store double 0.000000e+00, ptr %f.fptr, align 8
  %cond2.2 = icmp sgt i32 %nm, 0
  br i1 %cond2.2, label %f.k.preheader, label %f.j.latch

f.k.preheader:
  br label %f.k

f.k:
  %fk = phi i64 [ 0, %f.k.preheader ], [ %fk.next, %f.k ]
  %c.ptr = getelementptr inbounds double, ptr %firow_C.ptr, i64 %fk
  %cval = load double, ptr %c.ptr, align 8
  %dkrow = mul nsw i64 %fk, %nl64
  %dkrow.ptr = getelementptr inbounds double, ptr %D, i64 %dkrow
  %d.ptr = getelementptr inbounds double, ptr %dkrow.ptr, i64 %fj
  %dval = load double, ptr %d.ptr, align 8
  %mulv2 = fmul double %cval, %dval
  %fold = load double, ptr %f.fptr, align 8
  %fnew = fadd double %fold, %mulv2
  store double %fnew, ptr %f.fptr, align 8
  %fk.next = add nsw i64 %fk, 1
  %fkcmp = icmp slt i64 %fk.next, %nm64
  br i1 %fkcmp, label %f.k, label %f.j.latch

f.j.latch:
  %fj.next = add nsw i64 %fj, 1
  %fjcmp = icmp slt i64 %fj.next, %nl64
  br i1 %fjcmp, label %f.j, label %f.i.latch

f.i.latch:
  %fi.next = add nsw i64 %fi, 1
  %ficmp = icmp slt i64 %fi.next, %nj64
  br i1 %ficmp, label %f.i, label %f.end

f.end:
  ; ---- G = E*F : (ni x nl) = (ni x nj) * (nj x nl) ----
  %cond3.0 = icmp sgt i32 %ni, 0
  br i1 %cond3.0, label %g.i.preheader, label %g.end

g.i.preheader:
  br label %g.i

g.i:
  %gi = phi i64 [ 0, %g.i.preheader ], [ %gi.next, %g.i.latch ]
  %cond3.1 = icmp sgt i32 %nl, 0
  br i1 %cond3.1, label %g.j.preheader, label %g.i.latch

g.j.preheader:
  %girow_E = mul nsw i64 %gi, %nj64
  %girow_E.ptr = getelementptr inbounds double, ptr %E, i64 %girow_E
  %girow_G = mul nsw i64 %gi, %nl64
  %girow_G.ptr = getelementptr inbounds double, ptr %G, i64 %girow_G
  br label %g.j

g.j:
  %gj = phi i64 [ 0, %g.j.preheader ], [ %gj.next, %g.j.latch ]
  %g.gptr = getelementptr inbounds double, ptr %girow_G.ptr, i64 %gj
  store double 0.000000e+00, ptr %g.gptr, align 8
  %cond3.2 = icmp sgt i32 %nj, 0
  br i1 %cond3.2, label %g.k.preheader, label %g.j.latch

g.k.preheader:
  br label %g.k

g.k:
  %gk = phi i64 [ 0, %g.k.preheader ], [ %gk.next, %g.k ]
  %e2.ptr = getelementptr inbounds double, ptr %girow_E.ptr, i64 %gk
  %e2val = load double, ptr %e2.ptr, align 8
  %fkrow = mul nsw i64 %gk, %nl64
  %fkrow.ptr = getelementptr inbounds double, ptr %F, i64 %fkrow
  %f2.ptr = getelementptr inbounds double, ptr %fkrow.ptr, i64 %gj
  %f2val = load double, ptr %f2.ptr, align 8
  %mulv3 = fmul double %e2val, %f2val
  %gold = load double, ptr %g.gptr, align 8
  %gnew = fadd double %gold, %mulv3
  store double %gnew, ptr %g.gptr, align 8
  %gk.next = add nsw i64 %gk, 1
  %gkcmp = icmp slt i64 %gk.next, %nj64
  br i1 %gkcmp, label %g.k, label %g.j.latch

g.j.latch:
  %gj.next = add nsw i64 %gj, 1
  %gjcmp = icmp slt i64 %gj.next, %nl64
  br i1 %gjcmp, label %g.j, label %g.i.latch

g.i.latch:
  %gi.next = add nsw i64 %gi, 1
  %gicmp = icmp slt i64 %gi.next, %ni64
  br i1 %gicmp, label %g.i, label %g.end

g.end:
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
