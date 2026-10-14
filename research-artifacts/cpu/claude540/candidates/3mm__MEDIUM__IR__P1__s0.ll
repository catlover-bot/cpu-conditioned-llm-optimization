; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_3mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, i32 noundef %nm, ptr noundef %E, ptr noundef %A, ptr noundef %B, ptr noundef %F, ptr noundef %C, ptr noundef %D, ptr noundef %G) #0 {
entry:
  %ni.z = sext i32 %ni to i64
  %nj.z = sext i32 %nj to i64
  %nk.z = sext i32 %nk to i64
  %nl.z = sext i32 %nl to i64
  %nm.z = sext i32 %nm to i64

  %ni.pos = icmp sgt i64 %ni.z, 0
  %nj.pos = icmp sgt i64 %nj.z, 0
  %nk.pos = icmp sgt i64 %nk.z, 0
  %nl.pos = icmp sgt i64 %nl.z, 0
  %nm.pos = icmp sgt i64 %nm.z, 0

  ; ===== E = A*B : ni x nj, over nk =====
  %loop1.cond = and i1 %ni.pos, %nj.pos
  br i1 %loop1.cond, label %l1.i.preheader, label %phase2.entry

l1.i.preheader:
  br label %l1.i

l1.i:
  %i1 = phi i64 [ 0, %l1.i.preheader ], [ %i1.next, %l1.i.latch ]
  br label %l1.j.preheader

l1.j.preheader:
  br label %l1.j

l1.j:
  %j1 = phi i64 [ 0, %l1.j.preheader ], [ %j1.next, %l1.j.latch ]
  %e.off = mul nsw i64 %i1, %nj.z
  %e.off2 = add i64 %e.off, %j1
  %e.ptr = getelementptr inbounds double, ptr %E, i64 %e.off2
  store double 0.000000e+00, ptr %e.ptr, align 8
  br i1 %nk.pos, label %l1.k.preheader, label %l1.k.end

l1.k.preheader:
  %a.row = mul nsw i64 %i1, %nk.z
  %a.rowptr = getelementptr inbounds double, ptr %A, i64 %a.row
  br label %l1.k

l1.k:
  %k1 = phi i64 [ 0, %l1.k.preheader ], [ %k1.next, %l1.k ]
  %e.acc = phi double [ 0.000000e+00, %l1.k.preheader ], [ %e.add, %l1.k ]
  %a.ptr = getelementptr inbounds double, ptr %a.rowptr, i64 %k1
  %a.val = load double, ptr %a.ptr, align 8
  %b.row = mul nsw i64 %k1, %nj.z
  %b.rowptr = getelementptr inbounds double, ptr %B, i64 %b.row
  %b.ptr = getelementptr inbounds double, ptr %b.rowptr, i64 %j1
  %b.val = load double, ptr %b.ptr, align 8
  %mul1 = fmul double %a.val, %b.val
  %e.add = fadd double %e.acc, %mul1
  %k1.next = add nsw i64 %k1, 1
  %k1.done = icmp eq i64 %k1.next, %nk.z
  br i1 %k1.done, label %l1.k.exit, label %l1.k, !llvm.loop !10

l1.k.exit:
  store double %e.add, ptr %e.ptr, align 8
  br label %l1.j.latch

l1.k.end:
  br label %l1.j.latch

l1.j.latch:
  %j1.next = add nsw i64 %j1, 1
  %j1.done = icmp eq i64 %j1.next, %nj.z
  br i1 %j1.done, label %l1.i.latch, label %l1.j, !llvm.loop !11

l1.i.latch:
  %i1.next = add nsw i64 %i1, 1
  %i1.done = icmp eq i64 %i1.next, %ni.z
  br i1 %i1.done, label %phase2.entry, label %l1.i, !llvm.loop !12

phase2.entry:
  ; ===== F = C*D : nj x nl, over nm =====
  %loop2.cond = and i1 %nj.pos, %nl.pos
  br i1 %loop2.cond, label %l2.i.preheader, label %phase3.entry

l2.i.preheader:
  br label %l2.i

l2.i:
  %i2 = phi i64 [ 0, %l2.i.preheader ], [ %i2.next, %l2.i.latch ]
  br label %l2.j.preheader

l2.j.preheader:
  br label %l2.j

l2.j:
  %j2 = phi i64 [ 0, %l2.j.preheader ], [ %j2.next, %l2.j.latch ]
  %f.off = mul nsw i64 %i2, %nl.z
  %f.off2 = add i64 %f.off, %j2
  %f.ptr = getelementptr inbounds double, ptr %F, i64 %f.off2
  store double 0.000000e+00, ptr %f.ptr, align 8
  br i1 %nm.pos, label %l2.k.preheader, label %l2.k.end

l2.k.preheader:
  %c.row = mul nsw i64 %i2, %nm.z
  %c.rowptr = getelementptr inbounds double, ptr %C, i64 %c.row
  br label %l2.k

l2.k:
  %k2 = phi i64 [ 0, %l2.k.preheader ], [ %k2.next, %l2.k ]
  %f.acc = phi double [ 0.000000e+00, %l2.k.preheader ], [ %f.add, %l2.k ]
  %c.ptr = getelementptr inbounds double, ptr %c.rowptr, i64 %k2
  %c.val = load double, ptr %c.ptr, align 8
  %d.row = mul nsw i64 %k2, %nl.z
  %d.rowptr = getelementptr inbounds double, ptr %D, i64 %d.row
  %d.ptr = getelementptr inbounds double, ptr %d.rowptr, i64 %j2
  %d.val = load double, ptr %d.ptr, align 8
  %mul2 = fmul double %c.val, %d.val
  %f.add = fadd double %f.acc, %mul2
  %k2.next = add nsw i64 %k2, 1
  %k2.done = icmp eq i64 %k2.next, %nm.z
  br i1 %k2.done, label %l2.k.exit, label %l2.k, !llvm.loop !13

l2.k.exit:
  store double %f.add, ptr %f.ptr, align 8
  br label %l2.j.latch

l2.k.end:
  br label %l2.j.latch

l2.j.latch:
  %j2.next = add nsw i64 %j2, 1
  %j2.done = icmp eq i64 %j2.next, %nl.z
  br i1 %j2.done, label %l2.i.latch, label %l2.j, !llvm.loop !14

l2.i.latch:
  %i2.next = add nsw i64 %i2, 1
  %i2.done = icmp eq i64 %i2.next, %nj.z
  br i1 %i2.done, label %phase3.entry, label %l2.i, !llvm.loop !15

phase3.entry:
  ; ===== G = E*F : ni x nl, over nj =====
  %loop3.cond = and i1 %ni.pos, %nl.pos
  br i1 %loop3.cond, label %l3.i.preheader, label %exit

l3.i.preheader:
  br label %l3.i

l3.i:
  %i3 = phi i64 [ 0, %l3.i.preheader ], [ %i3.next, %l3.i.latch ]
  br label %l3.j.preheader

l3.j.preheader:
  br label %l3.j

l3.j:
  %j3 = phi i64 [ 0, %l3.j.preheader ], [ %j3.next, %l3.j.latch ]
  %g.off = mul nsw i64 %i3, %nl.z
  %g.off2 = add i64 %g.off, %j3
  %g.ptr = getelementptr inbounds double, ptr %G, i64 %g.off2
  store double 0.000000e+00, ptr %g.ptr, align 8
  br i1 %nj.pos, label %l3.k.preheader, label %l3.k.end

l3.k.preheader:
  %e.row = mul nsw i64 %i3, %nj.z
  %e.rowptr = getelementptr inbounds double, ptr %E, i64 %e.row
  br label %l3.k

l3.k:
  %k3 = phi i64 [ 0, %l3.k.preheader ], [ %k3.next, %l3.k ]
  %g.acc = phi double [ 0.000000e+00, %l3.k.preheader ], [ %g.add, %l3.k ]
  %e2.ptr = getelementptr inbounds double, ptr %e.rowptr, i64 %k3
  %e2.val = load double, ptr %e2.ptr, align 8
  %f.row = mul nsw i64 %k3, %nl.z
  %f.rowptr = getelementptr inbounds double, ptr %F, i64 %f.row
  %f2.ptr = getelementptr inbounds double, ptr %f.rowptr, i64 %j3
  %f2.val = load double, ptr %f2.ptr, align 8
  %mul3 = fmul double %e2.val, %f2.val
  %g.add = fadd double %g.acc, %mul3
  %k3.next = add nsw i64 %k3, 1
  %k3.done = icmp eq i64 %k3.next, %nj.z
  br i1 %k3.done, label %l3.k.exit, label %l3.k, !llvm.loop !16

l3.k.exit:
  store double %g.add, ptr %g.ptr, align 8
  br label %l3.j.latch

l3.k.end:
  br label %l3.j.latch

l3.j.latch:
  %j3.next = add nsw i64 %j3, 1
  %j3.done = icmp eq i64 %j3.next, %nl.z
  br i1 %j3.done, label %l3.i.latch, label %l3.j, !llvm.loop !17

l3.i.latch:
  %i3.next = add nsw i64 %i3, 1
  %i3.done = icmp eq i64 %i3.next, %ni.z
  br i1 %i3.done, label %exit, label %l3.i, !llvm.loop !18

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
!14 = distinct !{!14, !7}
!15 = distinct !{!15, !7}
!16 = distinct !{!16, !7}
!17 = distinct !{!17, !7}
!18 = distinct !{!18, !7}
