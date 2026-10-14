; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %wz = sext i32 %w to i64
  %hz = sext i32 %h to i64

  %fneg = fneg float %alpha
  %e1 = call float @expf(float noundef %fneg) #2
  %sub = fsub float 1.000000e+00, %e1
  %sub10 = fsub float 1.000000e+00, %e1
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %mul14 = fmul float %mul11, %e1
  %add15 = fadd float 1.000000e+00, %mul14
  %mul16 = fmul float 2.000000e+00, %alpha
  %call17 = call float @expf(float noundef %mul16) #2
  %sub18 = fsub float %add15, %call17
  %k = fdiv float %mul, %sub18

  %a1 = fmul float %k, 1.000000e+00
  %mul21 = fmul float %k, %e1
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22

  %mul26 = fmul float %k, %e1
  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul26, %add27

  %fneg29 = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %call31 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %fneg29, %call31

  %fneg33 = fneg float %alpha
  %b1 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2

  %mul35 = fmul float -2.000000e+00, %alpha
  %call36 = call float @expf(float noundef %mul35) #2
  %b2 = fneg float %call36

  %c1 = fadd float 0.0, 1.000000e+00
  %c2 = fadd float 0.0, 1.000000e+00

  %a5 = fadd float %a1, 0.0
  %a6 = fadd float %a2, 0.0
  %a7 = fadd float %a3, 0.0
  %a8 = fadd float %a4, 0.0

  br label %for.body.1.preheader

for.body.1.preheader:
  %wcmp0 = icmp slt i32 0, %w
  br i1 %wcmp0, label %for.body.1.ph, label %for.end64

for.body.1.ph:
  br label %for.body.1

for.body.1:                                       ; loop over i for pass 1
  %i1 = phi i32 [ 0, %for.body.1.ph ], [ %inc63, %for.inc62 ]
  %hcmp0 = icmp slt i32 0, %h
  br i1 %hcmp0, label %for.body40.ph, label %for.end.1

for.body40.ph:
  %i1z = sext i32 %i1 to i64
  %rowIn1 = mul nsw i64 %i1z, %hz
  %rowY1 = mul nsw i64 %i1z, %hz
  br label %for.body40

for.body40:
  %j1 = phi i32 [ 0, %for.body40.ph ], [ %incj1, %for.body40 ]
  %xm1v = phi float [ 0.000000e+00, %for.body40.ph ], [ %xin, %for.body40 ]
  %ym1v = phi float [ 0.000000e+00, %for.body40.ph ], [ %y1out, %for.body40 ]
  %ym2v = phi float [ 0.000000e+00, %for.body40.ph ], [ %ym1v, %for.body40 ]

  %j1z = sext i32 %j1 to i64
  %inIdx = add nsw i64 %rowIn1, %j1z
  %inPtr = getelementptr inbounds float, ptr %imgIn, i64 %inIdx
  %xin = load float, ptr %inPtr, align 4

  %m43 = fmul float %a1, %xin
  %m44 = fmul float %a2, %xm1v
  %s45 = fadd float %m43, %m44
  %m46 = fmul float %b1, %ym1v
  %s47 = fadd float %s45, %m46
  %m48 = fmul float %b2, %ym2v
  %s49 = fadd float %s47, %m48

  %y1Idx = add nsw i64 %rowY1, %j1z
  %y1Ptr = getelementptr inbounds float, ptr %y1, i64 %y1Idx
  store float %s49, ptr %y1Ptr, align 4

  %y1out = load float, ptr %y1Ptr, align 4

  %incj1 = add nsw i32 %j1, 1
  %cmpj1 = icmp slt i32 %incj1, %h
  br i1 %cmpj1, label %for.body40, label %for.end.1

for.end.1:
  br label %for.inc62

for.inc62:
  %inc63 = add nsw i32 %i1, 1
  %cmpi1 = icmp slt i32 %inc63, %w
  br i1 %cmpi1, label %for.body.1, label %for.end64

for.end64:
  br label %for.cond65.preheader

for.cond65.preheader:
  %wcmp1 = icmp slt i32 0, %w
  br i1 %wcmp1, label %for.body67.ph, label %for.end95

for.body67.ph:
  br label %for.body67

for.body67:                                       ; loop over i for pass 2
  %i2 = phi i32 [ 0, %for.body67.ph ], [ %inc94, %for.inc93 ]
  %hgt0 = icmp sgt i32 %h, 0
  br i1 %hgt0, label %for.body71.ph, label %for.end92

for.body71.ph:
  %i2z = sext i32 %i2 to i64
  %rowIn2 = mul nsw i64 %i2z, %hz
  %rowY2b = mul nsw i64 %i2z, %hz
  %jstart = sub nsw i32 %h, 1
  br label %for.body71

for.body71:
  %j2 = phi i32 [ %jstart, %for.body71.ph ], [ %decj2, %for.body71 ]
  %xp1v = phi float [ 0.000000e+00, %for.body71.ph ], [ %xp1n, %for.body71 ]
  %xp2v = phi float [ 0.000000e+00, %for.body71.ph ], [ %xp1v, %for.body71 ]
  %yp1v = phi float [ 0.000000e+00, %for.body71.ph ], [ %yp1n, %for.body71 ]
  %yp2v = phi float [ 0.000000e+00, %for.body71.ph ], [ %yp1v, %for.body71 ]

  %m72 = fmul float %a3, %xp1v
  %m73 = fmul float %a4, %xp2v
  %s74 = fadd float %m72, %m73
  %m75 = fmul float %b1, %yp1v
  %s76 = fadd float %s74, %m75
  %m77 = fmul float %b2, %yp2v
  %s78 = fadd float %s76, %m77

  %j2z = sext i32 %j2 to i64
  %y2Idx = add nsw i64 %rowY2b, %j2z
  %y2Ptr = getelementptr inbounds float, ptr %y2, i64 %y2Idx
  store float %s78, ptr %y2Ptr, align 4

  %inIdx2 = add nsw i64 %rowIn2, %j2z
  %inPtr2 = getelementptr inbounds float, ptr %imgIn, i64 %inIdx2
  %xp1n = load float, ptr %inPtr2, align 4

  %yp1n = load float, ptr %y2Ptr, align 4

  %decj2 = add nsw i32 %j2, -1
  %cmpj2 = icmp sge i32 %decj2, 0
  br i1 %cmpj2, label %for.body71, label %for.end92

for.end92:
  br label %for.inc93

for.inc93:
  %inc94 = add nsw i32 %i2, 1
  %cmpi2 = icmp slt i32 %inc94, %w
  br i1 %cmpi2, label %for.body67, label %for.end95

for.end95:
  br label %for.cond96.preheader

for.cond96.preheader:
  %wcmp2 = icmp slt i32 0, %w
  br i1 %wcmp2, label %for.body98.ph, label %for.end121

for.body98.ph:
  br label %for.body98

for.body98:                                       ; loop over i for combine pass 1
  %i3 = phi i32 [ 0, %for.body98.ph ], [ %inc120, %for.inc119 ]
  %hcmp2 = icmp slt i32 0, %h
  br i1 %hcmp2, label %for.body101.ph, label %for.end118

for.body101.ph:
  %i3z = sext i32 %i3 to i64
  %rowY1c = mul nsw i64 %i3z, %hz
  %rowY2c = mul nsw i64 %i3z, %hz
  %rowOutc = mul nsw i64 %i3z, %hz
  br label %for.body101

for.body101:
  %j3 = phi i32 [ 0, %for.body101.ph ], [ %incj3, %for.body101 ]
  %j3z = sext i32 %j3 to i64

  %y1Idx3 = add nsw i64 %rowY1c, %j3z
  %y1Ptr3 = getelementptr inbounds float, ptr %y1, i64 %y1Idx3
  %v1 = load float, ptr %y1Ptr3, align 4

  %y2Idx3 = add nsw i64 %rowY2c, %j3z
  %y2Ptr3 = getelementptr inbounds float, ptr %y2, i64 %y2Idx3
  %v2 = load float, ptr %y2Ptr3, align 4

  %sum3 = fadd float %v1, %v2
  %mul111 = fmul float %c1, %sum3

  %outIdx3 = add nsw i64 %rowOutc, %j3z
  %outPtr3 = getelementptr inbounds float, ptr %imgOut, i64 %outIdx3
  store float %mul111, ptr %outPtr3, align 4

  %incj3 = add nsw i32 %j3, 1
  %cmpj3 = icmp slt i32 %incj3, %h
  br i1 %cmpj3, label %for.body101, label %for.end118

for.end118:
  br label %for.inc119

for.inc119:
  %inc120 = add nsw i32 %i3, 1
  %cmpi3 = icmp slt i32 %inc120, %w
  br i1 %cmpi3, label %for.body98, label %for.end121

for.end121:
  br label %for.cond122.preheader

for.cond122.preheader:
  %hcmp3 = icmp slt i32 0, %h
  br i1 %hcmp3, label %for.body124.ph, label %for.end156

for.body124.ph:
  br label %for.body124

for.body124:                                      ; loop over j for pass 3
  %j4 = phi i32 [ 0, %for.body124.ph ], [ %incj4, %for.inc154 ]
  %wgt0 = icmp sgt i32 %w, 0
  br i1 %wgt0, label %for.body127.ph, label %for.end153

for.body127.ph:
  %j4z = sext i32 %j4 to i64
  br label %for.body127

for.body127:
  %i4 = phi i32 [ 0, %for.body127.ph ], [ %inci4, %for.body127 ]
  %tm1v = phi float [ 0.000000e+00, %for.body127.ph ], [ %tv, %for.body127 ]
  %ym1v4 = phi float [ 0.000000e+00, %for.body127.ph ], [ %y1out4, %for.body127 ]
  %ym2v4 = phi float [ 0.000000e+00, %for.body127.ph ], [ %ym1v4, %for.body127 ]

  %i4z = sext i32 %i4 to i64
  %rowOut4 = mul nsw i64 %i4z, %hz
  %outIdx4 = add nsw i64 %rowOut4, %j4z
  %outPtr4 = getelementptr inbounds float, ptr %imgOut, i64 %outIdx4
  %tv = load float, ptr %outPtr4, align 4

  %m132 = fmul float %a5, %tv
  %m133 = fmul float %a6, %tm1v
  %s134 = fadd float %m132, %m133
  %m135 = fmul float %b1, %ym1v4
  %s136 = fadd float %s134, %m135
  %m137 = fmul float %b2, %ym2v4
  %s138 = fadd float %s136, %m137

  %rowY14 = mul nsw i64 %i4z, %hz
  %y1Idx4 = add nsw i64 %rowY14, %j4z
  %y1Ptr4 = getelementptr inbounds float, ptr %y1, i64 %y1Idx4
  store float %s138, ptr %y1Ptr4, align 4

  %y1out4 = load float, ptr %y1Ptr4, align 4

  %inci4 = add nsw i32 %i4, 1
  %cmpi4 = icmp slt i32 %inci4, %w
  br i1 %cmpi4, label %for.body127, label %for.end153

for.end153:
  br label %for.inc154

for.inc154:
  %incj4 = add nsw i32 %j4, 1
  %cmpj4 = icmp slt i32 %incj4, %h
  br i1 %cmpj4, label %for.body124, label %for.end156

for.end156:
  br label %for.cond157.preheader

for.cond157.preheader:
  %hcmp4 = icmp slt i32 0, %h
  br i1 %hcmp4, label %for.body159.ph, label %for.end188

for.body159.ph:
  br label %for.body159

for.body159:                                      ; loop over j for pass 4
  %j5 = phi i32 [ 0, %for.body159.ph ], [ %incj5, %for.inc186 ]
  %wgt1 = icmp sgt i32 %w, 0
  br i1 %wgt1, label %for.body163.ph, label %for.end185

for.body163.ph:
  %j5z = sext i32 %j5 to i64
  %istart5 = sub nsw i32 %w, 1
  br label %for.body163

for.body163:
  %i5 = phi i32 [ %istart5, %for.body163.ph ], [ %deci5, %for.body163 ]
  %tp1v = phi float [ 0.000000e+00, %for.body163.ph ], [ %tp1n, %for.body163 ]
  %tp2v = phi float [ 0.000000e+00, %for.body163.ph ], [ %tp1v, %for.body163 ]
  %yp1v5 = phi float [ 0.000000e+00, %for.body163.ph ], [ %yp1n5, %for.body163 ]
  %yp2v5 = phi float [ 0.000000e+00, %for.body163.ph ], [ %yp1v5, %for.body163 ]

  %m164 = fmul float %a7, %tp1v
  %m165 = fmul float %a8, %tp2v
  %s166 = fadd float %m164, %m165
  %m167 = fmul float %b1, %yp1v5
  %s168 = fadd float %s166, %m167
  %m169 = fmul float %b2, %yp2v5
  %s170 = fadd float %s168, %m169

  %i5z = sext i32 %i5 to i64
  %rowY25 = mul nsw i64 %i5z, %hz
  %y2Idx5 = add nsw i64 %rowY25, %j5z
  %y2Ptr5 = getelementptr inbounds float, ptr %y2, i64 %y2Idx5
  store float %s170, ptr %y2Ptr5, align 4

  %rowOut5 = mul nsw i64 %i5z, %hz
  %outIdx5 = add nsw i64 %rowOut5, %j5z
  %outPtr5 = getelementptr inbounds float, ptr %imgOut, i64 %outIdx5
  %tp1n = load float, ptr %outPtr5, align 4

  %yp1n5 = load float, ptr %y2Ptr5, align 4

  %deci5 = add nsw i32 %i5, -1
  %cmpi5 = icmp sge i32 %deci5, 0
  br i1 %cmpi5, label %for.body163, label %for.end185

for.end185:
  br label %for.inc186

for.inc186:
  %incj5 = add nsw i32 %j5, 1
  %cmpj5 = icmp slt i32 %incj5, %h
  br i1 %cmpj5, label %for.body159, label %for.end188

for.end188:
  br label %for.cond189.preheader

for.cond189.preheader:
  %wcmp3 = icmp slt i32 0, %w
  br i1 %wcmp3, label %for.body191.ph, label %for.end214

for.body191.ph:
  br label %for.body191

for.body191:                                      ; loop over i for combine pass 2
  %i6 = phi i32 [ 0, %for.body191.ph ], [ %inc213, %for.inc212 ]
  %hcmp5 = icmp slt i32 0, %h
  br i1 %hcmp5, label %for.body194.ph, label %for.end211

for.body194.ph:
  %i6z = sext i32 %i6 to i64
  %rowY16 = mul nsw i64 %i6z, %hz
  %rowY26 = mul nsw i64 %i6z, %hz
  %rowOut6 = mul nsw i64 %i6z, %hz
  br label %for.body194

for.body194:
  %j6 = phi i32 [ 0, %for.body194.ph ], [ %incj6, %for.body194 ]
  %j6z = sext i32 %j6 to i64

  %y1Idx6 = add nsw i64 %rowY16, %j6z
  %y1Ptr6 = getelementptr inbounds float, ptr %y1, i64 %y1Idx6
  %v16 = load float, ptr %y1Ptr6, align 4

  %y2Idx6 = add nsw i64 %rowY26, %j6z
  %y2Ptr6 = getelementptr inbounds float, ptr %y2, i64 %y2Idx6
  %v26 = load float, ptr %y2Ptr6, align 4

  %sum6 = fadd float %v16, %v26
  %mul204 = fmul float %c2, %sum6

  %outIdx6 = add nsw i64 %rowOut6, %j6z
  %outPtr6 = getelementptr inbounds float, ptr %imgOut, i64 %outIdx6
  store float %mul204, ptr %outPtr6, align 4

  %incj6 = add nsw i32 %j6, 1
  %cmpj6 = icmp slt i32 %incj6, %h
  br i1 %cmpj6, label %for.body194, label %for.end211

for.end211:
  br label %for.inc212

for.inc212:
  %inc213 = add nsw i32 %i6, 1
  %cmpi6 = icmp slt i32 %inc213, %w
  br i1 %cmpi6, label %for.body191, label %for.end214

for.end214:
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
