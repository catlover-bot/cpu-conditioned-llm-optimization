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
  br i1 %mcmp0, label %j1.preheader, label %for.end20

j1.preheader:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %j1.loop

j1.loop:
  %j1 = phi i64 [ 0, %j1.preheader ], [ %j1.next, %j1.latch ]
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ncmp0, label %i1.preheader, label %j1.store

i1.preheader:
  %data.row0.base = getelementptr inbounds double, ptr %data, i64 %j1
  br label %i1.loop

i1.loop:
  %i1 = phi i64 [ 0, %i1.preheader ], [ %i1.next, %i1.loop ]
  %sum1 = phi double [ 0.000000e+00, %i1.preheader ], [ %sum1.next, %i1.loop ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %dptr1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %dptr1b = getelementptr inbounds double, ptr %dptr1, i64 %j1
  %dval1 = load double, ptr %dptr1b, align 8
  %sum1.next = fadd double %sum1, %dval1
  %i1.next = add nsw i64 %i1, 1
  %i1cmp = icmp slt i64 %i1.next, %n64
  br i1 %i1cmp, label %i1.loop, label %j1.store

j1.store:
  %sumphi = phi double [ 0.000000e+00, %j1.loop ], [ %sum1.next, %i1.loop ]
  %meandiv = fdiv double %sumphi, %float_n
  store double %meandiv, ptr %mean.j1.ptr, align 8
  br label %j1.latch

j1.latch:
  %j1.next = add nsw i64 %j1, 1
  %j1cmp = icmp slt i64 %j1.next, %m64
  br i1 %j1cmp, label %j1.loop, label %for.end20

for.end20:
  br i1 %mcmp0, label %j2.preheader, label %for.end64

j2.preheader:
  %ncmp0.2 = icmp sgt i32 %n, 0
  br label %j2.loop

j2.loop:
  %j2 = phi i64 [ 0, %j2.preheader ], [ %j2.next, %j2.latch ]
  %stddev.j2.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.j2.ptr, align 8
  br i1 %ncmp0.2, label %i2.preheader, label %j2.store

i2.preheader:
  br label %i2.loop

i2.loop:
  %i2 = phi i64 [ 0, %i2.preheader ], [ %i2.next, %i2.loop ]
  %sum2 = phi double [ 0.000000e+00, %i2.preheader ], [ %sum2.next, %i2.loop ]
  %rowoff2 = mul nsw i64 %i2, %m64
  %dptr2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  %dptr2b = getelementptr inbounds double, ptr %dptr2, i64 %j2
  %dval2 = load double, ptr %dptr2b, align 8
  %sub2 = fsub double %dval2, %meanval2
  %mul2 = fmul double %sub2, %sub2
  %sum2.next = fadd double %sum2, %mul2
  %i2.next = add nsw i64 %i2, 1
  %i2cmp = icmp slt i64 %i2.next, %n64
  br i1 %i2cmp, label %i2.loop, label %j2.store

j2.store:
  %sum2phi = phi double [ 0.000000e+00, %j2.loop ], [ %sum2.next, %i2.loop ]
  %div50 = fdiv double %sum2phi, %float_n
  %sqrtcall = call double @sqrt(double noundef %div50) #2
  %cmp57 = fcmp ole double %sqrtcall, %eps
  %cond = select i1 %cmp57, double 1.000000e+00, double %sqrtcall
  store double %cond, ptr %stddev.j2.ptr, align 8
  br label %j2.latch

j2.latch:
  %j2.next = add nsw i64 %j2, 1
  %j2cmp = icmp slt i64 %j2.next, %m64
  br i1 %j2cmp, label %j2.loop, label %for.end64

for.end64:
  %ncmp1 = icmp sgt i32 %n, 0
  br i1 %ncmp1, label %i3.preheader, label %for.end92

i3.preheader:
  %mcmp1 = icmp sgt i32 %m, 0
  %sqrtfn = call double @sqrt(double noundef %float_n) #2
  br label %i3.loop

i3.loop:
  %i3 = phi i64 [ 0, %i3.preheader ], [ %i3.next, %i3.latch ]
  br i1 %mcmp1, label %j3.preheader, label %i3.latch

j3.preheader:
  %rowoff3 = mul nsw i64 %i3, %m64
  %rowbase3 = getelementptr inbounds double, ptr %data, i64 %rowoff3
  br label %j3.loop

j3.loop:
  %j3 = phi i64 [ 0, %j3.preheader ], [ %j3.next, %j3.loop ]
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanval3 = load double, ptr %mean.j3.ptr, align 8
  %dptr3 = getelementptr inbounds double, ptr %rowbase3, i64 %j3
  %dval3 = load double, ptr %dptr3, align 8
  %sub77 = fsub double %dval3, %meanval3
  store double %sub77, ptr %dptr3, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stdval3 = load double, ptr %stddev.j3.ptr, align 8
  %mul81 = fmul double %sqrtfn, %stdval3
  %dval3b = load double, ptr %dptr3, align 8
  %div86 = fdiv double %dval3b, %mul81
  store double %div86, ptr %dptr3, align 8
  %j3.next = add nsw i64 %j3, 1
  %j3cmp = icmp slt i64 %j3.next, %m64
  br i1 %j3cmp, label %j3.loop, label %i3.latch

i3.latch:
  %i3.next = add nsw i64 %i3, 1
  %i3cmp = icmp slt i64 %i3.next, %n64
  br i1 %i3cmp, label %i3.loop, label %for.end92

for.end92:
  %msub1 = sub nsw i32 %m, 1
  %mcmp2 = icmp slt i32 0, %msub1
  br i1 %mcmp2, label %i4.preheader, label %for.end142

i4.preheader:
  %msub1.64 = sext i32 %msub1 to i64
  br label %i4.loop

i4.loop:
  %i4 = phi i64 [ 0, %i4.preheader ], [ %i4.next, %i4.latch ]
  %corr.diag.off = mul nsw i64 %i4, %m64
  %corr.diag.row = getelementptr inbounds double, ptr %corr, i64 %corr.diag.off
  %corr.diag.ptr = getelementptr inbounds double, ptr %corr.diag.row, i64 %i4
  store double 1.000000e+00, ptr %corr.diag.ptr, align 8

  %j4start = add nsw i64 %i4, 1
  %j4cmp0 = icmp slt i64 %j4start, %m64
  br i1 %j4cmp0, label %j4.preheader, label %i4.latch

j4.preheader:
  %ncmp2 = icmp sgt i32 %n, 0
  br label %j4.loop

j4.loop:
  %j4 = phi i64 [ %j4start, %j4.preheader ], [ %j4.next, %j4.latch2 ]
  %corr.row4 = getelementptr inbounds double, ptr %corr, i64 %corr.diag.off
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr.row4, i64 %j4
  br i1 %ncmp2, label %k4.preheader, label %k4.store

k4.preheader:
  br label %k4.loop

k4.loop:
  %k4 = phi i64 [ 0, %k4.preheader ], [ %k4.next, %k4.loop ]
  %sum4 = phi double [ 0.000000e+00, %k4.preheader ], [ %sum4.next, %k4.loop ]
  %krow4 = mul nsw i64 %k4, %m64
  %kbase4 = getelementptr inbounds double, ptr %data, i64 %krow4
  %ki4ptr = getelementptr inbounds double, ptr %kbase4, i64 %i4
  %ki4val = load double, ptr %ki4ptr, align 8
  %kj4ptr = getelementptr inbounds double, ptr %kbase4, i64 %j4
  %kj4val = load double, ptr %kj4ptr, align 8
  %mul120 = fmul double %ki4val, %kj4val
  %sum4.next = fadd double %sum4, %mul120
  %k4.next = add nsw i64 %k4, 1
  %k4cmp = icmp slt i64 %k4.next, %n64
  br i1 %k4cmp, label %k4.loop, label %k4.store

k4.store:
  %sum4phi = phi double [ 0.000000e+00, %j4.loop ], [ %sum4.next, %k4.loop ]
  store double %sum4phi, ptr %corr.ij.ptr, align 8
  %corr.row4j = mul nsw i64 %j4, %m64
  %corr.rowj.base = getelementptr inbounds double, ptr %corr, i64 %corr.row4j
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr.rowj.base, i64 %i4
  store double %sum4phi, ptr %corr.ji.ptr, align 8
  br label %j4.latch2

j4.latch2:
  %j4.next = add nsw i64 %j4, 1
  %j4cmp = icmp slt i64 %j4.next, %m64
  br i1 %j4cmp, label %j4.loop, label %i4.latch

i4.latch:
  %i4.next = add nsw i64 %i4, 1
  %i4cmp = icmp slt i64 %i4.next, %msub1.64
  br i1 %i4cmp, label %i4.loop, label %for.end142

for.end142:
  %msub2 = sub nsw i32 %m, 1
  %msub2.64 = sext i32 %msub2 to i64
  %corr.last.off = mul nsw i64 %msub2.64, %m64
  %corr.last.row = getelementptr inbounds double, ptr %corr, i64 %corr.last.off
  %corr.last.ptr = getelementptr inbounds double, ptr %corr.last.row, i64 %msub2.64
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
