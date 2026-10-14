; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.mn = icmp sgt i32 %n, 0
  br i1 %cmp.mn, label %preheader, label %for.end94

preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp.m0 = icmp sgt i32 %m, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %preheader
  %k = phi i32 [ 0, %preheader ], [ %inc93, %for.inc92 ]
  %k64 = sext i32 %k to i64
  br i1 %cmp.m0, label %for.body6.preheader, label %for.end.noloop

for.body6.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body6.preheader, %for.body8
  %i.06 = phi i32 [ 0, %for.body6.preheader ], [ %inc, %for.body8 ]
  %nrm.06 = phi double [ 0.000000e+00, %for.body6.preheader ], [ %add15, %for.body8 ]
  %i64.6 = sext i32 %i.06 to i64
  %rowoff.6 = mul nsw i64 %i64.6, %n64
  %arrayidx.6 = getelementptr inbounds double, ptr %A, i64 %rowoff.6
  %arrayidx10.6 = getelementptr inbounds double, ptr %arrayidx.6, i64 %k64
  %val.6 = load double, ptr %arrayidx10.6, align 8
  %mul.6 = fmul double %val.6, %val.6
  %add15.6 = fadd double %nrm.06, %mul.6
  %inc.6 = add nsw i32 %i.06, 1
  %cmp7.6 = icmp slt i32 %inc.6, %m
  br i1 %cmp7.6, label %for.body8, label %for.end.loopexit

  ; placeholder to keep naming consistent (unused)
for.body8.unused:
  br label %for.body8

for.end.loopexit:
  %nrm.final = phi double [ %add15.6, %for.body8 ]
  br label %for.end

for.end.noloop:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.end.noloop
  %nrm.merged = phi double [ %nrm.final, %for.end.loopexit ], [ 0.000000e+00, %for.end.noloop ]
  %call = call double @sqrt(double noundef %nrm.merged) #2
  %Rk.row = mul nsw i64 %k64, %n64
  %Rkk.ptr0 = getelementptr inbounds double, ptr %R, i64 %Rk.row
  %Rkk.ptr = getelementptr inbounds double, ptr %Rkk.ptr0, i64 %k64
  store double %call, ptr %Rkk.ptr, align 8

  br i1 %cmp.m0, label %for.body22, label %for.end37

for.body22:                                       ; preds = %for.end, %for.body22
  %i22 = phi i32 [ 0, %for.end ], [ %inc36, %for.body22 ]
  %i22.64 = sext i32 %i22 to i64
  %A22.row = mul nsw i64 %i22.64, %n64
  %A22.base = getelementptr inbounds double, ptr %A, i64 %A22.row
  %A22.elem = getelementptr inbounds double, ptr %A22.base, i64 %k64
  %A22.val = load double, ptr %A22.elem, align 8
  %div = fdiv double %A22.val, %call
  %Q22.row = mul nsw i64 %i22.64, %n64
  %Q22.base = getelementptr inbounds double, ptr %Q, i64 %Q22.row
  %Q22.elem = getelementptr inbounds double, ptr %Q22.base, i64 %k64
  store double %div, ptr %Q22.elem, align 8
  %inc36 = add nsw i32 %i22, 1
  %cmp21 = icmp slt i32 %inc36, %m
  br i1 %cmp21, label %for.body22, label %for.end37

for.end37:                                        ; preds = %for.body22, %for.end
  %kp1 = add nsw i32 %k, 1
  %cmp.j0 = icmp slt i32 %kp1, %n
  br i1 %cmp.j0, label %for.body41.preheader, label %for.end91

for.body41.preheader:
  br label %for.body41

for.body41:                                       ; preds = %for.body41.preheader, %for.end88
  %j = phi i32 [ %kp1, %for.body41.preheader ], [ %inc90, %for.end88 ]
  %j64 = sext i32 %j to i64
  %Rkj.elem = getelementptr inbounds double, ptr %Rkk.ptr0, i64 %j64
  store double 0.000000e+00, ptr %Rkj.elem, align 8

  br i1 %cmp.m0, label %for.body48.preheader, label %for.end65

for.body48.preheader:
  br label %for.body48

for.body48:                                       ; preds = %for.body48.preheader, %for.body48
  %i48 = phi i32 [ 0, %for.body48.preheader ], [ %inc64, %for.body48 ]
  %i48.64 = sext i32 %i48 to i64
  %Q48.row = mul nsw i64 %i48.64, %n64
  %Q48.base = getelementptr inbounds double, ptr %Q, i64 %Q48.row
  %Q48.elem = getelementptr inbounds double, ptr %Q48.base, i64 %k64
  %Q48.val = load double, ptr %Q48.elem, align 8
  %A48.row = mul nsw i64 %i48.64, %n64
  %A48.base = getelementptr inbounds double, ptr %A, i64 %A48.row
  %A48.elem = getelementptr inbounds double, ptr %A48.base, i64 %j64
  %A48.val = load double, ptr %A48.elem, align 8
  %mul57 = fmul double %Q48.val, %A48.val
  %Rkj.cur = load double, ptr %Rkj.elem, align 8
  %add62 = fadd double %Rkj.cur, %mul57
  store double %add62, ptr %Rkj.elem, align 8
  %inc64 = add nsw i32 %i48, 1
  %cmp47 = icmp slt i32 %inc64, %m
  br i1 %cmp47, label %for.body48, label %for.end65

for.end65:                                        ; preds = %for.body48, %for.body41
  br i1 %cmp.m0, label %for.body68.preheader, label %for.end88

for.body68.preheader:
  %Rkj.val = load double, ptr %Rkj.elem, align 8
  br label %for.body68

for.body68:                                       ; preds = %for.body68.preheader, %for.body68
  %i68 = phi i32 [ 0, %for.body68.preheader ], [ %inc87, %for.body68 ]
  %i68.64 = sext i32 %i68 to i64
  %A68.row = mul nsw i64 %i68.64, %n64
  %A68.base = getelementptr inbounds double, ptr %A, i64 %A68.row
  %A68.elem = getelementptr inbounds double, ptr %A68.base, i64 %j64
  %A68.val = load double, ptr %A68.elem, align 8
  %Q68.row = mul nsw i64 %i68.64, %n64
  %Q68.base = getelementptr inbounds double, ptr %Q, i64 %Q68.row
  %Q68.elem = getelementptr inbounds double, ptr %Q68.base, i64 %k64
  %Q68.val = load double, ptr %Q68.elem, align 8
  %mul81 = fmul double %Q68.val, %Rkj.val
  %sub = fsub double %A68.val, %mul81
  store double %sub, ptr %A68.elem, align 8
  %inc87 = add nsw i32 %i68, 1
  %cmp67 = icmp slt i32 %inc87, %m
  br i1 %cmp67, label %for.body68, label %for.end88

for.end88:                                        ; preds = %for.body68, %for.end65
  %inc90 = add nsw i32 %j, 1
  %cmp40 = icmp slt i32 %inc90, %n
  br i1 %cmp40, label %for.body41, label %for.end91

for.end91:                                        ; preds = %for.end88, %for.end37
  %inc93 = add nsw i32 %k, 1
  %cmp = icmp slt i32 %inc93, %n
  br i1 %cmp, label %for.cond, label %for.end94

for.inc92:
  br label %for.cond

for.end94:                                        ; preds = %for.end91, %entry
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
