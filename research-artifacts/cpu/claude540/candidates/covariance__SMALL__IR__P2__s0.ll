; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp.m0 = icmp sgt i32 %m, 0
  br i1 %cmp.m0, label %n.check, label %for.end86

n.check:
  %cmp.n0 = icmp sgt i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br label %mean.outer.preheader

mean.outer.preheader:
  br label %mean.outer

mean.outer:                                       ; preds = %mean.outer.latch, %mean.outer.preheader
  %j = phi i32 [ 0, %mean.outer.preheader ], [ %inc18, %mean.outer.latch ]
  %j64 = sext i32 %j to i64
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j64
  store double 0.000000e+00, ptr %mean.j.ptr, align 8
  br i1 %cmp.n0, label %mean.inner.preheader, label %mean.outer.latch

mean.inner.preheader:
  br label %mean.inner

mean.inner:                                        ; preds = %mean.inner, %mean.inner.preheader
  %i = phi i32 [ 0, %mean.inner.preheader ], [ %inc, %mean.inner ]
  %acc = phi double [ 0.000000e+00, %mean.inner.preheader ], [ %add14, %mean.inner ]
  %i64 = sext i32 %i to i64
  %row.off = mul nsw i64 %i64, %m64
  %data.idx = add nsw i64 %row.off, %j64
  %data.ptr = getelementptr inbounds double, ptr %data, i64 %data.idx
  %dval = load double, ptr %data.ptr, align 8
  %add14 = fadd double %acc, %dval
  %inc = add nsw i32 %i, 1
  %cmp6 = icmp slt i32 %inc, %n
  br i1 %cmp6, label %mean.inner, label %mean.inner.exit

mean.inner.exit:
  store double %add14, ptr %mean.j.ptr, align 8
  br label %mean.outer.latch

mean.outer.latch:                                  ; preds = %mean.outer, %mean.inner.exit
  %meanval = load double, ptr %mean.j.ptr, align 8
  %div = fdiv double %meanval, %float_n
  store double %div, ptr %mean.j.ptr, align 8
  %inc18 = add nsw i32 %j, 1
  %cmp = icmp slt i32 %inc18, %m
  br i1 %cmp, label %mean.outer, label %center.outer.preheader

center.outer.preheader:
  br i1 %cmp.n0, label %center.outer.preheader2, label %for.end37

center.outer.preheader2:
  br label %center.outer

center.outer:                                      ; preds = %center.inner.exit, %center.outer.preheader2
  %ci = phi i32 [ 0, %center.outer.preheader2 ], [ %inc36, %center.inner.exit ]
  %ci64 = sext i32 %ci to i64
  %crow.off = mul nsw i64 %ci64, %m64
  br label %center.inner

center.inner:                                      ; preds = %center.inner, %center.outer
  %cj = phi i32 [ 0, %center.outer ], [ %inc33, %center.inner ]
  %cj64 = sext i32 %cj to i64
  %cmean.ptr = getelementptr inbounds double, ptr %mean, i64 %cj64
  %cmeanv = load double, ptr %cmean.ptr, align 8
  %cdata.idx = add nsw i64 %crow.off, %cj64
  %cdata.ptr = getelementptr inbounds double, ptr %data, i64 %cdata.idx
  %cdataval = load double, ptr %cdata.ptr, align 8
  %csub = fsub double %cdataval, %cmeanv
  store double %csub, ptr %cdata.ptr, align 8
  %inc33 = add nsw i32 %cj, 1
  %cmp24 = icmp slt i32 %inc33, %m
  br i1 %cmp24, label %center.inner, label %center.inner.exit

center.inner.exit:
  %inc36 = add nsw i32 %ci, 1
  %cmp21 = icmp slt i32 %inc36, %n
  br i1 %cmp21, label %center.outer, label %for.end37

for.end37:                                         ; preds = %center.inner.exit, %center.outer.preheader
  br label %cov.outer

cov.outer:                                         ; preds = %cov.outer.latch, %for.end37
  %oi = phi i32 [ 0, %for.end37 ], [ %inc85, %cov.outer.latch ]
  %oi64 = sext i32 %oi to i64
  %orow.off = mul nsw i64 %oi64, %m64
  br label %cov.mid

cov.mid:                                           ; preds = %cov.mid.latch, %cov.outer
  %oj = phi i32 [ %oi, %cov.outer ], [ %inc82, %cov.mid.latch ]
  %oj64 = sext i32 %oj to i64
  %cov.i.ptr = getelementptr inbounds double, ptr %cov, i64 %orow.off
  %cov.ij.ptr = getelementptr inbounds double, ptr %cov.i.ptr, i64 %oj64
  store double 0.000000e+00, ptr %cov.ij.ptr, align 8
  br i1 %cmp.n0, label %cov.inner.preheader, label %cov.inner.exit

cov.inner.preheader:
  br label %cov.inner

cov.inner:                                         ; preds = %cov.inner, %cov.inner.preheader
  %k = phi i32 [ 0, %cov.inner.preheader ], [ %inck, %cov.inner ]
  %acc2 = phi double [ 0.000000e+00, %cov.inner.preheader ], [ %add63, %cov.inner ]
  %k64 = sext i32 %k to i64
  %krow.off = mul nsw i64 %k64, %m64
  %d1.idx = add nsw i64 %krow.off, %oi64
  %d1.ptr = getelementptr inbounds double, ptr %data, i64 %d1.idx
  %d1v = load double, ptr %d1.ptr, align 8
  %d2.idx = add nsw i64 %krow.off, %oj64
  %d2.ptr = getelementptr inbounds double, ptr %data, i64 %d2.idx
  %d2v = load double, ptr %d2.ptr, align 8
  %mulv = fmul double %d1v, %d2v
  %add63 = fadd double %acc2, %mulv
  %inck = add nsw i32 %k, 1
  %cmp49 = icmp slt i32 %inck, %n
  br i1 %cmp49, label %cov.inner, label %cov.inner.exit

cov.inner.exit:                                    ; preds = %cov.inner, %cov.mid
  %accfinal = phi double [ 0.000000e+00, %cov.mid ], [ %add63, %cov.inner ]
  store double %accfinal, ptr %cov.ij.ptr, align 8
  %sub67 = fsub double %float_n, 1.000000e+00
  %covval = load double, ptr %cov.ij.ptr, align 8
  %div72 = fdiv double %covval, %sub67
  store double %div72, ptr %cov.ij.ptr, align 8
  %symval = load double, ptr %cov.ij.ptr, align 8
  %cov.j.ptr = getelementptr inbounds double, ptr %cov, i64 %oj64
  %mrow.off = mul nsw i64 %oj64, %m64
  %cov.j.ptr2 = getelementptr inbounds double, ptr %cov, i64 %mrow.off
  %cov.ji.ptr = getelementptr inbounds double, ptr %cov.j.ptr2, i64 %oi64
  store double %symval, ptr %cov.ji.ptr, align 8
  br label %cov.mid.latch

cov.mid.latch:                                     ; preds = %cov.inner.exit
  %inc82 = add nsw i32 %oj, 1
  %cmp24b = icmp slt i32 %inc82, %m
  br i1 %cmp24b, label %cov.mid, label %cov.outer.latch

cov.outer.latch:                                   ; preds = %cov.mid.latch
  %inc85 = add nsw i32 %oi, 1
  %cmp39 = icmp slt i32 %inc85, %m
  br i1 %cmp39, label %cov.outer, label %for.end86

for.end86:                                         ; preds = %cov.outer.latch, %entry
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
