; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_seidel_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A) #0 {
entry:
  %cmp.tsteps = icmp sgt i32 %tsteps, 0
  br i1 %cmp.tsteps, label %check.n, label %for.end73

check.n:
  %n64 = sext i32 %n to i64
  %cmp.n = icmp sgt i32 %n, 2
  br i1 %cmp.n, label %preheader.t, label %for.end73

preheader.t:
  ; i and j loop bounds: i,j from 1 to n-2 inclusive
  %n.sub2 = add nsw i32 %n, -2
  %n.sub2.64 = sext i32 %n.sub2 to i64
  br label %for.t

for.t:                                            ; preds = %for.inc71, %preheader.t
  %t = phi i32 [ 0, %preheader.t ], [ %inc72, %for.inc71 ]
  br label %for.i

for.i:                                            ; preds = %for.inc68, %for.t
  %i64 = phi i64 [ 1, %for.t ], [ %i64.next, %for.inc68 ]
  ; row pointers: row i-1, row i, row i+1
  %im1 = sub nsw i64 %i64, 1
  %ip1 = add nsw i64 %i64, 1
  %rowim1.off = mul nsw i64 %im1, %n64
  %rowi.off = mul nsw i64 %i64, %n64
  %rowip1.off = mul nsw i64 %ip1, %n64
  %rowim1 = getelementptr inbounds double, ptr %A, i64 %rowim1.off
  %rowi = getelementptr inbounds double, ptr %A, i64 %rowi.off
  %rowip1 = getelementptr inbounds double, ptr %A, i64 %rowip1.off
  br label %for.j

for.j:                                            ; preds = %for.body9, %for.i
  %j64 = phi i64 [ 1, %for.i ], [ %j64.next, %for.body9 ]
  br label %for.body9

for.body9:
  %jm1 = sub nsw i64 %j64, 1
  %jp1 = add nsw i64 %j64, 1

  %p.im1.jm1 = getelementptr inbounds double, ptr %rowim1, i64 %jm1
  %v.im1.jm1 = load double, ptr %p.im1.jm1, align 8

  %p.im1.j = getelementptr inbounds double, ptr %rowim1, i64 %j64
  %v.im1.j = load double, ptr %p.im1.j, align 8
  %s1 = fadd double %v.im1.jm1, %v.im1.j

  %p.im1.jp1 = getelementptr inbounds double, ptr %rowim1, i64 %jp1
  %v.im1.jp1 = load double, ptr %p.im1.jp1, align 8
  %s2 = fadd double %s1, %v.im1.jp1

  %p.i.jm1 = getelementptr inbounds double, ptr %rowi, i64 %jm1
  %v.i.jm1 = load double, ptr %p.i.jm1, align 8
  %s3 = fadd double %s2, %v.i.jm1

  %p.i.j = getelementptr inbounds double, ptr %rowi, i64 %j64
  %v.i.j = load double, ptr %p.i.j, align 8
  %s4 = fadd double %s3, %v.i.j

  %p.i.jp1 = getelementptr inbounds double, ptr %rowi, i64 %jp1
  %v.i.jp1 = load double, ptr %p.i.jp1, align 8
  %s5 = fadd double %s4, %v.i.jp1

  %p.ip1.jm1 = getelementptr inbounds double, ptr %rowip1, i64 %jm1
  %v.ip1.jm1 = load double, ptr %p.ip1.jm1, align 8
  %s6 = fadd double %s5, %v.ip1.jm1

  %p.ip1.j = getelementptr inbounds double, ptr %rowip1, i64 %j64
  %v.ip1.j = load double, ptr %p.ip1.j, align 8
  %s7 = fadd double %s6, %v.ip1.j

  %p.ip1.jp1 = getelementptr inbounds double, ptr %rowip1, i64 %jp1
  %v.ip1.jp1 = load double, ptr %p.ip1.jp1, align 8
  %s8 = fadd double %s7, %v.ip1.jp1

  %div = fdiv double %s8, 9.000000e+00
  store double %div, ptr %p.i.j, align 8

  %j64.next = add nsw i64 %j64, 1
  %cmp.j = icmp sle i64 %j64.next, %n.sub2.64
  br i1 %cmp.j, label %for.j, label %for.inc68

for.inc68:                                        ; preds = %for.body9
  %i64.next = add nsw i64 %i64, 1
  %cmp.i = icmp sle i64 %i64.next, %n.sub2.64
  br i1 %cmp.i, label %for.i, label %for.end70

for.end70:                                        ; preds = %for.inc68
  br label %for.inc71

for.inc71:                                        ; preds = %for.end70
  %inc72 = add nsw i32 %t, 1
  %cmp.t = icmp slt i32 %inc72, %tsteps
  br i1 %cmp.t, label %for.t, label %for.end73

for.end73:                                        ; preds = %for.inc71, %entry, %check.n
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
