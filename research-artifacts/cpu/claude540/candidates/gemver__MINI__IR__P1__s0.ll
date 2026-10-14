; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gemver(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %u1, ptr noundef %v1, ptr noundef %u2, ptr noundef %v2, ptr noundef %w, ptr noundef %x, ptr noundef %y, ptr noundef %z) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %preheader, label %for.end95

preheader:
  %n64 = zext i32 %n to i64

  ; ---- Loop 1: A[i][j] += u1[i]*v1[j] + u2[i]*v2[j] ----
  br label %outer1.head

outer1.head:
  %i1 = phi i64 [ 0, %preheader ], [ %i1.next, %outer1.latch ]
  %u1i.ptr = getelementptr inbounds double, ptr %u1, i64 %i1
  %u1i = load double, ptr %u1i.ptr, align 8
  %u2i.ptr = getelementptr inbounds double, ptr %u2, i64 %i1
  %u2i = load double, ptr %u2i.ptr, align 8
  %Arow1 = mul nsw i64 %i1, %n64
  %Arowptr1 = getelementptr inbounds double, ptr %A, i64 %Arow1
  br label %inner1.body

inner1.body:
  %j1 = phi i64 [ 0, %outer1.head ], [ %j1.next, %inner1.body ]
  %Aij.ptr = getelementptr inbounds double, ptr %Arowptr1, i64 %j1
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
  %cmp.inner1 = icmp slt i64 %j1.next, %n64
  br i1 %cmp.inner1, label %inner1.body, label %outer1.latch

outer1.latch:
  %i1.next = add nuw nsw i64 %i1, 1
  %cmp.outer1 = icmp slt i64 %i1.next, %n64
  br i1 %cmp.outer1, label %outer1.head, label %for.end32

for.end32:
  br label %outer2.head

  ; ---- Loop 2: x[i] += beta*A[j][i]*y[j] ----
outer2.head:
  %i2 = phi i64 [ 0, %for.end32 ], [ %i2.next, %outer2.latch ]
  br label %inner2.body

inner2.body:
  %j2 = phi i64 [ 0, %outer2.head ], [ %j2.next, %inner2.body ]
  %xi.ptr2 = getelementptr inbounds double, ptr %x, i64 %i2
  %xi.load = load double, ptr %xi.ptr2, align 8
  %Arow2 = mul nsw i64 %j2, %n64
  %Arowptr2 = getelementptr inbounds double, ptr %A, i64 %Arow2
  %Aji.ptr = getelementptr inbounds double, ptr %Arowptr2, i64 %i2
  %Aji = load double, ptr %Aji.ptr, align 8
  %mul45 = fmul double %beta, %Aji
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.ptr, align 8
  %mul48 = fmul double %mul45, %yj
  %add49 = fadd double %xi.load, %mul48
  store double %add49, ptr %xi.ptr2, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %cmp.inner2 = icmp slt i64 %j2.next, %n64
  br i1 %cmp.inner2, label %inner2.body, label %outer2.latch

outer2.latch:
  %i2.next = add nuw nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %n64
  br i1 %cmp.outer2, label %outer2.head, label %for.end57

for.end57:
  br label %loop3.body

  ; ---- Loop 3: x[i] += z[i] ----
loop3.body:
  %i3 = phi i64 [ 0, %for.end57 ], [ %i3.next, %loop3.body ]
  %xi.ptr3 = getelementptr inbounds double, ptr %x, i64 %i3
  %xi3 = load double, ptr %xi.ptr3, align 8
  %zi.ptr = getelementptr inbounds double, ptr %z, i64 %i3
  %zi = load double, ptr %zi.ptr, align 8
  %add65 = fadd double %xi3, %zi
  store double %add65, ptr %xi.ptr3, align 8
  %i3.next = add nuw nsw i64 %i3, 1
  %cmp.loop3 = icmp slt i64 %i3.next, %n64
  br i1 %cmp.loop3, label %loop3.body, label %for.end70

for.end70:
  br label %outer4.head

  ; ---- Loop 4: w[i] += alpha*A[i][j]*x[j] ----
outer4.head:
  %i4 = phi i64 [ 0, %for.end70 ], [ %i4.next, %outer4.latch ]
  %Arow4 = mul nsw i64 %i4, %n64
  %Arowptr4 = getelementptr inbounds double, ptr %A, i64 %Arow4
  %wi.ptr = getelementptr inbounds double, ptr %w, i64 %i4
  %wi.init = load double, ptr %wi.ptr, align 8
  br label %inner4.body

inner4.body:
  %j4 = phi i64 [ 0, %outer4.head ], [ %j4.next, %inner4.body ]
  %wacc = phi double [ %wi.init, %outer4.head ], [ %add87, %inner4.body ]
  %Aij4.ptr = getelementptr inbounds double, ptr %Arowptr4, i64 %j4
  %Aij4 = load double, ptr %Aij4.ptr, align 8
  %mul83 = fmul double %alpha, %Aij4
  %xj.ptr = getelementptr inbounds double, ptr %x, i64 %j4
  %xj = load double, ptr %xj.ptr, align 8
  %mul86 = fmul double %mul83, %xj
  %add87 = fadd double %wacc, %mul86
  %j4.next = add nuw nsw i64 %j4, 1
  %cmp.inner4 = icmp slt i64 %j4.next, %n64
  br i1 %cmp.inner4, label %inner4.body, label %inner4.exit

inner4.exit:
  store double %add87, ptr %wi.ptr, align 8
  br label %outer4.latch

outer4.latch:
  %i4.next = add nuw nsw i64 %i4, 1
  %cmp.outer4 = icmp slt i64 %i4.next, %n64
  br i1 %cmp.outer4, label %outer4.head, label %for.end95

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
