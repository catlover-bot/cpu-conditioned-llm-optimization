; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp0 = icmp sgt i32 %n, 0
  br i1 %cmp0, label %preheader, label %for.end95

preheader:
  %n64 = sext i32 %n to i64

  br label %loop1.outer

loop1.outer:                                      ; preds = %loop1.outer.inc, %preheader
  %i1 = phi i64 [ 0, %preheader ], [ %i1.next, %loop1.outer.inc ]
  %Arow.base = mul nsw i64 %i1, %n64
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.base
  %u1i.ptr = getelementptr inbounds double, ptr %u1, i64 %i1
  %u1i = load double, ptr %u1i.ptr, align 8
  %u2i.ptr = getelementptr inbounds double, ptr %u2, i64 %i1
  %u2i = load double, ptr %u2i.ptr, align 8
  br label %loop1.inner

loop1.inner:                                       ; preds = %loop1.inner, %loop1.outer
  %j1 = phi i64 [ 0, %loop1.outer ], [ %j1.next, %loop1.inner ]
  %Aij.ptr = getelementptr inbounds double, ptr %Arow.ptr, i64 %j1
  %Aij = load double, ptr %Aij.ptr, align 8
  %v1j.ptr = getelementptr inbounds double, ptr %v1, i64 %j1
  %v1j = load double, ptr %v1j.ptr, align 8
  %mul1 = fmul double %u1i, %v1j
  %add1 = fadd double %Aij, %mul1
  %v2j.ptr = getelementptr inbounds double, ptr %v2, i64 %j1
  %v2j = load double, ptr %v2j.ptr, align 8
  %mul2 = fmul double %u2i, %v2j
  %add2 = fadd double %add1, %mul2
  store double %add2, ptr %Aij.ptr, align 8
  %j1.next = add nuw nsw i64 %j1, 1
  %cmp1i = icmp slt i64 %j1.next, %n64
  br i1 %cmp1i, label %loop1.inner, label %loop1.outer.inc

loop1.outer.inc:
  %i1.next = add nuw nsw i64 %i1, 1
  %cmp1o = icmp slt i64 %i1.next, %n64
  br i1 %cmp1o, label %loop1.outer, label %loop2.pre

loop2.pre:
  br label %loop2.outer

loop2.outer:                                       ; preds = %loop2.outer.inc, %loop2.pre
  %i2 = phi i64 [ 0, %loop2.pre ], [ %i2.next, %loop2.outer.inc ]
  %xi.ptr = getelementptr inbounds double, ptr %x, i64 %i2
  %xi0 = load double, ptr %xi.ptr, align 8
  br label %loop2.inner

loop2.inner:                                       ; preds = %loop2.inner, %loop2.outer
  %j2 = phi i64 [ 0, %loop2.outer ], [ %j2.next, %loop2.inner ]
  %xi.acc = phi double [ %xi0, %loop2.outer ], [ %xi.new, %loop2.inner ]
  %Aj.base = mul nsw i64 %j2, %n64
  %Aji.ptr0 = getelementptr inbounds double, ptr %A, i64 %Aj.base
  %Aji.ptr = getelementptr inbounds double, ptr %Aji.ptr0, i64 %i2
  %Aji = load double, ptr %Aji.ptr, align 8
  %mulb = fmul double %beta, %Aji
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.ptr, align 8
  %mulc = fmul double %mulb, %yj
  %xi.new = fadd double %xi.acc, %mulc
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp2i = icmp slt i64 %j2.next, %n64
  br i1 %cmp2i, label %loop2.inner, label %loop2.inner.exit

loop2.inner.exit:
  store double %xi.new, ptr %xi.ptr, align 8
  br label %loop2.outer.inc

loop2.outer.inc:
  %i2.next = add nuw nsw i64 %i2, 1
  %cmp2o = icmp slt i64 %i2.next, %n64
  br i1 %cmp2o, label %loop2.outer, label %loop3.pre

loop3.pre:
  br label %loop3

loop3:                                             ; preds = %loop3, %loop3.pre
  %i3 = phi i64 [ 0, %loop3.pre ], [ %i3.next, %loop3 ]
  %xi3.ptr = getelementptr inbounds double, ptr %x, i64 %i3
  %xi3 = load double, ptr %xi3.ptr, align 8
  %zi3.ptr = getelementptr inbounds double, ptr %z, i64 %i3
  %zi3 = load double, ptr %zi3.ptr, align 8
  %add3 = fadd double %xi3, %zi3
  store double %add3, ptr %xi3.ptr, align 8
  %i3.next = add nuw nsw i64 %i3, 1
  %cmp3 = icmp slt i64 %i3.next, %n64
  br i1 %cmp3, label %loop3, label %loop4.pre

loop4.pre:
  br label %loop4.outer

loop4.outer:                                       ; preds = %loop4.outer.inc, %loop4.pre
  %i4 = phi i64 [ 0, %loop4.pre ], [ %i4.next, %loop4.outer.inc ]
  %Arow4.base = mul nsw i64 %i4, %n64
  %Arow4.ptr = getelementptr inbounds double, ptr %A, i64 %Arow4.base
  %wi.ptr = getelementptr inbounds double, ptr %w, i64 %i4
  %wi0 = load double, ptr %wi.ptr, align 8
  br label %loop4.inner

loop4.inner:                                       ; preds = %loop4.inner, %loop4.outer
  %j4 = phi i64 [ 0, %loop4.outer ], [ %j4.next, %loop4.inner ]
  %wi.acc = phi double [ %wi0, %loop4.outer ], [ %wi.new, %loop4.inner ]
  %Aij4.ptr = getelementptr inbounds double, ptr %Arow4.ptr, i64 %j4
  %Aij4 = load double, ptr %Aij4.ptr, align 8
  %mula = fmul double %alpha, %Aij4
  %xj.ptr = getelementptr inbounds double, ptr %x, i64 %j4
  %xj = load double, ptr %xj.ptr, align 8
  %mulx = fmul double %mula, %xj
  %wi.new = fadd double %wi.acc, %mulx
  %j4.next = add nuw nsw i64 %j4, 1
  %cmp4i = icmp slt i64 %j4.next, %n64
  br i1 %cmp4i, label %loop4.inner, label %loop4.inner.exit

loop4.inner.exit:
  store double %wi.new, ptr %wi.ptr, align 8
  br label %loop4.outer.inc

loop4.outer.inc:
  %i4.next = add nuw nsw i64 %i4, 1
  %cmp4o = icmp slt i64 %i4.next, %n64
  br i1 %cmp4o, label %loop4.outer, label %for.end95

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
