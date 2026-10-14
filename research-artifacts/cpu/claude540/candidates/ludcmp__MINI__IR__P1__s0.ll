; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n.pos = icmp sgt i32 %n, 0
  br i1 %cmp.n.pos, label %preheader, label %for.end64

preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc62, %preheader
  %i = phi i32 [ 0, %preheader ], [ %inc63, %for.inc62 ]
  %cmp = icmp slt i32 %i, %n
  br i1 %cmp, label %for.body, label %for.end64.loopexit

for.body:                                         ; preds = %for.cond
  %i64 = sext i32 %i to i64
  %Arow_i = getelementptr inbounds double, ptr %A, i64 %i64
  %irow_off = mul nsw i64 %i64, %n64
  %Arow_i_base = getelementptr inbounds double, ptr %A, i64 %irow_off
  %cmp6.check = icmp slt i32 0, %i
  br i1 %cmp6.check, label %for.body7.preheader, label %for.end31

for.body7.preheader:
  br label %for.body7

for.body7:                                         ; preds = %for.inc29, %for.body7.preheader
  %j = phi i32 [ 0, %for.body7.preheader ], [ %inc30, %for.inc29 ]
  %j64 = sext i32 %j to i64
  %arrayidx9 = getelementptr inbounds double, ptr %Arow_i_base, i64 %j64
  %w0 = load double, ptr %arrayidx9, align 8
  %krow_off_j = mul nsw i64 %j64, %n64
  %cmp11.check = icmp slt i32 0, %j
  br i1 %cmp11.check, label %for.body12.preheader, label %for.end

for.body12.preheader:
  br label %for.body12

for.body12:                                        ; preds = %for.inc, %for.body12.preheader
  %k = phi i32 [ 0, %for.body12.preheader ], [ %inc, %for.inc ]
  %w.k = phi double [ %w0, %for.body12.preheader ], [ %sub, %for.inc ]
  %k64 = sext i32 %k to i64
  %arrayidx16 = getelementptr inbounds double, ptr %Arow_i_base, i64 %k64
  %v1 = load double, ptr %arrayidx16, align 8
  %krow_off = mul nsw i64 %k64, %n64
  %Arow_k_base = getelementptr inbounds double, ptr %A, i64 %krow_off
  %arrayidx20 = getelementptr inbounds double, ptr %Arow_k_base, i64 %j64
  %v2 = load double, ptr %arrayidx20, align 8
  %mul = fmul double %v1, %v2
  %sub = fsub double %w.k, %mul
  br label %for.inc

for.inc:                                          ; preds = %for.body12
  %inc = add nsw i32 %k, 1
  %cmp10.next = icmp slt i32 %inc, %j
  br i1 %cmp10.next, label %for.body12, label %for.end.loopexit

for.end.loopexit:
  %w.fromloop = phi double [ %sub, %for.inc ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body7
  %w.merge = phi double [ %w0, %for.body7 ], [ %w.fromloop, %for.end.loopexit ]
  %Arow_j_base = getelementptr inbounds double, ptr %A, i64 %krow_off_j
  %arrayidx24 = getelementptr inbounds double, ptr %Arow_j_base, i64 %j64
  %diag = load double, ptr %arrayidx24, align 8
  %div = fdiv double %w.merge, %diag
  store double %div, ptr %arrayidx9, align 8
  br label %for.inc29

for.inc29:                                        ; preds = %for.end
  %inc30 = add nsw i32 %j, 1
  %cmp5.next = icmp slt i32 %inc30, %i
  br i1 %cmp5.next, label %for.body7, label %for.end31.loopexit

for.end31.loopexit:
  br label %for.end31

for.end31:                                        ; preds = %for.end31.loopexit, %for.body
  br label %for.cond32

for.cond32:                                       ; preds = %for.inc59, %for.end31
  %j2 = phi i32 [ %i, %for.end31 ], [ %inc60, %for.inc59 ]
  %cmp33 = icmp slt i32 %j2, %n
  br i1 %cmp33, label %for.body34, label %for.end61

for.body34:                                       ; preds = %for.cond32
  %j2_64 = sext i32 %j2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %Arow_i_base, i64 %j2_64
  %w2_0 = load double, ptr %arrayidx38, align 8
  %cmp40.check = icmp slt i32 0, %i
  br i1 %cmp40.check, label %for.body41.preheader, label %for.end54

for.body41.preheader:
  br label %for.body41

for.body41:                                        ; preds = %for.inc52, %for.body41.preheader
  %k2 = phi i32 [ 0, %for.body41.preheader ], [ %inc53, %for.inc52 ]
  %w2.k = phi double [ %w2_0, %for.body41.preheader ], [ %sub51, %for.inc52 ]
  %k2_64 = sext i32 %k2 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %Arow_i_base, i64 %k2_64
  %v3 = load double, ptr %arrayidx45, align 8
  %k2row_off = mul nsw i64 %k2_64, %n64
  %Arow_k2_base = getelementptr inbounds double, ptr %A, i64 %k2row_off
  %arrayidx49 = getelementptr inbounds double, ptr %Arow_k2_base, i64 %j2_64
  %v4 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %v3, %v4
  %sub51 = fsub double %w2.k, %mul50
  br label %for.inc52

for.inc52:                                        ; preds = %for.body41
  %inc53 = add nsw i32 %k2, 1
  %cmp39.next = icmp slt i32 %inc53, %i
  br i1 %cmp39.next, label %for.body41, label %for.end54.loopexit

for.end54.loopexit:
  %w2.fromloop = phi double [ %sub51, %for.inc52 ]
  br label %for.end54

for.end54:                                        ; preds = %for.end54.loopexit, %for.body34
  %w2.merge = phi double [ %w2_0, %for.body34 ], [ %w2.fromloop, %for.end54.loopexit ]
  store double %w2.merge, ptr %arrayidx38, align 8
  br label %for.inc59

for.inc59:                                        ; preds = %for.end54
  %inc60 = add nsw i32 %j2, 1
  br label %for.cond32

for.end61:                                        ; preds = %for.cond32
  br label %for.inc62

for.inc62:                                        ; preds = %for.end61
  %inc63 = add nsw i32 %i, 1
  br label %for.cond

for.end64.loopexit:
  br label %for.end64

for.end64:                                        ; preds = %for.end64.loopexit, %entry
  br i1 %cmp.n.pos, label %preheader2, label %for.end88

preheader2:
  br label %for.cond65

for.cond65:                                       ; preds = %for.inc86, %preheader2
  %i2 = phi i32 [ 0, %preheader2 ], [ %inc87, %for.inc86 ]
  %cmp66 = icmp slt i32 %i2, %n
  br i1 %cmp66, label %for.body67, label %for.end88.loopexit

for.body67:                                       ; preds = %for.cond65
  %i2_64 = sext i32 %i2 to i64
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i2_64
  %w3_0 = load double, ptr %arrayidx69, align 8
  %irow_off3 = mul nsw i64 %i2_64, %n64
  %Arow_i3_base = getelementptr inbounds double, ptr %A, i64 %irow_off3
  %cmp71.check = icmp slt i32 0, %i2
  br i1 %cmp71.check, label %for.body72.preheader, label %for.end83

for.body72.preheader:
  br label %for.body72

for.body72:                                         ; preds = %for.inc81, %for.body72.preheader
  %j3 = phi i32 [ 0, %for.body72.preheader ], [ %inc82, %for.inc81 ]
  %w3.k = phi double [ %w3_0, %for.body72.preheader ], [ %sub80, %for.inc81 ]
  %j3_64 = sext i32 %j3 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %Arow_i3_base, i64 %j3_64
  %v5 = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3_64
  %v6 = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %v5, %v6
  %sub80 = fsub double %w3.k, %mul79
  br label %for.inc81

for.inc81:                                        ; preds = %for.body72
  %inc82 = add nsw i32 %j3, 1
  %cmp70.next = icmp slt i32 %inc82, %i2
  br i1 %cmp70.next, label %for.body72, label %for.end83.loopexit

for.end83.loopexit:
  %w3.fromloop = phi double [ %sub80, %for.inc81 ]
  br label %for.end83

for.end83:                                        ; preds = %for.end83.loopexit, %for.body67
  %w3.merge = phi double [ %w3_0, %for.body67 ], [ %w3.fromloop, %for.end83.loopexit ]
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i2_64
  store double %w3.merge, ptr %arrayidx85, align 8
  br label %for.inc86

for.inc86:                                        ; preds = %for.end83
  %inc87 = add nsw i32 %i2, 1
  br label %for.cond65

for.end88.loopexit:
  br label %for.end88

for.end88:                                        ; preds = %for.end88.loopexit, %for.end64
  %sub89 = sub nsw i32 %n, 1
  %cmp.n.pos2 = icmp sge i32 %sub89, 0
  br i1 %cmp.n.pos2, label %preheader3, label %for.end118

preheader3:
  br label %for.cond90

for.cond90:                                       ; preds = %for.inc117, %preheader3
  %i3 = phi i32 [ %sub89, %preheader3 ], [ %dec, %for.inc117 ]
  %cmp91 = icmp sge i32 %i3, 0
  br i1 %cmp91, label %for.body92, label %for.end118.loopexit

for.body92:                                       ; preds = %for.cond90
  %i3_64 = sext i32 %i3 to i64
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i3_64
  %w4_0 = load double, ptr %arrayidx94, align 8
  %j4_init = add nsw i32 %i3, 1
  %irow_off4 = mul nsw i64 %i3_64, %n64
  %Arow_i4_base = getelementptr inbounds double, ptr %A, i64 %irow_off4
  %cmp97.check = icmp slt i32 %j4_init, %n
  br i1 %cmp97.check, label %for.body98.preheader, label %for.end109

for.body98.preheader:
  br label %for.body98

for.body98:                                         ; preds = %for.inc107, %for.body98.preheader
  %j4 = phi i32 [ %j4_init, %for.body98.preheader ], [ %inc108, %for.inc107 ]
  %w4.k = phi double [ %w4_0, %for.body98.preheader ], [ %sub106, %for.inc107 ]
  %j4_64 = sext i32 %j4 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %Arow_i4_base, i64 %j4_64
  %v7 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j4_64
  %v8 = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %v7, %v8
  %sub106 = fsub double %w4.k, %mul105
  br label %for.inc107

for.inc107:                                       ; preds = %for.body98
  %inc108 = add nsw i32 %j4, 1
  %cmp96.next = icmp slt i32 %inc108, %n
  br i1 %cmp96.next, label %for.body98, label %for.end109.loopexit

for.end109.loopexit:
  %w4.fromloop = phi double [ %sub106, %for.inc107 ]
  br label %for.end109

for.end109:                                       ; preds = %for.end109.loopexit, %for.body92
  %w4.merge = phi double [ %w4_0, %for.body92 ], [ %w4.fromloop, %for.end109.loopexit ]
  %arrayidx113 = getelementptr inbounds double, ptr %Arow_i4_base, i64 %i3_64
  %diag2 = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %w4.merge, %diag2
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i3_64
  store double %div114, ptr %arrayidx116, align 8
  br label %for.inc117

for.inc117:                                       ; preds = %for.end109
  %dec = add nsw i32 %i3, -1
  br label %for.cond90

for.end118.loopexit:
  br label %for.end118

for.end118:                                       ; preds = %for.end118.loopexit, %for.end88
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
