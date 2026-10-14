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
  %cmp = icmp slt i32 %i.0, %n
  br i1 %cmp, label %for.body, label %phase2.check

for.body:                                         ; preds = %for.cond
  %i.64 = sext i32 %i.0 to i64
  %row.i = mul nsw i64 %i.64, %n64
  %rowptr.i = getelementptr inbounds double, ptr %A, i64 %row.i
  %cmp6.first = icmp slt i32 0, %i.0
  br i1 %cmp6.first, label %for.body7.preheader, label %for.end31

for.body7.preheader:
  br label %for.body7

for.body7:                                        ; preds = %for.body7.preheader, %for.end
  %j.0 = phi i32 [ %inc30, %for.end ], [ 0, %for.body7.preheader ]
  %j.64 = sext i32 %j.0 to i64
  %arrayidx9 = getelementptr inbounds double, ptr %rowptr.i, i64 %j.64
  %w0 = load double, ptr %arrayidx9, align 8
  %cmp11.first = icmp slt i32 0, %j.0
  br i1 %cmp11.first, label %for.body12.preheader, label %for.end

for.body12.preheader:
  br label %for.body12

for.body12:                                       ; preds = %for.body12.preheader, %for.body12
  %k.0 = phi i32 [ %inc, %for.body12 ], [ 0, %for.body12.preheader ]
  %w.acc = phi double [ %w0, %for.body12.preheader ], [ %sub, %for.body12 ]
  %k.64 = sext i32 %k.0 to i64
  %arrayidx16 = getelementptr inbounds double, ptr %rowptr.i, i64 %k.64
  %v1 = load double, ptr %arrayidx16, align 8
  %rowk = mul nsw i64 %k.64, %n64
  %rowptr.k = getelementptr inbounds double, ptr %A, i64 %rowk
  %arrayidx20 = getelementptr inbounds double, ptr %rowptr.k, i64 %j.64
  %v2 = load double, ptr %arrayidx20, align 8
  %mul = fmul double %v1, %v2
  %sub = fsub double %w.acc, %mul
  %inc = add nsw i32 %k.0, 1
  %cmp11 = icmp slt i32 %inc, %j.0
  br i1 %cmp11, label %for.body12, label %for.end

for.end:                                          ; preds = %for.body12, %for.body7
  %w.final = phi double [ %w0, %for.body7 ], [ %sub, %for.body12 ]
  %arrayidx24 = getelementptr inbounds double, ptr %rowptr.i, i64 %j.64
  %diag.j = mul nsw i64 %j.64, %n64
  %rowptr.j = getelementptr inbounds double, ptr %A, i64 %diag.j
  %arrayidx24d = getelementptr inbounds double, ptr %rowptr.j, i64 %j.64
  %diagval = load double, ptr %arrayidx24d, align 8
  %div = fdiv double %w.final, %diagval
  store double %div, ptr %arrayidx24, align 8
  %inc30 = add nsw i32 %j.0, 1
  %cmp5 = icmp slt i32 %inc30, %i.0
  br i1 %cmp5, label %for.body7, label %for.end31

for.end31:                                        ; preds = %for.end, %for.body
  %cmp33.first = icmp slt i32 %i.0, %n
  br i1 %cmp33.first, label %for.body34.preheader, label %for.end61

for.body34.preheader:
  br label %for.body34

for.body34:                                       ; preds = %for.body34.preheader, %for.end54
  %j2.0 = phi i32 [ %inc60, %for.end54 ], [ %i.0, %for.body34.preheader ]
  %j2.64 = sext i32 %j2.0 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %rowptr.i, i64 %j2.64
  %w1 = load double, ptr %arrayidx38, align 8
  %cmp40.first = icmp slt i32 0, %i.0
  br i1 %cmp40.first, label %for.body41.preheader, label %for.end54

for.body41.preheader:
  br label %for.body41

for.body41:                                       ; preds = %for.body41.preheader, %for.body41
  %k2.0 = phi i32 [ %inc53, %for.body41 ], [ 0, %for.body41.preheader ]
  %w1.acc = phi double [ %w1, %for.body41.preheader ], [ %sub51, %for.body41 ]
  %k2.64 = sext i32 %k2.0 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %rowptr.i, i64 %k2.64
  %v3 = load double, ptr %arrayidx45, align 8
  %rowk2 = mul nsw i64 %k2.64, %n64
  %rowptr.k2 = getelementptr inbounds double, ptr %A, i64 %rowk2
  %arrayidx49 = getelementptr inbounds double, ptr %rowptr.k2, i64 %j2.64
  %v4 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %v3, %v4
  %sub51 = fsub double %w1.acc, %mul50
  %inc53 = add nsw i32 %k2.0, 1
  %cmp40 = icmp slt i32 %inc53, %i.0
  br i1 %cmp40, label %for.body41, label %for.end54

for.end54:                                        ; preds = %for.body41, %for.body34
  %w1.final = phi double [ %w1, %for.body34 ], [ %sub51, %for.body41 ]
  %arrayidx58 = getelementptr inbounds double, ptr %rowptr.i, i64 %j2.64
  store double %w1.final, ptr %arrayidx58, align 8
  %inc60 = add nsw i32 %j2.0, 1
  %cmp33 = icmp slt i32 %inc60, %n
  br i1 %cmp33, label %for.body34, label %for.end61

for.end61:                                        ; preds = %for.end54, %for.end31
  br label %for.inc62

for.inc62:                                        ; preds = %for.end61
  %inc63 = add nsw i32 %i.0, 1
  br label %for.cond

phase2.check:                                     ; preds = %for.inc62, %entry
  %cmp.n.pos2 = icmp sgt i32 %n, 0
  br i1 %cmp.n.pos2, label %phase2.preheader, label %phase3.setup

phase2.preheader:
  %n64.p2 = sext i32 %n to i64
  br label %for.cond65

for.cond65:                                       ; preds = %for.inc86, %phase2.preheader
  %i2.0 = phi i32 [ 0, %phase2.preheader ], [ %inc87, %for.inc86 ]
  %cmp66 = icmp slt i32 %i2.0, %n
  br i1 %cmp66, label %for.body67, label %phase3.setup

for.body67:                                       ; preds = %for.cond65
  %i2.64 = sext i32 %i2.0 to i64
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i2.64
  %bw0 = load double, ptr %arrayidx69, align 8
  %row2.i = mul nsw i64 %i2.64, %n64.p2
  %rowptr2.i = getelementptr inbounds double, ptr %A, i64 %row2.i
  %cmp71.first = icmp slt i32 0, %i2.0
  br i1 %cmp71.first, label %for.body72.preheader, label %for.end83

for.body72.preheader:
  br label %for.body72

for.body72:                                       ; preds = %for.body72.preheader, %for.body72
  %j3.0 = phi i32 [ %inc82, %for.body72 ], [ 0, %for.body72.preheader ]
  %bw.acc = phi double [ %bw0, %for.body72.preheader ], [ %sub80, %for.body72 ]
  %j3.64 = sext i32 %j3.0 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %rowptr2.i, i64 %j3.64
  %av = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3.64
  %yv = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %av, %yv
  %sub80 = fsub double %bw.acc, %mul79
  %inc82 = add nsw i32 %j3.0, 1
  %cmp71 = icmp slt i32 %inc82, %i2.0
  br i1 %cmp71, label %for.body72, label %for.end83

for.end83:                                        ; preds = %for.body72, %for.body67
  %bw.final = phi double [ %bw0, %for.body67 ], [ %sub80, %for.body72 ]
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i2.64
  store double %bw.final, ptr %arrayidx85, align 8
  br label %for.inc86

for.inc86:                                        ; preds = %for.end83
  %inc87 = add nsw i32 %i2.0, 1
  br label %for.cond65

phase3.setup:                                     ; preds = %for.cond65, %phase2.check
  %n64.p3 = sext i32 %n to i64
  %sub89 = sub nsw i32 %n, 1
  br label %for.cond90

for.cond90:                                       ; preds = %for.inc117, %phase3.setup
  %i3.0 = phi i32 [ %sub89, %phase3.setup ], [ %dec, %for.inc117 ]
  %cmp91 = icmp sge i32 %i3.0, 0
  br i1 %cmp91, label %for.body92, label %for.end118

for.body92:                                       ; preds = %for.cond90
  %i3.64 = sext i32 %i3.0 to i64
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i3.64
  %yw0 = load double, ptr %arrayidx94, align 8
  %add95 = add nsw i32 %i3.0, 1
  %row3.i = mul nsw i64 %i3.64, %n64.p3
  %rowptr3.i = getelementptr inbounds double, ptr %A, i64 %row3.i
  %cmp97.first = icmp slt i32 %add95, %n
  br i1 %cmp97.first, label %for.body98.preheader, label %for.end109

for.body98.preheader:
  br label %for.body98

for.body98:                                       ; preds = %for.body98.preheader, %for.body98
  %j4.0 = phi i32 [ %inc108, %for.body98 ], [ %add95, %for.body98.preheader ]
  %yw.acc = phi double [ %yw0, %for.body98.preheader ], [ %sub106, %for.body98 ]
  %j4.64 = sext i32 %j4.0 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %rowptr3.i, i64 %j4.64
  %av2 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j4.64
  %xv = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %av2, %xv
  %sub106 = fsub double %yw.acc, %mul105
  %inc108 = add nsw i32 %j4.0, 1
  %cmp97 = icmp slt i32 %inc108, %n
  br i1 %cmp97, label %for.body98, label %for.end109

for.end109:                                       ; preds = %for.body98, %for.body92
  %yw.final = phi double [ %yw0, %for.body92 ], [ %sub106, %for.body98 ]
  %arrayidx113 = getelementptr inbounds double, ptr %rowptr3.i, i64 %i3.64
  %diagv = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %yw.final, %diagv
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i3.64
  store double %div114, ptr %arrayidx116, align 8
  br label %for.inc117

for.inc117:                                       ; preds = %for.end109
  %dec = add nsw i32 %i3.0, -1
  br label %for.cond90

for.end118:                                       ; preds = %for.cond90
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
