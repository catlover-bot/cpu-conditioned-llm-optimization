; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_durbin(i32 noundef %n, ptr noundef %r, ptr noundef %y) #0 {
entry:
  %z = alloca [120 x double], align 16
  %arrayidx = getelementptr inbounds double, ptr %r, i64 0
  %0 = load double, ptr %arrayidx, align 8
  %fneg = fneg double %0
  %arrayidx2 = getelementptr inbounds double, ptr %y, i64 0
  store double %fneg, ptr %arrayidx2, align 8
  %fneg4 = fneg double %0
  %cmp.entry = icmp slt i32 1, %n
  br i1 %cmp.entry, label %for.body.preheader, label %for.end50

for.body.preheader:
  br label %for.body

for.body:                                         ; preds = %for.inc48, %for.body.preheader
  %alpha.0 = phi double [ %fneg4, %for.body.preheader ], [ %div, %for.inc48 ]
  %beta.0 = phi double [ 1.000000e+00, %for.body.preheader ], [ %mul5, %for.inc48 ]
  %k.0 = phi i32 [ 1, %for.body.preheader ], [ %inc49, %for.inc48 ]
  %mul = fmul double %alpha.0, %alpha.0
  %sub = fsub double 1.000000e+00, %mul
  %mul5 = fmul double %sub, %beta.0
  %cmp7.first = icmp slt i32 0, %k.0
  br i1 %cmp7.first, label %for.body8.preheader, label %for.end

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body8.preheader
  %i.06 = phi i32 [ 0, %for.body8.preheader ], [ %inc, %for.body8 ]
  %sum.06 = phi double [ 0.000000e+00, %for.body8.preheader ], [ %add15, %for.body8 ]
  %sub9 = sub nsw i32 %k.0, %i.06
  %sub10 = sub nsw i32 %sub9, 1
  %idxprom = sext i32 %sub10 to i64
  %arrayidx11 = getelementptr inbounds double, ptr %r, i64 %idxprom
  %1 = load double, ptr %arrayidx11, align 8
  %idxprom12 = sext i32 %i.06 to i64
  %arrayidx13 = getelementptr inbounds double, ptr %y, i64 %idxprom12
  %2 = load double, ptr %arrayidx13, align 8
  %mul14 = fmul double %1, %2
  %add15 = fadd double %sum.06, %mul14
  %inc = add nsw i32 %i.06, 1
  %cmp7 = icmp slt i32 %inc, %k.0
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:
  %add15.lcssa = phi double [ %add15, %for.body8 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %sum.1 = phi double [ 0.000000e+00, %for.body ], [ %add15.lcssa, %for.end.loopexit ]
  %idxprom16 = sext i32 %k.0 to i64
  %arrayidx17 = getelementptr inbounds double, ptr %r, i64 %idxprom16
  %3 = load double, ptr %arrayidx17, align 8
  %add18 = fadd double %3, %sum.1
  %fneg19 = fneg double %add18
  %div = fdiv double %fneg19, %mul5
  %cmp21.first = icmp slt i32 0, %k.0
  br i1 %cmp21.first, label %for.body22.preheader, label %for.end35

for.body22.preheader:
  br label %for.body22

for.body22:                                       ; preds = %for.body22, %for.body22.preheader
  %i.14 = phi i32 [ 0, %for.body22.preheader ], [ %inc34, %for.body22 ]
  %idxprom23 = sext i32 %i.14 to i64
  %arrayidx24 = getelementptr inbounds double, ptr %y, i64 %idxprom23
  %4 = load double, ptr %arrayidx24, align 8
  %sub25 = sub nsw i32 %k.0, %i.14
  %sub26 = sub nsw i32 %sub25, 1
  %idxprom27 = sext i32 %sub26 to i64
  %arrayidx28 = getelementptr inbounds double, ptr %y, i64 %idxprom27
  %5 = load double, ptr %arrayidx28, align 8
  %mul29 = fmul double %div, %5
  %add30 = fadd double %4, %mul29
  %idxprom31 = sext i32 %i.14 to i64
  %arrayidx32 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom31
  store double %add30, ptr %arrayidx32, align 8
  %inc34 = add nsw i32 %i.14, 1
  %cmp21 = icmp slt i32 %inc34, %k.0
  br i1 %cmp21, label %for.body22, label %for.end35.loopexit

for.end35.loopexit:
  br label %for.end35

for.end35:                                        ; preds = %for.end35.loopexit, %for.end
  %cmp37.first = icmp slt i32 0, %k.0
  br i1 %cmp37.first, label %for.body38.preheader, label %for.end45

for.body38.preheader:
  br label %for.body38

for.body38:                                       ; preds = %for.body38, %for.body38.preheader
  %i.22 = phi i32 [ 0, %for.body38.preheader ], [ %inc44, %for.body38 ]
  %idxprom39 = sext i32 %i.22 to i64
  %arrayidx40 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom39
  %6 = load double, ptr %arrayidx40, align 8
  %idxprom41 = sext i32 %i.22 to i64
  %arrayidx42 = getelementptr inbounds double, ptr %y, i64 %idxprom41
  store double %6, ptr %arrayidx42, align 8
  %inc44 = add nsw i32 %i.22, 1
  %cmp37 = icmp slt i32 %inc44, %k.0
  br i1 %cmp37, label %for.body38, label %for.end45.loopexit

for.end45.loopexit:
  br label %for.end45

for.end45:                                        ; preds = %for.end45.loopexit, %for.end35
  %idxprom46 = sext i32 %k.0 to i64
  %arrayidx47 = getelementptr inbounds double, ptr %y, i64 %idxprom46
  store double %div, ptr %arrayidx47, align 8
  %inc49 = add nsw i32 %k.0, 1
  %cmp = icmp slt i32 %inc49, %n
  br i1 %cmp, label %for.body, label %for.end50.loopexit

for.end50.loopexit:
  br label %for.end50

for.end50:                                        ; preds = %for.end50.loopexit, %entry
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
