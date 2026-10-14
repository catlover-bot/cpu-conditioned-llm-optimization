; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %cmp.t = icmp sgt i32 %tsteps, 0
  %and.run = and i1 %cmp.n, %cmp.t
  br i1 %and.run, label %preheader, label %for.end246

preheader:
  %n64 = sext i32 %n to i64
  %conv = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %conv
  %DY = fdiv double 1.000000e+00, %conv
  %conv10 = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %conv10

  %mulA = fmul double 2.000000e+00, %DT
  %mulDX2 = fmul double %DX, %DX
  %mul1 = fdiv double %mulA, %mulDX2

  %mulB = fmul double 1.000000e+00, %DT
  %mulDY2 = fmul double %DY, %DY
  %mul2 = fdiv double %mulB, %mulDY2

  %a.neg = fneg double %mul1
  %a = fdiv double %a.neg, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fadd double 0.000000e+00, %a
  %d.neg = fneg double %mul2
  %d = fdiv double %d.neg, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fadd double 0.000000e+00, %d

  %nm1 = sub nsw i32 %n, 1
  %nm1.64 = sext i32 %nm1 to i64
  %nm2 = sub nsw i32 %n, 2
  %nm2.64.for.j = sext i32 %nm2 to i64

  br label %t.loop

t.loop:
  %t = phi i32 [ 1, %preheader ], [ %t.inc, %t.end ]
  br label %i.loop1

i.loop1:
  %i = phi i32 [ 1, %t.loop ], [ %i.inc1, %i.loop1.end ]
  %i64 = sext i32 %i to i64

  ; v[0][i] = 1.0
  %v0.base = getelementptr inbounds double, ptr %v, i64 0
  %v0.i = getelementptr inbounds double, ptr %v0.base, i64 %i64
  store double 1.000000e+00, ptr %v0.i, align 8

  ; p[i][0] = 0.0
  %p.rowbase = mul nsw i64 %i64, %n64
  %p.row = getelementptr inbounds double, ptr %p, i64 %p.rowbase
  store double 0.000000e+00, ptr %p.row, align 8

  ; q[i][0] = v[0][i]
  %v0.i.val = load double, ptr %v0.i, align 8
  %q.row = getelementptr inbounds double, ptr %q, i64 %p.rowbase
  store double %v0.i.val, ptr %q.row, align 8

  br label %j.loop1

j.loop1:
  %j = phi i32 [ 1, %i.loop1 ], [ %j.inc1, %j.loop1 ]
  %j64 = sext i32 %j to i64
  %jm1 = sub nsw i32 %j, 1
  %jm1.64 = sext i32 %jm1 to i64
  %jp1 = add nsw i32 %j, 1
  %jp1.64 = sext i32 %jp1 to i64
  %im1 = sub nsw i32 %i, 1
  %im1.64 = sext i32 %im1 to i64
  %ip1 = add nsw i32 %i, 1
  %ip1.64 = sext i32 %ip1 to i64

  %p.i.jm1.ptr = getelementptr inbounds double, ptr %p.row, i64 %jm1.64
  %p.i.jm1 = load double, ptr %p.i.jm1.ptr, align 8

  %c.neg = fneg double %c
  %t1 = fmul double %a, %p.i.jm1
  %t2 = fadd double %t1, %b
  %div50 = fdiv double %c.neg, %t2
  %p.i.j.ptr = getelementptr inbounds double, ptr %p.row, i64 %j64
  store double %div50, ptr %p.i.j.ptr, align 8

  %u.jrow = getelementptr inbounds double, ptr %u, i64 %j64, i64 0
  %u.jbase = mul nsw i64 %j64, %n64
  %u.j.base.ptr = getelementptr inbounds double, ptr %u, i64 %u.jbase
  %u.j.im1.ptr = getelementptr inbounds double, ptr %u.j.base.ptr, i64 %im1.64
  %u.j.im1 = load double, ptr %u.j.im1.ptr, align 8

  %d.neg2 = fneg double %d
  %mul61 = fmul double %d.neg2, %u.j.im1
  %mul62 = fmul double 2.000000e+00, %d
  %add63 = fadd double 1.000000e+00, %mul62
  %u.j.i.ptr = getelementptr inbounds double, ptr %u.j.base.ptr, i64 %i64
  %u.j.i = load double, ptr %u.j.i.ptr, align 8
  %mul68 = fmul double %add63, %u.j.i
  %add69 = fadd double %mul61, %mul68

  %u.j.ip1.ptr = getelementptr inbounds double, ptr %u.j.base.ptr, i64 %ip1.64
  %u.j.ip1 = load double, ptr %u.j.ip1.ptr, align 8
  %mul75 = fmul double %f, %u.j.ip1
  %sub76 = fsub double %add69, %mul75

  %q.rowbase.i = mul nsw i64 %i64, %n64
  %q.row.base.ptr = getelementptr inbounds double, ptr %q, i64 %q.rowbase.i
  %q.i.jm1.ptr = getelementptr inbounds double, ptr %q.row.base.ptr, i64 %jm1.64
  %q.i.jm1 = load double, ptr %q.i.jm1.ptr, align 8
  %mul82 = fmul double %a, %q.i.jm1
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %p.i.jm1
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90

  %q.i.j.ptr = getelementptr inbounds double, ptr %q.row.base.ptr, i64 %j64
  store double %div91, ptr %q.i.j.ptr, align 8

  %j.inc1 = add nsw i32 %j, 1
  %cmp39 = icmp slt i32 %j.inc1, %nm1
  br i1 %cmp39, label %j.loop1, label %j.end1

j.end1:
  ; v[n-1][i] = 1.0
  %vlast.base = mul nsw i64 %nm1.64, %n64
  %vlast.ptr = getelementptr inbounds double, ptr %v, i64 %vlast.base
  %vlast.i.ptr = getelementptr inbounds double, ptr %vlast.ptr, i64 %i64
  store double 1.000000e+00, ptr %vlast.i.ptr, align 8

  br label %j.loop2

j.loop2:
  %j2 = phi i32 [ %nm2, %j.end1 ], [ %j2.dec, %j.loop2 ]
  %j2.64 = sext i32 %j2 to i64
  %j2p1 = add nsw i32 %j2, 1
  %j2p1.64 = sext i32 %j2p1 to i64

  %p.i.j2.ptr = getelementptr inbounds double, ptr %p.row, i64 %j2.64
  %p.i.j2 = load double, ptr %p.i.j2.ptr, align 8

  %v.j2p1.base = mul nsw i64 %j2p1.64, %n64
  %v.j2p1.ptr = getelementptr inbounds double, ptr %v, i64 %v.j2p1.base
  %v.j2p1.i.ptr = getelementptr inbounds double, ptr %v.j2p1.ptr, i64 %i64
  %v.j2p1.i = load double, ptr %v.j2p1.i.ptr, align 8

  %mul115 = fmul double %p.i.j2, %v.j2p1.i

  %q.i.j2.ptr = getelementptr inbounds double, ptr %q.row.base.ptr, i64 %j2.64
  %q.i.j2 = load double, ptr %q.i.j2.ptr, align 8
  %add120 = fadd double %mul115, %q.i.j2

  %v.j2.base = mul nsw i64 %j2.64, %n64
  %v.j2.ptr = getelementptr inbounds double, ptr %v, i64 %v.j2.base
  %v.j2.i.ptr = getelementptr inbounds double, ptr %v.j2.ptr, i64 %i64
  store double %add120, ptr %v.j2.i.ptr, align 8

  %j2.dec = add nsw i32 %j2, -1
  %cmp103 = icmp sge i32 %j2.dec, 1
  br i1 %cmp103, label %j.loop2, label %i.loop1.end

i.loop1.end:
  %i.inc1 = add nsw i32 %i, 1
  %cmp24 = icmp slt i32 %i.inc1, %nm1
  br i1 %cmp24, label %i.loop1, label %i.loop2.pre

i.loop2.pre:
  br label %i.loop2

i.loop2:
  %ii = phi i32 [ 1, %i.loop2.pre ], [ %ii.inc, %i.loop2.end ]
  %ii64 = sext i32 %ii to i64

  ; u[i][0] = 1.0
  %u.rowbase = mul nsw i64 %ii64, %n64
  %u.row = getelementptr inbounds double, ptr %u, i64 %u.rowbase
  store double 1.000000e+00, ptr %u.row, align 8

  ; p[i][0] = 0.0
  %p.rowbase2 = mul nsw i64 %ii64, %n64
  %p.row2 = getelementptr inbounds double, ptr %p, i64 %p.rowbase2
  store double 0.000000e+00, ptr %p.row2, align 8

  ; q[i][0] = u[i][0]
  %u.row.val = load double, ptr %u.row, align 8
  %q.row2 = getelementptr inbounds double, ptr %q, i64 %p.rowbase2
  store double %u.row.val, ptr %q.row2, align 8

  br label %j.loop3

j.loop3:
  %j3 = phi i32 [ 1, %i.loop2 ], [ %j3.inc, %j.loop3 ]
  %j3.64 = sext i32 %j3 to i64
  %j3m1 = sub nsw i32 %j3, 1
  %j3m1.64 = sext i32 %j3m1 to i64
  %iim1 = sub nsw i32 %ii, 1
  %iim1.64 = sext i32 %iim1 to i64
  %iip1 = add nsw i32 %ii, 1
  %iip1.64 = sext i32 %iip1 to i64

  %p.ii.j3m1.ptr = getelementptr inbounds double, ptr %p.row2, i64 %j3m1.64
  %p.ii.j3m1 = load double, ptr %p.ii.j3m1.ptr, align 8

  %f.neg = fneg double %f
  %t3 = fmul double %d, %p.ii.j3m1
  %t4 = fadd double %t3, %e
  %div160 = fdiv double %f.neg, %t4
  %p.ii.j3.ptr = getelementptr inbounds double, ptr %p.row2, i64 %j3.64
  store double %div160, ptr %p.ii.j3.ptr, align 8

  %v.iim1.base = mul nsw i64 %iim1.64, %n64
  %v.iim1.ptr = getelementptr inbounds double, ptr %v, i64 %v.iim1.base
  %v.iim1.j3.ptr = getelementptr inbounds double, ptr %v.iim1.ptr, i64 %j3.64
  %v.iim1.j3 = load double, ptr %v.iim1.j3.ptr, align 8

  %a.neg2 = fneg double %a
  %mul171 = fmul double %a.neg2, %v.iim1.j3
  %mul172 = fmul double 2.000000e+00, %a
  %add173 = fadd double 1.000000e+00, %mul172

  %v.ii.base = mul nsw i64 %ii64, %n64
  %v.ii.ptr = getelementptr inbounds double, ptr %v, i64 %v.ii.base
  %v.ii.j3.ptr = getelementptr inbounds double, ptr %v.ii.ptr, i64 %j3.64
  %v.ii.j3 = load double, ptr %v.ii.j3.ptr, align 8
  %mul178 = fmul double %add173, %v.ii.j3
  %add179 = fadd double %mul171, %mul178

  %v.iip1.base = mul nsw i64 %iip1.64, %n64
  %v.iip1.ptr = getelementptr inbounds double, ptr %v, i64 %v.iip1.base
  %v.iip1.j3.ptr = getelementptr inbounds double, ptr %v.iip1.ptr, i64 %j3.64
  %v.iip1.j3 = load double, ptr %v.iip1.j3.ptr, align 8
  %mul185 = fmul double %c, %v.iip1.j3
  %sub186 = fsub double %add179, %mul185

  %q.ii.j3m1.ptr = getelementptr inbounds double, ptr %q.row2, i64 %j3m1.64
  %q.ii.j3m1 = load double, ptr %q.ii.j3m1.ptr, align 8
  %mul192 = fmul double %d, %q.ii.j3m1
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %p.ii.j3m1
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200

  %q.ii.j3.ptr = getelementptr inbounds double, ptr %q.row2, i64 %j3.64
  store double %div201, ptr %q.ii.j3.ptr, align 8

  %j3.inc = add nsw i32 %j3, 1
  %cmp149 = icmp slt i32 %j3.inc, %nm1
  br i1 %cmp149, label %j.loop3, label %j.end3

j.end3:
  ; u[i][n-1] = 1.0
  %ulast.i.ptr = getelementptr inbounds double, ptr %u.row, i64 %nm1.64
  store double 1.000000e+00, ptr %ulast.i.ptr, align 8

  br label %j.loop4

j.loop4:
  %j4 = phi i32 [ %nm2, %j.end3 ], [ %j4.dec, %j.loop4 ]
  %j4.64 = sext i32 %j4 to i64
  %j4p1 = add nsw i32 %j4, 1
  %j4p1.64 = sext i32 %j4p1 to i64

  %p.ii.j4.ptr = getelementptr inbounds double, ptr %p.row2, i64 %j4.64
  %p.ii.j4 = load double, ptr %p.ii.j4.ptr, align 8

  %u.ii.j4p1.ptr = getelementptr inbounds double, ptr %u.row, i64 %j4p1.64
  %u.ii.j4p1 = load double, ptr %u.ii.j4p1.ptr, align 8

  %mul228 = fmul double %p.ii.j4, %u.ii.j4p1

  %q.ii.j4.ptr = getelementptr inbounds double, ptr %q.row2, i64 %j4.64
  %q.ii.j4 = load double, ptr %q.ii.j4.ptr, align 8
  %add233 = fadd double %mul228, %q.ii.j4

  %u.ii.j4.ptr = getelementptr inbounds double, ptr %u.row, i64 %j4.64
  store double %add233, ptr %u.ii.j4.ptr, align 8

  %j4.dec = add nsw i32 %j4, -1
  %cmp216 = icmp sge i32 %j4.dec, 1
  br i1 %cmp216, label %j.loop4, label %i.loop2.end

i.loop2.end:
  %ii.inc = add nsw i32 %ii, 1
  %cmp132 = icmp slt i32 %ii.inc, %nm1
  br i1 %cmp132, label %i.loop2, label %t.end

t.end:
  %t.inc = add nsw i32 %t, 1
  %cmp = icmp sle i32 %t.inc, %tsteps
  br i1 %cmp, label %t.loop, label %for.end246

for.end246:
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
