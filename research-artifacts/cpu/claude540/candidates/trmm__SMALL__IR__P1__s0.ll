; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_trmm(i32 noundef %m, i32 noundef %n, double noundef %alpha, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.m = icmp sgt i32 %m, 0
  br i1 %cmp.m, label %preheader.i, label %for.end36

preheader.i:
  %cmp.n = icmp sgt i32 %n, 0
  %m64 = zext i32 %m to i64
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc34, %preheader.i
  %i = phi i32 [ 0, %preheader.i ], [ %inc35, %for.inc34 ]

  br i1 %cmp.n, label %for.body, label %for.inc34

for.body:                                         ; preds = %for.cond
  %i64 = zext i32 %i to i64
  %krow.start = add nsw i32 %i, 1
  %kcmp = icmp slt i32 %krow.start, %m
  %krow.start64 = sext i32 %krow.start to i64
  %Bi.row = getelementptr inbounds double, ptr %B, i64 %i64
  %Bi.row.off = mul i64 %i64, %n64
  %Bi.ptr.base = getelementptr inbounds double, ptr %B, i64 %Bi.row.off
  br label %for.cond4

for.cond4:                                        ; preds = %for.inc31, %for.body
  %j = phi i32 [ 0, %for.body ], [ %inc32, %for.inc31 ]
  %j64 = zext i32 %j to i64

  %Bij.ptr = getelementptr inbounds double, ptr %Bi.ptr.base, i64 %j64

  br i1 %kcmp, label %for.cond8.preheader, label %for.end

for.cond8.preheader:
  br label %for.cond8

for.cond8:                                        ; preds = %for.inc, %for.cond8.preheader
  %k = phi i32 [ %krow.start, %for.cond8.preheader ], [ %inc, %for.inc ]
  %sum = phi double [ 0.0, %for.cond8.preheader ], [ %add21, %for.inc ]
  %k64 = zext i32 %k to i64

  %Ak.off = mul nsw i64 %k64, %m64
  %Aki.ptr = getelementptr inbounds double, ptr %A, i64 %Ak.off
  %Aki.ptr2 = getelementptr inbounds double, ptr %Aki.ptr, i64 %i64
  %Aval = load double, ptr %Aki.ptr2, align 8

  %Bk.off = mul nsw i64 %k64, %n64
  %Bkj.ptr = getelementptr inbounds double, ptr %B, i64 %Bk.off
  %Bkj.ptr2 = getelementptr inbounds double, ptr %Bkj.ptr, i64 %j64
  %Bval = load double, ptr %Bkj.ptr2, align 8

  %mul = fmul double %Aval, %Bval
  %add21 = fadd double %sum, %mul

  %inc = add nsw i32 %k, 1
  %cmp9 = icmp slt i32 %inc, %m
  br i1 %cmp9, label %for.cond8, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.cond4
  %sum.final = phi double [ 0.0, %for.cond4 ], [ %add21, %for.end.loopexit ]

  %Bval.orig = load double, ptr %Bij.ptr, align 8
  %add.acc = fadd double %Bval.orig, %sum.final
  %mul26 = fmul double %alpha, %add.acc
  store double %mul26, ptr %Bij.ptr, align 8

  br label %for.inc31

for.inc31:                                        ; preds = %for.end
  %inc32 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc32, %n
  br i1 %cmp5, label %for.cond4, label %for.inc34, !llvm.loop !8

for.inc34:                                        ; preds = %for.inc31, %for.cond
  %inc35 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc35, %m
  br i1 %cmp, label %for.cond, label %for.end36, !llvm.loop !9

for.end36:                                        ; preds = %for.inc34, %entry
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
