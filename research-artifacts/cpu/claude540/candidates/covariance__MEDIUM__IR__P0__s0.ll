; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp_m_pos = icmp sgt i32 %m, 0
  %cmp_n_pos = icmp sgt i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br label %loop1.j.cond

loop1.j.cond:
  %j1 = phi i32 [ 0, %entry ], [ %j1.inc, %loop1.j.end ]
  %cmp1 = icmp slt i32 %j1, %m
  br i1 %cmp1, label %loop1.j.body, label %loop2.i.cond

loop1.j.body:
  %j1.64 = sext i32 %j1 to i64
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1.64
  store double 0.000000e+00, ptr %mean.j1.ptr, align 8
  br i1 %cmp_n_pos, label %loop1.i.body.preheader, label %loop1.i.end

loop1.i.body.preheader:
  br label %loop1.i.body

loop1.i.body:
  %i1 = phi i32 [ 0, %loop1.i.body.preheader ], [ %i1.inc, %loop1.i.body ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.body.preheader ], [ %sum1.new, %loop1.i.body ]
  %i1.64 = sext i32 %i1 to i64
  %row1.off = mul nsw i64 %i1.64, %m64
  %row1.base = getelementptr inbounds double, ptr %data, i64 %row1.off
  %elt1 = getelementptr inbounds double, ptr %row1.base, i64 %j1.64
  %val1 = load double, ptr %elt1, align 8
  %sum1.new = fadd double %sum1, %val1
  %i1.inc = add nsw i32 %i1, 1
  %cmp1i = icmp slt i32 %i1.inc, %n
  br i1 %cmp1i, label %loop1.i.body, label %loop1.i.end.from.body

loop1.i.end.from.body:
  br label %loop1.i.end

loop1.i.end:
  %sum1.final = phi double [ 0.000000e+00, %loop1.j.body ], [ %sum1.new, %loop1.i.end.from.body ]
  %div1 = fdiv double %sum1.final, %float_n
  store double %div1, ptr %mean.j1.ptr, align 8
  br label %loop1.j.end

loop1.j.end:
  %j1.inc = add nsw i32 %j1, 1
  br label %loop1.j.cond

loop2.i.cond:
  br i1 %cmp_n_pos, label %loop2.i.body.preheader, label %loop3.i.cond.preheader

loop2.i.body.preheader:
  br label %loop2.i.body

loop2.i.body:
  %i2 = phi i32 [ 0, %loop2.i.body.preheader ], [ %i2.inc, %loop2.i.end ]
  br i1 %cmp_m_pos, label %loop2.j.body.preheader, label %loop2.i.end

loop2.j.body.preheader:
  %i2.64 = sext i32 %i2 to i64
  %row2.off = mul nsw i64 %i2.64, %m64
  %row2.base = getelementptr inbounds double, ptr %data, i64 %row2.off
  br label %loop2.j.body

loop2.j.body:
  %j2 = phi i32 [ 0, %loop2.j.body.preheader ], [ %j2.inc, %loop2.j.body ]
  %j2.64 = sext i32 %j2 to i64
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2.64
  %mean.j2.val = load double, ptr %mean.j2.ptr, align 8
  %elt2 = getelementptr inbounds double, ptr %row2.base, i64 %j2.64
  %val2 = load double, ptr %elt2, align 8
  %sub2 = fsub double %val2, %mean.j2.val
  store double %sub2, ptr %elt2, align 8
  %j2.inc = add nsw i32 %j2, 1
  %cmp2j = icmp slt i32 %j2.inc, %m
  br i1 %cmp2j, label %loop2.j.body, label %loop2.i.end

loop2.i.end:
  %i2.inc = add nsw i32 %i2, 1
  %cmp2i = icmp slt i32 %i2.inc, %n
  br i1 %cmp2i, label %loop2.i.body, label %loop3.i.cond.preheader

loop3.i.cond.preheader:
  br label %loop3.i.cond

loop3.i.cond:
  %i3 = phi i32 [ 0, %loop3.i.cond.preheader ], [ %i3.inc, %loop3.i.end ]
  %cmp3 = icmp slt i32 %i3, %m
  br i1 %cmp3, label %loop3.j.cond.preheader, label %exit

loop3.j.cond.preheader:
  %i3.64 = sext i32 %i3 to i64
  %covrow3.off = mul nsw i64 %i3.64, %m64
  %covrow3.base = getelementptr inbounds double, ptr %cov, i64 %covrow3.off
  %datacol.i3 = %i3.64
  %sub67 = fsub double %float_n, 1.000000e+00
  br label %loop3.j.cond

loop3.j.cond:
  %j3 = phi i32 [ %i3, %loop3.j.cond.preheader ], [ %j3.inc, %loop3.k.end ]
  %cmp3j = icmp slt i32 %j3, %m
  br i1 %cmp3j, label %loop3.k.body.preheader, label %loop3.i.end.from.jend

loop3.k.body.preheader:
  %j3.64 = sext i32 %j3 to i64
  %cov.ij.ptr = getelementptr inbounds double, ptr %covrow3.base, i64 %j3.64
  br i1 %cmp_n_pos, label %loop3.k.body.entry, label %loop3.k.end.zero

loop3.k.body.entry:
  br label %loop3.k.body

loop3.k.body:
  %k3 = phi i32 [ 0, %loop3.k.body.entry ], [ %k3.inc, %loop3.k.body ]
  %sum3 = phi double [ 0.000000e+00, %loop3.k.body.entry ], [ %sum3.new, %loop3.k.body ]
  %k3.64 = sext i32 %k3 to i64
  %krow.off = mul nsw i64 %k3.64, %m64
  %krow.base = getelementptr inbounds double, ptr %data, i64 %krow.off
  %elt.ki = getelementptr inbounds double, ptr %krow.base, i64 %datacol.i3
  %val.ki = load double, ptr %elt.ki, align 8
  %elt.kj = getelementptr inbounds double, ptr %krow.base, i64 %j3.64
  %val.kj = load double, ptr %elt.kj, align 8
  %mul3 = fmul double %val.ki, %val.kj
  %sum3.new = fadd double %sum3, %mul3
  %k3.inc = add nsw i32 %k3, 1
  %cmp3k = icmp slt i32 %k3.inc, %n
  br i1 %cmp3k, label %loop3.k.body, label %loop3.k.end.from.body

loop3.k.end.from.body:
  br label %loop3.k.end

loop3.k.end.zero:
  br label %loop3.k.end

loop3.k.end:
  %sum3.final = phi double [ 0.000000e+00, %loop3.k.end.zero ], [ %sum3.new, %loop3.k.end.from.body ]
  %div3 = fdiv double %sum3.final, %sub67
  store double %div3, ptr %cov.ij.ptr, align 8
  %covji.off = mul nsw i64 %j3.64, %m64
  %covji.base = getelementptr inbounds double, ptr %cov, i64 %covji.off
  %cov.ji.ptr = getelementptr inbounds double, ptr %covji.base, i64 %i3.64
  store double %div3, ptr %cov.ji.ptr, align 8
  %j3.inc = add nsw i32 %j3, 1
  br label %loop3.j.cond

loop3.i.end.from.jend:
  br label %loop3.i.end

loop3.i.end:
  %i3.inc = add nsw i32 %i3, 1
  br label %loop3.i.cond

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
