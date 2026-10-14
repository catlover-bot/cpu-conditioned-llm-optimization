; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_durbin(i32 noundef %n, ptr noundef %r, ptr noundef %y) #0 {
entry:
  %z = alloca [120 x double], align 16
  %cmp0 = icmp sgt i32 %n, 0
  br i1 %cmp0, label %init.do, label %for.cond.preheader

init.do:
  %r0 = load double, ptr %r, align 8
  %negr0 = fneg double %r0
  store double %negr0, ptr %y, align 8
  br label %for.cond.preheader

for.cond.preheader:
  %beta.init = phi double [ 1.000000e+00, %entry ], [ 1.000000e+00, %init.do ]
  %alpha.init = phi double [ 0.000000e+00, %entry ], [ %negr0, %init.do ]
  br label %for.cond

for.cond:
  %k = phi i32 [ 1, %for.cond.preheader ], [ %inc49, %for.inc48 ]
  %alpha.outer = phi double [ %alpha.init, %for.cond.preheader ], [ %alpha.new, %for.inc48 ]
  %beta.outer = phi double [ %beta.init, %for.cond.preheader ], [ %beta.new, %for.inc48 ]
  %cmp = icmp slt i32 %k, %n
  br i1 %cmp, label %for.body, label %for.end50

for.body:
  %mul = fmul double %alpha.outer, %alpha.outer
  %sub = fsub double 1.000000e+00, %mul
  %beta.new = fmul double %sub, %beta.outer
  br label %for.cond6

for.cond6:
  %i1 = phi i32 [ 0, %for.body ], [ %inc, %for.inc ]
  %sum = phi double [ 0.000000e+00, %for.body ], [ %add15, %for.inc ]
  %cmp7 = icmp slt i32 %i1, %k
  br i1 %cmp7, label %for.body8, label %for.end

for.body8:
  %sub9 = sub nsw i32 %k, %i1
  %sub10 = sub nsw i32 %sub9, 1
  %idxprom = sext i32 %sub10 to i64
  %arrayidx11 = getelementptr inbounds double, ptr %r, i64 %idxprom
  %v11 = load double, ptr %arrayidx11, align 8
  %idxprom12 = sext i32 %i1 to i64
  %arrayidx13 = getelementptr inbounds double, ptr %y, i64 %idxprom12
  %v13 = load double, ptr %arrayidx13, align 8
  %mul14 = fmul double %v11, %v13
  %add15 = fadd double %sum, %mul14
  br label %for.inc

for.inc:
  %inc = add nsw i32 %i1, 1
  br label %for.cond6, !llvm.loop !6

for.end:
  %sum.final = phi double [ %sum, %for.cond6 ]
  %idxprom16 = sext i32 %k to i64
  %arrayidx17 = getelementptr inbounds double, ptr %r, i64 %idxprom16
  %v17 = load double, ptr %arrayidx17, align 8
  %add18 = fadd double %v17, %sum.final
  %fneg19 = fneg double %add18
  %alpha.new = fdiv double %fneg19, %beta.new
  br label %for.cond20

for.cond20:
  %i2 = phi i32 [ 0, %for.end ], [ %inc34, %for.inc33 ]
  %cmp21 = icmp slt i32 %i2, %k
  br i1 %cmp21, label %for.body22, label %for.end35

for.body22:
  %idxprom23 = sext i32 %i2 to i64
  %arrayidx24 = getelementptr inbounds double, ptr %y, i64 %idxprom23
  %v24 = load double, ptr %arrayidx24, align 8
  %sub25 = sub nsw i32 %k, %i2
  %sub26 = sub nsw i32 %sub25, 1
  %idxprom27 = sext i32 %sub26 to i64
  %arrayidx28 = getelementptr inbounds double, ptr %y, i64 %idxprom27
  %v28 = load double, ptr %arrayidx28, align 8
  %mul29 = fmul double %alpha.new, %v28
  %add30 = fadd double %v24, %mul29
  %idxprom31 = sext i32 %i2 to i64
  %arrayidx32 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom31
  store double %add30, ptr %arrayidx32, align 8
  br label %for.inc33

for.inc33:
  %inc34 = add nsw i32 %i2, 1
  br label %for.cond20, !llvm.loop !8

for.end35:
  br label %for.cond36

for.cond36:
  %i3 = phi i32 [ 0, %for.end35 ], [ %inc44, %for.inc43 ]
  %cmp37 = icmp slt i32 %i3, %k
  br i1 %cmp37, label %for.body38, label %for.end45

for.body38:
  %idxprom39 = sext i32 %i3 to i64
  %arrayidx40 = getelementptr inbounds [120 x double], ptr %z, i64 0, i64 %idxprom39
  %v40 = load double, ptr %arrayidx40, align 8
  %idxprom41 = sext i32 %i3 to i64
  %arrayidx42 = getelementptr inbounds double, ptr %y, i64 %idxprom41
  store double %v40, ptr %arrayidx42, align 8
  br label %for.inc43

for.inc43:
  %inc44 = add nsw i32 %i3, 1
  br label %for.cond36, !llvm.loop !9

for.end45:
  %idxprom46 = sext i32 %k to i64
  %arrayidx47 = getelementptr inbounds double, ptr %y, i64 %idxprom46
  store double %alpha.new, ptr %arrayidx47, align 8
  br label %for.inc48

for.inc48:
  %inc49 = add nsw i32 %k, 1
  br label %for.cond, !llvm.loop !10

for.end50:
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
!10 = distinct !{!10, !7}
