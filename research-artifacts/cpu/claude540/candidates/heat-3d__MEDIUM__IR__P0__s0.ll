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
  br label %for.body.i.1

for.body.i.1:
  br label %i.loop.A

; ---- Phase A: compute B from A ----
i.loop.A:
  %i.A = phi i64 [ 1, %for.body.i.1 ], [ %i.A.next, %i.end.A ]
  br label %j.loop.A

j.loop.A:
  %j.A = phi i64 [ 1, %i.loop.A ], [ %j.A.next, %j.end.A ]
  br label %k.loop.A

k.loop.A:
  %k.A = phi i64 [ 1, %j.loop.A ], [ %k.A.next, %k.body.A ]
  %cmp.k.A = icmp ult i64 %k.A, %nm1.64
  br i1 %cmp.k.A, label %k.body.A, label %j.end.A

k.body.A:
  %ip1.A = add nuw nsw i64 %i.A, 1
  %im1.A = sub nsw i64 %i.A, 1
  %jp1.A = add nuw nsw i64 %j.A, 1
  %jm1.A = sub nsw i64 %j.A, 1
  %kp1.A = add nuw nsw i64 %k.A, 1
  %km1.A = sub nsw i64 %k.A, 1

  %nn.A = mul nuw i64 %n64, %n64

  ; A[i+1][j][k]
  %base.ip1 = mul nsw i64 %ip1.A, %nn.A
  %off.ip1.j = mul nsw i64 %j.A, %n64
  %ptr.ip1.0 = getelementptr inbounds double, ptr %A, i64 %base.ip1
  %ptr.ip1.1 = getelementptr inbounds double, ptr %ptr.ip1.0, i64 %off.ip1.j
  %ptr.ip1.2 = getelementptr inbounds double, ptr %ptr.ip1.1, i64 %k.A
  %v.ip1 = load double, ptr %ptr.ip1.2, align 8

  ; A[i][j][k]
  %base.i = mul nsw i64 %i.A, %nn.A
  %off.i.j = mul nsw i64 %j.A, %n64
  %ptr.i.0 = getelementptr inbounds double, ptr %A, i64 %base.i
  %ptr.i.1 = getelementptr inbounds double, ptr %ptr.i.0, i64 %off.i.j
  %ptr.i.jk = getelementptr inbounds double, ptr %ptr.i.1, i64 %k.A
  %v.i.jk = load double, ptr %ptr.i.jk, align 8

  %mul.a1 = fmul double 2.000000e+00, %v.i.jk
  %sub.a1 = fsub double %v.ip1, %mul.a1

  ; A[i-1][j][k]
  %base.im1 = mul nsw i64 %im1.A, %nn.A
  %ptr.im1.0 = getelementptr inbounds double, ptr %A, i64 %base.im1
  %ptr.im1.1 = getelementptr inbounds double, ptr %ptr.im1.0, i64 %off.i.j
  %ptr.im1.2 = getelementptr inbounds double, ptr %ptr.im1.1, i64 %k.A
  %v.im1 = load double, ptr %ptr.im1.2, align 8

  %add.a1 = fadd double %sub.a1, %v.im1
  %mul.a1b = fmul double 1.250000e-01, %add.a1

  ; A[i][j+1][k]
  %off.i.jp1 = mul nsw i64 %jp1.A, %n64
  %ptr.i.jp1.1 = getelementptr inbounds double, ptr %ptr.i.0, i64 %off.i.jp1
  %ptr.i.jp1.2 = getelementptr inbounds double, ptr %ptr.i.jp1.1, i64 %k.A
  %v.jp1 = load double, ptr %ptr.i.jp1.2, align 8

  %mul.a2 = fmul double 2.000000e+00, %v.i.jk
  %sub.a2 = fsub double %v.jp1, %mul.a2

  ; A[i][j-1][k]
  %off.i.jm1 = mul nsw i64 %jm1.A, %n64
  %ptr.i.jm1.1 = getelementptr inbounds double, ptr %ptr.i.0, i64 %off.i.jm1
  %ptr.i.jm1.2 = getelementptr inbounds double, ptr %ptr.i.jm1.1, i64 %k.A
  %v.jm1 = load double, ptr %ptr.i.jm1.2, align 8

  %add.a2 = fadd double %sub.a2, %v.jm1
  %mul.a2b = fmul double 1.250000e-01, %add.a2

  %add.ab = fadd double %mul.a1b, %mul.a2b

  ; A[i][j][k+1]
  %ptr.i.jk.p1 = getelementptr inbounds double, ptr %ptr.i.jk, i64 1
  %v.kp1 = load double, ptr %ptr.i.jk.p1, align 8

  %mul.a3 = fmul double 2.000000e+00, %v.i.jk
  %sub.a3 = fsub double %v.kp1, %mul.a3

  ; A[i][j][k-1]
  %ptr.i.jk.m1 = getelementptr inbounds double, ptr %ptr.i.jk, i64 -1
  %v.km1 = load double, ptr %ptr.i.jk.m1, align 8

  %add.a3 = fadd double %sub.a3, %v.km1
  %mul.a3b = fmul double 1.250000e-01, %add.a3

  %add.abc = fadd double %add.ab, %mul.a3b
  %result.A = fadd double %add.abc, %v.i.jk

  ; store to B[i][j][k]
  %base.b.i = mul nsw i64 %i.A, %nn.A
  %off.b.j = mul nsw i64 %j.A, %n64
  %ptr.b.0 = getelementptr inbounds double, ptr %B, i64 %base.b.i
  %ptr.b.1 = getelementptr inbounds double, ptr %ptr.b.0, i64 %off.b.j
  %ptr.b.2 = getelementptr inbounds double, ptr %ptr.b.1, i64 %k.A
  store double %result.A, ptr %ptr.b.2, align 8

  %k.A.next = add nuw nsw i64 %k.A, 1
  br label %k.loop.A

j.end.A:
  %j.A.next = add nuw nsw i64 %j.A, 1
  %cmp.j.A = icmp ult i64 %j.A.next, %nm1.64
  br i1 %cmp.j.A, label %j.loop.A, label %i.end.A

i.end.A:
  %i.A.next = add nuw nsw i64 %i.A, 1
  %cmp.i.A = icmp ult i64 %i.A.next, %nm1.64
  br i1 %cmp.i.A, label %i.loop.A, label %phaseB.start

; ---- Phase B: compute A from B ----
phaseB.start:
  br label %i.loop.B

i.loop.B:
  %i.B = phi i64 [ 1, %phaseB.start ], [ %i.B.next, %i.end.B ]
  br label %j.loop.B

j.loop.B:
  %j.B = phi i64 [ 1, %i.loop.B ], [ %j.B.next, %j.end.B ]
  br label %k.loop.B

k.loop.B:
  %k.B = phi i64 [ 1, %j.loop.B ], [ %k.B.next, %k.body.B ]
  %cmp.k.B = icmp ult i64 %k.B, %nm1.64
  br i1 %cmp.k.B, label %k.body.B, label %j.end.B

k.body.B:
  %ip1.B = add nuw nsw i64 %i.B, 1
  %im1.B = sub nsw i64 %i.B, 1
  %jp1.B = add nuw nsw i64 %j.B, 1
  %jm1.B = sub nsw i64 %j.B, 1

  %nn.B = mul nuw i64 %n64, %n64

  ; B[i+1][j][k]
  %base.ip1.B = mul nsw i64 %ip1.B, %nn.B
  %off.ip1.j.B = mul nsw i64 %j.B, %n64
  %ptr.ip1.0.B = getelementptr inbounds double, ptr %B, i64 %base.ip1.B
  %ptr.ip1.1.B = getelementptr inbounds double, ptr %ptr.ip1.0.B, i64 %off.ip1.j.B
  %ptr.ip1.2.B = getelementptr inbounds double, ptr %ptr.ip1.1.B, i64 %k.B
  %v.ip1.B = load double, ptr %ptr.ip1.2.B, align 8

  ; B[i][j][k]
  %base.i.B = mul nsw i64 %i.B, %nn.B
  %off.i.j.B = mul nsw i64 %j.B, %n64
  %ptr.i.0.B = getelementptr inbounds double, ptr %B, i64 %base.i.B
  %ptr.i.1.B = getelementptr inbounds double, ptr %ptr.i.0.B, i64 %off.i.j.B
  %ptr.i.jk.B = getelementptr inbounds double, ptr %ptr.i.1.B, i64 %k.B
  %v.i.jk.B = load double, ptr %ptr.i.jk.B, align 8

  %mul.b1 = fmul double 2.000000e+00, %v.i.jk.B
  %sub.b1 = fsub double %v.ip1.B, %mul.b1

  ; B[i-1][j][k]
  %base.im1.B = mul nsw i64 %im1.B, %nn.B
  %ptr.im1.0.B = getelementptr inbounds double, ptr %B, i64 %base.im1.B
  %ptr.im1.1.B = getelementptr inbounds double, ptr %ptr.im1.0.B, i64 %off.i.j.B
  %ptr.im1.2.B = getelementptr inbounds double, ptr %ptr.im1.1.B, i64 %k.B
  %v.im1.B = load double, ptr %ptr.im1.2.B, align 8

  %add.b1 = fadd double %sub.b1, %v.im1.B
  %mul.b1b = fmul double 1.250000e-01, %add.b1

  ; B[i][j+1][k]
  %off.i.jp1.B = mul nsw i64 %jp1.B, %n64
  %ptr.i.jp1.1.B = getelementptr inbounds double, ptr %ptr.i.0.B, i64 %off.i.jp1.B
  %ptr.i.jp1.2.B = getelementptr inbounds double, ptr %ptr.i.jp1.1.B, i64 %k.B
  %v.jp1.B = load double, ptr %ptr.i.jp1.2.B, align 8

  %mul.b2 = fmul double 2.000000e+00, %v.i.jk.B
  %sub.b2 = fsub double %v.jp1.B, %mul.b2

  ; B[i][j-1][k]
  %off.i.jm1.B = mul nsw i64 %jm1.B, %n64
  %ptr.i.jm1.1.B = getelementptr inbounds double, ptr %ptr.i.0.B, i64 %off.i.jm1.B
  %ptr.i.jm1.2.B = getelementptr inbounds double, ptr %ptr.i.jm1.1.B, i64 %k.B
  %v.jm1.B = load double, ptr %ptr.i.jm1.2.B, align 8

  %add.b2 = fadd double %sub.b2, %v.jm1.B
  %mul.b2b = fmul double 1.250000e-01, %add.b2

  %add.bb = fadd double %mul.b1b, %mul.b2b

  ; B[i][j][k+1]
  %ptr.i.jk.p1.B = getelementptr inbounds double, ptr %ptr.i.jk.B, i64 1
  %v.kp1.B = load double, ptr %ptr.i.jk.p1.B, align 8

  %mul.b3 = fmul double 2.000000e+00, %v.i.jk.B
  %sub.b3 = fsub double %v.kp1.B, %mul.b3

  ; B[i][j][k-1]
  %ptr.i.jk.m1.B = getelementptr inbounds double, ptr %ptr.i.jk.B, i64 -1
  %v.km1.B = load double, ptr %ptr.i.jk.m1.B, align 8

  %add.b3 = fadd double %sub.b3, %v.km1.B
  %mul.b3b = fmul double 1.250000e-01, %add.b3

  %add.bbc = fadd double %add.bb, %mul.b3b
  %result.B = fadd double %add.bbc, %v.i.jk.B

  ; store to A[i][j][k]
  %base.a.i = mul nsw i64 %i.B, %nn.B
  %off.a.j = mul nsw i64 %j.B, %n64
  %ptr.a.0 = getelementptr inbounds double, ptr %A, i64 %base.a.i
  %ptr.a.1 = getelementptr inbounds double, ptr %ptr.a.0, i64 %off.a.j
  %ptr.a.2 = getelementptr inbounds double, ptr %ptr.a.1, i64 %k.B
  store double %result.B, ptr %ptr.a.2, align 8

  %k.B.next = add nuw nsw i64 %k.B, 1
  br label %k.loop.B

j.end.B:
  %j.B.next = add nuw nsw i64 %j.B, 1
  %cmp.j.B = icmp ult i64 %j.B.next, %nm1.64
  br i1 %cmp.j.B, label %j.loop.B, label %i.end.B

i.end.B:
  %i.B.next = add nuw nsw i64 %i.B, 1
  %cmp.i.B = icmp ult i64 %i.B.next, %nm1.64
  br i1 %cmp.i.B, label %i.loop.B, label %for.inc215

for.inc215:
  %inc216 = add nsw i32 %t, 1
  %cmp.t.loop = icmp sle i32 %inc216, 100
  br i1 %cmp.t.loop, label %for.cond, label %for.end217

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
