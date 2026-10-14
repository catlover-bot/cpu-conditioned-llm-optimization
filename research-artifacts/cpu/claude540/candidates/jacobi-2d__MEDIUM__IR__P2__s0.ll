; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  br i1 %cmp.n, label %check.tsteps, label %for.end93

check.tsteps:
  %cmp.t0 = icmp sgt i32 %tsteps, 0
  br i1 %cmp.t0, label %preheader, label %for.end93

preheader:
  %n64 = sext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1_64 = sext i32 %nm1 to i64
  ; number of inner j iterations (from j=1 to n-2 inclusive) = n-2
  %jcount64 = sub nsw i64 %nm1_64, 1
  %icount64 = sub nsw i64 %nm1_64, 1
  %has_inner = icmp sgt i64 %jcount64, 0
  %has_outer = icmp sgt i64 %icount64, 0
  %do_inner_loops = and i1 %has_inner, %has_outer
  br label %for.cond

for.cond:
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  %cmp = icmp slt i32 %t, %tsteps
  br i1 %cmp, label %for.body, label %for.end93

for.body:
  br i1 %do_inner_loops, label %outer1.preheader, label %outer2.check

outer1.preheader:
  br label %outer1

; First sweep: B[i][j] = 0.2*(A[i][j]+A[i][j-1]+A[i][1+j]+A[1+i][j]+A[i-1][j])
outer1:
  %i1 = phi i64 [ 1, %outer1.preheader ], [ %i1.next, %outer1.latch ]
  %rowbase = mul nsw i64 %i1, %n64
  %rowA = getelementptr inbounds double, ptr %A, i64 %rowbase
  %i1p1 = add nsw i64 %i1, 1
  %rowbaseP1 = mul nsw i64 %i1p1, %n64
  %rowA.p1 = getelementptr inbounds double, ptr %A, i64 %rowbaseP1
  %i1m1 = sub nsw i64 %i1, 1
  %rowbaseM1 = mul nsw i64 %i1m1, %n64
  %rowA.m1 = getelementptr inbounds double, ptr %A, i64 %rowbaseM1
  %rowB = getelementptr inbounds double, ptr %B, i64 %rowbase
  br label %inner1

inner1:
  %j1 = phi i64 [ 1, %outer1 ], [ %j1.next, %inner1 ]
  %a.center.ptr = getelementptr inbounds double, ptr %rowA, i64 %j1
  %a.center = load double, ptr %a.center.ptr, align 8
  %j1m1 = sub nsw i64 %j1, 1
  %a.left.ptr = getelementptr inbounds double, ptr %rowA, i64 %j1m1
  %a.left = load double, ptr %a.left.ptr, align 8
  %s1 = fadd double %a.center, %a.left
  %j1p1 = add nsw i64 %j1, 1
  %a.right.ptr = getelementptr inbounds double, ptr %rowA, i64 %j1p1
  %a.right = load double, ptr %a.right.ptr, align 8
  %s2 = fadd double %s1, %a.right
  %a.down.ptr = getelementptr inbounds double, ptr %rowA.p1, i64 %j1
  %a.down = load double, ptr %a.down.ptr, align 8
  %s3 = fadd double %s2, %a.down
  %a.up.ptr = getelementptr inbounds double, ptr %rowA.m1, i64 %j1
  %a.up = load double, ptr %a.up.ptr, align 8
  %s4 = fadd double %s3, %a.up
  %mulres = fmul double 2.000000e-01, %s4
  %b.ptr = getelementptr inbounds double, ptr %rowB, i64 %j1
  store double %mulres, ptr %b.ptr, align 8
  %j1.next = add nsw i64 %j1, 1
  %inner1.cond = icmp slt i64 %j1.next, %nm1_64
  br i1 %inner1.cond, label %inner1, label %outer1.latch

outer1.latch:
  %i1.next = add nsw i64 %i1, 1
  %outer1.cond = icmp slt i64 %i1.next, %nm1_64
  br i1 %outer1.cond, label %outer1, label %outer2.check

outer2.check:
  br i1 %do_inner_loops, label %outer2.preheader, label %for.inc91

outer2.preheader:
  br label %outer2

; Second sweep: A[i][j] = 0.2*(B[i][j]+B[i][j-1]+B[i][1+j]+B[1+i][j]+B[i-1][j])
outer2:
  %i2 = phi i64 [ 1, %outer2.preheader ], [ %i2.next, %outer2.latch ]
  %rowbase2 = mul nsw i64 %i2, %n64
  %rowB2 = getelementptr inbounds double, ptr %B, i64 %rowbase2
  %i2p1 = add nsw i64 %i2, 1
  %rowbase2P1 = mul nsw i64 %i2p1, %n64
  %rowB2.p1 = getelementptr inbounds double, ptr %B, i64 %rowbase2P1
  %i2m1 = sub nsw i64 %i2, 1
  %rowbase2M1 = mul nsw i64 %i2m1, %n64
  %rowB2.m1 = getelementptr inbounds double, ptr %B, i64 %rowbase2M1
  %rowA2 = getelementptr inbounds double, ptr %A, i64 %rowbase2
  br label %inner2

inner2:
  %j2 = phi i64 [ 1, %outer2 ], [ %j2.next, %inner2 ]
  %b.center.ptr = getelementptr inbounds double, ptr %rowB2, i64 %j2
  %b.center = load double, ptr %b.center.ptr, align 8
  %j2m1 = sub nsw i64 %j2, 1
  %b.left.ptr = getelementptr inbounds double, ptr %rowB2, i64 %j2m1
  %b.left = load double, ptr %b.left.ptr, align 8
  %t1 = fadd double %b.center, %b.left
  %j2p1 = add nsw i64 %j2, 1
  %b.right.ptr = getelementptr inbounds double, ptr %rowB2, i64 %j2p1
  %b.right = load double, ptr %b.right.ptr, align 8
  %t2 = fadd double %t1, %b.right
  %b.down.ptr = getelementptr inbounds double, ptr %rowB2.p1, i64 %j2
  %b.down = load double, ptr %b.down.ptr, align 8
  %t3 = fadd double %t2, %b.down
  %b.up.ptr = getelementptr inbounds double, ptr %rowB2.m1, i64 %j2
  %b.up = load double, ptr %b.up.ptr, align 8
  %t4 = fadd double %t3, %b.up
  %mulres2 = fmul double 2.000000e-01, %t4
  %a.ptr2 = getelementptr inbounds double, ptr %rowA2, i64 %j2
  store double %mulres2, ptr %a.ptr2, align 8
  %j2.next = add nsw i64 %j2, 1
  %inner2.cond = icmp slt i64 %j2.next, %nm1_64
  br i1 %inner2.cond, label %inner2, label %outer2.latch

outer2.latch:
  %i2.next = add nsw i64 %i2, 1
  %outer2.cond = icmp slt i64 %i2.next, %nm1_64
  br i1 %outer2.cond, label %outer2, label %for.inc91

for.inc91:
  %inc92 = add nsw i32 %t, 1
  br label %for.cond

for.end93:
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
