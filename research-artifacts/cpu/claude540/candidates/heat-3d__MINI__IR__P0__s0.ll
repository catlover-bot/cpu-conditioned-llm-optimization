; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp slt i32 %n, 3
  %cmp.t = icmp sle i32 1, 20
  %and.cond = and i1 %cmp.t, 1
  br i1 %cmp.n, label %for.end217, label %check.tsteps

check.tsteps:
  br i1 %cmp.t, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm1.64 = zext i32 %nm1 to i64
  %nsq = mul nuw i64 %n64, %n64
  br label %t.loop

t.loop:
  %t = phi i32 [ 1, %preheader ], [ %t.inc, %t.latch ]
  br label %i.loop.A

i.loop.A:
  %i.A = phi i32 [ 1, %t.loop ], [ %i.A.inc, %i.latch.A ]
  %i.A.64 = sext i32 %i.A to i64
  %ip1.A = add nsw i32 %i.A, 1
  %ip1.A.64 = sext i32 %ip1.A to i64
  %im1.A = sub nsw i32 %i.A, 1
  %im1.A.64 = sext i32 %im1.A to i64
  br label %j.loop.A

j.loop.A:
  %j.A = phi i32 [ 1, %i.loop.A ], [ %j.A.inc, %j.latch.A ]
  %j.A.64 = sext i32 %j.A to i64
  %jp1.A = add nsw i32 %j.A, 1
  %jp1.A.64 = sext i32 %jp1.A to i64
  %jm1.A = sub nsw i32 %j.A, 1
  %jm1.A.64 = sext i32 %jm1.A to i64

  %base.ip1.A = mul nsw i64 %ip1.A.64, %nsq
  %base.i.A   = mul nsw i64 %i.A.64, %nsq
  %base.im1.A = mul nsw i64 %im1.A.64, %nsq

  %row.ip1.j.A = mul nsw i64 %j.A.64, %n64
  %row.i.jp1.A = mul nsw i64 %jp1.A.64, %n64
  %row.i.j.A   = mul nsw i64 %j.A.64, %n64
  %row.i.jm1.A = mul nsw i64 %jm1.A.64, %n64

  %ptr.ip1.j.A = getelementptr inbounds double, ptr %A, i64 %base.ip1.A
  %ptr.ip1.j.A2 = getelementptr inbounds double, ptr %ptr.ip1.j.A, i64 %row.ip1.j.A

  %ptr.i.j.A = getelementptr inbounds double, ptr %A, i64 %base.i.A
  %ptr.i.j.A2 = getelementptr inbounds double, ptr %ptr.i.j.A, i64 %row.i.j.A

  %ptr.im1.j.A = getelementptr inbounds double, ptr %A, i64 %base.im1.A
  %ptr.im1.j.A2 = getelementptr inbounds double, ptr %ptr.im1.j.A, i64 %row.i.j.A

  %ptr.i.jp1.A = getelementptr inbounds double, ptr %A, i64 %base.i.A
  %ptr.i.jp1.A2 = getelementptr inbounds double, ptr %ptr.i.jp1.A, i64 %row.i.jp1.A

  %ptr.i.jm1.A = getelementptr inbounds double, ptr %A, i64 %base.i.A
  %ptr.i.jm1.A2 = getelementptr inbounds double, ptr %ptr.i.jm1.A, i64 %row.i.jm1.A

  br label %k.loop.A

k.loop.A:
  %k.A = phi i32 [ 1, %j.loop.A ], [ %k.A.inc, %k.loop.A ]
  %k.A.64 = sext i32 %k.A to i64
  %kp1.A = add nsw i32 %k.A, 1
  %kp1.A.64 = sext i32 %kp1.A to i64
  %km1.A = sub nsw i32 %k.A, 1
  %km1.A.64 = sext i32 %km1.A to i64

  %gep.ip1 = getelementptr inbounds double, ptr %ptr.ip1.j.A2, i64 %k.A.64
  %v.ip1 = load double, ptr %gep.ip1, align 8

  %gep.center = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %k.A.64
  %v.center = load double, ptr %gep.center, align 8

  %mul.c2 = fmul double 2.000000e+00, %v.center
  %sub.a = fsub double %v.ip1, %mul.c2

  %gep.im1 = getelementptr inbounds double, ptr %ptr.im1.j.A2, i64 %k.A.64
  %v.im1 = load double, ptr %gep.im1, align 8

  %add.a = fadd double %sub.a, %v.im1
  %term1 = fmul double 1.250000e-01, %add.a

  %gep.jp1 = getelementptr inbounds double, ptr %ptr.i.jp1.A2, i64 %k.A.64
  %v.jp1 = load double, ptr %gep.jp1, align 8

  %gep.center2 = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %k.A.64
  %v.center2 = load double, ptr %gep.center2, align 8

  %mul.c2b = fmul double 2.000000e+00, %v.center2
  %sub.b = fsub double %v.jp1, %mul.c2b

  %gep.jm1 = getelementptr inbounds double, ptr %ptr.i.jm1.A2, i64 %k.A.64
  %v.jm1 = load double, ptr %gep.jm1, align 8

  %add.b = fadd double %sub.b, %v.jm1
  %term2 = fmul double 1.250000e-01, %add.b

  %sum12 = fadd double %term1, %term2

  %gep.kp1 = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %kp1.A.64
  %v.kp1 = load double, ptr %gep.kp1, align 8

  %gep.center3 = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %k.A.64
  %v.center3 = load double, ptr %gep.center3, align 8

  %mul.c2c = fmul double 2.000000e+00, %v.center3
  %sub.c = fsub double %v.kp1, %mul.c2c

  %gep.km1 = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %km1.A.64
  %v.km1 = load double, ptr %gep.km1, align 8

  %add.c = fadd double %sub.c, %v.km1
  %term3 = fmul double 1.250000e-01, %add.c

  %sum123 = fadd double %sum12, %term3

  %gep.center4 = getelementptr inbounds double, ptr %ptr.i.j.A2, i64 %k.A.64
  %v.center4 = load double, ptr %gep.center4, align 8

  %result = fadd double %sum123, %v.center4

  %base.i.B = mul nsw i64 %ip1.A.64, %nsq
  %base.i.B0 = mul nsw i64 %i.A.64, %nsq
  %row.i.j.B = mul nsw i64 %j.A.64, %n64
  %ptr.out.B = getelementptr inbounds double, ptr %B, i64 %base.i.B0
  %ptr.out.B2 = getelementptr inbounds double, ptr %ptr.out.B, i64 %row.i.j.B
  %gep.out = getelementptr inbounds double, ptr %ptr.out.B2, i64 %k.A.64
  store double %result, ptr %gep.out, align 8

  %k.A.inc = add nsw i32 %k.A, 1
  %cmp.k.A = icmp slt i32 %k.A.inc, %nm1
  br i1 %cmp.k.A, label %k.loop.A, label %j.latch.A, !llvm.loop !6

j.latch.A:
  %j.A.inc = add nsw i32 %j.A, 1
  %cmp.j.A = icmp slt i32 %j.A.inc, %nm1
  br i1 %cmp.j.A, label %j.loop.A, label %i.latch.A, !llvm.loop !8

i.latch.A:
  %i.A.inc = add nsw i32 %i.A, 1
  %cmp.i.A = icmp slt i32 %i.A.inc, %nm1
  br i1 %cmp.i.A, label %i.loop.A, label %i.loop.B, !llvm.loop !9

i.loop.B:
  %i.B = phi i32 [ 1, %i.latch.A ], [ %i.B.inc, %i.latch.B ]
  %i.B.64 = sext i32 %i.B to i64
  %ip1.B = add nsw i32 %i.B, 1
  %ip1.B.64 = sext i32 %ip1.B to i64
  %im1.B = sub nsw i32 %i.B, 1
  %im1.B.64 = sext i32 %im1.B to i64
  br label %j.loop.B

j.loop.B:
  %j.B = phi i32 [ 1, %i.loop.B ], [ %j.B.inc, %j.latch.B ]
  %j.B.64 = sext i32 %j.B to i64
  %jp1.B = add nsw i32 %j.B, 1
  %jp1.B.64 = sext i32 %jp1.B to i64
  %jm1.B = sub nsw i32 %j.B, 1
  %jm1.B.64 = sext i32 %jm1.B to i64

  %base.ip1.B = mul nsw i64 %ip1.B.64, %nsq
  %base.i.Bv   = mul nsw i64 %i.B.64, %nsq
  %base.im1.B = mul nsw i64 %im1.B.64, %nsq

  %row.ip1.j.B = mul nsw i64 %j.B.64, %n64
  %row.i.jp1.B = mul nsw i64 %jp1.B.64, %n64
  %row.i.j.B   = mul nsw i64 %j.B.64, %n64
  %row.i.jm1.B = mul nsw i64 %jm1.B.64, %n64

  %ptr.ip1.j.B = getelementptr inbounds double, ptr %B, i64 %base.ip1.B
  %ptr.ip1.j.B2 = getelementptr inbounds double, ptr %ptr.ip1.j.B, i64 %row.ip1.j.B

  %ptr.i.j.B = getelementptr inbounds double, ptr %B, i64 %base.i.Bv
  %ptr.i.j.B2 = getelementptr inbounds double, ptr %ptr.i.j.B, i64 %row.i.j.B

  %ptr.im1.j.B = getelementptr inbounds double, ptr %B, i64 %base.im1.B
  %ptr.im1.j.B2 = getelementptr inbounds double, ptr %ptr.im1.j.B, i64 %row.i.j.B

  %ptr.i.jp1.B = getelementptr inbounds double, ptr %B, i64 %base.i.Bv
  %ptr.i.jp1.B2 = getelementptr inbounds double, ptr %ptr.i.jp1.B, i64 %row.i.jp1.B

  %ptr.i.jm1.B = getelementptr inbounds double, ptr %B, i64 %base.i.Bv
  %ptr.i.jm1.B2 = getelementptr inbounds double, ptr %ptr.i.jm1.B, i64 %row.i.jm1.B

  br label %k.loop.B

k.loop.B:
  %k.B = phi i32 [ 1, %j.loop.B ], [ %k.B.inc, %k.loop.B ]
  %k.B.64 = sext i32 %k.B to i64
  %kp1.B = add nsw i32 %k.B, 1
  %kp1.B.64 = sext i32 %kp1.B to i64
  %km1.B = sub nsw i32 %k.B, 1
  %km1.B.64 = sext i32 %km1.B to i64

  %gep.ip1.b = getelementptr inbounds double, ptr %ptr.ip1.j.B2, i64 %k.B.64
  %v.ip1.b = load double, ptr %gep.ip1.b, align 8

  %gep.center.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %k.B.64
  %v.center.b = load double, ptr %gep.center.b, align 8

  %mul.c2.b = fmul double 2.000000e+00, %v.center.b
  %sub.a.b = fsub double %v.ip1.b, %mul.c2.b

  %gep.im1.b = getelementptr inbounds double, ptr %ptr.im1.j.B2, i64 %k.B.64
  %v.im1.b = load double, ptr %gep.im1.b, align 8

  %add.a.b = fadd double %sub.a.b, %v.im1.b
  %term1.b = fmul double 1.250000e-01, %add.a.b

  %gep.jp1.b = getelementptr inbounds double, ptr %ptr.i.jp1.B2, i64 %k.B.64
  %v.jp1.b = load double, ptr %gep.jp1.b, align 8

  %gep.center2.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %k.B.64
  %v.center2.b = load double, ptr %gep.center2.b, align 8

  %mul.c2b.b = fmul double 2.000000e+00, %v.center2.b
  %sub.b.b = fsub double %v.jp1.b, %mul.c2b.b

  %gep.jm1.b = getelementptr inbounds double, ptr %ptr.i.jm1.B2, i64 %k.B.64
  %v.jm1.b = load double, ptr %gep.jm1.b, align 8

  %add.b.b = fadd double %sub.b.b, %v.jm1.b
  %term2.b = fmul double 1.250000e-01, %add.b.b

  %sum12.b = fadd double %term1.b, %term2.b

  %gep.kp1.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %kp1.B.64
  %v.kp1.b = load double, ptr %gep.kp1.b, align 8

  %gep.center3.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %k.B.64
  %v.center3.b = load double, ptr %gep.center3.b, align 8

  %mul.c2c.b = fmul double 2.000000e+00, %v.center3.b
  %sub.c.b = fsub double %v.kp1.b, %mul.c2c.b

  %gep.km1.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %km1.B.64
  %v.km1.b = load double, ptr %gep.km1.b, align 8

  %add.c.b = fadd double %sub.c.b, %v.km1.b
  %term3.b = fmul double 1.250000e-01, %add.c.b

  %sum123.b = fadd double %sum12.b, %term3.b

  %gep.center4.b = getelementptr inbounds double, ptr %ptr.i.j.B2, i64 %k.B.64
  %v.center4.b = load double, ptr %gep.center4.b, align 8

  %result.b = fadd double %sum123.b, %v.center4.b

  %base.i.A0 = mul nsw i64 %i.B.64, %nsq
  %row.i.j.A0 = mul nsw i64 %j.B.64, %n64
  %ptr.out.A = getelementptr inbounds double, ptr %A, i64 %base.i.A0
  %ptr.out.A2 = getelementptr inbounds double, ptr %ptr.out.A, i64 %row.i.j.A0
  %gep.out.b = getelementptr inbounds double, ptr %ptr.out.A2, i64 %k.B.64
  store double %result.b, ptr %gep.out.b, align 8

  %k.B.inc = add nsw i32 %k.B, 1
  %cmp.k.B = icmp slt i32 %k.B.inc, %nm1
  br i1 %cmp.k.B, label %k.loop.B, label %j.latch.B, !llvm.loop !10

j.latch.B:
  %j.B.inc = add nsw i32 %j.B, 1
  %cmp.j.B = icmp slt i32 %j.B.inc, %nm1
  br i1 %cmp.j.B, label %j.loop.B, label %i.latch.B, !llvm.loop !11

i.latch.B:
  %i.B.inc = add nsw i32 %i.B, 1
  %cmp.i.B = icmp slt i32 %i.B.inc, %nm1
  br i1 %cmp.i.B, label %i.loop.B, label %t.latch, !llvm.loop !12

t.latch:
  %t.inc = add nsw i32 %t, 1
  %cmp.t.loop = icmp sle i32 %t.inc, 20
  br i1 %cmp.t.loop, label %t.loop, label %for.end217, !llvm.loop !13

for.end217:
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
