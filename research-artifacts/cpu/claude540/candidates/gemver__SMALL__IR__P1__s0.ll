; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %loop3.check

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %outer.loop

outer.loop:                                       ; preds = %outer.preheader, %outer.latch
  %i = phi i64 [ 0, %outer.preheader ], [ %i.next, %outer.latch ]
  %Arow.base = mul nsw i64 %i, %n64
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.base
  %u1i.ptr = getelementptr inbounds double, ptr %u1, i64 %i
  %u1i = load double, ptr %u1i.ptr, align 8
  %u2i.ptr = getelementptr inbounds double, ptr %u2, i64 %i
  %u2i = load double, ptr %u2i.ptr, align 8
  br label %inner.loop

inner.loop:                                       ; preds = %outer.loop, %inner.loop
  %j = phi i64 [ 0, %outer.loop ], [ %j.next, %inner.loop ]
  %Aij.ptr = getelementptr inbounds double, ptr %Arow.ptr, i64 %j
  %Aij = load double, ptr %Aij.ptr, align 8
  %v1j.ptr = getelementptr inbounds double, ptr %v1, i64 %j
  %v1j = load double, ptr %v1j.ptr, align 8
  %mul1 = fmul double %u1i, %v1j
  %add1 = fadd double %Aij, %mul1
  %v2j.ptr = getelementptr inbounds double, ptr %v2, i64 %j
  %v2j = load double, ptr %v2j.ptr, align 8
  %mul2 = fmul double %u2i, %v2j
  %add2 = fadd double %add1, %mul2
  store double %add2, ptr %Aij.ptr, align 8
  %j.next = add nsw i64 %j, 1
  %inner.cmp = icmp slt i64 %j.next, %n64
  br i1 %inner.cmp, label %inner.loop, label %outer.latch

outer.latch:                                      ; preds = %inner.loop
  %i.next = add nsw i64 %i, 1
  %outer.cmp = icmp slt i64 %i.next, %n64
  br i1 %outer.cmp, label %outer.loop, label %loop2.check

loop2.check:                                      ; preds = %outer.latch
  br label %loop2.preheader

loop2.preheader:
  br i1 %cmp.n, label %loop2.outer, label %loop3.check

loop2.outer:                                      ; preds = %loop2.preheader, %loop2.latch
  %i2 = phi i64 [ 0, %loop2.preheader ], [ %i2.next, %loop2.latch ]
  %xi2.ptr = getelementptr inbounds double, ptr %x, i64 %i2
  %xi2.init = load double, ptr %xi2.ptr, align 8
  br label %loop2.inner

loop2.inner:                                      ; preds = %loop2.outer, %loop2.inner
  %j2 = phi i64 [ 0, %loop2.outer ], [ %j2.next, %loop2.inner ]
  %xacc = phi double [ %xi2.init, %loop2.outer ], [ %xnew, %loop2.inner ]
  %Ajrow.base = mul nsw i64 %j2, %n64
  %Aji.ptr = getelementptr inbounds double, ptr %A, i64 %Ajrow.base
  %Aji2.ptr = getelementptr inbounds double, ptr %Aji.ptr, i64 %i2
  %Aji2 = load double, ptr %Aji2.ptr, align 8
  %mulb = fmul double %beta, %Aji2
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.ptr, align 8
  %mulc = fmul double %mulb, %yj
  %xnew = fadd double %xacc, %mulc
  store double %xnew, ptr %xi2.ptr, align 8
  %j2.next = add nsw i64 %j2, 1
  %inner2.cmp = icmp slt i64 %j2.next, %n64
  br i1 %inner2.cmp, label %loop2.inner, label %loop2.latch

loop2.latch:                                      ; preds = %loop2.inner
  %i2.next = add nsw i64 %i2, 1
  %outer2.cmp = icmp slt i64 %i2.next, %n64
  br i1 %outer2.cmp, label %loop2.outer, label %loop3.check

loop3.check:                                      ; preds = %loop2.latch, %loop2.preheader, %entry
  br i1 %cmp.n, label %loop3.body.preheader, label %loop4.check

loop3.body.preheader:
  br label %loop3.body

loop3.body:                                       ; preds = %loop3.body.preheader, %loop3.body
  %i3 = phi i64 [ 0, %loop3.body.preheader ], [ %i3.next, %loop3.body ]
  %xi3.ptr = getelementptr inbounds double, ptr %x, i64 %i3
  %xi3 = load double, ptr %xi3.ptr, align 8
  %zi.ptr = getelementptr inbounds double, ptr %z, i64 %i3
  %zi = load double, ptr %zi.ptr, align 8
  %add3 = fadd double %xi3, %zi
  store double %add3, ptr %xi3.ptr, align 8
  %i3.next = add nsw i64 %i3, 1
  %cmp3 = icmp slt i64 %i3.next, %n64
  br i1 %cmp3, label %loop3.body, label %loop4.check

loop4.check:                                      ; preds = %loop3.body, %loop3.check, %entry
  %cmp.n.4 = icmp sgt i32 %n, 0
  br i1 %cmp.n.4, label %loop4.outer.preheader, label %end

loop4.outer.preheader:
  %n64.4 = sext i32 %n to i64
  br label %loop4.outer

loop4.outer:                                      ; preds = %loop4.outer.preheader, %loop4.latch
  %i4 = phi i64 [ 0, %loop4.outer.preheader ], [ %i4.next, %loop4.latch ]
  %wi4.ptr = getelementptr inbounds double, ptr %w, i64 %i4
  %wi4.init = load double, ptr %wi4.ptr, align 8
  %Arow4.base = mul nsw i64 %i4, %n64.4
  %Arow4.ptr = getelementptr inbounds double, ptr %A, i64 %Arow4.base
  br label %loop4.inner

loop4.inner:                                      ; preds = %loop4.outer, %loop4.inner
  %j4 = phi i64 [ 0, %loop4.outer ], [ %j4.next, %loop4.inner ]
  %wacc = phi double [ %wi4.init, %loop4.outer ], [ %wnew, %loop4.inner ]
  %Aij4.ptr = getelementptr inbounds double, ptr %Arow4.ptr, i64 %j4
  %Aij4 = load double, ptr %Aij4.ptr, align 8
  %mula = fmul double %alpha, %Aij4
  %xj4.ptr = getelementptr inbounds double, ptr %x, i64 %j4
  %xj4 = load double, ptr %xj4.ptr, align 8
  %mulx = fmul double %mula, %xj4
  %wnew = fadd double %wacc, %mulx
  %j4.next = add nsw i64 %j4, 1
  %inner4.cmp = icmp slt i64 %j4.next, %n64.4
  br i1 %inner4.cmp, label %loop4.inner, label %loop4.latch

loop4.latch:                                      ; preds = %loop4.inner
  store double %wnew, ptr %wi4.ptr, align 8
  %i4.next = add nsw i64 %i4, 1
  %outer4.cmp = icmp slt i64 %i4.next, %n64.4
  br i1 %outer4.cmp, label %loop4.outer, label %end

end:                                              ; preds = %loop4.latch, %loop4.check
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
