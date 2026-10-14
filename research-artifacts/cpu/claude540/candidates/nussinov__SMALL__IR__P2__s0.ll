; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_nussinov(i32 noundef %n, ptr noundef %seq, ptr noundef %table) #0 {
entry:
  %cmp.n.pos = icmp sgt i32 %n, 0
  br i1 %cmp.n.pos, label %outer.preheader, label %for.end199

outer.preheader:
  %n64 = zext i32 %n to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc198, %outer.preheader
  %i = phi i32 [ %n, %outer.preheader ], [ %dec, %for.inc198 ]
  %i.dec0 = add nsw i32 %i, -1
  %cmp = icmp sge i32 %i.dec0, 0
  br i1 %cmp, label %for.body, label %for.end199

for.body:                                         ; preds = %for.cond
  %ii = add nsw i32 %i, -1
  %ii64 = sext i32 %ii to i64
  %row_i_off = mul nsw i64 %ii64, %n64
  %row_i = getelementptr inbounds i32, ptr %table, i64 %row_i_off
  %ip1 = add nsw i32 %ii, 1
  %ip1_inb = icmp slt i32 %ip1, %n
  %ip1_64 = sext i32 %ip1 to i64
  %row_ip1_off = mul nsw i64 %ip1_64, %n64
  %row_ip1 = getelementptr inbounds i32, ptr %table, i64 %row_ip1_off
  %jstart = add nsw i32 %ii, 1
  br label %for.cond4

for.cond4:                                        ; preds = %for.inc195, %for.body
  %j = phi i32 [ %jstart, %for.body ], [ %inc196, %for.inc195 ]
  %cmp5 = icmp slt i32 %j, %n
  br i1 %cmp5, label %for.body6, label %for.end197

for.body6:                                        ; preds = %for.cond4
  %j64 = sext i32 %j to i64
  %jm1 = add nsw i32 %j, -1
  %jm1_64 = sext i32 %jm1 to i64
  %cmp8 = icmp sge i32 %jm1, 0
  br i1 %cmp8, label %if.then, label %if.end

if.then:                                          ; preds = %for.body6
  %arrayidx.ij = getelementptr inbounds i32, ptr %row_i, i64 %j64
  %v.ij = load i32, ptr %arrayidx.ij, align 4
  %arrayidx.ijm1 = getelementptr inbounds i32, ptr %row_i, i64 %jm1_64
  %v.ijm1 = load i32, ptr %arrayidx.ijm1, align 4
  %cmp16 = icmp sge i32 %v.ij, %v.ijm1
  %cond = select i1 %cmp16, i32 %v.ij, i32 %v.ijm1
  store i32 %cond, ptr %arrayidx.ij, align 4
  br label %if.end

if.end:                                           ; preds = %cond.end, %for.body6
  br i1 %ip1_inb, label %if.then32, label %if.end60

if.then32:                                        ; preds = %if.end
  %arrayidx.ij.2 = getelementptr inbounds i32, ptr %row_i, i64 %j64
  %v.ij.2 = load i32, ptr %arrayidx.ij.2, align 4
  %arrayidx.ip1j = getelementptr inbounds i32, ptr %row_ip1, i64 %j64
  %v.ip1j = load i32, ptr %arrayidx.ip1j, align 4
  %cmp42 = icmp sge i32 %v.ij.2, %v.ip1j
  %cond55 = select i1 %cmp42, i32 %v.ij.2, i32 %v.ip1j
  store i32 %cond55, ptr %arrayidx.ij.2, align 4
  br label %if.end60

if.end60:                                         ; preds = %cond.end54, %if.end
  %cmp62 = icmp sge i32 %jm1, 0
  br i1 %cmp62, label %land.lhs.true, label %if.end151

land.lhs.true:                                    ; preds = %if.end60
  br i1 %ip1_inb, label %if.then65, label %if.end151

if.then65:                                        ; preds = %land.lhs.true
  %jm2 = add nsw i32 %j, -2
  %cmp67 = icmp slt i32 %ii, %jm2
  br i1 %cmp67, label %if.then68, label %if.else

if.then68:                                        ; preds = %if.then65
  %arrayidx.ij.3 = getelementptr inbounds i32, ptr %row_i, i64 %j64
  %v.ij.3 = load i32, ptr %arrayidx.ij.3, align 4
  %arrayidx.ip1jm1 = getelementptr inbounds i32, ptr %row_ip1, i64 %jm1_64
  %v.ip1jm1 = load i32, ptr %arrayidx.ip1jm1, align 4
  %arrayidx.seq.i = getelementptr inbounds i8, ptr %seq, i64 %ii64
  %s.i = load i8, ptr %arrayidx.seq.i, align 1
  %conv = sext i8 %s.i to i32
  %arrayidx.seq.j = getelementptr inbounds i8, ptr %seq, i64 %j64
  %s.j = load i8, ptr %arrayidx.seq.j, align 1
  %conv83 = sext i8 %s.j to i32
  %add84 = add nsw i32 %conv, %conv83
  %cmp85 = icmp eq i32 %add84, 3
  %cond87 = select i1 %cmp85, i32 1, i32 0
  %add88 = add nsw i32 %v.ip1jm1, %cond87
  %cmp89 = icmp sge i32 %v.ij.3, %add88
  %cond115 = select i1 %cmp89, i32 %v.ij.3, i32 %add88
  store i32 %cond115, ptr %arrayidx.ij.3, align 4
  br label %if.end150

if.else:                                          ; preds = %if.then65
  %arrayidx.ij.4 = getelementptr inbounds i32, ptr %row_i, i64 %j64
  %v.ij.4 = load i32, ptr %arrayidx.ij.4, align 4
  %arrayidx.ip1jm1.2 = getelementptr inbounds i32, ptr %row_ip1, i64 %jm1_64
  %v.ip1jm1.2 = load i32, ptr %arrayidx.ip1jm1.2, align 4
  %cmp130 = icmp sge i32 %v.ij.4, %v.ip1jm1.2
  %cond145 = select i1 %cmp130, i32 %v.ij.4, i32 %v.ip1jm1.2
  store i32 %cond145, ptr %arrayidx.ij.4, align 4
  br label %if.end150

if.end150:                                        ; preds = %if.else, %if.then68
  br label %if.end151

if.end151:                                        ; preds = %if.end150, %land.lhs.true, %if.end60
  %kstart = add nsw i32 %ii, 1
  %cmp.k.entry = icmp slt i32 %kstart, %j
  br i1 %cmp.k.entry, label %for.body156.preheader, label %for.end

for.body156.preheader:
  %arrayidx.ij.5 = getelementptr inbounds i32, ptr %row_i, i64 %j64
  br label %for.body156

for.body156:                                      ; preds = %for.body156.preheader, %for.body156
  %k = phi i32 [ %kstart, %for.body156.preheader ], [ %inc, %for.body156 ]
  %v.ij.cur = load i32, ptr %arrayidx.ij.5, align 4
  %k64 = sext i32 %k to i64
  %arrayidx.ik = getelementptr inbounds i32, ptr %row_i, i64 %k64
  %v.ik = load i32, ptr %arrayidx.ik, align 4
  %kp1 = add nsw i32 %k, 1
  %kp1_64 = sext i32 %kp1 to i64
  %row_kp1_off = mul nsw i64 %kp1_64, %n64
  %row_kp1 = getelementptr inbounds i32, ptr %table, i64 %row_kp1_off
  %arrayidx.kp1j = getelementptr inbounds i32, ptr %row_kp1, i64 %j64
  %v.kp1j = load i32, ptr %arrayidx.kp1j, align 4
  %add170 = add nsw i32 %v.ik, %v.kp1j
  %cmp171 = icmp sge i32 %v.ij.cur, %add170
  %cond190 = select i1 %cmp171, i32 %v.ij.cur, i32 %add170
  store i32 %cond190, ptr %arrayidx.ij.5, align 4
  %inc = add nsw i32 %k, 1
  %cmp154 = icmp slt i32 %inc, %j
  br i1 %cmp154, label %for.body156, label %for.end.loopexit, !llvm.loop !6

for.end.loopexit:                                 ; preds = %for.body156
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %if.end151
  br label %for.inc195

for.inc195:                                       ; preds = %for.end
  %inc196 = add nsw i32 %j, 1
  br label %for.cond4, !llvm.loop !8

for.end197:                                       ; preds = %for.cond4
  br label %for.inc198

for.inc198:                                       ; preds = %for.end197
  %dec = add nsw i32 %i, -1
  br label %for.cond, !llvm.loop !9

for.end199:                                       ; preds = %for.cond, %entry
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
