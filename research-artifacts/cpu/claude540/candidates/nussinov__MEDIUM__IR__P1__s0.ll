; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_nussinov(i32 noundef %n, ptr noundef %seq, ptr noundef %table) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %n.ok, label %for.end199

n.ok:
  %n64 = zext i32 %n to i64
  %i0 = sub nsw i32 %n, 1
  br label %for.cond

for.cond:                                         ; preds = %for.inc198, %n.ok
  %i = phi i32 [ %i0, %n.ok ], [ %dec, %for.inc198 ]
  %cmp = icmp sge i32 %i, 0
  br i1 %cmp, label %for.body, label %for.end199

for.body:                                         ; preds = %for.cond
  %i64 = sext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow = getelementptr inbounds i32, ptr %table, i64 %irow.off
  %ip1 = add nsw i32 %i, 1
  %ip1.inbounds = icmp slt i32 %ip1, %n
  %ip1.64 = sext i32 %ip1 to i64
  %ip1row.off = mul nsw i64 %ip1.64, %n64
  %ip1row = getelementptr inbounds i32, ptr %table, i64 %ip1row.off
  %seqi = getelementptr inbounds i8, ptr %seq, i64 %i64
  %seqi.val = load i8, ptr %seqi, align 1
  %seqi.conv = sext i8 %seqi.val to i32
  br label %for.cond4

for.cond4:                                        ; preds = %for.inc195, %for.body
  %j = phi i32 [ %ip1, %for.body ], [ %inc196, %for.inc195 ]
  %cmp5 = icmp slt i32 %j, %n
  br i1 %cmp5, label %for.body6, label %for.end197

for.body6:                                        ; preds = %for.cond4
  %j64 = sext i32 %j to i64
  %jm1 = sub nsw i32 %j, 1
  %jm1.64 = sext i32 %jm1 to i64

  %tij.ptr = getelementptr inbounds i32, ptr %irow, i64 %j64
  %tijm1.ptr = getelementptr inbounds i32, ptr %irow, i64 %jm1.64

  %jm1.ge0 = icmp sge i32 %jm1, 0
  br i1 %jm1.ge0, label %if.then, label %if.end

if.then:                                          ; preds = %for.body6
  %v.tij.a = load i32, ptr %tij.ptr, align 4
  %v.tijm1.a = load i32, ptr %tijm1.ptr, align 4
  %cmp16 = icmp sge i32 %v.tij.a, %v.tijm1.a
  %cond = select i1 %cmp16, i32 %v.tij.a, i32 %v.tijm1.a
  store i32 %cond, ptr %tij.ptr, align 4
  br label %if.end

if.end:                                           ; preds = %cond.end, %for.body6
  br i1 %ip1.inbounds, label %if.then32, label %if.end60

if.then32:                                        ; preds = %if.end
  %tip1j.ptr = getelementptr inbounds i32, ptr %ip1row, i64 %j64
  %v.tij.b = load i32, ptr %tij.ptr, align 4
  %v.tip1j.b = load i32, ptr %tip1j.ptr, align 4
  %cmp42 = icmp sge i32 %v.tij.b, %v.tip1j.b
  %cond55 = select i1 %cmp42, i32 %v.tij.b, i32 %v.tip1j.b
  store i32 %cond55, ptr %tij.ptr, align 4
  br label %if.end60

if.end60:                                         ; preds = %if.then32, %if.end
  %jm1.ge0.2 = icmp sge i32 %jm1, 0
  %and.cond = and i1 %jm1.ge0.2, %ip1.inbounds
  br i1 %and.cond, label %if.then65, label %if.end151

if.then65:                                        ; preds = %if.end60
  %sub66 = sub nsw i32 %j, 1
  %cmp67 = icmp slt i32 %i, %sub66
  br i1 %cmp67, label %if.then68, label %if.else

if.then68:                                        ; preds = %if.then65
  %v.tij.c = load i32, ptr %tij.ptr, align 4
  %tip1jm1.ptr = getelementptr inbounds i32, ptr %ip1row, i64 %jm1.64
  %v.tip1jm1 = load i32, ptr %tip1jm1.ptr, align 4
  %seqj = getelementptr inbounds i8, ptr %seq, i64 %j64
  %seqj.val = load i8, ptr %seqj, align 1
  %seqj.conv = sext i8 %seqj.val to i32
  %add84 = add nsw i32 %seqi.conv, %seqj.conv
  %cmp85 = icmp eq i32 %add84, 3
  %cond87 = select i1 %cmp85, i32 1, i32 0
  %add88 = add nsw i32 %v.tip1jm1, %cond87
  %cmp89 = icmp sge i32 %v.tij.c, %add88
  %cond115 = select i1 %cmp89, i32 %v.tij.c, i32 %add88
  store i32 %cond115, ptr %tij.ptr, align 4
  br label %if.end150

if.else:                                          ; preds = %if.then65
  %v.tij.d = load i32, ptr %tij.ptr, align 4
  %tip1jm1.ptr2 = getelementptr inbounds i32, ptr %ip1row, i64 %jm1.64
  %v.tip1jm1.2 = load i32, ptr %tip1jm1.ptr2, align 4
  %cmp130 = icmp sge i32 %v.tij.d, %v.tip1jm1.2
  %cond145 = select i1 %cmp130, i32 %v.tij.d, i32 %v.tip1jm1.2
  store i32 %cond145, ptr %tij.ptr, align 4
  br label %if.end150

if.end150:                                        ; preds = %if.else, %if.then68
  br label %if.end151

if.end151:                                        ; preds = %if.end150, %if.end60
  %k0 = add nsw i32 %i, 1
  %k.cmp0 = icmp slt i32 %k0, %j
  br i1 %k.cmp0, label %for.body156.preheader, label %for.end

for.body156.preheader:
  br label %for.body156

for.cond153:                                      ; preds = %for.inc
  %k.next = phi i32 [ %inc, %for.inc ]
  %cmp154 = icmp slt i32 %k.next, %j
  br i1 %cmp154, label %for.body156, label %for.end

for.body156:                                      ; preds = %for.cond153, %for.body156.preheader
  %k = phi i32 [ %k0, %for.body156.preheader ], [ %k.next, %for.cond153 ]
  %k64 = sext i32 %k to i64
  %kp1 = add nsw i32 %k, 1
  %kp1.64 = sext i32 %kp1 to i64
  %kp1row.off = mul nsw i64 %kp1.64, %n64
  %kp1row = getelementptr inbounds i32, ptr %table, i64 %kp1row.off

  %v.tij.e = load i32, ptr %tij.ptr, align 4
  %tik.ptr = getelementptr inbounds i32, ptr %irow, i64 %k64
  %v.tik = load i32, ptr %tik.ptr, align 4
  %tkp1j.ptr = getelementptr inbounds i32, ptr %kp1row, i64 %j64
  %v.tkp1j = load i32, ptr %tkp1j.ptr, align 4
  %add170 = add nsw i32 %v.tik, %v.tkp1j
  %cmp171 = icmp sge i32 %v.tij.e, %add170
  %cond190 = select i1 %cmp171, i32 %v.tij.e, i32 %add170
  store i32 %cond190, ptr %tij.ptr, align 4

  br label %for.inc

for.inc:                                          ; preds = %for.body156
  %inc = add nsw i32 %k, 1
  br label %for.cond153, !llvm.loop !6

for.end:                                          ; preds = %for.cond153, %if.end151
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
