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
  br i1 %mcmp0, label %ph1, label %for.end19

ph1:
  %ncmp0 = icmp sgt i32 %n, 0
  br label %for.body.j1

for.body.j1:                                      ; preds = %for.inc17, %ph1
  %j1 = phi i64 [ 0, %ph1 ], [ %j1.next, %for.inc17 ]
  %mean.j1.ptr = getelementptr inbounds double, ptr %mean, i64 %j1
  store double 0.000000e+00, ptr %mean.j1.ptr, align 8
  br i1 %ncmp0, label %for.body.i1.preheader, label %for.end

for.body.i1.preheader:
  br label %for.body.i1

for.body.i1:                                      ; preds = %for.body.i1, %for.body.i1.preheader
  %i1 = phi i64 [ 0, %for.body.i1.preheader ], [ %i1.next, %for.body.i1 ]
  %acc1 = phi double [ 0.000000e+00, %for.body.i1.preheader ], [ %acc1.next, %for.body.i1 ]
  %rowoff1 = mul nsw i64 %i1, %m64
  %dataidx1 = getelementptr inbounds double, ptr %data, i64 %rowoff1
  %elptr1 = getelementptr inbounds double, ptr %dataidx1, i64 %j1
  %el1 = load double, ptr %elptr1, align 8
  %acc1.next = fadd double %acc1, %el1
  %i1.next = add nsw i64 %i1, 1
  %cmp1 = icmp slt i64 %i1.next, %n64
  br i1 %cmp1, label %for.body.i1, label %for.end.loopexit

for.end.loopexit:
  %acc1.lcssa = phi double [ %acc1.next, %for.body.i1 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body.j1
  %meanval.pre = phi double [ 0.000000e+00, %for.body.j1 ], [ %acc1.lcssa, %for.end.loopexit ]
  %div = fdiv double %meanval.pre, %float_n
  store double %div, ptr %mean.j1.ptr, align 8
  br label %for.inc17

for.inc17:                                        ; preds = %for.end
  %j1.next = add nsw i64 %j1, 1
  %cmp.j1 = icmp slt i64 %j1.next, %m64
  br i1 %cmp.j1, label %for.body.j1, label %for.end19

for.end19:                                        ; preds = %for.inc17, %entry
  br i1 %mcmp0, label %ph2, label %for.end37

ph2:
  %ncmp2 = icmp sgt i32 %n, 0
  br i1 %ncmp2, label %for.body.i2.preheader, label %for.end37

for.body.i2.preheader:
  br label %for.body.i2

for.body.i2:                                      ; preds = %for.inc35, %for.body.i2.preheader
  %i2 = phi i64 [ 0, %for.body.i2.preheader ], [ %i2.next, %for.inc35 ]
  %rowoff2 = mul nsw i64 %i2, %m64
  %dataidx2 = getelementptr inbounds double, ptr %data, i64 %rowoff2
  br label %for.body.j2

for.body.j2:                                      ; preds = %for.body.j2, %for.body.i2
  %j2 = phi i64 [ 0, %for.body.i2 ], [ %j2.next, %for.body.j2 ]
  %mean.j2.ptr = getelementptr inbounds double, ptr %mean, i64 %j2
  %meanval2 = load double, ptr %mean.j2.ptr, align 8
  %elptr2 = getelementptr inbounds double, ptr %dataidx2, i64 %j2
  %el2 = load double, ptr %elptr2, align 8
  %sub = fsub double %el2, %meanval2
  store double %sub, ptr %elptr2, align 8
  %j2.next = add nsw i64 %j2, 1
  %cmp.j2 = icmp slt i64 %j2.next, %m64
  br i1 %cmp.j2, label %for.body.j2, label %for.inc35

for.inc35:                                        ; preds = %for.body.j2
  %i2.next = add nsw i64 %i2, 1
  %cmp.i2 = icmp slt i64 %i2.next, %n64
  br i1 %cmp.i2, label %for.body.i2, label %for.end37

for.end37:                                        ; preds = %for.inc35, %ph2, %for.end19
  br i1 %mcmp0, label %ph3, label %for.end86

ph3:
  %ncmp3 = icmp sgt i32 %n, 0
  %nm1 = fsub double %float_n, 1.000000e+00
  br label %for.body.i3

for.body.i3:                                      ; preds = %for.inc84, %ph3
  %i3 = phi i64 [ 0, %ph3 ], [ %i3.next, %for.inc84 ]
  %covrowoff = mul nsw i64 %i3, %m64
  %covrowptr = getelementptr inbounds double, ptr %cov, i64 %covrowoff
  br label %for.body.j3

for.body.j3:                                      ; preds = %for.inc81, %for.body.i3
  %j3 = phi i64 [ %i3, %for.body.i3 ], [ %j3.next, %for.inc81 ]
  %covij.ptr = getelementptr inbounds double, ptr %covrowptr, i64 %j3
  br i1 %ncmp3, label %for.body.k3.preheader, label %for.end66

for.body.k3.preheader:
  br label %for.body.k3

for.body.k3:                                      ; preds = %for.body.k3, %for.body.k3.preheader
  %k3 = phi i64 [ 0, %for.body.k3.preheader ], [ %k3.next, %for.body.k3 ]
  %acc3 = phi double [ 0.000000e+00, %for.body.k3.preheader ], [ %acc3.next, %for.body.k3 ]
  %krowoff = mul nsw i64 %k3, %m64
  %krowptr = getelementptr inbounds double, ptr %data, i64 %krowoff
  %ki.ptr = getelementptr inbounds double, ptr %krowptr, i64 %i3
  %ki.val = load double, ptr %ki.ptr, align 8
  %kj.ptr = getelementptr inbounds double, ptr %krowptr, i64 %j3
  %kj.val = load double, ptr %kj.ptr, align 8
  %mul = fmul double %ki.val, %kj.val
  %acc3.next = fadd double %acc3, %mul
  %k3.next = add nsw i64 %k3, 1
  %cmp.k3 = icmp slt i64 %k3.next, %n64
  br i1 %cmp.k3, label %for.body.k3, label %for.end66.loopexit

for.end66.loopexit:
  %acc3.lcssa = phi double [ %acc3.next, %for.body.k3 ]
  br label %for.end66

for.end66:                                        ; preds = %for.end66.loopexit, %for.body.j3
  %covval.pre = phi double [ 0.000000e+00, %for.body.j3 ], [ %acc3.lcssa, %for.end66.loopexit ]
  %div72 = fdiv double %covval.pre, %nm1
  store double %div72, ptr %covij.ptr, align 8
  %covji.rowoff = mul nsw i64 %j3, %m64
  %covji.rowptr = getelementptr inbounds double, ptr %cov, i64 %covji.rowoff
  %covji.ptr = getelementptr inbounds double, ptr %covji.rowptr, i64 %i3
  store double %div72, ptr %covji.ptr, align 8
  br label %for.inc81

for.inc81:                                        ; preds = %for.end66
  %j3.next = add nsw i64 %j3, 1
  %cmp.j3 = icmp slt i64 %j3.next, %m64
  br i1 %cmp.j3, label %for.body.j3, label %for.inc84

for.inc84:                                        ; preds = %for.inc81
  %i3.next = add nsw i64 %i3, 1
  %cmp.i3 = icmp slt i64 %i3.next, %m64
  br i1 %cmp.i3, label %for.body.i3, label %for.end86

for.end86:                                        ; preds = %for.inc84, %ph3, %for.end37
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
