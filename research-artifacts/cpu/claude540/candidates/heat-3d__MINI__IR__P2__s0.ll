; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  br i1 %cmp.n, label %check.tsteps, label %for.end217

check.tsteps:
  %cmp.t0 = icmp sle i32 1, %tsteps
  br i1 %cmp.t0, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  ; number of iterations of i,j,k loops (from 1 to n-2 inclusive) = n-2 if n>=2 else 0
  %trip64 = sext i32 %nm1 to i64
  %trip = sub nsw i64 %trip64, 1
  %hasInner = icmp sgt i64 %trip, 0
  br label %t.loop

t.loop:
  %t = phi i32 [ 1, %preheader ], [ %t.inc, %t.latch ]
  br i1 %hasInner, label %i.loop.A, label %i.loop.A.skip

i.loop.A.skip:
  br label %i.loop.B.skip

i.loop.A:
  %i.A = phi i64 [ 1, %t.loop ], [ %i.A.inc, %i.A.latch ]
  br label %j.loop.A

j.loop.A:
  %j.A = phi i64 [ 1, %i.loop.A ], [ %j.A.inc, %j.A.latch ]
  br label %k.loop.A

k.loop.A:
  %k.A = phi i64 [ 1, %j.loop.A ], [ %k.A.inc, %k.loop.A ]

  %nsq = mul nuw i64 %n64, %n64
  %ip1 = add nsw i64 %i.A, 1
  %base_ip1 = mul i64 %ip1, %nsq
  %base_i   = mul i64 %i.A, %nsq
  %im1 = add nsw i64 %i.A, -1
  %base_im1 = mul i64 %im1, %nsq
  %jn = mul i64 %j.A, %n64
  %jp1 = add nsw i64 %j.A, 1
  %jn_p1 = mul i64 %jp1, %n64
  %jm1 = add nsw i64 %j.A, -1
  %jn_m1 = mul i64 %jm1, %n64
  %kp1 = add nsw i64 %k.A, 1
  %km1 = add nsw i64 %k.A, -1

  ; A[i+1][j][k]
  %off1 = add i64 %base_ip1, %jn
  %off1b = add i64 %off1, %k.A
  %p1 = getelementptr inbounds double, ptr %A, i64 %off1b
  %v1 = load double, ptr %p1, align 8

  ; A[i][j][k]
  %off2 = add i64 %base_i, %jn
  %off2b = add i64 %off2, %k.A
  %p2 = getelementptr inbounds double, ptr %A, i64 %off2b
  %v2 = load double, ptr %p2, align 8
  %mul_v2 = fmul double 2.000000e+00, %v2
  %sub1 = fsub double %v1, %mul_v2

  ; A[i-1][j][k]
  %off3 = add i64 %base_im1, %jn
  %off3b = add i64 %off3, %k.A
  %p3 = getelementptr inbounds double, ptr %A, i64 %off3b
  %v3 = load double, ptr %p3, align 8
  %add1 = fadd double %sub1, %v3
  %term1 = fmul double 1.250000e-01, %add1

  ; A[i][j+1][k]
  %off4 = add i64 %base_i, %jn_p1
  %off4b = add i64 %off4, %k.A
  %p4 = getelementptr inbounds double, ptr %A, i64 %off4b
  %v4 = load double, ptr %p4, align 8

  ; A[i][j][k] again
  %p5 = getelementptr inbounds double, ptr %A, i64 %off2b
  %v5 = load double, ptr %p5, align 8
  %mul_v5 = fmul double 2.000000e+00, %v5
  %sub2 = fsub double %v4, %mul_v5

  ; A[i][j-1][k]
  %off6 = add i64 %base_i, %jn_m1
  %off6b = add i64 %off6, %k.A
  %p6 = getelementptr inbounds double, ptr %A, i64 %off6b
  %v6 = load double, ptr %p6, align 8
  %add2 = fadd double %sub2, %v6
  %term2 = fmul double 1.250000e-01, %add2
  %sum12 = fadd double %term1, %term2

  ; A[i][j][k+1]
  %off7 = add i64 %off2b, 1
  %p7 = getelementptr inbounds double, ptr %A, i64 %off7
  %v7 = load double, ptr %p7, align 8

  ; A[i][j][k] again
  %p8 = getelementptr inbounds double, ptr %A, i64 %off2b
  %v8 = load double, ptr %p8, align 8
  %mul_v8 = fmul double 2.000000e+00, %v8
  %sub3 = fsub double %v7, %mul_v8

  ; A[i][j][k-1]
  %off9 = add i64 %off2b, -1
  %p9 = getelementptr inbounds double, ptr %A, i64 %off9
  %v9 = load double, ptr %p9, align 8
  %add3 = fadd double %sub3, %v9
  %term3 = fmul double 1.250000e-01, %add3
  %sum123 = fadd double %sum12, %term3

  ; A[i][j][k] final add
  %p10 = getelementptr inbounds double, ptr %A, i64 %off2b
  %v10 = load double, ptr %p10, align 8
  %final = fadd double %sum123, %v10

  ; store to B[i][j][k]
  %pB = getelementptr inbounds double, ptr %B, i64 %off2b
  store double %final, ptr %pB, align 8

  %k.A.inc = add nsw i64 %k.A, 1
  %k.A.cmp = icmp slt i64 %k.A.inc, %trip64
  br i1 %k.A.cmp, label %k.loop.A, label %j.loop.A.latch

j.loop.A.latch:
  %j.A.inc = add nsw i64 %j.A, 1
  %j.A.cmp = icmp slt i64 %j.A.inc, %trip64
  br i1 %j.A.cmp, label %j.loop.A, label %i.loop.A.latch

i.loop.A.latch:
  %i.A.inc = add nsw i64 %i.A, 1
  %i.A.cmp = icmp slt i64 %i.A.inc, %trip64
  br i1 %i.A.cmp, label %i.loop.A, label %i.loop.B.skip

i.loop.B.skip:
  br i1 %hasInner, label %i.loop.B, label %t.latch

i.loop.B:
  %i.B = phi i64 [ 1, %i.loop.B.skip ], [ %i.B.inc, %i.B.latch ]
  br label %j.loop.B

j.loop.B:
  %j.B = phi i64 [ 1, %i.loop.B ], [ %j.B.inc, %j.B.latch ]
  br label %k.loop.B

k.loop.B:
  %k.B = phi i64 [ 1, %j.loop.B ], [ %k.B.inc, %k.loop.B ]

  %nsqB = mul nuw i64 %n64, %n64
  %ip1B = add nsw i64 %i.B, 1
  %base_ip1B = mul i64 %ip1B, %nsqB
  %base_iB   = mul i64 %i.B, %nsqB
  %im1B = add nsw i64 %i.B, -1
  %base_im1B = mul i64 %im1B, %nsqB
  %jnB = mul i64 %j.B, %n64
  %jp1B = add nsw i64 %j.B, 1
  %jn_p1B = mul i64 %jp1B, %n64
  %jm1B = add nsw i64 %j.B, -1
  %jn_m1B = mul i64 %jm1B, %n64

  ; B[i+1][j][k]
  %offB1 = add i64 %base_ip1B, %jnB
  %offB1b = add i64 %offB1, %k.B
  %pB1 = getelementptr inbounds double, ptr %B, i64 %offB1b
  %vB1 = load double, ptr %pB1, align 8

  ; B[i][j][k]
  %offB2 = add i64 %base_iB, %jnB
  %offB2b = add i64 %offB2, %k.B
  %pB2 = getelementptr inbounds double, ptr %B, i64 %offB2b
  %vB2 = load double, ptr %pB2, align 8
  %mul_vB2 = fmul double 2.000000e+00, %vB2
  %subB1 = fsub double %vB1, %mul_vB2

  ; B[i-1][j][k]
  %offB3 = add i64 %base_im1B, %jnB
  %offB3b = add i64 %offB3, %k.B
  %pB3 = getelementptr inbounds double, ptr %B, i64 %offB3b
  %vB3 = load double, ptr %pB3, align 8
  %addB1 = fadd double %subB1, %vB3
  %termB1 = fmul double 1.250000e-01, %addB1

  ; B[i][j+1][k]
  %offB4 = add i64 %base_iB, %jn_p1B
  %offB4b = add i64 %offB4, %k.B
  %pB4 = getelementptr inbounds double, ptr %B, i64 %offB4b
  %vB4 = load double, ptr %pB4, align 8

  ; B[i][j][k] again
  %pB5 = getelementptr inbounds double, ptr %B, i64 %offB2b
  %vB5 = load double, ptr %pB5, align 8
  %mul_vB5 = fmul double 2.000000e+00, %vB5
  %subB2 = fsub double %vB4, %mul_vB5

  ; B[i][j-1][k]
  %offB6 = add i64 %base_iB, %jn_m1B
  %offB6b = add i64 %offB6, %k.B
  %pB6 = getelementptr inbounds double, ptr %B, i64 %offB6b
  %vB6 = load double, ptr %pB6, align 8
  %addB2 = fadd double %subB2, %vB6
  %termB2 = fmul double 1.250000e-01, %addB2
  %sumB12 = fadd double %termB1, %termB2

  ; B[i][j][k+1]
  %offB7 = add i64 %offB2b, 1
  %pB7 = getelementptr inbounds double, ptr %B, i64 %offB7
  %vB7 = load double, ptr %pB7, align 8

  ; B[i][j][k] again
  %pB8 = getelementptr inbounds double, ptr %B, i64 %offB2b
  %vB8 = load double, ptr %pB8, align 8
  %mul_vB8 = fmul double 2.000000e+00, %vB8
  %subB3 = fsub double %vB7, %mul_vB8

  ; B[i][j][k-1]
  %offB9 = add i64 %offB2b, -1
  %pB9 = getelementptr inbounds double, ptr %B, i64 %offB9
  %vB9 = load double, ptr %pB9, align 8
  %addB3 = fadd double %subB3, %vB9
  %termB3 = fmul double 1.250000e-01, %addB3
  %sumB123 = fadd double %sumB12, %termB3

  ; B[i][j][k] final add
  %pB10 = getelementptr inbounds double, ptr %B, i64 %offB2b
  %vB10 = load double, ptr %pB10, align 8
  %finalB = fadd double %sumB123, %vB10

  ; store to A[i][j][k]
  %pA = getelementptr inbounds double, ptr %A, i64 %offB2b
  store double %finalB, ptr %pA, align 8

  %k.B.inc = add nsw i64 %k.B, 1
  %k.B.cmp = icmp slt i64 %k.B.inc, %trip64
  br i1 %k.B.cmp, label %k.loop.B, label %j.loop.B.latch

j.loop.B.latch:
  %j.B.inc = add nsw i64 %j.B, 1
  %j.B.cmp = icmp slt i64 %j.B.inc, %trip64
  br i1 %j.B.cmp, label %j.loop.B, label %i.loop.B.latch

i.loop.B.latch:
  %i.B.inc = add nsw i64 %i.B, 1
  %i.B.cmp = icmp slt i64 %i.B.inc, %trip64
  br i1 %i.B.cmp, label %i.loop.B, label %t.latch

t.latch:
  %t.inc = add nsw i32 %t, 1
  %t.cmp = icmp sle i32 %t.inc, 20
  br i1 %t.cmp, label %t.loop, label %for.end217

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
