; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n.pos = icmp sgt i32 %n, 0
  br i1 %cmp.n.pos, label %outer.preheader, label %phase2.check

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc62, %outer.preheader
  %i.0 = phi i32 [ 0, %outer.preheader ], [ %inc63, %for.inc62 ]
  %i.0.64 = sext i32 %i.0 to i64
  %Arow_i = getelementptr inbounds double, ptr %A, i64 %i.0.64
  %Arow_i.off = mul nsw i64 %i.0.64, %n64
  %Arow_i.ptr = getelementptr inbounds double, ptr %A, i64 %Arow_i.off
  %cmp = icmp slt i32 %i.0, %n
  br i1 %cmp, label %for.body, label %for.end64

for.body:                                         ; preds = %for.cond
  br label %for.cond5

for.cond5:                                        ; preds = %for.inc29, %for.body
  %j.0 = phi i32 [ 0, %for.body ], [ %inc30, %for.inc29 ]
  %cmp6 = icmp slt i32 %j.0, %i.0
  br i1 %cmp6, label %for.body7, label %for.end31

for.body7:                                        ; preds = %for.cond5
  %j.0.64 = sext i32 %j.0 to i64
  %arrayidx9 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %j.0.64
  %w0 = load double, ptr %arrayidx9, align 8
  br label %for.cond10

for.cond10:                                       ; preds = %for.body12, %for.body7
  %k.0 = phi i32 [ 0, %for.body7 ], [ %inc, %for.body12 ]
  %w.0 = phi double [ %w0, %for.body7 ], [ %sub, %for.body12 ]
  %cmp11 = icmp slt i32 %k.0, %j.0
  br i1 %cmp11, label %for.body12, label %for.end

for.body12:                                       ; preds = %for.cond10
  %k.0.64 = sext i32 %k.0 to i64
  %arrayidx16 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %k.0.64
  %aik = load double, ptr %arrayidx16, align 8
  %Arow_k.off = mul nsw i64 %k.0.64, %n64
  %Arow_k.ptr = getelementptr inbounds double, ptr %A, i64 %Arow_k.off
  %arrayidx20 = getelementptr inbounds double, ptr %Arow_k.ptr, i64 %j.0.64
  %akj = load double, ptr %arrayidx20, align 8
  %mul = fmul double %aik, %akj
  %sub = fsub double %w.0, %mul
  %inc = add nsw i32 %k.0, 1
  br label %for.cond10, !llvm.loop !6

for.end:                                          ; preds = %for.cond10
  %arrayidx24 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %j.0.64
  %ajj_off = mul nsw i64 %j.0.64, %n64
  %Arow_j.ptr = getelementptr inbounds double, ptr %A, i64 %ajj_off
  %arrayidx24.j = getelementptr inbounds double, ptr %Arow_j.ptr, i64 %j.0.64
  %ajj = load double, ptr %arrayidx24.j, align 8
  %div = fdiv double %w.0, %ajj
  store double %div, ptr %arrayidx24, align 8
  br label %for.inc29

for.inc29:                                        ; preds = %for.end
  %inc30 = add nsw i32 %j.0, 1
  br label %for.cond5, !llvm.loop !8

for.end31:                                        ; preds = %for.cond5
  br label %for.cond32

for.cond32:                                       ; preds = %for.inc59, %for.end31
  %j2.0 = phi i32 [ %i.0, %for.end31 ], [ %inc60, %for.inc59 ]
  %cmp33 = icmp slt i32 %j2.0, %n
  br i1 %cmp33, label %for.body34, label %for.end61

for.body34:                                       ; preds = %for.cond32
  %j2.0.64 = sext i32 %j2.0 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %j2.0.64
  %w1 = load double, ptr %arrayidx38, align 8
  br label %for.cond39

for.cond39:                                       ; preds = %for.body41, %for.body34
  %k2.0 = phi i32 [ 0, %for.body34 ], [ %inc53, %for.body41 ]
  %w2.0 = phi double [ %w1, %for.body34 ], [ %sub51, %for.body41 ]
  %cmp40 = icmp slt i32 %k2.0, %i.0
  br i1 %cmp40, label %for.body41, label %for.end54

for.body41:                                       ; preds = %for.cond39
  %k2.0.64 = sext i32 %k2.0 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %k2.0.64
  %aik2 = load double, ptr %arrayidx45, align 8
  %Arow_k2.off = mul nsw i64 %k2.0.64, %n64
  %Arow_k2.ptr = getelementptr inbounds double, ptr %A, i64 %Arow_k2.off
  %arrayidx49 = getelementptr inbounds double, ptr %Arow_k2.ptr, i64 %j2.0.64
  %akj2 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %aik2, %akj2
  %sub51 = fsub double %w2.0, %mul50
  %inc53 = add nsw i32 %k2.0, 1
  br label %for.cond39, !llvm.loop !9

for.end54:                                        ; preds = %for.cond39
  %arrayidx58 = getelementptr inbounds double, ptr %Arow_i.ptr, i64 %j2.0.64
  store double %w2.0, ptr %arrayidx58, align 8
  br label %for.inc59

for.inc59:                                        ; preds = %for.end54
  %inc60 = add nsw i32 %j2.0, 1
  br label %for.cond32, !llvm.loop !10

for.end61:                                        ; preds = %for.cond32
  br label %for.inc62

for.inc62:                                        ; preds = %for.end61
  %inc63 = add nsw i32 %i.0, 1
  br label %for.cond, !llvm.loop !11

for.end64:                                        ; preds = %for.cond
  br label %phase2.check

phase2.check:                                     ; preds = %for.end64, %entry
  br i1 %cmp.n.pos, label %phase2.preheader, label %phase3.check

phase2.preheader:
  %n64.p2 = sext i32 %n to i64
  br label %for.cond65

for.cond65:                                       ; preds = %for.inc86, %phase2.preheader
  %i3.0 = phi i32 [ 0, %phase2.preheader ], [ %inc87, %for.inc86 ]
  %i3.0.64 = sext i32 %i3.0 to i64
  %Arow_i3.off = mul nsw i64 %i3.0.64, %n64.p2
  %Arow_i3.ptr = getelementptr inbounds double, ptr %A, i64 %Arow_i3.off
  %cmp66 = icmp slt i32 %i3.0, %n
  br i1 %cmp66, label %for.body67, label %for.end88

for.body67:                                       ; preds = %for.cond65
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i3.0.64
  %w3.0 = load double, ptr %arrayidx69, align 8
  br label %for.cond70

for.cond70:                                       ; preds = %for.body72, %for.body67
  %j3.0 = phi i32 [ 0, %for.body67 ], [ %inc82, %for.body72 ]
  %w4.0 = phi double [ %w3.0, %for.body67 ], [ %sub80, %for.body72 ]
  %cmp71 = icmp slt i32 %j3.0, %i3.0
  br i1 %cmp71, label %for.body72, label %for.end83

for.body72:                                       ; preds = %for.cond70
  %j3.0.64 = sext i32 %j3.0 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %Arow_i3.ptr, i64 %j3.0.64
  %aij3 = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3.0.64
  %yj = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %aij3, %yj
  %sub80 = fsub double %w4.0, %mul79
  %inc82 = add nsw i32 %j3.0, 1
  br label %for.cond70, !llvm.loop !12

for.end83:                                        ; preds = %for.cond70
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i3.0.64
  store double %w4.0, ptr %arrayidx85, align 8
  br label %for.inc86

for.inc86:                                        ; preds = %for.end83
  %inc87 = add nsw i32 %i3.0, 1
  br label %for.cond65, !llvm.loop !13

for.end88:                                        ; preds = %for.cond65
  br label %phase3.check

phase3.check:                                     ; preds = %for.end88, %phase2.check
  %i.start = sub nsw i32 %n, 1
  %cmp.p3.pos = icmp sge i32 %i.start, 0
  br i1 %cmp.p3.pos, label %phase3.preheader, label %for.end118

phase3.preheader:
  %n64.p3 = sext i32 %n to i64
  br label %for.cond90

for.cond90:                                       ; preds = %for.inc117, %phase3.preheader
  %i5.0 = phi i32 [ %i.start, %phase3.preheader ], [ %dec, %for.inc117 ]
  %i5.0.64 = sext i32 %i5.0 to i64
  %Arow_i5.off = mul nsw i64 %i5.0.64, %n64.p3
  %Arow_i5.ptr = getelementptr inbounds double, ptr %A, i64 %Arow_i5.off
  %cmp91 = icmp sge i32 %i5.0, 0
  br i1 %cmp91, label %for.body92, label %for.end118

for.body92:                                       ; preds = %for.cond90
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i5.0.64
  %w5.0 = load double, ptr %arrayidx94, align 8
  %add95 = add nsw i32 %i5.0, 1
  br label %for.cond96

for.cond96:                                       ; preds = %for.body98, %for.body92
  %j5.0 = phi i32 [ %add95, %for.body92 ], [ %inc108, %for.body98 ]
  %w6.0 = phi double [ %w5.0, %for.body92 ], [ %sub106, %for.body98 ]
  %cmp97 = icmp slt i32 %j5.0, %n
  br i1 %cmp97, label %for.body98, label %for.end109

for.body98:                                       ; preds = %for.cond96
  %j5.0.64 = sext i32 %j5.0 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %Arow_i5.ptr, i64 %j5.0.64
  %aij5 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j5.0.64
  %xj = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %aij5, %xj
  %sub106 = fsub double %w6.0, %mul105
  %inc108 = add nsw i32 %j5.0, 1
  br label %for.cond96, !llvm.loop !14

for.end109:                                       ; preds = %for.cond96
  %arrayidx113 = getelementptr inbounds double, ptr %Arow_i5.ptr, i64 %i5.0.64
  %aii5 = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %w6.0, %aii5
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i5.0.64
  store double %div114, ptr %arrayidx116, align 8
  br label %for.inc117

for.inc117:                                       ; preds = %for.end109
  %dec = add nsw i32 %i5.0, -1
  br label %for.cond90, !llvm.loop !15

for.end118:                                       ; preds = %for.cond90, %phase3.check
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
