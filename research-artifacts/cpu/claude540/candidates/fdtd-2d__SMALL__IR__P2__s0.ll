; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %cmp.tmax = icmp slt i32 0, %tmax
  br i1 %cmp.tmax, label %preheader, label %for.end122

preheader:
  %ny64 = sext i32 %ny to i64
  %nx64 = sext i32 %nx to i64
  %nxm1 = add nsw i32 %nx, -1
  %nym1 = add nsw i32 %ny, -1
  %cmp.j0 = icmp slt i32 0, %ny
  %cmp.i1 = icmp slt i32 1, %nx
  %cmp.j1 = icmp slt i32 1, %ny
  %cmp.i0b = icmp slt i32 0, %nx
  %cmp.i0c = icmp slt i32 0, %nxm1
  %cmp.j0c = icmp slt i32 0, %nym1
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc121, %for.inc120 ]

  ; ---- loop 1: ey[0][j] = fict[t] ----
  br i1 %cmp.j0, label %l1.body, label %l1.end

l1.body:
  %fict.arrayidx = getelementptr inbounds double, ptr %_fict_, i64 0
  %t64 = sext i32 %t to i64
  %fict.gep = getelementptr inbounds double, ptr %_fict_, i64 %t64
  %fictval = load double, ptr %fict.gep, align 8
  br label %l1.loop

l1.loop:
  %j1v = phi i64 [ 0, %l1.body ], [ %j1v.next, %l1.loop ]
  %ey.row0 = getelementptr inbounds double, ptr %ey, i64 0
  %ey.elem0 = getelementptr inbounds double, ptr %ey.row0, i64 %j1v
  store double %fictval, ptr %ey.elem0, align 8
  %j1v.next = add nsw i64 %j1v, 1
  %j1v.cmp = icmp slt i64 %j1v.next, %ny64
  br i1 %j1v.cmp, label %l1.loop, label %l1.end

l1.end:
  br i1 %cmp.i1, label %l2.outer.preheader, label %for.end42

l2.outer.preheader:
  br label %l2.outer

l2.outer:                                         ; i from 1 to nx-1
  %iv2 = phi i64 [ 1, %l2.outer.preheader ], [ %iv2.next, %l2.outer.latch ]
  br i1 %cmp.j0, label %l2.inner, label %l2.outer.latch

l2.inner:
  %j2v = phi i64 [ 0, %l2.outer ], [ %j2v.next, %l2.inner ]
  %ey.rowoff = mul nsw i64 %iv2, %ny64
  %ey.row = getelementptr inbounds double, ptr %ey, i64 %ey.rowoff
  %ey.elem = getelementptr inbounds double, ptr %ey.row, i64 %j2v
  %ey.val = load double, ptr %ey.elem, align 8

  %hz.rowoff = mul nsw i64 %iv2, %ny64
  %hz.row = getelementptr inbounds double, ptr %hz, i64 %hz.rowoff
  %hz.elem = getelementptr inbounds double, ptr %hz.row, i64 %j2v
  %hz.val = load double, ptr %hz.elem, align 8

  %im1 = add nsw i64 %iv2, -1
  %hzm1.rowoff = mul nsw i64 %im1, %ny64
  %hzm1.row = getelementptr inbounds double, ptr %hz, i64 %hzm1.rowoff
  %hzm1.elem = getelementptr inbounds double, ptr %hzm1.row, i64 %j2v
  %hzm1.val = load double, ptr %hzm1.elem, align 8

  %sub31.v = fsub double %hz.val, %hzm1.val
  %mul.v = fmul double 5.000000e-01, %sub31.v
  %sub32.v = fsub double %ey.val, %mul.v
  store double %sub32.v, ptr %ey.elem, align 8

  %j2v.next = add nsw i64 %j2v, 1
  %j2v.cmp = icmp slt i64 %j2v.next, %ny64
  br i1 %j2v.cmp, label %l2.inner, label %l2.outer.latch

l2.outer.latch:
  %iv2.next = add nsw i64 %iv2, 1
  %iv2.cmp = icmp slt i64 %iv2.next, %nx64
  br i1 %iv2.cmp, label %l2.outer, label %for.end42

for.end42:
  br i1 %cmp.i0b, label %l3.outer, label %for.end74

l3.outer:                                         ; i from 0 to nx-1
  %iv3 = phi i64 [ 0, %for.end42 ], [ %iv3.next, %l3.outer.latch ]
  br i1 %cmp.j1, label %l3.inner, label %l3.outer.latch

l3.inner:
  %j3v = phi i64 [ 1, %l3.outer ], [ %j3v.next, %l3.inner ]
  %ex.rowoff = mul nsw i64 %iv3, %ny64
  %ex.row = getelementptr inbounds double, ptr %ex, i64 %ex.rowoff
  %ex.elem = getelementptr inbounds double, ptr %ex.row, i64 %j3v
  %ex.val = load double, ptr %ex.elem, align 8

  %hz3.rowoff = mul nsw i64 %iv3, %ny64
  %hz3.row = getelementptr inbounds double, ptr %hz, i64 %hz3.rowoff
  %hz3.elem = getelementptr inbounds double, ptr %hz3.row, i64 %j3v
  %hz3.val = load double, ptr %hz3.elem, align 8

  %jm1 = add nsw i64 %j3v, -1
  %hz3m1.elem = getelementptr inbounds double, ptr %hz3.row, i64 %jm1
  %hz3m1.val = load double, ptr %hz3m1.elem, align 8

  %sub62.v = fsub double %hz3.val, %hz3m1.val
  %mul63.v = fmul double 5.000000e-01, %sub62.v
  %sub64.v = fsub double %ex.val, %mul63.v
  store double %sub64.v, ptr %ex.elem, align 8

  %j3v.next = add nsw i64 %j3v, 1
  %j3v.cmp = icmp slt i64 %j3v.next, %ny64
  br i1 %j3v.cmp, label %l3.inner, label %l3.outer.latch

l3.outer.latch:
  %iv3.next = add nsw i64 %iv3, 1
  %iv3.cmp = icmp slt i64 %iv3.next, %nx64
  br i1 %iv3.cmp, label %l3.outer, label %for.end74

for.end74:
  br i1 %cmp.i0c, label %l4.outer, label %for.end119

l4.outer:                                         ; i from 0 to nx-2
  %iv4 = phi i64 [ 0, %for.end74 ], [ %iv4.next, %l4.outer.latch ]
  br i1 %cmp.j0c, label %l4.inner, label %l4.outer.latch

l4.inner:
  %j4v = phi i64 [ 0, %l4.outer ], [ %j4v.next, %l4.inner ]
  %hz4.rowoff = mul nsw i64 %iv4, %ny64
  %hz4.row = getelementptr inbounds double, ptr %hz, i64 %hz4.rowoff
  %hz4.elem = getelementptr inbounds double, ptr %hz4.row, i64 %j4v
  %hz4.val = load double, ptr %hz4.elem, align 8

  %ex4.rowoff = mul nsw i64 %iv4, %ny64
  %ex4.row = getelementptr inbounds double, ptr %ex, i64 %ex4.rowoff
  %jp1 = add nsw i64 %j4v, 1
  %ex4.elem.jp1 = getelementptr inbounds double, ptr %ex4.row, i64 %jp1
  %ex4.val.jp1 = load double, ptr %ex4.elem.jp1, align 8

  %ex4.elem.j = getelementptr inbounds double, ptr %ex4.row, i64 %j4v
  %ex4.val.j = load double, ptr %ex4.elem.j, align 8

  %sub96.v = fsub double %ex4.val.jp1, %ex4.val.j

  %ip1 = add nsw i64 %iv4, 1
  %ey4p.rowoff = mul nsw i64 %ip1, %ny64
  %ey4p.row = getelementptr inbounds double, ptr %ey, i64 %ey4p.rowoff
  %ey4p.elem = getelementptr inbounds double, ptr %ey4p.row, i64 %j4v
  %ey4p.val = load double, ptr %ey4p.elem, align 8

  %add102.v = fadd double %sub96.v, %ey4p.val

  %ey4.rowoff = mul nsw i64 %iv4, %ny64
  %ey4.row = getelementptr inbounds double, ptr %ey, i64 %ey4.rowoff
  %ey4.elem = getelementptr inbounds double, ptr %ey4.row, i64 %j4v
  %ey4.val = load double, ptr %ey4.elem, align 8

  %sub107.v = fsub double %add102.v, %ey4.val
  %mul108.v = fmul double 0x3FE6666666666666, %sub107.v
  %sub109.v = fsub double %hz4.val, %mul108.v
  store double %sub109.v, ptr %hz4.elem, align 8

  %j4v.next = add nsw i64 %j4v, 1
  %j4v.cmp = icmp slt i64 %j4v.next, %nym1
  br i1 %j4v.cmp, label %l4.inner, label %l4.outer.latch

l4.outer.latch:
  %iv4.next = add nsw i64 %iv4, 1
  %iv4.cmp = icmp slt i64 %iv4.next, %nxm1
  br i1 %iv4.cmp, label %l4.outer, label %for.end119

for.end119:
  br label %for.inc120

for.inc120:
  %inc121 = add nsw i32 %t, 1
  %cmp.next = icmp slt i32 %inc121, %tmax
  br i1 %cmp.next, label %for.cond, label %for.end122

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
