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
  br i1 %mcmp0, label %loop1.preheader, label %loop1.end

loop1.preheader:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %loop1.j

loop1.j:
  %j1 = phi i64 [ 0, %loop1.preheader ], [ %j1.inc, %loop1.j.inc ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ncmp0, label %loop1.i.preheader, label %loop1.i.end

loop1.i.preheader:
  br label %loop1.i

loop1.i:
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.inc, %loop1.i ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.preheader ], [ %sum1.new, %loop1.i ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %rowptr1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %elptr1 = getelementptr inbounds double, ptr %rowptr1, i64 %j1
  %el1 = load double, ptr %elptr1, align 8
  %sum1.new = fadd double %sum1, %el1
  %i1.inc = add nsw i64 %i1, 1
  %i1done = icmp eq i64 %i1.inc, %n64
  br i1 %i1done, label %loop1.i.exit, label %loop1.i

loop1.i.exit:
  br label %loop1.i.end

loop1.i.end:
  %sumphi = phi double [ 0.000000e+00, %loop1.j ], [ %sum1.new, %loop1.i.exit ]
  %meandiv = fdiv double %sumphi, %float_n
  store double %meandiv, ptr %mean.j.ptr, align 8
  br label %loop1.j.inc

loop1.j.inc:
  %j1.inc = add nsw i64 %j1, 1
  %j1done = icmp eq i64 %j1.inc, %m64
  br i1 %j1done, label %loop1.exit, label %loop1.j

loop1.exit:
  br label %loop1.end

loop1.end:
  br label %loop2.j

loop2.j:
  %j2 = phi i64 [ 0, %loop1.end ], [ %j2.inc, %loop2.j.inc ]
  %stddev.j.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.j2.ptr, align 8
  %ncmp2 = icmp sgt i32 %n, 0
  br i1 %ncmp2, label %loop2.i.preheader, label %loop2.i.end

loop2.i.preheader:
  br label %loop2.i

loop2.i:
  %i2 = phi i64 [ 0, %loop2.i.preheader ], [ %i2.inc, %loop2.i ]
  %sum2 = phi double [ 0.000000e+00, %loop2.i.preheader ], [ %sum2.new, %loop2.i ]
  %rowoff2 = mul nsw i64 %i2, %m64
  %rowptr2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  %elptr2 = getelementptr inbounds double, ptr %rowptr2, i64 %j2
  %el2 = load double, ptr %elptr2, align 8
  %sub2 = fsub double %el2, %meanval2
  %mul2 = fmul double %sub2, %sub2
  %sum2.new = fadd double %sum2, %mul2
  %i2.inc = add nsw i64 %i2, 1
  %i2done = icmp eq i64 %i2.inc, %n64
  br i1 %i2done, label %loop2.i.exit, label %loop2.i

loop2.i.exit:
  br label %loop2.i.end

loop2.i.end:
  %sum2phi = phi double [ 0.000000e+00, %loop2.j ], [ %sum2.new, %loop2.i.exit ]
  %stddivval = fdiv double %sum2phi, %float_n
  store double %stddivval, ptr %stddev.j.ptr, align 8
  %sqrtcall = call double @sqrt(double noundef %stddivval) #2
  store double %sqrtcall, ptr %stddev.j.ptr, align 8
  %cmpeps = fcmp ole double %sqrtcall, %eps
  br i1 %cmpeps, label %loop2.cond.true, label %loop2.cond.false

loop2.cond.true:
  br label %loop2.cond.end

loop2.cond.false:
  br label %loop2.cond.end

loop2.cond.end:
  %condval = phi double [ 1.000000e+00, %loop2.cond.true ], [ %sqrtcall, %loop2.cond.false ]
  store double %condval, ptr %stddev.j.ptr, align 8
  br label %loop2.j.inc

loop2.j.inc:
  %j2.inc = add nsw i64 %j2, 1
  %j2done = icmp eq i64 %j2.inc, %m64
  br i1 %j2done, label %loop2.exit, label %loop2.j

loop2.exit:
  br label %loop3.i

loop3.i:
  %i3 = phi i64 [ 0, %loop2.exit ], [ %i3.inc, %loop3.i.inc ]
  %i3cont = icmp slt i64 %i3, %n64
  br i1 %i3cont, label %loop3.body, label %loop3.end

loop3.body:
  %sqrtfn = call double @sqrt(double noundef %float_n) #2
  br label %loop3.j

loop3.j:
  %j3 = phi i64 [ 0, %loop3.body ], [ %j3.inc, %loop3.j.inc ]
  %j3cont = icmp slt i64 %j3, %m64
  br i1 %j3cont, label %loop3.jbody, label %loop3.jend

loop3.jbody:
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanval3 = load double, ptr %mean.j3.ptr, align 8
  %rowoff3 = mul nsw i64 %i3, %m64
  %rowptr3 = getelementptr inbounds double, ptr %data, i64 %rowoff3
  %elptr3 = getelementptr inbounds double, ptr %rowptr3, i64 %j3
  %el3 = load double, ptr %elptr3, align 8
  %sub3 = fsub double %el3, %meanval3
  store double %sub3, ptr %elptr3, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stddevval3 = load double, ptr %stddev.j3.ptr, align 8
  %mul3 = fmul double %sqrtfn, %stddevval3
  %el3b = load double, ptr %elptr3, align 8
  %divval3 = fdiv double %el3b, %mul3
  store double %divval3, ptr %elptr3, align 8
  br label %loop3.j.inc

loop3.j.inc:
  %j3.inc = add nsw i64 %j3, 1
  br label %loop3.j

loop3.jend:
  br label %loop3.i.inc

loop3.i.inc:
  %i3.inc = add nsw i64 %i3, 1
  br label %loop3.i

loop3.end:
  br label %loop4.i

loop4.i:
  %i4 = phi i64 [ 0, %loop3.end ], [ %i4.inc, %loop4.i.inc ]
  %m4sub1 = sub nsw i32 %m, 1
  %m4sub1.64 = sext i32 %m4sub1 to i64
  %i4cont = icmp slt i64 %i4, %m4sub1.64
  br i1 %i4cont, label %loop4.body, label %loop4.end

loop4.body:
  %corr.diag.rowoff = mul nsw i64 %i4, %m64
  %corr.diag.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.diag.rowoff
  %corr.diag.ptr = getelementptr inbounds double, ptr %corr.diag.rowptr, i64 %i4
  store double 1.000000e+00, ptr %corr.diag.ptr, align 8
  %j4start = add nsw i64 %i4, 1
  br label %loop4.j

loop4.j:
  %j4 = phi i64 [ %j4start, %loop4.body ], [ %j4.inc, %loop4.j.inc ]
  %j4cont = icmp slt i64 %j4, %m64
  br i1 %j4cont, label %loop4.jbody, label %loop4.jend

loop4.jbody:
  %corr.ij.rowoff = mul nsw i64 %i4, %m64
  %corr.ij.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.ij.rowoff
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr.ij.rowptr, i64 %j4
  store double 0.000000e+00, ptr %corr.ij.ptr, align 8
  %ncmp4 = icmp sgt i32 %n, 0
  br i1 %ncmp4, label %loop4.k.preheader, label %loop4.kend

loop4.k.preheader:
  br label %loop4.k

loop4.k:
  %k4 = phi i64 [ 0, %loop4.k.preheader ], [ %k4.inc, %loop4.k ]
  %sumk = phi double [ 0.000000e+00, %loop4.k.preheader ], [ %sumk.new, %loop4.k ]
  %krowoff = mul nsw i64 %k4, %m64
  %krowptr = getelementptr inbounds double, ptr %data, i64 %krowoff
  %kel_i = getelementptr inbounds double, ptr %krowptr, i64 %i4
  %vi = load double, ptr %kel_i, align 8
  %kel_j = getelementptr inbounds double, ptr %krowptr, i64 %j4
  %vj = load double, ptr %kel_j, align 8
  %mulk = fmul double %vi, %vj
  %sumk.new = fadd double %sumk, %mulk
  %k4.inc = add nsw i64 %k4, 1
  %k4done = icmp eq i64 %k4.inc, %n64
  br i1 %k4done, label %loop4.k.exit, label %loop4.k

loop4.k.exit:
  br label %loop4.kend

loop4.kend:
  %sumkphi = phi double [ 0.000000e+00, %loop4.jbody ], [ %sumk.new, %loop4.k.exit ]
  store double %sumkphi, ptr %corr.ij.ptr, align 8

  %corr.ji.rowoff = mul nsw i64 %j4, %m64
  %corr.ji.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.ji.rowoff
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr.ji.rowptr, i64 %i4
  store double %sumkphi, ptr %corr.ji.ptr, align 8

  br label %loop4.j.inc

loop4.j.inc:
  %j4.inc = add nsw i64 %j4, 1
  br label %loop4.j

loop4.jend:
  br label %loop4.i.inc

loop4.i.inc:
  %i4.inc = add nsw i64 %i4, 1
  br label %loop4.i

loop4.end:
  %mlast32 = sub nsw i32 %m, 1
  %mlast64 = sext i32 %mlast32 to i64
  %corr.last.rowoff = mul nsw i64 %mlast64, %m64
  %corr.last.rowptr = getelementptr inbounds double, ptr %corr, i64 %corr.last.rowoff
  %corr.last.ptr = getelementptr inbounds double, ptr %corr.last.rowptr, i64 %mlast64
  store double 1.000000e+00, ptr %corr.last.ptr, align 8
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
