; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1.64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc215, %preheader
  %t = phi i32 [ 1, %preheader ], [ %inc216, %for.inc215 ]
  %cmp = icmp sle i32 %t, 100
  br i1 %cmp, label %pass1.i.header, label %for.end217

; ---------------- Pass 1: compute B from A ----------------
pass1.i.header:
  br label %pass1.i.cond

pass1.i.cond:
  %i1 = phi i64 [ 1, %pass1.i.header ], [ %i1.inc, %pass1.i.latch ]
  %cmp.i1 = icmp slt i64 %i1, %nm1.64
  br i1 %cmp.i1, label %pass1.j.header, label %pass1.end

pass1.j.header:
  %ip1 = add nsw i64 %i1, 1
  %im1 = add nsw i64 %i1, -1
  %i.base = mul i64 %i1, %n64
  %i.base = mul i64 %i.base, %n64
  %ip1.base = mul i64 %ip1, %n64
  %ip1.base2 = mul i64 %ip1.base, %n64
  %im1.base = mul i64 %im1, %n64
  %im1.base2 = mul i64 %im1.base, %n64
  br label %pass1.j.cond

pass1.j.cond:
  %j1 = phi i64 [ 1, %pass1.j.header ], [ %j1.inc, %pass1.j.latch ]
  %cmp.j1 = icmp slt i64 %j1, %nm1.64
  br i1 %cmp.j1, label %pass1.k.header, label %pass1.j.end

pass1.k.header:
  %jp1 = add nsw i64 %j1, 1
  %jm1 = add nsw i64 %j1, -1
  %row.c = mul nsw i64 %j1, %n64
  %row.p = mul nsw i64 %jp1, %n64
  %row.m = mul nsw i64 %jm1, %n64
  %base.c.i = add i64 %i.base, %row.c
  %base.c.ip1 = add i64 %ip1.base2, %row.c
  %base.c.im1 = add i64 %im1.base2, %row.c
  %base.p.i = add i64 %i.base, %row.p
  %base.m.i = add i64 %i.base, %row.m
  br label %pass1.k.cond

pass1.k.cond:
  %k1 = phi i64 [ 1, %pass1.k.header ], [ %k1.inc, %pass1.k.body ]
  %cmp.k1 = icmp slt i64 %k1, %nm1.64
  br i1 %cmp.k1, label %pass1.k.body, label %pass1.j.latch

pass1.k.body:
  %kp1 = add nsw i64 %k1, 1
  %km1 = add nsw i64 %k1, -1

  %off.c.i = add i64 %base.c.i, %k1
  %ptr.c.i = getelementptr inbounds double, ptr %A, i64 %off.c.i
  %v.c.i = load double, ptr %ptr.c.i, align 8

  %off.ip1 = add i64 %base.c.ip1, %k1
  %ptr.ip1 = getelementptr inbounds double, ptr %A, i64 %off.ip1
  %v.ip1 = load double, ptr %ptr.ip1, align 8

  %off.im1 = add i64 %base.c.im1, %k1
  %ptr.im1 = getelementptr inbounds double, ptr %A, i64 %off.im1
  %v.im1 = load double, ptr %ptr.im1, align 8

  %off.jp1 = add i64 %base.p.i, %k1
  %ptr.jp1 = getelementptr inbounds double, ptr %A, i64 %off.jp1
  %v.jp1 = load double, ptr %ptr.jp1, align 8

  %off.jm1 = add i64 %base.m.i, %k1
  %ptr.jm1 = getelementptr inbounds double, ptr %A, i64 %off.jm1
  %v.jm1 = load double, ptr %ptr.jm1, align 8

  %off.kp1 = add i64 %base.c.i, %kp1
  %ptr.kp1 = getelementptr inbounds double, ptr %A, i64 %off.kp1
  %v.kp1 = load double, ptr %ptr.kp1, align 8

  %off.km1 = add i64 %base.c.i, %km1
  %ptr.km1 = getelementptr inbounds double, ptr %A, i64 %off.km1
  %v.km1 = load double, ptr %ptr.km1, align 8

  %mul.i = fmul double 2.000000e+00, %v.c.i
  %sub.i = fsub double %v.ip1, %mul.i
  %add.i = fadd double %sub.i, %v.im1
  %term.i = fmul double 1.250000e-01, %add.i

  %mul.j = fmul double 2.000000e+00, %v.c.i
  %sub.j = fsub double %v.jp1, %mul.j
  %add.j = fadd double %sub.j, %v.jm1
  %term.j = fmul double 1.250000e-01, %add.j

  %sum.ij = fadd double %term.i, %term.j

  %mul.k = fmul double 2.000000e+00, %v.c.i
  %sub.k = fsub double %v.kp1, %mul.k
  %add.k = fadd double %sub.k, %v.km1
  %term.k = fmul double 1.250000e-01, %add.k

  %sum.ijk = fadd double %sum.ij, %term.k
  %result = fadd double %sum.ijk, %v.c.i

  %off.b = add i64 %base.c.i, %k1
  %ptr.b = getelementptr inbounds double, ptr %B, i64 %off.b
  store double %result, ptr %ptr.b, align 8

  %k1.inc = add nsw i64 %k1, 1
  br label %pass1.k.cond

pass1.j.latch:
  %j1.inc = add nsw i64 %j1, 1
  br label %pass1.j.cond

pass1.j.end:
  br label %pass1.i.latch

pass1.i.latch:
  %i1.inc = add nsw i64 %i1, 1
  br label %pass1.i.cond

pass1.end:
  br label %pass2.i.header

; ---------------- Pass 2: compute A from B ----------------
pass2.i.header:
  br label %pass2.i.cond

pass2.i.cond:
  %i2 = phi i64 [ 1, %pass1.end ], [ %i2.inc, %pass2.i.latch ]
  %cmp.i2 = icmp slt i64 %i2, %nm1.64
  br i1 %cmp.i2, label %pass2.j.header, label %pass2.end

pass2.j.header:
  %ip2 = add nsw i64 %i2, 1
  %im2 = add nsw i64 %i2, -1
  %i2.base = mul i64 %i2, %n64
  %i2.base2 = mul i64 %i2.base, %n64
  %ip2.base = mul i64 %ip2, %n64
  %ip2.base2 = mul i64 %ip2.base, %n64
  %im2.base = mul i64 %im2, %n64
  %im2.base2 = mul i64 %im2.base, %n64
  br label %pass2.j.cond

pass2.j.cond:
  %j2 = phi i64 [ 1, %pass2.j.header ], [ %j2.inc, %pass2.j.latch ]
  %cmp.j2 = icmp slt i64 %j2, %nm1.64
  br i1 %cmp.j2, label %pass2.k.header, label %pass2.j.end

pass2.k.header:
  %jp2 = add nsw i64 %j2, 1
  %jm2 = add nsw i64 %j2, -1
  %row2.c = mul nsw i64 %j2, %n64
  %row2.p = mul nsw i64 %jp2, %n64
  %row2.m = mul nsw i64 %jm2, %n64
  %base2.c.i = add i64 %i2.base2, %row2.c
  %base2.c.ip1 = add i64 %ip2.base2, %row2.c
  %base2.c.im1 = add i64 %im2.base2, %row2.c
  %base2.p.i = add i64 %i2.base2, %row2.p
  %base2.m.i = add i64 %i2.base2, %row2.m
  br label %pass2.k.cond

pass2.k.cond:
  %k2 = phi i64 [ 1, %pass2.k.header ], [ %k2.inc, %pass2.k.body ]
  %cmp.k2 = icmp slt i64 %k2, %nm1.64
  br i1 %cmp.k2, label %pass2.k.body, label %pass2.j.latch

pass2.k.body:
  %kp2 = add nsw i64 %k2, 1
  %km2 = add nsw i64 %k2, -1

  %off2.c.i = add i64 %base2.c.i, %k2
  %ptr2.c.i = getelementptr inbounds double, ptr %B, i64 %off2.c.i
  %w.c.i = load double, ptr %ptr2.c.i, align 8

  %off2.ip1 = add i64 %base2.c.ip1, %k2
  %ptr2.ip1 = getelementptr inbounds double, ptr %B, i64 %off2.ip1
  %w.ip1 = load double, ptr %ptr2.ip1, align 8

  %off2.im1 = add i64 %base2.c.im1, %k2
  %ptr2.im1 = getelementptr inbounds double, ptr %B, i64 %off2.im1
  %w.im1 = load double, ptr %ptr2.im1, align 8

  %off2.jp1 = add i64 %base2.p.i, %k2
  %ptr2.jp1 = getelementptr inbounds double, ptr %B, i64 %off2.jp1
  %w.jp1 = load double, ptr %ptr2.jp1, align 8

  %off2.jm1 = add i64 %base2.m.i, %k2
  %ptr2.jm1 = getelementptr inbounds double, ptr %B, i64 %off2.jm1
  %w.jm1 = load double, ptr %ptr2.jm1, align 8

  %off2.kp1 = add i64 %base2.c.i, %kp2
  %ptr2.kp1 = getelementptr inbounds double, ptr %B, i64 %off2.kp1
  %w.kp1 = load double, ptr %ptr2.kp1, align 8

  %off2.km1 = add i64 %base2.c.i, %km2
  %ptr2.km1 = getelementptr inbounds double, ptr %B, i64 %off2.km1
  %w.km1 = load double, ptr %ptr2.km1, align 8

  %mul2.i = fmul double 2.000000e+00, %w.c.i
  %sub2.i = fsub double %w.ip1, %mul2.i
  %add2.i = fadd double %sub2.i, %w.im1
  %term2.i = fmul double 1.250000e-01, %add2.i

  %mul2.j = fmul double 2.000000e+00, %w.c.i
  %sub2.j = fsub double %w.jp1, %mul2.j
  %add2.j = fadd double %sub2.j, %w.jm1
  %term2.j = fmul double 1.250000e-01, %add2.j

  %sum2.ij = fadd double %term2.i, %term2.j

  %mul2.k = fmul double 2.000000e+00, %w.c.i
  %sub2.k = fsub double %w.kp1, %mul2.k
  %add2.k = fadd double %sub2.k, %w.km1
  %term2.k = fmul double 1.250000e-01, %add2.k

  %sum2.ijk = fadd double %sum2.ij, %term2.k
  %result2 = fadd double %sum2.ijk, %w.c.i

  %off2.a = add i64 %base2.c.i, %k2
  %ptr2.a = getelementptr inbounds double, ptr %A, i64 %off2.a
  store double %result2, ptr %ptr2.a, align 8

  %k2.inc = add nsw i64 %k2, 1
  br label %pass2.k.cond

pass2.j.latch:
  %j2.inc = add nsw i64 %j2, 1
  br label %pass2.j.cond

pass2.j.end:
  br label %pass2.i.latch

pass2.i.latch:
  %i2.inc = add nsw i64 %i2, 1
  br label %pass2.i.cond

pass2.end:
  br label %for.inc215

for.inc215:
  %inc216 = add nsw i32 %t, 1
  br label %for.cond

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
