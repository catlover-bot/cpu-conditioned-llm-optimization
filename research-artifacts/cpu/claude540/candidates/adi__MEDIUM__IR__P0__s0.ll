; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n1 = icmp sle i32 %n, 1
  br i1 %cmp.n1, label %check.tsteps.trivial, label %compute.consts

check.tsteps.trivial:
  br label %for.end246

compute.consts:
  %n64 = sext i32 %n to i64
  %nm1 = sub nsw i32 %n, 1
  %nm1.64 = zext i32 %nm1 to i64

  %conv = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %conv
  %DY = fdiv double 1.000000e+00, %conv
  %conv10 = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %conv10

  ; B1=2.0, B2=1.0
  %mul1.num = fmul double 2.000000e+00, %DT
  %DXsq = fmul double %DX, %DX
  %mul1 = fdiv double %mul1.num, %DXsq
  %mul2.num = fmul double 1.000000e+00, %DT
  %DYsq = fmul double %DY, %DY
  %mul2 = fdiv double %mul2.num, %DYsq

  %a = fdiv double (fneg double %mul1), 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fdiv double (fneg double %mul1), 2.000000e+00
  %d = fdiv double (fneg double %mul2), 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fdiv double (fneg double %mul2), 2.000000e+00

  br label %for.cond

for.cond:
  %t = phi i32 [ 1, %compute.consts ], [ %inc245, %for.inc244 ]
  %cmp = icmp sle i32 %t, %tsteps
  br i1 %cmp, label %for.body, label %for.end246.from.loop

for.body:
  br label %for.cond23

for.cond23:
  %i = phi i32 [ 1, %for.body ], [ %inc128, %for.inc127 ]
  %cmp24 = icmp slt i32 %i, %nm1
  br i1 %cmp24, label %for.body26, label %for.end129

for.body26:
  %i64 = sext i32 %i to i64
  ; v[0][i] = 1.0
  %vrow0 = getelementptr inbounds double, ptr %v, i64 0
  %v0i = getelementptr inbounds double, ptr %vrow0, i64 %i64
  store double 1.000000e+00, ptr %v0i, align 8

  ; p[i][0] = 0.0
  %prowi.off = mul nsw i64 %i64, %n64
  %prowi = getelementptr inbounds double, ptr %p, i64 %prowi.off
  store double 0.000000e+00, ptr %prowi, align 8

  ; q[i][0] = v[0][i]
  %v0i.val = load double, ptr %v0i, align 8
  %qrowi.off = mul nsw i64 %i64, %n64
  %qrowi = getelementptr inbounds double, ptr %q, i64 %qrowi.off
  store double %v0i.val, ptr %qrowi, align 8

  br label %for.cond37

for.cond37:
  %j = phi i32 [ 1, %for.body26 ], [ %inc, %for.inc ]
  %cmp39 = icmp slt i32 %j, %nm1
  br i1 %cmp39, label %for.body41, label %for.end

for.body41:
  %j64 = sext i32 %j to i64
  %jm1 = sub nsw i32 %j, 1
  %jm1.64 = sext i32 %jm1 to i64
  %jp1 = add nsw i32 %j, 1
  %jp1.64 = sext i32 %jp1 to i64
  %im1 = sub nsw i32 %i, 1
  %im1.64 = sext i32 %im1 to i64
  %ip1 = add nsw i32 %i, 1
  %ip1.64 = sext i32 %ip1 to i64

  %p.rowi = getelementptr inbounds double, ptr %prowi, i64 0
  %p.i.jm1 = getelementptr inbounds double, ptr %p.rowi, i64 %jm1.64
  %p.i.jm1.val = load double, ptr %p.i.jm1, align 8

  %negc = fneg double %c
  %mul48 = fmul double %a, %p.i.jm1.val
  %add49 = fadd double %mul48, %b
  %div50 = fdiv double %negc, %add49

  %p.i.j = getelementptr inbounds double, ptr %p.rowi, i64 %j64
  store double %div50, ptr %p.i.j, align 8

  %u.rowj.off = mul nsw i64 %j64, %n64
  %u.rowj = getelementptr inbounds double, ptr %u, i64 %u.rowj.off
  %u.j.im1 = getelementptr inbounds double, ptr %u.rowj, i64 %im1.64
  %u.j.im1.val = load double, ptr %u.j.im1, align 8

  %negd = fneg double %d
  %mul61 = fmul double %negd, %u.j.im1.val

  %mul62 = fmul double 2.000000e+00, %d
  %add63 = fadd double 1.000000e+00, %mul62

  %u.j.i = getelementptr inbounds double, ptr %u.rowj, i64 %i64
  %u.j.i.val = load double, ptr %u.j.i, align 8
  %mul68 = fmul double %add63, %u.j.i.val
  %add69 = fadd double %mul61, %mul68

  %u.j.ip1 = getelementptr inbounds double, ptr %u.rowj, i64 %ip1.64
  %u.j.ip1.val = load double, ptr %u.j.ip1, align 8
  %mul75 = fmul double %f, %u.j.ip1.val
  %sub76 = fsub double %add69, %mul75

  %q.rowi = getelementptr inbounds double, ptr %qrowi, i64 0
  %q.i.jm1 = getelementptr inbounds double, ptr %q.rowi, i64 %jm1.64
  %q.i.jm1.val = load double, ptr %q.i.jm1, align 8
  %mul82 = fmul double %a, %q.i.jm1.val
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %p.i.jm1.val
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90

  %q.i.j = getelementptr inbounds double, ptr %q.rowi, i64 %j64
  store double %div91, ptr %q.i.j, align 8

  br label %for.inc

for.inc:
  %inc = add nsw i32 %j, 1
  br label %for.cond37, !llvm.loop !6

for.end:
  ; v[n-1][i] = 1.0
  %vrow.nm1.off = mul nsw i64 %nm1.64, %n64
  %vrow.nm1 = getelementptr inbounds double, ptr %v, i64 %vrow.nm1.off
  %v.nm1.i = getelementptr inbounds double, ptr %vrow.nm1, i64 %i64
  store double 1.000000e+00, ptr %v.nm1.i, align 8

  %nm2 = sub nsw i32 %n, 2
  br label %for.cond102

for.cond102:
  %j2 = phi i32 [ %nm2, %for.end ], [ %dec, %for.inc125 ]
  %cmp103 = icmp sge i32 %j2, 1
  br i1 %cmp103, label %for.body105, label %for.end126

for.body105:
  %j2.64 = sext i32 %j2 to i64
  %j2p1 = add nsw i32 %j2, 1
  %j2p1.64 = sext i32 %j2p1 to i64

  %p.rowi2 = getelementptr inbounds double, ptr %prowi, i64 0
  %p.i.j2 = getelementptr inbounds double, ptr %p.rowi2, i64 %j2.64
  %p.i.j2.val = load double, ptr %p.i.j2, align 8

  %v.rowj2p1.off = mul nsw i64 %j2p1.64, %n64
  %v.rowj2p1 = getelementptr inbounds double, ptr %v, i64 %v.rowj2p1.off
  %v.j2p1.i = getelementptr inbounds double, ptr %v.rowj2p1, i64 %i64
  %v.j2p1.i.val = load double, ptr %v.j2p1.i, align 8

  %mul115 = fmul double %p.i.j2.val, %v.j2p1.i.val

  %q.rowi2 = getelementptr inbounds double, ptr %qrowi, i64 0
  %q.i.j2 = getelementptr inbounds double, ptr %q.rowi2, i64 %j2.64
  %q.i.j2.val = load double, ptr %q.i.j2, align 8

  %add120 = fadd double %mul115, %q.i.j2.val

  %v.rowj2.off = mul nsw i64 %j2.64, %n64
  %v.rowj2 = getelementptr inbounds double, ptr %v, i64 %v.rowj2.off
  %v.j2.i = getelementptr inbounds double, ptr %v.rowj2, i64 %i64
  store double %add120, ptr %v.j2.i, align 8

  br label %for.inc125

for.inc125:
  %dec = add nsw i32 %j2, -1
  br label %for.cond102, !llvm.loop !8

for.end126:
  br label %for.inc127

for.inc127:
  %inc128 = add nsw i32 %i, 1
  br label %for.cond23, !llvm.loop !9

for.end129:
  br label %for.cond130

for.cond130:
  %i2 = phi i32 [ 1, %for.end129 ], [ %inc242, %for.inc241 ]
  %cmp132 = icmp slt i32 %i2, %nm1
  br i1 %cmp132, label %for.body134, label %for.end243

for.body134:
  %i2.64 = sext i32 %i2 to i64

  ; u[i][0] = 1.0
  %u.rowi2.off = mul nsw i64 %i2.64, %n64
  %u.rowi2 = getelementptr inbounds double, ptr %u, i64 %u.rowi2.off
  store double 1.000000e+00, ptr %u.rowi2, align 8

  ; p[i][0] = 0.0
  %p.rowi2b.off = mul nsw i64 %i2.64, %n64
  %p.rowi2b = getelementptr inbounds double, ptr %p, i64 %p.rowi2b.off
  store double 0.000000e+00, ptr %p.rowi2b, align 8

  ; q[i][0] = u[i][0]
  %u.rowi2.val = load double, ptr %u.rowi2, align 8
  %q.rowi2b.off = mul nsw i64 %i2.64, %n64
  %q.rowi2b = getelementptr inbounds double, ptr %q, i64 %q.rowi2b.off
  store double %u.rowi2.val, ptr %q.rowi2b, align 8

  br label %for.cond147

for.cond147:
  %j3 = phi i32 [ 1, %for.body134 ], [ %inc207, %for.inc206 ]
  %cmp149 = icmp slt i32 %j3, %nm1
  br i1 %cmp149, label %for.body151, label %for.end208

for.body151:
  %j3.64 = sext i32 %j3 to i64
  %j3m1 = sub nsw i32 %j3, 1
  %j3m1.64 = sext i32 %j3m1 to i64
  %j3p1 = add nsw i32 %j3, 1
  %j3p1.64 = sext i32 %j3p1 to i64
  %i2m1 = sub nsw i32 %i2, 1
  %i2m1.64 = sext i32 %i2m1 to i64
  %i2p1 = add nsw i32 %i2, 1
  %i2p1.64 = sext i32 %i2p1 to i64

  %p.rowi2c = getelementptr inbounds double, ptr %p.rowi2b, i64 0
  %p.i2.j3m1 = getelementptr inbounds double, ptr %p.rowi2c, i64 %j3m1.64
  %p.i2.j3m1.val = load double, ptr %p.i2.j3m1, align 8

  %negf = fneg double %f
  %mul158 = fmul double %d, %p.i2.j3m1.val
  %add159 = fadd double %mul158, %e
  %div160 = fdiv double %negf, %add159

  %p.i2.j3 = getelementptr inbounds double, ptr %p.rowi2c, i64 %j3.64
  store double %div160, ptr %p.i2.j3, align 8

  %v.rowi2m1.off = mul nsw i64 %i2m1.64, %n64
  %v.rowi2m1 = getelementptr inbounds double, ptr %v, i64 %v.rowi2m1.off
  %v.i2m1.j3 = getelementptr inbounds double, ptr %v.rowi2m1, i64 %j3.64
  %v.i2m1.j3.val = load double, ptr %v.i2m1.j3, align 8

  %nega = fneg double %a
  %mul171 = fmul double %nega, %v.i2m1.j3.val

  %mul172 = fmul double 2.000000e+00, %a
  %add173 = fadd double 1.000000e+00, %mul172

  %v.rowi2.off = mul nsw i64 %i2.64, %n64
  %v.rowi2 = getelementptr inbounds double, ptr %v, i64 %v.rowi2.off
  %v.i2.j3 = getelementptr inbounds double, ptr %v.rowi2, i64 %j3.64
  %v.i2.j3.val = load double, ptr %v.i2.j3, align 8
  %mul178 = fmul double %add173, %v.i2.j3.val
  %add179 = fadd double %mul171, %mul178

  %v.rowi2p1.off = mul nsw i64 %i2p1.64, %n64
  %v.rowi2p1 = getelementptr inbounds double, ptr %v, i64 %v.rowi2p1.off
  %v.i2p1.j3 = getelementptr inbounds double, ptr %v.rowi2p1, i64 %j3.64
  %v.i2p1.j3.val = load double, ptr %v.i2p1.j3, align 8
  %mul185 = fmul double %c, %v.i2p1.j3.val
  %sub186 = fsub double %add179, %mul185

  %q.rowi2c = getelementptr inbounds double, ptr %q.rowi2b, i64 0
  %q.i2.j3m1 = getelementptr inbounds double, ptr %q.rowi2c, i64 %j3m1.64
  %q.i2.j3m1.val = load double, ptr %q.i2.j3m1, align 8
  %mul192 = fmul double %d, %q.i2.j3m1.val
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %p.i2.j3m1.val
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200

  %q.i2.j3 = getelementptr inbounds double, ptr %q.rowi2c, i64 %j3.64
  store double %div201, ptr %q.i2.j3, align 8

  br label %for.inc206

for.inc206:
  %inc207 = add nsw i32 %j3, 1
  br label %for.cond147, !llvm.loop !10

for.end208:
  ; u[i][n-1] = 1.0
  %u.rowi2c.off = mul nsw i64 %i2.64, %n64
  %u.rowi2c = getelementptr inbounds double, ptr %u, i64 %u.rowi2c.off
  %u.i2.nm1 = getelementptr inbounds double, ptr %u.rowi2c, i64 %nm1.64
  store double 1.000000e+00, ptr %u.i2.nm1, align 8

  %nm2b = sub nsw i32 %n, 2
  br label %for.cond215

for.cond215:
  %j4 = phi i32 [ %nm2b, %for.end208 ], [ %dec239, %for.inc238 ]
  %cmp216 = icmp sge i32 %j4, 1
  br i1 %cmp216, label %for.body218, label %for.end240

for.body218:
  %j4.64 = sext i32 %j4 to i64
  %j4p1 = add nsw i32 %j4, 1
  %j4p1.64 = sext i32 %j4p1 to i64

  %p.rowi2d = getelementptr inbounds double, ptr %p.rowi2b, i64 0
  %p.i2.j4 = getelementptr inbounds double, ptr %p.rowi2d, i64 %j4.64
  %p.i2.j4.val = load double, ptr %p.i2.j4, align 8

  %u.rowi2d = getelementptr inbounds double, ptr %u.rowi2c, i64 0
  %u.i2.j4p1 = getelementptr inbounds double, ptr %u.rowi2d, i64 %j4p1.64
  %u.i2.j4p1.val = load double, ptr %u.i2.j4p1, align 8

  %mul228 = fmul double %p.i2.j4.val, %u.i2.j4p1.val

  %q.rowi2d = getelementptr inbounds double, ptr %q.rowi2b, i64 0
  %q.i2.j4 = getelementptr inbounds double, ptr %q.rowi2d, i64 %j4.64
  %q.i2.j4.val = load double, ptr %q.i2.j4, align 8

  %add233 = fadd double %mul228, %q.i2.j4.val

  %u.i2.j4 = getelementptr inbounds double, ptr %u.rowi2d, i64 %j4.64
  store double %add233, ptr %u.i2.j4, align 8

  br label %for.inc238

for.inc238:
  %dec239 = add nsw i32 %j4, -1
  br label %for.cond215, !llvm.loop !11

for.end240:
  br label %for.inc241

for.inc241:
  %inc242 = add nsw i32 %i2, 1
  br label %for.cond130, !llvm.loop !12

for.end243:
  br label %for.inc244

for.inc244:
  %inc245 = add nsw i32 %t, 1
  br label %for.cond, !llvm.loop !13

for.end246.from.loop:
  br label %for.end246

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
