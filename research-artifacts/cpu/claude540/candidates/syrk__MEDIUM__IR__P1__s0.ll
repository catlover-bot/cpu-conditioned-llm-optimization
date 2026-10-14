; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syrk(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end38

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.m.pos = icmp sgt i32 %m, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc36, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc37, %for.inc36 ]
  %i64 = sext i32 %i to i64
  %Crow = getelementptr inbounds double, ptr %C, i64 %n64
  %Crow.i = mul nsw i64 %i64, %n64
  %Crow.ptr = getelementptr inbounds double, ptr %C, i64 %Crow.i
  %Arow.i = mul nsw i64 %i64, %m64
  %Arow.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i
  %jlim1 = add nsw i32 %i, 1
  br label %for.body6.preheader

for.body6.preheader:
  br label %for.body6

for.body6:                                        ; preds = %for.body6.preheader, %for.body6
  %j1 = phi i32 [ 0, %for.body6.preheader ], [ %inc1, %for.body6 ]
  %j1.64 = sext i32 %j1 to i64
  %arrayidx8 = getelementptr inbounds double, ptr %Crow.ptr, i64 %j1.64
  %ld1 = load double, ptr %arrayidx8, align 8
  %mul = fmul double %ld1, %beta
  store double %mul, ptr %arrayidx8, align 8
  %inc1 = add nsw i32 %j1, 1
  %cmp5 = icmp sle i32 %inc1, %i
  br i1 %cmp5, label %for.body6, label %for.end

for.end:                                          ; preds = %for.body6, for.cond (via jlim check below not used)
  br i1 %cmp.m.pos, label %for.body11.preheader, label %for.end35

for.body11.preheader:
  br label %for.body11

for.body11:                                        ; preds = %for.body11.preheader, %for.inc33
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc34, %for.inc33 ]
  %k64 = sext i32 %k to i64
  %Aik.ptr = getelementptr inbounds double, ptr %Arow.ptr, i64 %k64
  %Aik = load double, ptr %Aik.ptr, align 8
  %alphaAik = fmul double %alpha, %Aik
  br label %for.body14.preheader

for.body14.preheader:
  br label %for.body14

for.body14:                                        ; preds = %for.body14.preheader, %for.body14
  %j2 = phi i32 [ 0, %for.body14.preheader ], [ %inc2, %for.body14 ]
  %j2.64 = sext i32 %j2 to i64
  %Ajrow.i = mul nsw i64 %j2.64, %m64
  %Ajrow.ptr = getelementptr inbounds double, ptr %A, i64 %Ajrow.i
  %Ajk.ptr = getelementptr inbounds double, ptr %Ajrow.ptr, i64 %k64
  %Ajk = load double, ptr %Ajk.ptr, align 8
  %mul24 = fmul double %alphaAik, %Ajk
  %Cij.ptr = getelementptr inbounds double, ptr %Crow.ptr, i64 %j2.64
  %Cij = load double, ptr %Cij.ptr, align 8
  %add29 = fadd double %Cij, %mul24
  store double %add29, ptr %Cij.ptr, align 8
  %inc2 = add nsw i32 %j2, 1
  %cmp13 = icmp sle i32 %inc2, %i
  br i1 %cmp13, label %for.body14, label %for.inc33

for.inc33:                                        ; preds = %for.body14
  %inc34 = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc34, %m
  br i1 %cmp10, label %for.body11, label %for.end35

for.end35:                                        ; preds = %for.inc33, %for.end
  br label %for.inc36

for.inc36:                                        ; preds = %for.end35
  %inc37 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc37, %n
  br i1 %cmp, label %for.cond, label %for.end38

for.end38:                                         ; preds = %for.inc36, %entry
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
