; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_jacobi_2d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.t = icmp sgt i32 %tsteps, 0
  %run = and i1 %cmp.n, %cmp.t
  br i1 %run, label %preheader, label %for.end93

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %inner.nonempty = icmp sgt i32 %nm1, 1
  br label %for.cond

for.cond:                                         ; preds = %for.inc91, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc92, %for.inc91 ]
  br i1 %inner.nonempty, label %for.body.outer1, label %for.body.outer2

for.body.outer1:
  br label %for.i.1

for.i.1:                                          ; preds = %for.inc41, %for.body.outer1
  %i1 = phi i32 [ 1, %for.body.outer1 ], [ %inc42, %for.inc41 ]
  %i1.64 = sext i32 %i1 to i64
  %i1.row = mul nsw i64 %i1.64, %n64
  %i1p1 = add nsw i32 %i1, 1
  %i1p1.64 = sext i32 %i1p1 to i64
  %i1p1.row = mul nsw i64 %i1p1.64, %n64
  %i1m1 = add nsw i32 %i1, -1
  %i1m1.64 = sext i32 %i1m1 to i64
  %i1m1.row = mul nsw i64 %i1m1.64, %n64
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %i1.row
  %Arow.ip1 = getelementptr inbounds double, ptr %A, i64 %i1p1.row
  %Arow.im1 = getelementptr inbounds double, ptr %A, i64 %i1m1.row
  %Brow.i = getelementptr inbounds double, ptr %B, i64 %i1.row
  br label %for.j.1

for.j.1:                                          ; preds = %for.j.1, %for.i.1
  %j1 = phi i32 [ 1, %for.i.1 ], [ %inc.j1, %for.j.1 ]
  %j1.64 = sext i32 %j1 to i64
  %j1m1.64 = add nsw i64 %j1.64, -1
  %j1p1.64 = add nsw i64 %j1.64, 1

  %a.center = getelementptr inbounds double, ptr %Arow.i, i64 %j1.64
  %v.center = load double, ptr %a.center, align 8
  %a.left = getelementptr inbounds double, ptr %Arow.i, i64 %j1m1.64
  %v.left = load double, ptr %a.left, align 8
  %add18 = fadd double %v.center, %v.left
  %a.right = getelementptr inbounds double, ptr %Arow.i, i64 %j1p1.64
  %v.right = load double, ptr %a.right, align 8
  %add24 = fadd double %add18, %v.right
  %a.down = getelementptr inbounds double, ptr %Arow.ip1, i64 %j1.64
  %v.down = load double, ptr %a.down, align 8
  %add30 = fadd double %add24, %v.down
  %a.up = getelementptr inbounds double, ptr %Arow.im1, i64 %j1.64
  %v.up = load double, ptr %a.up, align 8
  %add36 = fadd double %add30, %v.up
  %mul = fmul double 2.000000e-01, %add36
  %b.dst = getelementptr inbounds double, ptr %Brow.i, i64 %j1.64
  store double %mul, ptr %b.dst, align 8

  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1 = icmp slt i32 %inc.j1, %nm1
  br i1 %cmp.j1, label %for.j.1, label %for.inc41, !llvm.loop !6

for.inc41:                                        ; preds = %for.j.1
  %inc42 = add nsw i32 %i1, 1
  %cmp.i1 = icmp slt i32 %inc42, %nm1
  br i1 %cmp.i1, label %for.i.1, label %for.body.outer2, !llvm.loop !8

for.body.outer2:                                  ; preds = %for.inc41, %for.cond
  br i1 %inner.nonempty, label %for.i.2, label %for.inc91

for.i.2:                                          ; preds = %for.inc88, %for.body.outer2
  %i2 = phi i32 [ 1, %for.body.outer2 ], [ %inc89, %for.inc88 ]
  %i2.64 = sext i32 %i2 to i64
  %i2.row = mul nsw i64 %i2.64, %n64
  %i2p1 = add nsw i32 %i2, 1
  %i2p1.64 = sext i32 %i2p1 to i64
  %i2p1.row = mul nsw i64 %i2p1.64, %n64
  %i2m1 = add nsw i32 %i2, -1
  %i2m1.64 = sext i32 %i2m1 to i64
  %i2m1.row = mul nsw i64 %i2m1.64, %n64
  %Brow.i2 = getelementptr inbounds double, ptr %B, i64 %i2.row
  %Brow.ip1 = getelementptr inbounds double, ptr %B, i64 %i2p1.row
  %Brow.im1 = getelementptr inbounds double, ptr %B, i64 %i2m1.row
  %Arow.i2 = getelementptr inbounds double, ptr %A, i64 %i2.row
  br label %for.j.2

for.j.2:                                          ; preds = %for.j.2, %for.i.2
  %j2 = phi i32 [ 1, %for.i.2 ], [ %inc.j2, %for.j.2 ]
  %j2.64 = sext i32 %j2 to i64
  %j2m1.64 = add nsw i64 %j2.64, -1
  %j2p1.64 = add nsw i64 %j2.64, 1

  %b.center = getelementptr inbounds double, ptr %Brow.i2, i64 %j2.64
  %vb.center = load double, ptr %b.center, align 8
  %b.left = getelementptr inbounds double, ptr %Brow.i2, i64 %j2m1.64
  %vb.left = load double, ptr %b.left, align 8
  %add61 = fadd double %vb.center, %vb.left
  %b.right = getelementptr inbounds double, ptr %Brow.i2, i64 %j2p1.64
  %vb.right = load double, ptr %b.right, align 8
  %add67 = fadd double %add61, %vb.right
  %b.down = getelementptr inbounds double, ptr %Brow.ip1, i64 %j2.64
  %vb.down = load double, ptr %b.down, align 8
  %add73 = fadd double %add67, %vb.down
  %b.up = getelementptr inbounds double, ptr %Brow.im1, i64 %j2.64
  %vb.up = load double, ptr %b.up, align 8
  %add79 = fadd double %add73, %vb.up
  %mul80 = fmul double 2.000000e-01, %add79
  %a.dst = getelementptr inbounds double, ptr %Arow.i2, i64 %j2.64
  store double %mul80, ptr %a.dst, align 8

  %inc.j2 = add nsw i32 %j2, 1
  %cmp.j2 = icmp slt i32 %inc.j2, %nm1
  br i1 %cmp.j2, label %for.j.2, label %for.inc88, !llvm.loop !9

for.inc88:                                        ; preds = %for.j.2
  %inc89 = add nsw i32 %i2, 1
  %cmp.i2 = icmp slt i32 %inc89, %nm1
  br i1 %cmp.i2, label %for.i.2, label %for.inc91, !llvm.loop !10

for.inc91:                                        ; preds = %for.inc88, %for.body.outer2
  %inc92 = add nsw i32 %t, 1
  %cmp.t.loop = icmp slt i32 %inc92, %tsteps
  br i1 %cmp.t.loop, label %for.cond, label %for.end93, !llvm.loop !11

for.end93:                                        ; preds = %for.inc91, %entry
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
!11 = distinct !{!11, !7}
