; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n0 = icmp sgt i32 %n, 0
  br i1 %cmp.n0, label %outer.preheader, label %phase2.check

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc62, %outer.preheader
  %i.0 = phi i32 [ 0, %outer.preheader ], [ %inc63, %for.inc62 ]
  %i.64 = sext i32 %i.0 to i64
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %i.64
  %Arow.i.off = mul nsw i64 %i.64, %n64
  %Arow.i.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i.off
  br label %for.cond5

for.cond5:                                        ; preds = %for.inc29, %for.cond
  %j.0 = phi i32 [ 0, %for.cond ], [ %inc30, %for.inc29 ]
  %cmp6 = icmp slt i32 %j.0, %i.0
  br i1 %cmp6, label %for.body7, label %for.end31

for.body7:                                        ; preds = %for.cond5
  %j.64 = sext i32 %j.0 to i64
  %arrayidx9 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j.64
  %w0 = load double, ptr %arrayidx9, align 8
  %Arow.j.off = mul nsw i64 %j.64, %n64
  %Arow.j.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.j.off
  br label %for.cond10

for.cond10:                                       ; preds = %for.body12, %for.body7
  %k.0 = phi i32 [ 0, %for.body7 ], [ %inc, %for.body12 ]
  %w.1 = phi double [ %w0, %for.body7 ], [ %sub, %for.body12 ]
  %cmp11 = icmp slt i32 %k.0, %j.0
  br i1 %cmp11, label %for.body12, label %for.end

for.body12:                                       ; preds = %for.cond10
  %k.64 = sext i32 %k.0 to i64
  %arrayidx16 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k.64
  %v16 = load double, ptr %arrayidx16, align 8
  %arrayidx20 = getelementptr inbounds double, ptr %Arow.j.ptr, i64 %k.64
  %v20 = load double, ptr %arrayidx20, align 8
  %mul = fmul double %v16, %v20
  %sub = fsub double %w.1, %mul
  %inc = add nsw i32 %k.0, 1
  br label %for.cond10, !llvm.loop !6

for.end:                                          ; preds = %for.cond10
  %arrayidx24 = getelementptr inbounds double, ptr %Arow.j.ptr, i64 %j.64
  %v24 = load double, ptr %arrayidx24, align 8
  %div = fdiv double %w.1, %v24
  store double %div, ptr %arrayidx9, align 8
  %inc30 = add nsw i32 %j.0, 1
  br label %for.cond5, !llvm.loop !8

for.end31:                                        ; preds = %for.cond5
  br label %for.cond32

for.cond32:                                       ; preds = %for.inc59, %for.end31
  %j2.0 = phi i32 [ %i.0, %for.end31 ], [ %inc60, %for.inc59 ]
  %cmp33 = icmp slt i32 %j2.0, %n
  br i1 %cmp33, label %for.body34, label %for.end61

for.body34:                                       ; preds = %for.cond32
  %j2.64 = sext i32 %j2.0 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j2.64
  %w1 = load double, ptr %arrayidx38, align 8
  br label %for.cond39

for.cond39:                                       ; preds = %for.body41, %for.body34
  %k2.0 = phi i32 [ 0, %for.body34 ], [ %inc53, %for.body41 ]
  %w2.1 = phi double [ %w1, %for.body34 ], [ %sub51, %for.body41 ]
  %cmp40 = icmp slt i32 %k2.0, %i.0
  br i1 %cmp40, label %for.body41, label %for.end54

for.body41:                                       ; preds = %for.cond39
  %k2.64 = sext i32 %k2.0 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k2.64
  %v45 = load double, ptr %arrayidx45, align 8
  %Arow.k2.off = mul nsw i64 %k2.64, %n64
  %Arow.k2.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.k2.off
  %arrayidx49 = getelementptr inbounds double, ptr %Arow.k2.ptr, i64 %j2.64
  %v49 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %v45, %v49
  %sub51 = fsub double %w2.1, %mul50
  %inc53 = add nsw i32 %k2.0, 1
  br label %for.cond39, !llvm.loop !9

for.end54:                                        ; preds = %for.cond39
  store double %w2.1, ptr %arrayidx38, align 8
  %inc60 = add nsw i32 %j2.0, 1
  br label %for.cond32, !llvm.loop !10

for.end61:                                        ; preds = %for.cond32
  br label %for.inc62

for.inc62:                                        ; preds = %for.end61
  %inc63 = add nsw i32 %i.0, 1
  %cmp.outer = icmp slt i32 %inc63, %n
  br i1 %cmp.outer, label %for.cond, label %phase2.check

phase2.check:                                     ; preds = %for.inc62, %entry
  %cmp.n1 = icmp sgt i32 %n, 0
  br i1 %cmp.n1, label %phase2.preheader, label %phase3.check

phase2.preheader:
  %n64.2 = sext i32 %n to i64
  br label %for.cond65

for.cond65:                                       ; preds = %for.inc86, %phase2.preheader
  %i2.0 = phi i32 [ 0, %phase2.preheader ], [ %inc87, %for.inc86 ]
  %i2.64 = sext i32 %i2.0 to i64
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i2.64
  %bw0 = load double, ptr %arrayidx69, align 8
  %Arow.i2.off = mul nsw i64 %i2.64, %n64.2
  %Arow.i2.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i2.off
  br label %for.cond70

for.cond70:                                       ; preds = %for.body72, %for.cond65
  %j3.0 = phi i32 [ 0, %for.cond65 ], [ %inc82, %for.body72 ]
  %bw.1 = phi double [ %bw0, %for.cond65 ], [ %sub80, %for.body72 ]
  %cmp71 = icmp slt i32 %j3.0, %i2.0
  br i1 %cmp71, label %for.body72, label %for.end83

for.body72:                                       ; preds = %for.cond70
  %j3.64 = sext i32 %j3.0 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %Arow.i2.ptr, i64 %j3.64
  %v76 = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3.64
  %v78 = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %v76, %v78
  %sub80 = fsub double %bw.1, %mul79
  %inc82 = add nsw i32 %j3.0, 1
  br label %for.cond70, !llvm.loop !12

for.end83:                                        ; preds = %for.cond70
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i2.64
  store double %bw.1, ptr %arrayidx85, align 8
  %inc87 = add nsw i32 %i2.0, 1
  %cmp.p2 = icmp slt i32 %inc87, %n
  br i1 %cmp.p2, label %for.cond65, label %phase3.check, !llvm.loop !13

phase3.check:                                     ; preds = %for.end83, %phase2.check
  %n.sub1 = sub nsw i32 %n, 1
  %cmp.n2 = icmp sge i32 %n.sub1, 0
  br i1 %cmp.n2, label %phase3.preheader, label %for.end118

phase3.preheader:
  %n64.3 = sext i32 %n to i64
  br label %for.cond90

for.cond90:                                       ; preds = %for.end109, %phase3.preheader
  %i3.0 = phi i32 [ %n.sub1, %phase3.preheader ], [ %dec, %for.end109 ]
  %i3.64 = sext i32 %i3.0 to i64
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i3.64
  %yw0 = load double, ptr %arrayidx94, align 8
  %j4.init = add nsw i32 %i3.0, 1
  %Arow.i3.off = mul nsw i64 %i3.64, %n64.3
  %Arow.i3.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i3.off
  br label %for.cond96

for.cond96:                                       ; preds = %for.body98, %for.cond90
  %j4.0 = phi i32 [ %j4.init, %for.cond90 ], [ %inc108, %for.body98 ]
  %yw.1 = phi double [ %yw0, %for.cond90 ], [ %sub106, %for.body98 ]
  %cmp97 = icmp slt i32 %j4.0, %n
  br i1 %cmp97, label %for.body98, label %for.end109

for.body98:                                       ; preds = %for.cond96
  %j4.64 = sext i32 %j4.0 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %Arow.i3.ptr, i64 %j4.64
  %v102 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j4.64
  %v104 = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %v102, %v104
  %sub106 = fsub double %yw.1, %mul105
  %inc108 = add nsw i32 %j4.0, 1
  br label %for.cond96, !llvm.loop !14

for.end109:                                       ; preds = %for.cond96
  %arrayidx113 = getelementptr inbounds double, ptr %Arow.i3.ptr, i64 %i3.64
  %v113 = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %yw.1, %v113
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i3.64
  store double %div114, ptr %arrayidx116, align 8
  %dec = add nsw i32 %i3.0, -1
  %cmp.p3 = icmp sge i32 %dec, 0
  br i1 %cmp.p3, label %for.cond90, label %for.end118, !llvm.loop !15

for.end118:                                       ; preds = %for.end109, %phase3.check
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
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
!14 = distinct !{!14, !7}
!15 = distinct !{!15, !7}
