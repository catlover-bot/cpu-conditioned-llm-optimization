; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_nussinov(i32 noundef %n, ptr noundef %seq, ptr noundef %table) #0 {
entry:
  %n64 = sext i32 %n to i64
  %i0 = sub nsw i32 %n, 1
  %cmp.entry = icmp sge i32 %i0, 0
  br i1 %cmp.entry, label %for.cond.preheader, label %for.end199

for.cond.preheader:                              ; preds = %entry
  br label %for.cond

for.cond:                                         ; preds = %for.inc198, %for.cond.preheader
  %i = phi i32 [ %i0, %for.cond.preheader ], [ %dec, %for.inc198 ]
  %i64 = sext i32 %i to i64
  %irow.off = mul nsw i64 %i64, %n64
  %irow.ptr = getelementptr inbounds i32, ptr %table, i64 %irow.off
  %ip1 = add nsw i32 %i, 1
  %cmp.j0 = icmp slt i32 %ip1, %n
  br i1 %cmp.j0, label %for.body.preheader, label %for.inc198

for.body.preheader:                              ; preds = %for.cond
  %ip1_64 = sext i32 %ip1 to i64
  %ip1row.off = mul nsw i64 %ip1_64, %n64
  %ip1row.ptr = getelementptr inbounds i32, ptr %table, i64 %ip1row.off
  %seq.i.ptr = getelementptr inbounds i8, ptr %seq, i64 %i64
  %seq.i.val = load i8, ptr %seq.i.ptr, align 1
  %seq.i.conv = sext i8 %seq.i.val to i32
  br label %for.cond4

for.cond4:                                        ; preds = %for.inc195, %for.body.preheader
  %j = phi i32 [ %ip1, %for.body.preheader ], [ %inc196, %for.inc195 ]

  ; table[i][j]
  %j64 = sext i32 %j to i64
  %tij.ptr = getelementptr inbounds i32, ptr %irow.ptr, i64 %j64
  %jm1 = sub nsw i32 %j, 1
  %jm1_64 = sext i32 %jm1 to i64

  %cmp8 = icmp sge i32 %jm1, 0
  br i1 %cmp8, label %if.then, label %if.end

if.then:                                          ; preds = %for.cond4
  %tij.val0 = load i32, ptr %tij.ptr, align 4
  %tijm1.ptr = getelementptr inbounds i32, ptr %irow.ptr, i64 %jm1_64
  %tijm1.val0 = load i32, ptr %tijm1.ptr, align 4
  %cmp16 = icmp sge i32 %tij.val0, %tijm1.val0
  %sel1 = select i1 %cmp16, i32 %tij.val0, i32 %tijm1.val0
  store i32 %sel1, ptr %tij.ptr, align 4
  br label %if.end

if.end:                                           ; preds = %if.then, %for.cond4
  br i1 %cmp.j0, label %if.then32, label %if.end60

if.then32:                                        ; preds = %if.end
  %tij.val1 = load i32, ptr %tij.ptr, align 4
  %tip1j.ptr = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %j64
  %tip1j.val0 = load i32, ptr %tip1j.ptr, align 4
  %cmp42 = icmp sge i32 %tij.val1, %tip1j.val0
  %sel2 = select i1 %cmp42, i32 %tij.val1, i32 %tip1j.val0
  store i32 %sel2, ptr %tij.ptr, align 4
  br label %if.end60

if.end60:                                         ; preds = %if.then32, %if.end
  %cmp62 = icmp sge i32 %jm1, 0
  br i1 %cmp62, label %land.lhs.true, label %if.end151

land.lhs.true:                                    ; preds = %if.end60
  br i1 %cmp.j0, label %if.then65, label %if.end151

if.then65:                                        ; preds = %land.lhs.true
  %sub66 = sub nsw i32 %j, 1
  %cmp67 = icmp slt i32 %i, %sub66
  br i1 %cmp67, label %if.then68, label %if.else

if.then68:                                        ; preds = %if.then65
  %tij.val2 = load i32, ptr %tij.ptr, align 4
  %tip1jm1.ptr = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %jm1_64
  %tip1jm1.val = load i32, ptr %tip1jm1.ptr, align 4
  %seq.j.ptr = getelementptr inbounds i8, ptr %seq, i64 %j64
  %seq.j.val = load i8, ptr %seq.j.ptr, align 1
  %seq.j.conv = sext i8 %seq.j.val to i32
  %sum = add nsw i32 %seq.i.conv, %seq.j.conv
  %cmp85 = icmp eq i32 %sum, 3
  %cond87 = select i1 %cmp85, i32 1, i32 0
  %add88 = add nsw i32 %tip1jm1.val, %cond87
  %cmp89 = icmp sge i32 %tij.val2, %add88
  %sel3 = select i1 %cmp89, i32 %tij.val2, i32 %add88
  store i32 %sel3, ptr %tij.ptr, align 4
  br label %if.end151

if.else:                                          ; preds = %if.then65
  %tij.val3 = load i32, ptr %tij.ptr, align 4
  %tip1jm1.ptr2 = getelementptr inbounds i32, ptr %ip1row.ptr, i64 %jm1_64
  %tip1jm1.val2 = load i32, ptr %tip1jm1.ptr2, align 4
  %cmp130 = icmp sge i32 %tij.val3, %tip1jm1.val2
  %sel4 = select i1 %cmp130, i32 %tij.val3, i32 %tip1jm1.val2
  store i32 %sel4, ptr %tij.ptr, align 4
  br label %if.end151

if.end151:                                        ; preds = %if.else, %if.then68, %land.lhs.true, %if.end60
  %k0 = add nsw i32 %i, 1
  %cmp.k0 = icmp slt i32 %k0, %j
  br i1 %cmp.k0, label %for.body156.preheader, label %for.inc195

for.body156.preheader:                           ; preds = %if.end151
  br label %for.body156

for.body156:                                      ; preds = %for.body156, %for.body156.preheader
  %k = phi i32 [ %k0, %for.body156.preheader ], [ %inc, %for.body156 ]
  %tij.cur = load i32, ptr %tij.ptr, align 4
  %k64 = sext i32 %k to i64
  %tik.ptr = getelementptr inbounds i32, ptr %irow.ptr, i64 %k64
  %tik.val = load i32, ptr %tik.ptr, align 4
  %kp1 = add nsw i32 %k, 1
  %kp1_64 = sext i32 %kp1 to i64
  %kp1row.off = mul nsw i64 %kp1_64, %n64
  %kp1row.ptr = getelementptr inbounds i32, ptr %table, i64 %kp1row.off
  %tkp1j.ptr = getelementptr inbounds i32, ptr %kp1row.ptr, i64 %j64
  %tkp1j.val = load i32, ptr %tkp1j.ptr, align 4
  %add170 = add nsw i32 %tik.val, %tkp1j.val
  %cmp171 = icmp sge i32 %tij.cur, %add170
  %sel5 = select i1 %cmp171, i32 %tij.cur, i32 %add170
  store i32 %sel5, ptr %tij.ptr, align 4
  %inc = add nsw i32 %k, 1
  %cmp.k = icmp slt i32 %inc, %j
  br i1 %cmp.k, label %for.body156, label %for.inc195.loopexit

for.inc195.loopexit:                             ; preds = %for.body156
  br label %for.inc195

for.inc195:                                       ; preds = %for.inc195.loopexit, %if.end151
  %inc196 = add nsw i32 %j, 1
  %cmp5 = icmp slt i32 %inc196, %n
  br i1 %cmp5, label %for.cond4, label %for.inc198.loopexit

for.inc198.loopexit:                             ; preds = %for.inc195
  br label %for.inc198

for.inc198:                                       ; preds = %for.inc198.loopexit, %for.cond
  %dec = add nsw i32 %i, -1
  %cmp.i = icmp sge i32 %dec, 0
  br i1 %cmp.i, label %for.cond, label %for.end199.loopexit

for.end199.loopexit:                             ; preds = %for.inc198
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
