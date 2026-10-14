; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_1d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end37

preheader:
  %n64 = sext i32 %n to i64
  %upper64 = add nsw i64 %n64, -1
  br label %for.cond

for.cond:                                         ; preds = %for.inc35, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc36, %for.inc35 ]
  br label %for.body

for.body:                                         ; preds = %for.cond
  br label %for.body4

for.body4:                                        ; preds = %for.body4, %for.body
  %i64.1 = phi i64 [ 1, %for.body ], [ %inc.1, %for.body4 ]
  %im1 = add nsw i64 %i64.1, -1
  %arrayidx.im1 = getelementptr inbounds double, ptr %A, i64 %im1
  %v.im1 = load double, ptr %arrayidx.im1, align 8
  %arrayidx.i = getelementptr inbounds double, ptr %A, i64 %i64.1
  %v.i = load double, ptr %arrayidx.i, align 8
  %add8 = fadd double %v.im1, %v.i
  %ip1 = add nsw i64 %i64.1, 1
  %arrayidx.ip1 = getelementptr inbounds double, ptr %A, i64 %ip1
  %v.ip1 = load double, ptr %arrayidx.ip1, align 8
  %add12 = fadd double %add8, %v.ip1
  %mul = fmul double 3.333300e-01, %add12
  %arrayidx.B = getelementptr inbounds double, ptr %B, i64 %i64.1
  store double %mul, ptr %arrayidx.B, align 8
  %inc.1 = add nsw i64 %i64.1, 1
  %cmp3 = icmp slt i64 %inc.1, %upper64
  br i1 %cmp3, label %for.body4, label %for.end

for.end:                                          ; preds = %for.body4
  br label %for.body18

for.body18:                                       ; preds = %for.body18, %for.end
  %i64.2 = phi i64 [ 1, %for.end ], [ %inc.2, %for.body18 ]
  %im1.2 = add nsw i64 %i64.2, -1
  %arrayidx.Bim1 = getelementptr inbounds double, ptr %B, i64 %im1.2
  %v.Bim1 = load double, ptr %arrayidx.Bim1, align 8
  %arrayidx.Bi = getelementptr inbounds double, ptr %B, i64 %i64.2
  %v.Bi = load double, ptr %arrayidx.Bi, align 8
  %add24 = fadd double %v.Bim1, %v.Bi
  %ip1.2 = add nsw i64 %i64.2, 1
  %arrayidx.Bip1 = getelementptr inbounds double, ptr %B, i64 %ip1.2
  %v.Bip1 = load double, ptr %arrayidx.Bip1, align 8
  %add28 = fadd double %add24, %v.Bip1
  %mul29 = fmul double 3.333300e-01, %add28
  %arrayidx.A = getelementptr inbounds double, ptr %A, i64 %i64.2
  store double %mul29, ptr %arrayidx.A, align 8
  %inc.2 = add nsw i64 %i64.2, 1
  %cmp17 = icmp slt i64 %inc.2, %upper64
  br i1 %cmp17, label %for.body18, label %for.end34

for.end34:                                        ; preds = %for.body18
  br label %for.inc35

for.inc35:                                        ; preds = %for.end34
  %inc36 = add nsw i32 %t, 1
  %cmp.loop = icmp slt i32 %inc36, %tsteps
  br i1 %cmp.loop, label %for.cond, label %for.end37

for.end37:                                        ; preds = %for.inc35, %entry
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
