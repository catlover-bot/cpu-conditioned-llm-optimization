; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %n.i64 = sext i32 %n to i64

  %conv = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %conv
  %DY = fdiv double 1.000000e+00, %conv

  %conv10 = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %conv10

  ; mul1 = (2.0*DT) / (DX*DX)
  %mulDT1 = fmul double 2.000000e+00, %DT
  %DXDX = fmul double %DX, %DX
  %mul1 = fdiv double %mulDT1, %DXDX

  ; mul2 = (1.0*DT) / (DY*DY)
  %mulDT2 = fmul double 1.000000e+00, %DT
  %DYDY = fmul double %DY, %DY
  %mul2 = fdiv double %mulDT2, %DYDY

  %a.neg = fneg double %mul1
  %a = fdiv double %a.neg, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fadd double 0.000000e+00, %a
  %d.neg = fneg double %mul2
  %d = fdiv double %d.neg, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fadd double 0.000000e+00, %d

  br label %for.cond

for.cond:
  %t = phi i32 [ 1, %entry ], [ %inc245, %for.inc244 ]
  %cmp = icmp sle i32 %t, %tsteps
  br i1 %cmp, label %for.body, label %for.end246

for.body:
  br i1 %cmp.n, label %for.cond23.preheader, label %for.end243

for.cond23.preheader:
  br label %for.body26

for.body26:
  %i = phi i32 [ 1, %for.cond23.preheader ], [ %inc128, %for.inc127 ]

  ; v[0][i] = 1.0
  %i64.a = sext i32 %i to i64
  %v0i.ptr = getelementptr inbounds double, ptr %v, i64 %i64.a
  store double 1.000000e+00, ptr %v0i.ptr, align 8

  ; p[i][0] = 0.0
  %prow.a = mul nsw i64 %i64.a, %n.i64
  %pbase.a = getelementptr inbounds double, ptr %p, i64 %prow.a
  store double 0.000000e+00, ptr %pbase.a, align 8

  ; q[i][0] = v[0][i]
  %v0i.val = load double, ptr %v0i.ptr, align 8
  %qbase.a = getelementptr inbounds double, ptr %q, i64 %prow.a
  store double %v0i.val, ptr %qbase.a, align 8

  %n.sub1 = add nsw i32 %n, -1
  %inner.cmp = icmp slt i32 1, %n.sub1
  br i1 %inner.cmp, label %for.body41.preheader, label %for.end

for.body41.preheader:
  %urow.a = mul nsw i64 %i64.a, %n.i64
  %urow.base.a = getelementptr inbounds double, ptr %u, i64 %urow.a
  br label %for.body41

for.body41:
  %j = phi i32 [ 1, %for.body41.preheader ], [ %inc, %for.body41 ]

  %j64 = sext i32 %j to i64
  %jm1 = add nsw i32 %j, -1
  %jm164 = sext i32 %jm1 to i64

  %pij_m1.ptr = getelementptr inbounds double, ptr %pbase.a, i64 %jm164
  %pij_m1 = load double, ptr %pij_m1.ptr, align 8

  %c.neg = fneg double %c
  %mul48 = fmul double %a, %pij_m1
  %add49 = fadd double %mul48, %b
  %div50 = fdiv double %c.neg, %add49
  %pij.ptr = getelementptr inbounds double, ptr %pbase.a, i64 %j64
  store double %div50, ptr %pij.ptr, align 8

  %ujcol.a = mul nsw i64 %j64, %n.i64
  %ujbase.a = getelementptr inbounds double, ptr %u, i64 %ujcol.a
  %im1 = add nsw i32 %i, -1
  %im164 = sext i32 %im1 to i64
  %u_jm1i.ptr = getelementptr inbounds double, ptr %ujbase.a, i64 %im164
  %u_jm1i = load double, ptr %u_jm1i.ptr, align 8

  %d.neg2 = fneg double %d
  %mul61 = fmul double %d.neg2, %u_jm1i

  %mul62 = fmul double 2.000000e+00, %d
  %add63 = fadd double 1.000000e+00, %mul62
  %u_ji.ptr = getelementptr inbounds double, ptr %ujbase.a, i64 %i64.a
  %u_ji = load double, ptr %u_ji.ptr, align 8
  %mul68 = fmul double %add63, %u_ji
  %add69 = fadd double %mul61, %mul68

  %ip1 = add nsw i32 %i, 1
  %ip164 = sext i32 %ip1 to i64
  %u_jip1.ptr = getelementptr inbounds double, ptr %ujbase.a, i64 %ip164
  %u_jip1 = load double, ptr %u_jip1.ptr, align 8
  %mul75 = fmul double %f, %u_jip1
  %sub76 = fsub double %add69, %mul75

  %qij_m1.ptr = getelementptr inbounds double, ptr %qbase.a, i64 %jm164
  %qij_m1 = load double, ptr %qij_m1.ptr, align 8
  %mul82 = fmul double %a, %qij_m1
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %pij_m1
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90
  %qij.ptr = getelementptr inbounds double, ptr %qbase.a, i64 %j64
  store double %div91, ptr %qij.ptr, align 8

  %inc = add nsw i32 %j, 1
  %cmp39 = icmp slt i32 %inc, %n.sub1
  br i1 %cmp39, label %for.body41, label %for.end.loopexit

for.end.loopexit:
  br label %for.end

for.end:
  %nm1 = add nsw i32 %n, -1
  %nm164 = sext i32 %nm1 to i64
  %vlast.row = mul nsw i64 %nm164, %n.i64
  %vlast.base = getelementptr inbounds double, ptr %v, i64 %vlast.row
  %vlast.ptr = getelementptr inbounds double, ptr %vlast.base, i64 %i64.a
  store double 1.000000e+00, ptr %vlast.ptr, align 8

  %jstart = add nsw i32 %n, -2
  %jstart.cmp = icmp sge i32 %jstart, 1
  br i1 %jstart.cmp, label %for.body105.preheader, label %for.end126

for.body105.preheader:
  br label %for.body105

for.body105:
  %j2 = phi i32 [ %jstart, %for.body105.preheader ], [ %dec, %for.body105 ]

  %j264 = sext i32 %j2 to i64
  %pij2.ptr = getelementptr inbounds double, ptr %pbase.a, i64 %j264
  %pij2 = load double, ptr %pij2.ptr, align 8

  %jp1 = add nsw i32 %j2, 1
  %jp164 = sext i32 %jp1 to i64
  %vrow.jp1 = mul nsw i64 %jp164, %n.i64
  %vbase.jp1 = getelementptr inbounds double, ptr %v, i64 %vrow.jp1
  %v.jp1i.ptr = getelementptr inbounds double, ptr %vbase.jp1, i64 %i64.a
  %v.jp1i = load double, ptr %v.jp1i.ptr, align 8

  %mul115 = fmul double %pij2, %v.jp1i

  %qij2.ptr = getelementptr inbounds double, ptr %qbase.a, i64 %j264
  %qij2 = load double, ptr %qij2.ptr, align 8
  %add120 = fadd double %mul115, %qij2

  %vrow.j2 = mul nsw i64 %j264, %n.i64
  %vbase.j2 = getelementptr inbounds double, ptr %v, i64 %vrow.j2
  %v.j2i.ptr = getelementptr inbounds double, ptr %vbase.j2, i64 %i64.a
  store double %add120, ptr %v.j2i.ptr, align 8

  %dec = add nsw i32 %j2, -1
  %cmp103 = icmp sge i32 %dec, 1
  br i1 %cmp103, label %for.body105, label %for.end126.loopexit

for.end126.loopexit:
  br label %for.end126

for.end126:
  %inc128 = add nsw i32 %i, 1
  %cmp24 = icmp slt i32 %inc128, %n.sub1
  br i1 %cmp24, label %for.body26, label %for.end129

for.inc127:
  br label %for.body26

for.end129:
  br label %for.cond130.preheader

for.cond130.preheader:
  br i1 %cmp.n, label %for.body134.preheader, label %for.end243

for.body134.preheader:
  br label %for.body134

for.body134:
  %i2 = phi i32 [ 1, %for.body134.preheader ], [ %inc242, %for.end240 ]

  %i264 = sext i32 %i2 to i64
  %urow2 = mul nsw i64 %i264, %n.i64
  %ubase2 = getelementptr inbounds double, ptr %u, i64 %urow2
  store double 1.000000e+00, ptr %ubase2, align 8

  %prow2 = mul nsw i64 %i264, %n.i64
  %pbase2 = getelementptr inbounds double, ptr %p, i64 %prow2
  store double 0.000000e+00, ptr %pbase2, align 8

  %u0.val = load double, ptr %ubase2, align 8
  %qbase2 = getelementptr inbounds double, ptr %q, i64 %prow2
  store double %u0.val, ptr %qbase2, align 8

  %n.sub1.b = add nsw i32 %n, -1
  %inner.cmp.b = icmp slt i32 1, %n.sub1.b
  br i1 %inner.cmp.b, label %for.body151.preheader, label %for.end208

for.body151.preheader:
  br label %for.body151

for.body151:
  %j3 = phi i32 [ 1, %for.body151.preheader ], [ %inc207, %for.body151 ]

  %j364 = sext i32 %j3 to i64
  %j3m1 = add nsw i32 %j3, -1
  %j3m164 = sext i32 %j3m1 to i64

  %pij3_m1.ptr = getelementptr inbounds double, ptr %pbase2, i64 %j3m164
  %pij3_m1 = load double, ptr %pij3_m1.ptr, align 8

  %f.neg = fneg double %f
  %mul158 = fmul double %d, %pij3_m1
  %add159 = fadd double %mul158, %e
  %div160 = fdiv double %f.neg, %add159
  %pij3.ptr = getelementptr inbounds double, ptr %pbase2, i64 %j364
  store double %div160, ptr %pij3.ptr, align 8

  %i2m1 = add nsw i32 %i2, -1
  %i2m164 = sext i32 %i2m1 to i64
  %vrow.i2m1 = mul nsw i64 %i2m164, %n.i64
  %vbase.i2m1 = getelementptr inbounds double, ptr %v, i64 %vrow.i2m1
  %v.im1j.ptr = getelementptr inbounds double, ptr %vbase.i2m1, i64 %j364
  %v.im1j = load double, ptr %v.im1j.ptr, align 8

  %a.neg2 = fneg double %a
  %mul171 = fmul double %a.neg2, %v.im1j

  %mul172 = fmul double 2.000000e+00, %a
  %add173 = fadd double 1.000000e+00, %mul172
  %vrow.i2 = mul nsw i64 %i264, %n.i64
  %vbase.i2 = getelementptr inbounds double, ptr %v, i64 %vrow.i2
  %v.i2j.ptr = getelementptr inbounds double, ptr %vbase.i2, i64 %j364
  %v.i2j = load double, ptr %v.i2j.ptr, align 8
  %mul178 = fmul double %add173, %v.i2j
  %add179 = fadd double %mul171, %mul178

  %i2p1 = add nsw i32 %i2, 1
  %i2p164 = sext i32 %i2p1 to i64
  %vrow.i2p1 = mul nsw i64 %i2p164, %n.i64
  %vbase.i2p1 = getelementptr inbounds double, ptr %v, i64 %vrow.i2p1
  %v.ip1j.ptr = getelementptr inbounds double, ptr %vbase.i2p1, i64 %j364
  %v.ip1j = load double, ptr %v.ip1j.ptr, align 8
  %mul185 = fmul double %c, %v.ip1j
  %sub186 = fsub double %add179, %mul185

  %qij3_m1.ptr = getelementptr inbounds double, ptr %qbase2, i64 %j3m164
  %qij3_m1 = load double, ptr %qij3_m1.ptr, align 8
  %mul192 = fmul double %d, %qij3_m1
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %pij3_m1
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200
  %qij3.ptr = getelementptr inbounds double, ptr %qbase2, i64 %j364
  store double %div201, ptr %qij3.ptr, align 8

  %inc207 = add nsw i32 %j3, 1
  %cmp149 = icmp slt i32 %inc207, %n.sub1.b
  br i1 %cmp149, label %for.body151, label %for.end208.loopexit

for.end208.loopexit:
  br label %for.end208

for.end208:
  %nm1.b = add nsw i32 %n, -1
  %nm164.b = sext i32 %nm1.b to i64
  %ulast.ptr = getelementptr inbounds double, ptr %ubase2, i64 %nm164.b
  store double 1.000000e+00, ptr %ulast.ptr, align 8

  %jstart2 = add nsw i32 %n, -2
  %jstart2.cmp = icmp sge i32 %jstart2, 1
  br i1 %jstart2.cmp, label %for.body218.preheader, label %for.end240

for.body218.preheader:
  br label %for.body218

for.body218:
  %j4 = phi i32 [ %jstart2, %for.body218.preheader ], [ %dec239, %for.body218 ]

  %j464 = sext i32 %j4 to i64
  %pij4.ptr = getelementptr inbounds double, ptr %pbase2, i64 %j464
  %pij4 = load double, ptr %pij4.ptr, align 8

  %j4p1 = add nsw i32 %j4, 1
  %j4p164 = sext i32 %j4p1 to i64
  %u.ijp1.ptr = getelementptr inbounds double, ptr %ubase2, i64 %j4p164
  %u.ijp1 = load double, ptr %u.ijp1.ptr, align 8

  %mul228 = fmul double %pij4, %u.ijp1

  %qij4.ptr = getelementptr inbounds double, ptr %qbase2, i64 %j464
  %qij4 = load double, ptr %qij4.ptr, align 8
  %add233 = fadd double %mul228, %qij4

  %u.ij.ptr = getelementptr inbounds double, ptr %ubase2, i64 %j464
  store double %add233, ptr %u.ij.ptr, align 8

  %dec239 = add nsw i32 %j4, -1
  %cmp216 = icmp sge i32 %dec239, 1
  br i1 %cmp216, label %for.body218, label %for.end240.loopexit

for.end240.loopexit:
  br label %for.end240

for.end240:
  %inc242 = add nsw i32 %i2, 1
  %cmp132 = icmp slt i32 %inc242, %n.sub1.b
  br i1 %cmp132, label %for.body134, label %for.end243

for.end243:
  %inc245 = add nsw i32 %t, 1
  br label %for.cond244.exit

for.cond244.exit:
  br label %for.inc244

for.inc244:
  br label %for.cond

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
