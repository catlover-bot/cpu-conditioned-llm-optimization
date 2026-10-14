; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.t = icmp sgt i32 %tsteps, 0
  %n64 = sext i32 %n to i64
  br i1 %cmp.t, label %t.check, label %for.end93

t.check:
  ; check if inner loops have any work: need n-2 >= 1, i.e. n >= 3
  %nm2 = add nsw i32 %n, -2
  %inner.has.work = icmp sgt i32 %nm2, 0
  br label %t.preheader

t.preheader:
  br label %for.cond

for.cond:
  %t = phi i32 [ 0, %t.preheader ], [ %inc92, %for.inc91 ]
  br i1 %inner.has.work, label %phaseA.preheader, label %for.inc91

phaseA.preheader:
  br label %phaseA.i

phaseA.i:
  %i.A = phi i32 [ 1, %phaseA.preheader ], [ %inc42, %phaseA.i.inc ]
  %i64.A = sext i32 %i.A to i64
  %row.A.center = mul nsw i64 %i64.A, %n64
  %i64.A.p1 = add nsw i64 %i64.A, 1
  %row.A.p1 = mul nsw i64 %i64.A.p1, %n64
  %i64.A.m1 = add nsw i64 %i64.A, -1
  %row.A.m1 = mul nsw i64 %i64.A.m1, %n64
  br label %phaseA.j

phaseA.j:
  %j.A = phi i32 [ 1, %phaseA.i ], [ %inc.A, %phaseA.body ]
  %j64.A = sext i32 %j.A to i64
  br label %phaseA.body

phaseA.body:
  %idx.center = add nsw i64 %row.A.center, %j64.A
  %p.center = getelementptr inbounds double, ptr %A, i64 %idx.center
  %v.center = load double, ptr %p.center, align 8

  %j64.m1 = add nsw i64 %j64.A, -1
  %idx.left = add nsw i64 %row.A.center, %j64.m1
  %p.left = getelementptr inbounds double, ptr %A, i64 %idx.left
  %v.left = load double, ptr %p.left, align 8

  %add18 = fadd double %v.center, %v.left

  %j64.p1 = add nsw i64 %j64.A, 1
  %idx.right = add nsw i64 %row.A.center, %j64.p1
  %p.right = getelementptr inbounds double, ptr %A, i64 %idx.right
  %v.right = load double, ptr %p.right, align 8

  %add24 = fadd double %add18, %v.right

  %idx.down = add nsw i64 %row.A.p1, %j64.A
  %p.down = getelementptr inbounds double, ptr %A, i64 %idx.down
  %v.down = load double, ptr %p.down, align 8

  %add30 = fadd double %add24, %v.down

  %idx.up = add nsw i64 %row.A.m1, %j64.A
  %p.up = getelementptr inbounds double, ptr %A, i64 %idx.up
  %v.up = load double, ptr %p.up, align 8

  %add36 = fadd double %add30, %v.up

  %mulv = fmul double 2.000000e-01, %add36

  %idx.B = add nsw i64 %row.A.center, %j64.A
  %p.B = getelementptr inbounds double, ptr %B, i64 %idx.B
  store double %mulv, ptr %p.B, align 8

  %inc.A = add nsw i32 %j.A, 1
  %nm1.A = add nsw i32 %n, -1
  %cmp.j.A = icmp slt i32 %inc.A, %nm1.A
  br i1 %cmp.j.A, label %phaseA.body, label %phaseA.i.inc

phaseA.i.inc:
  %inc42 = add nsw i32 %i.A, 1
  %nm1.i.A = add nsw i32 %n, -1
  %cmp.i.A = icmp slt i32 %inc42, %nm1.i.A
  br i1 %cmp.i.A, label %phaseA.i, label %phaseB.preheader

phaseB.preheader:
  br label %phaseB.i

phaseB.i:
  %i.B = phi i32 [ 1, %phaseB.preheader ], [ %inc89, %phaseB.i.inc ]
  %i64.B = sext i32 %i.B to i64
  %row.B.center = mul nsw i64 %i64.B, %n64
  %i64.B.p1 = add nsw i64 %i64.B, 1
  %row.B.p1 = mul nsw i64 %i64.B.p1, %n64
  %i64.B.m1 = add nsw i64 %i64.B, -1
  %row.B.m1 = mul nsw i64 %i64.B.m1, %n64
  br label %phaseB.j

phaseB.j:
  %j.B = phi i32 [ 1, %phaseB.i ], [ %inc.B, %phaseB.body ]
  %j64.B = sext i32 %j.B to i64
  br label %phaseB.body

phaseB.body:
  %idxB.center = add nsw i64 %row.B.center, %j64.B
  %pB.center = getelementptr inbounds double, ptr %B, i64 %idxB.center
  %vB.center = load double, ptr %pB.center, align 8

  %j64B.m1 = add nsw i64 %j64.B, -1
  %idxB.left = add nsw i64 %row.B.center, %j64B.m1
  %pB.left = getelementptr inbounds double, ptr %B, i64 %idxB.left
  %vB.left = load double, ptr %pB.left, align 8

  %add61 = fadd double %vB.center, %vB.left

  %j64B.p1 = add nsw i64 %j64.B, 1
  %idxB.right = add nsw i64 %row.B.center, %j64B.p1
  %pB.right = getelementptr inbounds double, ptr %B, i64 %idxB.right
  %vB.right = load double, ptr %pB.right, align 8

  %add67 = fadd double %add61, %vB.right

  %idxB.down = add nsw i64 %row.B.p1, %j64.B
  %pB.down = getelementptr inbounds double, ptr %B, i64 %idxB.down
  %vB.down = load double, ptr %pB.down, align 8

  %add73 = fadd double %add67, %vB.down

  %idxB.up = add nsw i64 %row.B.m1, %j64.B
  %pB.up = getelementptr inbounds double, ptr %B, i64 %idxB.up
  %vB.up = load double, ptr %pB.up, align 8

  %add79 = fadd double %add73, %vB.up

  %mulv80 = fmul double 2.000000e-01, %add79

  %idxA.store = add nsw i64 %row.B.center, %j64.B
  %pA.store = getelementptr inbounds double, ptr %A, i64 %idxA.store
  store double %mulv80, ptr %pA.store, align 8

  %inc.B = add nsw i32 %j.B, 1
  %nm1.B = add nsw i32 %n, -1
  %cmp.j.B = icmp slt i32 %inc.B, %nm1.B
  br i1 %cmp.j.B, label %phaseB.body, label %phaseB.i.inc

phaseB.i.inc:
  %inc89 = add nsw i32 %i.B, 1
  %nm1.i.B = add nsw i32 %n, -1
  %cmp.i.B = icmp slt i32 %inc89, %nm1.i.B
  br i1 %cmp.i.B, label %phaseB.i, label %for.inc91

for.inc91:
  %inc92 = add nsw i32 %t, 1
  %cmp.t.loop = icmp slt i32 %inc92, %tsteps
  br i1 %cmp.t.loop, label %for.cond, label %for.end93

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
