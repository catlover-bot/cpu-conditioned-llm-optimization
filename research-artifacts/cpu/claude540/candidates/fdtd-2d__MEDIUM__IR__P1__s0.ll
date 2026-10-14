; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %cmp_t = icmp slt i32 0, %tmax
  br i1 %cmp_t, label %preheader, label %for.end122

preheader:
  %ny64 = sext i32 %ny to i64
  %nx64 = sext i32 %nx to i64
  %nx.sub1 = add nsw i32 %nx, -1
  %ny.sub1 = add nsw i32 %ny, -1
  %cmp.j.pos = icmp sgt i32 %ny, 0
  %cmp.i1.pos = icmp sgt i32 %nx, 1
  %cmp.i0.pos = icmp sgt i32 %nx, 0
  %cmp.j1.pos = icmp sgt i32 %ny, 1
  %cmp.i2.pos = icmp slt i32 0, %nx.sub1
  %cmp.j2.pos = icmp slt i32 0, %ny.sub1
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc121, %for.inc120 ]

  ; ---- loop 1: ey[0][j] = _fict_[t] ----
  br i1 %cmp.j.pos, label %loop1.body, label %loop1.end

loop1.body:
  %fict.idx = sext i32 %t to i64
  %fict.ptr = getelementptr inbounds double, ptr %_fict_, i64 %fict.idx
  %fict.val = load double, ptr %fict.ptr, align 8
  br label %loop1.inner

loop1.inner:
  %j1 = phi i64 [ 0, %loop1.body ], [ %j1.next, %loop1.inner ]
  %ey.row0.ptr = getelementptr inbounds double, ptr %ey, i64 %j1
  store double %fict.val, ptr %ey.row0.ptr, align 8
  %j1.next = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %ny64
  br i1 %j1.cmp, label %loop1.inner, label %loop1.end

loop1.end:
  br i1 %cmp.i1.pos, label %loop2.outer.preheader, label %for.end42

loop2.outer.preheader:
  br label %loop2.outer

loop2.outer:                                      ; preds = %loop2.outer.preheader, %loop2.outer.latch
  %i2 = phi i64 [ 1, %loop2.outer.preheader ], [ %i2.next, %loop2.outer.latch ]
  %i2.32 = trunc i64 %i2 to i32
  %ey.row.off = mul nsw i64 %i2, %ny64
  %ey.row.ptr = getelementptr inbounds double, ptr %ey, i64 %ey.row.off
  %hz.row.ptr = getelementptr inbounds double, ptr %hz, i64 %ey.row.off
  %i2.sub1 = add nsw i64 %i2, -1
  %hz.rowm1.off = mul nsw i64 %i2.sub1, %ny64
  %hz.rowm1.ptr = getelementptr inbounds double, ptr %hz, i64 %hz.rowm1.off
  br i1 %cmp.j.pos, label %loop2.inner, label %loop2.outer.latch

loop2.inner:                                      ; preds = %loop2.outer, %loop2.inner
  %j2 = phi i64 [ 0, %loop2.outer ], [ %j2.next, %loop2.inner ]
  %ey.elem.ptr = getelementptr inbounds double, ptr %ey.row.ptr, i64 %j2
  %ey.val = load double, ptr %ey.elem.ptr, align 8
  %hz.elem.ptr = getelementptr inbounds double, ptr %hz.row.ptr, i64 %j2
  %hz.val = load double, ptr %hz.elem.ptr, align 8
  %hzm1.elem.ptr = getelementptr inbounds double, ptr %hz.rowm1.ptr, i64 %j2
  %hzm1.val = load double, ptr %hzm1.elem.ptr, align 8
  %sub31 = fsub double %hz.val, %hzm1.val
  %mul = fmul double 5.000000e-01, %sub31
  %sub32 = fsub double %ey.val, %mul
  store double %sub32, ptr %ey.elem.ptr, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %ny64
  br i1 %j2.cmp, label %loop2.inner, label %loop2.outer.latch

loop2.outer.latch:
  %i2.next = add nsw i64 %i2, 1
  %i2.next.32 = trunc i64 %i2.next to i32
  %i2.cmp = icmp slt i32 %i2.next.32, %nx
  br i1 %i2.cmp, label %loop2.outer, label %for.end42

for.end42:                                        ; preds = %loop2.outer.latch, %loop1.end
  br i1 %cmp.i0.pos, label %loop3.outer.preheader, label %for.end74

loop3.outer.preheader:
  br label %loop3.outer

loop3.outer:                                      ; preds = %loop3.outer.preheader, %loop3.outer.latch
  %i3 = phi i64 [ 0, %loop3.outer.preheader ], [ %i3.next, %loop3.outer.latch ]
  %ex.row.off = mul nsw i64 %i3, %ny64
  %ex.row.ptr = getelementptr inbounds double, ptr %ex, i64 %ex.row.off
  %hz.row3.off = mul nsw i64 %i3, %ny64
  %hz.row3.ptr = getelementptr inbounds double, ptr %hz, i64 %hz.row3.off
  br i1 %cmp.j1.pos, label %loop3.inner, label %loop3.outer.latch

loop3.inner:                                      ; preds = %loop3.outer, %loop3.inner
  %j3 = phi i64 [ 1, %loop3.outer ], [ %j3.next, %loop3.inner ]
  %ex.elem.ptr = getelementptr inbounds double, ptr %ex.row.ptr, i64 %j3
  %ex.val = load double, ptr %ex.elem.ptr, align 8
  %hz.elem3.ptr = getelementptr inbounds double, ptr %hz.row3.ptr, i64 %j3
  %hz.val3 = load double, ptr %hz.elem3.ptr, align 8
  %j3.sub1 = add nsw i64 %j3, -1
  %hzm1.elem3.ptr = getelementptr inbounds double, ptr %hz.row3.ptr, i64 %j3.sub1
  %hzm1.val3 = load double, ptr %hzm1.elem3.ptr, align 8
  %sub62 = fsub double %hz.val3, %hzm1.val3
  %mul63 = fmul double 5.000000e-01, %sub62
  %sub64 = fsub double %ex.val, %mul63
  store double %sub64, ptr %ex.elem.ptr, align 8
  %j3.next = add nuw nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.next, %ny64
  br i1 %j3.cmp, label %loop3.inner, label %loop3.outer.latch

loop3.outer.latch:
  %i3.next = add nsw i64 %i3, 1
  %i3.next.32 = trunc i64 %i3.next to i32
  %i3.cmp = icmp slt i32 %i3.next.32, %nx
  br i1 %i3.cmp, label %loop3.outer, label %for.end74

for.end74:                                        ; preds = %loop3.outer.latch, %for.end42
  br i1 %cmp.i2.pos, label %loop4.outer.preheader, label %for.end119

loop4.outer.preheader:
  br label %loop4.outer

loop4.outer:                                      ; preds = %loop4.outer.preheader, %loop4.outer.latch
  %i4 = phi i64 [ 0, %loop4.outer.preheader ], [ %i4.next, %loop4.outer.latch ]
  %hz.row4.off = mul nsw i64 %i4, %ny64
  %hz.row4.ptr = getelementptr inbounds double, ptr %hz, i64 %hz.row4.off
  %ex.row4.off = mul nsw i64 %i4, %ny64
  %ex.row4.ptr = getelementptr inbounds double, ptr %ex, i64 %ex.row4.off
  %i4.add1 = add nsw i64 %i4, 1
  %ey.row4p1.off = mul nsw i64 %i4.add1, %ny64
  %ey.row4p1.ptr = getelementptr inbounds double, ptr %ey, i64 %ey.row4p1.off
  %ey.row4.off = mul nsw i64 %i4, %ny64
  %ey.row4.ptr = getelementptr inbounds double, ptr %ey, i64 %ey.row4.off
  br i1 %cmp.j2.pos, label %loop4.inner, label %loop4.outer.latch

loop4.inner:                                      ; preds = %loop4.outer, %loop4.inner
  %j4 = phi i64 [ 0, %loop4.outer ], [ %j4.next, %loop4.inner ]
  %hz.elem4.ptr = getelementptr inbounds double, ptr %hz.row4.ptr, i64 %j4
  %hz.val4 = load double, ptr %hz.elem4.ptr, align 8
  %j4.add1 = add nuw nsw i64 %j4, 1
  %ex.elem4p1.ptr = getelementptr inbounds double, ptr %ex.row4.ptr, i64 %j4.add1
  %ex.val4p1 = load double, ptr %ex.elem4p1.ptr, align 8
  %ex.elem4.ptr = getelementptr inbounds double, ptr %ex.row4.ptr, i64 %j4
  %ex.val4 = load double, ptr %ex.elem4.ptr, align 8
  %sub96 = fsub double %ex.val4p1, %ex.val4
  %ey.elem4p1.ptr = getelementptr inbounds double, ptr %ey.row4p1.ptr, i64 %j4
  %ey.val4p1 = load double, ptr %ey.elem4p1.ptr, align 8
  %add102 = fadd double %sub96, %ey.val4p1
  %ey.elem4.ptr = getelementptr inbounds double, ptr %ey.row4.ptr, i64 %j4
  %ey.val4 = load double, ptr %ey.elem4.ptr, align 8
  %sub107 = fsub double %add102, %ey.val4
  %mul108 = fmul double 0x3FE6666666666666, %sub107
  %sub109 = fsub double %hz.val4, %mul108
  store double %sub109, ptr %hz.elem4.ptr, align 8
  %j4.next = add nuw nsw i64 %j4, 1
  %j4.next.32 = trunc i64 %j4.next to i32
  %j4.cmp = icmp slt i32 %j4.next.32, %ny.sub1
  br i1 %j4.cmp, label %loop4.inner, label %loop4.outer.latch

loop4.outer.latch:
  %i4.next = add nsw i64 %i4, 1
  %i4.next.32 = trunc i64 %i4.next to i32
  %i4.cmp = icmp slt i32 %i4.next.32, %nx.sub1
  br i1 %i4.cmp, label %loop4.outer, label %for.end119

for.end119:                                       ; preds = %loop4.outer.latch, %for.end74
  br label %for.inc120

for.inc120:
  %inc121 = add nsw i32 %t, 1
  %cmp.t.next = icmp slt i32 %inc121, %tmax
  br i1 %cmp.t.next, label %for.cond, label %for.end122.loopexit

for.end122.loopexit:
  br label %for.end122

for.end122:                                       ; preds = %for.end122.loopexit, %entry
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
