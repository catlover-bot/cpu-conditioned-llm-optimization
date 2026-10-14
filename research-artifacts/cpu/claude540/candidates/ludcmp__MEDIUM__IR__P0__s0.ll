; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %outer.preheader, label %second.check

outer.preheader:
  %n64 = sext i32 %n to i64
  br label %for.cond

for.cond:
  %i = phi i32 [ 0, %outer.preheader ], [ %inc63, %for.inc62 ]
  %i64 = sext i32 %i to i64
  %Arow_i = getelementptr inbounds double, ptr %A, i64 %i64
  %Arow_off = mul nsw i64 %i64, %n64
  %Arow_i_base = getelementptr inbounds double, ptr %A, i64 %Arow_off
  %cmp.j1 = icmp sgt i32 %i, 0
  br i1 %cmp.j1, label %for.body5.preheader, label %for.end31

for.body5.preheader:
  br label %for.cond5

for.cond5:
  %j = phi i32 [ 0, %for.body5.preheader ], [ %inc30, %for.inc29 ]
  %j64 = sext i32 %j to i64
  %arrayidx9 = getelementptr inbounds double, ptr %Arow_i_base, i64 %j64
  %w0 = load double, ptr %arrayidx9, align 8
  %cmp.k1 = icmp sgt i32 %j, 0
  br i1 %cmp.k1, label %for.body12.preheader, label %for.end

for.body12.preheader:
  %jrow_off = mul nsw i64 %j64, %n64
  %jrow_base = getelementptr inbounds double, ptr %A, i64 %jrow_off
  br label %for.body12

for.body12:
  %k = phi i32 [ 0, %for.body12.preheader ], [ %inc, %for.body12 ]
  %w.k = phi double [ %w0, %for.body12.preheader ], [ %sub, %for.body12 ]
  %k64 = sext i32 %k to i64
  %arrayidx16 = getelementptr inbounds double, ptr %Arow_i_base, i64 %k64
  %aik = load double, ptr %arrayidx16, align 8
  %arrayidx20 = getelementptr inbounds double, ptr %jrow_base, i64 %k64
  %akj = load double, ptr %arrayidx20, align 8
  %mul = fmul double %aik, %akj
  %sub = fsub double %w.k, %mul
  %inc = add nsw i32 %k, 1
  %cmp.k = icmp slt i32 %inc, %j
  br i1 %cmp.k, label %for.body12, label %for.end

for.end:
  %w.final = phi double [ %w0, %for.cond5 ], [ %sub, %for.body12 ]
  %arrayidx24 = getelementptr inbounds double, ptr %Arow_i_base, i64 %j64
  %ajj = load double, ptr %arrayidx24, align 8
  %div = fdiv double %w.final, %ajj
  store double %div, ptr %arrayidx9, align 8
  br label %for.inc29

for.inc29:
  %inc30 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc30, %i
  br i1 %cmp5, label %for.cond5, label %for.end31

for.end31:
  %cmp.j2 = icmp slt i32 %i, %n
  br i1 %cmp.j2, label %for.body34.preheader, label %for.inc62

for.body34.preheader:
  br label %for.cond32

for.cond32:
  %j2 = phi i32 [ %i, %for.body34.preheader ], [ %inc60, %for.inc59 ]
  %j2_64 = sext i32 %j2 to i64
  %arrayidx38 = getelementptr inbounds double, ptr %Arow_i_base, i64 %j2_64
  %w2_0 = load double, ptr %arrayidx38, align 8
  br i1 %cmp.j1, label %for.body41.preheader, label %for.end54

for.body41.preheader:
  br label %for.body41

for.body41:
  %k2 = phi i32 [ 0, %for.body41.preheader ], [ %inc53, %for.body41 ]
  %w2.k = phi double [ %w2_0, %for.body41.preheader ], [ %sub51, %for.body41 ]
  %k2_64 = sext i32 %k2 to i64
  %arrayidx45 = getelementptr inbounds double, ptr %Arow_i_base, i64 %k2_64
  %aik2 = load double, ptr %arrayidx45, align 8
  %k2row_off = mul nsw i64 %k2_64, %n64
  %k2row_base = getelementptr inbounds double, ptr %A, i64 %k2row_off
  %arrayidx49 = getelementptr inbounds double, ptr %k2row_base, i64 %j2_64
  %akj2 = load double, ptr %arrayidx49, align 8
  %mul50 = fmul double %aik2, %akj2
  %sub51 = fsub double %w2.k, %mul50
  %inc53 = add nsw i32 %k2, 1
  %cmp.k2 = icmp slt i32 %inc53, %i
  br i1 %cmp.k2, label %for.body41, label %for.end54

for.end54:
  %w2.final = phi double [ %w2_0, %for.cond32 ], [ %sub51, %for.body41 ]
  store double %w2.final, ptr %arrayidx38, align 8
  br label %for.inc59

for.inc59:
  %inc60 = add nsw i32 %j2, 1
  %cmp32 = icmp slt i32 %inc60, %n
  br i1 %cmp32, label %for.cond32, label %for.inc62

for.inc62:
  %inc63 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc63, %n
  br i1 %cmp, label %for.cond, label %second.check

second.check:
  %cmp.n2 = icmp sgt i32 %n, 0
  br i1 %cmp.n2, label %for.body67.preheader, label %third.check

for.body67.preheader:
  %n64.2 = sext i32 %n to i64
  br label %for.cond65

for.cond65:
  %i3 = phi i32 [ 0, %for.body67.preheader ], [ %inc87, %for.inc86 ]
  %i3_64 = sext i32 %i3 to i64
  %arrayidx69 = getelementptr inbounds double, ptr %b, i64 %i3_64
  %w3_0 = load double, ptr %arrayidx69, align 8
  %cmp.j3 = icmp sgt i32 %i3, 0
  br i1 %cmp.j3, label %for.body72.preheader, label %for.end83

for.body72.preheader:
  %i3row_off = mul nsw i64 %i3_64, %n64.2
  %i3row_base = getelementptr inbounds double, ptr %A, i64 %i3row_off
  br label %for.body72

for.body72:
  %j3 = phi i32 [ 0, %for.body72.preheader ], [ %inc82, %for.body72 ]
  %w3.k = phi double [ %w3_0, %for.body72.preheader ], [ %sub80, %for.body72 ]
  %j3_64 = sext i32 %j3 to i64
  %arrayidx76 = getelementptr inbounds double, ptr %i3row_base, i64 %j3_64
  %aij3 = load double, ptr %arrayidx76, align 8
  %arrayidx78 = getelementptr inbounds double, ptr %y, i64 %j3_64
  %yj3 = load double, ptr %arrayidx78, align 8
  %mul79 = fmul double %aij3, %yj3
  %sub80 = fsub double %w3.k, %mul79
  %inc82 = add nsw i32 %j3, 1
  %cmp.j3loop = icmp slt i32 %inc82, %i3
  br i1 %cmp.j3loop, label %for.body72, label %for.end83

for.end83:
  %w3.final = phi double [ %w3_0, %for.cond65 ], [ %sub80, %for.body72 ]
  %arrayidx85 = getelementptr inbounds double, ptr %y, i64 %i3_64
  store double %w3.final, ptr %arrayidx85, align 8
  br label %for.inc86

for.inc86:
  %inc87 = add nsw i32 %i3, 1
  %cmp65 = icmp slt i32 %inc87, %n
  br i1 %cmp65, label %for.cond65, label %third.check

third.check:
  %n64.3 = sext i32 %n to i64
  %start.i = sub nsw i32 %n, 1
  %cmp.start = icmp sge i32 %start.i, 0
  br i1 %cmp.start, label %for.body92.preheader, label %for.end118

for.body92.preheader:
  br label %for.cond90

for.cond90:
  %i4 = phi i32 [ %start.i, %for.body92.preheader ], [ %dec, %for.inc117 ]
  %i4_64 = sext i32 %i4 to i64
  %arrayidx94 = getelementptr inbounds double, ptr %y, i64 %i4_64
  %w4_0 = load double, ptr %arrayidx94, align 8
  %j4start = add nsw i32 %i4, 1
  %cmp.j4 = icmp slt i32 %j4start, %n
  br i1 %cmp.j4, label %for.body98.preheader, label %for.end109

for.body98.preheader:
  %i4row_off = mul nsw i64 %i4_64, %n64.3
  %i4row_base = getelementptr inbounds double, ptr %A, i64 %i4row_off
  br label %for.body98

for.body98:
  %j4 = phi i32 [ %j4start, %for.body98.preheader ], [ %inc108, %for.body98 ]
  %w4.k = phi double [ %w4_0, %for.body98.preheader ], [ %sub106, %for.body98 ]
  %j4_64 = sext i32 %j4 to i64
  %arrayidx102 = getelementptr inbounds double, ptr %i4row_base, i64 %j4_64
  %aij4 = load double, ptr %arrayidx102, align 8
  %arrayidx104 = getelementptr inbounds double, ptr %x, i64 %j4_64
  %xj4 = load double, ptr %arrayidx104, align 8
  %mul105 = fmul double %aij4, %xj4
  %sub106 = fsub double %w4.k, %mul105
  %inc108 = add nsw i32 %j4, 1
  %cmp.j4loop = icmp slt i32 %inc108, %n
  br i1 %cmp.j4loop, label %for.body98, label %for.end109

for.end109:
  %w4.final = phi double [ %w4_0, %for.cond90 ], [ %sub106, %for.body98 ]
  %i4row_off2 = mul nsw i64 %i4_64, %n64.3
  %i4row_base2 = getelementptr inbounds double, ptr %A, i64 %i4row_off2
  %arrayidx113 = getelementptr inbounds double, ptr %i4row_base2, i64 %i4_64
  %aii4 = load double, ptr %arrayidx113, align 8
  %div114 = fdiv double %w4.final, %aii4
  %arrayidx116 = getelementptr inbounds double, ptr %x, i64 %i4_64
  store double %div114, ptr %arrayidx116, align 8
  br label %for.inc117

for.inc117:
  %dec = add nsw i32 %i4, -1
  %cmp90 = icmp sge i32 %dec, 0
  br i1 %cmp90, label %for.cond90, label %for.end118

for.end118:
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
