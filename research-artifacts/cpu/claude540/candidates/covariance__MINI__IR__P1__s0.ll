; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp_m0 = icmp sgt i32 %m, 0
  %cmp_n0 = icmp sgt i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br label %loop1.outer

loop1.outer:                                      ; j loop for mean init/sum/div
  %j1 = phi i32 [ 0, %entry ], [ %j1.inc, %loop1.latch ]
  br i1 %cmp_n0, label %loop1.inner.preheader, label %loop1.latch

loop1.inner.preheader:
  %j1.64 = sext i32 %j1 to i64
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1.64
  store double 0.000000e+00, ptr %mean.j1.ptr, align 8
  br label %loop1.inner

loop1.inner:
  %i1 = phi i32 [ 0, %loop1.inner.preheader ], [ %i1.inc, %loop1.inner ]
  %acc1 = phi double [ 0.000000e+00, %loop1.inner.preheader ], [ %acc1.new, %loop1.inner ]
  %i1.64 = sext i32 %i1 to i64
  %row1.off = mul nsw i64 %i1.64, %m64
  %data.row1 = getelementptr inbounds double, ptr %data, i64 %row1.off
  %data.elem1 = getelementptr inbounds double, ptr %data.row1, i64 %j1.64
  %dval1 = load double, ptr %data.elem1, align 8
  %acc1.new = fadd double %acc1, %dval1
  %i1.inc = add nsw i32 %i1, 1
  %cmp1.inner = icmp slt i32 %i1.inc, %n
  br i1 %cmp1.inner, label %loop1.inner, label %loop1.inner.exit

loop1.inner.exit:
  store double %acc1.new, ptr %mean.j1.ptr, align 8
  %div1 = fdiv double %acc1.new, %float_n
  store double %div1, ptr %mean.j1.ptr, align 8
  br label %loop1.latch

loop1.latch:
  %j1.inc = add nsw i32 %j1, 1
  %cmp1.outer = icmp slt i32 %j1.inc, %m
  br i1 %cmp1.outer, label %loop1.outer, label %loop2.outer.preheader

loop2.outer.preheader:
  br label %loop2.outer

loop2.outer:                                      ; i loop for centering
  %i2 = phi i32 [ 0, %loop2.outer.preheader ], [ %i2.inc, %loop2.latch ]
  br i1 %cmp_m0, label %loop2.inner.preheader, label %loop2.latch

loop2.inner.preheader:
  %i2.64 = sext i32 %i2 to i64
  %row2.off = mul nsw i64 %i2.64, %m64
  %data.row2 = getelementptr inbounds double, ptr %data, i64 %row2.off
  br label %loop2.inner

loop2.inner:
  %j2 = phi i32 [ 0, %loop2.inner.preheader ], [ %j2.inc, %loop2.inner ]
  %j2.64 = sext i32 %j2 to i64
  %mean.elem2 = getelementptr inbounds double, ptr %mean, i64 %j2.64
  %meanval2 = load double, ptr %mean.elem2, align 8
  %data.elem2 = getelementptr inbounds double, ptr %data.row2, i64 %j2.64
  %dval2 = load double, ptr %data.elem2, align 8
  %sub2 = fsub double %dval2, %meanval2
  store double %sub2, ptr %data.elem2, align 8
  %j2.inc = add nsw i32 %j2, 1
  %cmp2.inner = icmp slt i32 %j2.inc, %m
  br i1 %cmp2.inner, label %loop2.inner, label %loop2.latch

loop2.latch:
  %i2.inc = add nsw i32 %i2, 1
  %cmp2.outer = icmp slt i32 %i2.inc, %n
  br i1 %cmp2.outer, label %loop2.outer, label %loop3.outer.preheader

loop3.outer.preheader:
  %fn.sub1 = fsub double %float_n, 1.000000e+00
  br label %loop3.outer

loop3.outer:                                      ; i loop for cov
  %i3 = phi i32 [ 0, %loop3.outer.preheader ], [ %i3.inc, %loop3.latch ]
  %i3.64 = sext i32 %i3 to i64
  %cov.row.i3.off = mul nsw i64 %i3.64, %m64
  %cov.row.i3 = getelementptr inbounds double, ptr %cov, i64 %cov.row.i3.off
  %data.row.i3 = getelementptr inbounds double, ptr %data, i64 %i3.64
  %cmp3.jcond = icmp slt i32 %i3, %m
  br i1 %cmp3.jcond, label %loop3.inner.preheader, label %loop3.latch

loop3.inner.preheader:
  br label %loop3.inner

loop3.inner:                                      ; j loop for cov
  %j3 = phi i32 [ %i3, %loop3.inner.preheader ], [ %j3.inc, %loop3.k.exit ]
  %j3.64 = sext i32 %j3 to i64
  %cov.elem.ij = getelementptr inbounds double, ptr %cov.row.i3, i64 %j3.64
  store double 0.000000e+00, ptr %cov.elem.ij, align 8
  br i1 %cmp_n0, label %loop3.k.preheader, label %loop3.k.exit

loop3.k.preheader:
  br label %loop3.k

loop3.k:                                          ; k loop
  %k3 = phi i32 [ 0, %loop3.k.preheader ], [ %k3.inc, %loop3.k ]
  %acc3 = phi double [ 0.000000e+00, %loop3.k.preheader ], [ %acc3.new, %loop3.k ]
  %k3.64 = sext i32 %k3 to i64
  %row3.off = mul nsw i64 %k3.64, %m64
  %data.row3 = getelementptr inbounds double, ptr %data, i64 %row3.off
  %data.elem.ki = getelementptr inbounds double, ptr %data.row3, i64 %i3.64
  %dval.ki = load double, ptr %data.elem.ki, align 8
  %data.elem.kj = getelementptr inbounds double, ptr %data.row3, i64 %j3.64
  %dval.kj = load double, ptr %data.elem.kj, align 8
  %mulk = fmul double %dval.ki, %dval.kj
  %acc3.new = fadd double %acc3, %mulk
  %k3.inc = add nsw i32 %k3, 1
  %cmp3.k = icmp slt i32 %k3.inc, %n
  br i1 %cmp3.k, label %loop3.k, label %loop3.k.exit.fromk

loop3.k.exit.fromk:
  store double %acc3.new, ptr %cov.elem.ij, align 8
  br label %loop3.k.exit

loop3.k.exit:
  %covval.ij = load double, ptr %cov.elem.ij, align 8
  %div3 = fdiv double %covval.ij, %fn.sub1
  store double %div3, ptr %cov.elem.ij, align 8
  %covval.ij2 = load double, ptr %cov.elem.ij, align 8
  %cov.row.j3.off = mul nsw i64 %j3.64, %m64
  %cov.row.j3 = getelementptr inbounds double, ptr %cov, i64 %cov.row.j3.off
  %cov.elem.ji = getelementptr inbounds double, ptr %cov.row.j3, i64 %i3.64
  store double %covval.ij2, ptr %cov.elem.ji, align 8
  %j3.inc = add nsw i32 %j3, 1
  %cmp3.jinner = icmp slt i32 %j3.inc, %m
  br i1 %cmp3.jinner, label %loop3.inner, label %loop3.latch

loop3.latch:
  %i3.inc = add nsw i32 %i3, 1
  %cmp3.outer = icmp slt i32 %i3.inc, %m
  br i1 %cmp3.outer, label %loop3.outer, label %exit

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
