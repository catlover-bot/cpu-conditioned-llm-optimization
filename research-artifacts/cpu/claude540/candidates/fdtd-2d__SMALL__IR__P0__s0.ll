; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %cmp.tmax = icmp sgt i32 %tmax, 0
  br i1 %cmp.tmax, label %preheader, label %for.end122

preheader:
  %nx64 = zext i32 %nx to i64
  %ny64 = zext i32 %ny to i64
  %tmax64 = zext i32 %tmax to i64
  %nx.gt1 = icmp sgt i32 %nx, 1
  %ny.gt1 = icmp sgt i32 %ny, 0
  %nxm1 = sub nsw i32 %nx, 1
  %nym1 = sub nsw i32 %ny, 1
  %cmp.i.outer = icmp slt i32 0, %nxm1
  %cmp.j.outer = icmp slt i32 0, %nym1
  br label %t.loop

t.loop:
  %t = phi i64 [0, %preheader], [%t.inc, %t.latch]

  ; ---- loop 1: for j in [0, ny): ey[0][j] = fict[t]
  %fict.ptr = getelementptr inbounds double, ptr %_fict_, i64 %t
  %fictval = load double, ptr %fict.ptr, align 8
  br i1 %ny.gt1, label %l1.body.preheader, label %l1.end

l1.body.preheader:
  br label %l1.body

l1.body:
  %j1 = phi i64 [0, %l1.body.preheader], [%j1.inc, %l1.body]
  %ey0.ptr = getelementptr inbounds double, ptr %ey, i64 %j1
  store double %fictval, ptr %ey0.ptr, align 8
  %j1.inc = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.inc, %ny64
  br i1 %j1.cmp, label %l1.body, label %l1.end

l1.end:
  br i1 %nx.gt1, label %l2.i.preheader, label %l3.i.preheader

l2.i.preheader:
  br label %l2.i

l2.i:
  %i2 = phi i64 [1, %l2.i.preheader], [%i2.inc, %l2.i.latch]
  %i2rowEY = mul nsw i64 %i2, %ny64
  %i2rowHZ = mul nsw i64 %i2, %ny64
  %i2m1 = sub nsw i64 %i2, 1
  %i2m1rowHZ = mul nsw i64 %i2m1, %ny64
  br i1 %ny.gt1, label %l2.j.preheader, label %l2.j.end

l2.j.preheader:
  br label %l2.j

l2.j:
  %j2 = phi i64 [0, %l2.j.preheader], [%j2.inc, %l2.j]
  %ey.idx = add i64 %i2rowEY, %j2
  %ey.ptr = getelementptr inbounds double, ptr %ey, i64 %ey.idx
  %ey.val = load double, ptr %ey.ptr, align 8
  %hz.idx = add i64 %i2rowHZ, %j2
  %hz.ptr = getelementptr inbounds double, ptr %hz, i64 %hz.idx
  %hz.val = load double, ptr %hz.ptr, align 8
  %hzm1.idx = add i64 %i2m1rowHZ, %j2
  %hzm1.ptr = getelementptr inbounds double, ptr %hz, i64 %hzm1.idx
  %hzm1.val = load double, ptr %hzm1.ptr, align 8
  %sub31 = fsub double %hz.val, %hzm1.val
  %mul = fmul double 5.000000e-01, %sub31
  %sub32 = fsub double %ey.val, %mul
  store double %sub32, ptr %ey.ptr, align 8
  %j2.inc = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.inc, %ny64
  br i1 %j2.cmp, label %l2.j, label %l2.j.end

l2.j.end:
  br label %l2.i.latch

l2.i.latch:
  %i2.inc = add nuw nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.inc, %nx64
  br i1 %i2.cmp, label %l2.i, label %l3.i.preheader

l3.i.preheader:
  br label %l3.i

l3.i:
  %i3 = phi i64 [0, %l3.i.preheader], [%i3.inc, %l3.i.latch]
  %i3rowEX = mul nsw i64 %i3, %ny64
  %i3rowHZ = mul nsw i64 %i3, %ny64
  br i1 %ny.gt1, label %l3.j.preheader, label %l3.j.end

l3.j.preheader:
  br label %l3.j

l3.j:
  %j3 = phi i64 [1, %l3.j.preheader], [%j3.inc, %l3.j]
  %ex.idx = add i64 %i3rowEX, %j3
  %ex.ptr = getelementptr inbounds double, ptr %ex, i64 %ex.idx
  %ex.val = load double, ptr %ex.ptr, align 8
  %hz.idx3 = add i64 %i3rowHZ, %j3
  %hz.ptr3 = getelementptr inbounds double, ptr %hz, i64 %hz.idx3
  %hz.val3 = load double, ptr %hz.ptr3, align 8
  %j3m1 = sub nsw i64 %j3, 1
  %hzm1.idx3 = add i64 %i3rowHZ, %j3m1
  %hzm1.ptr3 = getelementptr inbounds double, ptr %hz, i64 %hzm1.idx3
  %hzm1.val3 = load double, ptr %hzm1.ptr3, align 8
  %sub62 = fsub double %hz.val3, %hzm1.val3
  %mul63 = fmul double 5.000000e-01, %sub62
  %sub64 = fsub double %ex.val, %mul63
  store double %sub64, ptr %ex.ptr, align 8
  %j3.inc = add nuw nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.inc, %ny64
  br i1 %j3.cmp, label %l3.j, label %l3.j.end

l3.j.end:
  br label %l3.i.latch

l3.i.latch:
  %i3.inc = add nuw nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.inc, %nx64
  br i1 %i3.cmp, label %l3.i, label %l4.i.preheader

l4.i.preheader:
  br i1 %cmp.i.outer, label %l4.i.preheader2, label %t.latch

l4.i.preheader2:
  %nxm1.64 = zext i32 %nxm1 to i64
  %nym1.64 = zext i32 %nym1 to i64
  br label %l4.i

l4.i:
  %i4 = phi i64 [0, %l4.i.preheader2], [%i4.inc, %l4.i.latch]
  %i4rowHZ = mul nsw i64 %i4, %ny64
  %i4rowEX = mul nsw i64 %i4, %ny64
  %i4p1 = add nsw i64 %i4, 1
  %i4p1rowEY = mul nsw i64 %i4p1, %ny64
  %i4rowEY = mul nsw i64 %i4, %ny64
  br i1 %cmp.j.outer, label %l4.j.preheader, label %l4.j.end

l4.j.preheader:
  br label %l4.j

l4.j:
  %j4 = phi i64 [0, %l4.j.preheader], [%j4.inc, %l4.j]
  %hz.idx4 = add i64 %i4rowHZ, %j4
  %hz.ptr4 = getelementptr inbounds double, ptr %hz, i64 %hz.idx4
  %hz.val4 = load double, ptr %hz.ptr4, align 8
  %j4p1 = add nsw i64 %j4, 1
  %ex.idx4a = add i64 %i4rowEX, %j4p1
  %ex.ptr4a = getelementptr inbounds double, ptr %ex, i64 %ex.idx4a
  %ex.val4a = load double, ptr %ex.ptr4a, align 8
  %ex.idx4b = add i64 %i4rowEX, %j4
  %ex.ptr4b = getelementptr inbounds double, ptr %ex, i64 %ex.idx4b
  %ex.val4b = load double, ptr %ex.ptr4b, align 8
  %sub96 = fsub double %ex.val4a, %ex.val4b
  %ey.idx4a = add i64 %i4p1rowEY, %j4
  %ey.ptr4a = getelementptr inbounds double, ptr %ey, i64 %ey.idx4a
  %ey.val4a = load double, ptr %ey.ptr4a, align 8
  %add102 = fadd double %sub96, %ey.val4a
  %ey.idx4b = add i64 %i4rowEY, %j4
  %ey.ptr4b = getelementptr inbounds double, ptr %ey, i64 %ey.idx4b
  %ey.val4b = load double, ptr %ey.ptr4b, align 8
  %sub107 = fsub double %add102, %ey.val4b
  %mul108 = fmul double 0x3FE6666666666666, %sub107
  %sub109 = fsub double %hz.val4, %mul108
  store double %sub109, ptr %hz.ptr4, align 8
  %j4.inc = add nuw nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.inc, %nym1.64
  br i1 %j4.cmp, label %l4.j, label %l4.j.end

l4.j.end:
  br label %l4.i.latch

l4.i.latch:
  %i4.inc = add nuw nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.inc, %nxm1.64
  br i1 %i4.cmp, label %l4.i, label %t.latch

t.latch:
  %t.inc = add nuw nsw i64 %t, 1
  %t.cmp = icmp slt i64 %t.inc, %tmax64
  br i1 %t.cmp, label %t.loop, label %for.end122

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
