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
  br i1 %mgt0, label %loop1.j.preheader, label %loop1.end

loop1.j.preheader:
  %ngt0.1 = icmp sgt i32 %n, 0
  br label %loop1.j

loop1.j:                                          ; preds = %loop1.j.inc, %loop1.j.preheader
  %j1 = phi i64 [ 0, %loop1.j.preheader ], [ %j1.inc, %loop1.j.inc ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ngt0.1, label %loop1.i.preheader, label %loop1.i.end.zero

loop1.i.preheader:
  %data.row0.j = getelementptr inbounds double, ptr %data, i64 %j1
  br label %loop1.i

loop1.i:                                          ; preds = %loop1.i, %loop1.i.preheader
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.inc, %loop1.i ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.preheader ], [ %sum1.new, %loop1.i ]
  %ioff1 = mul nsw i64 %i1, %m64
  %dataij.ptr = getelementptr inbounds double, ptr %data.row0.j, i64 %ioff1
  %dataij = load double, ptr %dataij.ptr, align 8
  %sum1.new = fadd double %sum1, %dataij
  %i1.inc = add nsw i64 %i1, 1
  %cmp1i = icmp slt i64 %i1.inc, %n64
  br i1 %cmp1i, label %loop1.i, label %loop1.i.end

loop1.i.end:                                      ; preds = %loop1.i
  br label %loop1.i.end.zero

loop1.i.end.zero:                                 ; preds = %loop1.i.end, %loop1.j
  %sumfinal1 = phi double [ 0.000000e+00, %loop1.j ], [ %sum1.new, %loop1.i.end ]
  store double %sumfinal1, ptr %mean.j.ptr, align 8
  %meanval = load double, ptr %mean.j.ptr, align 8
  %meandiv = fdiv double %meanval, %float_n
  store double %meandiv, ptr %mean.j.ptr, align 8
  %j1.inc = add nsw i64 %j1, 1
  %cmp1j = icmp slt i64 %j1.inc, %m64
  br i1 %cmp1j, label %loop1.j, label %loop1.end

loop1.end:                                        ; preds = %loop1.i.end.zero, %entry
  br i1 %mgt0, label %loop2.j.preheader, label %loop2.end

loop2.j.preheader:
  %ngt0.2 = icmp sgt i32 %n, 0
  br label %loop2.j

loop2.j:                                          ; preds = %loop2.j.inc, %loop2.j.preheader
  %j2 = phi i64 [ 0, %loop2.j.preheader ], [ %j2.inc, %loop2.j.inc ]
  %stddev.j.ptr = getelementptr inbounds double, ptr %stddev, i64 %j2
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanj2 = load double, ptr %mean.j2.ptr, align 8
  br i1 %ngt0.2, label %loop2.i.preheader, label %loop2.i.end.zero

loop2.i.preheader:
  %data.row0.j2 = getelementptr inbounds double, ptr %data, i64 %j2
  br label %loop2.i

loop2.i:                                          ; preds = %loop2.i, %loop2.i.preheader
  %i2 = phi i64 [ 0, %loop2.i.preheader ], [ %i2.inc, %loop2.i ]
  %sum2 = phi double [ 0.000000e+00, %loop2.i.preheader ], [ %sum2.new, %loop2.i ]
  %ioff2 = mul nsw i64 %i2, %m64
  %dataij2.ptr = getelementptr inbounds double, ptr %data.row0.j2, i64 %ioff2
  %dataij2 = load double, ptr %dataij2.ptr, align 8
  %sub2 = fsub double %dataij2, %meanj2
  %mul2 = fmul double %sub2, %sub2
  %sum2.new = fadd double %sum2, %mul2
  %i2.inc = add nsw i64 %i2, 1
  %cmp2i = icmp slt i64 %i2.inc, %n64
  br i1 %cmp2i, label %loop2.i, label %loop2.i.end

loop2.i.end:                                      ; preds = %loop2.i
  br label %loop2.i.end.zero

loop2.i.end.zero:                                 ; preds = %loop2.i.end, %loop2.j
  %sumfinal2 = phi double [ 0.000000e+00, %loop2.j ], [ %sum2.new, %loop2.i.end ]
  store double %sumfinal2, ptr %stddev.j.ptr, align 8
  %stdval = load double, ptr %stddev.j.ptr, align 8
  %stddiv = fdiv double %stdval, %float_n
  store double %stddiv, ptr %stddev.j.ptr, align 8
  %sqrtval = call double @sqrt(double noundef %stddiv) #2
  store double %sqrtval, ptr %stddev.j.ptr, align 8
  %stdload2 = load double, ptr %stddev.j.ptr, align 8
  %cmple = fcmp ole double %stdload2, %eps
  %selval = select i1 %cmple, double 1.000000e+00, double %stdload2
  store double %selval, ptr %stddev.j.ptr, align 8
  %j2.inc = add nsw i64 %j2, 1
  %cmp2j = icmp slt i64 %j2.inc, %m64
  br i1 %cmp2j, label %loop2.j, label %loop2.end

loop2.end:                                        ; preds = %loop2.i.end.zero, %loop1.end
  %sqrt_floatn = call double @sqrt(double noundef %float_n) #2
  %ngt0.3 = icmp sgt i32 %n, 0
  br i1 %ngt0.3, label %loop3.i.preheader, label %loop3.end

loop3.i.preheader:
  %mgt0.3 = icmp sgt i32 %m, 0
  br label %loop3.i

loop3.i:                                          ; preds = %loop3.i.inc, %loop3.i.preheader
  %i3 = phi i64 [ 0, %loop3.i.preheader ], [ %i3.inc, %loop3.i.inc ]
  br i1 %mgt0.3, label %loop3.j.preheader, label %loop3.i.inc

loop3.j.preheader:
  %ioff3 = mul nsw i64 %i3, %m64
  %data.row3 = getelementptr inbounds double, ptr %data, i64 %ioff3
  br label %loop3.j

loop3.j:                                          ; preds = %loop3.j, %loop3.j.preheader
  %j3 = phi i64 [ 0, %loop3.j.preheader ], [ %j3.inc, %loop3.j ]
  %mean.j3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %meanj3 = load double, ptr %mean.j3.ptr, align 8
  %data.ij3.ptr = getelementptr inbounds double, ptr %data.row3, i64 %j3
  %dataij3 = load double, ptr %data.ij3.ptr, align 8
  %subij3 = fsub double %dataij3, %meanj3
  store double %subij3, ptr %data.ij3.ptr, align 8
  %stddev.j3.ptr = getelementptr inbounds double, ptr %stddev, i64 %j3
  %stddevj3 = load double, ptr %stddev.j3.ptr, align 8
  %mulden3 = fmul double %sqrt_floatn, %stddevj3
  %dataij3b = load double, ptr %data.ij3.ptr, align 8
  %divval3 = fdiv double %dataij3b, %mulden3
  store double %divval3, ptr %data.ij3.ptr, align 8
  %j3.inc = add nsw i64 %j3, 1
  %cmp3j = icmp slt i64 %j3.inc, %m64
  br i1 %cmp3j, label %loop3.j, label %loop3.j.end

loop3.j.end:                                      ; preds = %loop3.j
  br label %loop3.i.inc

loop3.i.inc:                                      ; preds = %loop3.j.end, %loop3.i
  %i3.inc = add nsw i64 %i3, 1
  %cmp3i = icmp slt i64 %i3.inc, %n64
  br i1 %cmp3i, label %loop3.i, label %loop3.end

loop3.end:                                        ; preds = %loop3.i.inc, %loop2.end
  %mminus1 = sub nsw i32 %m, 1
  %mminus1.64 = sext i32 %mminus1 to i64
  %cmp4outer = icmp slt i64 0, %mminus1.64
  br i1 %cmp4outer, label %loop4.i.preheader, label %loop4.end

loop4.i.preheader:
  %ngt0.4 = icmp sgt i32 %n, 0
  br label %loop4.i

loop4.i:                                          ; preds = %loop4.i.inc, %loop4.i.preheader
  %i4 = phi i64 [ 0, %loop4.i.preheader ], [ %i4.inc, %loop4.i.inc ]
  %corr.rowi.ptr = getelementptr inbounds double, ptr %corr, i64 %m64
  %ioff4c = mul nsw i64 %i4, %m64
  %corr.row.i4 = getelementptr inbounds double, ptr %corr, i64 %ioff4c
  %corr.ii.ptr = getelementptr inbounds double, ptr %corr.row.i4, i64 %i4
  store double 1.000000e+00, ptr %corr.ii.ptr, align 8
  %j4start = add nsw i64 %i4, 1
  %cmp4j.entry = icmp slt i64 %j4start, %m64
  br i1 %cmp4j.entry, label %loop4.j.preheader, label %loop4.j.end

loop4.j.preheader:
  br label %loop4.j

loop4.j:                                          ; preds = %loop4.j.inc, %loop4.j.preheader
  %j4 = phi i64 [ %j4start, %loop4.j.preheader ], [ %j4.inc, %loop4.j.inc ]
  %corr.ij4.ptr = getelementptr inbounds double, ptr %corr.row.i4, i64 %j4
  store double 0.000000e+00, ptr %corr.ij4.ptr, align 8
  br i1 %ngt0.4, label %loop4.k.preheader, label %loop4.k.end

loop4.k.preheader:
  %data.col.i4 = getelementptr inbounds double, ptr %data, i64 %i4
  %data.col.j4 = getelementptr inbounds double, ptr %data, i64 %j4
  br label %loop4.k

loop4.k:                                          ; preds = %loop4.k, %loop4.k.preheader
  %k4 = phi i64 [ 0, %loop4.k.preheader ], [ %k4.inc, %loop4.k ]
  %sum4 = phi double [ 0.000000e+00, %loop4.k.preheader ], [ %sum4.new, %loop4.k ]
  %koff4 = mul nsw i64 %k4, %m64
  %dataki.ptr = getelementptr inbounds double, ptr %data.col.i4, i64 %koff4
  %dataki = load double, ptr %dataki.ptr, align 8
  %datakj.ptr = getelementptr inbounds double, ptr %data.col.j4, i64 %koff4
  %datakj = load double, ptr %datakj.ptr, align 8
  %mul4 = fmul double %dataki, %datakj
  %sum4.new = fadd double %sum4, %mul4
  %k4.inc = add nsw i64 %k4, 1
  %cmp4k = icmp slt i64 %k4.inc, %n64
  br i1 %cmp4k, label %loop4.k, label %loop4.k.end.compute

loop4.k.end.compute:
  br label %loop4.k.end

loop4.k.end:                                      ; preds = %loop4.k.end.compute, %loop4.j
  %sumfinal4 = phi double [ 0.000000e+00, %loop4.j ], [ %sum4.new, %loop4.k.end.compute ]
  store double %sumfinal4, ptr %corr.ij4.ptr, align 8
  %corr.ij4.val = load double, ptr %corr.ij4.ptr, align 8
  %corr.jrow.ptr = getelementptr inbounds double, ptr %data, i64 0
  %joff4c = mul nsw i64 %j4, %m64
  %corr.row.j4 = getelementptr inbounds double, ptr %corr, i64 %joff4c
  %corr.ji4.ptr = getelementptr inbounds double, ptr %corr.row.j4, i64 %i4
  store double %corr.ij4.val, ptr %corr.ji4.ptr, align 8
  %j4.inc = add nsw i64 %j4, 1
  %cmp4j = icmp slt i64 %j4.inc, %m64
  br i1 %cmp4j, label %loop4.j, label %loop4.j.end

loop4.j.end:                                      ; preds = %loop4.k.end, %loop4.j.entry.false
  br label %loop4.i.inc

loop4.i.inc:                                      ; preds = %loop4.j.end
  %i4.inc = add nsw i64 %i4, 1
  %cmp4i = icmp slt i64 %i4.inc, %mminus1.64
  br i1 %cmp4i, label %loop4.i, label %loop4.end

loop4.end:                                        ; preds = %loop4.i.inc, %loop3.end
  %mminus1b = sub nsw i32 %m, 1
  %mminus1b64 = sext i32 %mminus1b to i64
  %finaloff = mul nsw i64 %mminus1b64, %m64
  %corr.final.row = getelementptr inbounds double, ptr %corr, i64 %finaloff
  %corr.final.ptr = getelementptr inbounds double, ptr %corr.final.row, i64 %mminus1b64
  store double 1.000000e+00, ptr %corr.final.ptr, align 8
  ret void
}

; loop4.j.entry.false is unreachable placeholder to satisfy phi predecessor naming; not used.
; (no-op)

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
