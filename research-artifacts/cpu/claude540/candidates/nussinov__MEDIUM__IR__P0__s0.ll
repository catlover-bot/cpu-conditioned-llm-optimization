; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_nussinov(i32 noundef %n, ptr noundef %seq, ptr noundef %table) #0 {
entry:
  %n64 = sext i32 %n to i64
  %i0 = sub nsw i32 %n, 1
  %i0.cmp = icmp sge i32 %i0, 0
  br i1 %i0.cmp, label %outer.preheader, label %for.end199

outer.preheader:
  br label %for.cond

for.cond:                                         ; preds = %for.inc198, %outer.preheader
  %i = phi i32 [ %i0, %outer.preheader ], [ %dec, %for.inc198 ]

  %jstart = add nsw i32 %i, 1
  %cmp5.0 = icmp slt i32 %jstart, %n
  br i1 %cmp5.0, label %for.body6.preheader, label %for.end197

for.body6.preheader:
  %i64 = sext i32 %i to i64
  %irow.base = mul nsw i64 %i64, %n64
  %irow.ptr = getelementptr inbounds i32, ptr %table, i64 %irow.base
  %ip1 = add nsw i32 %i, 1
  %ip1.inb = icmp slt i32 %ip1, %n
  %ip1_64 = sext i32 %ip1 to i64
  %ip1row.base = mul nsw i64 %ip1_64, %n64
  %ip1row.ptr = getelementptr inbounds i32, ptr %table, i64 %ip1row.base
  %seqi.ptr = getelementptr inbounds i8, ptr %seq, i64 %i64
  %seqi.val = load i8, ptr %seqi.ptr, align 1
  %seqi.conv = sext i8 %seqi.val to i32
  br label %for.body6

for.body6:                                        ; preds = %for.inc195, %for.body6.preheader
  %j = phi i32 [ %jstart, %for.body6.preheader ], [ %inc196, %for.inc195 ]

  %arrayidx.ij = getelementptr inbounds i32, ptr %irow.ptr, i64 %j64.iv
  br label %dummy

dummy:
  br label %real.body6

real.body6:
  %j64 = sext i32 %j to i64
  %arrayidx.ij.real = getelementptr inbounds i32, ptr %irow.ptr, i64 %j64
  %sub7 = sub nsw i32 %j, 1
  %cmp8 = icmp sge i32 %sub7, 0
  br i1 %cmp8, label %if.then, label %if.end

if.then:                                          ; preds = %real.body6
  %sub7_64 = sext i32 %sub7 to i64
  %arrayidx.ijm1 = getelementptr inbounds i32, ptr %irow.ptr, i64 %sub7_64
  %v.ij = load i32, ptr %arrayidx.ij.real, align 4
  %v.ijm1 = load i32, ptr %arrayidx.ijm1, align 4
  %cmp16 = icmp sge i32 %v.ij, %v.ijm1
  %cond = select i1 %cmp16, i32 %v.ij, i32 %v.ijm1
  store i32 %cond, ptr %arrayidx.ij.real, align 4
  br label %if.end

if.end:                                           ; preds = %if.then, %real.body6
  br i1 %ip1.inb, label %if.then32, label %if.end60

if.then32:                                        ; preds = %if.end
  %arrayidx.ip1j = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %j64
  %v.ij.2 = load i32, ptr %arrayidx.ij.real, align 4
  %v.ip1j = load i32, ptr %arrayidx.ip1j, align 4
  %cmp42 = icmp sge i32 %v.ij.2, %v.ip1j
  %cond55 = select i1 %cmp42, i32 %v.ij.2, i32 %v.ip1j
  store i32 %cond55, ptr %arrayidx.ij.real, align 4
  br label %if.end60

if.end60:                                         ; preds = %if.then32, %if.end
  %cmp62 = icmp sge i32 %sub7, 0
  br i1 %cmp62, label %land.check, label %if.end151

land.check:
  br i1 %ip1.inb, label %if.then65, label %if.end151

if.then65:                                        ; preds = %land.check
  %sub66 = sub nsw i32 %j, 1
  %cmp67 = icmp slt i32 %i, %sub66
  br i1 %cmp67, label %if.then68, label %if.else

if.then68:                                        ; preds = %if.then65
  %v.ij.3 = load i32, ptr %arrayidx.ij.real, align 4
  %sub76 = sub nsw i32 %j, 1
  %sub76_64 = sext i32 %sub76 to i64
  %arrayidx.ip1.jm1 = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %sub76_64
  %v.ip1.jm1 = load i32, ptr %arrayidx.ip1.jm1, align 4
  %seqj.ptr = getelementptr inbounds i8, ptr %seq, i64 %j64
  %seqj.val = load i8, ptr %seqj.ptr, align 1
  %seqj.conv = sext i8 %seqj.val to i32
  %add84 = add nsw i32 %seqi.conv, %seqj.conv
  %cmp85 = icmp eq i32 %add84, 3
  %cond87 = select i1 %cmp85, i32 1, i32 0
  %add88 = add nsw i32 %v.ip1.jm1, %cond87
  %cmp89 = icmp sge i32 %v.ij.3, %add88
  %cond115 = select i1 %cmp89, i32 %v.ij.3, i32 %add88
  store i32 %cond115, ptr %arrayidx.ij.real, align 4
  br label %if.end150

if.else:                                          ; preds = %if.then65
  %v.ij.4 = load i32, ptr %arrayidx.ij.real, align 4
  %sub127 = sub nsw i32 %j, 1
  %sub127_64 = sext i32 %sub127 to i64
  %arrayidx.ip1.jm1.2 = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %sub127_64
  %v.ip1.jm1.2 = load i32, ptr %arrayidx.ip1.jm1.2, align 4
  %cmp130 = icmp sge i32 %v.ij.4, %v.ip1.jm1.2
  %cond145 = select i1 %cmp130, i32 %v.ij.4, i32 %v.ip1.jm1.2
  store i32 %cond145, ptr %arrayidx.ij.real, align 4
  br label %if.end150

if.end150:                                        ; preds = %if.else, %if.then68
  br label %if.end151

if.end151:                                        ; preds = %if.end150, %land.check, %if.end60
  %kstart = add nsw i32 %i, 1
  %cmp154.0 = icmp slt i32 %kstart, %j
  br i1 %cmp154.0, label %for.body156.preheader, label %for.end

for.body156.preheader:
  br label %for.body156

for.body156:                                      ; preds = %for.inc, %for.body156.preheader
  %k = phi i32 [ %kstart, %for.body156.preheader ], [ %inc, %for.inc ]
  %k64 = sext i32 %k to i64
  %arrayidx.ik = getelementptr inbounds i32, ptr %irow.ptr, i64 %k64
  %v.ik = load i32, ptr %arrayidx.ik, align 4
  %kp1 = add nsw i32 %k, 1
  %kp1_64 = sext i32 %kp1 to i64
  %kp1row.base = mul nsw i64 %kp1_64, %n64
  %kp1row.ptr = getelementptr inbounds i32, ptr %table, i64 %kp1row.base
  %arrayidx.kp1j = getelementptr inbounds i32, ptr %kp1row.ptr, i64 %j64
  %v.kp1j = load i32, ptr %arrayidx.kp1j, align 4
  %add170 = add nsw i32 %v.ik, %v.kp1j
  %v.ij.5 = load i32, ptr %arrayidx.ij.real, align 4
  %cmp171 = icmp sge i32 %v.ij.5, %add170
  %cond190 = select i1 %cmp171, i32 %v.ij.5, i32 %add170
  store i32 %cond190, ptr %arrayidx.ij.real, align 4
  br label %for.inc

for.inc:                                          ; preds = %for.body156
  %inc = add nsw i32 %k, 1
  %cmp154 = icmp slt i32 %inc, %j
  br i1 %cmp154, label %for.body156, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %if.end151
  br label %for.inc195

for.inc195:                                       ; preds = %for.end
  %inc196 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc196, %n
  br i1 %cmp5, label %for.body6, label %for.end197.loopexit

for.end197.loopexit:
  br label %for.end197

for.end197:                                       ; preds = %for.end197.loopexit, %for.cond
  br label %for.inc198

for.inc198:                                       ; preds = %for.end197
  %dec = add nsw i32 %i, -1
  %cmp = icmp sge i32 %dec, 0
  br i1 %cmp, label %for.cond, label %for.end199.loopexit

for.end199.loopexit:
  br label %for.end199

for.end199:                                       ; preds = %for.end199.loopexit, %entry
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
