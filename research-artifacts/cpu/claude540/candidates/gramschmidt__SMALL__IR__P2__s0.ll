; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.mn = icmp sgt i32 %m, 0
  %cmp.nn = icmp sgt i32 %n, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %entry
  %k = phi i32 [ 0, %entry ], [ %inc93, %for.inc92 ]
  %cmp = icmp slt i32 %k, %n
  br i1 %cmp, label %for.body, label %for.end94

for.body:                                         ; preds = %for.cond
  %k64 = sext i32 %k to i64
  br i1 %cmp.mn, label %for.body6.preheader, label %for.end

for.body6.preheader:                              ; preds = %for.body
  br label %for.body8

for.body8:                                        ; preds = %for.body6.preheader, %for.body8
  %i.06 = phi i64 [ 0, %for.body6.preheader ], [ %inc.i, %for.body8 ]
  %nrm.05 = phi double [ 0.000000e+00, %for.body6.preheader ], [ %add15, %for.body8 ]
  %rowA = mul nsw i64 %i.06, %n64
  %off = add nsw i64 %rowA, %k64
  %arrayidx10 = getelementptr inbounds double, ptr %A, i64 %off
  %v = load double, ptr %arrayidx10, align 8
  %mul = fmul double %v, %v
  %add15 = fadd double %nrm.05, %mul
  %inc.i = add nsw i64 %i.06, 1
  %exit.cond = icmp eq i64 %inc.i, %m64
  br i1 %exit.cond, label %for.end, label %for.body8

for.end:                                          ; preds = %for.body8, %for.body
  %nrm.lcssa = phi double [ 0.000000e+00, %for.body ], [ %add15, %for.body8 ]
  %call = call double @sqrt(double noundef %nrm.lcssa) #2
  %rowR_k = mul nsw i64 %k64, %n64
  %offRkk = add nsw i64 %rowR_k, %k64
  %arrayidx19 = getelementptr inbounds double, ptr %R, i64 %offRkk
  store double %call, ptr %arrayidx19, align 8
  br i1 %cmp.mn, label %for.body22.preheader, label %for.end37

for.body22.preheader:                             ; preds = %for.end
  br label %for.body22

for.body22:                                       ; preds = %for.body22.preheader, %for.body22
  %i22 = phi i64 [ 0, %for.body22.preheader ], [ %inc36.i, %for.body22 ]
  %rowA22 = mul nsw i64 %i22, %n64
  %offA22 = add nsw i64 %rowA22, %k64
  %arrayidx26 = getelementptr inbounds double, ptr %A, i64 %offA22
  %vA22 = load double, ptr %arrayidx26, align 8
  %div = fdiv double %vA22, %call
  %rowQ22 = mul nsw i64 %i22, %n64
  %offQ22 = add nsw i64 %rowQ22, %k64
  %arrayidx34 = getelementptr inbounds double, ptr %Q, i64 %offQ22
  store double %div, ptr %arrayidx34, align 8
  %inc36.i = add nsw i64 %i22, 1
  %exit.cond22 = icmp eq i64 %inc36.i, %m64
  br i1 %exit.cond22, label %for.end37, label %for.body22

for.end37:                                        ; preds = %for.body22, %for.end
  %kp1 = add nsw i32 %k, 1
  %cmp40.check = icmp slt i32 %kp1, %n
  br i1 %cmp40.check, label %for.body41.preheader, label %for.end91

for.body41.preheader:                             ; preds = %for.end37
  br label %for.body41

for.body41:                                       ; preds = %for.body41.preheader, %for.inc89
  %j = phi i32 [ %kp1, %for.body41.preheader ], [ %inc90, %for.inc89 ]
  %j64 = sext i32 %j to i64
  %rowR_k41 = mul nsw i64 %k64, %n64
  %offRkj = add nsw i64 %rowR_k41, %j64
  %arrayidx45 = getelementptr inbounds double, ptr %R, i64 %offRkj
  store double 0.000000e+00, ptr %arrayidx45, align 8
  br i1 %cmp.mn, label %for.body48.preheader, label %for.end65

for.body48.preheader:                             ; preds = %for.body41
  br label %for.body48

for.body48:                                       ; preds = %for.body48.preheader, %for.body48
  %i48 = phi i64 [ 0, %for.body48.preheader ], [ %inc64.i, %for.body48 ]
  %rowQ48 = mul nsw i64 %i48, %n64
  %offQ48 = add nsw i64 %rowQ48, %k64
  %arrayidx52 = getelementptr inbounds double, ptr %Q, i64 %offQ48
  %vQ48 = load double, ptr %arrayidx52, align 8
  %rowA48 = mul nsw i64 %i48, %n64
  %offA48 = add nsw i64 %rowA48, %j64
  %arrayidx56 = getelementptr inbounds double, ptr %A, i64 %offA48
  %vA48 = load double, ptr %arrayidx56, align 8
  %mul57 = fmul double %vQ48, %vA48
  %curR = load double, ptr %arrayidx45, align 8
  %add62 = fadd double %curR, %mul57
  store double %add62, ptr %arrayidx45, align 8
  %inc64.i = add nsw i64 %i48, 1
  %exit.cond48 = icmp eq i64 %inc64.i, %m64
  br i1 %exit.cond48, label %for.end65, label %for.body48

for.end65:                                        ; preds = %for.body48, %for.body41
  br i1 %cmp.mn, label %for.body68.preheader, label %for.end88

for.body68.preheader:                             ; preds = %for.end65
  br label %for.body68

for.body68:                                       ; preds = %for.body68.preheader, %for.body68
  %i68 = phi i64 [ 0, %for.body68.preheader ], [ %inc87.i, %for.body68 ]
  %rowA68 = mul nsw i64 %i68, %n64
  %offA68 = add nsw i64 %rowA68, %j64
  %arrayidx72 = getelementptr inbounds double, ptr %A, i64 %offA68
  %vA68 = load double, ptr %arrayidx72, align 8
  %rowQ68 = mul nsw i64 %i68, %n64
  %offQ68 = add nsw i64 %rowQ68, %k64
  %arrayidx76 = getelementptr inbounds double, ptr %Q, i64 %offQ68
  %vQ68 = load double, ptr %arrayidx76, align 8
  %rowR68 = mul nsw i64 %k64, %n64
  %offR68 = add nsw i64 %rowR68, %j64
  %arrayidx80 = getelementptr inbounds double, ptr %R, i64 %offR68
  %vR68 = load double, ptr %arrayidx80, align 8
  %mul81 = fmul double %vQ68, %vR68
  %sub = fsub double %vA68, %mul81
  store double %sub, ptr %arrayidx72, align 8
  %inc87.i = add nsw i64 %i68, 1
  %exit.cond68 = icmp eq i64 %inc87.i, %m64
  br i1 %exit.cond68, label %for.end88, label %for.body68

for.end88:                                        ; preds = %for.body68, %for.end65
  br label %for.inc89

for.inc89:                                        ; preds = %for.end88
  %inc90 = add nsw i32 %j, 1
  %cmp40 = icmp slt i32 %inc90, %n
  br i1 %cmp40, label %for.body41, label %for.end91

for.end91:                                        ; preds = %for.inc89, %for.end37
  br label %for.inc92

for.inc92:                                        ; preds = %for.end91
  %inc93 = add nsw i32 %k, 1
  br label %for.cond

for.end94:                                        ; preds = %for.cond
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
