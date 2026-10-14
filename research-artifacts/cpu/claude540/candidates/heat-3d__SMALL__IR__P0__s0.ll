; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_heat_3d(i32 noundef %tsteps, i32 noundef %n, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 2
  br i1 %cmp.n, label %check.tsteps, label %for.end217

check.tsteps:
  %cmp.t0 = icmp sle i32 1, %tsteps
  br i1 %cmp.t0, label %preheader, label %for.end217

preheader:
  %n64 = zext i32 %n to i64
  %nm1 = add nsw i32 %n, -1
  %nm1.64 = zext i32 %nm1 to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc215, %preheader
  %t = phi i32 [ 1, %preheader ], [ %inc216, %for.inc215 ]
  br label %for.body

for.body:
  br label %for.cond6

for.cond6:                                        ; preds = %for.inc104, %for.body
  %i = phi i64 [ 1, %for.body ], [ %inc105, %for.inc104 ]
  %cmp7 = icmp slt i64 %i, %nm1.64
  br i1 %cmp7, label %for.body8, label %for.end106

for.body8:
  %ip1 = add nsw i64 %i, 1
  %im1 = add nsw i64 %i, -1
  %i.base = mul nsw i64 %ip1, %n64
  %i.base2 = mul nsw i64 %i, %n64
  %im1.base = mul nsw i64 %im1, %n64
  br label %for.cond9

for.cond9:                                        ; preds = %for.inc101, %for.body8
  %j = phi i64 [ 1, %for.body8 ], [ %inc102, %for.inc101 ]
  %cmp11 = icmp slt i64 %j, %nm1.64
  br i1 %cmp11, label %for.body12, label %for.end103

for.body12:
  %jp1 = add nsw i64 %j, 1
  %jm1 = add nsw i64 %j, -1
  %row.ip1 = add nsw i64 %i.base, %j
  %row.ip1.mul = mul nsw i64 %row.ip1, %n64
  %row.i = add nsw i64 %i.base2, %j
  %row.i.mul = mul nsw i64 %row.i, %n64
  %row.im1 = add nsw i64 %im1.base, %j
  %row.im1.mul = mul nsw i64 %row.im1, %n64
  %row.i.jp1 = add nsw i64 %i.base2, %jp1
  %row.i.jp1.mul = mul nsw i64 %row.i.jp1, %n64
  %row.i.jm1 = add nsw i64 %i.base2, %jm1
  %row.i.jm1.mul = mul nsw i64 %row.i.jm1, %n64
  %ptr.ip1 = getelementptr inbounds double, ptr %A, i64 %row.ip1.mul
  %ptr.i = getelementptr inbounds double, ptr %A, i64 %row.i.mul
  %ptr.im1 = getelementptr inbounds double, ptr %A, i64 %row.im1.mul
  %ptr.i.jp1 = getelementptr inbounds double, ptr %A, i64 %row.i.jp1.mul
  %ptr.i.jm1 = getelementptr inbounds double, ptr %A, i64 %row.i.jm1.mul
  br label %for.cond13

for.cond13:                                       ; preds = %for.inc, %for.body12
  %k = phi i64 [ 1, %for.body12 ], [ %inc, %for.inc ]
  %cmp15 = icmp slt i64 %k, %nm1.64
  br i1 %cmp15, label %for.body16, label %for.end

for.body16:
  %kp1 = add nsw i64 %k, 1
  %km1 = add nsw i64 %k, -1

  %a.ip1 = getelementptr inbounds double, ptr %ptr.ip1, i64 %k
  %v.ip1 = load double, ptr %a.ip1, align 8
  %a.i = getelementptr inbounds double, ptr %ptr.i, i64 %k
  %v.i = load double, ptr %a.i, align 8
  %mul = fmul double 2.000000e+00, %v.i
  %sub28 = fsub double %v.ip1, %mul
  %a.im1 = getelementptr inbounds double, ptr %ptr.im1, i64 %k
  %v.im1 = load double, ptr %a.im1, align 8
  %add36 = fadd double %sub28, %v.im1
  %mul37 = fmul double 1.250000e-01, %add36

  %a.jp1 = getelementptr inbounds double, ptr %ptr.i.jp1, i64 %k
  %v.jp1 = load double, ptr %a.jp1, align 8
  %v.i2 = load double, ptr %a.i, align 8
  %mul51 = fmul double 2.000000e+00, %v.i2
  %sub52 = fsub double %v.jp1, %mul51
  %a.jm1 = getelementptr inbounds double, ptr %ptr.i.jm1, i64 %k
  %v.jm1 = load double, ptr %a.jm1, align 8
  %add60 = fadd double %sub52, %v.jm1
  %mul61 = fmul double 1.250000e-01, %add60
  %add62 = fadd double %mul37, %mul61

  %a.kp1 = getelementptr inbounds double, ptr %a.i, i64 1
  %v.kp1 = load double, ptr %a.kp1, align 8
  %v.i3 = load double, ptr %a.i, align 8
  %mul76 = fmul double 2.000000e+00, %v.i3
  %sub77 = fsub double %v.kp1, %mul76
  %a.km1 = getelementptr inbounds double, ptr %a.i, i64 -1
  %v.km1 = load double, ptr %a.km1, align 8
  %add85 = fadd double %sub77, %v.km1
  %mul86 = fmul double 1.250000e-01, %add85
  %add87 = fadd double %add62, %mul86

  %v.i4 = load double, ptr %a.i, align 8
  %add94 = fadd double %add87, %v.i4

  %b.row = mul nsw i64 %ip1, %n64
  %b.row2 = add nsw i64 %b.row, %j
  %b.row3 = mul nsw i64 %b.row2, %n64
  %b.addr = getelementptr inbounds double, ptr %B, i64 %b.row3
  %b.final = getelementptr inbounds double, ptr %b.addr, i64 %k
  store double %add94, ptr %b.final, align 8
  br label %for.inc

for.inc:                                          ; preds = %for.body16
  %inc = add nsw i64 %k, 1
  br label %for.cond13, !llvm.loop !6

for.end:                                          ; preds = %for.cond13
  br label %for.inc101

for.inc101:                                       ; preds = %for.end
  %inc102 = add nsw i64 %j, 1
  br label %for.cond9, !llvm.loop !8

for.end103:                                       ; preds = %for.cond9
  br label %for.inc104

for.inc104:                                       ; preds = %for.end103
  %inc105 = add nsw i64 %i, 1
  br label %for.cond6, !llvm.loop !9

for.end106:                                       ; preds = %for.cond6
  br label %for.cond107

for.cond107:                                      ; preds = %for.inc212, %for.end106
  %i2 = phi i64 [ 1, %for.end106 ], [ %inc213, %for.inc212 ]
  %cmp109 = icmp slt i64 %i2, %nm1.64
  br i1 %cmp109, label %for.body110, label %for.end214

for.body110:
  %ip1b = add nsw i64 %i2, 1
  %im1b = add nsw i64 %i2, -1
  %i2.base = mul nsw i64 %ip1b, %n64
  %i2.base2 = mul nsw i64 %i2, %n64
  %im1b.base = mul nsw i64 %im1b, %n64
  br label %for.cond111

for.cond111:                                      ; preds = %for.inc209, %for.body110
  %j2 = phi i64 [ 1, %for.body110 ], [ %inc210, %for.inc209 ]
  %cmp113 = icmp slt i64 %j2, %nm1.64
  br i1 %cmp113, label %for.body114, label %for.end211

for.body114:
  %jp1b = add nsw i64 %j2, 1
  %jm1b = add nsw i64 %j2, -1
  %r.ip1 = add nsw i64 %i2.base, %j2
  %r.ip1.mul = mul nsw i64 %r.ip1, %n64
  %r.i = add nsw i64 %i2.base2, %j2
  %r.i.mul = mul nsw i64 %r.i, %n64
  %r.im1 = add nsw i64 %im1b.base, %j2
  %r.im1.mul = mul nsw i64 %r.im1, %n64
  %r.i.jp1 = add nsw i64 %i2.base2, %jp1b
  %r.i.jp1.mul = mul nsw i64 %r.i.jp1, %n64
  %r.i.jm1 = add nsw i64 %i2.base2, %jm1b
  %r.i.jm1.mul = mul nsw i64 %r.i.jm1, %n64
  %bp.ip1 = getelementptr inbounds double, ptr %B, i64 %r.ip1.mul
  %bp.i = getelementptr inbounds double, ptr %B, i64 %r.i.mul
  %bp.im1 = getelementptr inbounds double, ptr %B, i64 %r.im1.mul
  %bp.i.jp1 = getelementptr inbounds double, ptr %B, i64 %r.i.jp1.mul
  %bp.i.jm1 = getelementptr inbounds double, ptr %B, i64 %r.i.jm1.mul
  br label %for.cond115

for.cond115:                                      ; preds = %for.inc206, %for.body114
  %k2 = phi i64 [ 1, %for.body114 ], [ %inc207, %for.inc206 ]
  %cmp117 = icmp slt i64 %k2, %nm1.64
  br i1 %cmp117, label %for.body118, label %for.end208

for.body118:
  %kp1b = add nsw i64 %k2, 1
  %km1b = add nsw i64 %k2, -1

  %bv.ip1p = getelementptr inbounds double, ptr %bp.ip1, i64 %k2
  %bv.ip1 = load double, ptr %bv.ip1p, align 8
  %bv.ip = getelementptr inbounds double, ptr %bp.i, i64 %k2
  %bv.i = load double, ptr %bv.ip, align 8
  %bmul132 = fmul double 2.000000e+00, %bv.i
  %bsub133 = fsub double %bv.ip1, %bmul132
  %bv.im1p = getelementptr inbounds double, ptr %bp.im1, i64 %k2
  %bv.im1 = load double, ptr %bv.im1p, align 8
  %badd141 = fadd double %bsub133, %bv.im1
  %bmul142 = fmul double 1.250000e-01, %badd141

  %bv.jp1p = getelementptr inbounds double, ptr %bp.i.jp1, i64 %k2
  %bv.jp1 = load double, ptr %bv.jp1p, align 8
  %bv.i2 = load double, ptr %bv.ip, align 8
  %bmul156 = fmul double 2.000000e+00, %bv.i2
  %bsub157 = fsub double %bv.jp1, %bmul156
  %bv.jm1p = getelementptr inbounds double, ptr %bp.i.jm1, i64 %k2
  %bv.jm1 = load double, ptr %bv.jm1p, align 8
  %badd165 = fadd double %bsub157, %bv.jm1
  %bmul166 = fmul double 1.250000e-01, %badd165
  %badd167 = fadd double %bmul142, %bmul166

  %bv.kp1p = getelementptr inbounds double, ptr %bv.ip, i64 1
  %bv.kp1 = load double, ptr %bv.kp1p, align 8
  %bv.i3 = load double, ptr %bv.ip, align 8
  %bmul181 = fmul double 2.000000e+00, %bv.i3
  %bsub182 = fsub double %bv.kp1, %bmul181
  %bv.km1p = getelementptr inbounds double, ptr %bv.ip, i64 -1
  %bv.km1 = load double, ptr %bv.km1p, align 8
  %badd190 = fadd double %bsub182, %bv.km1
  %bmul191 = fmul double 1.250000e-01, %badd190
  %badd192 = fadd double %badd167, %bmul191

  %bv.i4 = load double, ptr %bv.ip, align 8
  %badd199 = fadd double %badd192, %bv.i4

  %a.row = mul nsw i64 %i2, %n64
  %a.row2 = add nsw i64 %a.row, %j2
  %a.row3 = mul nsw i64 %a.row2, %n64
  %a.addr = getelementptr inbounds double, ptr %A, i64 %a.row3
  %a.final = getelementptr inbounds double, ptr %a.addr, i64 %k2
  store double %badd199, ptr %a.final, align 8
  br label %for.inc206

for.inc206:                                       ; preds = %for.body118
  %inc207 = add nsw i64 %k2, 1
  br label %for.cond115, !llvm.loop !10

for.end208:                                       ; preds = %for.cond115
  br label %for.inc209

for.inc209:                                       ; preds = %for.end208
  %inc210 = add nsw i64 %j2, 1
  br label %for.cond111, !llvm.loop !11

for.end211:                                       ; preds = %for.cond111
  br label %for.inc212

for.inc212:                                       ; preds = %for.end211
  %inc213 = add nsw i64 %i2, 1
  br label %for.cond107, !llvm.loop !12

for.end214:                                       ; preds = %for.cond107
  br label %for.inc215

for.inc215:                                       ; preds = %for.end214
  %inc216 = add nsw i32 %t, 1
  %cmp = icmp sle i32 %inc216, %tsteps
  br i1 %cmp, label %for.cond, label %for.end217.loopexit, !llvm.loop !13

for.end217.loopexit:
  br label %for.end217

for.end217:                                       ; preds = %for.end217.loopexit, %check.tsteps, %entry
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
