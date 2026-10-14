; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %for.end64

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc62, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc63, %for.inc62 ]
  %i64 = sext i32 %i to i64
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %i64
  %Arow.i.off = mul nsw i64 %i64, %n64
  %Arow.i.ptr = getelementptr inbounds double, ptr %A, i64 %Arow.i.off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body7.preheader, label %for.end31

for.body7.preheader:
  br label %for.body7

for.body7:                                        ; preds = %for.end, %for.body7.preheader
  %j = phi i32 [ 0, %for.body7.preheader ], [ %inc30, %for.end ]
  %j64 = sext i32 %j to i64
  %arrayidx9 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j64
  %w.init = load double, ptr %arrayidx9, align 8
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body12.preheader, label %for.end

for.body12.preheader:
  %krow.off = mul nsw i64 %j64, %n64
  br label %for.body12

for.body12:                                        ; preds = %for.body12, %for.body12.preheader
  %k = phi i32 [ 0, %for.body12.preheader ], [ %inc, %for.body12 ]
  %w.acc = phi double [ %w.init, %for.body12.preheader ], [ %sub, %for.body12 ]
  %k64 = sext i32 %k to i64
  %arrayidx16 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k64
  %A.ik = load double, ptr %arrayidx16, align 8
  %krow.ptr = getelementptr inbounds double, ptr %A, i64 %krow.off
  %arrayidx20 = getelementptr inbounds double, ptr %krow.ptr, i64 %j64
  %A.kj = load double, ptr %arrayidx20, align 8
  %mul = fmul double %A.ik, %A.kj
  %sub = fsub double %w.acc, %mul
  %inc = add nsw i32 %k, 1
  %cmp11 = icmp slt i32 %inc, %j
  br i1 %cmp11, label %for.body12, label %for.end.loopexit

for.end.loopexit:
  %sub.lcssa = phi double [ %sub, %for.body12 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body7
  %w.final = phi double [ %w.init, %for.body7 ], [ %sub.lcssa, %for.end.loopexit ]
  %arrayidx24 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j64
  %jrow.off = mul nsw i64 %j64, %n64
  %jrow.ptr = getelementptr inbounds double, ptr %A, i64 %jrow.off
  %arrayidx.jj = getelementptr inbounds double, ptr %jrow.ptr, i64 %j64
  %A.jj = load double, ptr %arrayidx.jj, align 8
  %div = fdiv double %w.final, %A.jj
  store double %div, ptr %arrayidx24, align 8
  %inc30 = add nsw i32 %j, 1
  %cmp6 = icmp slt i32 %inc30, %i
  br i1 %cmp6, label %for.body7, label %for.end31.loopexit

for.end31.loopexit:
  br label %for.end31

for.end31:                                        ; preds = %for.end31.loopexit, %for.cond
  br label %for.body34

for.body34:                                        ; preds = %for.inc59, %for.end31
  %j2 = phi i32 [ %i, %for.end31 ], [ %inc60, %for.inc59 ]
  %j2.64 = sext i32 %j2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j2.64
  %w2.init = load double, ptr %arrayidx38, align 8
  br i1 %cmp.j1, label %for.body41.preheader, label %for.end54

for.body41.preheader:
  br label %for.body41

for.body41:                                        ; preds = %for.body41, %for.body41.preheader
  %k2 = phi i32 [ 0, %for.body41.preheader ], [ %inc53, %for.body41 ]
  %w2.acc = phi double [ %w2.init, %for.body41.preheader ], [ %sub51, %for.body41 ]
  %k2.64 = sext i32 %k2 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %k2.64
  %A.ik2 = load double, ptr %arrayidx45, align 8
  %k2row.off = mul nsw i64 %k2.64, %n64
  %k2row.ptr = getelementptr inbounds double, ptr %A, i64 %k2row.off
  %arrayidx49 = getelementptr inbounds double, ptr %k2row.ptr, i64 %j2.64
  %A.kj2 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %A.ik2, %A.kj2
  %sub51 = fsub double %w2.acc, %mul50
  %inc53 = add nsw i32 %k2, 1
  %cmp40 = icmp slt i32 %inc53, %i
  br i1 %cmp40, label %for.body41, label %for.end54.loopexit

for.end54.loopexit:
  %sub51.lcssa = phi double [ %sub51, %for.body41 ]
  br label %for.end54

for.end54:                                        ; preds = %for.end54.loopexit, %for.body34
  %w2.final = phi double [ %w2.init, %for.body34 ], [ %sub51.lcssa, %for.end54.loopexit ]
  %arrayidx58 = getelementptr inbounds double, ptr %Arow.i.ptr, i64 %j2.64
  store double %w2.final, ptr %arrayidx58, align 8
  %inc60 = add nsw i32 %j2, 1
  %cmp33 = icmp slt i32 %inc60, %n
  br i1 %cmp33, label %for.body34, label %for.end61.loopexit

for.end61.loopexit:
  br label %for.end61

for.end61:                                        ; preds = %for.end61.loopexit
  br label %for.inc62

for.inc62:                                        ; preds = %for.end61
  %inc63 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc63, %n
  br i1 %cmp, label %for.cond, label %for.end64.loopexit

for.end64.loopexit:
  br label %for.end64

for.end64:                                        ; preds = %for.end64.loopexit, %entry
  br i1 %cmp.n, label %fwd.preheader, label %for.end88

fwd.preheader:
  %n64.2 = sext i32 %n to i64
  br label %for.cond65

for.cond65:                                       ; preds = %for.inc86, %fwd.preheader
  %i2 = phi i32 [ 0, %fwd.preheader ], [ %inc87, %for.inc86 ]
  %i2.64 = sext i32 %i2 to i64
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i2.64
  %b.i = load double, ptr %arrayidx69, align 8
  %Arow2.off = mul nsw i64 %i2.64, %n64.2
  %Arow2.ptr = getelementptr inbounds double, ptr %A, i64 %Arow2.off
  %cmp.j3 = icmp sgt i32 %i2, 0
  br i1 %cmp.j3, label %for.body72.preheader, label %for.end83

for.body72.preheader:
  br label %for.body72

for.body72:                                        ; preds = %for.body72, %for.body72.preheader
  %j3 = phi i32 [ 0, %for.body72.preheader ], [ %inc82, %for.body72 ]
  %w3.acc = phi double [ %b.i, %for.body72.preheader ], [ %sub80, %for.body72 ]
  %j3.64 = sext i32 %j3 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %Arow2.ptr, i64 %j3.64
  %A.ij3 = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3.64
  %y.j3 = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %A.ij3, %y.j3
  %sub80 = fsub double %w3.acc, %mul79
  %inc82 = add nsw i32 %j3, 1
  %cmp71 = icmp slt i32 %inc82, %i2
  br i1 %cmp71, label %for.body72, label %for.end83.loopexit

for.end83.loopexit:
  %sub80.lcssa = phi double [ %sub80, %for.body72 ]
  br label %for.end83

for.end83:                                        ; preds = %for.end83.loopexit, %for.cond65
  %w3.final = phi double [ %b.i, %for.cond65 ], [ %sub80.lcssa, %for.end83.loopexit ]
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i2.64
  store double %w3.final, ptr %arrayidx85, align 8
  %inc87 = add nsw i32 %i2, 1
  %cmp66 = icmp slt i32 %inc87, %n
  br i1 %cmp66, label %for.cond65, label %for.end88.loopexit

for.end88.loopexit:
  br label %for.end88

for.end88:                                        ; preds = %for.end88.loopexit, %for.end64
  %sub89 = sub nsw i32 %n, 1
  %cmp.bwd = icmp sge i32 %sub89, 0
  br i1 %cmp.bwd, label %bwd.preheader, label %for.end118

bwd.preheader:
  %n64.3 = sext i32 %n to i64
  br label %for.cond90

for.cond90:                                       ; preds = %for.inc117, %bwd.preheader
  %i4 = phi i32 [ %sub89, %bwd.preheader ], [ %dec, %for.inc117 ]
  %i4.64 = sext i32 %i4 to i64
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i4.64
  %y.i4 = load double, ptr %arrayidx94, align 8
  %add95 = add nsw i32 %i4, 1
  %Arow4.off = mul nsw i64 %i4.64, %n64.3
  %Arow4.ptr = getelementptr inbounds double, ptr %A, i64 %Arow4.off
  %cmp.j5 = icmp slt i32 %add95, %n
  br i1 %cmp.j5, label %for.body98.preheader, label %for.end109

for.body98.preheader:
  br label %for.body98

for.body98:                                        ; preds = %for.body98, %for.body98.preheader
  %j5 = phi i32 [ %add95, %for.body98.preheader ], [ %inc108, %for.body98 ]
  %w4.acc = phi double [ %y.i4, %for.body98.preheader ], [ %sub106, %for.body98 ]
  %j5.64 = sext i32 %j5 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %Arow4.ptr, i64 %j5.64
  %A.ij5 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j5.64
  %x.j5 = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %A.ij5, %x.j5
  %sub106 = fsub double %w4.acc, %mul105
  %inc108 = add nsw i32 %j5, 1
  %cmp97 = icmp slt i32 %inc108, %n
  br i1 %cmp97, label %for.body98, label %for.end109.loopexit

for.end109.loopexit:
  %sub106.lcssa = phi double [ %sub106, %for.body98 ]
  br label %for.end109

for.end109:                                       ; preds = %for.end109.loopexit, %for.cond90
  %w4.final = phi double [ %y.i4, %for.cond90 ], [ %sub106.lcssa, %for.end109.loopexit ]
  %arrayidx113 = getelementptr inbounds double, ptr %Arow4.ptr, i64 %i4.64
  %A.ii = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %w4.final, %A.ii
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i4.64
  store double %div114, ptr %arrayidx116, align 8
  %dec = add nsw i32 %i4, -1
  %cmp91 = icmp sge i32 %dec, 0
  br i1 %cmp91, label %for.cond90, label %for.end118.loopexit

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
