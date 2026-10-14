; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_3mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, i32 noundef %nm, ptr noundef %E, ptr noundef %A, ptr noundef %B, ptr noundef %F, ptr noundef %C, ptr noundef %D, ptr noundef %G) #0 {
entry:
  %add = add nsw i32 %ni, 0
  %0 = zext i32 %add to i64
  %add1 = add nsw i32 %nj, 0
  %1 = zext i32 %add1 to i64
  %add3 = add nsw i32 %nk, 0
  %2 = zext i32 %add3 to i64
  %add5 = add nsw i32 %nj, 0
  %3 = zext i32 %add5 to i64
  %add7 = add nsw i32 %nl, 0
  %4 = zext i32 %add7 to i64
  %add9 = add nsw i32 %nm, 0
  %5 = zext i32 %add9 to i64
  %add11 = add nsw i32 %nl, 0
  %6 = zext i32 %add11 to i64

  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64
  %nm64 = sext i32 %nm to i64

  ; ---------- Loop nest 1: E = A*B ----------
  %cmp.i.pre = icmp sgt i32 %ni, 0
  br i1 %cmp.i.pre, label %outer1.preheader, label %for.end40

outer1.preheader:
  %cmp.j.pre = icmp sgt i32 %nj, 0
  %cmp.k.pre = icmp sgt i32 %nk, 0
  br label %outer1.body

outer1.body:
  %i1 = phi i64 [0, %outer1.preheader], [%i1.next, %outer1.latch]
  br i1 %cmp.j.pre, label %inner1j.body, label %outer1.latch

inner1j.body:
  %j1 = phi i64 [0, %outer1.body], [%j1.next, %inner1j.latch]
  %Erow = mul nsw i64 %i1, %1
  %Eoff = add nsw i64 %Erow, %j1
  %Eptr = getelementptr inbounds double, ptr %E, i64 %Eoff
  store double 0.000000e+00, ptr %Eptr, align 8
  br i1 %cmp.k.pre, label %inner1k.body, label %inner1j.latch

inner1k.body:
  %k1 = phi i64 [0, %inner1j.body], [%k1.next, %inner1k.body]
  %Arow = mul nsw i64 %i1, %2
  %Aoff = add nsw i64 %Arow, %k1
  %Aptr = getelementptr inbounds double, ptr %A, i64 %Aoff
  %aval = load double, ptr %Aptr, align 8
  %Brow = mul nsw i64 %k1, %3
  %Boff = add nsw i64 %Brow, %j1
  %Bptr = getelementptr inbounds double, ptr %B, i64 %Boff
  %bval = load double, ptr %Bptr, align 8
  %mulv = fmul double %aval, %bval
  %eval = load double, ptr %Eptr, align 8
  %addv = fadd double %eval, %mulv
  store double %addv, ptr %Eptr, align 8
  %k1.next = add nsw i64 %k1, 1
  %kcmp = icmp slt i64 %k1.next, %nk64
  br i1 %kcmp, label %inner1k.body, label %inner1j.latch

inner1j.latch:
  %j1.next = add nsw i64 %j1, 1
  %jcmp = icmp slt i64 %j1.next, %nj64
  br i1 %jcmp, label %inner1j.body, label %outer1.latch

outer1.latch:
  %i1.next = add nsw i64 %i1, 1
  %icmp = icmp slt i64 %i1.next, %ni64
  br i1 %icmp, label %outer1.body, label %for.end40

for.end40:
  ; ---------- Loop nest 2: F = C*D ----------
  %cmp2.i.pre = icmp sgt i32 %nj, 0
  br i1 %cmp2.i.pre, label %outer2.preheader, label %for.end76

outer2.preheader:
  %cmp2.j.pre = icmp sgt i32 %nl, 0
  %cmp2.k.pre = icmp sgt i32 %nm, 0
  br label %outer2.body

outer2.body:
  %i2 = phi i64 [0, %outer2.preheader], [%i2.next, %outer2.latch]
  br i1 %cmp2.j.pre, label %inner2j.body, label %outer2.latch

inner2j.body:
  %j2 = phi i64 [0, %outer2.body], [%j2.next, %inner2j.latch]
  %Frow = mul nsw i64 %i2, %4
  %Foff = add nsw i64 %Frow, %j2
  %Fptr = getelementptr inbounds double, ptr %F, i64 %Foff
  store double 0.000000e+00, ptr %Fptr, align 8
  br i1 %cmp2.k.pre, label %inner2k.body, label %inner2j.latch

inner2k.body:
  %k2 = phi i64 [0, %inner2j.body], [%k2.next, %inner2k.body]
  %Crow = mul nsw i64 %i2, %5
  %Coff = add nsw i64 %Crow, %k2
  %Cptr = getelementptr inbounds double, ptr %C, i64 %Coff
  %cval = load double, ptr %Cptr, align 8
  %Drow = mul nsw i64 %k2, %6
  %Doff = add nsw i64 %Drow, %j2
  %Dptr = getelementptr inbounds double, ptr %D, i64 %Doff
  %dval = load double, ptr %Dptr, align 8
  %mulv2 = fmul double %cval, %dval
  %fval = load double, ptr %Fptr, align 8
  %addv2 = fadd double %fval, %mulv2
  store double %addv2, ptr %Fptr, align 8
  %k2.next = add nsw i64 %k2, 1
  %kcmp2 = icmp slt i64 %k2.next, %nm64
  br i1 %kcmp2, label %inner2k.body, label %inner2j.latch

inner2j.latch:
  %j2.next = add nsw i64 %j2, 1
  %jcmp2 = icmp slt i64 %j2.next, %nl64
  br i1 %jcmp2, label %inner2j.body, label %outer2.latch

outer2.latch:
  %i2.next = add nsw i64 %i2, 1
  %icmp2 = icmp slt i64 %i2.next, %nj64
  br i1 %icmp2, label %outer2.body, label %for.end76

for.end76:
  ; ---------- Loop nest 3: G = E*F ----------
  %cmp3.i.pre = icmp sgt i32 %ni, 0
  br i1 %cmp3.i.pre, label %outer3.preheader, label %for.end112

outer3.preheader:
  %cmp3.j.pre = icmp sgt i32 %nl, 0
  %cmp3.k.pre = icmp sgt i32 %nj, 0
  br label %outer3.body

outer3.body:
  %i3 = phi i64 [0, %outer3.preheader], [%i3.next, %outer3.latch]
  br i1 %cmp3.j.pre, label %inner3j.body, label %outer3.latch

inner3j.body:
  %j3 = phi i64 [0, %outer3.body], [%j3.next, %inner3j.latch]
  %Grow = mul nsw i64 %i3, %6
  %Goff = add nsw i64 %Grow, %j3
  %Gptr = getelementptr inbounds double, ptr %G, i64 %Goff
  store double 0.000000e+00, ptr %Gptr, align 8
  br i1 %cmp3.k.pre, label %inner3k.body, label %inner3j.latch

inner3k.body:
  %k3 = phi i64 [0, %inner3j.body], [%k3.next, %inner3k.body]
  %Erow2 = mul nsw i64 %i3, %1
  %Eoff2 = add nsw i64 %Erow2, %k3
  %Eptr2 = getelementptr inbounds double, ptr %E, i64 %Eoff2
  %eval2 = load double, ptr %Eptr2, align 8
  %Frow2 = mul nsw i64 %k3, %4
  %Foff2 = add nsw i64 %Frow2, %j3
  %Fptr2 = getelementptr inbounds double, ptr %F, i64 %Foff2
  %fval2 = load double, ptr %Fptr2, align 8
  %mulv3 = fmul double %eval2, %fval2
  %gval = load double, ptr %Gptr, align 8
  %addv3 = fadd double %gval, %mulv3
  store double %addv3, ptr %Gptr, align 8
  %k3.next = add nsw i64 %k3, 1
  %kcmp3 = icmp slt i64 %k3.next, %nj64
  br i1 %kcmp3, label %inner3k.body, label %inner3j.latch

inner3j.latch:
  %j3.next = add nsw i64 %j3, 1
  %jcmp3 = icmp slt i64 %j3.next, %nl64
  br i1 %jcmp3, label %inner3j.body, label %outer3.latch

outer3.latch:
  %i3.next = add nsw i64 %i3, 1
  %icmp3 = icmp slt i64 %i3.next, %ni64
  br i1 %icmp3, label %outer3.body, label %for.end112

for.end112:
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
