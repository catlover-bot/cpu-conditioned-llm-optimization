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
  %nx64 = sext i32 %nx to i64
  %ny64 = sext i32 %ny to i64
  %tmax64 = zext i32 %tmax to i64
  %ny.pos = icmp sgt i32 %ny, 0
  %nx.gt1 = icmp sgt i32 %nx, 1
  %ny.gt1 = icmp sgt i32 %ny, 1
  %nxm1 = sub nsw i32 %nx, 1
  %nym1 = sub nsw i32 %ny, 1
  %nxm1.pos = icmp sgt i32 %nxm1, 0
  %nym1.pos = icmp sgt i32 %nym1, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc120, %preheader
  %t = phi i32 [ 0, %preheader ], [ %inc121, %for.inc120 ]
  %t64 = zext i32 %t to i64
  br i1 %ny.pos, label %loop1.preheader, label %for.end

loop1.preheader:
  %fict.ptr = getelementptr inbounds double, ptr %_fict_, i64 %t64
  %fictval = load double, ptr %fict.ptr, align 8
  ; ey row 0 base
  br label %loop1.body

loop1.body:
  %j1 = phi i32 [ 0, %loop1.preheader ], [ %inc.j1, %loop1.body ]
  %j1.64 = sext i32 %j1 to i64
  %ey0.idx = getelementptr inbounds double, ptr %ey, i64 %j1.64
  store double %fictval, ptr %ey0.idx, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp.j1 = icmp slt i32 %inc.j1, %ny
  br i1 %cmp.j1, label %loop1.body, label %for.end

for.end:                                          ; preds = %loop1.body, %for.cond
  br i1 %nx.gt1, label %loop2.i.preheader, label %for.end42

loop2.i.preheader:
  br label %loop2.i

loop2.i:                                          ; preds = %loop2.i.preheader, %loop2.i.inc
  %i2 = phi i32 [ 1, %loop2.i.preheader ], [ %inc.i2, %loop2.i.inc ]
  %i2.64 = sext i32 i2 to i64
  br i1 %ny.pos, label %loop2.j.preheader, label %loop2.i.inc

loop2.j.preheader:
  %i2.64.p = sext i32 %i2 to i64
  %ey.row.i2 = mul nsw i64 %i2.64.p, %ny64
  %ey.rowptr.i2 = getelementptr inbounds double, ptr %ey, i64 %ey.row.i2
  %hz.row.i2 = mul nsw i64 %i2.64.p, %ny64
  %hz.rowptr.i2 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i2
  %im1 = sub nsw i32 %i2, 1
  %im1.64 = sext i32 %im1 to i64
  %hz.row.im1 = mul nsw i64 %im1.64, %ny64
  %hz.rowptr.im1 = getelementptr inbounds double, ptr %hz, i64 %hz.row.im1
  br label %loop2.j

loop2.j:                                          ; preds = %loop2.j.preheader, %loop2.j
  %j2 = phi i32 [ 0, %loop2.j.preheader ], [ %inc.j2, %loop2.j ]
  %j2.64 = sext i32 %j2 to i64
  %ey.elt = getelementptr inbounds double, ptr %ey.rowptr.i2, i64 %j2.64
  %ey.val = load double, ptr %ey.elt, align 8
  %hz.elt.i2 = getelementptr inbounds double, ptr %hz.rowptr.i2, i64 %j2.64
  %hz.val.i2 = load double, ptr %hz.elt.i2, align 8
  %hz.elt.im1 = getelementptr inbounds double, ptr %hz.rowptr.im1, i64 %j2.64
  %hz.val.im1 = load double, ptr %hz.elt.im1, align 8
  %sub31 = fsub double %hz.val.i2, %hz.val.im1
  %mul.5 = fmul double 5.000000e-01, %sub31
  %sub32 = fsub double %ey.val, %mul.5
  store double %sub32, ptr %ey.elt, align 8
  %inc.j2 = add nsw i32 %j2, 1
  %cmp.j2 = icmp slt i32 %inc.j2, %ny
  br i1 %cmp.j2, label %loop2.j, label %loop2.i.inc

loop2.i.inc:                                      ; preds = %loop2.j, %loop2.i
  %inc.i2 = add nsw i32 %i2, 1
  %cmp.i2 = icmp slt i32 %inc.i2, %nx
  br i1 %cmp.i2, label %loop2.i, label %for.end42

for.end42:                                        ; preds = %loop2.i.inc, %for.end
  br i1 %ny.gt1, label %loop3.i.preheader, label %for.end74

loop3.i.preheader:
  br label %loop3.i

loop3.i:                                          ; preds = %loop3.i.preheader, %loop3.i.inc
  %i3 = phi i32 [ 0, %loop3.i.preheader ], [ %inc.i3, %loop3.i.inc ]
  %i3.64 = sext i32 %i3 to i64
  %ex.row.i3 = mul nsw i64 %i3.64, %ny64
  %ex.rowptr.i3 = getelementptr inbounds double, ptr %ex, i64 %ex.row.i3
  %hz.row.i3 = mul nsw i64 %i3.64, %ny64
  %hz.rowptr.i3 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i3
  br i1 %nx.gt1, label %skip_unused, label %skip_unused
skip_unused:
  br i1 true, label %loop3.j.check, label %loop3.j.check

loop3.j.check:
  br i1 %ny.gt1, label %loop3.j.preheader, label %loop3.i.inc

loop3.j.preheader:
  br label %loop3.j

loop3.j:                                          ; preds = %loop3.j.preheader, %loop3.j
  %j3 = phi i32 [ 1, %loop3.j.preheader ], [ %inc.j3, %loop3.j ]
  %j3.64 = sext i32 %j3 to i64
  %ex.elt = getelementptr inbounds double, ptr %ex.rowptr.i3, i64 %j3.64
  %ex.val = load double, ptr %ex.elt, align 8
  %hz.elt.j = getelementptr inbounds double, ptr %hz.rowptr.i3, i64 %j3.64
  %hz.val.j = load double, ptr %hz.elt.j, align 8
  %jm1 = sub nsw i32 %j3, 1
  %jm1.64 = sext i32 %jm1 to i64
  %hz.elt.jm1 = getelementptr inbounds double, ptr %hz.rowptr.i3, i64 %jm1.64
  %hz.val.jm1 = load double, ptr %hz.elt.jm1, align 8
  %sub62 = fsub double %hz.val.j, %hz.val.jm1
  %mul63.5 = fmul double 5.000000e-01, %sub62
  %sub64 = fsub double %ex.val, %mul63.5
  store double %sub64, ptr %ex.elt, align 8
  %inc.j3 = add nsw i32 %j3, 1
  %cmp.j3 = icmp slt i32 %inc.j3, %ny
  br i1 %cmp.j3, label %loop3.j, label %loop3.i.inc

loop3.i.inc:                                      ; preds = %loop3.j, %loop3.j.check
  %inc.i3 = add nsw i32 %i3, 1
  %cmp.i3 = icmp slt i32 %inc.i3, %nx
  br i1 %cmp.i3, label %loop3.i, label %for.end74

for.end74:                                        ; preds = %loop3.i.inc, %for.end42
  br i1 %nxm1.pos, label %loop4.i.preheader, label %for.end119

loop4.i.preheader:
  br label %loop4.i

loop4.i:                                          ; preds = %loop4.i.preheader, %loop4.i.inc
  %i4 = phi i32 [ 0, %loop4.i.preheader ], [ %inc.i4, %loop4.i.inc ]
  %i4.64 = sext i32 %i4 to i64
  %hz.row.i4 = mul nsw i64 %i4.64, %ny64
  %hz.rowptr.i4 = getelementptr inbounds double, ptr %hz, i64 %hz.row.i4
  %ex.row.i4 = mul nsw i64 %i4.64, %ny64
  %ex.rowptr.i4 = getelementptr inbounds double, ptr %ex, i64 %ex.row.i4
  %ip1.4 = add nsw i32 %i4, 1
  %ip1.4.64 = sext i32 %ip1.4 to i64
  %ey.row.ip1 = mul nsw i64 %ip1.4.64, %ny64
  %ey.rowptr.ip1 = getelementptr inbounds double, ptr %ey, i64 %ey.row.ip1
  %ey.row.i4 = mul nsw i64 %i4.64, %ny64
  %ey.rowptr.i4 = getelementptr inbounds double, ptr %ey, i64 %ey.row.i4
  br i1 %nym1.pos, label %loop4.j.preheader, label %loop4.i.inc

loop4.j.preheader:
  br label %loop4.j

loop4.j:                                          ; preds = %loop4.j.preheader, %loop4.j
  %j4 = phi i32 [ 0, %loop4.j.preheader ], [ %inc.j4, %loop4.j ]
  %j4.64 = sext i32 %j4 to i64
  %hz.elt.4 = getelementptr inbounds double, ptr %hz.rowptr.i4, i64 %j4.64
  %hz.val.4 = load double, ptr %hz.elt.4, align 8
  %jp1.4 = add nsw i32 %j4, 1
  %jp1.4.64 = sext i32 %jp1.4 to i64
  %ex.elt.jp1 = getelementptr inbounds double, ptr %ex.rowptr.i4, i64 %jp1.4.64
  %ex.val.jp1 = load double, ptr %ex.elt.jp1, align 8
  %ex.elt.j = getelementptr inbounds double, ptr %ex.rowptr.i4, i64 %j4.64
  %ex.val.j = load double, ptr %ex.elt.j, align 8
  %sub96 = fsub double %ex.val.jp1, %ex.val.j
  %ey.elt.ip1 = getelementptr inbounds double, ptr %ey.rowptr.ip1, i64 %j4.64
  %ey.val.ip1 = load double, ptr %ey.elt.ip1, align 8
  %add102 = fadd double %sub96, %ey.val.ip1
  %ey.elt.i4 = getelementptr inbounds double, ptr %ey.rowptr.i4, i64 %j4.64
  %ey.val.i4 = load double, ptr %ey.elt.i4, align 8
  %sub107 = fsub double %add102, %ey.val.i4
  %mul108 = fmul double 0x3FE6666666666666, %sub107
  %sub109 = fsub double %hz.val.4, %mul108
  store double %sub109, ptr %hz.elt.4, align 8
  %inc.j4 = add nsw i32 %j4, 1
  %cmp.j4 = icmp slt i32 %inc.j4, %nym1
  br i1 %cmp.j4, label %loop4.j, label %loop4.i.inc

loop4.i.inc:                                      ; preds = %loop4.j, %loop4.i
  %inc.i4 = add nsw i32 %i4, 1
  %cmp.i4 = icmp slt i32 %inc.i4, %nxm1
  br i1 %cmp.i4, label %loop4.i, label %for.end119

for.end119:                                       ; preds = %loop4.i.inc, %for.end74
  br label %for.inc120

for.inc120:                                       ; preds = %for.end119
  %inc121 = add nsw i32 %t, 1
  %cmp.t = icmp slt i32 %inc121, %tmax
  br i1 %cmp.t, label %for.cond, label %for.end122

for.end122:                                       ; preds = %for.inc120, %entry
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
