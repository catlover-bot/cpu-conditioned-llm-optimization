; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_2mm(i32 noundef %ni, i32 noundef %nj, i32 noundef %nk, i32 noundef %nl, double noundef %alpha, double noundef %beta, ptr noundef %tmp, ptr noundef %A, ptr noundef %B, ptr noundef %C, ptr noundef %D) #0 {
entry:
  %ni64 = sext i32 %ni to i64
  %nj64 = sext i32 %nj to i64
  %nk64 = sext i32 %nk to i64
  %nl64 = sext i32 %nl to i64

  %cmp_i0 = icmp sgt i32 %ni, 0
  br i1 %cmp_i0, label %outer1.preheader, label %for.end37

outer1.preheader:
  %cmp_j0 = icmp sgt i32 %nj, 0
  %cmp_k0 = icmp sgt i32 %nk, 0
  br label %outer1.head

outer1.head:
  %i1 = phi i64 [0, %outer1.preheader], [%i1.next, %outer1.latch]
  %tmp_row_off = mul nsw i64 %i1, %nj64
  %tmp_row_ptr = getelementptr inbounds double, ptr %tmp, i64 %tmp_row_off
  %A_row_off = mul nsw i64 %i1, %nk64
  %A_row_ptr = getelementptr inbounds double, ptr %A, i64 %A_row_off
  br i1 %cmp_j0, label %inner1.preheader, label %outer1.latch

inner1.preheader:
  br label %inner1.head

inner1.head:
  %j1 = phi i64 [0, %inner1.preheader], [%j1.next, %inner1.latch]
  %tmp_elem_ptr = getelementptr inbounds double, ptr %tmp_row_ptr, i64 %j1
  store double 0.000000e+00, ptr %tmp_elem_ptr, align 8
  br i1 %cmp_k0, label %kloop.preheader, label %inner1.latch

kloop.preheader:
  br label %kloop

kloop:
  %k1 = phi i64 [0, %kloop.preheader], [%k1.next, %kloop]
  %acc = phi double [0.000000e+00, %kloop.preheader], [%add31, %kloop]
  %A_elem_ptr = getelementptr inbounds double, ptr %A_row_ptr, i64 %k1
  %aval = load double, ptr %A_elem_ptr, align 8
  %mul = fmul double %alpha, %aval
  %B_row_off = mul nsw i64 %k1, %nj64
  %B_row_ptr = getelementptr inbounds double, ptr %B, i64 %B_row_off
  %B_elem_ptr = getelementptr inbounds double, ptr %B_row_ptr, i64 %j1
  %bval = load double, ptr %B_elem_ptr, align 8
  %mul26 = fmul double %mul, %bval
  %add31 = fadd double %acc, %mul26
  %k1.next = add nsw i64 %k1, 1
  %kcmp = icmp slt i64 %k1.next, %nk64
  br i1 %kcmp, label %kloop, label %kloop.exit

kloop.exit:
  store double %add31, ptr %tmp_elem_ptr, align 8
  br label %inner1.latch

inner1.latch:
  %j1.next = add nsw i64 %j1, 1
  %jcmp = icmp slt i64 %j1.next, %nj64
  br i1 %jcmp, label %inner1.head, label %outer1.latch

outer1.latch:
  %i1.next = add nsw i64 %i1, 1
  %icmp1 = icmp slt i64 %i1.next, %ni64
  br i1 %icmp1, label %outer1.head, label %for.end37

for.end37:
  %cmp_i2 = icmp sgt i32 %ni, 0
  br i1 %cmp_i2, label %outer2.preheader, label %for.end74

outer2.preheader:
  %cmp_l0 = icmp sgt i32 %nl, 0
  %cmp_j2_0 = icmp sgt i32 %nj, 0
  br label %outer2.head

outer2.head:
  %i2 = phi i64 [0, %outer2.preheader], [%i2.next, %outer2.latch]
  %D_row_off = mul nsw i64 %i2, %nl64
  %D_row_ptr = getelementptr inbounds double, ptr %D, i64 %D_row_off
  %tmp_row_off2 = mul nsw i64 %i2, %nj64
  %tmp_row_ptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmp_row_off2
  br i1 %cmp_l0, label %inner2.preheader, label %outer2.latch

inner2.preheader:
  br label %inner2.head

inner2.head:
  %j2 = phi i64 [0, %inner2.preheader], [%j2.next, %inner2.latch]
  %D_elem_ptr = getelementptr inbounds double, ptr %D_row_ptr, i64 %j2
  %dval = load double, ptr %D_elem_ptr, align 8
  %mul48 = fmul double %dval, %beta
  store double %mul48, ptr %D_elem_ptr, align 8
  br i1 %cmp_j2_0, label %kloop2.preheader, label %inner2.latch

kloop2.preheader:
  br label %kloop2

kloop2:
  %k2 = phi i64 [0, %kloop2.preheader], [%k2.next, %kloop2]
  %acc2 = phi double [%mul48, %kloop2.preheader], [%add65, %kloop2]
  %tmp_elem_ptr2 = getelementptr inbounds double, ptr %tmp_row_ptr2, i64 %k2
  %tval = load double, ptr %tmp_elem_ptr2, align 8
  %C_row_off = mul nsw i64 %k2, %nl64
  %C_row_ptr = getelementptr inbounds double, ptr %C, i64 %C_row_off
  %C_elem_ptr = getelementptr inbounds double, ptr %C_row_ptr, i64 %j2
  %cval = load double, ptr %C_elem_ptr, align 8
  %mul60 = fmul double %tval, %cval
  %add65 = fadd double %acc2, %mul60
  %k2.next = add nsw i64 %k2, 1
  %kcmp2 = icmp slt i64 %k2.next, %nj64
  br i1 %kcmp2, label %kloop2, label %kloop2.exit

kloop2.exit:
  store double %add65, ptr %D_elem_ptr, align 8
  br label %inner2.latch

inner2.latch:
  %j2.next = add nsw i64 %j2, 1
  %jcmp2 = icmp slt i64 %j2.next, %nl64
  br i1 %jcmp2, label %inner2.head, label %outer2.latch

outer2.latch:
  %i2.next = add nsw i64 %i2, 1
  %icmp2 = icmp slt i64 %i2.next, %ni64
  br i1 %icmp2, label %outer2.head, label %for.end74

for.end74:
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
