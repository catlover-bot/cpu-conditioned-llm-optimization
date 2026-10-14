; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_mvt(i32 noundef %n, ptr noundef %x1, ptr noundef %x2, ptr noundef %y_1, ptr noundef %y_2, ptr noundef %A) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer1.preheader, label %for.end20

outer1.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:
  %i = phi i64 [ 0, %outer1.preheader ], [ %inc19, %for.inc18 ]
  %row.base = mul nsw i64 %i, %n64
  %arrayidx17 = getelementptr inbounds double, ptr %x1, i64 %i
  br label %for.body8

for.body8:
  %j = phi i64 [ 0, %for.body ], [ %inc, %for.body8 ]
  %acc = phi double [ 0.0, %for.body ], [ %add15, %for.body8 ]
  %Aidx = add nsw i64 %row.base, %j
  %arrayidx12 = getelementptr inbounds double, ptr %A, i64 %Aidx
  %Aval = load double, ptr %arrayidx12, align 8
  %arrayidx14 = getelementptr inbounds double, ptr %y_1, i64 %j
  %yval = load double, ptr %arrayidx14, align 8
  %mul = fmul double %Aval, %yval
  %add15 = fadd double %acc, %mul
  %inc = add nsw i64 %j, 1
  %cmp7 = icmp slt i64 %inc, %n64
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:
  %final.acc = phi double [ %add15, %for.body8 ]
  %x1val = load double, ptr %arrayidx17, align 8
  %sum = fadd double %x1val, %final.acc
  store double %sum, ptr %arrayidx17, align 8
  br label %for.inc18

for.inc18:
  %inc19 = add nsw i64 %i, 1
  %cmp = icmp slt i64 %inc19, %n64
  br i1 %cmp, label %for.body, label %for.end20

for.end20:
  br i1 %cmp.n, label %outer2.preheader, label %for.end44

outer2.preheader:
  br label %for.body23

for.body23:
  %i2 = phi i64 [ 0, %outer2.preheader ], [ %inc43, %for.inc42 ]
  %arrayidx38 = getelementptr inbounds double, ptr %x2, i64 %i2
  br label %for.body26

for.body26:
  %j2 = phi i64 [ 0, %for.body23 ], [ %inc40, %for.body26 ]
  %acc2 = phi double [ 0.0, %for.body23 ], [ %add36, %for.body26 ]
  %row2.base = mul nsw i64 %j2, %n64
  %Aidx2 = add nsw i64 %row2.base, %i2
  %arrayidx32 = getelementptr inbounds double, ptr %A, i64 %Aidx2
  %Aval2 = load double, ptr %arrayidx32, align 8
  %arrayidx34 = getelementptr inbounds double, ptr %y_2, i64 %j2
  %yval2 = load double, ptr %arrayidx34, align 8
  %mul35 = fmul double %Aval2, %yval2
  %add36 = fadd double %acc2, %mul35
  %inc40 = add nsw i64 %j2, 1
  %cmp25 = icmp slt i64 %inc40, %n64
  br i1 %cmp25, label %for.body26, label %for.end41.loopexit

for.end41.loopexit:
  %final.acc2 = phi double [ %add36, %for.body26 ]
  %x2val = load double, ptr %arrayidx38, align 8
  %sum2 = fadd double %x2val, %final.acc2
  store double %sum2, ptr %arrayidx38, align 8
  br label %for.inc42

for.inc42:
  %inc43 = add nsw i64 %i2, 1
  %cmp22 = icmp slt i64 %inc43, %n64
  br i1 %cmp22, label %for.body23, label %for.end44

for.end44:
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
