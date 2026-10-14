; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %nx.pos = icmp sgt i32 %nx, 0
  %ny.pos = icmp sgt i32 %ny, 0
  %tmax.pos = icmp sgt i32 %tmax, 0
  %nx64 = zext i32 %nx to i64
  %ny64 = zext i32 %ny to i64
  %nxm1 = sub nsw i32 %nx, 1
  %nym1 = sub nsw i32 %ny, 1
  %nxm1.pos = icmp sgt i32 %nxm1, 0
  %nym1.pos = icmp sgt i32 %nym1, 0
  %and1 = and i1 %tmax.pos, %ny.pos
  br i1 %and1, label %tloop.preheader, label %for.end122

tloop.preheader:
  br label %for.cond

for.cond:
  %t = phi i32 [ 0, %tloop.preheader ], [ %inc121, %for.inc120 ]
  %arrayidx = getelementptr inbounds double, ptr %_fict_, i64 0
  ; placeholder to keep index calc pattern minimal; actual load below
  br label %loop1

loop1:
  %tidx = sext i32 %t to i64
  %fict.gep = getelementptr inbounds double, ptr %_fict_, i64 %tidx
  %fict.val = load double, ptr %fict.gep, align 8
  br label %loop1.body
loop1.body:
  br label %j1.loop

j1.loop:
  %j1 = phi i32 [ 0, %loop1.body ], [ %j1.inc, %j1.inc.bb ]
  %ey.row0 = getelementptr inbounds double, ptr %ey, i64 0
  %j1.64 = sext i32 %j1 to i64
  %ey.elem0 = getelementptr inbounds double, ptr %ey.row0, i64 %j1.64
  store double %fict.val, ptr %ey.elem0, align 8
  br label %j1.inc.bb
j1.inc.bb:
  %j1.inc = add nsw i32 %j1, 1
  %j1.cmp = icmp slt i32 %j1.inc, %ny
  br i1 %j1.cmp, label %j1.loop, label %loop1.end

loop1.end:
  br i1 %nx.pos, label %i2.preheader, label %loop2.end

i2.preheader:
  br label %i2.loop

i2.loop:
  %i2 = phi i32 [ 1, %i2.preheader ], [ %i2.inc, %i2.inc.bb ]
  %i2.in.range = icmp slt i32 %i2, %nx
  br i1 %i2.in.range, label %i2.body.check, label %loop2.end

i2.body.check:
  br i1 %ny.pos, label %j2.preheader, label %i2.inc.bb

j2.preheader:
  %i2.64 = sext i32 %i2 to i64
  %i2m1.64 = sub nsw i64 %i2.64, 1
  %ey.row.i2 = mul nsw i64 %i2.64, %ny64
  %ey.rowptr.i2 = getelementptr inbounds double, ptr %ey, i64 %ey.row.i2
  %hz.row.i2 = mul nsw i64 %i2.64, %ny64
  %hz.rowptr.i2 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i2
  %hz.row.i2m1 = mul nsw i64 %i2m1.64, %ny64
  %hz.rowptr.i2m1 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i2m1
  br label %j2.loop

j2.loop:
  %j2 = phi i32 [ 0, %j2.preheader ], [ %j2.inc, %j2.inc.bb ]
  %j2.64 = sext i32 %j2 to i64
  %ey.elem = getelementptr inbounds double, ptr %ey.rowptr.i2, i64 %j2.64
  %ey.val = load double, ptr %ey.elem, align 8
  %hz.elem = getelementptr inbounds double, ptr %hz.rowptr.i2, i64 %j2.64
  %hz.val = load double, ptr %hz.elem, align 8
  %hz.elem.prev = getelementptr inbounds double, ptr %hz.rowptr.i2m1, i64 %j2.64
  %hz.val.prev = load double, ptr %hz.elem.prev, align 8
  %sub31 = fsub double %hz.val, %hz.val.prev
  %mul = fmul double 5.000000e-01, %sub31
  %sub32 = fsub double %ey.val, %mul
  store double %sub32, ptr %ey.elem, align 8
  br label %j2.inc.bb
j2.inc.bb:
  %j2.inc = add nsw i32 %j2, 1
  %j2.cmp = icmp slt i32 %j2.inc, %ny
  br i1 %j2.cmp, label %j2.loop, label %i2.inc.bb

i2.inc.bb:
  %i2.inc = add nsw i32 %i2, 1
  br label %i2.loop

loop2.end:
  br i1 %nx.pos, label %i3.preheader, label %loop3.end

i3.preheader:
  br label %i3.loop

i3.loop:
  %i3 = phi i32 [ 0, %i3.preheader ], [ %i3.inc, %i3.inc.bb ]
  %i3.in.range = icmp slt i32 %i3, %nx
  br i1 %i3.in.range, label %i3.body.check, label %loop3.end

i3.body.check:
  br i1 %nym1.pos, label %j3.preheader, label %i3.inc.bb

j3.preheader:
  %i3.64 = sext i32 %i3 to i64
  %ex.row.i3 = mul nsw i64 %i3.64, %ny64
  %ex.rowptr.i3 = getelementptr inbounds double, ptr %ex, i64 %ex.row.i3
  %hz.row.i3 = mul nsw i64 %i3.64, %ny64
  %hz.rowptr.i3 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i3
  br label %j3.loop

j3.loop:
  %j3 = phi i32 [ 1, %j3.preheader ], [ %j3.inc, %j3.inc.bb ]
  %j3.64 = sext i32 %j3 to i64
  %j3m1.64 = sub nsw i64 %j3.64, 1
  %ex.elem = getelementptr inbounds double, ptr %ex.rowptr.i3, i64 %j3.64
  %ex.val = load double, ptr %ex.elem, align 8
  %hz.elem = getelementptr inbounds double, ptr %hz.rowptr.i3, i64 %j3.64
  %hz.val = load double, ptr %hz.elem, align 8
  %hz.elem.prev = getelementptr inbounds double, ptr %hz.rowptr.i3, i64 %j3m1.64
  %hz.val.prev = load double, ptr %hz.elem.prev, align 8
  %sub62 = fsub double %hz.val, %hz.val.prev
  %mul63 = fmul double 5.000000e-01, %sub62
  %sub64 = fsub double %ex.val, %mul63
  store double %sub64, ptr %ex.elem, align 8
  br label %j3.inc.bb
j3.inc.bb:
  %j3.inc = add nsw i32 %j3, 1
  %j3.cmp = icmp slt i32 %j3.inc, %ny
  br i1 %j3.cmp, label %j3.loop, label %i3.inc.bb

i3.inc.bb:
  %i3.inc = add nsw i32 %i3, 1
  br label %i3.loop

loop3.end:
  br i1 %nxm1.pos, label %i4.preheader, label %loop4.end

i4.preheader:
  br label %i4.loop

i4.loop:
  %i4 = phi i32 [ 0, %i4.preheader ], [ %i4.inc, %i4.inc.bb ]
  %i4.in.range = icmp slt i32 %i4, %nxm1
  br i1 %i4.in.range, label %i4.body.check, label %loop4.end

i4.body.check:
  br i1 %nym1.pos, label %j4.preheader, label %i4.inc.bb

j4.preheader:
  %i4.64 = sext i32 %i4 to i64
  %i4p1.64 = add nsw i64 %i4.64, 1
  %hz.row.i4 = mul nsw i64 %i4.64, %ny64
  %hz.rowptr.i4 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i4
  %ex.row.i4 = mul nsw i64 %i4.64, %ny64
  %ex.rowptr.i4 = getelementptr inbounds double, ptr %ex, i64 %ex.row.i4
  %ey.row.i4 = mul nsw i64 %i4.64, %ny64
  %ey.rowptr.i4 = getelementptr inbounds double, ptr %ey, i64 %ey.row.i4
  %ey.row.i4p1 = mul nsw i64 %i4p1.64, %ny64
  %ey.rowptr.i4p1 = getelementptr inbounds double, ptr %ey, i64 %ey.row.i4p1
  br label %j4.loop

j4.loop:
  %j4 = phi i32 [ 0, %j4.preheader ], [ %j4.inc, %j4.inc.bb ]
  %j4.64 = sext i32 %j4 to i64
  %j4p1.64 = add nsw i64 %j4.64, 1
  %hz.elem = getelementptr inbounds double, ptr %hz.rowptr.i4, i64 %j4.64
  %hz.val = load double, ptr %hz.elem, align 8
  %ex.elem.p1 = getelementptr inbounds double, ptr %ex.rowptr.i4, i64 %j4p1.64
  %ex.val.p1 = load double, ptr %ex.elem.p1, align 8
  %ex.elem = getelementptr inbounds double, ptr %ex.rowptr.i4, i64 %j4.64
  %ex.val = load double, ptr %ex.elem, align 8
  %sub96 = fsub double %ex.val.p1, %ex.val
  %ey.elem.p1 = getelementptr inbounds double, ptr %ey.rowptr.i4p1, i64 %j4.64
  %ey.val.p1 = load double, ptr %ey.elem.p1, align 8
  %add102 = fadd double %sub96, %ey.val.p1
  %ey.elem = getelementptr inbounds double, ptr %ey.rowptr.i4, i64 %j4.64
  %ey.val = load double, ptr %ey.elem, align 8
  %sub107 = fsub double %add102, %ey.val
  %mul108 = fmul double 0x3FE6666666666666, %sub107
  %sub109 = fsub double %hz.val, %mul108
  store double %sub109, ptr %hz.elem, align 8
  br label %j4.inc.bb
j4.inc.bb:
  %j4.inc = add nsw i32 %j4, 1
  %j4.cmp = icmp slt i32 %j4.inc, %nym1
  br i1 %j4.cmp, label %j4.loop, label %i4.inc.bb

i4.inc.bb:
  %i4.inc = add nsw i32 %i4, 1
  br label %i4.loop

loop4.end:
  br label %for.inc120

for.inc120:
  %inc121 = add nsw i32 %t, 1
  %t.cmp = icmp slt i32 %inc121, %tmax
  br i1 %t.cmp, label %for.cond, label %for.end122

for.end122:
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
