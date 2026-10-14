; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_correlation(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %corr, ptr noundef %mean, ptr noundef %stddev) #0 {
entry:
  %eps = alloca double, align 8
  store double 1.000000e-01, ptr %eps, align 8

  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  %mgt0 = icmp sgt i32 %m, 0
  %ngt0 = icmp sgt i32 %n, 0

  br label %loop1.outer.check

loop1.outer.check:
  br i1 %mgt0, label %loop1.outer, label %for.end20

loop1.outer:
  %j1 = phi i64 [ 0, %loop1.outer.check ], [ %j1.next, %loop1.inc ]
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ngt0, label %loop1.inner.preheader, label %loop1.store0

loop1.inner.preheader:
  br label %loop1.inner

loop1.inner:
  %i1 = phi i64 [ 0, %loop1.inner.preheader ], [ %i1.next, %loop1.inner ]
  %sum1 = phi double [ 0.000000e+00, %loop1.inner.preheader ], [ %sum1.next, %loop1.inner ]
  %row1off = mul nsw i64 %i1, %m64
  %rowidx1 = add nsw i64 %row1off, %j1
  %dptr1 = getelementptr inbounds double, ptr %data, i64 %rowidx1
  %dval1 = load double, ptr %dptr1, align 8
  %sum1.next = fadd double %sum1, %dval1
  %i1.next = add nsw i64 %i1, 1
  %cmp1i = icmp slt i64 %i1.next, %n64
  br i1 %cmp1i, label %loop1.inner, label %loop1.inner.exit

loop1.inner.exit:
  store double %sum1.next, ptr %mean.j1.ptr, align 8
  br label %loop1.div

loop1.store0:
  store double 0.000000e+00, ptr %mean.j1.ptr, align 8
  br label %loop1.div

loop1.div:
  %meanval1 = load double, ptr %mean.j1.ptr, align 8
  %meandiv1 = fdiv double %meanval1, %float_n
  store double %meandiv1, ptr %mean.j1.ptr, align 8
  br label %loop1.inc

loop1.inc:
  %j1.next = add nsw i64 %j1, 1
  %cmp1j = icmp slt i64 %j1.next, %m64
  br i1 %cmp1j, label %loop1.outer, label %for.end20

for.end20:
  br i1 %mgt0, label %loop2.outer, label %for.end64

loop2.outer:
  %j2 = phi i64 [ 0, %for.end20 ], [ %j2.next, %loop2.inc ]
  %stddev.j2.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.j2.ptr, align 8
  br i1 %ngt0, label %loop2.inner.preheader, label %loop2.store0

loop2.inner.preheader:
  br label %loop2.inner

loop2.inner:
  %i2 = phi i64 [ 0, %loop2.inner.preheader ], [ %i2.next, %loop2.inner ]
  %sum2 = phi double [ 0.000000e+00, %loop2.inner.preheader ], [ %sum2.next, %loop2.inner ]
  %row2off = mul nsw i64 %i2, %m64
  %rowidx2 = add nsw i64 %row2off, %j2
  %dptr2 = getelementptr inbounds double, ptr %data, i64 %rowidx2
  %dval2 = load double, ptr %dptr2, align 8
  %sub2 = fsub double %dval2, %meanval2
  %mul2 = fmul double %sub2, %sub2
  %sum2.next = fadd double %sum2, %mul2
  %i2.next = add nsw i64 %i2, 1
  %cmp2i = icmp slt i64 %i2.next, %n64
  br i1 %cmp2i, label %loop2.inner, label %loop2.inner.exit

loop2.inner.exit:
  store double %sum2.next, ptr %stddev.j2.ptr, align 8
  br label %loop2.div

loop2.store0:
  store double 0.000000e+00, ptr %stddev.j2.ptr, align 8
  br label %loop2.div

loop2.div:
  %sdval = load double, ptr %stddev.j2.ptr, align 8
  %sddiv = fdiv double %sdval, %float_n
  store double %sddiv, ptr %stddev.j2.ptr, align 8
  %sqrtres = call double @sqrt(double noundef %sddiv) #2
  store double %sqrtres, ptr %stddev.j2.ptr, align 8
  %cmp57 = fcmp ole double %sqrtres, 1.000000e-01
  %cond = select i1 %cmp57, double 1.000000e+00, double %sqrtres
  store double %cond, ptr %stddev.j2.ptr, align 8
  br label %loop2.inc

loop2.inc:
  %j2.next = add nsw i64 %j2, 1
  %cmp2j = icmp slt i64 %j2.next, %m64
  br i1 %cmp2j, label %loop2.outer, label %for.end64

for.end64:
  %sqrt_n = call double @sqrt(double noundef %float_n) #2
  br i1 %ngt0, label %loop3.outer, label %for.end92

loop3.outer:
  %i3 = phi i64 [ 0, %for.end64 ], [ %i3.next, %loop3.inc ]
  %row3off = mul nsw i64 %i3, %m64
  br i1 %mgt0, label %loop3.inner, label %loop3.inc

loop3.inner:
  %j3 = phi i64 [ 0, %loop3.outer ], [ %j3.next, %loop3.inner ]
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanval3 = load double, ptr %mean.j3.ptr, align 8
  %rowidx3 = add nsw i64 %row3off, %j3
  %dptr3 = getelementptr inbounds double, ptr %data, i64 %rowidx3
  %dval3 = load double, ptr %dptr3, align 8
  %sub3 = fsub double %dval3, %meanval3
  store double %sub3, ptr %dptr3, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3
  %sdval3 = load double, ptr %stddev.j3.ptr, align 8
  %mul81 = fmul double %sqrt_n, %sdval3
  %dval3b = load double, ptr %dptr3, align 8
  %divres = fdiv double %dval3b, %mul81
  store double %divres, ptr %dptr3, align 8
  %j3.next = add nsw i64 %j3, 1
  %cmp3j = icmp slt i64 %j3.next, %m64
  br i1 %cmp3j, label %loop3.inner, label %loop3.inc

loop3.inc:
  %i3.next = add nsw i64 %i3, 1
  %cmp3i = icmp slt i64 %i3.next, %n64
  br i1 %cmp3i, label %loop3.outer, label %for.end92

for.end92:
  %mminus1 = sub nsw i32 %m, 1
  %mminus1_64 = sext i32 %mminus1 to i64
  %cmp4outer = icmp slt i64 0, %mminus1_64
  br i1 %cmp4outer, label %loop4.outer, label %for.end142

loop4.outer:
  %i4 = phi i64 [ 0, %for.end92 ], [ %i4.next, %loop4.inc ]
  %row4off = mul nsw i64 %i4, %m64
  %corr.diag.idx = add nsw i64 %row4off, %i4
  %corr.diag.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.diag.idx
  store double 1.000000e+00, ptr %corr.diag.ptr, align 8
  %j4start = add nsw i64 %i4, 1
  %cmp4j.init = icmp slt i64 %j4start, %m64
  br i1 %cmp4j.init, label %loop4.inner, label %loop4.inc

loop4.inner:
  %j4 = phi i64 [ %j4start, %loop4.outer ], [ %j4.next, %loop4.k.exit ]
  %corr.ij.idx = add nsw i64 %row4off, %j4
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.ij.idx
  br i1 %ngt0, label %loop4.k.preheader, label %loop4.k.store0

loop4.k.preheader:
  br label %loop4.k

loop4.k:
  %k4 = phi i64 [ 0, %loop4.k.preheader ], [ %k4.next, %loop4.k ]
  %sumk = phi double [ 0.000000e+00, %loop4.k.preheader ], [ %sumk.next, %loop4.k ]
  %krow = mul nsw i64 %k4, %m64
  %kidx_i = add nsw i64 %krow, %i4
  %kptr_i = getelementptr inbounds double, ptr %data, i64 %kidx_i
  %kval_i = load double, ptr %kptr_i, align 8
  %kidx_j = add nsw i64 %krow, %j4
  %kptr_j = getelementptr inbounds double, ptr %data, i64 %kidx_j
  %kval_j = load double, ptr %kptr_j, align 8
  %mulk = fmul double %kval_i, %kval_j
  %sumk.next = fadd double %sumk, %mulk
  %k4.next = add nsw i64 %k4, 1
  %cmpk = icmp slt i64 %k4.next, %n64
  br i1 %cmpk, label %loop4.k, label %loop4.k.exit

loop4.k.exit:
  store double %sumk.next, ptr %corr.ij.ptr, align 8
  br label %loop4.copy

loop4.k.store0:
  store double 0.000000e+00, ptr %corr.ij.ptr, align 8
  br label %loop4.copy

loop4.copy:
  %corrval = load double, ptr %corr.ij.ptr, align 8
  %rowj4off = mul nsw i64 %j4, %m64
  %corr.ji.idx = add nsw i64 %rowj4off, %i4
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.ji.idx
  store double %corrval, ptr %corr.ji.ptr, align 8
  %j4.next = add nsw i64 %j4, 1
  %cmp4j = icmp slt i64 %j4.next, %m64
  br i1 %cmp4j, label %loop4.inner, label %loop4.k.exit2

loop4.k.exit2:
  br label %loop4.inc

loop4.inc:
  %i4.next = add nsw i64 %i4, 1
  %cmp4i = icmp slt i64 %i4.next, %mminus1_64
  br i1 %cmp4i, label %loop4.outer, label %for.end142

for.end142:
  %mminus1b = sub nsw i32 %m, 1
  %mminus1b64 = sext i32 %mminus1b to i64
  %diagoff = mul nsw i64 %mminus1b64, %m64
  %diagidx = add nsw i64 %diagoff, %mminus1b64
  %diagptr = getelementptr inbounds double, ptr %corr, i64 %diagidx
  store double 1.000000e+00, ptr %diagptr, align 8
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
