; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_correlation(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %corr, ptr noundef %mean, ptr noundef %stddev) #0 {
entry:
  %eps = fadd double 0.000000e+00, 1.000000e-01
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  %mgt0 = icmp sgt i32 %m, 0
  br i1 %mgt0, label %j1.preheader, label %for.end20

j1.preheader:
  %ngt0 = icmp sgt i32 %n, 0
  br label %j1.head

j1.head:
  %j1 = phi i64 [ 0, %j1.preheader ], [ %j1.next, %j1.latch ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ngt0, label %i1.preheader, label %j1.storediv

i1.preheader:
  br label %i1.body

i1.body:
  %i1 = phi i64 [ 0, %i1.preheader ], [ %i1.next, %i1.body ]
  %acc1 = phi double [ 0.000000e+00, %i1.preheader ], [ %acc1.next, %i1.body ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %elptr1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %elptr1j = getelementptr inbounds double, ptr %elptr1, i64 %j1
  %val1 = load double, ptr %elptr1j, align 8
  %acc1.next = fadd double %acc1, %val1
  %i1.next = add nsw i64 %i1, 1
  %i1cmp = icmp slt i64 %i1.next, %n64
  br i1 %i1cmp, label %i1.body, label %i1.exit

i1.exit:
  br label %j1.storediv

j1.storediv:
  %sumphi = phi double [ 0.000000e+00, %j1.head ], [ %acc1.next, %i1.exit ]
  %meanval = fdiv double %sumphi, %float_n
  store double %meanval, ptr %mean.j.ptr, align 8
  br label %j1.latch

j1.latch:
  %j1.next = add nsw i64 %j1, 1
  %j1cmp = icmp slt i64 %j1.next, %m64
  br i1 %j1cmp, label %j1.head, label %for.end20

for.end20:
  br i1 %mgt0, label %j2.preheader, label %for.end64

j2.preheader:
  %ngt0.2 = icmp sgt i32 %n, 0
  br label %j2.head

j2.head:
  %j2 = phi i64 [ 0, %j2.preheader ], [ %j2.next, %j2.latch ]
  %stddev.j.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.j.ptr2 = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.j.ptr2, align 8
  br i1 %ngt0.2, label %i2.preheader, label %j2.storediv

i2.preheader:
  br label %i2.body

i2.body:
  %i2 = phi i64 [ 0, %i2.preheader ], [ %i2.next, %i2.body ]
  %acc2 = phi double [ 0.000000e+00, %i2.preheader ], [ %acc2.next, %i2.body ]
  %rowoff2 = mul nsw i64 %i2, %m64
  %elptr2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  %elptr2j = getelementptr inbounds double, ptr %elptr2, i64 %j2
  %val2 = load double, ptr %elptr2j, align 8
  %sub2 = fsub double %val2, %meanval2
  %mul2 = fmul double %sub2, %sub2
  %acc2.next = fadd double %acc2, %mul2
  %i2.next = add nsw i64 %i2, 1
  %i2cmp = icmp slt i64 %i2.next, %n64
  br i1 %i2cmp, label %i2.body, label %i2.exit

i2.exit:
  br label %j2.storediv

j2.storediv:
  %sumphi2 = phi double [ 0.000000e+00, %j2.head ], [ %acc2.next, %i2.exit ]
  %divval = fdiv double %sumphi2, %float_n
  store double %divval, ptr %stddev.j.ptr, align 8
  %sqrtval = call double @sqrt(double noundef %divval)
  store double %sqrtval, ptr %stddev.j.ptr, align 8
  %cmple = fcmp ole double %sqrtval, %eps
  %selval = select i1 %cmple, double 1.000000e+00, double %sqrtval
  store double %selval, ptr %stddev.j.ptr, align 8
  br label %j2.latch

j2.latch:
  %j2.next = add nsw i64 %j2, 1
  %j2cmp = icmp slt i64 %j2.next, %m64
  br i1 %j2cmp, label %j2.head, label %for.end64

for.end64:
  %ngt0.3 = icmp sgt i32 %n, 0
  br i1 %ngt0.3, label %i3.preheader, label %for.end92

i3.preheader:
  %sqrtfn = call double @sqrt(double noundef %float_n)
  %mgt0.3 = icmp sgt i32 %m, 0
  br label %i3.head

i3.head:
  %i3 = phi i64 [ 0, %i3.preheader ], [ %i3.next, %i3.latch ]
  %rowoff3 = mul nsw i64 %i3, %m64
  %elptr3 = getelementptr inbounds double, ptr %data, i64 %rowoff3
  br i1 %mgt0.3, label %j3.body, label %i3.latch

j3.body:
  %j3 = phi i64 [ 0, %i3.head ], [ %j3.next, %j3.body ]
  %mean.j.ptr3 = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanval3 = load double, ptr %mean.j.ptr3, align 8
  %elptr3j = getelementptr inbounds double, ptr %elptr3, i64 %j3
  %val3 = load double, ptr %elptr3j, align 8
  %sub3 = fsub double %val3, %meanval3
  store double %sub3, ptr %elptr3j, align 8
  %stddev.j.ptr3 = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stdval3 = load double, ptr %stddev.j.ptr3, align 8
  %mul3 = fmul double %sqrtfn, %stdval3
  %val3b = load double, ptr %elptr3j, align 8
  %div3 = fdiv double %val3b, %mul3
  store double %div3, ptr %elptr3j, align 8
  %j3.next = add nsw i64 %j3, 1
  %j3cmp = icmp slt i64 %j3.next, %m64
  br i1 %j3cmp, label %j3.body, label %i3.latch

i3.latch:
  %i3.next = add nsw i64 %i3, 1
  %i3cmp = icmp slt i64 %i3.next, %n64
  br i1 %i3cmp, label %i3.head, label %for.end92

for.end92:
  %msub1 = sub nsw i32 %m, 1
  %mgt0.4 = icmp slt i32 0, %msub1
  br i1 %mgt0.4, label %i4.preheader, label %for.end142

i4.preheader:
  %msub1.64 = sext i32 %msub1 to i64
  %ngt0.4 = icmp sgt i32 %n, 0
  br label %i4.head

i4.head:
  %i4 = phi i64 [ 0, %i4.preheader ], [ %i4.next, %i4.latch ]
  %rowoff4 = mul nsw i64 %i4, %m64
  %corr.i.row = getelementptr inbounds double, ptr %corr, i64 %rowoff4
  %corr.ii.ptr = getelementptr inbounds double, ptr %corr.i.row, i64 %i4
  store double 1.000000e+00, ptr %corr.ii.ptr, align 8
  %j4start = add nsw i64 %i4, 1
  %j4cmp.entry = icmp slt i64 %j4start, %m64
  br i1 %j4cmp.entry, label %j4.head, label %i4.latch

j4.head:
  %j4 = phi i64 [ %j4start, %i4.head ], [ %j4.next, %j4.latch ]
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr.i.row, i64 %j4
  br i1 %ngt0.4, label %k4.preheader, label %k4.storeval

k4.preheader:
  br label %k4.body

k4.body:
  %k4 = phi i64 [ 0, %k4.preheader ], [ %k4.next, %k4.body ]
  %acc4 = phi double [ 0.000000e+00, %k4.preheader ], [ %acc4.next, %k4.body ]
  %rowoff4k = mul nsw i64 %k4, %m64
  %elptr4k = getelementptr inbounds double, ptr %data, i64 %rowoff4k
  %elptr4ki = getelementptr inbounds double, ptr %elptr4k, i64 %i4
  %val4i = load double, ptr %elptr4ki, align 8
  %elptr4kj = getelementptr inbounds double, ptr %elptr4k, i64 %j4
  %val4j = load double, ptr %elptr4kj, align 8
  %mul4 = fmul double %val4i, %val4j
  %acc4.next = fadd double %acc4, %mul4
  %k4.next = add nsw i64 %k4, 1
  %k4cmp = icmp slt i64 %k4.next, %n64
  br i1 %k4cmp, label %k4.body, label %k4.exit

k4.exit:
  br label %k4.storeval

k4.storeval:
  %sumphi4 = phi double [ 0.000000e+00, %j4.head ], [ %acc4.next, %k4.exit ]
  store double %sumphi4, ptr %corr.ij.ptr, align 8
  %rowoff4j = mul nsw i64 %j4, %m64
  %corr.j.row = getelementptr inbounds double, ptr %corr, i64 %rowoff4j
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr.j.row, i64 %i4
  store double %sumphi4, ptr %corr.ji.ptr, align 8
  br label %j4.latch

j4.latch:
  %j4.next = add nsw i64 %j4, 1
  %j4cmp = icmp slt i64 %j4.next, %m64
  br i1 %j4cmp, label %j4.head, label %i4.latch

i4.latch:
  %i4.next = add nsw i64 %i4, 1
  %i4cmp = icmp slt i64 %i4.next, %msub1.64
  br i1 %i4cmp, label %i4.head, label %for.end142

for.end142:
  %msub1b = sub nsw i32 %m, 1
  %msub1b64 = sext i32 %msub1b to i64
  %rowofff = mul nsw i64 %msub1b64, %m64
  %corr.ff.row = getelementptr inbounds double, ptr %corr, i64 %rowofff
  %corr.ff.ptr = getelementptr inbounds double, ptr %corr.ff.row, i64 %msub1b64
  store double 1.000000e+00, ptr %corr.ff.ptr, align 8
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
