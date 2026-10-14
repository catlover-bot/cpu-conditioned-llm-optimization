; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_covariance(i32 noundef %m, i32 noundef %n, double noundef %float_n, ptr noundef %data, ptr noundef %cov, ptr noundef %mean) #0 {
entry:
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64

  %mcmp0 = icmp sgt i32 %m, 0
  br i1 %mcmp0, label %loop1.preheader, label %loop3.check

loop1.preheader:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %loop1.j

loop1.j:                                          ; preds = %loop1.preheader, %loop1.j.inc
  %j1 = phi i64 [ 0, %loop1.preheader ], [ %j1.next, %loop1.j.inc ]
  %mean.j.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  br i1 %ncmp0, label %loop1.i.preheader, label %loop1.after

loop1.i.preheader:
  br label %loop1.i

loop1.i:                                          ; preds = %loop1.i.preheader, %loop1.i
  %i1 = phi i64 [ 0, %loop1.i.preheader ], [ %i1.next, %loop1.i ]
  %sum1 = phi double [ 0.000000e+00, %loop1.i.preheader ], [ %sum1.next, %loop1.i ]
  %row.off = mul nsw i64 %i1, %m64
  %data.idx = add i64 %row.off, %j1
  %data.ptr = getelementptr inbounds double, ptr %data, i64 %data.idx
  %dval = load double, ptr %data.ptr, align 8
  %sum1.next = fadd double %sum1, %dval
  %i1.next = add nsw i64 %i1, 1
  %i1cmp = icmp slt i64 %i1.next, %n64
  br i1 %i1cmp, label %loop1.i, label %loop1.i.exit

loop1.i.exit:
  store double %sum1.next, ptr %mean.j.ptr, align 8
  br label %loop1.after

loop1.after:                                      ; preds = %loop1.i.exit, %loop1.j
  %meanval.pre = phi double [ 0.000000e+00, %loop1.j ], [ %sum1.next, %loop1.i.exit ]
  %divv = fdiv double %meanval.pre, %float_n
  store double %divv, ptr %mean.j.ptr, align 8
  br label %loop1.j.inc

loop1.j.inc:
  %j1.next = add nsw i64 %j1, 1
  %j1cmp = icmp slt i64 %j1.next, %m64
  br i1 %j1cmp, label %loop1.j, label %loop3.check

loop3.check:                                      ; preds = %loop1.j.inc, %entry
  %ncmp1 = icmp sgt i32 %n, 0
  br i1 %ncmp1, label %loop3.i.preheader, label %loop5.check

loop3.i.preheader:
  br label %loop3.i

loop3.i:                                          ; preds = %loop3.i.preheader, %loop3.i.inc
  %i3 = phi i64 [ 0, %loop3.i.preheader ], [ %i3.next, %loop3.i.inc ]
  %row3.off = mul nsw i64 %i3, %m64
  br i1 %mcmp0, label %loop3.j.preheader, label %loop3.i.inc

loop3.j.preheader:
  br label %loop3.j

loop3.j:                                          ; preds = %loop3.j.preheader, %loop3.j
  %j3 = phi i64 [ 0, %loop3.j.preheader ], [ %j3.next, %loop3.j ]
  %mean3.ptr = getelementptr inbounds double, ptr %mean, i64 %j3
  %mean3val = load double, ptr %mean3.ptr, align 8
  %data3.idx = add i64 %row3.off, %j3
  %data3.ptr = getelementptr inbounds double, ptr %data, i64 %data3.idx
  %data3val = load double, ptr %data3.ptr, align 8
  %sub3 = fsub double %data3val, %mean3val
  store double %sub3, ptr %data3.ptr, align 8
  %j3.next = add nsw i64 %j3, 1
  %j3cmp = icmp slt i64 %j3.next, %m64
  br i1 %j3cmp, label %loop3.j, label %loop3.i.inc

loop3.i.inc:                                      ; preds = %loop3.i, %loop3.j
  %i3.next = add nsw i64 %i3, 1
  %i3cmp = icmp slt i64 %i3.next, %n64
  br i1 %i3cmp, label %loop3.i, label %loop5.check

loop5.check:                                      ; preds = %loop3.i.inc, %loop3.check
  br i1 %mcmp0, label %loop5.i.preheader, label %loop5.end

loop5.i.preheader:
  %ncmp2 = icmp sgt i32 %n, 0
  %fnm1 = fsub double %float_n, 1.000000e+00
  br label %loop5.i

loop5.i:                                          ; preds = %loop5.i.preheader, %loop5.i.inc
  %i5 = phi i64 [ 0, %loop5.i.preheader ], [ %i5.next, %loop5.i.inc ]
  %cov.row.i.off = mul nsw i64 %i5, %m64
  %jcmp5 = icmp slt i64 %i5, %m64
  br i1 %jcmp5, label %loop5.j.preheader, label %loop5.i.inc

loop5.j.preheader:
  br label %loop5.j

loop5.j:                                          ; preds = %loop5.j.preheader, %loop5.j.exit
  %j5 = phi i64 [ %i5, %loop5.j.preheader ], [ %j5.next, %loop5.j.exit ]
  %cov.idx.ij = add i64 %cov.row.i.off, %j5
  %cov.ptr.ij = getelementptr inbounds double, ptr %cov, i64 %cov.idx.ij
  br i1 %ncmp2, label %loop5.k.preheader, label %loop5.k.zero

loop5.k.zero:
  br label %loop5.j.exit

loop5.k.preheader:
  br label %loop5.k

loop5.k:                                          ; preds = %loop5.k.preheader, %loop5.k
  %k5 = phi i64 [ 0, %loop5.k.preheader ], [ %k5.next, %loop5.k ]
  %sum5 = phi double [ 0.000000e+00, %loop5.k.preheader ], [ %sum5.next, %loop5.k ]
  %row.k.off = mul nsw i64 %k5, %m64
  %idx.ki = add i64 %row.k.off, %i5
  %ptr.ki = getelementptr inbounds double, ptr %data, i64 %idx.ki
  %val.ki = load double, ptr %ptr.ki, align 8
  %idx.kj = add i64 %row.k.off, %j5
  %ptr.kj = getelementptr inbounds double, ptr %data, i64 %idx.kj
  %val.kj = load double, ptr %ptr.kj, align 8
  %mulkij = fmul double %val.ki, %val.kj
  %sum5.next = fadd double %sum5, %mulkij
  %k5.next = add nsw i64 %k5, 1
  %k5cmp = icmp slt i64 %k5.next, %n64
  br i1 %k5cmp, label %loop5.k, label %loop5.k.exit

loop5.k.exit:
  br label %loop5.j.exit

loop5.j.exit:                                     ; preds = %loop5.k.zero, %loop5.k.exit
  %sumfinal = phi double [ 0.000000e+00, %loop5.k.zero ], [ %sum5.next, %loop5.k.exit ]
  %divfin = fdiv double %sumfinal, %fnm1
  store double %divfin, ptr %cov.ptr.ij, align 8
  %cov.row.j.off = mul nsw i64 %j5, %m64
  %cov.idx.ji = add i64 %cov.row.j.off, %i5
  %cov.ptr.ji = getelementptr inbounds double, ptr %cov, i64 %cov.idx.ji
  store double %divfin, ptr %cov.ptr.ji, align 8
  %j5.next = add nsw i64 %j5, 1
  %j5cmp = icmp slt i64 %j5.next, %m64
  br i1 %j5cmp, label %loop5.j, label %loop5.i.inc

loop5.i.inc:                                      ; preds = %loop5.i, %loop5.j.exit
  %i5.next = add nsw i64 %i5, 1
  %i5cmp = icmp slt i64 %i5.next, %m64
  br i1 %i5cmp, label %loop5.i, label %loop5.end

loop5.end:                                        ; preds = %loop5.i.inc, %loop5.check
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
