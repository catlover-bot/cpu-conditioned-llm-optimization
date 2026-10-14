; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_symm(i32 noundef %m, i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %outer.preheader, label %for.end61

outer.preheader:
  %cmp.n.pre = icmp sgt i32 %n, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc59, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc60, %for.inc59 ]
  br i1 %cmp.n.pre, label %for.body, label %for.end61.loopexit

for.body:                                         ; preds = %for.cond
  %i64 = sext i32 %i to i64
  %Bi.row = getelementptr inbounds double, ptr %B, i64 %i64
  %Bi.rowoff = mul nsw i64 %i64, %n64
  %Bi.base = getelementptr inbounds double, ptr %B, i64 %Bi.rowoff
  %Ai.rowoff = mul nsw i64 %i64, %m64
  %Ai.base = getelementptr inbounds double, ptr %A, i64 %Ai.rowoff
  %Aii.ptr = getelementptr inbounds double, ptr %Ai.base, i64 %i64
  %Aii.val = load double, ptr %Aii.ptr, align 8
  br label %for.body8

for.body8:                                        ; preds = %for.end, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc57, %for.end ]
  %cmp.k = icmp sgt i32 %i, 0
  br i1 %cmp.k, label %for.body11.preheader, label %for.end

for.body11.preheader:
  %j64 = sext i32 %j to i64
  %Bij.ptr = getelementptr inbounds double, ptr %Bi.base, i64 %j64
  %Bij.val = load double, ptr %Bij.ptr, align 8
  br label %for.body11

for.body11:                                       ; preds = %for.body11.preheader, %for.body11
  %k = phi i32 [ 0, %for.body11.preheader ], [ %inc, %for.body11 ]
  %temp2.acc = phi double [ 0.000000e+00, %for.body11.preheader ], [ %add33, %for.body11 ]
  %k64 = sext i32 %k to i64
  %mul = fmul double %alpha, %Bij.val
  %Aik.ptr = getelementptr inbounds double, ptr %Ai.base, i64 %k64
  %Aik.val = load double, ptr %Aik.ptr, align 8
  %mul18 = fmul double %mul, %Aik.val
  %Ckrowoff = mul nsw i64 %k64, %n64
  %Ck.base = getelementptr inbounds double, ptr %C, i64 %Ckrowoff
  %Ckj.ptr = getelementptr inbounds double, ptr %Ck.base, i64 %j64
  %Ckj.val = load double, ptr %Ckj.ptr, align 8
  %add23 = fadd double %Ckj.val, %mul18
  store double %add23, ptr %Ckj.ptr, align 8
  %Bkrowoff = mul nsw i64 %k64, %n64
  %Bk.base = getelementptr inbounds double, ptr %B, i64 %Bkrowoff
  %Bkj.ptr = getelementptr inbounds double, ptr %Bk.base, i64 %j64
  %Bkj.val = load double, ptr %Bkj.ptr, align 8
  %mul32 = fmul double %Bkj.val, %Aik.val
  %add33 = fadd double %temp2.acc, %mul32
  %inc = add nsw i32 %k, 1
  %cmp10 = icmp slt i32 %inc, %i
  br i1 %cmp10, label %for.body11, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body11
  %add33.lcssa = phi double [ %add33, %for.body11 ]
  %Bij.val.lcssa = phi double [ %Bij.val, %for.body11 ]
  %j64.lcssa = phi i64 [ %j64, %for.body11 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body8
  %temp2.final = phi double [ 0.000000e+00, %for.body8 ], [ %add33.lcssa, %for.end.loopexit ]
  %Bij.final = phi double [ 0.000000e+00, %for.body8 ], [ %Bij.val.lcssa, %for.end.loopexit ]
  %jidx = phi i64 [ 0, %for.body8 ], [ 0, %for.end.loopexit ]
  %j64b = sext i32 %j to i64
  %Bij.ptr2 = getelementptr inbounds double, ptr %Bi.base, i64 %j64b
  %Bij.load = load double, ptr %Bij.ptr2, align 8
  %Cirowoff = mul nsw i64 %i64, %n64
  %Ci.base = getelementptr inbounds double, ptr %C, i64 %Cirowoff
  %Cij.ptr = getelementptr inbounds double, ptr %Ci.base, i64 %j64b
  %Cij.val = load double, ptr %Cij.ptr, align 8
  %mul38 = fmul double %beta, %Cij.val
  %mul43 = fmul double %alpha, %Bij.load
  %mul48 = fmul double %mul43, %Aii.val
  %add49 = fadd double %mul38, %mul48
  %mul50 = fmul double %alpha, %temp2.final
  %add51 = fadd double %add49, %mul50
  store double %add51, ptr %Cij.ptr, align 8
  %inc57 = add nsw i32 %j, 1
  %cmp7 = icmp slt i32 %inc57, %n
  br i1 %cmp7, label %for.body8, label %for.end61.loopexit2

for.end61.loopexit2:                              ; preds = %for.end
  br label %for.inc59

for.inc59:                                        ; preds = %for.end61.loopexit2
  %inc60 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc60, %m
  br i1 %cmp, label %for.cond, label %for.end61.loopexit

for.end61.loopexit:                               ; preds = %for.inc59, %for.cond
  br label %for.end61

for.end61:                                        ; preds = %for.end61.loopexit, %entry
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
