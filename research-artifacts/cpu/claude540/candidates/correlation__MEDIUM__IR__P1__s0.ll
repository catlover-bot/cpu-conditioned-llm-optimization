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
  br i1 %mgt0, label %j1.preheader, label %for.end20

j1.preheader:
  %ngt0 = icmp sgt i32 %n, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc18, %j1.preheader
  %j.0 = phi i32 [ 0, %j1.preheader ], [ %inc19, %for.inc18 ]
  %j.0.64 = sext i32 %j.0 to i64
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j.0.64
  store double 0.000000e+00, ptr %mean.j.ptr, align 8
  br i1 %ngt0, label %for.body6.preheader, label %for.end

for.body6.preheader:
  br label %for.cond6

for.cond6:                                        ; preds = %for.body8, %for.body6.preheader
  %i.0 = phi i32 [ 0, %for.body6.preheader ], [ %inc, %for.body8 ]
  %acc.0 = phi double [ 0.000000e+00, %for.body6.preheader ], [ %add15, %for.body8 ]
  %i.0.64 = sext i32 %i.0 to i64
  %rowoff = mul nsw i64 %i.0.64, %m64
  %dataidx = add nsw i64 %rowoff, %j.0.64
  %arrayidx12 = getelementptr inbounds double, ptr %data, i64 %dataidx
  %dval = load double, ptr %arrayidx12, align 8
  %add15 = fadd double %acc.0, %dval
  br label %for.body8

for.body8:
  %inc = add nsw i32 %i.0, 1
  %cmp7 = icmp slt i32 %inc, %n
  br i1 %cmp7, label %for.cond6, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.cond
  %meanacc = phi double [ 0.000000e+00, %for.cond ], [ %add15, %for.end.loopexit ]
  %div = fdiv double %meanacc, %float_n
  store double %div, ptr %mean.j.ptr, align 8
  br label %for.inc18

for.inc18:                                        ; preds = %for.end
  %inc19 = add nsw i32 %j.0, 1
  %cmp = icmp slt i32 %inc19, %m
  br i1 %cmp, label %for.cond, label %for.end20

for.end20:                                        ; preds = %for.inc18, %entry
  br i1 %mgt0, label %j2.preheader, label %for.end64

j2.preheader:
  %ngt0.2 = icmp sgt i32 %n, 0
  br label %for.cond21

for.cond21:                                       ; preds = %for.inc62, %j2.preheader
  %j2.0 = phi i32 [ 0, %j2.preheader ], [ %inc63, %for.inc62 ]
  %j2.0.64 = sext i32 %j2.0 to i64
  %stddev.j.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2.0.64
  store double 0.000000e+00, ptr %stddev.j.ptr, align 8
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2.0.64
  %meanval = load double, ptr %mean.j2.ptr, align 8
  br i1 %ngt0.2, label %for.body28.preheader, label %for.end47

for.body28.preheader:
  br label %for.cond26

for.cond26:                                       ; preds = %for.body28, %for.body28.preheader
  %i2.0 = phi i32 [ 0, %for.body28.preheader ], [ %inc46, %for.body28 ]
  %acc2.0 = phi double [ 0.000000e+00, %for.body28.preheader ], [ %add44, %for.body28 ]
  %i2.0.64 = sext i32 %i2.0 to i64
  %rowoff2 = mul nsw i64 %i2.0.64, %m64
  %dataidx2 = add nsw i64 %rowoff2, %j2.0.64
  %arrayidx32 = getelementptr inbounds double, ptr %data, i64 %dataidx2
  %dval2 = load double, ptr %arrayidx32, align 8
  %sub = fsub double %dval2, %meanval
  %mul = fmul double %sub, %sub
  %add44 = fadd double %acc2.0, %mul
  br label %for.body28

for.body28:
  %inc46 = add nsw i32 %i2.0, 1
  %cmp27 = icmp slt i32 %inc46, %n
  br i1 %cmp27, label %for.cond26, label %for.end47.loopexit

for.end47.loopexit:
  br label %for.end47

for.end47:                                        ; preds = %for.end47.loopexit, %for.cond21
  %stddevacc = phi double [ 0.000000e+00, %for.cond21 ], [ %add44, %for.end47.loopexit ]
  %div50 = fdiv double %stddevacc, %float_n
  store double %div50, ptr %stddev.j.ptr, align 8
  %call = call double @sqrt(double noundef %div50) #2
  store double %call, ptr %stddev.j.ptr, align 8
  %epsval = load double, ptr %eps, align 8
  %cmp57 = fcmp ole double %call, %epsval
  %cond = select i1 %cmp57, double 1.000000e+00, double %call
  store double %cond, ptr %stddev.j.ptr, align 8
  br label %for.inc62

for.inc62:                                        ; preds = %for.end47
  %inc63 = add nsw i32 %j2.0, 1
  %cmp22 = icmp slt i32 %inc63, %m
  br i1 %cmp22, label %for.cond21, label %for.end64

for.end64:                                        ; preds = %for.inc62, %for.end20
  %sqrtfn = call double @sqrt(double noundef %float_n) #2
  %ngt0.3 = icmp sgt i32 %n, 0
  br i1 %ngt0.3, label %for.cond65.preheader, label %for.end92

for.cond65.preheader:
  br i1 %mgt0, label %for.body67.preheader, label %for.end92

for.body67.preheader:
  br label %for.cond65

for.cond65:                                       ; preds = %for.end89, %for.body67.preheader
  %i3.0 = phi i32 [ 0, %for.body67.preheader ], [ %inc91, %for.end89 ]
  %i3.0.64 = sext i32 %i3.0 to i64
  %rowoff3 = mul nsw i64 %i3.0.64, %m64
  br label %for.cond68

for.cond68:                                       ; preds = %for.body70, %for.cond65
  %j3.0 = phi i32 [ 0, %for.cond65 ], [ %inc88, %for.body70 ]
  %j3.0.64 = sext i32 %j3.0 to i64
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3.0.64
  %meanval3 = load double, ptr %mean.j3.ptr, align 8
  %dataidx3 = add nsw i64 %rowoff3, %j3.0.64
  %arrayidx76 = getelementptr inbounds double, ptr %data, i64 %dataidx3
  %dval3 = load double, ptr %arrayidx76, align 8
  %sub77 = fsub double %dval3, %meanval3
  store double %sub77, ptr %arrayidx76, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3.0.64
  %stddevval3 = load double, ptr %stddev.j3.ptr, align 8
  %mul81 = fmul double %sqrtfn, %stddevval3
  %dval3b = load double, ptr %arrayidx76, align 8
  %div86 = fdiv double %dval3b, %mul81
  store double %div86, ptr %arrayidx76, align 8
  br label %for.body70

for.body70:
  %inc88 = add nsw i32 %j3.0, 1
  %cmp69 = icmp slt i32 %inc88, %m
  br i1 %cmp69, label %for.cond68, label %for.end89

for.end89:                                        ; preds = %for.body70
  %inc91 = add nsw i32 %i3.0, 1
  %cmp66 = icmp slt i32 %inc91, %n
  br i1 %cmp66, label %for.cond65, label %for.end92.loopexit

for.end92.loopexit:
  br label %for.end92

for.end92:                                        ; preds = %for.end92.loopexit, %for.cond65.preheader, %for.end64
  %msub1 = sub nsw i32 %m, 1
  %imlt = icmp slt i32 0, %msub1
  br i1 %imlt, label %for.body96.preheader, label %for.end142

for.body96.preheader:
  br label %for.cond93

for.cond93:                                       ; preds = %for.end139, %for.body96.preheader
  %i4.0 = phi i32 [ 0, %for.body96.preheader ], [ %inc141, %for.end139 ]
  %i4.0.64 = sext i32 %i4.0 to i64
  %corr.rowoff = mul nsw i64 %i4.0.64, %m64
  %corr.diag.idx = add nsw i64 %corr.rowoff, %i4.0.64
  %corr.diag.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.diag.idx
  store double 1.000000e+00, ptr %corr.diag.ptr, align 8
  %jstart = add nsw i32 %i4.0, 1
  %jlt = icmp slt i32 %jstart, %m
  br i1 %jlt, label %for.body104.preheader, label %for.end139

for.body104.preheader:
  br label %for.cond102

for.cond102:                                      ; preds = %for.end128, %for.body104.preheader
  %j4.0 = phi i32 [ %jstart, %for.body104.preheader ], [ %inc138, %for.end128 ]
  %j4.0.64 = sext i32 %j4.0 to i64
  %corr.ij.idx = add nsw i64 %corr.rowoff, %j4.0.64
  %corr.ij.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.ij.idx
  br i1 %ngt0, label %for.body111.preheader, label %for.end128.zero

for.body111.preheader:
  br label %for.cond109

for.cond109:                                      ; preds = %for.body111, %for.body111.preheader
  %k.0 = phi i32 [ 0, %for.body111.preheader ], [ %inc127, %for.body111 ]
  %kacc.0 = phi double [ 0.000000e+00, %for.body111.preheader ], [ %add125, %for.body111 ]
  %k.0.64 = sext i32 %k.0 to i64
  %krowoff = mul nsw i64 %k.0.64, %m64
  %kidx_i = add nsw i64 %krowoff, %i4.0.64
  %karrayidx_i = getelementptr inbounds double, ptr %data, i64 %kidx_i
  %kval_i = load double, ptr %karrayidx_i, align 8
  %kidx_j = add nsw i64 %krowoff, %j4.0.64
  %karrayidx_j = getelementptr inbounds double, ptr %data, i64 %kidx_j
  %kval_j = load double, ptr %karrayidx_j, align 8
  %mul120 = fmul double %kval_i, %kval_j
  %add125 = fadd double %kacc.0, %mul120

  br label %for.body111

for.body111:
  %inc127 = add nsw i32 %k.0, 1
  %cmp110 = icmp slt i32 %inc127, %n
  br i1 %cmp110, label %for.cond109, label %for.end128.loopexit

for.end128.loopexit:
  br label %for.end128

for.end128.zero:
  br label %for.end128

for.end128:                                       ; preds = %for.end128.loopexit, %for.end128.zero
  %kacc.final = phi double [ 0.000000e+00, %for.end128.zero ], [ %add125, %for.end128.loopexit ]
  store double %kacc.final, ptr %corr.ij.ptr, align 8
  %corr.ji.rowoff = mul nsw i64 %j4.0.64, %m64
  %corr.ji.idx = add nsw i64 %corr.ji.rowoff, %i4.0.64
  %corr.ji.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.ji.idx
  store double %kacc.final, ptr %corr.ji.ptr, align 8
  br label %for.inc137

for.inc137:
  %inc138 = add nsw i32 %j4.0, 1
  %cmp103 = icmp slt i32 %inc138, %m
  br i1 %cmp103, label %for.cond102, label %for.end139.loopexit

for.end139.loopexit:
  br label %for.end139

for.end139:                                       ; preds = %for.end139.loopexit, %for.cond93
  br label %for.inc140

for.inc140:
  %inc141 = add nsw i32 %i4.0, 1
  %cmp95 = icmp slt i32 %inc141, %msub1
  br i1 %cmp95, label %for.cond93, label %for.end142.loopexit

for.end142.loopexit:
  br label %for.end142

for.end142:                                       ; preds = %for.end142.loopexit, %entry.for.end142, %for.end92
  %msub2 = sub nsw i32 %m, 1
  %msub2.64 = sext i32 %msub2 to i64
  %corr.last.rowoff = mul nsw i64 %msub2.64, %m64
  %corr.last.idx = add nsw i64 %corr.last.rowoff, %msub2.64
  %corr.last.ptr = getelementptr inbounds double, ptr %corr, i64 %corr.last.idx
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
