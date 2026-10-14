; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp_m_le0 = icmp sle i32 %m, 0
  %cmp_n_le0 = icmp sle i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br i1 %cmp_m_le0, label %for.end19, label %mean.outer.preheader

mean.outer.preheader:
  br label %mean.outer

mean.outer:                                       ; preds = %mean.outer.preheader, %mean.outer.latch
  %j = phi i64 [ 0, %mean.outer.preheader ], [ %j.next, %mean.outer.latch ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j
  store double 0.000000e+00, ptr %mean.j.ptr, align 8

  br i1 %cmp_n_le0, label %mean.divide, label %mean.inner.preheader

mean.inner.preheader:
  br label %mean.inner

mean.inner:                                        ; preds = %mean.inner.preheader, %mean.inner
  %i = phi i64 [ 0, %mean.inner.preheader ], [ %i.next, %mean.inner ]
  %row.off = mul nsw i64 %i, %m64
  %elem.off = add nsw i64 %row.off, %j
  %data.elem.ptr = getelementptr inbounds double, ptr %data, i64 %elem.off
  %dval = load double, ptr %data.elem.ptr, align 8
  %meanv = load double, ptr %mean.j.ptr, align 8
  %addv = fadd double %meanv, %dval
  store double %addv, ptr %mean.j.ptr, align 8
  %i.next = add nsw i64 %i, 1
  %inner.cond = icmp slt i64 %i.next, %n64
  br i1 %inner.cond, label %mean.inner, label %mean.divide

mean.divide:                                       ; preds = %mean.outer, %mean.inner
  %meanv2 = load double, ptr %mean.j.ptr, align 8
  %divv = fdiv double %meanv2, %float_n
  store double %divv, ptr %mean.j.ptr, align 8
  %j.next = add nsw i64 %j, 1
  %outer.cond = icmp slt i64 %j.next, %m64
  br i1 %outer.cond, label %mean.outer.latch, label %for.end19

mean.outer.latch:
  br label %mean.outer

for.end19:                                        ; preds = %mean.divide, %entry
  br i1 %cmp_n_le0, label %for.end37, label %center.outer.preheader

center.outer.preheader:
  br label %center.outer

center.outer:                                      ; preds = %center.outer.preheader, %center.outer.latch
  %ci = phi i64 [ 0, %center.outer.preheader ], [ %ci.next, %center.outer.latch ]
  %crow.off = mul nsw i64 %ci, %m64
  br i1 %cmp_m_le0, label %center.outer.latch, label %center.inner.preheader

center.inner.preheader:
  br label %center.inner

center.inner:                                       ; preds = %center.inner.preheader, %center.inner
  %cj = phi i64 [ 0, %center.inner.preheader ], [ %cj.next, %center.inner ]
  %cmean.ptr = getelementptr inbounds double, ptr %mean, i64 %cj
  %cmeanv = load double, ptr %cmean.ptr, align 8
  %celem.off = add nsw i64 %crow.off, %cj
  %cdata.ptr = getelementptr inbounds double, ptr %data, i64 %celem.off
  %cdatav = load double, ptr %cdata.ptr, align 8
  %csub = fsub double %cdatav, %cmeanv
  store double %csub, ptr %cdata.ptr, align 8
  %cj.next = add nsw i64 %cj, 1
  %cinner.cond = icmp slt i64 %cj.next, %m64
  br i1 %cinner.cond, label %center.inner, label %center.outer.latch

center.outer.latch:                                 ; preds = %center.outer, %center.inner
  %ci.next = add nsw i64 %ci, 1
  %couter.cond = icmp slt i64 %ci.next, %n64
  br i1 %couter.cond, label %center.outer, label %for.end37

for.end37:                                          ; preds = %center.outer.latch, %for.end19
  br i1 %cmp_m_le0, label %for.end86, label %cov.outer.preheader

cov.outer.preheader:
  %sub67 = fsub double %float_n, 1.000000e+00
  br label %cov.outer

cov.outer:                                          ; preds = %cov.outer.preheader, %cov.outer.latch
  %oi = phi i64 [ 0, %cov.outer.preheader ], [ %oi.next, %cov.outer.latch ]
  %oi.row.off = mul nsw i64 %oi, %m64
  %ojinit = %oi
  %jstart.cond = icmp slt i64 %oi, %m64
  br i1 %jstart.cond, label %cov.inner.preheader, label %cov.outer.latch

cov.inner.preheader:
  br label %cov.inner

cov.inner:                                          ; preds = %cov.inner.preheader, %cov.inner.latch
  %oj = phi i64 [ %oi, %cov.inner.preheader ], [ %oj.next, %cov.inner.latch ]
  %cov.ij.off = add nsw i64 %oi.row.off, %oj
  %cov.ij.ptr = getelementptr inbounds double, ptr %cov, i64 %cov.ij.off
  store double 0.000000e+00, ptr %cov.ij.ptr, align 8

  %cmp_n_le0_2 = icmp sle i32 %n, 0
  br i1 %cmp_n_le0_2, label %cov.k.end, label %cov.k.preheader

cov.k.preheader:
  br label %cov.k

cov.k:                                              ; preds = %cov.k.preheader, %cov.k
  %k = phi i64 [ 0, %cov.k.preheader ], [ %k.next, %cov.k ]
  %k.row.off = mul nsw i64 %k, %m64
  %ki.off = add nsw i64 %k.row.off, %oi
  %ki.ptr = getelementptr inbounds double, ptr %data, i64 %ki.off
  %ki.val = load double, ptr %ki.ptr, align 8
  %kj.off = add nsw i64 %k.row.off, %oj
  %kj.ptr = getelementptr inbounds double, ptr %data, i64 %kj.off
  %kj.val = load double, ptr %kj.ptr, align 8
  %prod = fmul double %ki.val, %kj.val
  %covval = load double, ptr %cov.ij.ptr, align 8
  %covadd = fadd double %covval, %prod
  store double %covadd, ptr %cov.ij.ptr, align 8
  %k.next = add nsw i64 %k, 1
  %k.cond = icmp slt i64 %k.next, %n64
  br i1 %k.cond, label %cov.k, label %cov.k.end

cov.k.end:                                          ; preds = %cov.k.preheader, %cov.k
  %covval2 = load double, ptr %cov.ij.ptr, align 8
  %covdiv = fdiv double %covval2, %sub67
  store double %covdiv, ptr %cov.ij.ptr, align 8

  %ji.off = mul nsw i64 %oj, %m64
  %ji.elem.off = add nsw i64 %ji.off, %oi
  %ji.ptr = getelementptr inbounds double, ptr %cov, i64 %ji.elem.off
  store double %covdiv, ptr %ji.ptr, align 8

  %oj.next = add nsw i64 %oj, 1
  %j.cond = icmp slt i64 %oj.next, %m64
  br i1 %j.cond, label %cov.inner.latch, label %cov.outer.latch

cov.inner.latch:
  br label %cov.inner

cov.outer.latch:                                    ; preds = %cov.outer, %cov.inner
  %oi.next = add nsw i64 %oi, 1
  %i.cond = icmp slt i64 %oi.next, %m64
  br i1 %i.cond, label %cov.outer, label %for.end86

for.end86:                                          ; preds = %cov.outer.latch, %for.end37
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
