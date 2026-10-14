; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_durbin(i32 noundef %n, ptr noundef %r, ptr noundef %y) #0 {
entry:
  %z = alloca [120 x double], align 16
  %cmp.entry = icmp sgt i32 %n, 0
  br i1 %cmp.entry, label %init, label %for.end50

init:
  %r0 = load double, ptr %r, align 8
  %fneg = fneg double %r0
  store double %fneg, ptr %y, align 8
  %fneg4 = fneg double %r0
  %cmp.outer0 = icmp sgt i32 %n, 1
  br i1 %cmp.outer0, label %for.body.preheader, label %for.end50

for.body.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc48, %for.body.preheader
  %k = phi i32 [ 1, %for.body.preheader ], [ %inc49, %for.inc48 ]
  %alpha = phi double [ %fneg4, %for.body.preheader ], [ %alpha.new, %for.inc48 ]
  %beta = phi double [ 1.000000e+00, %for.body.preheader ], [ %beta.new, %for.inc48 ]
  %mul = fmul double %alpha, %alpha
  %sub = fsub double 1.000000e+00, %mul
  %beta.new = fmul double %sub, %beta
  %k64 = sext i32 %k to i64

  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body
  %i = phi i32 [ 0, %for.body ], [ %inc, %for.body8 ]
  %sum = phi double [ 0.000000e+00, %for.body ], [ %add15, %for.body8 ]
  %sub9 = sub nsw i32 %k, %i
  %sub10 = sub nsw i32 %sub9, 1
  %idxprom = sext i32 %sub10 to i64
  %arrayidx11 = getelementptr inbounds double, ptr %r, i64 %idxprom
  %rv = load double, ptr %arrayidx11, align 8
  %idxprom12 = sext i32 %i to i64
  %arrayidx13 = getelementptr inbounds double, ptr %y, i64 %idxprom12
  %yv = load double, ptr %arrayidx13, align 8
  %mul14 = fmul double %rv, %yv
  %add15 = fadd double %sum, %mul14
  %inc = add nsw i32 %i, 1
  %cmp7 = icmp slt i32 %inc, %k
  br i1 %cmp7, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8, %for.body (via zero-trip not possible since k>=1)
  %sum.final = phi double [ %add15, %for.body8 ]
  %arrayidx17 = getelementptr inbounds double, ptr %r, i64 %k64
  %rk = load double, ptr %arrayidx17, align 8
  %add18 = fadd double %rk, %sum.final
  %fneg19 = fneg double %add18
  %alpha.new = fdiv double %fneg19, %beta.new

  br label %for.body22

for.body22:                                       ; preds = %for.body22, %for.end
  %i2 = phi i32 [ 0, %for.end ], [ %inc34, %for.body22 ]
  %arrayidx24 = getelementptr inbounds double, ptr %y, i64 %i2
  %yv2 = load double, ptr %arrayidx24, align 8
  %sub25 = sub nsw i32 %k, %i2
  %sub26 = sub nsw i32 %sub25, 1
  %idxprom27 = sext i32 %sub26 to i64
  %arrayidx28 = getelementptr inbounds double, ptr %y, i64 %idxprom27
  %yv3 = load double, ptr %arrayidx28, align 8
  %mul29 = fmul double %alpha.new, %yv3
  %add30 = fadd double %yv2, %mul29
  %idxprom31 = sext i32 %i2 to i64
  %arrayidx32 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom31
  store double %add30, ptr %arrayidx32, align 8
  %inc34 = add nsw i32 %i2, 1
  %cmp21 = icmp slt i32 %inc34, %k
  br i1 %cmp21, label %for.body22, label %for.end35

for.end35:                                        ; preds = %for.body22
  br label %for.body38

for.body38:                                       ; preds = %for.body38, %for.end35
  %i3 = phi i32 [ 0, %for.end35 ], [ %inc44, %for.body38 ]
  %idxprom39 = sext i32 %i3 to i64
  %arrayidx40 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom39
  %zv = load double, ptr %arrayidx40, align 8
  %arrayidx42 = getelementptr inbounds double, ptr %y, i64 %idxprom39
  store double %zv, ptr %arrayidx42, align 8
  %inc44 = add nsw i32 %i3, 1
  %cmp37 = icmp slt i32 %inc44, %k
  br i1 %cmp37, label %for.body38, label %for.end45

for.end45:                                        ; preds = %for.body38
  %arrayidx47 = getelementptr inbounds double, ptr %y, i64 %k64
  store double %alpha.new, ptr %arrayidx47, align 8
  br label %for.inc48

for.inc48:                                        ; preds = %for.end45
  %inc49 = add nsw i32 %k, 1
  %cmp = icmp slt i32 %inc49, %n
  br i1 %cmp, label %for.body, label %for.end50

for.end50:                                        ; preds = %for.inc48, %init, %entry
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
