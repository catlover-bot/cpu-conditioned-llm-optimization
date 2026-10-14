; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %cmp_outer = icmp sgt i32 %nm1, 1
  %cmp_t = icmp sle i32 1, 40
  br i1 %cmp_t, label %check_dims, label %for.end217

check_dims:
  br i1 %cmp_outer, label %t.preheader, label %for.end217

t.preheader:
  %nsq = mul nsw i64 %n64, %n64
  %nm1_64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc215, %t.preheader
  %t = phi i32 [ 1, %t.preheader ], [ %inc216, %for.inc215 ]
  br label %for.body

for.body:                                         ; preds = %for.cond
  br label %i.loop.A

i.loop.A:                                         ; preds = %i.inc.A, %for.body
  %i.A = phi i64 [ 1, %for.body ], [ %i.A.inc, %i.inc.A ]
  %ip1.A = add nsw i64 %i.A, 1
  %im1.A = add nsw i64 %i.A, -1
  %ibase.A = mul nsw i64 %i.A, %nsq
  %ip1base.A = mul nsw i64 %ip1.A, %nsq
  %im1base.A = mul nsw i64 %im1.A, %nsq
  %Aptr.i = getelementptr inbounds double, ptr %A, i64 %ibase.A
  %Aptr.ip1 = getelementptr inbounds double, ptr %A, i64 %ip1base.A
  %Aptr.im1 = getelementptr inbounds double, ptr %A, i64 %im1base.A
  %Bptr.i = getelementptr inbounds double, ptr %B, i64 %ibase.A
  br label %j.loop.A

j.loop.A:                                         ; preds = %j.inc.A, %i.loop.A
  %j.A = phi i64 [ 1, %i.loop.A ], [ %j.A.inc, %j.inc.A ]
  %jn.A = mul nsw i64 %j.A, %n64
  %jp1n.A = add nsw i64 %jn.A, %n64
  %jm1n.A = sub nsw i64 %jn.A, %n64
  %Arow.i = getelementptr inbounds double, ptr %Aptr.i, i64 %jn.A
  %Arow.ip1 = getelementptr inbounds double, ptr %Aptr.ip1, i64 %jn.A
  %Arow.im1 = getelementptr inbounds double, ptr %Aptr.im1, i64 %jn.A
  %Arow.jp1 = getelementptr inbounds double, ptr %Aptr.i, i64 %jp1n.A
  %Arow.jm1 = getelementptr inbounds double, ptr %Aptr.i, i64 %jm1n.A
  %Brow.i = getelementptr inbounds double, ptr %Bptr.i, i64 %jn.A
  br label %k.loop.A

k.loop.A:                                         ; preds = %k.loop.A, %j.loop.A
  %k.A = phi i64 [ 1, %j.loop.A ], [ %k.A.inc, %k.loop.A ]
  %kp1.A = add nsw i64 %k.A, 1
  %km1.A = add nsw i64 %k.A, -1

  %p.i.j.k = getelementptr inbounds double, ptr %Arow.i, i64 %k.A
  %v.i.j.k = load double, ptr %p.i.j.k, align 8

  %p.ip1.j.k = getelementptr inbounds double, ptr %Arow.ip1, i64 %k.A
  %v.ip1.j.k = load double, ptr %p.ip1.j.k, align 8
  %mul.x = fmul double 2.000000e+00, %v.i.j.k
  %sub.x = fsub double %v.ip1.j.k, %mul.x
  %p.im1.j.k = getelementptr inbounds double, ptr %Arow.im1, i64 %k.A
  %v.im1.j.k = load double, ptr %p.im1.j.k, align 8
  %add.x = fadd double %sub.x, %v.im1.j.k
  %term.x = fmul double 1.250000e-01, %add.x

  %p.i.jp1.k = getelementptr inbounds double, ptr %Arow.jp1, i64 %k.A
  %v.i.jp1.k = load double, ptr %p.i.jp1.k, align 8
  %sub.y = fsub double %v.i.jp1.k, %mul.x
  %p.i.jm1.k = getelementptr inbounds double, ptr %Arow.jm1, i64 %k.A
  %v.i.jm1.k = load double, ptr %p.i.jm1.k, align 8
  %add.y = fadd double %sub.y, %v.i.jm1.k
  %term.y = fmul double 1.250000e-01, %add.y
  %sum.xy = fadd double %term.x, %term.y

  %p.i.j.kp1 = getelementptr inbounds double, ptr %Arow.i, i64 %kp1.A
  %v.i.j.kp1 = load double, ptr %p.i.j.kp1, align 8
  %sub.z = fsub double %v.i.j.kp1, %mul.x
  %p.i.j.km1 = getelementptr inbounds double, ptr %Arow.i, i64 %km1.A
  %v.i.j.km1 = load double, ptr %p.i.j.km1, align 8
  %add.z = fadd double %sub.z, %v.i.j.km1
  %term.z = fmul double 1.250000e-01, %add.z
  %sum.xyz = fadd double %sum.xy, %term.z

  %result = fadd double %sum.xyz, %v.i.j.k

  %pB = getelementptr inbounds double, ptr %Brow.i, i64 %k.A
  store double %result, ptr %pB, align 8

  %k.A.inc = add nsw i64 %k.A, 1
  %cmp.k.A = icmp slt i64 %k.A.inc, %nm1_64
  br i1 %cmp.k.A, label %k.loop.A, label %j.inc.A, !llvm.loop !6

j.inc.A:                                          ; preds = %k.loop.A
  %j.A.inc = add nsw i64 %j.A, 1
  %cmp.j.A = icmp slt i64 %j.A.inc, %nm1_64
  br i1 %cmp.j.A, label %j.loop.A, label %i.inc.A, !llvm.loop !8

i.inc.A:                                          ; preds = %j.inc.A
  %i.A.inc = add nsw i64 %i.A, 1
  %cmp.i.A = icmp slt i64 %i.A.inc, %nm1_64
  br i1 %cmp.i.A, label %i.loop.A, label %for.end106, !llvm.loop !9

for.end106:                                       ; preds = %i.inc.A
  br label %i.loop.B

i.loop.B:                                         ; preds = %i.inc.B, %for.end106
  %i.B = phi i64 [ 1, %for.end106 ], [ %i.B.inc, %i.inc.B ]
  %ip1.B = add nsw i64 %i.B, 1
  %im1.B = add nsw i64 %i.B, -1
  %ibase.B = mul nsw i64 %i.B, %nsq
  %ip1base.B = mul nsw i64 %ip1.B, %nsq
  %im1base.B = mul nsw i64 %im1.B, %nsq
  %Bptr.i2 = getelementptr inbounds double, ptr %B, i64 %ibase.B
  %Bptr.ip1 = getelementptr inbounds double, ptr %B, i64 %ip1base.B
  %Bptr.im1 = getelementptr inbounds double, ptr %B, i64 %im1base.B
  %Aptr.i2 = getelementptr inbounds double, ptr %A, i64 %ibase.B
  br label %j.loop.B

j.loop.B:                                         ; preds = %j.inc.B, %i.loop.B
  %j.B = phi i64 [ 1, %i.loop.B ], [ %j.B.inc, %j.inc.B ]
  %jn.B = mul nsw i64 %j.B, %n64
  %jp1n.B = add nsw i64 %jn.B, %n64
  %jm1n.B = sub nsw i64 %jn.B, %n64
  %Brow.i2 = getelementptr inbounds double, ptr %Bptr.i2, i64 %jn.B
  %Brow.ip1 = getelementptr inbounds double, ptr %Bptr.ip1, i64 %jn.B
  %Brow.im1 = getelementptr inbounds double, ptr %Bptr.im1, i64 %jn.B
  %Brow.jp1 = getelementptr inbounds double, ptr %Bptr.i2, i64 %jp1n.B
  %Brow.jm1 = getelementptr inbounds double, ptr %Bptr.i2, i64 %jm1n.B
  %Arow.i2 = getelementptr inbounds double, ptr %Aptr.i2, i64 %jn.B
  br label %k.loop.B

k.loop.B:                                         ; preds = %k.loop.B, %j.loop.B
  %k.B = phi i64 [ 1, %j.loop.B ], [ %k.B.inc, %k.loop.B ]
  %kp1.B = add nsw i64 %k.B, 1
  %km1.B = add nsw i64 %k.B, -1

  %q.i.j.k = getelementptr inbounds double, ptr %Brow.i2, i64 %k.B
  %w.i.j.k = load double, ptr %q.i.j.k, align 8

  %q.ip1.j.k = getelementptr inbounds double, ptr %Brow.ip1, i64 %k.B
  %w.ip1.j.k = load double, ptr %q.ip1.j.k, align 8
  %mul2.x = fmul double 2.000000e+00, %w.i.j.k
  %sub2.x = fsub double %w.ip1.j.k, %mul2.x
  %q.im1.j.k = getelementptr inbounds double, ptr %Brow.im1, i64 %k.B
  %w.im1.j.k = load double, ptr %q.im1.j.k, align 8
  %add2.x = fadd double %sub2.x, %w.im1.j.k
  %term2.x = fmul double 1.250000e-01, %add2.x

  %q.i.jp1.k = getelementptr inbounds double, ptr %Brow.jp1, i64 %k.B
  %w.i.jp1.k = load double, ptr %q.i.jp1.k, align 8
  %sub2.y = fsub double %w.i.jp1.k, %mul2.x
  %q.i.jm1.k = getelementptr inbounds double, ptr %Brow.jm1, i64 %k.B
  %w.i.jm1.k = load double, ptr %q.i.jm1.k, align 8
  %add2.y = fadd double %sub2.y, %w.i.jm1.k
  %term2.y = fmul double 1.250000e-01, %add2.y
  %sum2.xy = fadd double %term2.x, %term2.y

  %q.i.j.kp1 = getelementptr inbounds double, ptr %Brow.i2, i64 %kp1.B
  %w.i.j.kp1 = load double, ptr %q.i.j.kp1, align 8
  %sub2.z = fsub double %w.i.j.kp1, %mul2.x
  %q.i.j.km1 = getelementptr inbounds double, ptr %Brow.i2, i64 %km1.B
  %w.i.j.km1 = load double, ptr %q.i.j.km1, align 8
  %add2.z = fadd double %sub2.z, %w.i.j.km1
  %term2.z = fmul double 1.250000e-01, %add2.z
  %sum2.xyz = fadd double %sum2.xy, %term2.z

  %result2 = fadd double %sum2.xyz, %w.i.j.k

  %pA = getelementptr inbounds double, ptr %Arow.i2, i64 %k.B
  store double %result2, ptr %pA, align 8

  %k.B.inc = add nsw i64 %k.B, 1
  %cmp.k.B = icmp slt i64 %k.B.inc, %nm1_64
  br i1 %cmp.k.B, label %k.loop.B, label %j.inc.B, !llvm.loop !10

j.inc.B:                                          ; preds = %k.loop.B
  %j.B.inc = add nsw i64 %j.B, 1
  %cmp.j.B = icmp slt i64 %j.B.inc, %nm1_64
  br i1 %cmp.j.B, label %j.loop.B, label %i.inc.B, !llvm.loop !11

i.inc.B:                                          ; preds = %j.inc.B
  %i.B.inc = add nsw i64 %i.B, 1
  %cmp.i.B = icmp slt i64 %i.B.inc, %nm1_64
  br i1 %cmp.i.B, label %i.loop.B, label %for.inc215, !llvm.loop !12

for.inc215:                                       ; preds = %i.inc.B
  %inc216 = add nsw i32 %t, 1
  %cmp = icmp sle i32 %inc216, 40
  br i1 %cmp, label %for.cond, label %for.end217, !llvm.loop !13

for.end217:                                       ; preds = %for.inc215, %check_dims, %entry
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
