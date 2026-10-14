; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.tsteps = icmp sgt i32 %tsteps, 0
  %cmp.n = icmp sgt i32 %n, 2
  %run = and i1 %cmp.tsteps, %cmp.n
  br i1 %run, label %preheader, label %for.end73

preheader:
  %n64 = sext i32 %n to i64
  %nm2 = add nsw i32 %n, -2
  %nm2.64 = zext i32 %nm2 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc71, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc72, %for.inc71 ]
  br label %for.body

for.body:                                         ; preds = %for.cond
  br label %for.cond2

for.cond2:                                        ; preds = %for.inc68, %for.body
  %i64 = phi i64 [ 1, %for.body ], [ %inc69.64, %for.inc68 ]
  %row.base = mul nsw i64 %i64, %n64
  %row.m1.base = sub nsw i64 %row.base, %n64
  %row.p1.base = add nsw i64 %row.base, %n64
  br label %for.cond6

for.cond6:                                        ; preds = %for.body9, %for.cond2
  %j64 = phi i64 [ 1, %for.cond2 ], [ %inc.64, %for.body9 ]

  %idx.m1.m1 = add nsw i64 %row.m1.base, %j64
  %idx.m1.m1.f = add nsw i64 %idx.m1.m1, -1
  %p.m1.m1 = getelementptr inbounds double, ptr %A, i64 %idx.m1.m1.f
  %v.m1.m1 = load double, ptr %p.m1.m1, align 8

  %idx.m1.0 = add nsw i64 %row.m1.base, %j64
  %p.m1.0 = getelementptr inbounds double, ptr %A, i64 %idx.m1.0
  %v.m1.0 = load double, ptr %p.m1.0, align 8

  %s1 = fadd double %v.m1.m1, %v.m1.0

  %idx.m1.p1 = add nsw i64 %row.m1.base, %j64
  %idx.m1.p1.p = add nsw i64 %idx.m1.p1, 1
  %p.m1.p1 = getelementptr inbounds double, ptr %A, i64 %idx.m1.p1.p
  %v.m1.p1 = load double, ptr %p.m1.p1, align 8

  %s2 = fadd double %s1, %v.m1.p1

  %idx.0.m1 = add nsw i64 %row.base, %j64
  %idx.0.m1.f = add nsw i64 %idx.0.m1, -1
  %p.0.m1 = getelementptr inbounds double, ptr %A, i64 %idx.0.m1.f
  %v.0.m1 = load double, ptr %p.0.m1, align 8

  %s3 = fadd double %s2, %v.0.m1

  %idx.0.0 = add nsw i64 %row.base, %j64
  %p.0.0 = getelementptr inbounds double, ptr %A, i64 %idx.0.0
  %v.0.0 = load double, ptr %p.0.0, align 8

  %s4 = fadd double %s3, %v.0.0

  %idx.0.p1 = add nsw i64 %row.base, %j64
  %idx.0.p1.p = add nsw i64 %idx.0.p1, 1
  %p.0.p1 = getelementptr inbounds double, ptr %A, i64 %idx.0.p1.p
  %v.0.p1 = load double, ptr %p.0.p1, align 8

  %s5 = fadd double %s4, %v.0.p1

  %idx.p1.m1 = add nsw i64 %row.p1.base, %j64
  %idx.p1.m1.f = add nsw i64 %idx.p1.m1, -1
  %p.p1.m1 = getelementptr inbounds double, ptr %A, i64 %idx.p1.m1.f
  %v.p1.m1 = load double, ptr %p.p1.m1, align 8

  %s6 = fadd double %s5, %v.p1.m1

  %idx.p1.0 = add nsw i64 %row.p1.base, %j64
  %p.p1.0 = getelementptr inbounds double, ptr %A, i64 %idx.p1.0
  %v.p1.0 = load double, ptr %p.p1.0, align 8

  %s7 = fadd double %s6, %v.p1.0

  %idx.p1.p1 = add nsw i64 %row.p1.base, %j64
  %idx.p1.p1.p = add nsw i64 %idx.p1.p1, 1
  %p.p1.p1 = getelementptr inbounds double, ptr %A, i64 %idx.p1.p1.p
  %v.p1.p1 = load double, ptr %p.p1.p1, align 8

  %s8 = fadd double %s7, %v.p1.p1

  %divres = fdiv double %s8, 9.000000e+00

  %p.store = getelementptr inbounds double, ptr %A, i64 %idx.0.0
  store double %divres, ptr %p.store, align 8

  br label %for.body9

for.body9:                                        ; preds = %for.cond6
  %inc.64 = add nsw i64 %j64, 1
  %cmp8.next = icmp slt i64 %inc.64, %nm2.64
  br i1 %cmp8.next, label %for.cond6, label %for.end

for.end:                                          ; preds = %for.body9
  br label %for.inc68

for.inc68:                                        ; preds = %for.end
  %inc69.64 = add nsw i64 %i64, 1
  %cmp4.next = icmp slt i64 %inc69.64, %nm2.64
  br i1 %cmp4.next, label %for.cond2, label %for.end70

for.end70:                                        ; preds = %for.inc68
  br label %for.inc71

for.inc71:                                        ; preds = %for.end70
  %inc72 = add nsw i32 %t, 1
  %cmp.next = icmp slt i32 %inc72, %tsteps
  br i1 %cmp.next, label %for.cond, label %for.end73.loopexit

for.end73.loopexit:                               ; preds = %for.inc71
  br label %for.end73

for.end73:                                        ; preds = %for.end73.loopexit, %entry
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
