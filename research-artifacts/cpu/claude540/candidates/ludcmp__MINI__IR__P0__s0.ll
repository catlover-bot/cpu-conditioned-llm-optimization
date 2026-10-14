; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_ludcmp(i32 noundef %n, ptr noundef %A, ptr noundef %b, ptr noundef %x, ptr noundef %y) #0 {
entry:
  %cmp.n.pos = icmp sgt i32 %n, 0
  br i1 %cmp.n.pos, label %n.check, label %for.end64

n.check:
  %n64 = sext i32 %n to i64

  br label %for.cond.outer

for.cond.outer:
  %i.0 = phi i32 [ 0, %n.check ], [ %inc63, %for.inc62 ]
  %i.0.64 = sext i32 %i.0 to i64
  %i.row = mul nsw i64 %i.0.64, %n64
  %Arow.i = getelementptr inbounds double, ptr %A, i64 %i.row
  %cmp.j1 = icmp sgt i32 %i.0, 0
  br i1 %cmp.j1, label %for.body.j1.preheader, label %for.end31

for.body.j1.preheader:
  br label %for.body7

for.body7:
  %j.0 = phi i32 [ 0, %for.body.j1.preheader ], [ %inc30, %for.inc29 ]
  %j.0.64 = sext i32 %j.0 to i64
  %Ajrow.gep = getelementptr inbounds double, ptr %Arow.i, i64 %j.0.64
  %w0 = load double, ptr %Ajrow.gep, align 8
  %cmp.k1 = icmp sgt i32 %j.0, 0
  br i1 %cmp.k1, label %for.body12.preheader, label %for.end

for.body12.preheader:
  br label %for.body12

for.body12:
  %k.0 = phi i32 [ 0, %for.body12.preheader ], [ %inc, %for.body12 ]
  %w.acc = phi double [ %w0, %for.body12.preheader ], [ %sub, %for.body12 ]
  %k.0.64 = sext i32 %k.0 to i64
  %Aik.gep = getelementptr inbounds double, ptr %Arow.i, i64 %k.0.64
  %Aik = load double, ptr %Aik.gep, align 8
  %k.row = mul nsw i64 %k.0.64, %n64
  %Akrow.gep = getelementptr inbounds double, ptr %A, i64 %k.row
  %Akj.gep = getelementptr inbounds double, ptr %Akrow.gep, i64 %j.0.64
  %Akj = load double, ptr %Akj.gep, align 8
  %mul = fmul double %Aik, %Akj
  %sub = fsub double %w.acc, %mul
  %inc = add nsw i32 %k.0, 1
  %cmp.k = icmp slt i32 %inc, %j.0
  br i1 %cmp.k, label %for.body12, label %for.end

for.end:
  %w.final = phi double [ %w0, %for.body7 ], [ %sub, %for.body12 ]
  %Ajj.gep = getelementptr inbounds double, ptr %A, i64 %j.0.64
  %Ajrow.j = mul nsw i64 %j.0.64, %n64
  %Ajj.gep2 = getelementptr inbounds double, ptr %A, i64 %Ajrow.j
  %Ajj.final = getelementptr inbounds double, ptr %Ajj.gep2, i64 %j.0.64
  %Ajj = load double, ptr %Ajj.final, align 8
  %div = fdiv double %w.final, %Ajj
  store double %div, ptr %Ajrow.gep, align 8
  br label %for.inc29

for.inc29:
  %inc30 = add nsw i32 %j.0, 1
  %cmp.j = icmp slt i32 %inc30, %i.0
  br i1 %cmp.j, label %for.body7, label %for.end31

for.end31:
  br label %for.body34

for.body34:
  %j2.0 = phi i32 [ %i.0, %for.end31 ], [ %inc60, %for.inc59 ]
  %j2.64 = sext i32 %j2.0 to i64
  %Aij2.gep = getelementptr inbounds double, ptr %Arow.i, i64 %j2.64
  %w2.0 = load double, ptr %Aij2.gep, align 8
  br i1 %cmp.j1, label %for.body41.preheader, label %for.end54

for.body41.preheader:
  br label %for.body41

for.body41:
  %k2.0 = phi i32 [ 0, %for.body41.preheader ], [ %inc53, %for.body41 ]
  %w2.acc = phi double [ %w2.0, %for.body41.preheader ], [ %sub51, %for.body41 ]
  %k2.64 = sext i32 %k2.0 to i64
  %Aik2.gep = getelementptr inbounds double, ptr %Arow.i, i64 %k2.64
  %Aik2 = load double, ptr %Aik2.gep, align 8
  %k2.row = mul nsw i64 %k2.64, %n64
  %Ak2row.gep = getelementptr inbounds double, ptr %A, i64 %k2.row
  %Ak2j.gep = getelementptr inbounds double, ptr %Ak2row.gep, i64 %j2.64
  %Ak2j = load double, ptr %Ak2j.gep, align 8
  %mul50 = fmul double %Aik2, %Ak2j
  %sub51 = fsub double %w2.acc, %mul50
  %inc53 = add nsw i32 %k2.0, 1
  %cmp.k2 = icmp slt i32 %inc53, %i.0
  br i1 %cmp.k2, label %for.body41, label %for.end54

for.end54:
  %w2.final = phi double [ %w2.0, %for.body34 ], [ %sub51, %for.body41 ]
  store double %w2.final, ptr %Aij2.gep, align 8
  br label %for.inc59

for.inc59:
  %inc60 = add nsw i32 %j2.0, 1
  %cmp.j2 = icmp slt i32 %inc60, %n
  br i1 %cmp.j2, label %for.body34, label %for.end61

for.end61:
  br label %for.inc62

for.inc62:
  %inc63 = add nsw i32 %i.0, 1
  %cmp.i = icmp slt i32 %inc63, %n
  br i1 %cmp.i, label %for.cond.outer, label %for.end64

for.end64:
  br i1 %cmp.n.pos, label %n.check2, label %for.end88

n.check2:
  %n64.2 = sext i32 %n to i64
  br label %for.body67

for.body67:
  %i2.0 = phi i32 [ 0, %n.check2 ], [ %inc87, %for.inc86 ]
  %i2.64 = sext i32 %i2.0 to i64
  %bi.gep = getelementptr inbounds double, ptr %b, i64 %i2.64
  %b.val = load double, ptr %bi.gep, align 8
  %cmp.j3 = icmp sgt i32 %i2.0, 0
  br i1 %cmp.j3, label %for.body72.preheader, label %for.end83

for.body72.preheader:
  %i2.row = mul nsw i64 %i2.64, %n64.2
  %Arow.i2 = getelementptr inbounds double, ptr %A, i64 %i2.row
  br label %for.body72

for.body72:
  %j3.0 = phi i32 [ 0, %for.body72.preheader ], [ %inc82, %for.body72 ]
  %w3.acc = phi double [ %b.val, %for.body72.preheader ], [ %sub80, %for.body72 ]
  %j3.64 = sext i32 %j3.0 to i64
  %Aij3.gep = getelementptr inbounds double, ptr %Arow.i2, i64 %j3.64
  %Aij3 = load double, ptr %Aij3.gep, align 8
  %yj.gep = getelementptr inbounds double, ptr %y, i64 %j3.64
  %yj = load double, ptr %yj.gep, align 8
  %mul79 = fmul double %Aij3, %yj
  %sub80 = fsub double %w3.acc, %mul79
  %inc82 = add nsw i32 %j3.0, 1
  %cmp.j3l = icmp slt i32 %inc82, %i2.0
  br i1 %cmp.j3l, label %for.body72, label %for.end83

for.end83:
  %w3.final = phi double [ %b.val, %for.body67 ], [ %sub80, %for.body72 ]
  %yi.gep = getelementptr inbounds double, ptr %y, i64 %i2.64
  store double %w3.final, ptr %yi.gep, align 8
  br label %for.inc86

for.inc86:
  %inc87 = add nsw i32 %i2.0, 1
  %cmp.i2 = icmp slt i32 %inc87, %n
  br i1 %cmp.i2, label %for.body67, label %for.end88

for.end88:
  br i1 %cmp.n.pos, label %n.check3, label %for.end118

n.check3:
  %n64.3 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  br label %for.body92

for.body92:
  %i3.0 = phi i32 [ %nm1, %n.check3 ], [ %dec, %for.inc117 ]
  %i3.64 = sext i32 %i3.0 to i64
  %yi3.gep = getelementptr inbounds double, ptr %y, i64 %i3.64
  %y.val = load double, ptr %yi3.gep, align 8
  %j4.start = add nsw i32 %i3.0, 1
  %cmp.j4 = icmp slt i32 %j4.start, %n
  br i1 %cmp.j4, label %for.body98.preheader, label %for.end109

for.body98.preheader:
  %i3.row = mul nsw i64 %i3.64, %n64.3
  %Arow.i3 = getelementptr inbounds double, ptr %A, i64 %i3.row
  br label %for.body98

for.body98:
  %j4.0 = phi i32 [ %j4.start, %for.body98.preheader ], [ %inc108, %for.body98 ]
  %w4.acc = phi double [ %y.val, %for.body98.preheader ], [ %sub106, %for.body98 ]
  %j4.64 = sext i32 %j4.0 to i64
  %Aij4.gep = getelementptr inbounds double, ptr %Arow.i3, i64 %j4.64
  %Aij4 = load double, ptr %Aij4.gep, align 8
  %xj.gep = getelementptr inbounds double, ptr %x, i64 %j4.64
  %xj = load double, ptr %xj.gep, align 8
  %mul105 = fmul double %Aij4, %xj
  %sub106 = fsub double %w4.acc, %mul105
  %inc108 = add nsw i32 %j4.0, 1
  %cmp.j4l = icmp slt i32 %inc108, %n
  br i1 %cmp.j4l, label %for.body98, label %for.end109

for.end109:
  %w4.final = phi double [ %y.val, %for.body92 ], [ %sub106, %for.body98 ]
  %i3.row2 = mul nsw i64 %i3.64, %n64.3
  %Arow.i3b = getelementptr inbounds double, ptr %A, i64 %i3.row2
  %Aii3.gep = getelementptr inbounds double, ptr %Arow.i3b, i64 %i3.64
  %Aii3 = load double, ptr %Aii3.gep, align 8
  %div114 = fdiv double %w4.final, %Aii3
  %xi3.gep = getelementptr inbounds double, ptr %x, i64 %i3.64
  store double %div114, ptr %xi3.gep, align 8
  br label %for.inc117

for.inc117:
  %dec = add nsw i32 %i3.0, -1
  %cmp.i3 = icmp sge i32 %dec, 0
  br i1 %cmp.i3, label %for.body92, label %for.end118

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
