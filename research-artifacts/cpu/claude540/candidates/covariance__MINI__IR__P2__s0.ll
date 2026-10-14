; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp.m0 = icmp sgt i32 %m, 0
  %cmp.n0 = icmp sgt i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br label %loop1.cond

loop1.cond:
  %j1 = phi i32 [ 0, %entry ], [ %j1.inc, %loop1.inc ]
  %cmp1 = icmp slt i32 %j1, %m
  br i1 %cmp1, label %loop1.body, label %loop3.preheader

loop1.body:
  %j1.64 = sext i32 %j1 to i64
  %mean.j1 = getelementptr inbounds double, ptr %mean, i64 %j1.64
  store double 0.000000e+00, ptr %mean.j1, align 8
  br i1 %cmp.n0, label %loop2.body.preheader, label %loop1.end

loop2.body.preheader:
  br label %loop2.body

loop2.body:
  %i2 = phi i32 [ 0, %loop2.body.preheader ], [ %i2.inc, %loop2.body ]
  %sum2 = phi double [ 0.000000e+00, %loop2.body.preheader ], [ %sum2.new, %loop2.body ]
  %i2.64 = sext i32 %i2 to i64
  %rowoff2 = mul nsw i64 %i2.64, %m64
  %dataidx2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  %dataelem2 = getelementptr inbounds double, ptr %dataidx2, i64 %j1.64
  %dval2 = load double, ptr %dataelem2, align 8
  %sum2.new = fadd double %sum2, %dval2
  %i2.inc = add nsw i32 %i2, 1
  %cmp2 = icmp slt i32 %i2.inc, %n
  br i1 %cmp2, label %loop2.body, label %loop2.end

loop2.end:
  store double %sum2.new, ptr %mean.j1, align 8
  br label %loop1.end

loop1.end:
  %mean.j1.val = load double, ptr %mean.j1, align 8
  %div1 = fdiv double %mean.j1.val, %float_n
  store double %div1, ptr %mean.j1, align 8
  br label %loop1.inc

loop1.inc:
  %j1.inc = add nsw i32 %j1, 1
  br label %loop1.cond

loop3.preheader:
  br i1 %cmp.n0, label %loop3.outer.preheader, label %loop5.preheader

loop3.outer.preheader:
  br label %loop3.outer

loop3.outer:
  %i3 = phi i32 [ 0, %loop3.outer.preheader ], [ %i3.inc, %loop3.outer.inc ]
  %i3.64 = sext i32 %i3 to i64
  %rowoff3 = mul nsw i64 %i3.64, %m64
  %datarow3 = getelementptr inbounds double, ptr %data, i64 %rowoff3
  br i1 %cmp.m0, label %loop3.inner.preheader, label %loop3.outer.inc

loop3.inner.preheader:
  br label %loop3.inner

loop3.inner:
  %j3 = phi i32 [ 0, %loop3.inner.preheader ], [ %j3.inc, %loop3.inner ]
  %j3.64 = sext i32 %j3 to i64
  %meanelem3 = getelementptr inbounds double, ptr %mean, i64 %j3.64
  %meanval3 = load double, ptr %meanelem3, align 8
  %dataelem3 = getelementptr inbounds double, ptr %datarow3, i64 %j3.64
  %dval3 = load double, ptr %dataelem3, align 8
  %sub3 = fsub double %dval3, %meanval3
  store double %sub3, ptr %dataelem3, align 8
  %j3.inc = add nsw i32 %j3, 1
  %cmp3.inner = icmp slt i32 %j3.inc, %m
  br i1 %cmp3.inner, label %loop3.inner, label %loop3.outer.inc

loop3.outer.inc:
  %i3.inc = add nsw i32 %i3, 1
  %cmp3.outer = icmp slt i32 %i3.inc, %n
  br i1 %cmp3.outer, label %loop3.outer, label %loop5.preheader

loop5.preheader:
  br label %loop5.cond

loop5.cond:
  %i5 = phi i32 [ 0, %loop5.preheader ], [ %i5.inc, %loop5.outer.inc ]
  %cmp5 = icmp slt i32 %i5, %m
  br i1 %cmp5, label %loop5.body, label %loop.end

loop5.body:
  %i5.64 = sext i32 %i5 to i64
  %rowoffI = mul nsw i64 %i5.64, %m64
  %covrowI = getelementptr inbounds double, ptr %cov, i64 %rowoffI
  br label %loop6.cond

loop6.cond:
  %j6 = phi i32 [ %i5, %loop5.body ], [ %j6.inc, %loop6.inc ]
  %cmp6 = icmp slt i32 %j6, %m
  br i1 %cmp6, label %loop6.body, label %loop5.outer.inc

loop6.body:
  %j6.64 = sext i32 %j6 to i64
  %covelem6 = getelementptr inbounds double, ptr %covrowI, i64 %j6.64
  store double 0.000000e+00, ptr %covelem6, align 8
  br i1 %cmp.n0, label %loop7.preheader, label %loop6.end

loop7.preheader:
  br label %loop7.body

loop7.body:
  %k7 = phi i32 [ 0, %loop7.preheader ], [ %k7.inc, %loop7.body ]
  %sum7 = phi double [ 0.000000e+00, %loop7.preheader ], [ %sum7.new, %loop7.body ]
  %k7.64 = sext i32 %k7 to i64
  %rowoff7 = mul nsw i64 %k7.64, %m64
  %datarow7 = getelementptr inbounds double, ptr %data, i64 %rowoff7
  %dataI7 = getelementptr inbounds double, ptr %datarow7, i64 %i5.64
  %dvalI7 = load double, ptr %dataI7, align 8
  %dataJ7 = getelementptr inbounds double, ptr %datarow7, i64 %j6.64
  %dvalJ7 = load double, ptr %dataJ7, align 8
  %mul7 = fmul double %dvalI7, %dvalJ7
  %sum7.new = fadd double %sum7, %mul7
  %k7.inc = add nsw i32 %k7, 1
  %cmp7 = icmp slt i32 %k7.inc, %n
  br i1 %cmp7, label %loop7.body, label %loop7.end

loop7.end:
  store double %sum7.new, ptr %covelem6, align 8
  br label %loop6.end

loop6.end:
  %covval6 = load double, ptr %covelem6, align 8
  %subfn = fsub double %float_n, 1.000000e+00
  %div6 = fdiv double %covval6, %subfn
  store double %div6, ptr %covelem6, align 8
  %covval6b = load double, ptr %covelem6, align 8
  %j6.64b = sext i32 %j6 to i64
  %rowoffJ = mul nsw i64 %j6.64b, %m64
  %covrowJ = getelementptr inbounds double, ptr %cov, i64 %rowoffJ
  %covelemJI = getelementptr inbounds double, ptr %covrowJ, i64 %i5.64
  store double %covval6b, ptr %covelemJI, align 8
  br label %loop6.inc

loop6.inc:
  %j6.inc = add nsw i32 %j6, 1
  br label %loop6.cond

loop5.outer.inc:
  %i5.inc = add nsw i32 %i5, 1
  br label %loop5.cond

loop.end:
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
