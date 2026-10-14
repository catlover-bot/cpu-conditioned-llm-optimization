; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_fdtd_2d(i32 noundef %tmax, i32 noundef %nx, i32 noundef %ny, ptr noundef %ex, ptr noundef %ey, ptr noundef %hz, ptr noundef %_fict_) #0 {
entry:
  %cmp.nx = icmp sgt i32 %nx, 0
  %cmp.ny = icmp sgt i32 %ny, 0
  %cmp.tmax = icmp sgt i32 %tmax, 0
  %and1 = and i1 %cmp.nx, %cmp.ny
  %and2 = and i1 %and1, %cmp.tmax
  br i1 %and2, label %preheader, label %for.end122

preheader:
  %nx64 = zext i32 %nx to i64
  %ny64 = zext i32 %ny to i64
  %tmax64 = zext i32 %tmax to i64
  %nxm1 = add nsw i32 %nx, -1
  %nym1 = add nsw i32 %ny, -1
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i64 [ 0, %preheader ], [ %inc121, %for.inc120 ]

  ; ---- loop 1: ey[0][j] = fict[t] ----
  %fictptr = getelementptr inbounds double, ptr %_fict_, i64 %t
  %fictval = load double, ptr %fictptr, align 8
  br label %loop1

loop1:
  %j1 = phi i64 [ 0, %for.cond ], [ %j1.next, %loop1 ]
  %ey0ptr = getelementptr inbounds double, ptr %ey, i64 %j1
  store double %fictval, ptr %ey0ptr, align 8
  %j1.next = add nuw nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %ny64
  br i1 %j1.cmp, label %loop1, label %after.loop1

after.loop1:
  ; ---- loop2: for i=1..nx-1, for j=0..ny-1: ey[i][j] -= 0.5*(hz[i][j]-hz[i-1][j]) ----
  %nx.gt1 = icmp sgt i32 %nx, 1
  br i1 %nx.gt1, label %loop2.i.preheader, label %after.loop2

loop2.i.preheader:
  br label %loop2.i

loop2.i:
  %i2 = phi i64 [ 1, %loop2.i.preheader ], [ %i2.next, %loop2.i.latch ]
  %i2m1 = add nsw i64 %i2, -1
  %eyrow2 = mul nsw i64 %i2, %ny64
  %eyrowbase2 = getelementptr inbounds double, ptr %ey, i64 %eyrow2
  %hzrow2 = mul nsw i64 %i2, %ny64
  %hzrowbase2 = getelementptr inbounds double, ptr %hz, i64 %hzrow2
  %hzprow2 = mul nsw i64 %i2m1, %ny64
  %hzprowbase2 = getelementptr inbounds double, ptr %hz, i64 %hzprow2
  br label %loop2.j

loop2.j:
  %j2 = phi i64 [ 0, %loop2.i ], [ %j2.next, %loop2.j ]
  %eyptr2 = getelementptr inbounds double, ptr %eyrowbase2, i64 %j2
  %eyval2 = load double, ptr %eyptr2, align 8
  %hzptr2 = getelementptr inbounds double, ptr %hzrowbase2, i64 %j2
  %hzval2 = load double, ptr %hzptr2, align 8
  %hzpptr2 = getelementptr inbounds double, ptr %hzprowbase2, i64 %j2
  %hzpval2 = load double, ptr %hzpptr2, align 8
  %sub2 = fsub double %hzval2, %hzpval2
  %mul2 = fmul double 5.000000e-01, %sub2
  %res2 = fsub double %eyval2, %mul2
  store double %res2, ptr %eyptr2, align 8
  %j2.next = add nuw nsw i64 %j2, 1
  %j2.cmp = icmp slt i64 %j2.next, %ny64
  br i1 %j2.cmp, label %loop2.j, label %loop2.i.latch

loop2.i.latch:
  %i2.next = add nuw nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.next, %nx64
  br i1 %i2.cmp, label %loop2.i, label %after.loop2

after.loop2:
  ; ---- loop3: for i=0..nx-1, for j=1..ny-1: ex[i][j] -= 0.5*(hz[i][j]-hz[i][j-1]) ----
  %ny.gt1 = icmp sgt i32 %ny, 1
  br i1 %ny.gt1, label %loop3.i.preheader, label %after.loop3

loop3.i.preheader:
  br label %loop3.i

loop3.i:
  %i3 = phi i64 [ 0, %loop3.i.preheader ], [ %i3.next, %loop3.i.latch ]
  %exrow3 = mul nsw i64 %i3, %ny64
  %exrowbase3 = getelementptr inbounds double, ptr %ex, i64 %exrow3
  %hzrow3 = mul nsw i64 %i3, %ny64
  %hzrowbase3 = getelementptr inbounds double, ptr %hz, i64 %hzrow3
  br label %loop3.j

loop3.j:
  %j3 = phi i64 [ 1, %loop3.i ], [ %j3.next, %loop3.j ]
  %j3m1 = add nsw i64 %j3, -1
  %exptr3 = getelementptr inbounds double, ptr %exrowbase3, i64 %j3
  %exval3 = load double, ptr %exptr3, align 8
  %hzptr3 = getelementptr inbounds double, ptr %hzrowbase3, i64 %j3
  %hzval3 = load double, ptr %hzptr3, align 8
  %hzpptr3 = getelementptr inbounds double, ptr %hzrowbase3, i64 %j3m1
  %hzpval3 = load double, ptr %hzpptr3, align 8
  %sub3 = fsub double %hzval3, %hzpval3
  %mul3 = fmul double 5.000000e-01, %sub3
  %res3 = fsub double %exval3, %mul3
  store double %res3, ptr %exptr3, align 8
  %j3.next = add nuw nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.next, %ny64
  br i1 %j3.cmp, label %loop3.j, label %loop3.i.latch

loop3.i.latch:
  %i3.next = add nuw nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.next, %nx64
  br i1 %i3.cmp, label %loop3.i, label %after.loop3

after.loop3:
  ; ---- loop4: for i=0..nx-2, for j=0..ny-2: hz update ----
  %nxm1.gt0 = icmp sgt i32 %nxm1, 0
  %nym1.gt0 = icmp sgt i32 %nym1, 0
  %cond4 = and i1 %nxm1.gt0, %nym1.gt0
  br i1 %cond4, label %loop4.i.preheader, label %for.inc120

loop4.i.preheader:
  %nxm1.64 = zext i32 %nxm1 to i64
  %nym1.64 = zext i32 %nym1 to i64
  br label %loop4.i

loop4.i:
  %i4 = phi i64 [ 0, %loop4.i.preheader ], [ %i4.next, %loop4.i.latch ]
  %i4p1 = add nuw nsw i64 %i4, 1
  %hzrow4 = mul nsw i64 %i4, %ny64
  %hzrowbase4 = getelementptr inbounds double, ptr %hz, i64 %hzrow4
  %exrow4 = mul nsw i64 %i4, %ny64
  %exrowbase4 = getelementptr inbounds double, ptr %ex, i64 %exrow4
  %eyrow4 = mul nsw i64 %i4, %ny64
  %eyrowbase4 = getelementptr inbounds double, ptr %ey, i64 %eyrow4
  %eyrow4p1 = mul nsw i64 %i4p1, %ny64
  %eyrowbase4p1 = getelementptr inbounds double, ptr %ey, i64 %eyrow4p1
  br label %loop4.j

loop4.j:
  %j4 = phi i64 [ 0, %loop4.i ], [ %j4.next, %loop4.j ]
  %j4p1 = add nuw nsw i64 %j4, 1
  %hzptr4 = getelementptr inbounds double, ptr %hzrowbase4, i64 %j4
  %hzval4 = load double, ptr %hzptr4, align 8
  %exptr4_jp1 = getelementptr inbounds double, ptr %exrowbase4, i64 %j4p1
  %exval4_jp1 = load double, ptr %exptr4_jp1, align 8
  %exptr4_j = getelementptr inbounds double, ptr %exrowbase4, i64 %j4
  %exval4_j = load double, ptr %exptr4_j, align 8
  %subex4 = fsub double %exval4_jp1, %exval4_j
  %eyptr4_ip1 = getelementptr inbounds double, ptr %eyrowbase4p1, i64 %j4
  %eyval4_ip1 = load double, ptr %eyptr4_ip1, align 8
  %addey4 = fadd double %subex4, %eyval4_ip1
  %eyptr4_i = getelementptr inbounds double, ptr %eyrowbase4, i64 %j4
  %eyval4_i = load double, ptr %eyptr4_i, align 8
  %subey4 = fsub double %addey4, %eyval4_i
  %mul4 = fmul double 0x3FE6666666666666, %subey4
  %res4 = fsub double %hzval4, %mul4
  store double %res4, ptr %hzptr4, align 8
  %j4.next = add nuw nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.next, %nym1.64
  br i1 %j4.cmp, label %loop4.j, label %loop4.i.latch

loop4.i.latch:
  %i4.next = add nuw nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.next, %nxm1.64
  br i1 %i4.cmp, label %loop4.i, label %for.inc120

for.inc120:
  %inc121 = add nuw nsw i64 %t, 1
  %t.cmp = icmp slt i64 %inc121, %tmax64
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
