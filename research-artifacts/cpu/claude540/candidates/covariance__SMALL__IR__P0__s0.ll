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

loop1.outer:                                      ; j loop for mean init & accumulation & division
  %j1 = phi i32 [ 0, %entry ], [ %j1.inc, %loop1.latch ]
  %cmp1 = icmp slt i32 %j1, %m
  br i1 %cmp1, label %loop1.body, label %loop3.outer.pre

loop1.body:
  %j1.64 = sext i32 %j1 to i64
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1.64
  store double 0.000000e+00, ptr %mean.j1.ptr, align 8
  br i1 %cmp_n0, label %loop1.inner.preheader, label %loop1.div

loop1.inner.preheader:
  br label %loop1.inner

loop1.inner:
  %i1 = phi i32 [ 0, %loop1.inner.preheader ], [ %i1.inc, %loop1.inner ]
  %acc1 = phi double [ 0.000000e+00, %loop1.inner.preheader ], [ %add14, %loop1.inner ]
  %i1.64 = sext i32 %i1 to i64
  %rowoff1 = mul nsw i64 %i1.64, %m64
  %data.row1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %data.elt1 = getelementptr inbounds double, ptr %data.row1, i64 %j1.64
  %dval1 = load double, ptr %data.elt1, align 8
  %add14 = fadd double %acc1, %dval1
  %i1.inc = add nsw i32 %i1, 1
  %cmp1.inner = icmp slt i32 %i1.inc, %n
  br i1 %cmp1.inner, label %loop1.inner, label %loop1.inner.exit

loop1.inner.exit:
  store double %add14, ptr %mean.j1.ptr, align 8
  br label %loop1.div

loop1.div:
  %meanval = phi double [ 0.000000e+00, %loop1.body ], [ %add14, %loop1.inner.exit ]
  %div = fdiv double %meanval, %float_n
  store double %div, ptr %mean.j1.ptr, align 8
  br label %loop1.latch

loop1.latch:
  %j1.inc = add nsw i32 %j1, 1
  br label %loop1.outer

loop3.outer.pre:
  br label %loop2.outer

loop2.outer:                                      ; i loop: subtract mean from data
  %i2 = phi i32 [ 0, %loop3.outer.pre ], [ %i2.inc, %loop2.latch ]
  %cmp2 = icmp slt i32 %i2, %n
  br i1 %cmp2, label %loop2.body.preheader, label %loop3.entry

loop2.body.preheader:
  %i2.64 = sext i32 %i2 to i64
  %rowoff2 = mul nsw i64 %i2.64, %m64
  %data.row2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  br i1 %cmp_m0, label %loop2.inner, label %loop2.latch

loop2.inner:
  %j2 = phi i32 [ 0, %loop2.body.preheader ], [ %j2.inc, %loop2.inner ]
  %j2.64 = sext i32 %j2 to i64
  %mean.elt2 = getelementptr inbounds double, ptr %mean, i64 %j2.64
  %meanv2 = load double, ptr %mean.elt2, align 8
  %data.elt2 = getelementptr inbounds double, ptr %data.row2, i64 %j2.64
  %dval2 = load double, ptr %data.elt2, align 8
  %sub2 = fsub double %dval2, %meanv2
  store double %sub2, ptr %data.elt2, align 8
  %j2.inc = add nsw i32 %j2, 1
  %cmp2.inner = icmp slt i32 %j2.inc, %m
  br i1 %cmp2.inner, label %loop2.inner, label %loop2.latch

loop2.latch:
  %i2.inc = add nsw i32 %i2, 1
  br label %loop2.outer

loop3.entry:
  br label %loop3.outer

loop3.outer:                                      ; i loop for cov
  %i3 = phi i32 [ 0, %loop3.entry ], [ %i3.inc, %loop3.latch ]
  %cmp3 = icmp slt i32 %i3, %m
  br i1 %cmp3, label %loop3.body.preheader, label %exit

loop3.body.preheader:
  %i3.64 = sext i32 %i3 to i64
  %covrowoff3 = mul nsw i64 %i3.64, %m64
  %cov.row3 = getelementptr inbounds double, ptr %cov, i64 %covrowoff3
  br label %loop3.inner

loop3.inner:                                      ; j loop starting from i
  %j3 = phi i32 [ %i3, %loop3.body.preheader ], [ %j3.inc, %loop3.inner.latch ]
  %cmp3.inner = icmp slt i32 %j3, %m
  br i1 %cmp3.inner, label %loop3.inner.body, label %loop3.outer.latch

loop3.inner.body:
  %j3.64 = sext i32 %j3 to i64
  %cov.elt3 = getelementptr inbounds double, ptr %cov.row3, i64 %j3.64
  store double 0.000000e+00, ptr %cov.elt3, align 8
  br i1 %cmp_n0, label %loop3.kloop.preheader, label %loop3.kdone

loop3.kloop.preheader:
  br label %loop3.kloop

loop3.kloop:
  %k3 = phi i32 [ 0, %loop3.kloop.preheader ], [ %k3.inc, %loop3.kloop ]
  %acc3 = phi double [ 0.000000e+00, %loop3.kloop.preheader ], [ %add63, %loop3.kloop ]
  %k3.64 = sext i32 %k3 to i64
  %krowoff = mul nsw i64 %k3.64, %m64
  %data.krow = getelementptr inbounds double, ptr %data, i64 %krowoff
  %data.ki = getelementptr inbounds double, ptr %data.krow, i64 %i3.64
  %v_ki = load double, ptr %data.ki, align 8
  %data.kj = getelementptr inbounds double, ptr %data.krow, i64 %j3.64
  %v_kj = load double, ptr %data.kj, align 8
  %mul3 = fmul double %v_ki, %v_kj
  %add63 = fadd double %acc3, %mul3
  %k3.inc = add nsw i32 %k3, 1
  %cmp3.kloop = icmp slt i32 %k3.inc, %n
  br i1 %cmp3.kloop, label %loop3.kloop, label %loop3.kloop.exit

loop3.kloop.exit:
  store double %add63, ptr %cov.elt3, align 8
  br label %loop3.kdone

loop3.kdone:
  %covval = phi double [ 0.000000e+00, %loop3.inner.body ], [ %add63, %loop3.kloop.exit ]
  %sub67 = fsub double %float_n, 1.000000e+00
  %div72 = fdiv double %covval, %sub67
  store double %div72, ptr %cov.elt3, align 8
  %cov.sym.rowoff = mul nsw i64 %j3.64, %m64
  %cov.sym.row = getelementptr inbounds double, ptr %cov, i64 %cov.sym.rowoff
  %cov.sym.elt = getelementptr inbounds double, ptr %cov.sym.row, i64 %i3.64
  store double %div72, ptr %cov.sym.elt, align 8
  br label %loop3.inner.latch

loop3.inner.latch:
  %j3.inc = add nsw i32 %j3, 1
  br label %loop3.inner

loop3.outer.latch:
  br label %loop3.latch

loop3.latch:
  %i3.inc = add nsw i32 %i3, 1
  br label %loop3.outer

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
