; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.tsteps = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.tsteps
  br i1 %run, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm1.64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:
  %t = phi i32 [ 1, %preheader ], [ %inc216, %for.inc215 ]
  br label %for.cond6.preheader

for.cond6.preheader:
  br label %for.body8.preheader.i

for.body8.preheader.i:
  %i = phi i64 [ 1, %for.cond6.preheader ], [ %i.next, %for.inc104 ]
  %ip1 = add nuw nsw i64 %i, 1
  %im1 = sub nsw i64 %i, 1
  %ibase = mul nsw i64 %i, %n64
  %ibase = mul nsw i64 %ibase, %n64
  %ip1base = mul nsw i64 %ip1, %n64
  %ip1base = mul nsw i64 %ip1base, %n64
  %im1base = mul nsw i64 %im1, %n64
  %im1base = mul nsw i64 %im1base, %n64
  br label %for.body12.preheader.i

for.body12.preheader.i:
  %j = phi i64 [ 1, %for.body8.preheader.i ], [ %j.next, %for.inc101 ]
  %jp1 = add nuw nsw i64 %j, 1
  %jm1 = sub nsw i64 %j, 1
  %jbase = mul nsw i64 %j, %n64
  %jp1base = mul nsw i64 %jp1, %n64
  %jm1base = mul nsw i64 %jm1, %n64
  %rowc = add nsw i64 %ibase, %jbase
  %rowip1 = add nsw i64 %ip1base, %jbase
  %rowim1 = add nsw i64 %im1base, %jbase
  %rowjp1 = add nsw i64 %ibase, %jp1base
  %rowjm1 = add nsw i64 %ibase, %jm1base
  %ptrc.A = getelementptr inbounds double, ptr %A, i64 %rowc
  %ptrip1.A = getelementptr inbounds double, ptr %A, i64 %rowip1
  %ptrim1.A = getelementptr inbounds double, ptr %A, i64 %rowim1
  %ptrjp1.A = getelementptr inbounds double, ptr %A, i64 %rowjp1
  %ptrjm1.A = getelementptr inbounds double, ptr %A, i64 %rowjm1
  %ptrc.B = getelementptr inbounds double, ptr %B, i64 %rowc
  br label %for.body16

for.body16:
  %k = phi i64 [ 1, %for.body12.preheader.i ], [ %k.next, %for.body16 ]

  %a.c = getelementptr inbounds double, ptr %ptrc.A, i64 %k
  %a.ip1 = getelementptr inbounds double, ptr %ptrip1.A, i64 %k
  %a.im1 = getelementptr inbounds double, ptr %ptrim1.A, i64 %k
  %a.jp1 = getelementptr inbounds double, ptr %ptrjp1.A, i64 %k
  %a.jm1 = getelementptr inbounds double, ptr %ptrjm1.A, i64 %k
  %kp1 = add nuw nsw i64 %k, 1
  %km1 = sub nsw i64 %k, 1
  %a.kp1 = getelementptr inbounds double, ptr %ptrc.A, i64 %kp1
  %a.km1 = getelementptr inbounds double, ptr %ptrc.A, i64 %km1

  %v.ip1 = load double, ptr %a.ip1, align 8
  %v.c1 = load double, ptr %a.c, align 8
  %mul1 = fmul double 2.000000e+00, %v.c1
  %sub1 = fsub double %v.ip1, %mul1
  %v.im1 = load double, ptr %a.im1, align 8
  %add1 = fadd double %sub1, %v.im1
  %term1 = fmul double 1.250000e-01, %add1

  %v.jp1 = load double, ptr %a.jp1, align 8
  %v.c2 = load double, ptr %a.c, align 8
  %mul2 = fmul double 2.000000e+00, %v.c2
  %sub2 = fsub double %v.jp1, %mul2
  %v.jm1 = load double, ptr %a.jm1, align 8
  %add2 = fadd double %sub2, %v.jm1
  %term2 = fmul double 1.250000e-01, %add2

  %sum12 = fadd double %term1, %term2

  %v.kp1 = load double, ptr %a.kp1, align 8
  %v.c3 = load double, ptr %a.c, align 8
  %mul3 = fmul double 2.000000e+00, %v.c3
  %sub3 = fsub double %v.kp1, %mul3
  %v.km1 = load double, ptr %a.km1, align 8
  %add3 = fadd double %sub3, %v.km1
  %term3 = fmul double 1.250000e-01, %add3

  %sum123 = fadd double %sum12, %term3

  %v.c4 = load double, ptr %a.c, align 8
  %total = fadd double %sum123, %v.c4

  %b.c = getelementptr inbounds double, ptr %ptrc.B, i64 %k
  store double %total, ptr %b.c, align 8

  %k.next = add nuw nsw i64 %k, 1
  %kcmp = icmp slt i64 %k.next, %nm1.64
  br i1 %kcmp, label %for.body16, label %for.end.k

for.end.k:
  br label %for.inc101

for.inc101:
  %j.next = add nuw nsw i64 %j, 1
  %jcmp = icmp slt i64 %j.next, %nm1.64
  br i1 %jcmp, label %for.body12.preheader.i, label %for.end103

for.end103:
  br label %for.inc104

for.inc104:
  %i.next = add nuw nsw i64 %i, 1
  %icmp = icmp slt i64 %i.next, %nm1.64
  br i1 %icmp, label %for.body8.preheader.i, label %for.end106

for.end106:
  br label %for.body110.preheader.i

for.body110.preheader.i:
  %i2 = phi i64 [ 1, %for.end106 ], [ %i2.next, %for.inc212 ]
  %i2p1 = add nuw nsw i64 %i2, 1
  %i2m1 = sub nsw i64 %i2, 1
  %i2base = mul nsw i64 %i2, %n64
  %i2base2 = mul nsw i64 %i2base, %n64
  %i2p1base = mul nsw i64 %i2p1, %n64
  %i2p1base2 = mul nsw i64 %i2p1base, %n64
  %i2m1base = mul nsw i64 %i2m1, %n64
  %i2m1base2 = mul nsw i64 %i2m1base, %n64
  br label %for.body114.preheader.i

for.body114.preheader.i:
  %j2 = phi i64 [ 1, %for.body110.preheader.i ], [ %j2.next, %for.inc209 ]
  %j2p1 = add nuw nsw i64 %j2, 1
  %j2m1 = sub nsw i64 %j2, 1
  %j2base = mul nsw i64 %j2, %n64
  %j2p1base = mul nsw i64 %j2p1, %n64
  %j2m1base = mul nsw i64 %j2m1, %n64
  %row2c = add nsw i64 %i2base2, %j2base
  %row2ip1 = add nsw i64 %i2p1base2, %j2base
  %row2im1 = add nsw i64 %i2m1base2, %j2base
  %row2jp1 = add nsw i64 %i2base2, %j2p1base
  %row2jm1 = add nsw i64 %i2base2, %j2m1base
  %ptr2c.B = getelementptr inbounds double, ptr %B, i64 %row2c
  %ptr2ip1.B = getelementptr inbounds double, ptr %B, i64 %row2ip1
  %ptr2im1.B = getelementptr inbounds double, ptr %B, i64 %row2im1
  %ptr2jp1.B = getelementptr inbounds double, ptr %B, i64 %row2jp1
  %ptr2jm1.B = getelementptr inbounds double, ptr %B, i64 %row2jm1
  %ptr2c.A = getelementptr inbounds double, ptr %A, i64 %row2c
  br label %for.body118

for.body118:
  %k2 = phi i64 [ 1, %for.body114.preheader.i ], [ %k2.next, %for.body118 ]

  %b.c = getelementptr inbounds double, ptr %ptr2c.B, i64 %k2
  %b.ip1 = getelementptr inbounds double, ptr %ptr2ip1.B, i64 %k2
  %b.im1 = getelementptr inbounds double, ptr %ptr2im1.B, i64 %k2
  %b.jp1 = getelementptr inbounds double, ptr %ptr2jp1.B, i64 %k2
  %b.jm1 = getelementptr inbounds double, ptr %ptr2jm1.B, i64 %k2
  %k2p1 = add nuw nsw i64 %k2, 1
  %k2m1 = sub nsw i64 %k2, 1
  %b.kp1 = getelementptr inbounds double, ptr %ptr2c.B, i64 %k2p1
  %b.km1 = getelementptr inbounds double, ptr %ptr2c.B, i64 %k2m1

  %w.ip1 = load double, ptr %b.ip1, align 8
  %w.c1 = load double, ptr %b.c, align 8
  %wmul1 = fmul double 2.000000e+00, %w.c1
  %wsub1 = fsub double %w.ip1, %wmul1
  %w.im1 = load double, ptr %b.im1, align 8
  %wadd1 = fadd double %wsub1, %w.im1
  %wterm1 = fmul double 1.250000e-01, %wadd1

  %w.jp1 = load double, ptr %b.jp1, align 8
  %w.c2 = load double, ptr %b.c, align 8
  %wmul2 = fmul double 2.000000e+00, %w.c2
  %wsub2 = fsub double %w.jp1, %wmul2
  %w.jm1 = load double, ptr %b.jm1, align 8
  %wadd2 = fadd double %wsub2, %w.jm1
  %wterm2 = fmul double 1.250000e-01, %wadd2

  %wsum12 = fadd double %wterm1, %wterm2

  %w.kp1 = load double, ptr %b.kp1, align 8
  %w.c3 = load double, ptr %b.c, align 8
  %wmul3 = fmul double 2.000000e+00, %w.c3
  %wsub3 = fsub double %w.kp1, %wmul3
  %w.km1 = load double, ptr %b.km1, align 8
  %wadd3 = fadd double %wsub3, %w.km1
  %wterm3 = fmul double 1.250000e-01, %wadd3

  %wsum123 = fadd double %wsum12, %wterm3

  %w.c4 = load double, ptr %b.c, align 8
  %wtotal = fadd double %wsum123, %w.c4

  %a.c = getelementptr inbounds double, ptr %ptr2c.A, i64 %k2
  store double %wtotal, ptr %a.c, align 8

  %k2.next = add nuw nsw i64 %k2, 1
  %k2cmp = icmp slt i64 %k2.next, %nm1.64
  br i1 %k2cmp, label %for.body118, label %for.end.k2

for.end.k2:
  br label %for.inc209

for.inc209:
  %j2.next = add nuw nsw i64 %j2, 1
  %j2cmp = icmp slt i64 %j2.next, %nm1.64
  br i1 %j2cmp, label %for.body114.preheader.i, label %for.end211

for.end211:
  br label %for.inc212

for.inc212:
  %i2.next = add nuw nsw i64 %i2, 1
  %i2cmp = icmp slt i64 %i2.next, %nm1.64
  br i1 %i2cmp, label %for.body110.preheader.i, label %for.end214

for.end214:
  br label %for.inc215

for.inc215:
  %inc216 = add nsw i32 %t, 1
  %tcmp = icmp sle i32 %inc216, 20
  br i1 %tcmp, label %for.cond, label %for.end217.loopexit

for.end217.loopexit:
  br label %for.end217

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
