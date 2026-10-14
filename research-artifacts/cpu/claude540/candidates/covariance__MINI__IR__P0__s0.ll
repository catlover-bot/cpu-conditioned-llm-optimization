; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %cmp.mn = icmp sgt i32 %m, 0
  %cmp.nn = icmp sgt i32 %n, 0
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  br i1 %cmp.mn, label %meanloop.outer.preheader, label %for.end19

meanloop.outer.preheader:
  br label %meanloop.outer

meanloop.outer:                                    ; preds = %meanloop.outer.preheader, %meanloop.outer.end
  %j1 = phi i64 [ 0, %meanloop.outer.preheader ], [ %j1.next, %meanloop.outer.end ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  store double 0.000000e+00, ptr %mean.j.ptr, align 8
  br i1 %cmp.nn, label %meanloop.inner.preheader, label %meanloop.outer.end

meanloop.inner.preheader:
  br label %meanloop.inner

meanloop.inner:                                    ; preds = %meanloop.inner.preheader, %meanloop.inner
  %i1 = phi i64 [ 0, %meanloop.inner.preheader ], [ %i1.next, %meanloop.inner ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %dataidx1 = add nsw i64 %rowoff1, %j1
  %data.ptr1 = getelementptr inbounds double, ptr %data, i64 %dataidx1
  %dval1 = load double, ptr %data.ptr1, align 8
  %mval1 = load double, ptr %mean.j.ptr, align 8
  %addval1 = fadd double %mval1, %dval1
  store double %addval1, ptr %mean.j.ptr, align 8
  %i1.next = add nsw i64 %i1, 1
  %cmp.inner1 = icmp slt i64 %i1.next, %n64
  br i1 %cmp.inner1, label %meanloop.inner, label %meanloop.outer.end

meanloop.outer.end:                                 ; preds = %meanloop.inner, %meanloop.outer
  %meanval = load double, ptr %mean.j.ptr, align 8
  %divval = fdiv double %meanval, %float_n
  store double %divval, ptr %mean.j.ptr, align 8
  %j1.next = add nsw i64 %j1, 1
  %cmp.outer1 = icmp slt i64 %j1.next, %m64
  br i1 %cmp.outer1, label %meanloop.outer, label %for.end19

for.end19:                                          ; preds = %meanloop.outer.end, %entry
  br i1 %cmp.nn, label %centerloop.outer.preheader, label %for.end37

centerloop.outer.preheader:
  br label %centerloop.outer

centerloop.outer:                                   ; preds = %centerloop.outer.preheader, %centerloop.outer.end
  %i2 = phi i64 [ 0, %centerloop.outer.preheader ], [ %i2.next, %centerloop.outer.end ]
  %rowoff2 = mul nsw i64 %i2, %m64
  br i1 %cmp.mn, label %centerloop.inner.preheader, label %centerloop.outer.end

centerloop.inner.preheader:
  br label %centerloop.inner

centerloop.inner:                                   ; preds = %centerloop.inner.preheader, %centerloop.inner
  %j2 = phi i64 [ 0, %centerloop.inner.preheader ], [ %j2.next, %centerloop.inner ]
  %mean.ptr2 = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.ptr2, align 8
  %dataidx2 = add nsw i64 %rowoff2, %j2
  %data.ptr2 = getelementptr inbounds double, ptr %data, i64 %dataidx2
  %dval2 = load double, ptr %data.ptr2, align 8
  %subval2 = fsub double %dval2, %meanval2
  store double %subval2, ptr %data.ptr2, align 8
  %j2.next = add nsw i64 %j2, 1
  %cmp.inner2 = icmp slt i64 %j2.next, %m64
  br i1 %cmp.inner2, label %centerloop.inner, label %centerloop.outer.end

centerloop.outer.end:                               ; preds = %centerloop.inner, %centerloop.outer
  %i2.next = add nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %n64
  br i1 %cmp.outer2, label %centerloop.outer, label %for.end37

for.end37:                                          ; preds = %centerloop.outer.end, %for.end19
  %fnm1 = fsub double %float_n, 1.000000e+00
  br i1 %cmp.mn, label %covloop.i.preheader, label %for.end86

covloop.i.preheader:
  br label %covloop.i

covloop.i:                                          ; preds = %covloop.i.preheader, %covloop.i.end
  %i3 = phi i64 [ 0, %covloop.i.preheader ], [ %i3.next, %covloop.i.end ]
  %rowoff.i3 = mul nsw i64 %i3, %m64
  %cmp.jm = icmp slt i64 %i3, %m64
  br i1 %cmp.jm, label %covloop.j.preheader, label %covloop.i.end

covloop.j.preheader:
  br label %covloop.j

covloop.j:                                          ; preds = %covloop.j.preheader, %covloop.k.end
  %j3 = phi i64 [ %i3, %covloop.j.preheader ], [ %j3.next, %covloop.k.end ]
  %cov.i.rowoff = mul nsw i64 %i3, %m64
  %cov.ij.idx = add nsw i64 %cov.i.rowoff, %j3
  %cov.ij.ptr = getelementptr inbounds double, ptr %cov, i64 %cov.ij.idx
  store double 0.000000e+00, ptr %cov.ij.ptr, align 8
  br i1 %cmp.nn, label %covloop.k.preheader, label %covloop.k.end

covloop.k.preheader:
  br label %covloop.k

covloop.k:                                          ; preds = %covloop.k.preheader, %covloop.k
  %k3 = phi i64 [ 0, %covloop.k.preheader ], [ %k3.next, %covloop.k ]
  %rowoff.k3 = mul nsw i64 %k3, %m64
  %dataidx.ki = add nsw i64 %rowoff.k3, %i3
  %data.ki.ptr = getelementptr inbounds double, ptr %data, i64 %dataidx.ki
  %dval.ki = load double, ptr %data.ki.ptr, align 8
  %dataidx.kj = add nsw i64 %rowoff.k3, %j3
  %data.kj.ptr = getelementptr inbounds double, ptr %data, i64 %dataidx.kj
  %dval.kj = load double, ptr %data.kj.ptr, align 8
  %mulval = fmul double %dval.ki, %dval.kj
  %covval = load double, ptr %cov.ij.ptr, align 8
  %addval3 = fadd double %covval, %mulval
  store double %addval3, ptr %cov.ij.ptr, align 8
  %k3.next = add nsw i64 %k3, 1
  %cmp.k3 = icmp slt i64 %k3.next, %n64
  br i1 %cmp.k3, label %covloop.k, label %covloop.k.end

covloop.k.end:                                      ; preds = %covloop.k, %covloop.j
  %covval2 = load double, ptr %cov.ij.ptr, align 8
  %divval2 = fdiv double %covval2, %fnm1
  store double %divval2, ptr %cov.ij.ptr, align 8
  %cov.ji.rowoff = mul nsw i64 %j3, %m64
  %cov.ji.idx = add nsw i64 %cov.ji.rowoff, %i3
  %cov.ji.ptr = getelementptr inbounds double, ptr %cov, i64 %cov.ji.idx
  store double %divval2, ptr %cov.ji.ptr, align 8
  %j3.next = add nsw i64 %j3, 1
  %cmp.j3 = icmp slt i64 %j3.next, %m64
  br i1 %cmp.j3, label %covloop.j, label %covloop.i.end

covloop.i.end:                                      ; preds = %covloop.k.end, %covloop.i
  %i3.next = add nsw i64 %i3, 1
  %cmp.i3 = icmp slt i64 %i3.next, %m64
  br i1 %cmp.i3, label %covloop.i, label %for.end86

for.end86:                                          ; preds = %covloop.i.end, %for.end37
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
