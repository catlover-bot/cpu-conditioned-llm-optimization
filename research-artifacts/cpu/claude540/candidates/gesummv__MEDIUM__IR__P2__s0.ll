; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gesummv(i32 noundef %n, double noundef %alpha, double noundef %beta, ptr noundef %A, ptr noundef %B, ptr noundef %tmp, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end46

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.body

for.body:
  %i = phi i64 [ 0, %outer.preheader ], [ %inc45, %for.inc44 ]
  %Arow = getelementptr inbounds double, ptr %A, i64 %i
  %arow.mul = mul nsw i64 %i, %n64
  %Arow2 = getelementptr inbounds double, ptr %A, i64 %arow.mul
  %Brow.mul = mul nsw i64 %i, %n64
  %Brow2 = getelementptr inbounds double, ptr %B, i64 %Brow.mul
  %tmp.i.ptr = getelementptr inbounds double, ptr %tmp, i64 %i
  %y.i.ptr = getelementptr inbounds double, ptr %y, i64 %i

  br label %for.cond9

for.cond9:
  %j = phi i64 [ 0, %for.body ], [ %inc, %for.body11 ]
  %tmp.acc = phi double [ 0.000000e+00, %for.body ], [ %add20, %for.body11 ]
  %y.acc = phi double [ 0.000000e+00, %for.body ], [ %add32, %for.body11 ]
  %cmp10 = icmp slt i64 %j, %n64
  br i1 %cmp10, label %for.body11, label %for.end

for.body11:
  %Aelt.ptr = getelementptr inbounds double, ptr %Arow2, i64 %j
  %Aval = load double, ptr %Aelt.ptr, align 8
  %xelt.ptr = getelementptr inbounds double, ptr %x, i64 %j
  %xval = load double, ptr %xelt.ptr, align 8
  %mul = fmul double %Aval, %xval
  %add20 = fadd double %mul, %tmp.acc

  %Belt.ptr = getelementptr inbounds double, ptr %Brow2, i64 %j
  %Bval = load double, ptr %Belt.ptr, align 8
  %mul29 = fmul double %Bval, %xval
  %add32 = fadd double %mul29, %y.acc

  %inc = add nsw i64 %j, 1
  br label %for.cond9, !llvm.loop !6

for.end:
  store double %tmp.acc, ptr %tmp.i.ptr, align 8
  store double %y.acc, ptr %y.i.ptr, align 8

  %mul37 = fmul double %alpha, %tmp.acc
  %mul40 = fmul double %beta, %y.acc
  %add41 = fadd double %mul37, %mul40
  store double %add41, ptr %y.i.ptr, align 8
  br label %for.inc44

for.inc44:
  %inc45 = add nsw i64 %i, 1
  %cmp.outer = icmp slt i64 %inc45, %n64
  br i1 %cmp.outer, label %for.body, label %for.end46.exit

for.end46.exit:
  br label %for.end46

for.end46:
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
