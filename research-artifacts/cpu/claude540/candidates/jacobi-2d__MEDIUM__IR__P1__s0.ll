; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  br i1 %cmp.n, label %check.tsteps, label %for.end93

check.tsteps:
  %cmp.t = icmp sgt i32 %tsteps, 0
  br i1 %cmp.t, label %preheader, label %for.end93

preheader:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm1.64 = sext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc91, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br label %for.body.i.outer

for.body.i.outer:
  br label %for.cond4

for.cond4:                                         ; preds = %for.inc41, %for.body.i.outer
  %i = phi i64 [ 1, %for.body.i.outer ], [ %inc42.64, %for.inc41 ]
  %cmp5 = icmp slt i64 %i, %nm1.64
  br i1 %cmp5, label %for.body6.preheader, label %for.end43

for.body6.preheader:
  %i.rowoff = mul nsw i64 %i, %n64
  %rowA.cur = getelementptr inbounds double, ptr %A, i64 %i.rowoff
  %im1 = sub nsw i64 %i, 1
  %im1.rowoff = mul nsw i64 %im1, %n64
  %rowA.prev = getelementptr inbounds double, ptr %A, i64 %im1.rowoff
  %ip1 = add nsw i64 %i, 1
  %ip1.rowoff = mul nsw i64 %ip1, %n64
  %rowA.next = getelementptr inbounds double, ptr %A, i64 %ip1.rowoff
  %rowB.cur = getelementptr inbounds double, ptr %B, i64 %i.rowoff
  br label %for.body10

for.body10:                                       ; preds = %for.body10, %for.body6.preheader
  %j = phi i64 [ 1, %for.body6.preheader ], [ %jinc, %for.body10 ]
  %pC = getelementptr inbounds double, ptr %rowA.cur, i64 %j
  %vC = load double, ptr %pC, align 8
  %jm1 = sub nsw i64 %j, 1
  %pL = getelementptr inbounds double, ptr %rowA.cur, i64 %jm1
  %vL = load double, ptr %pL, align 8
  %add18 = fadd double %vC, %vL
  %jp1 = add nsw i64 %j, 1
  %pR = getelementptr inbounds double, ptr %rowA.cur, i64 %jp1
  %vR = load double, ptr %pR, align 8
  %add24 = fadd double %add18, %vR
  %pD = getelementptr inbounds double, ptr %rowA.next, i64 %j
  %vD = load double, ptr %pD, align 8
  %add30 = fadd double %add24, %vD
  %pU = getelementptr inbounds double, ptr %rowA.prev, i64 %j
  %vU = load double, ptr %pU, align 8
  %add36 = fadd double %add30, %vU
  %mul = fmul double 2.000000e-01, %add36
  %pOut = getelementptr inbounds double, ptr %rowB.cur, i64 %j
  store double %mul, ptr %pOut, align 8
  %jinc = add nsw i64 %j, 1
  %cmp9 = icmp slt i64 %jinc, %nm1.64
  br i1 %cmp9, label %for.body10, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit
  br label %for.inc41

for.inc41:                                        ; preds = %for.end
  %inc42.64 = add nsw i64 %i, 1
  br label %for.cond4

for.end43:                                        ; preds = %for.cond4
  br label %for.cond44

for.cond44:                                       ; preds = %for.inc88, %for.end43
  %i2 = phi i64 [ 1, %for.end43 ], [ %inc89.64, %for.inc88 ]
  %cmp46 = icmp slt i64 %i2, %nm1.64
  br i1 %cmp46, label %for.body47.preheader, label %for.end90

for.body47.preheader:
  %i2.rowoff = mul nsw i64 %i2, %n64
  %rowB.cur2 = getelementptr inbounds double, ptr %B, i64 %i2.rowoff
  %i2m1 = sub nsw i64 %i2, 1
  %i2m1.rowoff = mul nsw i64 %i2m1, %n64
  %rowB.prev = getelementptr inbounds double, ptr %B, i64 %i2m1.rowoff
  %i2p1 = add nsw i64 %i2, 1
  %i2p1.rowoff = mul nsw i64 %i2p1, %n64
  %rowB.next = getelementptr inbounds double, ptr %B, i64 %i2p1.rowoff
  %rowA.cur2 = getelementptr inbounds double, ptr %A, i64 %i2.rowoff
  br label %for.body51

for.body51:                                       ; preds = %for.body51, %for.body47.preheader
  %j2 = phi i64 [ 1, %for.body47.preheader ], [ %j2inc, %for.body51 ]
  %pC2 = getelementptr inbounds double, ptr %rowB.cur2, i64 %j2
  %vC2 = load double, ptr %pC2, align 8
  %j2m1 = sub nsw i64 %j2, 1
  %pL2 = getelementptr inbounds double, ptr %rowB.cur2, i64 %j2m1
  %vL2 = load double, ptr %pL2, align 8
  %add61 = fadd double %vC2, %vL2
  %j2p1 = add nsw i64 %j2, 1
  %pR2 = getelementptr inbounds double, ptr %rowB.cur2, i64 %j2p1
  %vR2 = load double, ptr %pR2, align 8
  %add67 = fadd double %add61, %vR2
  %pD2 = getelementptr inbounds double, ptr %rowB.next, i64 %j2
  %vD2 = load double, ptr %pD2, align 8
  %add73 = fadd double %add67, %vD2
  %pU2 = getelementptr inbounds double, ptr %rowB.prev, i64 %j2
  %vU2 = load double, ptr %pU2, align 8
  %add79 = fadd double %add73, %vU2
  %mul80 = fmul double 2.000000e-01, %add79
  %pOut2 = getelementptr inbounds double, ptr %rowA.cur2, i64 %j2
  store double %mul80, ptr %pOut2, align 8
  %j2inc = add nsw i64 %j2, 1
  %cmp50 = icmp slt i64 %j2inc, %nm1.64
  br i1 %cmp50, label %for.body51, label %for.end87.loopexit

for.end87.loopexit:
  br label %for.end87

for.end87:                                        ; preds = %for.end87.loopexit
  br label %for.inc88

for.inc88:                                        ; preds = %for.end87
  %inc89.64 = add nsw i64 %i2, 1
  br label %for.cond44

for.end90:                                        ; preds = %for.cond44
  br label %for.inc91

for.inc91:                                        ; preds = %for.end90
  %inc92 = add nsw i32 %t, 1
  %cmp.tloop = icmp slt i32 %inc92, %tsteps
  br i1 %cmp.tloop, label %for.cond, label %for.end93

for.end93:                                        ; preds = %for.inc91, %check.tsteps, %entry
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
