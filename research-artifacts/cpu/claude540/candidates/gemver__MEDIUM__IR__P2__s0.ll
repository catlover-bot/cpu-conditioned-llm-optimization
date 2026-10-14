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

  ; ---------- Loop 1: A[i][j] += u1[i]*v1[j] + u2[i]*v2[j] ----------
  br label %loop1.i.header

loop1.i.header:
  %i1 = phi i64 [ 0, %preheader ], [ %i1.next, %loop1.i.latch ]
  %u1i.ptr = getelementptr inbounds double, ptr %u1, i64 %i1
  %u1i = load double, ptr %u1i.ptr, align 8
  %u2i.ptr = getelementptr inbounds double, ptr %u2, i64 %i1
  %u2i = load double, ptr %u2i.ptr, align 8
  %Arow.base = mul nsw i64 %i1, %n64
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.base
  br label %loop1.j

loop1.j:
  %j1 = phi i64 [ 0, %loop1.i.header ], [ %j1.next, %loop1.j ]
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
  %j1.cmp = icmp slt i64 %j1.next, %n64
  br i1 %j1.cmp, label %loop1.j, label %loop1.i.latch

loop1.i.latch:
  %i1.next = add nuw nsw i64 %i1, 1
  %i1.cmp = icmp slt i64 %i1.next, %n64
  br i1 %i1.cmp, label %loop1.i.header, label %loop2.i.header

  ; ---------- Loop 2: x[i] += beta * A[j][i] * y[j], summed over j ----------
loop2.i.header:
  %i2 = phi i64 [ 0, %loop1.i.latch ], [ %i2.next, %loop2.i.latch ]
  %xi.ptr = getelementptr inbounds double, ptr %x, i64 %i2
  br label %loop2.j

loop2.j:
  %j2 = phi i64 [ 0, %loop2.i.header ], [ %j2.next, %loop2.j ]
  %xi.cur = load double, ptr %xi.ptr, align 8
  %Ajrow.base = mul nsw i64 %j2, %n64
  %Aji.ptr = getelementptr inbounds double, ptr %A, i64 %Ajrow.base
  %Aji.ptr2 = getelementptr inbounds double, ptr %Aji.ptr, i64 %i2
  %Aji = load double, ptr %Aji.ptr2, align 8
  %mul45 = fmul double %beta, %Aji
  %yj.ptr = getelementptr inbounds double, ptr %y, i64 %j2
  %yj = load double, ptr %yj.ptr, align 8
  %mul48 = fmul double %mul45, %yj
  %add49 = fadd double %xi.cur, %mul48
  store double %add49, ptr %xi.ptr, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %n64
  br i1 %j2.cmp, label %loop2.j, label %loop2.i.latch

loop2.i.latch:
  %i2.next = add nuw nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.next, %n64
  br i1 %i2.cmp, label %loop2.i.header, label %loop3.header

  ; ---------- Loop 3: x[i] += z[i] ----------
loop3.header:
  %i3 = phi i64 [ 0, %loop2.i.latch ], [ %i3.next, %loop3.header ]
  %xi3.ptr = getelementptr inbounds double, ptr %x, i64 %i3
  %xi3 = load double, ptr %xi3.ptr, align 8
  %zi3.ptr = getelementptr inbounds double, ptr %z, i64 %i3
  %zi3 = load double, ptr %zi3.ptr, align 8
  %add65 = fadd double %xi3, %zi3
  store double %add65, ptr %xi3.ptr, align 8
  %i3.next = add nuw nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.next, %n64
  br i1 %i3.cmp, label %loop3.header, label %loop4.i.header

  ; ---------- Loop 4: w[i] += alpha * A[i][j] * x[j], summed over j ----------
loop4.i.header:
  %i4 = phi i64 [ 0, %loop3.header ], [ %i4.next, %loop4.i.latch ]
  %wi.ptr = getelementptr inbounds double, ptr %w, i64 %i4
  %Arow4.base = mul nsw i64 %i4, %n64
  %Arow4.ptr = getelementptr inbounds double, ptr %A, i64 %Arow4.base
  br label %loop4.j

loop4.j:
  %j4 = phi i64 [ 0, %loop4.i.header ], [ %j4.next, %loop4.j ]
  %wi.cur = load double, ptr %wi.ptr, align 8
  %Aij4.ptr = getelementptr inbounds double, ptr %Arow4.ptr, i64 %j4
  %Aij4 = load double, ptr %Aij4.ptr, align 8
  %mul83 = fmul double %alpha, %Aij4
  %xj4.ptr = getelementptr inbounds double, ptr %x, i64 %j4
  %xj4 = load double, ptr %xj4.ptr, align 8
  %mul86 = fmul double %mul83, %xj4
  %add87 = fadd double %wi.cur, %mul86
  store double %add87, ptr %wi.ptr, align 8
  %j4.next = add nuw nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.next, %n64
  br i1 %j4.cmp, label %loop4.j, label %loop4.i.latch

loop4.i.latch:
  %i4.next = add nuw nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.next, %n64
  br i1 %i4.cmp, label %loop4.i.header, label %for.end95

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
