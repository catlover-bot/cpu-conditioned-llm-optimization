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
  %cmp.ny0 = icmp slt i32 0, %ny
  %cmp.nx1 = icmp slt i32 1, %nx
  %cmp.nx0 = icmp slt i32 0, %nx
  %nxm1 = sub nsw i32 %nx, 1
  %nym1 = sub nsw i32 %ny, 1
  %cmp.nxm1 = icmp slt i32 0, %nxm1
  %cmp.nym1 = icmp slt i32 0, %nym1
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc121, %for.inc120 ]

  ; ----- loop1: ey[0][j] = fict_[t] -----
  br i1 %cmp.ny0, label %loop1.body, label %loop1.end

loop1.body:
  %fict_arrayidx = getelementptr inbounds double, ptr %_fict_, i64 %t
  %fictval = load double, ptr %fict_arrayidx, align 8
  br label %loop1.for

loop1.for:
  %j1 = phi i64 [ 0, %loop1.body ], [ %j1.next, %loop1.for ]
  %ey.idx1 = getelementptr inbounds double, ptr %ey, i64 %j1
  store double %fictval, ptr %ey.idx1, align 8
  %j1.next = add nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %ny64
  br i1 %j1.cmp, label %loop1.for, label %loop1.end

loop1.end:
  br label %loop2.outer.check

  ; ----- loop2: for i=1..nx-1, for j=0..ny-1: ey[i][j] -= 0.5*(hz[i][j]-hz[i-1][j]) -----
loop2.outer.check:
  br i1 %cmp.nx1, label %loop2.outer, label %loop2.outer.end

loop2.outer:
  %i2 = phi i64 [ 1, %loop2.outer.check ], [ %i2.next, %loop2.inner.end ]
  br i1 %cmp.ny0, label %loop2.inner.preheader, label %loop2.inner.end

loop2.inner.preheader:
  %i2m1 = sub nsw i64 %i2, 1
  %ey.row2 = mul nsw i64 %i2, %ny64
  %ey.rowbase2 = getelementptr inbounds double, ptr %ey, i64 %ey.row2
  %hz.row2 = mul nsw i64 %i2, %ny64
  %hz.rowbase2 = getelementptr inbounds double, ptr %hz, i64 %hz.row2
  %hz.rowm1 = mul nsw i64 %i2m1, %ny64
  %hz.rowbasem1 = getelementptr inbounds double, ptr %hz, i64 %hz.rowm1
  br label %loop2.inner

loop2.inner:
  %j2 = phi i64 [ 0, %loop2.inner.preheader ], [ %j2.next, %loop2.inner ]
  %ey.p2 = getelementptr inbounds double, ptr %ey.rowbase2, i64 %j2
  %eyval2 = load double, ptr %ey.p2, align 8
  %hz.p2 = getelementptr inbounds double, ptr %hz.rowbase2, i64 %j2
  %hzval2 = load double, ptr %hz.p2, align 8
  %hz.pm1 = getelementptr inbounds double, ptr %hz.rowbasem1, i64 %j2
  %hzvalm1 = load double, ptr %hz.pm1, align 8
  %sub2 = fsub double %hzval2, %hzvalm1
  %mul2 = fmul double 5.000000e-01, %sub2
  %res2 = fsub double %eyval2, %mul2
  store double %res2, ptr %ey.p2, align 8
  %j2.next = add nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %ny64
  br i1 %j2.cmp, label %loop2.inner, label %loop2.inner.end

loop2.inner.end:
  %i2.next = add nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.next, %nx64
  br i1 %i2.cmp, label %loop2.outer, label %loop2.outer.end

loop2.outer.end:
  br label %loop3.outer.check

  ; ----- loop3: for i=0..nx-1, for j=1..ny-1: ex[i][j] -= 0.5*(hz[i][j]-hz[i][j-1]) -----
loop3.outer.check:
  br i1 %cmp.nx0, label %loop3.outer, label %loop3.outer.end

loop3.outer:
  %i3 = phi i64 [ 0, %loop3.outer.check ], [ %i3.next, %loop3.inner.end ]
  %cmp.ny1 = icmp slt i32 1, %ny
  br i1 %cmp.ny1, label %loop3.inner.preheader, label %loop3.inner.end

loop3.inner.preheader:
  %ex.row3 = mul nsw i64 %i3, %ny64
  %ex.rowbase3 = getelementptr inbounds double, ptr %ex, i64 %ex.row3
  %hz.row3 = mul nsw i64 %i3, %ny64
  %hz.rowbase3 = getelementptr inbounds double, ptr %hz, i64 %hz.row3
  br label %loop3.inner

loop3.inner:
  %j3 = phi i64 [ 1, %loop3.inner.preheader ], [ %j3.next, %loop3.inner ]
  %ex.p3 = getelementptr inbounds double, ptr %ex.rowbase3, i64 %j3
  %exval3 = load double, ptr %ex.p3, align 8
  %hz.p3 = getelementptr inbounds double, ptr %hz.rowbase3, i64 %j3
  %hzval3 = load double, ptr %hz.p3, align 8
  %j3m1 = sub nsw i64 %j3, 1
  %hz.pm1_3 = getelementptr inbounds double, ptr %hz.rowbase3, i64 %j3m1
  %hzvalm1_3 = load double, ptr %hz.pm1_3, align 8
  %sub3 = fsub double %hzval3, %hzvalm1_3
  %mul3 = fmul double 5.000000e-01, %sub3
  %res3 = fsub double %exval3, %mul3
  store double %res3, ptr %ex.p3, align 8
  %j3.next = add nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.next, %ny64
  br i1 %j3.cmp, label %loop3.inner, label %loop3.inner.end

loop3.inner.end:
  %i3.next = add nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.next, %nx64
  br i1 %i3.cmp, label %loop3.outer, label %loop3.outer.end

loop3.outer.end:
  br label %loop4.outer.check

  ; ----- loop4: for i=0..nx-2, for j=0..ny-2: hz update -----
loop4.outer.check:
  br i1 %cmp.nxm1, label %loop4.outer, label %for.end119

loop4.outer:
  %i4 = phi i64 [ 0, %loop4.outer.check ], [ %i4.next, %loop4.inner.end ]
  br i1 %cmp.nym1, label %loop4.inner.preheader, label %loop4.inner.end

loop4.inner.preheader:
  %hz.row4 = mul nsw i64 %i4, %ny64
  %hz.rowbase4 = getelementptr inbounds double, ptr %hz, i64 %hz.row4
  %ex.row4 = mul nsw i64 %i4, %ny64
  %ex.rowbase4 = getelementptr inbounds double, ptr %ex, i64 %ex.row4
  %i4p1 = add nsw i64 %i4, 1
  %ey.row4 = mul nsw i64 %i4, %ny64
  %ey.rowbase4 = getelementptr inbounds double, ptr %ey, i64 %ey.row4
  %ey.row4p1 = mul nsw i64 %i4p1, %ny64
  %ey.rowbase4p1 = getelementptr inbounds double, ptr %ey, i64 %ey.row4p1
  br label %loop4.inner

loop4.inner:
  %j4 = phi i64 [ 0, %loop4.inner.preheader ], [ %j4.next, %loop4.inner ]
  %hz.p4 = getelementptr inbounds double, ptr %hz.rowbase4, i64 %j4
  %hzval4 = load double, ptr %hz.p4, align 8
  %j4p1 = add nsw i64 %j4, 1
  %ex.p4p1 = getelementptr inbounds double, ptr %ex.rowbase4, i64 %j4p1
  %exvalp1 = load double, ptr %ex.p4p1, align 8
  %ex.p4 = getelementptr inbounds double, ptr %ex.rowbase4, i64 %j4
  %exval4 = load double, ptr %ex.p4, align 8
  %sub4a = fsub double %exvalp1, %exval4
  %ey.p4p1row = getelementptr inbounds double, ptr %ey.rowbase4p1, i64 %j4
  %eyval4p1row = load double, ptr %ey.p4p1row, align 8
  %add4 = fadd double %sub4a, %eyval4p1row
  %ey.p4 = getelementptr inbounds double, ptr %ey.rowbase4, i64 %j4
  %eyval4 = load double, ptr %ey.p4, align 8
  %sub4b = fsub double %add4, %eyval4
  %mul4 = fmul double 0x3FE6666666666666, %sub4b
  %res4 = fsub double %hzval4, %mul4
  store double %res4, ptr %hz.p4, align 8
  %j4.next = add nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.next, %nym1
  br i1 %j4.cmp, label %loop4.inner, label %loop4.inner.end

loop4.inner.end:
  %i4.next = add nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.next, %nxm1
  br i1 %i4.cmp, label %loop4.outer, label %for.end119

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
