; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp_mn = icmp sgt i32 %n, 0
  br i1 %cmp_mn, label %preheader, label %for.end94

preheader:
  %m64 = sext i32 %m to i64
  %n64 = sext i32 %n to i64
  %m.pos = icmp sgt i32 %m, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %preheader
  %k = phi i32 [ 0, %preheader ], [ %inc93, %for.inc92 ]
  %k64 = sext i32 %k to i64
  br i1 %m.pos, label %for.body6.preheader, label %for.end

for.body6.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8, %for.body6.preheader
  %i6 = phi i64 [ 0, %for.body6.preheader ], [ %i6.next, %for.body8 ]
  %nrm6 = phi double [ 0.000000e+00, %for.body6.preheader ], [ %add15, %for.body8 ]
  %rowoff6 = mul nsw i64 %i6, %n64
  %off6 = add nsw i64 %rowoff6, %k64
  %ptr6 = getelementptr inbounds double, ptr %A, i64 %off6
  %val6 = load double, ptr %ptr6, align 8
  %mul = fmul double %val6, %val6
  %add15 = fadd double %nrm6, %mul
  %i6.next = add nsw i64 %i6, 1
  %exit6 = icmp eq i64 %i6.next, %m64
  br i1 %exit6, label %for.end, label %for.body8

for.end:                                          ; preds = %for.body8, %for.cond
  %nrm.final = phi double [ 0.000000e+00, %for.cond ], [ %add15, %for.body8 ]
  %call = call double @sqrt(double noundef %nrm.final) #2
  %Rkk.off = mul nsw i64 %k64, %n64
  %Rkk.off2 = add nsw i64 %Rkk.off, %k64
  %Rkk.ptr = getelementptr inbounds double, ptr %R, i64 %Rkk.off2
  store double %call, ptr %Rkk.ptr, align 8
  br i1 %m.pos, label %for.body22.preheader, label %for.end37

for.body22.preheader:
  br label %for.body22

for.body22:                                       ; preds = %for.body22, %for.body22.preheader
  %i22 = phi i64 [ 0, %for.body22.preheader ], [ %i22.next, %for.body22 ]
  %rowoffA = mul nsw i64 %i22, %n64
  %offA = add nsw i64 %rowoffA, %k64
  %ptrA = getelementptr inbounds double, ptr %A, i64 %offA
  %valA = load double, ptr %ptrA, align 8
  %div = fdiv double %valA, %call
  %rowoffQ = mul nsw i64 %i22, %n64
  %offQ = add nsw i64 %rowoffQ, %k64
  %ptrQ = getelementptr inbounds double, ptr %Q, i64 %offQ
  store double %div, ptr %ptrQ, align 8
  %i22.next = add nsw i64 %i22, 1
  %exit22 = icmp eq i64 %i22.next, %m64
  br i1 %exit22, label %for.end37, label %for.body22

for.end37:                                        ; preds = %for.body22, %for.end
  %k.inc = add nsw i32 %k, 1
  %cmp40.check = icmp slt i32 %k.inc, %n
  br i1 %cmp40.check, label %for.body41.preheader, label %for.end91

for.body41.preheader:
  %k1.64 = sext i32 %k.inc to i64
  br label %for.body41

for.body41:                                       ; preds = %for.inc89, %for.body41.preheader
  %j32 = phi i32 [ %k.inc, %for.body41.preheader ], [ %inc90, %for.inc89 ]
  %j64 = sext i32 %j32 to i64
  %Rkj.off = mul nsw i64 %k64, %n64
  %Rkj.off2 = add nsw i64 %Rkj.off, %j64
  %Rkj.ptr = getelementptr inbounds double, ptr %R, i64 %Rkj.off2
  store double 0.000000e+00, ptr %Rkj.ptr, align 8
  br i1 %m.pos, label %for.body48.preheader, label %for.end65

for.body48.preheader:
  br label %for.body48

for.body48:                                       ; preds = %for.body48, %for.body48.preheader
  %i48 = phi i64 [ 0, %for.body48.preheader ], [ %i48.next, %for.body48 ]
  %rowoffQ48 = mul nsw i64 %i48, %n64
  %offQ48 = add nsw i64 %rowoffQ48, %k64
  %ptrQ48 = getelementptr inbounds double, ptr %Q, i64 %offQ48
  %valQ48 = load double, ptr %ptrQ48, align 8
  %rowoffA48 = mul nsw i64 %i48, %n64
  %offA48 = add nsw i64 %rowoffA48, %j64
  %ptrA48 = getelementptr inbounds double, ptr %A, i64 %offA48
  %valA48 = load double, ptr %ptrA48, align 8
  %mul57 = fmul double %valQ48, %valA48
  %cur = load double, ptr %Rkj.ptr, align 8
  %add62 = fadd double %cur, %mul57
  store double %add62, ptr %Rkj.ptr, align 8
  %i48.next = add nsw i64 %i48, 1
  %exit48 = icmp eq i64 %i48.next, %m64
  br i1 %exit48, label %for.end65, label %for.body48

for.end65:                                        ; preds = %for.body48, %for.body41
  br i1 %m.pos, label %for.body68.preheader, label %for.end88

for.body68.preheader:
  %Rkj.val = load double, ptr %Rkj.ptr, align 8
  br label %for.body68

for.body68:                                       ; preds = %for.body68, %for.body68.preheader
  %i68 = phi i64 [ 0, %for.body68.preheader ], [ %i68.next, %for.body68 ]
  %rowoffA68 = mul nsw i64 %i68, %n64
  %offA68 = add nsw i64 %rowoffA68, %j64
  %ptrA68 = getelementptr inbounds double, ptr %A, i64 %offA68
  %valA68 = load double, ptr %ptrA68, align 8
  %rowoffQ68 = mul nsw i64 %i68, %n64
  %offQ68 = add nsw i64 %rowoffQ68, %k64
  %ptrQ68 = getelementptr inbounds double, ptr %Q, i64 %offQ68
  %valQ68 = load double, ptr %ptrQ68, align 8
  %mul81 = fmul double %valQ68, %Rkj.val
  %sub = fsub double %valA68, %mul81
  store double %sub, ptr %ptrA68, align 8
  %i68.next = add nsw i64 %i68, 1
  %exit68 = icmp eq i64 %i68.next, %m64
  br i1 %exit68, label %for.end88, label %for.body68

for.end88:                                        ; preds = %for.body68, %for.end65
  br label %for.inc89

for.inc89:                                        ; preds = %for.end88
  %inc90 = add nsw i32 %j32, 1
  %cmp40 = icmp slt i32 %inc90, %n
  br i1 %cmp40, label %for.body41, label %for.end91

for.end91:                                        ; preds = %for.inc89, %for.end37
  br label %for.inc92

for.inc92:                                        ; preds = %for.end91
  %inc93 = add nsw i32 %k, 1
  %cmp = icmp slt i32 %inc93, %n
  br i1 %cmp, label %for.cond, label %for.end94

for.end94:                                        ; preds = %for.inc92, %entry
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
