; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_durbin(i32 noundef %n, ptr noundef %r, ptr noundef %y) #0 {
entry:
  %z = alloca [40 x double], align 16
  %cmp.entry = icmp slt i32 %n, 1
  %r0 = load double, ptr %r, align 8
  %fneg = fneg double %r0
  store double %fneg, ptr %y, align 8
  br i1 %cmp.entry, label %for.end50, label %preheader

preheader:
  br label %for.cond

for.cond:                                         ; preds = %for.inc48, %preheader
  %k = phi i32 [ 1, %preheader ], [ %inc49, %for.inc48 ]
  %alpha.0 = phi double [ %fneg, %preheader ], [ %alpha.new, %for.inc48 ]
  %beta.0 = phi double [ 1.000000e+00, %preheader ], [ %beta.new, %for.inc48 ]
  %cmp = icmp slt i32 %k, %n
  br i1 %cmp, label %for.body, label %for.end50

for.body:                                         ; preds = %for.cond
  %mul = fmul double %alpha.0, %alpha.0
  %sub = fsub double 1.000000e+00, %mul
  %beta.new = fmul double %sub, %beta.0
  br label %for.cond6

for.cond6:                                        ; preds = %for.body8, %for.body
  %i6 = phi i32 [ 0, %for.body ], [ %inc, %for.body8 ]
  %sum.0 = phi double [ 0.000000e+00, %for.body ], [ %add15, %for.body8 ]
  %cmp7 = icmp slt i32 %i6, %k
  br i1 %cmp7, label %for.body8, label %for.end

for.body8:                                        ; preds = %for.cond6
  %sub9 = sub nsw i32 %k, %i6
  %sub10 = sub nsw i32 %sub9, 1
  %idxprom = sext i32 %sub10 to i64
  %arrayidx11 = getelementptr inbounds double, ptr %r, i64 %idxprom
  %rv = load double, ptr %arrayidx11, align 8
  %idxprom12 = sext i32 %i6 to i64
  %arrayidx13 = getelementptr inbounds double, ptr %y, i64 %idxprom12
  %yv = load double, ptr %arrayidx13, align 8
  %mul14 = fmul double %rv, %yv
  %add15 = fadd double %sum.0, %mul14
  %inc = add nsw i32 %i6, 1
  br label %for.cond6, !llvm.loop !6

for.end:                                          ; preds = %for.cond6
  %idxprom16 = sext i32 %k to i64
  %arrayidx17 = getelementptr inbounds double, ptr %r, i64 %idxprom16
  %rk = load double, ptr %arrayidx17, align 8
  %add18 = fadd double %rk, %sum.0
  %fneg19 = fneg double %add18
  %alpha.new = fdiv double %fneg19, %beta.new
  br label %for.cond20

for.cond20:                                       ; preds = %for.body22, %for.end
  %i20 = phi i32 [ 0, %for.end ], [ %inc34, %for.body22 ]
  %cmp21 = icmp slt i32 %i20, %k
  br i1 %cmp21, label %for.body22, label %for.end35

for.body22:                                       ; preds = %for.cond20
  %idxprom23 = sext i32 %i20 to i64
  %arrayidx24 = getelementptr inbounds double, ptr %y, i64 %idxprom23
  %yv2 = load double, ptr %arrayidx24, align 8
  %sub25 = sub nsw i32 %k, %i20
  %sub26 = sub nsw i32 %sub25, 1
  %idxprom27 = sext i32 %sub26 to i64
  %arrayidx28 = getelementptr inbounds double, ptr %y, i64 %idxprom27
  %yv3 = load double, ptr %arrayidx28, align 8
  %mul29 = fmul double %alpha.new, %yv3
  %add30 = fadd double %yv2, %mul29
  %idxprom31 = sext i32 %i20 to i64
  %arrayidx32 = getelementptr inbounds [40 x double], ptr %z, i64 0, i64 %idxprom31
  store double %add30, ptr %arrayidx32, align 8
  %inc34 = add nsw i32 %i20, 1
  br label %for.cond20, !llvm.loop !8

for.end35:                                        ; preds = %for.cond20
  br label %for.cond36

for.cond36:                                       ; preds = %for.body38, %for.end35
  %i36 = phi i32 [ 0, %for.end35 ], [ %inc44, %for.body38 ]
  %cmp37 = icmp slt i32 %i36, %k
  br i1 %cmp37, label %for.body38, label %for.end45

for.body38:                                       ; preds = %for.cond36
  %idxprom39 = sext i32 %i36 to i64
  %arrayidx40 = getelementptr inbounds [40 x double], ptr %z, i64 0, i64 %idxprom39
  %zv = load double, ptr %arrayidx40, align 8
  %idxprom41 = sext i32 %i36 to i64
  %arrayidx42 = getelementptr inbounds double, ptr %y, i64 %idxprom41
  store double %zv, ptr %arrayidx42, align 8
  %inc44 = add nsw i32 %i36, 1
  br label %for.cond36, !llvm.loop !9

for.end45:                                        ; preds = %for.cond36
  %idxprom46 = sext i32 %k to i64
  %arrayidx47 = getelementptr inbounds double, ptr %y, i64 %idxprom46
  store double %alpha.new, ptr %arrayidx47, align 8
  %inc49 = add nsw i32 %k, 1
  br label %for.inc48

for.inc48:
  br label %for.cond, !llvm.loop !10

for.end50:                                        ; preds = %for.cond, %entry
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
