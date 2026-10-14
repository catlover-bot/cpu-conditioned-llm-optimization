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

  ; ---- Loop nest 1: E = A * B  (ni x nj), k over nk ----
  %cmp.i.outer1 = icmp sgt i32 %ni, 0
  br i1 %cmp.i.outer1, label %l1.i.preheader, label %l1.end

l1.i.preheader:
  %cmp.j.1 = icmp sgt i32 %nj, 0
  %cmp.k.1 = icmp sgt i32 %nk, 0
  br label %l1.i

l1.i:
  %i1 = phi i64 [ 0, %l1.i.preheader ], [ %i1.next, %l1.i.latch ]
  br i1 %cmp.j.1, label %l1.j.preheader, label %l1.i.latch

l1.j.preheader:
  %Erow1 = mul nsw i64 %i1, %nj64
  %Erowptr1 = getelementptr inbounds double, ptr %E, i64 %Erow1
  %Arow1 = mul nsw i64 %i1, %nk64
  %Arowptr1 = getelementptr inbounds double, ptr %A, i64 %Arow1
  br label %l1.j

l1.j:
  %j1 = phi i64 [ 0, %l1.j.preheader ], [ %j1.next, %l1.j.latch ]
  %Eelem1 = getelementptr inbounds double, ptr %Erowptr1, i64 %j1
  store double 0.000000e+00, ptr %Eelem1, align 8
  br i1 %cmp.k.1, label %l1.k.preheader, label %l1.j.latch

l1.k.preheader:
  br label %l1.k

l1.k:
  %k1 = phi i64 [ 0, %l1.k.preheader ], [ %k1.next, %l1.k ]
  %acc1 = phi double [ 0.000000e+00, %l1.k.preheader ], [ %add1, %l1.k ]
  %Aelem1 = getelementptr inbounds double, ptr %Arowptr1, i64 %k1
  %aval1 = load double, ptr %Aelem1, align 8
  %Brow1 = mul nsw i64 %k1, %nj64
  %Browptr1 = getelementptr inbounds double, ptr %B, i64 %Brow1
  %Belem1 = getelementptr inbounds double, ptr %Browptr1, i64 %j1
  %bval1 = load double, ptr %Belem1, align 8
  %mul1 = fmul double %aval1, %bval1
  %add1 = fadd double %acc1, %mul1
  store double %add1, ptr %Eelem1, align 8
  %k1.next = add nuw nsw i64 %k1, 1
  %k1.done = icmp eq i64 %k1.next, %nk64
  br i1 %k1.done, label %l1.j.latch, label %l1.k

l1.j.latch:
  %j1.next = add nuw nsw i64 %j1, 1
  %j1.done = icmp eq i64 %j1.next, %nj64
  br i1 %j1.done, label %l1.i.latch, label %l1.j

l1.i.latch:
  %i1.next = add nuw nsw i64 %i1, 1
  %i1.done = icmp eq i64 %i1.next, %ni64
  br i1 %i1.done, label %l1.end, label %l1.i

l1.end:
  ; ---- Loop nest 2: F = C * D  (nj x nl), k over nm ----
  %cmp.i.outer2 = icmp sgt i32 %nj, 0
  br i1 %cmp.i.outer2, label %l2.i.preheader, label %l2.end

l2.i.preheader:
  %cmp.j.2 = icmp sgt i32 %nl, 0
  %cmp.k.2 = icmp sgt i32 %nm, 0
  br label %l2.i

l2.i:
  %i2 = phi i64 [ 0, %l2.i.preheader ], [ %i2.next, %l2.i.latch ]
  br i1 %cmp.j.2, label %l2.j.preheader, label %l2.i.latch

l2.j.preheader:
  %Frow2 = mul nsw i64 %i2, %nl64
  %Frowptr2 = getelementptr inbounds double, ptr %F, i64 %Frow2
  %Crow2 = mul nsw i64 %i2, %nm64
  %Crowptr2 = getelementptr inbounds double, ptr %C, i64 %Crow2
  br label %l2.j

l2.j:
  %j2 = phi i64 [ 0, %l2.j.preheader ], [ %j2.next, %l2.j.latch ]
  %Felem2 = getelementptr inbounds double, ptr %Frowptr2, i64 %j2
  store double 0.000000e+00, ptr %Felem2, align 8
  br i1 %cmp.k.2, label %l2.k.preheader, label %l2.j.latch

l2.k.preheader:
  br label %l2.k

l2.k:
  %k2 = phi i64 [ 0, %l2.k.preheader ], [ %k2.next, %l2.k ]
  %acc2 = phi double [ 0.000000e+00, %l2.k.preheader ], [ %add2, %l2.k ]
  %Celem2 = getelementptr inbounds double, ptr %Crowptr2, i64 %k2
  %cval2 = load double, ptr %Celem2, align 8
  %Drow2 = mul nsw i64 %k2, %nl64
  %Drowptr2 = getelementptr inbounds double, ptr %D, i64 %Drow2
  %Delem2 = getelementptr inbounds double, ptr %Drowptr2, i64 %j2
  %dval2 = load double, ptr %Delem2, align 8
  %mul2 = fmul double %cval2, %dval2
  %add2 = fadd double %acc2, %mul2
  store double %add2, ptr %Felem2, align 8
  %k2.next = add nuw nsw i64 %k2, 1
  %k2.done = icmp eq i64 %k2.next, %nm64
  br i1 %k2.done, label %l2.j.latch, label %l2.k

l2.j.latch:
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.done = icmp eq i64 %j2.next, %nl64
  br i1 %j2.done, label %l2.i.latch, label %l2.j

l2.i.latch:
  %i2.next = add nuw nsw i64 %i2, 1
  %i2.done = icmp eq i64 %i2.next, %nj64
  br i1 %i2.done, label %l2.end, label %l2.i

l2.end:
  ; ---- Loop nest 3: G = E * F  (ni x nl), k over nj ----
  %cmp.i.outer3 = icmp sgt i32 %ni, 0
  br i1 %cmp.i.outer3, label %l3.i.preheader, label %l3.end

l3.i.preheader:
  %cmp.j.3 = icmp sgt i32 %nl, 0
  %cmp.k.3 = icmp sgt i32 %nj, 0
  br label %l3.i

l3.i:
  %i3 = phi i64 [ 0, %l3.i.preheader ], [ %i3.next, %l3.i.latch ]
  br i1 %cmp.j.3, label %l3.j.preheader, label %l3.i.latch

l3.j.preheader:
  %Grow3 = mul nsw i64 %i3, %nl64
  %Growptr3 = getelementptr inbounds double, ptr %G, i64 %Grow3
  %Erow3 = mul nsw i64 %i3, %nj64
  %Erowptr3 = getelementptr inbounds double, ptr %E, i64 %Erow3
  br label %l3.j

l3.j:
  %j3 = phi i64 [ 0, %l3.j.preheader ], [ %j3.next, %l3.j.latch ]
  %Gelem3 = getelementptr inbounds double, ptr %Growptr3, i64 %j3
  store double 0.000000e+00, ptr %Gelem3, align 8
  br i1 %cmp.k.3, label %l3.k.preheader, label %l3.j.latch

l3.k.preheader:
  br label %l3.k

l3.k:
  %k3 = phi i64 [ 0, %l3.k.preheader ], [ %k3.next, %l3.k ]
  %acc3 = phi double [ 0.000000e+00, %l3.k.preheader ], [ %add3, %l3.k ]
  %Eelem3 = getelementptr inbounds double, ptr %Erowptr3, i64 %k3
  %eval3 = load double, ptr %Eelem3, align 8
  %Frow3 = mul nsw i64 %k3, %nl64
  %Frowptr3 = getelementptr inbounds double, ptr %F, i64 %Frow3
  %Felem3 = getelementptr inbounds double, ptr %Frowptr3, i64 %j3
  %fval3 = load double, ptr %Felem3, align 8
  %mul3 = fmul double %eval3, %fval3
  %add3 = fadd double %acc3, %mul3
  store double %add3, ptr %Gelem3, align 8
  %k3.next = add nuw nsw i64 %k3, 1
  %k3.done = icmp eq i64 %k3.next, %nj64
  br i1 %k3.done, label %l3.j.latch, label %l3.k

l3.j.latch:
  %j3.next = add nuw nsw i64 %j3, 1
  %j3.done = icmp eq i64 %j3.next, %nl64
  br i1 %j3.done, label %l3.i.latch, label %l3.j

l3.i.latch:
  %i3.next = add nuw nsw i64 %i3, 1
  %i3.done = icmp eq i64 %i3.next, %ni64
  br i1 %i3.done, label %l3.end, label %l3.i

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
