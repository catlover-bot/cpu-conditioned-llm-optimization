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
  br i1 %i0.cmp, label %for.i.preheader, label %for.end199

for.i.preheader:
  br label %for.cond

for.cond:                                         ; preds = %for.inc198, %for.i.preheader
  %i = phi i32 [ %i0, %for.i.preheader ], [ %dec, %for.inc198 ]
  %i64 = sext i32 %i to i64
  %i.row.off = mul nsw i64 %i64, %n64
  %row.i = getelementptr inbounds i32, ptr %table, i64 %i.row.off
  %ip1 = add nsw i32 %i, 1
  %ip1.64 = sext i32 %ip1 to i64
  %ip1.row.off = mul nsw i64 %ip1.64, %n64
  %row.ip1 = getelementptr inbounds i32, ptr %table, i64 %ip1.row.off
  %ip1.inbound = icmp slt i32 %ip1, %n
  %seq.i.ptr = getelementptr inbounds i8, ptr %seq, i64 %i64
  %seq.i.val = load i8, ptr %seq.i.ptr, align 1
  %seq.i.conv = sext i8 %seq.i.val to i32

  br label %for.cond4

for.cond4:                                        ; preds = %for.inc195, %for.cond
  %j = phi i32 [ %ip1, %for.cond ], [ %inc196, %for.inc195 ]
  %cmp5 = icmp slt i32 %j, %n
  br i1 %cmp5, label %for.body6, label %for.end197

for.body6:                                        ; preds = %for.cond4
  %j64 = sext i32 %j to i64
  %arrayidx.ij = getelementptr inbounds i32, ptr %row.i, i64 %j64
  %jm1 = sub nsw i32 %j, 1
  %jm1.64 = sext i32 %jm1 to i64

  %jm1.ge0 = icmp sge i32 %jm1, 0
  br i1 %jm1.ge0, label %if.then, label %if.end

if.then:                                          ; preds = %for.body6
  %arrayidx.ijm1 = getelementptr inbounds i32, ptr %row.i, i64 %jm1.64
  %v.ij.a = load i32, ptr %arrayidx.ij, align 4
  %v.ijm1.a = load i32, ptr %arrayidx.ijm1, align 4
  %cmp16 = icmp sge i32 %v.ij.a, %v.ijm1.a
  %cond.sel1 = select i1 %cmp16, i32 %v.ij.a, i32 %v.ijm1.a
  store i32 %cond.sel1, ptr %arrayidx.ij, align 4
  br label %if.end

if.end:                                           ; preds = %if.then, %for.body6
  br i1 %ip1.inbound, label %if.then32, label %if.end60

if.then32:                                        ; preds = %if.end
  %v.ij.b = load i32, ptr %arrayidx.ij, align 4
  %arrayidx.ip1j = getelementptr inbounds i32, ptr %row.ip1, i64 %j64
  %v.ip1j.b = load i32, ptr %arrayidx.ip1j, align 4
  %cmp42 = icmp sge i32 %v.ij.b, %v.ip1j.b
  %cond.sel2 = select i1 %cmp42, i32 %v.ij.b, i32 %v.ip1j.b
  store i32 %cond.sel2, ptr %arrayidx.ij, align 4
  br label %if.end60

if.end60:                                         ; preds = %if.then32, %if.end
  %jm1.ge0.2 = icmp sge i32 %jm1, 0
  %cmp64 = and i1 %jm1.ge0.2, %ip1.inbound
  br i1 %cmp64, label %if.then65, label %if.end151

if.then65:                                        ; preds = %if.end60
  %jm2 = sub nsw i32 %j, 1
  %cmp67 = icmp slt i32 %i, %jm2
  br i1 %cmp67, label %if.then68, label %if.else

if.then68:                                        ; preds = %if.then65
  %v.ij.c = load i32, ptr %arrayidx.ij, align 4
  %arrayidx.ip1jm1 = getelementptr inbounds i32, ptr %row.ip1, i64 %jm1.64
  %v.ip1jm1 = load i32, ptr %arrayidx.ip1jm1, align 4
  %seq.j.ptr = getelementptr inbounds i8, ptr %seq, i64 %j64
  %seq.j.val = load i8, ptr %seq.j.ptr, align 1
  %seq.j.conv = sext i8 %seq.j.val to i32
  %sumij = add nsw i32 %seq.i.conv, %seq.j.conv
  %cmp85 = icmp eq i32 %sumij, 3
  %cond87 = select i1 %cmp85, i32 1, i32 0
  %add88 = add nsw i32 %v.ip1jm1, %cond87
  %cmp89 = icmp sge i32 %v.ij.c, %add88
  %cond.sel3 = select i1 %cmp89, i32 %v.ij.c, i32 %add88
  store i32 %cond.sel3, ptr %arrayidx.ij, align 4
  br label %if.end150

if.else:                                          ; preds = %if.then65
  %v.ij.d = load i32, ptr %arrayidx.ij, align 4
  %arrayidx.ip1jm1.2 = getelementptr inbounds i32, ptr %row.ip1, i64 %jm1.64
  %v.ip1jm1.2 = load i32, ptr %arrayidx.ip1jm1.2, align 4
  %cmp130 = icmp sge i32 %v.ij.d, %v.ip1jm1.2
  %cond.sel4 = select i1 %cmp130, i32 %v.ij.d, i32 %v.ip1jm1.2
  store i32 %cond.sel4, ptr %arrayidx.ij, align 4
  br label %if.end150

if.end150:                                        ; preds = %if.else, %if.then68
  br label %if.end151

if.end151:                                        ; preds = %if.end150, %if.end60
  %k0 = add nsw i32 %i, 1
  %k0.cmp = icmp slt i32 %k0, %j
  br i1 %k0.cmp, label %for.body156.preheader, label %for.end

for.body156.preheader:
  br label %for.body156

for.body156:                                      ; preds = %for.body156, %for.body156.preheader
  %k = phi i32 [ %k0, %for.body156.preheader ], [ %inc, %for.body156 ]
  %k64 = sext i32 %k to i64
  %v.ij.e = load i32, ptr %arrayidx.ij, align 4
  %arrayidx.ik = getelementptr inbounds i32, ptr %row.i, i64 %k64
  %v.ik = load i32, ptr %arrayidx.ik, align 4
  %kp1 = add nsw i32 %k, 1
  %kp1.64 = sext i32 %kp1 to i64
  %kp1.row.off = mul nsw i64 %kp1.64, %n64
  %row.kp1 = getelementptr inbounds i32, ptr %table, i64 %kp1.row.off
  %arrayidx.kp1j = getelementptr inbounds i32, ptr %row.kp1, i64 %j64
  %v.kp1j = load i32, ptr %arrayidx.kp1j, align 4
  %add170 = add nsw i32 %v.ik, %v.kp1j
  %cmp171 = icmp sge i32 %v.ij.e, %add170
  %cond.sel5 = select i1 %cmp171, i32 %v.ij.e, i32 %add170
  store i32 %cond.sel5, ptr %arrayidx.ij, align 4
  %inc = add nsw i32 %k, 1
  %k.cmp = icmp slt i32 %inc, %j
  br i1 %k.cmp, label %for.body156, label %for.end.loopexit, !llvm.loop !6

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
  %i.cmp = icmp sge i32 %dec, 0
  br i1 %i.cmp, label %for.cond, label %for.end199.loopexit, !llvm.loop !9

for.end199.loopexit:                              ; preds = %for.inc198
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
