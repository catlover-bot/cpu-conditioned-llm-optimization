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

  %cmp.i.pos = icmp sgt i32 %ni, 0
  %cmp.j.pos = icmp sgt i32 %nj, 0
  %cmp.k.pos = icmp sgt i32 %nk, 0
  %cmp.l.pos = icmp sgt i32 %nl, 0
  %cmp.m.pos = icmp sgt i32 %nm, 0

  br label %loop1.i.cond

loop1.i.cond:
  %i1 = phi i64 [ 0, %entry ], [ %i1.next, %loop1.i.inc ]
  %i1.cmp = icmp slt i64 %i1, %ni64
  br i1 %i1.cmp, label %loop1.j.preheader, label %loop2.i.cond.preheader

loop1.j.preheader:
  br label %loop1.j.cond

loop1.j.cond:
  %j1 = phi i64 [ 0, %loop1.j.preheader ], [ %j1.next, %loop1.j.inc ]
  %j1.cmp = icmp slt i64 %j1, %nj64
  br i1 %j1.cmp, label %loop1.j.body, label %loop1.j.end

loop1.j.body:
  %e1.row = mul nsw i64 %i1, %nj64
  %e1.idx = add nsw i64 %e1.row, %j1
  %e1.ptr = getelementptr inbounds double, ptr %E, i64 %e1.idx
  store double 0.000000e+00, ptr %e1.ptr, align 8
  br i1 %cmp.k.pos, label %loop1.k.preheader, label %loop1.j.inc

loop1.k.preheader:
  %a1.row = mul nsw i64 %i1, %nk64
  br label %loop1.k.body

loop1.k.body:
  %k1 = phi i64 [ 0, %loop1.k.preheader ], [ %k1.next, %loop1.k.body ]
  %acc1 = phi double [ 0.000000e+00, %loop1.k.preheader ], [ %add1, %loop1.k.body ]
  %a1.idx = add nsw i64 %a1.row, %k1
  %a1.ptr = getelementptr inbounds double, ptr %A, i64 %a1.idx
  %a1.val = load double, ptr %a1.ptr, align 8
  %b1.row = mul nsw i64 %k1, %nj64
  %b1.idx = add nsw i64 %b1.row, %j1
  %b1.ptr = getelementptr inbounds double, ptr %B, i64 %b1.idx
  %b1.val = load double, ptr %b1.ptr, align 8
  %mul1 = fmul double %a1.val, %b1.val
  %add1 = fadd double %acc1, %mul1
  %k1.next = add nsw i64 %k1, 1
  %k1.cmp = icmp slt i64 %k1.next, %nk64
  br i1 %k1.cmp, label %loop1.k.body, label %loop1.k.exit

loop1.k.exit:
  store double %add1, ptr %e1.ptr, align 8
  br label %loop1.j.inc

loop1.j.inc:
  %j1.next = add nsw i64 %j1, 1
  br label %loop1.j.cond

loop1.j.end:
  br label %loop1.i.inc

loop1.i.inc:
  %i1.next = add nsw i64 %i1, 1
  br label %loop1.i.cond

loop2.i.cond.preheader:
  br label %loop2.i.cond

loop2.i.cond:
  %i2 = phi i64 [ 0, %loop2.i.cond.preheader ], [ %i2.next, %loop2.i.inc ]
  %i2.cmp = icmp slt i64 %i2, %nj64
  br i1 %i2.cmp, label %loop2.j.preheader, label %loop3.i.cond.preheader

loop2.j.preheader:
  br label %loop2.j.cond

loop2.j.cond:
  %j2 = phi i64 [ 0, %loop2.j.preheader ], [ %j2.next, %loop2.j.inc ]
  %j2.cmp = icmp slt i64 %j2, %nl64
  br i1 %j2.cmp, label %loop2.j.body, label %loop2.j.end

loop2.j.body:
  %f2.row = mul nsw i64 %i2, %nl64
  %f2.idx = add nsw i64 %f2.row, %j2
  %f2.ptr = getelementptr inbounds double, ptr %F, i64 %f2.idx
  store double 0.000000e+00, ptr %f2.ptr, align 8
  br i1 %cmp.m.pos, label %loop2.k.preheader, label %loop2.j.inc

loop2.k.preheader:
  %c2.row = mul nsw i64 %i2, %nm64
  br label %loop2.k.body

loop2.k.body:
  %k2 = phi i64 [ 0, %loop2.k.preheader ], [ %k2.next, %loop2.k.body ]
  %acc2 = phi double [ 0.000000e+00, %loop2.k.preheader ], [ %add2, %loop2.k.body ]
  %c2.idx = add nsw i64 %c2.row, %k2
  %c2.ptr = getelementptr inbounds double, ptr %C, i64 %c2.idx
  %c2.val = load double, ptr %c2.ptr, align 8
  %d2.row = mul nsw i64 %k2, %nl64
  %d2.idx = add nsw i64 %d2.row, %j2
  %d2.ptr = getelementptr inbounds double, ptr %D, i64 %d2.idx
  %d2.val = load double, ptr %d2.ptr, align 8
  %mul2 = fmul double %c2.val, %d2.val
  %add2 = fadd double %acc2, %mul2
  %k2.next = add nsw i64 %k2, 1
  %k2.cmp = icmp slt i64 %k2.next, %nm64
  br i1 %k2.cmp, label %loop2.k.body, label %loop2.k.exit

loop2.k.exit:
  store double %add2, ptr %f2.ptr, align 8
  br label %loop2.j.inc

loop2.j.inc:
  %j2.next = add nsw i64 %j2, 1
  br label %loop2.j.cond

loop2.j.end:
  br label %loop2.i.inc

loop2.i.inc:
  %i2.next = add nsw i64 %i2, 1
  br label %loop2.i.cond

loop3.i.cond.preheader:
  br label %loop3.i.cond

loop3.i.cond:
  %i3 = phi i64 [ 0, %loop3.i.cond.preheader ], [ %i3.next, %loop3.i.inc ]
  %i3.cmp = icmp slt i64 %i3, %ni64
  br i1 %i3.cmp, label %loop3.j.preheader, label %exit

loop3.j.preheader:
  br label %loop3.j.cond

loop3.j.cond:
  %j3 = phi i64 [ 0, %loop3.j.preheader ], [ %j3.next, %loop3.j.inc ]
  %j3.cmp = icmp slt i64 %j3, %nl64
  br i1 %j3.cmp, label %loop3.j.body, label %loop3.j.end

loop3.j.body:
  %g3.row = mul nsw i64 %i3, %nl64
  %g3.idx = add nsw i64 %g3.row, %j3
  %g3.ptr = getelementptr inbounds double, ptr %G, i64 %g3.idx
  store double 0.000000e+00, ptr %g3.ptr, align 8
  br i1 %cmp.j.pos, label %loop3.k.preheader, label %loop3.j.inc

loop3.k.preheader:
  %e3.row = mul nsw i64 %i3, %nj64
  br label %loop3.k.body

loop3.k.body:
  %k3 = phi i64 [ 0, %loop3.k.preheader ], [ %k3.next, %loop3.k.body ]
  %acc3 = phi double [ 0.000000e+00, %loop3.k.preheader ], [ %add3, %loop3.k.body ]
  %e3.idx = add nsw i64 %e3.row, %k3
  %e3.ptr = getelementptr inbounds double, ptr %E, i64 %e3.idx
  %e3.val = load double, ptr %e3.ptr, align 8
  %f3.row = mul nsw i64 %k3, %nl64
  %f3.idx = add nsw i64 %f3.row, %j3
  %f3.ptr = getelementptr inbounds double, ptr %F, i64 %f3.idx
  %f3.val = load double, ptr %f3.ptr, align 8
  %mul3 = fmul double %e3.val, %f3.val
  %add3 = fadd double %acc3, %mul3
  %k3.next = add nsw i64 %k3, 1
  %k3.cmp = icmp slt i64 %k3.next, %nj64
  br i1 %k3.cmp, label %loop3.k.body, label %loop3.k.exit

loop3.k.exit:
  store double %add3, ptr %g3.ptr, align 8
  br label %loop3.j.inc

loop3.j.inc:
  %j3.next = add nsw i64 %j3, 1
  br label %loop3.j.cond

loop3.j.end:
  br label %loop3.i.inc

loop3.i.inc:
  %i3.next = add nsw i64 %i3, 1
  br label %loop3.i.cond

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
