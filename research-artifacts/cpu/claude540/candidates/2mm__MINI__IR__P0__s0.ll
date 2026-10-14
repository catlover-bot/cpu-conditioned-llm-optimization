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

  %cmp.i0 = icmp sgt i32 %ni, 0
  br i1 %cmp.i0, label %outer1.ph, label %phase2.check

outer1.ph:
  %cmp.j0 = icmp sgt i32 %nj, 0
  %cmp.k0 = icmp sgt i32 %nk, 0
  br label %outer1.loop

outer1.loop:                                      ; i loop for tmp = alpha*A*B
  %i1 = phi i64 [ 0, %outer1.ph ], [ %i1.next, %outer1.latch ]
  %i1row_tmp = mul nsw i64 %i1, %nj64
  %i1row_A = mul nsw i64 %i1, %nk64
  br i1 %cmp.j0, label %inner1.ph, label %outer1.latch

inner1.ph:
  br label %inner1.loop

inner1.loop:                                      ; j loop
  %j1 = phi i64 [ 0, %inner1.ph ], [ %j1.next, %inner1.latch ]
  %tmpidx = add nsw i64 %i1row_tmp, %j1
  %tmpptr = getelementptr inbounds double, ptr %tmp, i64 %tmpidx
  store double 0.000000e+00, ptr %tmpptr, align 8
  br i1 %cmp.k0, label %innerk1.ph, label %inner1.latch

innerk1.ph:
  br label %innerk1.loop

innerk1.loop:                                     ; k loop
  %k1 = phi i64 [ 0, %innerk1.ph ], [ %k1.next, %innerk1.loop ]
  %aidx = add nsw i64 %i1row_A, %k1
  %aptr = getelementptr inbounds double, ptr %A, i64 %aidx
  %aval = load double, ptr %aptr, align 8
  %mulA = fmul double %alpha, %aval
  %bkrow = mul nsw i64 %k1, %nj64
  %bidx = add nsw i64 %bkrow, %j1
  %bptr = getelementptr inbounds double, ptr %B, i64 %bidx
  %bval = load double, ptr %bptr, align 8
  %mulAB = fmul double %mulA, %bval
  %tmpval = load double, ptr %tmpptr, align 8
  %addv = fadd double %tmpval, %mulAB
  store double %addv, ptr %tmpptr, align 8
  %k1.next = add nsw i64 %k1, 1
  %k1cmp = icmp slt i64 %k1.next, %nk64
  br i1 %k1cmp, label %innerk1.loop, label %inner1.latch

inner1.latch:
  %j1.next = add nsw i64 %j1, 1
  %j1cmp = icmp slt i64 %j1.next, %nj64
  br i1 %j1cmp, label %inner1.loop, label %outer1.latch

outer1.latch:
  %i1.next = add nsw i64 %i1, 1
  %i1cmp = icmp slt i64 %i1.next, %ni64
  br i1 %i1cmp, label %outer1.loop, label %phase2.check

phase2.check:
  %cmp.i0b = icmp sgt i32 %ni, 0
  br i1 %cmp.i0b, label %outer2.ph, label %end

outer2.ph:
  %cmp.l0 = icmp sgt i32 %nl, 0
  %cmp.j0b = icmp sgt i32 %nj, 0
  br label %outer2.loop

outer2.loop:                                      ; i loop for D = D*beta + tmp*C
  %i2 = phi i64 [ 0, %outer2.ph ], [ %i2.next, %outer2.latch ]
  %i2row_D = mul nsw i64 %i2, %nl64
  %i2row_tmp = mul nsw i64 %i2, %nj64
  br i1 %cmp.l0, label %inner2.ph, label %outer2.latch

inner2.ph:
  br label %inner2.loop

inner2.loop:                                      ; l/j loop (variable named j in original -> nl bound)
  %j2 = phi i64 [ 0, %inner2.ph ], [ %j2.next, %inner2.latch ]
  %didx = add nsw i64 %i2row_D, %j2
  %dptr = getelementptr inbounds double, ptr %D, i64 %didx
  %dval = load double, ptr %dptr, align 8
  %mulD = fmul double %dval, %beta
  store double %mulD, ptr %dptr, align 8
  br i1 %cmp.j0b, label %innerk2.ph, label %inner2.latch

innerk2.ph:
  br label %innerk2.loop

innerk2.loop:                                     ; k loop bound nj
  %k2 = phi i64 [ 0, %innerk2.ph ], [ %k2.next, %innerk2.loop ]
  %tmpidx2 = add nsw i64 %i2row_tmp, %k2
  %tmpptr2 = getelementptr inbounds double, ptr %tmp, i64 %tmpidx2
  %tmpval2 = load double, ptr %tmpptr2, align 8
  %ckrow = mul nsw i64 %k2, %nl64
  %cidx = add nsw i64 %ckrow, %j2
  %cptr = getelementptr inbounds double, ptr %C, i64 %cidx
  %cval = load double, ptr %cptr, align 8
  %mulTC = fmul double %tmpval2, %cval
  %dval2 = load double, ptr %dptr, align 8
  %addv2 = fadd double %dval2, %mulTC
  store double %addv2, ptr %dptr, align 8
  %k2.next = add nsw i64 %k2, 1
  %k2cmp = icmp slt i64 %k2.next, %nj64
  br i1 %k2cmp, label %innerk2.loop, label %inner2.latch

inner2.latch:
  %j2.next = add nsw i64 %j2, 1
  %j2cmp = icmp slt i64 %j2.next, %nl64
  br i1 %j2cmp, label %inner2.loop, label %outer2.latch

outer2.latch:
  %i2.next = add nsw i64 %i2, 1
  %i2cmp = icmp slt i64 %i2.next, %ni64
  br i1 %i2cmp, label %outer2.loop, label %end

end:
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
