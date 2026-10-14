; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_correlation(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %corr, ptr noundef %mean, ptr noundef %stddev) #0 {
entry:
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  %eps = fadd double 0.000000e+00, 1.000000e-01

  %mcmp0 = icmp sgt i32 %m, 0
  br i1 %mcmp0, label %loop1.preheader, label %for.end20

loop1.preheader:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %loop1.j

loop1.j:
  %j1 = phi i64 [ 0, %loop1.preheader ], [ %j1.inc, %loop1.end ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ncmp0, label %loop1.i.preheader, label %loop1.storediv

loop1.i.preheader:
  br label %loop1.i

loop1.i:
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.inc, %loop1.i ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.preheader ], [ %sum1.new, %loop1.i ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %rowptr1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %dataptr1 = getelementptr inbounds double, ptr %rowptr1, i64 %j1
  %dval1 = load double, ptr %dataptr1, align 8
  %sum1.new = fadd double %sum1, %dval1
  %i1.inc = add nsw i64 %i1, 1
  %i1.cmp = icmp slt i64 %i1.inc, %n64
  br i1 %i1.cmp, label %loop1.i, label %loop1.i.exit

loop1.i.exit:
  br label %loop1.storediv

loop1.storediv:
  %sumphi = phi double [ 0.000000e+00, %loop1.j ], [ %sum1.new, %loop1.i.exit ]
  %divval = fdiv double %sumphi, %float_n
  store double %divval, ptr %mean.j.ptr, align 8
  br label %loop1.end

loop1.end:
  %j1.inc = add nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.inc, %m64
  br i1 %j1.cmp, label %loop1.j, label %for.end20

for.end20:
  %mcmp1 = icmp sgt i32 %m, 0
  br i1 %mcmp1, label %loop2.preheader, label %for.end64

loop2.preheader:
  %ncmp1 = icmp sgt i32 %n, 0
  br label %loop2.j

loop2.j:
  %j2 = phi i64 [ 0, %loop2.preheader ], [ %j2.inc, %loop2.end ]
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %stddev.j2.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %meanval2 = load double, ptr %mean.j2.ptr, align 8
  br i1 %ncmp1, label %loop2.i.preheader, label %loop2.storediv

loop2.i.preheader:
  br label %loop2.i

loop2.i:
  %i2 = phi i64 [ 0, %loop2.i.preheader ], [ %i2.inc, %loop2.i ]
  %sum2 = phi double [ 0.000000e+00, %loop2.i.preheader ], [ %sum2.new, %loop2.i ]
  %rowoff2 = mul nsw i64 %i2, %m64
  %rowptr2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  %dataptr2 = getelementptr inbounds double, ptr %rowptr2, i64 %j2
  %dval2 = load double, ptr %dataptr2, align 8
  %sub2 = fsub double %dval2, %meanval2
  %mul2 = fmul double %sub2, %sub2
  %sum2.new = fadd double %sum2, %mul2
  %i2.inc = add nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.inc, %n64
  br i1 %i2.cmp, label %loop2.i, label %loop2.i.exit

loop2.i.exit:
  br label %loop2.storediv

loop2.storediv:
  %sumphi2 = phi double [ 0.000000e+00, %loop2.j ], [ %sum2.new, %loop2.i.exit ]
  %divval2 = fdiv double %sumphi2, %float_n
  store double %divval2, ptr %stddev.j2.ptr, align 8
  %sqrtval = call double @sqrt(double noundef %divval2) #2
  store double %sqrtval, ptr %stddev.j2.ptr, align 8
  %cmpeps = fcmp ole double %sqrtval, %eps
  %condval = select i1 %cmpeps, double 1.000000e+00, double %sqrtval
  store double %condval, ptr %stddev.j2.ptr, align 8
  br label %loop2.end

loop2.end:
  %j2.inc = add nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.inc, %m64
  br i1 %j2.cmp, label %loop2.j, label %for.end64

for.end64:
  %ncmp2 = icmp sgt i32 %n, 0
  br i1 %ncmp2, label %loop3.i.preheader, label %for.end92

loop3.i.preheader:
  %sqrtfloatn = call double @sqrt(double noundef %float_n) #2
  %mcmp2 = icmp sgt i32 %m, 0
  br label %loop3.i

loop3.i:
  %i3 = phi i64 [ 0, %loop3.i.preheader ], [ %i3.inc, %loop3.i.end ]
  br i1 %mcmp2, label %loop3.j.preheader, label %loop3.i.end

loop3.j.preheader:
  br label %loop3.j

loop3.j:
  %j3 = phi i64 [ 0, %loop3.j.preheader ], [ %j3.inc, %loop3.j ]
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanval3 = load double, ptr %mean.j3.ptr, align 8
  %rowoff3 = mul nsw i64 %i3, %m64
  %rowptr3 = getelementptr inbounds double, ptr %data, i64 %rowoff3
  %dataptr3 = getelementptr inbounds double, ptr %rowptr3, i64 %j3
  %dval3 = load double, ptr %dataptr3, align 8
  %sub3 = fsub double %dval3, %meanval3
  store double %sub3, ptr %dataptr3, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stddevval3 = load double, ptr %stddev.j3.ptr, align 8
  %mul3 = fmul double %sqrtfloatn, %stddevval3
  %dval3b = load double, ptr %dataptr3, align 8
  %div3 = fdiv double %dval3b, %mul3
  store double %div3, ptr %dataptr3, align 8
  %j3.inc = add nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.inc, %m64
  br i1 %j3.cmp, label %loop3.j, label %loop3.i.end

loop3.i.end:
  %i3.inc = add nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.inc, %n64
  br i1 %i3.cmp, label %loop3.i, label %for.end92

for.end92:
  %mminus1 = sub nsw i32 %m, 1
  %mminus1.64 = sext i32 %mminus1 to i64
  %icmp4 = icmp slt i64 0, %mminus1.64
  br i1 %icmp4, label %loop4.i.preheader, label %for.end142

loop4.i.preheader:
  %ncmp3 = icmp sgt i32 %n, 0
  br label %loop4.i

loop4.i:
  %i4 = phi i64 [ 0, %loop4.i.preheader ], [ %i4.inc, %loop4.i.end ]
  %corr.diag.rowoff = mul nsw i64 %i4, %m64
  %corr.diag.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.diag.rowoff
  %corr.diag.ptr = getelementptr inbounds double, ptr %corr.diag.rowptr, i64 %i4
  store double 1.000000e+00, ptr %corr.diag.ptr, align 8
  %j4start = add nsw i64 %i4, 1
  %j4cmp0 = icmp slt i64 %j4start, %m64
  br i1 %j4cmp0, label %loop4.j.preheader, label %loop4.i.end

loop4.j.preheader:
  br label %loop4.j

loop4.j:
  %j4 = phi i64 [ %j4start, %loop4.j.preheader ], [ %j4.inc, %loop4.k.exit ]
  %corr.ij.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.diag.rowoff
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr.ij.rowptr, i64 %j4
  br i1 %ncmp3, label %loop4.k.preheader, label %loop4.k.store

loop4.k.preheader:
  br label %loop4.k

loop4.k:
  %k4 = phi i64 [ 0, %loop4.k.preheader ], [ %k4.inc, %loop4.k ]
  %sum4 = phi double [ 0.000000e+00, %loop4.k.preheader ], [ %sum4.new, %loop4.k ]
  %rowoff4a = mul nsw i64 %k4, %m64
  %rowptr4a = getelementptr inbounds double, ptr %data, i64 %rowoff4a
  %dataptr4a = getelementptr inbounds double, ptr %rowptr4a, i64 %i4
  %dval4a = load double, ptr %dataptr4a, align 8
  %dataptr4b = getelementptr inbounds double, ptr %rowptr4a, i64 %j4
  %dval4b = load double, ptr %dataptr4b, align 8
  %mul4 = fmul double %dval4a, %dval4b
  %sum4.new = fadd double %sum4, %mul4
  %k4.inc = add nsw i64 %k4, 1
  %k4.cmp = icmp slt i64 %k4.inc, %n64
  br i1 %k4.cmp, label %loop4.k, label %loop4.k.exit

loop4.k.exit:
  br label %loop4.k.store

loop4.k.store:
  %sumphi4 = phi double [ 0.000000e+00, %loop4.j ], [ %sum4.new, %loop4.k.exit ]
  store double %sumphi4, ptr %corr.ij.ptr, align 8
  %corr.ji.rowoff = mul nsw i64 %j4, %m64
  %corr.ji.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.ji.rowoff
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr.ji.rowptr, i64 %i4
  store double %sumphi4, ptr %corr.ji.ptr, align 8
  %j4.inc = add nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.inc, %m64
  br i1 %j4.cmp, label %loop4.j, label %loop4.i.end

loop4.i.end:
  %i4.inc = add nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.inc, %mminus1.64
  br i1 %i4.cmp, label %loop4.i, label %for.end142

for.end142:
  %mm1 = sub nsw i32 %m, 1
  %mm1.64 = sext i32 %mm1 to i64
  %corr.final.rowoff = mul nsw i64 %mm1.64, %m64
  %corr.final.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.final.rowoff
  %corr.final.ptr = getelementptr inbounds double, ptr %corr.final.rowptr, i64 %mm1.64
  store double 1.000000e+00, ptr %corr.final.ptr, align 8
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
