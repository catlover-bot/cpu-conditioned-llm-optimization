; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.t = icmp sgt i32 %tsteps, 0
  %do.work = and i1 %cmp.n, %cmp.t
  br i1 %do.work, label %preheader, label %for.end93

preheader:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %inner.nonempty = icmp sgt i32 %nm1, 1
  br label %for.cond

for.cond:
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br i1 %inner.nonempty, label %outer1.preheader, label %outer2.check

outer1.preheader:
  br label %for.body6

for.body6:
  %i1 = phi i32 [ 1, %outer1.preheader ], [ %inc42, %for.inc41 ]
  %i1_64 = sext i32 %i1 to i64
  %rowbase = mul nsw i64 %i1_64, %n64
  %row = getelementptr inbounds double, ptr %A, i64 %rowbase
  %rowup = getelementptr inbounds double, ptr %row, i64 %n64
  %rowdown = getelementptr inbounds double, ptr %row, i64 -1
  %rowdownbase = mul nsw i64 %n64, -1
  ; compute pointers for i-1 and i+1 rows directly
  %im1_64 = add nsw i64 %i1_64, -1
  %ip1_64 = add nsw i64 %i1_64, 1
  %rowim1base = mul nsw i64 %im1_64, %n64
  %rowip1base = mul nsw i64 %ip1_64, %n64
  %rowim1 = getelementptr inbounds double, ptr %A, i64 %rowim1base
  %rowip1 = getelementptr inbounds double, ptr %A, i64 %rowip1base
  %Brow = getelementptr inbounds double, ptr %B, i64 %rowbase
  br label %for.body10

for.body10:
  %j1 = phi i32 [ 1, %for.body6 ], [ %inc, %for.body10.inc ]
  %j1_64 = sext i32 %j1 to i64
  %jm1_64 = add nsw i64 %j1_64, -1
  %jp1_64 = add nsw i64 %j1_64, 1

  %pC = getelementptr inbounds double, ptr %row, i64 %j1_64
  %vC = load double, ptr %pC, align 8

  %pL = getelementptr inbounds double, ptr %row, i64 %jm1_64
  %vL = load double, ptr %pL, align 8
  %s1 = fadd double %vC, %vL

  %pR = getelementptr inbounds double, ptr %row, i64 %jp1_64
  %vR = load double, ptr %pR, align 8
  %s2 = fadd double %s1, %vR

  %pD = getelementptr inbounds double, ptr %rowip1, i64 %j1_64
  %vD = load double, ptr %pD, align 8
  %s3 = fadd double %s2, %vD

  %pU = getelementptr inbounds double, ptr %rowim1, i64 %j1_64
  %vU = load double, ptr %pU, align 8
  %s4 = fadd double %s3, %vU

  %res = fmul double 2.000000e-01, %s4

  %pB = getelementptr inbounds double, ptr %Brow, i64 %j1_64
  store double %res, ptr %pB, align 8

  br label %for.body10.inc

for.body10.inc:
  %inc = add nsw i32 %j1, 1
  %cmp.j1 = icmp slt i32 %inc, %nm1
  br i1 %cmp.j1, label %for.body10, label %for.inc41

for.inc41:
  %inc42 = add nsw i32 %i1, 1
  %cmp.i1 = icmp slt i32 %inc42, %nm1
  br i1 %cmp.i1, label %for.body6, label %outer2.check

outer2.check:
  br i1 %inner.nonempty, label %outer2.preheader, label %for.inc91

outer2.preheader:
  br label %for.body51.outer

for.body51.outer:
  %i2 = phi i32 [ 1, %outer2.preheader ], [ %inc89, %for.inc88 ]
  %i2_64 = sext i32 %i2 to i64
  %rowbase2 = mul nsw i64 %i2_64, %n64
  %row2 = getelementptr inbounds double, ptr %B, i64 %rowbase2
  %im1_64b = add nsw i64 %i2_64, -1
  %ip1_64b = add nsw i64 %i2_64, 1
  %rowim1baseB = mul nsw i64 %im1_64b, %n64
  %rowip1baseB = mul nsw i64 %ip1_64b, %n64
  %rowim1B = getelementptr inbounds double, ptr %B, i64 %rowim1baseB
  %rowip1B = getelementptr inbounds double, ptr %B, i64 %rowip1baseB
  %Arow2 = getelementptr inbounds double, ptr %A, i64 %rowbase2
  br label %for.body51

for.body51:
  %j2 = phi i32 [ 1, %for.body51.outer ], [ %inc86, %for.body51.inc ]
  %j2_64 = sext i32 %j2 to i64
  %jm1_64b = add nsw i64 %j2_64, -1
  %jp1_64b = add nsw i64 %j2_64, 1

  %pC2 = getelementptr inbounds double, ptr %row2, i64 %j2_64
  %vC2 = load double, ptr %pC2, align 8

  %pL2 = getelementptr inbounds double, ptr %row2, i64 %jm1_64b
  %vL2 = load double, ptr %pL2, align 8
  %t1 = fadd double %vC2, %vL2

  %pR2 = getelementptr inbounds double, ptr %row2, i64 %jp1_64b
  %vR2 = load double, ptr %pR2, align 8
  %t2 = fadd double %t1, %vR2

  %pD2 = getelementptr inbounds double, ptr %rowip1B, i64 %j2_64
  %vD2 = load double, ptr %pD2, align 8
  %t3 = fadd double %t2, %vD2

  %pU2 = getelementptr inbounds double, ptr %rowim1B, i64 %j2_64
  %vU2 = load double, ptr %pU2, align 8
  %t4 = fadd double %t3, %vU2

  %res2 = fmul double 2.000000e-01, %t4

  %pA2 = getelementptr inbounds double, ptr %Arow2, i64 %j2_64
  store double %res2, ptr %pA2, align 8

  br label %for.body51.inc

for.body51.inc:
  %inc86 = add nsw i32 %j2, 1
  %cmp.j2 = icmp slt i32 %inc86, %nm1
  br i1 %cmp.j2, label %for.body51, label %for.inc88

for.inc88:
  %inc89 = add nsw i32 %i2, 1
  %cmp.i2 = icmp slt i32 %inc89, %nm1
  br i1 %cmp.i2, label %for.body51.outer, label %for.inc91

for.inc91:
  %inc92 = add nsw i32 %t, 1
  %cmp.t2 = icmp slt i32 %inc92, %tsteps
  br i1 %cmp.t2, label %for.cond, label %for.end93

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
