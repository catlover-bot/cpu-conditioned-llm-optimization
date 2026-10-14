; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.t = icmp sgt i32 %tsteps, 0
  %and.entry = and i1 %cmp.n, %cmp.t
  br i1 %and.entry, label %check.inner, label %for.end93

check.inner:
  %sub.n1 = sub nsw i32 %n, 1
  %inner.nonempty = icmp sgt i32 %sub.n1, 1
  br i1 %inner.nonempty, label %preheader, label %for.end93

preheader:
  %n64 = zext i32 %n to i64
  %sub.n1.64 = zext i32 %sub.n1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc91, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br label %for.body.i1

for.body.i1:                                      ; preds = %for.inc41, %for.cond
  %i1 = phi i64 [ 1, %for.cond ], [ %inc42.1, %for.inc41 ]
  %irow.A = mul nsw i64 %i1, %n64
  %rowbase.A = getelementptr inbounds double, ptr %A, i64 %irow.A
  %ip1.1 = add nsw i64 %i1, 1
  %irowp1.A = mul nsw i64 %ip1.1, %n64
  %rowp1base.A = getelementptr inbounds double, ptr %A, i64 %irowp1.A
  %im1.1 = sub nsw i64 %i1, 1
  %irowm1.A = mul nsw i64 %im1.1, %n64
  %rowm1base.A = getelementptr inbounds double, ptr %A, i64 %irowm1.A
  %irow.B = mul nsw i64 %i1, %n64
  %rowbase.B = getelementptr inbounds double, ptr %B, i64 %irow.B
  br label %for.body10

for.body10:                                       ; preds = %for.body10, %for.body.i1
  %j1 = phi i64 [ 1, %for.body.i1 ], [ %inc.1, %for.body10 ]
  %center.ptr = getelementptr inbounds double, ptr %rowbase.A, i64 %j1
  %center.v = load double, ptr %center.ptr, align 8
  %jm1 = sub nsw i64 %j1, 1
  %left.ptr = getelementptr inbounds double, ptr %rowbase.A, i64 %jm1
  %left.v = load double, ptr %left.ptr, align 8
  %add18 = fadd double %center.v, %left.v
  %jp1 = add nsw i64 %j1, 1
  %right.ptr = getelementptr inbounds double, ptr %rowbase.A, i64 %jp1
  %right.v = load double, ptr %right.ptr, align 8
  %add24 = fadd double %add18, %right.v
  %down.ptr = getelementptr inbounds double, ptr %rowp1base.A, i64 %j1
  %down.v = load double, ptr %down.ptr, align 8
  %add30 = fadd double %add24, %down.v
  %up.ptr = getelementptr inbounds double, ptr %rowm1base.A, i64 %j1
  %up.v = load double, ptr %up.ptr, align 8
  %add36 = fadd double %add30, %up.v
  %mul = fmul double 2.000000e-01, %add36
  %Bdst.ptr = getelementptr inbounds double, ptr %rowbase.B, i64 %j1
  store double %mul, ptr %Bdst.ptr, align 8
  %inc.1 = add nsw i64 %j1, 1
  %cmp9 = icmp slt i64 %inc.1, %sub.n1.64
  br i1 %cmp9, label %for.body10, label %for.inc41

for.inc41:                                        ; preds = %for.body10
  %inc42.1 = add nsw i64 %i1, 1
  %cmp5 = icmp slt i64 %inc42.1, %sub.n1.64
  br i1 %cmp5, label %for.body.i1, label %for.end43

for.end43:                                        ; preds = %for.inc41
  br label %for.body.i2

for.body.i2:                                      ; preds = %for.inc88, %for.end43
  %i2 = phi i64 [ 1, %for.end43 ], [ %inc42.2, %for.inc88 ]
  %irow.B2 = mul nsw i64 %i2, %n64
  %rowbase.B2 = getelementptr inbounds double, ptr %B, i64 %irow.B2
  %ip1.2 = add nsw i64 %i2, 1
  %irowp1.B2 = mul nsw i64 %ip1.2, %n64
  %rowp1base.B2 = getelementptr inbounds double, ptr %B, i64 %irowp1.B2
  %im1.2 = sub nsw i64 %i2, 1
  %irowm1.B2 = mul nsw i64 %im1.2, %n64
  %rowm1base.B2 = getelementptr inbounds double, ptr %B, i64 %irowm1.B2
  %irow.A2 = mul nsw i64 %i2, %n64
  %rowbase.A2 = getelementptr inbounds double, ptr %A, i64 %irow.A2
  br label %for.body51

for.body51:                                       ; preds = %for.body51, %for.body.i2
  %j2 = phi i64 [ 1, %for.body.i2 ], [ %inc.2, %for.body51 ]
  %center.ptr2 = getelementptr inbounds double, ptr %rowbase.B2, i64 %j2
  %center.v2 = load double, ptr %center.ptr2, align 8
  %jm1.2 = sub nsw i64 %j2, 1
  %left.ptr2 = getelementptr inbounds double, ptr %rowbase.B2, i64 %jm1.2
  %left.v2 = load double, ptr %left.ptr2, align 8
  %add61 = fadd double %center.v2, %left.v2
  %jp1.2 = add nsw i64 %j2, 1
  %right.ptr2 = getelementptr inbounds double, ptr %rowbase.B2, i64 %jp1.2
  %right.v2 = load double, ptr %right.ptr2, align 8
  %add67 = fadd double %add61, %right.v2
  %down.ptr2 = getelementptr inbounds double, ptr %rowp1base.B2, i64 %j2
  %down.v2 = load double, ptr %down.ptr2, align 8
  %add73 = fadd double %add67, %down.v2
  %up.ptr2 = getelementptr inbounds double, ptr %rowm1base.B2, i64 %j2
  %up.v2 = load double, ptr %up.ptr2, align 8
  %add79 = fadd double %add73, %up.v2
  %mul80 = fmul double 2.000000e-01, %add79
  %Adst.ptr = getelementptr inbounds double, ptr %rowbase.A2, i64 %j2
  store double %mul80, ptr %Adst.ptr, align 8
  %inc.2 = add nsw i64 %j2, 1
  %cmp50 = icmp slt i64 %inc.2, %sub.n1.64
  br i1 %cmp50, label %for.body51, label %for.inc88

for.inc88:                                        ; preds = %for.body51
  %inc42.2 = add nsw i64 %i2, 1
  %cmp46 = icmp slt i64 %inc42.2, %sub.n1.64
  br i1 %cmp46, label %for.body.i2, label %for.end90

for.end90:                                        ; preds = %for.inc88
  br label %for.inc91

for.inc91:                                        ; preds = %for.end90
  %inc92 = add nsw i32 %t, 1
  %cmp = icmp slt i32 %inc92, %tsteps
  br i1 %cmp, label %for.cond, label %for.end93

for.end93:                                        ; preds = %entry, %check.inner, %for.inc91
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
