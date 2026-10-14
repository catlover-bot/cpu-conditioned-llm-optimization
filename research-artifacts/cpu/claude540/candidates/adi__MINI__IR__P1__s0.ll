; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_adi(i32 noundef %tsteps, i32 noundef %n, ptr noundef %u, ptr noundef %v, ptr noundef %p, ptr noundef %q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 1
  %n64 = sext i32 %n to i64
  %tsteps64 = sext i32 %tsteps to i64

  %conv = sitofp i32 %n to double
  %DX = fdiv double 1.000000e+00, %conv
  %DY = fdiv double 1.000000e+00, %conv
  %conv10 = sitofp i32 %tsteps to double
  %DT = fdiv double 1.000000e+00, %conv10

  %mul1.tmp1 = fmul double 2.000000e+00, %DT
  %mul1.tmp2 = fmul double %DX, %DX
  %mul1 = fdiv double %mul1.tmp1, %mul1.tmp2

  %mul2.tmp1 = fmul double 1.000000e+00, %DT
  %mul2.tmp2 = fmul double %DY, %DY
  %mul2 = fdiv double %mul2.tmp1, %mul2.tmp2

  %a.fneg = fneg double %mul1
  %a = fdiv double %a.fneg, 2.000000e+00
  %b = fadd double 1.000000e+00, %mul1
  %c = fadd double 0.000000e+00, %a
  %d.fneg = fneg double %mul2
  %d = fdiv double %d.fneg, 2.000000e+00
  %e = fadd double 1.000000e+00, %mul2
  %f = fadd double 0.000000e+00, %d

  %tsteps.le0 = icmp slt i32 %tsteps, 1
  br i1 %tsteps.le0, label %for.end246, label %for.cond.preheader

for.cond.preheader:                               ; preds = %entry
  br i1 %cmp.n, label %for.body.preheader, label %for.end246

for.body.preheader:                               ; preds = %for.cond.preheader
  %n.sub1 = add nsw i32 %n, -1
  %n.sub1.64 = sext i32 %n.sub1 to i64
  %n.sub2 = add nsw i32 %n, -2
  br label %for.body

for.body:                                         ; preds = %for.inc244, %for.body.preheader
  %t.06 = phi i64 [ 1, %for.body.preheader ], [ %inc245, %for.inc244 ]

  br label %for.body26

for.body26:                                       ; preds = %for.inc127, %for.body
  %i.05 = phi i64 [ 1, %for.body ], [ %inc128, %for.inc127 ]

  ; v[0][i] = 1.0
  %v.row0 = getelementptr inbounds double, ptr %v, i64 0
  %v0i = getelementptr inbounds double, ptr %v.row0, i64 %i.05
  store double 1.000000e+00, ptr %v0i, align 8

  ; p[i][0] = 0.0
  %p.rowi.base = mul nsw i64 %i.05, %n64
  %p.rowi = getelementptr inbounds double, ptr %p, i64 %p.rowi.base
  store double 0.000000e+00, ptr %p.rowi, align 8

  ; q[i][0] = v[0][i]
  %v0i.val = load double, ptr %v0i, align 8
  %q.rowi.base = mul nsw i64 %i.05, %n64
  %q.rowi = getelementptr inbounds double, ptr %q, i64 %q.rowi.base
  store double %v0i.val, ptr %q.rowi, align 8

  br label %for.body41

for.body41:                                       ; preds = %for.body41, %for.body26
  %j.04 = phi i64 [ 1, %for.body26 ], [ %inc, %for.body41 ]

  %p.im1 = add nsw i64 %j.04, -1
  %p.arrayidx47 = getelementptr inbounds double, ptr %p.rowi, i64 %p.im1
  %p.jm1.val = load double, ptr %p.arrayidx47, align 8

  %c.fneg = fneg double %c
  %mul48 = fmul double %a, %p.jm1.val
  %add49 = fadd double %mul48, %b
  %div50 = fdiv double %c.fneg, %add49
  %p.arrayidx54 = getelementptr inbounds double, ptr %p.rowi, i64 %j.04
  store double %div50, ptr %p.arrayidx54, align 8

  %u.rowj.base = mul nsw i64 %j.04, %n64
  %u.rowj = getelementptr inbounds double, ptr %u, i64 %u.rowj.base
  %i.m1 = add nsw i64 %i.05, -1
  %u.arrayidx60 = getelementptr inbounds double, ptr %u.rowj, i64 %i.m1
  %u.im1.val = load double, ptr %u.arrayidx60, align 8

  %d.fneg55 = fneg double %d
  %mul61 = fmul double %d.fneg55, %u.im1.val

  %mul62 = fmul double 2.000000e+00, %d
  %add63 = fadd double 1.000000e+00, %mul62
  %u.arrayidx67 = getelementptr inbounds double, ptr %u.rowj, i64 %i.05
  %u.i.val = load double, ptr %u.arrayidx67, align 8
  %mul68 = fmul double %add63, %u.i.val
  %add69 = fadd double %mul61, %mul68

  %i.p1 = add nsw i64 %i.05, 1
  %u.arrayidx74 = getelementptr inbounds double, ptr %u.rowj, i64 %i.p1
  %u.ip1.val = load double, ptr %u.arrayidx74, align 8
  %mul75 = fmul double %f, %u.ip1.val
  %sub76 = fsub double %add69, %mul75

  %q.arrayidx81 = getelementptr inbounds double, ptr %q.rowi, i64 %p.im1
  %q.jm1.val = load double, ptr %q.arrayidx81, align 8
  %mul82 = fmul double %a, %q.jm1.val
  %sub83 = fsub double %sub76, %mul82

  %mul89 = fmul double %a, %p.jm1.val
  %add90 = fadd double %mul89, %b
  %div91 = fdiv double %sub83, %add90
  %q.arrayidx95 = getelementptr inbounds double, ptr %q.rowi, i64 %j.04
  store double %div91, ptr %q.arrayidx95, align 8

  %inc = add nsw i64 %j.04, 1
  %cmp39 = icmp slt i64 %inc, %n.sub1.64
  br i1 %cmp39, label %for.body41, label %for.end

for.end:                                          ; preds = %for.body41
  %v.rowlast.base = mul nsw i64 %n.sub1.64, %n64
  %v.rowlast = getelementptr inbounds double, ptr %v, i64 %v.rowlast.base
  %v.arrayidx100 = getelementptr inbounds double, ptr %v.rowlast, i64 %i.05
  store double 1.000000e+00, ptr %v.arrayidx100, align 8

  %n.sub2.ge1 = icmp sge i32 %n.sub2, 1
  br i1 %n.sub2.ge1, label %for.body105.preheader, label %for.end126

for.body105.preheader:                            ; preds = %for.end
  %n.sub2.64 = sext i32 %n.sub2 to i64
  br label %for.body105

for.body105:                                      ; preds = %for.body105, %for.body105.preheader
  %j.13 = phi i64 [ %n.sub2.64, %for.body105.preheader ], [ %dec, %for.body105 ]

  %p.arrayidx109 = getelementptr inbounds double, ptr %p.rowi, i64 %j.13
  %p.j.val = load double, ptr %p.arrayidx109, align 8

  %j.p1 = add nsw i64 %j.13, 1
  %v.rowjp1.base = mul nsw i64 %j.p1, %n64
  %v.rowjp1 = getelementptr inbounds double, ptr %v, i64 %v.rowjp1.base
  %v.arrayidx114 = getelementptr inbounds double, ptr %v.rowjp1, i64 %i.05
  %v.jp1.val = load double, ptr %v.arrayidx114, align 8
  %mul115 = fmul double %p.j.val, %v.jp1.val

  %q.arrayidx119 = getelementptr inbounds double, ptr %q.rowi, i64 %j.13
  %q.j.val = load double, ptr %q.arrayidx119, align 8
  %add120 = fadd double %mul115, %q.j.val

  %v.rowj.base = mul nsw i64 %j.13, %n64
  %v.rowj = getelementptr inbounds double, ptr %v, i64 %v.rowj.base
  %v.arrayidx124 = getelementptr inbounds double, ptr %v.rowj, i64 %i.05
  store double %add120, ptr %v.arrayidx124, align 8

  %dec = add nsw i64 %j.13, -1
  %cmp103 = icmp sge i64 %dec, 1
  br i1 %cmp103, label %for.body105, label %for.end126.loopexit

for.end126.loopexit:                              ; preds = %for.body105
  br label %for.end126

for.end126:                                       ; preds = %for.end126.loopexit, %for.end
  %inc128 = add nsw i64 %i.05, 1
  %cmp24 = icmp slt i64 %inc128, %n.sub1.64
  br i1 %cmp24, label %for.body26, label %for.end129

for.end129:                                       ; preds = %for.end126
  br label %for.body134

for.body134:                                      ; preds = %for.inc241, %for.end129
  %i2.05 = phi i64 [ 1, %for.end129 ], [ %inc242, %for.inc241 ]

  %u.rowi.base = mul nsw i64 %i2.05, %n64
  %u.rowi = getelementptr inbounds double, ptr %u, i64 %u.rowi.base
  store double 1.000000e+00, ptr %u.rowi, align 8

  %p2.rowi.base = mul nsw i64 %i2.05, %n64
  %p2.rowi = getelementptr inbounds double, ptr %p, i64 %p2.rowi.base
  store double 0.000000e+00, ptr %p2.rowi, align 8

  %u.row0.val = load double, ptr %u.rowi, align 8
  %q2.rowi.base = mul nsw i64 %i2.05, %n64
  %q2.rowi = getelementptr inbounds double, ptr %q, i64 %q2.rowi.base
  store double %u.row0.val, ptr %q2.rowi, align 8

  br label %for.body151

for.body151:                                      ; preds = %for.body151, %for.body134
  %j2.04 = phi i64 [ 1, %for.body134 ], [ %inc207, %for.body151 ]

  %p2.jm1 = add nsw i64 %j2.04, -1
  %p2.arrayidx157 = getelementptr inbounds double, ptr %p2.rowi, i64 %p2.jm1
  %p2.jm1.val = load double, ptr %p2.arrayidx157, align 8

  %f.fneg = fneg double %f
  %mul158 = fmul double %d, %p2.jm1.val
  %add159 = fadd double %mul158, %e
  %div160 = fdiv double %f.fneg, %add159
  %p2.arrayidx164 = getelementptr inbounds double, ptr %p2.rowi, i64 %j2.04
  store double %div160, ptr %p2.arrayidx164, align 8

  %i2.m1 = add nsw i64 %i2.05, -1
  %v.rowim1.base = mul nsw i64 %i2.m1, %n64
  %v.rowim1 = getelementptr inbounds double, ptr %v, i64 %v.rowim1.base
  %v.arrayidx170 = getelementptr inbounds double, ptr %v.rowim1, i64 %j2.04
  %v.im1.val = load double, ptr %v.arrayidx170, align 8

  %a.fneg165 = fneg double %a
  %mul171 = fmul double %a.fneg165, %v.im1.val

  %mul172 = fmul double 2.000000e+00, %a
  %add173 = fadd double 1.000000e+00, %mul172
  %v.rowi2.base = mul nsw i64 %i2.05, %n64
  %v.rowi2 = getelementptr inbounds double, ptr %v, i64 %v.rowi2.base
  %v.arrayidx177 = getelementptr inbounds double, ptr %v.rowi2, i64 %j2.04
  %v.i.val = load double, ptr %v.arrayidx177, align 8
  %mul178 = fmul double %add173, %v.i.val
  %add179 = fadd double %mul171, %mul178

  %i2.p1 = add nsw i64 %i2.05, 1
  %v.rowip1.base = mul nsw i64 %i2.p1, %n64
  %v.rowip1 = getelementptr inbounds double, ptr %v, i64 %v.rowip1.base
  %v.arrayidx184 = getelementptr inbounds double, ptr %v.rowip1, i64 %j2.04
  %v.ip1.val = load double, ptr %v.arrayidx184, align 8
  %mul185 = fmul double %c, %v.ip1.val
  %sub186 = fsub double %add179, %mul185

  %q2.arrayidx191 = getelementptr inbounds double, ptr %q2.rowi, i64 %p2.jm1
  %q2.jm1.val = load double, ptr %q2.arrayidx191, align 8
  %mul192 = fmul double %d, %q2.jm1.val
  %sub193 = fsub double %sub186, %mul192

  %mul199 = fmul double %d, %p2.jm1.val
  %add200 = fadd double %mul199, %e
  %div201 = fdiv double %sub193, %add200
  %q2.arrayidx205 = getelementptr inbounds double, ptr %q2.rowi, i64 %j2.04
  store double %div201, ptr %q2.arrayidx205, align 8

  %inc207 = add nsw i64 %j2.04, 1
  %cmp149 = icmp slt i64 %inc207, %n.sub1.64
  br i1 %cmp149, label %for.body151, label %for.end208

for.end208:                                       ; preds = %for.body151
  %u.arrayidx213 = getelementptr inbounds double, ptr %u.rowi, i64 %n.sub1.64
  store double 1.000000e+00, ptr %u.arrayidx213, align 8

  br i1 %n.sub2.ge1, label %for.body218.preheader, label %for.end240

for.body218.preheader:                            ; preds = %for.end208
  %n.sub2.64.b = sext i32 %n.sub2 to i64
  br label %for.body218

for.body218:                                      ; preds = %for.body218, %for.body218.preheader
  %j3.13 = phi i64 [ %n.sub2.64.b, %for.body218.preheader ], [ %dec239, %for.body218 ]

  %p2.arrayidx222 = getelementptr inbounds double, ptr %p2.rowi, i64 %j3.13
  %p2.j.val = load double, ptr %p2.arrayidx222, align 8

  %j3.p1 = add nsw i64 %j3.13, 1
  %u.arrayidx227 = getelementptr inbounds double, ptr %u.rowi, i64 %j3.p1
  %u.jp1.val = load double, ptr %u.arrayidx227, align 8
  %mul228 = fmul double %p2.j.val, %u.jp1.val

  %q2.arrayidx232 = getelementptr inbounds double, ptr %q2.rowi, i64 %j3.13
  %q2.j.val = load double, ptr %q2.arrayidx232, align 8
  %add233 = fadd double %mul228, %q2.j.val

  %u.arrayidx237 = getelementptr inbounds double, ptr %u.rowi, i64 %j3.13
  store double %add233, ptr %u.arrayidx237, align 8

  %dec239 = add nsw i64 %j3.13, -1
  %cmp216 = icmp sge i64 %dec239, 1
  br i1 %cmp216, label %for.body218, label %for.end240.loopexit

for.end240.loopexit:                              ; preds = %for.body218
  br label %for.end240

for.end240:                                       ; preds = %for.end240.loopexit, %for.end208
  %inc242 = add nsw i64 %i2.05, 1
  %cmp132 = icmp slt i64 %inc242, %n.sub1.64
  br i1 %cmp132, label %for.body134, label %for.end243

for.end243:                                       ; preds = %for.end240
  br label %for.inc244

for.inc244:                                       ; preds = %for.end243
  %inc245 = add nsw i64 %t.06, 1
  %cmp = icmp sle i64 %inc245, %tsteps64
  br i1 %cmp, label %for.body, label %for.end246.loopexit

for.end246.loopexit:                              ; preds = %for.inc244
  br label %for.end246

for.end246:                                       ; preds = %for.end246.loopexit, %for.cond.preheader, %entry
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
