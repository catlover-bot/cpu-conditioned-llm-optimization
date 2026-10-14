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

  %mcmp0 = icmp sgt i32 %m, 0
  br i1 %mcmp0, label %mean.outer.preheader, label %for.end20

mean.outer.preheader:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %mean.outer

mean.outer:
  %j1 = phi i64 [ 0, %mean.outer.preheader ], [ %j1.next, %mean.outer.latch ]
  %mean.arrayidx = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ncmp0, label %mean.inner.preheader, label %mean.store0

mean.inner.preheader:
  br label %mean.inner

mean.inner:
  %i1 = phi i64 [ 0, %mean.inner.preheader ], [ %i1.next, %mean.inner ]
  %sum = phi double [ 0.000000e+00, %mean.inner.preheader ], [ %sum.next, %mean.inner ]
  %data.off = mul nsw i64 %i1, %m64
  %data.row = getelementptr inbounds double, ptr %data, i64 %data.off
  %data.elem = getelementptr inbounds double, ptr %data.row, i64 %j1
  %dval = load double, ptr %data.elem, align 8
  %sum.next = fadd double %sum, %dval
  %i1.next = add nsw i64 %i1, 1
  %icmp1 = icmp slt i64 %i1.next, %n64
  br i1 %icmp1, label %mean.inner, label %mean.inner.exit

mean.inner.exit:
  br label %mean.store

mean.store0:
  br label %mean.store

mean.store:
  %sumval = phi double [ %sum.next, %mean.inner.exit ], [ 0.000000e+00, %mean.store0 ]
  %meandiv = fdiv double %sumval, %float_n
  store double %meandiv, ptr %mean.arrayidx, align 8
  br label %mean.outer.latch

mean.outer.latch:
  %j1.next = add nsw i64 %j1, 1
  %jcmp1 = icmp slt i64 %j1.next, %m64
  br i1 %jcmp1, label %mean.outer, label %for.end20

for.end20:
  br i1 %mcmp0, label %std.outer.preheader, label %for.end64

std.outer.preheader:
  %ncmp0b = icmp sgt i32 %n, 0
  br label %std.outer

std.outer:
  %j2 = phi i64 [ 0, %std.outer.preheader ], [ %j2.next, %std.outer.latch ]
  %std.arrayidx = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.arrayidx2 = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanv = load double, ptr %mean.arrayidx2, align 8
  br i1 %ncmp0b, label %std.inner.preheader, label %std.store0

std.inner.preheader:
  br label %std.inner

std.inner:
  %i2 = phi i64 [ 0, %std.inner.preheader ], [ %i2.next, %std.inner ]
  %ssum = phi double [ 0.000000e+00, %std.inner.preheader ], [ %ssum.next, %std.inner ]
  %data.off2 = mul nsw i64 %i2, %m64
  %data.row2 = getelementptr inbounds double, ptr %data, i64 %data.off2
  %data.elem2 = getelementptr inbounds double, ptr %data.row2, i64 %j2
  %dval2 = load double, ptr %data.elem2, align 8
  %sub2 = fsub double %dval2, %meanv
  %mul2 = fmul double %sub2, %sub2
  %ssum.next = fadd double %ssum, %mul2
  %i2.next = add nsw i64 %i2, 1
  %icmp2 = icmp slt i64 %i2.next, %n64
  br i1 %icmp2, label %std.inner, label %std.inner.exit

std.inner.exit:
  br label %std.store

std.store0:
  br label %std.store

std.store:
  %ssumval = phi double [ %ssum.next, %std.inner.exit ], [ 0.000000e+00, %std.store0 ]
  %stddiv = fdiv double %ssumval, %float_n
  %sqrtres = call double @sqrt(double noundef %stddiv) #2
  %cmple = fcmp ole double %sqrtres, 1.000000e-01
  %condval = select i1 %cmple, double 1.000000e+00, double %sqrtres
  store double %condval, ptr %std.arrayidx, align 8
  br label %std.outer.latch

std.outer.latch:
  %j2.next = add nsw i64 %j2, 1
  %jcmp2 = icmp slt i64 %j2.next, %m64
  br i1 %jcmp2, label %std.outer, label %for.end64

for.end64:
  %ncmp1 = icmp sgt i32 %n, 0
  br i1 %ncmp1, label %center.outer.preheader, label %for.end92

center.outer.preheader:
  %sqrtn = call double @sqrt(double noundef %float_n) #2
  %mcmp1 = icmp sgt i32 %m, 0
  br label %center.outer

center.outer:
  %i3 = phi i64 [ 0, %center.outer.preheader ], [ %i3.next, %center.outer.latch ]
  br i1 %mcmp1, label %center.inner.preheader, label %center.outer.latch

center.inner.preheader:
  %data.row3.base = mul nsw i64 %i3, %m64
  br label %center.inner

center.inner:
  %j3 = phi i64 [ 0, %center.inner.preheader ], [ %j3.next, %center.inner ]
  %mean.elem3 = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanv3 = load double, ptr %mean.elem3, align 8
  %data.row3 = getelementptr inbounds double, ptr %data, i64 %data.row3.base
  %data.elem3 = getelementptr inbounds double, ptr %data.row3, i64 %j3
  %dval3 = load double, ptr %data.elem3, align 8
  %sub3 = fsub double %dval3, %meanv3
  store double %sub3, ptr %data.elem3, align 8
  %std.elem3 = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stdv3 = load double, ptr %std.elem3, align 8
  %mul3 = fmul double %sqrtn, %stdv3
  %dval3b = load double, ptr %data.elem3, align 8
  %div3 = fdiv double %dval3b, %mul3
  store double %div3, ptr %data.elem3, align 8
  %j3.next = add nsw i64 %j3, 1
  %jcmp3 = icmp slt i64 %j3.next, %m64
  br i1 %jcmp3, label %center.inner, label %center.inner.exit

center.inner.exit:
  br label %center.outer.latch

center.outer.latch:
  %i3.next = add nsw i64 %i3, 1
  %icmp3 = icmp slt i64 %i3.next, %n64
  br i1 %icmp3, label %center.outer, label %for.end92

for.end92:
  %msub1 = sub nsw i32 %m, 1
  %corrcmp0 = icmp sgt i32 %msub1, 0
  br i1 %corrcmp0, label %corr.outer.preheader, label %for.end142

corr.outer.preheader:
  %msub1.64 = sext i32 %msub1 to i64
  %ncmp2 = icmp sgt i32 %n, 0
  br label %corr.outer

corr.outer:
  %i4 = phi i64 [ 0, %corr.outer.preheader ], [ %i4.next, %corr.outer.latch ]
  %corr.diag = getelementptr inbounds double, ptr %corr, i64 %i4
  %corr.rowbase = mul nsw i64 %i4, %m64
  %corr.row = getelementptr inbounds double, ptr %corr, i64 %corr.rowbase
  %corr.diagelem = getelementptr inbounds double, ptr %corr.row, i64 %i4
  store double 1.000000e+00, ptr %corr.diagelem, align 8
  %j4start = add nsw i64 %i4, 1
  %jcmp4start = icmp slt i64 %j4start, %m64
  br i1 %jcmp4start, label %corr.j.preheader, label %corr.outer.latch

corr.j.preheader:
  br label %corr.j

corr.j:
  %j4 = phi i64 [ %j4start, %corr.j.preheader ], [ %j4.next, %corr.j.latch ]
  %corr.elem4 = getelementptr inbounds double, ptr %corr.row, i64 %j4
  br i1 %ncmp2, label %corr.k.preheader, label %corr.k.store0

corr.k.preheader:
  br label %corr.k

corr.k:
  %k4 = phi i64 [ 0, %corr.k.preheader ], [ %k4.next, %corr.k ]
  %csum = phi double [ 0.000000e+00, %corr.k.preheader ], [ %csum.next, %corr.k ]
  %data.rowk.base = mul nsw i64 %k4, %m64
  %data.rowk = getelementptr inbounds double, ptr %data, i64 %data.rowk.base
  %data.elemi = getelementptr inbounds double, ptr %data.rowk, i64 %i4
  %dvali = load double, ptr %data.elemi, align 8
  %data.elemj = getelementptr inbounds double, ptr %data.rowk, i64 %j4
  %dvalj = load double, ptr %data.elemj, align 8
  %mulk = fmul double %dvali, %dvalj
  %csum.next = fadd double %csum, %mulk
  %k4.next = add nsw i64 %k4, 1
  %kcmp4 = icmp slt i64 %k4.next, %n64
  br i1 %kcmp4, label %corr.k, label %corr.k.exit

corr.k.exit:
  br label %corr.k.store

corr.k.store0:
  br label %corr.k.store

corr.k.store:
  %csumval = phi double [ %csum.next, %corr.k.exit ], [ 0.000000e+00, %corr.k.store0 ]
  store double %csumval, ptr %corr.elem4, align 8
  %corr.sym.rowbase = mul nsw i64 %j4, %m64
  %corr.sym.row = getelementptr inbounds double, ptr %corr, i64 %corr.sym.rowbase
  %corr.sym.elem = getelementptr inbounds double, ptr %corr.sym.row, i64 %i4
  store double %csumval, ptr %corr.sym.elem, align 8
  br label %corr.j.latch

corr.j.latch:
  %j4.next = add nsw i64 %j4, 1
  %jcmp4 = icmp slt i64 %j4.next, %m64
  br i1 %jcmp4, label %corr.j, label %corr.j.exit

corr.j.exit:
  br label %corr.outer.latch

corr.outer.latch:
  %i4.next = add nsw i64 %i4, 1
  %icmp4 = icmp slt i64 %i4.next, %msub1.64
  br i1 %icmp4, label %corr.outer, label %for.end142

for.end142:
  %msub2 = sub nsw i32 %m, 1
  %msub2.64 = sext i32 %msub2 to i64
  %corr.last.rowbase = mul nsw i64 %msub2.64, %m64
  %corr.last.row = getelementptr inbounds double, ptr %corr, i64 %corr.last.rowbase
  %corr.last.elem = getelementptr inbounds double, ptr %corr.last.row, i64 %msub2.64
  store double 1.000000e+00, ptr %corr.last.elem, align 8
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
