; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end93

preheader:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm1_64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc91, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br label %for.body.i1

for.body.i1:                                      ; A -> B pass, i = 1 .. n-2
  %i1 = phi i64 [ 1, %for.cond ], [ %i1.next, %i1.end ]
  %irow = mul nsw i64 %i1, %n64
  %irow.prev = sub nsw i64 %irow, %n64
  %irow.next = add nsw i64 %irow, %n64
  br label %j1.body

j1.body:
  %j1 = phi i64 [ 1, %for.body.i1 ], [ %j1.next, %j1.body ]

  %idx.c = add nsw i64 %irow, %j1
  %p.c = getelementptr inbounds double, ptr %A, i64 %idx.c
  %v.c = load double, ptr %p.c, align 8

  %idx.w = add nsw i64 %irow, %j1
  %idx.w2 = sub nsw i64 %idx.w, 1
  %p.w = getelementptr inbounds double, ptr %A, i64 %idx.w2
  %v.w = load double, ptr %p.w, align 8

  %add18 = fadd double %v.c, %v.w

  %idx.e = add nsw i64 %irow, %j1
  %idx.e2 = add nsw i64 %idx.e, 1
  %p.e = getelementptr inbounds double, ptr %A, i64 %idx.e2
  %v.e = load double, ptr %p.e, align 8

  %add24 = fadd double %add18, %v.e

  %idx.s = add nsw i64 %irow.next, %j1
  %p.s = getelementptr inbounds double, ptr %A, i64 %idx.s
  %v.s = load double, ptr %p.s, align 8

  %add30 = fadd double %add24, %v.s

  %idx.n = add nsw i64 %irow.prev, %j1
  %p.n = getelementptr inbounds double, ptr %A, i64 %idx.n
  %v.n = load double, ptr %p.n, align 8

  %add36 = fadd double %add30, %v.n

  %mul = fmul double 2.000000e-01, %add36

  %idx.b = add nsw i64 %irow, %j1
  %p.b = getelementptr inbounds double, ptr %B, i64 %idx.b
  store double %mul, ptr %p.b, align 8

  %j1.next = add nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %nm1_64
  br i1 %j1.cmp, label %j1.body, label %i1.end

i1.end:
  %i1.next = add nsw i64 %i1, 1
  %i1.cmp = icmp slt i64 %i1.next, %nm1_64
  br i1 %i1.cmp, label %for.body.i1, label %for.body.i2

for.body.i2:                                      ; B -> A pass, i = 1 .. n-2
  %i2 = phi i64 [ 1, %i1.end ], [ %i2.next, %i2.end ]
  %irow2 = mul nsw i64 %i2, %n64
  %irow2.prev = sub nsw i64 %irow2, %n64
  %irow2.next = add nsw i64 %irow2, %n64
  br label %j2.body

j2.body:
  %j2 = phi i64 [ 1, %for.body.i2 ], [ %j2.next, %j2.body ]

  %idx2.c = add nsw i64 %irow2, %j2
  %p2.c = getelementptr inbounds double, ptr %B, i64 %idx2.c
  %v2.c = load double, ptr %p2.c, align 8

  %idx2.w2 = sub nsw i64 %idx2.c, 1
  %p2.w = getelementptr inbounds double, ptr %B, i64 %idx2.w2
  %v2.w = load double, ptr %p2.w, align 8

  %add61 = fadd double %v2.c, %v2.w

  %idx2.e2 = add nsw i64 %idx2.c, 1
  %p2.e = getelementptr inbounds double, ptr %B, i64 %idx2.e2
  %v2.e = load double, ptr %p2.e, align 8

  %add67 = fadd double %add61, %v2.e

  %idx2.s = add nsw i64 %irow2.next, %j2
  %p2.s = getelementptr inbounds double, ptr %B, i64 %idx2.s
  %v2.s = load double, ptr %p2.s, align 8

  %add73 = fadd double %add67, %v2.s

  %idx2.n = add nsw i64 %irow2.prev, %j2
  %p2.n = getelementptr inbounds double, ptr %B, i64 %idx2.n
  %v2.n = load double, ptr %p2.n, align 8

  %add79 = fadd double %add73, %v2.n

  %mul80 = fmul double 2.000000e-01, %add79

  %idx2.b = add nsw i64 %irow2, %j2
  %p2.b = getelementptr inbounds double, ptr %A, i64 %idx2.b
  store double %mul80, ptr %p2.b, align 8

  %j2.next = add nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %nm1_64
  br i1 %j2.cmp, label %j2.body, label %i2.end

i2.end:
  %i2.next = add nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.next, %nm1_64
  br i1 %i2.cmp, label %for.body.i2, label %for.inc91

for.inc91:
  %inc92 = add nsw i32 %t, 1
  %t.cmp = icmp slt i32 %inc92, %tsteps
  br i1 %t.cmp, label %for.cond, label %for.end93

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
