; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %cmp.w0 = icmp sgt i32 %w, 0
  %cmp.h0 = icmp sgt i32 %h, 0
  %wz = sext i32 %w to i64
  %hz = sext i32 %h to i64

  %fneg = fneg float %alpha
  %call = call float @expf(float noundef %fneg) #2
  %sub = fsub float 1.000000e+00, %call
  %sub10 = fsub float 1.000000e+00, %call
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %mul14 = fmul float %mul11, %call
  %add15 = fadd float 1.000000e+00, %mul14
  %mul16 = fmul float 2.000000e+00, %alpha
  %call17 = call float @expf(float noundef %mul16) #2
  %sub18 = fsub float %add15, %call17
  %k = fdiv float %mul, %sub18

  %a1 = fmul float %k, 1.0
  %mul21 = fmul float %k, %call
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22

  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul21, %add27

  %fneg29 = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %call31 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %fneg29, %call31

  %fneg33 = fneg float %alpha
  %b1 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2

  %call36 = call float @expf(float noundef %mul30) #2
  %b2 = fneg float %call36

  %a5 = fmul float %k, 1.0
  %a6 = fmul float %mul21, %sub22
  %a7 = fmul float %mul21, %add27
  %a8 = fmul float %fneg29, %call31

  %c1 = fadd float 1.0, 0.0
  %c2 = fadd float 1.0, 0.0

  br i1 %cmp.w0, label %stage1.preheader, label %stage2.check

stage1.preheader:
  br label %stage1.i

stage1.i:                                         ; preds = %stage1.i.end, %stage1.preheader
  %i1 = phi i64 [ 0, %stage1.preheader ], [ %i1.next, %stage1.i.end ]
  %inRow1 = getelementptr inbounds float, ptr %imgIn, i64 %i1
  %inRowPtr1 = mul nsw i64 %i1, %hz
  %inRowBase1 = getelementptr inbounds float, ptr %imgIn, i64 %inRowPtr1
  %y1RowPtr1 = mul nsw i64 %i1, %hz
  %y1RowBase1 = getelementptr inbounds float, ptr %y1, i64 %y1RowPtr1
  br i1 %cmp.h0, label %stage1.j.preheader, label %stage1.i.end

stage1.j.preheader:
  br label %stage1.j

stage1.j:                                         ; preds = %stage1.j, %stage1.j.preheader
  %j1 = phi i64 [ 0, %stage1.j.preheader ], [ %j1.next, %stage1.j ]
  %ym1.1 = phi float [ 0.000000e+00, %stage1.j.preheader ], [ %ym1.next, %stage1.j ]
  %ym2.1 = phi float [ 0.000000e+00, %stage1.j.preheader ], [ %ym1.1, %stage1.j ]
  %xm1.1 = phi float [ 0.000000e+00, %stage1.j.preheader ], [ %curIn, %stage1.j ]

  %inElem1 = getelementptr inbounds float, ptr %inRowBase1, i64 %j1
  %curIn = load float, ptr %inElem1, align 4
  %m43 = fmul float %a1, %curIn
  %m44 = fmul float %a2, %xm1.1
  %ad45 = fadd float %m43, %m44
  %m46 = fmul float %b1, %ym1.1
  %ad47 = fadd float %ad45, %m46
  %m48 = fmul float %b2, %ym2.1
  %ad49 = fadd float %ad47, %m48

  %y1Elem1 = getelementptr inbounds float, ptr %y1RowBase1, i64 %j1
  store float %ad49, ptr %y1Elem1, align 4

  %ym1.next = phi float [ %ad49, %stage1.j ]
  %j1.next = add nsw i64 %j1, 1
  %j1.cmp = icmp slt i64 %j1.next, %hz
  br i1 %j1.cmp, label %stage1.j, label %stage1.i.end

stage1.i.end:                                     ; preds = %stage1.j, %stage1.i
  %i1.next = add nsw i64 %i1, 1
  %i1.cmp = icmp slt i64 %i1.next, %wz
  br i1 %i1.cmp, label %stage1.i, label %stage2.check

stage2.check:
  br i1 %cmp.w0, label %stage2.preheader, label %stage3.check

stage2.preheader:
  br label %stage2.i

stage2.i:                                         ; preds = %stage2.i.end, %stage2.preheader
  %i2 = phi i64 [ 0, %stage2.preheader ], [ %i2.next, %stage2.i.end ]
  %inRowPtr2 = mul nsw i64 %i2, %hz
  %inRowBase2 = getelementptr inbounds float, ptr %imgIn, i64 %inRowPtr2
  %y2RowPtr2 = mul nsw i64 %i2, %hz
  %y2RowBase2 = getelementptr inbounds float, ptr %y2, i64 %y2RowPtr2
  br i1 %cmp.h0, label %stage2.j.preheader, label %stage2.i.end

stage2.j.preheader:
  %hm1 = sub nsw i64 %hz, 1
  br label %stage2.j

stage2.j:                                         ; preds = %stage2.j, %stage2.j.preheader
  %j2 = phi i64 [ %hm1, %stage2.j.preheader ], [ %j2.next, %stage2.j ]
  %xp1.2 = phi float [ 0.000000e+00, %stage2.j.preheader ], [ %curIn2, %stage2.j ]
  %xp2.2 = phi float [ 0.000000e+00, %stage2.j.preheader ], [ %xp1.2, %stage2.j ]
  %yp1.2 = phi float [ 0.000000e+00, %stage2.j.preheader ], [ %ad78, %stage2.j ]
  %yp2.2 = phi float [ 0.000000e+00, %stage2.j.preheader ], [ %yp1.2, %stage2.j ]

  %m72 = fmul float %a3, %xp1.2
  %m73 = fmul float %a4, %xp2.2
  %ad74 = fadd float %m72, %m73
  %m75 = fmul float %b1, %yp1.2
  %ad76 = fadd float %ad74, %m75
  %m77 = fmul float %b2, %yp2.2
  %ad78 = fadd float %ad76, %m77

  %y2Elem2 = getelementptr inbounds float, ptr %y2RowBase2, i64 %j2
  store float %ad78, ptr %y2Elem2, align 4

  %inElem2 = getelementptr inbounds float, ptr %inRowBase2, i64 %j2
  %curIn2 = load float, ptr %inElem2, align 4

  %j2.next = sub nsw i64 %j2, 1
  %j2.cmp = icmp sge i64 %j2.next, 0
  br i1 %j2.cmp, label %stage2.j, label %stage2.i.end

stage2.i.end:                                     ; preds = %stage2.j, %stage2.i
  %i2.next = add nsw i64 %i2, 1
  %i2.cmp = icmp slt i64 %i2.next, %wz
  br i1 %i2.cmp, label %stage2.i, label %stage3.check

stage3.check:
  br i1 %cmp.w0, label %stage3.preheader, label %stage4.check

stage3.preheader:
  br label %stage3.i

stage3.i:                                         ; preds = %stage3.i.end, %stage3.preheader
  %i3 = phi i64 [ 0, %stage3.preheader ], [ %i3.next, %stage3.i.end ]
  %y1RowBase3 = getelementptr inbounds float, ptr %y1, i64 %i3
  %y1RowPtr3 = mul nsw i64 %i3, %hz
  %y1RowBase3b = getelementptr inbounds float, ptr %y1, i64 %y1RowPtr3
  %y2RowPtr3 = mul nsw i64 %i3, %hz
  %y2RowBase3 = getelementptr inbounds float, ptr %y2, i64 %y2RowPtr3
  %outRowPtr3 = mul nsw i64 %i3, %hz
  %outRowBase3 = getelementptr inbounds float, ptr %imgOut, i64 %outRowPtr3
  br i1 %cmp.h0, label %stage3.j.preheader, label %stage3.i.end

stage3.j.preheader:
  br label %stage3.j

stage3.j:                                         ; preds = %stage3.j, %stage3.j.preheader
  %j3 = phi i64 [ 0, %stage3.j.preheader ], [ %j3.next, %stage3.j ]

  %y1Elem3 = getelementptr inbounds float, ptr %y1RowBase3b, i64 %j3
  %v1 = load float, ptr %y1Elem3, align 4
  %y2Elem3 = getelementptr inbounds float, ptr %y2RowBase3, i64 %j3
  %v2 = load float, ptr %y2Elem3, align 4
  %ad110 = fadd float %v1, %v2
  %m111 = fmul float %c1, %ad110

  %outElem3 = getelementptr inbounds float, ptr %outRowBase3, i64 %j3
  store float %m111, ptr %outElem3, align 4

  %j3.next = add nsw i64 %j3, 1
  %j3.cmp = icmp slt i64 %j3.next, %hz
  br i1 %j3.cmp, label %stage3.j, label %stage3.i.end

stage3.i.end:                                     ; preds = %stage3.j, %stage3.i
  %i3.next = add nsw i64 %i3, 1
  %i3.cmp = icmp slt i64 %i3.next, %wz
  br i1 %i3.cmp, label %stage3.i, label %stage4.check

stage4.check:
  br i1 %cmp.h0, label %stage4.preheader, label %stage5.check

stage4.preheader:
  br label %stage4.j

stage4.j:                                         ; preds = %stage4.j.end, %stage4.preheader
  %j4 = phi i64 [ 0, %stage4.preheader ], [ %j4.next, %stage4.j.end ]
  br i1 %cmp.w0, label %stage4.i.preheader, label %stage4.j.end

stage4.i.preheader:
  br label %stage4.i

stage4.i:                                         ; preds = %stage4.i, %stage4.i.preheader
  %i4 = phi i64 [ 0, %stage4.i.preheader ], [ %i4.next, %stage4.i ]
  %tm1.4 = phi float [ 0.000000e+00, %stage4.i.preheader ], [ %curOut4, %stage4.i ]
  %ym1.4 = phi float [ 0.000000e+00, %stage4.i.preheader ], [ %ad138, %stage4.i ]
  %ym2.4 = phi float [ 0.000000e+00, %stage4.i.preheader ], [ %ym1.4, %stage4.i ]

  %outRowPtr4 = mul nsw i64 %i4, %hz
  %outRowBase4 = getelementptr inbounds float, ptr %imgOut, i64 %outRowPtr4
  %outElem4 = getelementptr inbounds float, ptr %outRowBase4, i64 %j4
  %curOut4 = load float, ptr %outElem4, align 4

  %m132 = fmul float %a5, %curOut4
  %m133 = fmul float %a6, %tm1.4
  %ad134 = fadd float %m132, %m133
  %m135 = fmul float %b1, %ym1.4
  %ad136 = fadd float %ad134, %m135
  %m137 = fmul float %b2, %ym2.4
  %ad138 = fadd float %ad136, %m137

  %y1RowPtr4 = mul nsw i64 %i4, %hz
  %y1RowBase4 = getelementptr inbounds float, ptr %y1, i64 %y1RowPtr4
  %y1Elem4 = getelementptr inbounds float, ptr %y1RowBase4, i64 %j4
  store float %ad138, ptr %y1Elem4, align 4

  %i4.next = add nsw i64 %i4, 1
  %i4.cmp = icmp slt i64 %i4.next, %wz
  br i1 %i4.cmp, label %stage4.i, label %stage4.j.end

stage4.j.end:                                     ; preds = %stage4.i, %stage4.j
  %j4.next = add nsw i64 %j4, 1
  %j4.cmp = icmp slt i64 %j4.next, %hz
  br i1 %j4.cmp, label %stage4.j, label %stage5.check

stage5.check:
  br i1 %cmp.h0, label %stage5.preheader, label %stage6.check

stage5.preheader:
  br label %stage5.j

stage5.j:                                         ; preds = %stage5.j.end, %stage5.preheader
  %j5 = phi i64 [ 0, %stage5.preheader ], [ %j5.next, %stage5.j.end ]
  br i1 %cmp.w0, label %stage5.i.preheader, label %stage5.j.end

stage5.i.preheader:
  %wm1 = sub nsw i64 %wz, 1
  br label %stage5.i

stage5.i:                                         ; preds = %stage5.i, %stage5.i.preheader
  %i5 = phi i64 [ %wm1, %stage5.i.preheader ], [ %i5.next, %stage5.i ]
  %tp1.5 = phi float [ 0.000000e+00, %stage5.i.preheader ], [ %curOut5, %stage5.i ]
  %tp2.5 = phi float [ 0.000000e+00, %stage5.i.preheader ], [ %tp1.5, %stage5.i ]
  %yp1.5 = phi float [ 0.000000e+00, %stage5.i.preheader ], [ %ad170, %stage5.i ]
  %yp2.5 = phi float [ 0.000000e+00, %stage5.i.preheader ], [ %yp1.5, %stage5.i ]

  %m164 = fmul float %a7, %tp1.5
  %m165 = fmul float %a8, %tp2.5
  %ad166 = fadd float %m164, %m165
  %m167 = fmul float %b1, %yp1.5
  %ad168 = fadd float %ad166, %m167
  %m169 = fmul float %b2, %yp2.5
  %ad170 = fadd float %ad168, %m169

  %y2RowPtr5 = mul nsw i64 %i5, %hz
  %y2RowBase5 = getelementptr inbounds float, ptr %y2, i64 %y2RowPtr5
  %y2Elem5 = getelementptr inbounds float, ptr %y2RowBase5, i64 %j5
  store float %ad170, ptr %y2Elem5, align 4

  %outRowPtr5 = mul nsw i64 %i5, %hz
  %outRowBase5 = getelementptr inbounds float, ptr %imgOut, i64 %outRowPtr5
  %outElem5 = getelementptr inbounds float, ptr %outRowBase5, i64 %j5
  %curOut5 = load float, ptr %outElem5, align 4

  %i5.next = sub nsw i64 %i5, 1
  %i5.cmp = icmp sge i64 %i5.next, 0
  br i1 %i5.cmp, label %stage5.i, label %stage5.j.end

stage5.j.end:                                     ; preds = %stage5.i, %stage5.j
  %j5.next = add nsw i64 %j5, 1
  %j5.cmp = icmp slt i64 %j5.next, %hz
  br i1 %j5.cmp, label %stage5.j, label %stage6.check

stage6.check:
  br i1 %cmp.w0, label %stage6.preheader, label %exit

stage6.preheader:
  br label %stage6.i

stage6.i:                                         ; preds = %stage6.i.end, %stage6.preheader
  %i6 = phi i64 [ 0, %stage6.preheader ], [ %i6.next, %stage6.i.end ]
  %y1RowPtr6 = mul nsw i64 %i6, %hz
  %y1RowBase6 = getelementptr inbounds float, ptr %y1, i64 %y1RowPtr6
  %y2RowPtr6 = mul nsw i64 %i6, %hz
  %y2RowBase6 = getelementptr inbounds float, ptr %y2, i64 %y2RowPtr6
  %outRowPtr6 = mul nsw i64 %i6, %hz
  %outRowBase6 = getelementptr inbounds float, ptr %imgOut, i64 %outRowPtr6
  br i1 %cmp.h0, label %stage6.j.preheader, label %stage6.i.end

stage6.j.preheader:
  br label %stage6.j

stage6.j:                                         ; preds = %stage6.j, %stage6.j.preheader
  %j6 = phi i64 [ 0, %stage6.j.preheader ], [ %j6.next, %stage6.j ]

  %y1Elem6 = getelementptr inbounds float, ptr %y1RowBase6, i64 %j6
  %v1b = load float, ptr %y1Elem6, align 4
  %y2Elem6 = getelementptr inbounds float, ptr %y2RowBase6, i64 %j6
  %v2b = load float, ptr %y2Elem6, align 4
  %ad203 = fadd float %v1b, %v2b
  %m204 = fmul float %c2, %ad203

  %outElem6 = getelementptr inbounds float, ptr %outRowBase6, i64 %j6
  store float %m204, ptr %outElem6, align 4

  %j6.next = add nsw i64 %j6, 1
  %j6.cmp = icmp slt i64 %j6.next, %hz
  br i1 %j6.cmp, label %stage6.j, label %stage6.i.end

stage6.i.end:                                     ; preds = %stage6.j, %stage6.i
  %i6.next = add nsw i64 %i6, 1
  %i6.cmp = icmp slt i64 %i6.next, %wz
  br i1 %i6.cmp, label %stage6.i, label %exit

exit:
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
