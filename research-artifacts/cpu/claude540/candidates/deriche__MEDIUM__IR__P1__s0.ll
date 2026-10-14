; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %cmp.w.pos = icmp sgt i32 %w, 0
  %cmp.h.pos = icmp sgt i32 %h, 0

  %wz = zext i32 %w to i64
  %hz = zext i32 %h to i64

  %fneg.a = fneg float %alpha
  %exp.neg.a = call float @expf(float noundef %fneg.a) #2
  %sub.k1 = fsub float 1.000000e+00, %exp.neg.a
  %mul.k1 = fmul float %sub.k1, %sub.k1
  %mul.a2 = fmul float 2.000000e+00, %alpha
  %mul.a2.expna = fmul float %mul.a2, %exp.neg.a
  %add.k2 = fadd float 1.000000e+00, %mul.a2.expna
  %mul.a2b = fmul float 2.000000e+00, %alpha
  %exp.2a = call float @expf(float noundef %mul.a2b) #2
  %sub.k2 = fsub float %add.k2, %exp.2a
  %k = fdiv float %mul.k1, %sub.k2

  %a1 = fadd float %k, 0.000000e+00
  %a5 = fadd float %k, 0.000000e+00

  %k.expna = fmul float %k, %exp.neg.a
  %sub.am1 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %k.expna, %sub.am1
  %a6 = fmul float %k.expna, %sub.am1

  %add.ap1 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %k.expna, %add.ap1
  %a7 = fmul float %k.expna, %add.ap1

  %fneg.k = fneg float %k
  %mul.neg2a = fmul float -2.000000e+00, %alpha
  %exp.neg2a = call float @expf(float noundef %mul.neg2a) #2
  %a4 = fmul float %fneg.k, %exp.neg2a
  %a8 = fmul float %fneg.k, %exp.neg2a

  %fneg.b1 = fneg float %alpha
  %b1 = call float @powf(float noundef 2.000000e+00, float noundef %fneg.b1) #2

  %mul.neg2a.b2 = fmul float -2.000000e+00, %alpha
  %exp.neg2a.b2 = call float @expf(float noundef %mul.neg2a.b2) #2
  %b2 = fneg float %exp.neg2a.b2

  %c1 = fadd float 1.000000e+00, 0.000000e+00
  %c2 = fadd float 1.000000e+00, 0.000000e+00

  br i1 %cmp.w.pos, label %outer1.preheader, label %for.end64

outer1.preheader:
  br i1 %cmp.h.pos, label %outer1.body.preheader, label %outer1.trivial

outer1.trivial:
  ; h <= 0: inner loop never runs, just iterate i from 0 to w
  br label %for.end64

outer1.body.preheader:
  br label %outer1.body

outer1.body:                                         ; preds = %outer1.inc, %outer1.body.preheader
  %i1 = phi i64 [ 0, %outer1.body.preheader ], [ %i1.next, %outer1.inc ]
  %imgIn.row1 = getelementptr inbounds float, ptr %imgIn, i64 %i1
  %row.off1 = mul nsw i64 %i1, %hz
  %imgIn.rowbase1 = getelementptr inbounds float, ptr %imgIn, i64 %row.off1
  %y1.rowbase1 = getelementptr inbounds float, ptr %y1, i64 %row.off1
  br label %inner1.body

inner1.body:                                        ; preds = %inner1.body, %outer1.body
  %j1 = phi i64 [ 0, %outer1.body ], [ %j1.next, %inner1.body ]
  %xm1.phi = phi float [ 0.000000e+00, %outer1.body ], [ %xin1, %inner1.body ]
  %ym1.phi = phi float [ 0.000000e+00, %outer1.body ], [ %yout1, %inner1.body ]
  %ym2.phi = phi float [ 0.000000e+00, %outer1.body ], [ %ym1.phi, %inner1.body ]

  %in.ptr1 = getelementptr inbounds float, ptr %imgIn.rowbase1, i64 %j1
  %xin1 = load float, ptr %in.ptr1, align 4

  %m1.1 = fmul float %a1, %xin1
  %m1.2 = fmul float %a2, %xm1.phi
  %s1.1 = fadd float %m1.1, %m1.2
  %m1.3 = fmul float %b1, %ym1.phi
  %s1.2 = fadd float %s1.1, %m1.3
  %m1.4 = fmul float %b2, %ym2.phi
  %yout1 = fadd float %s1.2, %m1.4

  %y1.ptr1 = getelementptr inbounds float, ptr %y1.rowbase1, i64 %j1
  store float %yout1, ptr %y1.ptr1, align 4

  %j1.next = add nsw i64 %j1, 1
  %cmp.inner1 = icmp slt i64 %j1.next, %hz
  br i1 %cmp.inner1, label %inner1.body, label %outer1.inc

outer1.inc:
  %i1.next = add nsw i64 %i1, 1
  %cmp.outer1 = icmp slt i64 %i1.next, %wz
  br i1 %cmp.outer1, label %outer1.body, label %for.end64

for.end64:                                         ; preds = %outer1.inc, %outer1.trivial, %entry
  br i1 %cmp.w.pos, label %outer2.preheader, label %for.end95

outer2.preheader:
  br i1 %cmp.h.pos, label %outer2.body.preheader, label %for.end95

outer2.body.preheader:
  br label %outer2.body

outer2.body:                                        ; preds = %outer2.inc, %outer2.body.preheader
  %i2 = phi i64 [ 0, %outer2.body.preheader ], [ %i2.next, %outer2.inc ]
  %row.off2 = mul nsw i64 %i2, %hz
  %imgIn.rowbase2 = getelementptr inbounds float, ptr %imgIn, i64 %row.off2
  %y2.rowbase2 = getelementptr inbounds float, ptr %y2, i64 %row.off2
  %hm1 = sub nsw i64 %hz, 1
  br label %inner2.body

inner2.body:                                        ; preds = %inner2.body, %outer2.body
  %j2 = phi i64 [ %hm1, %outer2.body ], [ %j2.next, %inner2.body ]
  %xp1.phi = phi float [ 0.000000e+00, %outer2.body ], [ %xin2, %inner2.body ]
  %xp2.phi = phi float [ 0.000000e+00, %outer2.body ], [ %xp1.phi, %inner2.body ]
  %yp1.phi = phi float [ 0.000000e+00, %outer2.body ], [ %yin2, %inner2.body ]
  %yp2.phi = phi float [ 0.000000e+00, %outer2.body ], [ %yp1.phi, %inner2.body ]

  %m2.1 = fmul float %a3, %xp1.phi
  %m2.2 = fmul float %a4, %xp2.phi
  %s2.1 = fadd float %m2.1, %m2.2
  %m2.3 = fmul float %b1, %yp1.phi
  %s2.2 = fadd float %s2.1, %m2.3
  %m2.4 = fmul float %b2, %yp2.phi
  %yout2 = fadd float %s2.2, %m2.4

  %y2.ptr2 = getelementptr inbounds float, ptr %y2.rowbase2, i64 %j2
  store float %yout2, ptr %y2.ptr2, align 4

  %in.ptr2 = getelementptr inbounds float, ptr %imgIn.rowbase2, i64 %j2
  %xin2 = load float, ptr %in.ptr2, align 4

  %yin2 = load float, ptr %y2.ptr2, align 4

  %j2.next = add nsw i64 %j2, -1
  %cmp.inner2 = icmp sge i64 %j2.next, 0
  br i1 %cmp.inner2, label %inner2.body, label %outer2.inc

outer2.inc:
  %i2.next = add nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %wz
  br i1 %cmp.outer2, label %outer2.body, label %for.end95

for.end95:                                          ; preds = %outer2.inc, %outer2.preheader, %for.end64
  br i1 %cmp.w.pos, label %outer3.preheader, label %for.end121

outer3.preheader:
  br i1 %cmp.h.pos, label %outer3.body.preheader, label %for.end121

outer3.body.preheader:
  br label %outer3.body

outer3.body:                                        ; preds = %outer3.inc, %outer3.body.preheader
  %i3 = phi i64 [ 0, %outer3.body.preheader ], [ %i3.next, %outer3.inc ]
  %row.off3.y1 = mul nsw i64 %i3, %hz
  %y1.rowbase3 = getelementptr inbounds float, ptr %y1, i64 %row.off3.y1
  %y2.rowbase3 = getelementptr inbounds float, ptr %y2, i64 %row.off3.y1
  %imgOut.rowbase3 = getelementptr inbounds float, ptr %imgOut, i64 %row.off3.y1
  br label %inner3.body

inner3.body:                                        ; preds = %inner3.body, %outer3.body
  %j3 = phi i64 [ 0, %outer3.body ], [ %j3.next, %inner3.body ]

  %y1.ptr3 = getelementptr inbounds float, ptr %y1.rowbase3, i64 %j3
  %v1.3 = load float, ptr %y1.ptr3, align 4
  %y2.ptr3 = getelementptr inbounds float, ptr %y2.rowbase3, i64 %j3
  %v2.3 = load float, ptr %y2.ptr3, align 4
  %add3 = fadd float %v1.3, %v2.3
  %mul3 = fmul float %c1, %add3

  %out.ptr3 = getelementptr inbounds float, ptr %imgOut.rowbase3, i64 %j3
  store float %mul3, ptr %out.ptr3, align 4

  %j3.next = add nsw i64 %j3, 1
  %cmp.inner3 = icmp slt i64 %j3.next, %hz
  br i1 %cmp.inner3, label %inner3.body, label %outer3.inc

outer3.inc:
  %i3.next = add nsw i64 %i3, 1
  %cmp.outer3 = icmp slt i64 %i3.next, %wz
  br i1 %cmp.outer3, label %outer3.body, label %for.end121

for.end121:                                         ; preds = %outer3.inc, %outer3.preheader, %for.end95
  br i1 %cmp.h.pos, label %outer4.preheader, label %for.end156

outer4.preheader:
  br i1 %cmp.w.pos, label %outer4.body.preheader, label %for.end156

outer4.body.preheader:
  br label %outer4.body

outer4.body:                                        ; preds = %outer4.inc, %outer4.body.preheader
  %j4 = phi i64 [ 0, %outer4.body.preheader ], [ %j4.next, %outer4.inc ]
  br label %inner4.body

inner4.body:                                        ; preds = %inner4.body, %outer4.body
  %i4 = phi i64 [ 0, %outer4.body ], [ %i4.next, %inner4.body ]
  %tm1.phi = phi float [ 0.000000e+00, %outer4.body ], [ %tin4, %inner4.body ]
  %ym1.4phi = phi float [ 0.000000e+00, %outer4.body ], [ %yout4, %inner4.body ]
  %ym2.4phi = phi float [ 0.000000e+00, %outer4.body ], [ %ym1.4phi, %inner4.body ]

  %row.off4 = mul nsw i64 %i4, %hz
  %out.ptr4 = getelementptr inbounds float, ptr %imgOut, i64 %row.off4
  %out.ptr4.j = getelementptr inbounds float, ptr %out.ptr4, i64 %j4
  %xin4 = load float, ptr %out.ptr4.j, align 4

  %m4.1 = fmul float %a5, %xin4
  %m4.2 = fmul float %a6, %tm1.phi
  %s4.1 = fadd float %m4.1, %m4.2
  %m4.3 = fmul float %b1, %ym1.4phi
  %s4.2 = fadd float %s4.1, %m4.3
  %m4.4 = fmul float %b2, %ym2.4phi
  %yout4 = fadd float %s4.2, %m4.4

  %y1.ptr4 = getelementptr inbounds float, ptr %y1, i64 %row.off4
  %y1.ptr4.j = getelementptr inbounds float, ptr %y1.ptr4, i64 %j4
  store float %yout4, ptr %y1.ptr4.j, align 4

  %tin4 = load float, ptr %out.ptr4.j, align 4

  %i4.next = add nsw i64 %i4, 1
  %cmp.inner4 = icmp slt i64 %i4.next, %wz
  br i1 %cmp.inner4, label %inner4.body, label %outer4.inc

outer4.inc:
  %j4.next = add nsw i64 %j4, 1
  %cmp.outer4 = icmp slt i64 %j4.next, %hz
  br i1 %cmp.outer4, label %outer4.body, label %for.end156

for.end156:                                         ; preds = %outer4.inc, %outer4.preheader, %for.end121
  br i1 %cmp.h.pos, label %outer5.preheader, label %for.end188

outer5.preheader:
  br i1 %cmp.w.pos, label %outer5.body.preheader, label %for.end188

outer5.body.preheader:
  br label %outer5.body

outer5.body:                                        ; preds = %outer5.inc, %outer5.body.preheader
  %j5 = phi i64 [ 0, %outer5.body.preheader ], [ %j5.next, %outer5.inc ]
  %wm1 = sub nsw i64 %wz, 1
  br label %inner5.body

inner5.body:                                        ; preds = %inner5.body, %outer5.body
  %i5 = phi i64 [ %wm1, %outer5.body ], [ %i5.next, %inner5.body ]
  %tp1.phi = phi float [ 0.000000e+00, %outer5.body ], [ %tin5, %inner5.body ]
  %tp2.phi = phi float [ 0.000000e+00, %outer5.body ], [ %tp1.phi, %inner5.body ]
  %yp1.5phi = phi float [ 0.000000e+00, %outer5.body ], [ %yin5, %inner5.body ]
  %yp2.5phi = phi float [ 0.000000e+00, %outer5.body ], [ %yp1.5phi, %inner5.body ]

  %m5.1 = fmul float %a7, %tp1.phi
  %m5.2 = fmul float %a8, %tp2.phi
  %s5.1 = fadd float %m5.1, %m5.2
  %m5.3 = fmul float %b1, %yp1.5phi
  %s5.2 = fadd float %s5.1, %m5.3
  %m5.4 = fmul float %b2, %yp2.5phi
  %yout5 = fadd float %s5.2, %m5.4

  %row.off5 = mul nsw i64 %i5, %hz
  %y2.ptr5 = getelementptr inbounds float, ptr %y2, i64 %row.off5
  %y2.ptr5.j = getelementptr inbounds float, ptr %y2.ptr5, i64 %j5
  store float %yout5, ptr %y2.ptr5.j, align 4

  %out.ptr5 = getelementptr inbounds float, ptr %imgOut, i64 %row.off5
  %out.ptr5.j = getelementptr inbounds float, ptr %out.ptr5, i64 %j5
  %tin5 = load float, ptr %out.ptr5.j, align 4

  %yin5 = load float, ptr %y2.ptr5.j, align 4

  %i5.next = add nsw i64 %i5, -1
  %cmp.inner5 = icmp sge i64 %i5.next, 0
  br i1 %cmp.inner5, label %inner5.body, label %outer5.inc

outer5.inc:
  %j5.next = add nsw i64 %j5, 1
  %cmp.outer5 = icmp slt i64 %j5.next, %hz
  br i1 %cmp.outer5, label %outer5.body, label %for.end188

for.end188:                                         ; preds = %outer5.inc, %outer5.preheader, %for.end156
  br i1 %cmp.w.pos, label %outer6.preheader, label %for.end214

outer6.preheader:
  br i1 %cmp.h.pos, label %outer6.body.preheader, label %for.end214

outer6.body.preheader:
  br label %outer6.body

outer6.body:                                        ; preds = %outer6.inc, %outer6.body.preheader
  %i6 = phi i64 [ 0, %outer6.body.preheader ], [ %i6.next, %outer6.inc ]
  %row.off6 = mul nsw i64 %i6, %hz
  %y1.rowbase6 = getelementptr inbounds float, ptr %y1, i64 %row.off6
  %y2.rowbase6 = getelementptr inbounds float, ptr %y2, i64 %row.off6
  %imgOut.rowbase6 = getelementptr inbounds float, ptr %imgOut, i64 %row.off6
  br label %inner6.body

inner6.body:                                        ; preds = %inner6.body, %outer6.body
  %j6 = phi i64 [ 0, %outer6.body ], [ %j6.next, %inner6.body ]

  %y1.ptr6 = getelementptr inbounds float, ptr %y1.rowbase6, i64 %j6
  %v1.6 = load float, ptr %y1.ptr6, align 4
  %y2.ptr6 = getelementptr inbounds float, ptr %y2.rowbase6, i64 %j6
  %v2.6 = load float, ptr %y2.ptr6, align 4
  %add6 = fadd float %v1.6, %v2.6
  %mul6 = fmul float %c2, %add6

  %out.ptr6 = getelementptr inbounds float, ptr %imgOut.rowbase6, i64 %j6
  store float %mul6, ptr %out.ptr6, align 4

  %j6.next = add nsw i64 %j6, 1
  %cmp.inner6 = icmp slt i64 %j6.next, %hz
  br i1 %cmp.inner6, label %inner6.body, label %outer6.inc

outer6.inc:
  %i6.next = add nsw i64 %i6, 1
  %cmp.outer6 = icmp slt i64 %i6.next, %wz
  br i1 %cmp.outer6, label %outer6.body, label %for.end214

for.end214:                                         ; preds = %outer6.inc, %outer6.preheader, %for.end188
  ret void
}

; Function Attrs: nounwind
declare float @expf(float noundef) #1

; Function Attrs: nounwind
declare float @powf(float noundef, float noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
