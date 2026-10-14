; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %cmp.w = icmp sgt i32 %w, 0
  %cmp.h = icmp sgt i32 %h, 0
  %wi64 = sext i32 %w to i64
  %hi64 = sext i32 %h to i64

  %fneg = fneg float %alpha
  %call = call float @expf(float noundef %fneg) #2
  %sub = fsub float 1.000000e+00, %call
  %call9 = call float @expf(float noundef %fneg) #2
  %sub10 = fsub float 1.000000e+00, %call9
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %call13 = call float @expf(float noundef %fneg) #2
  %mul14 = fmul float %mul11, %call13
  %add15 = fadd float 1.000000e+00, %mul14
  %call17 = call float @expf(float noundef %mul11) #2
  %sub18 = fsub float %add15, %call17
  %k = fdiv float %mul, %sub18

  %a1 = fadd float %k, 0.000000e+00
  %a5 = fadd float %k, 0.000000e+00

  %call20 = call float @expf(float noundef %fneg) #2
  %mul21 = fmul float %k, %call20
  %sub22 = fsub float %alpha, 1.000000e+00
  %mul23 = fmul float %mul21, %sub22
  %a2 = fadd float %mul23, 0.000000e+00
  %a6 = fadd float %mul23, 0.000000e+00

  %call25 = call float @expf(float noundef %fneg) #2
  %mul26 = fmul float %k, %call25
  %add27 = fadd float %alpha, 1.000000e+00
  %mul28 = fmul float %mul26, %add27
  %a3 = fadd float %mul28, 0.000000e+00
  %a7 = fadd float %mul28, 0.000000e+00

  %kneg = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %call31 = call float @expf(float noundef %mul30) #2
  %mul32 = fmul float %kneg, %call31
  %a4 = fadd float %mul32, 0.000000e+00
  %a8 = fadd float %mul32, 0.000000e+00

  %fneg33 = fneg float %alpha
  %call34 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2
  %b1 = fadd float %call34, 0.000000e+00

  %mul35 = fmul float -2.000000e+00, %alpha
  %call36 = call float @expf(float noundef %mul35) #2
  %b2 = fneg float %call36

  %c1 = fadd float 1.000000e+00, 0.000000e+00
  %c2 = fadd float 1.000000e+00, 0.000000e+00

  br i1 %cmp.w, label %outer1.preheader, label %stage1.done

outer1.preheader:
  br i1 %cmp.h, label %outer1.body.lr, label %stage1.done

outer1.body.lr:
  br label %outer1.body

outer1.body:                                        ; loop over i
  %i1 = phi i64 [ 0, %outer1.body.lr ], [ %i1.next, %outer1.inc ]
  %rowIn1 = getelementptr inbounds float, ptr %imgIn, i64 %i1
  %rowY1a = getelementptr inbounds float, ptr %y1, i64 %i1
  ; base row pointers need multiply by h, done via GEP with stride
  %rowInOff = mul nsw i64 %i1, %hi64
  %rowInPtr = getelementptr inbounds float, ptr %imgIn, i64 %rowInOff
  %rowY1Off = mul nsw i64 %i1, %hi64
  %rowY1Ptr = getelementptr inbounds float, ptr %y1, i64 %rowY1Off
  br label %inner1.body

inner1.body:                                        ; loop over j
  %j1 = phi i64 [ 0, %outer1.body ], [ %j1.next, %inner1.body ]
  %ym1.1 = phi float [ 0.000000e+00, %outer1.body ], [ %ym1.1.next, %inner1.body ]
  %ym2.1 = phi float [ 0.000000e+00, %outer1.body ], [ %ym1.1, %inner1.body ]
  %xm1.1 = phi float [ 0.000000e+00, %outer1.body ], [ %xcur1, %inner1.body ]

  %pIn1 = getelementptr inbounds float, ptr %rowInPtr, i64 %j1
  %xcur1 = load float, ptr %pIn1, align 4

  %t1a = fmul float %a1, %xcur1
  %t1b = fmul float %a2, %xm1.1
  %t1c = fadd float %t1a, %t1b
  %t1d = fmul float %b1, %ym1.1
  %t1e = fadd float %t1c, %t1d
  %t1f = fmul float %b2, %ym2.1
  %t1g = fadd float %t1e, %t1f

  %pY1 = getelementptr inbounds float, ptr %rowY1Ptr, i64 %j1
  store float %t1g, ptr %pY1, align 4

  %ym1.1.next = fadd float %t1g, 0.000000e+00

  %j1.next = add nsw i64 %j1, 1
  %cmp.inner1 = icmp slt i64 %j1.next, %hi64
  br i1 %cmp.inner1, label %inner1.body, label %outer1.inc

outer1.inc:
  %i1.next = add nsw i64 %i1, 1
  %cmp.outer1 = icmp slt i64 %i1.next, %wi64
  br i1 %cmp.outer1, label %outer1.body, label %stage1.done

stage1.done:
  br i1 %cmp.w, label %outer2.preheader, label %stage2.done

outer2.preheader:
  br i1 %cmp.h, label %outer2.body.lr, label %stage2.done

outer2.body.lr:
  %hm1 = add nsw i64 %hi64, -1
  br label %outer2.body

outer2.body:
  %i2 = phi i64 [ 0, %outer2.body.lr ], [ %i2.next, %outer2.inc ]
  %rowInOff2 = mul nsw i64 %i2, %hi64
  %rowInPtr2 = getelementptr inbounds float, ptr %imgIn, i64 %rowInOff2
  %rowY2Off = mul nsw i64 %i2, %hi64
  %rowY2Ptr = getelementptr inbounds float, ptr %y2, i64 %rowY2Off
  br label %inner2.body

inner2.body:
  %j2 = phi i64 [ %hm1, %outer2.body ], [ %j2.next, %inner2.body ]
  %yp1.2 = phi float [ 0.000000e+00, %outer2.body ], [ %val2, %inner2.body ]
  %yp2.2 = phi float [ 0.000000e+00, %outer2.body ], [ %yp1.2, %inner2.body ]
  %xp1.2 = phi float [ 0.000000e+00, %outer2.body ], [ %xcur2, %inner2.body ]
  %xp2.2 = phi float [ 0.000000e+00, %outer2.body ], [ %xp1.2, %inner2.body ]

  %t2a = fmul float %a3, %xp1.2
  %t2b = fmul float %a4, %xp2.2
  %t2c = fadd float %t2a, %t2b
  %t2d = fmul float %b1, %yp1.2
  %t2e = fadd float %t2c, %t2d
  %t2f = fmul float %b2, %yp2.2
  %val2 = fadd float %t2e, %t2f

  %pY2 = getelementptr inbounds float, ptr %rowY2Ptr, i64 %j2
  store float %val2, ptr %pY2, align 4

  %pIn2 = getelementptr inbounds float, ptr %rowInPtr2, i64 %j2
  %xcur2 = load float, ptr %pIn2, align 4

  %j2.next = add nsw i64 %j2, -1
  %cmp.inner2 = icmp sge i64 %j2.next, 0
  br i1 %cmp.inner2, label %inner2.body, label %outer2.inc

outer2.inc:
  %i2.next = add nsw i64 %i2, 1
  %cmp.outer2 = icmp slt i64 %i2.next, %wi64
  br i1 %cmp.outer2, label %outer2.body, label %stage2.done

stage2.done:
  br i1 %cmp.w, label %outer3.preheader, label %stage3.done

outer3.preheader:
  br i1 %cmp.h, label %outer3.body.lr, label %stage3.done

outer3.body.lr:
  br label %outer3.body

outer3.body:
  %i3 = phi i64 [ 0, %outer3.body.lr ], [ %i3.next, %outer3.inc ]
  %rowY1Off3 = mul nsw i64 %i3, %hi64
  %rowY1Ptr3 = getelementptr inbounds float, ptr %y1, i64 %rowY1Off3
  %rowY2Off3 = mul nsw i64 %i3, %hi64
  %rowY2Ptr3 = getelementptr inbounds float, ptr %y2, i64 %rowY2Off3
  %rowOutOff3 = mul nsw i64 %i3, %hi64
  %rowOutPtr3 = getelementptr inbounds float, ptr %imgOut, i64 %rowOutOff3
  br label %inner3.body

inner3.body:
  %j3 = phi i64 [ 0, %outer3.body ], [ %j3.next, %inner3.body ]
  %pY1_3 = getelementptr inbounds float, ptr %rowY1Ptr3, i64 %j3
  %v1_3 = load float, ptr %pY1_3, align 4
  %pY2_3 = getelementptr inbounds float, ptr %rowY2Ptr3, i64 %j3
  %v2_3 = load float, ptr %pY2_3, align 4
  %sum3 = fadd float %v1_3, %v2_3
  %mul3 = fmul float %c1, %sum3
  %pOut3 = getelementptr inbounds float, ptr %rowOutPtr3, i64 %j3
  store float %mul3, ptr %pOut3, align 4

  %j3.next = add nsw i64 %j3, 1
  %cmp.inner3 = icmp slt i64 %j3.next, %hi64
  br i1 %cmp.inner3, label %inner3.body, label %outer3.inc

outer3.inc:
  %i3.next = add nsw i64 %i3, 1
  %cmp.outer3 = icmp slt i64 %i3.next, %wi64
  br i1 %cmp.outer3, label %outer3.body, label %stage3.done

stage3.done:
  br i1 %cmp.h, label %outer4.preheader, label %stage4.done

outer4.preheader:
  br i1 %cmp.w, label %outer4.body.lr, label %stage4.done

outer4.body.lr:
  br label %outer4.body

outer4.body:                                        ; loop over j
  %j4 = phi i64 [ 0, %outer4.body.lr ], [ %j4.next, %outer4.inc ]
  br label %inner4.body

inner4.body:                                        ; loop over i
  %i4 = phi i64 [ 0, %outer4.body ], [ %i4.next, %inner4.body ]
  %tm1.4 = phi float [ 0.000000e+00, %outer4.body ], [ %vout4, %inner4.body ]
  %ym1.4 = phi float [ 0.000000e+00, %outer4.body ], [ %val4, %inner4.body ]
  %ym2.4 = phi float [ 0.000000e+00, %outer4.body ], [ %ym1.4, %inner4.body ]

  %rowOutOff4 = mul nsw i64 %i4, %hi64
  %rowOutPtr4 = getelementptr inbounds float, ptr %imgOut, i64 %rowOutOff4
  %pOut4 = getelementptr inbounds float, ptr %rowOutPtr4, i64 %j4
  %vout4 = load float, ptr %pOut4, align 4

  %t4a = fmul float %a5, %vout4
  %t4b = fmul float %a6, %tm1.4
  %t4c = fadd float %t4a, %t4b
  %t4d = fmul float %b1, %ym1.4
  %t4e = fadd float %t4c, %t4d
  %t4f = fmul float %b2, %ym2.4
  %val4 = fadd float %t4e, %t4f

  %rowY1Off4 = mul nsw i64 %i4, %hi64
  %rowY1Ptr4 = getelementptr inbounds float, ptr %y1, i64 %rowY1Off4
  %pY1_4 = getelementptr inbounds float, ptr %rowY1Ptr4, i64 %j4
  store float %val4, ptr %pY1_4, align 4

  %i4.next = add nsw i64 %i4, 1
  %cmp.inner4 = icmp slt i64 %i4.next, %wi64
  br i1 %cmp.inner4, label %inner4.body, label %outer4.inc

outer4.inc:
  %j4.next = add nsw i64 %j4, 1
  %cmp.outer4 = icmp slt i64 %j4.next, %hi64
  br i1 %cmp.outer4, label %outer4.body, label %stage4.done

stage4.done:
  br i1 %cmp.h, label %outer5.preheader, label %stage5.done

outer5.preheader:
  br i1 %cmp.w, label %outer5.body.lr, label %stage5.done

outer5.body.lr:
  %wm1 = add nsw i64 %wi64, -1
  br label %outer5.body

outer5.body:                                        ; loop over j
  %j5 = phi i64 [ 0, %outer5.body.lr ], [ %j5.next, %outer5.inc ]
  br label %inner5.body

inner5.body:                                        ; loop over i, decreasing
  %i5 = phi i64 [ %wm1, %outer5.body ], [ %i5.next, %inner5.body ]
  %tp1.5 = phi float [ 0.000000e+00, %outer5.body ], [ %vout5, %inner5.body ]
  %tp2.5 = phi float [ 0.000000e+00, %outer5.body ], [ %tp1.5, %inner5.body ]
  %yp1.5 = phi float [ 0.000000e+00, %outer5.body ], [ %val5, %inner5.body ]
  %yp2.5 = phi float [ 0.000000e+00, %outer5.body ], [ %yp1.5, %inner5.body ]

  %t5a = fmul float %a7, %tp1.5
  %t5b = fmul float %a8, %tp2.5
  %t5c = fadd float %t5a, %t5b
  %t5d = fmul float %b1, %yp1.5
  %t5e = fadd float %t5c, %t5d
  %t5f = fmul float %b2, %yp2.5
  %val5 = fadd float %t5e, %t5f

  %rowY2Off5 = mul nsw i64 %i5, %hi64
  %rowY2Ptr5 = getelementptr inbounds float, ptr %y2, i64 %rowY2Off5
  %pY2_5 = getelementptr inbounds float, ptr %rowY2Ptr5, i64 %j5
  store float %val5, ptr %pY2_5, align 4

  %rowOutOff5 = mul nsw i64 %i5, %hi64
  %rowOutPtr5 = getelementptr inbounds float, ptr %imgOut, i64 %rowOutOff5
  %pOut5 = getelementptr inbounds float, ptr %rowOutPtr5, i64 %j5
  %vout5 = load float, ptr %pOut5, align 4

  %i5.next = add nsw i64 %i5, -1
  %cmp.inner5 = icmp sge i64 %i5.next, 0
  br i1 %cmp.inner5, label %inner5.body, label %outer5.inc

outer5.inc:
  %j5.next = add nsw i64 %j5, 1
  %cmp.outer5 = icmp slt i64 %j5.next, %hi64
  br i1 %cmp.outer5, label %outer5.body, label %stage5.done

stage5.done:
  br i1 %cmp.w, label %outer6.preheader, label %stage6.done

outer6.preheader:
  br i1 %cmp.h, label %outer6.body.lr, label %stage6.done

outer6.body.lr:
  br label %outer6.body

outer6.body:
  %i6 = phi i64 [ 0, %outer6.body.lr ], [ %i6.next, %outer6.inc ]
  %rowY1Off6 = mul nsw i64 %i6, %hi64
  %rowY1Ptr6 = getelementptr inbounds float, ptr %y1, i64 %rowY1Off6
  %rowY2Off6 = mul nsw i64 %i6, %hi64
  %rowY2Ptr6 = getelementptr inbounds float, ptr %y2, i64 %rowY2Off6
  %rowOutOff6 = mul nsw i64 %i6, %hi64
  %rowOutPtr6 = getelementptr inbounds float, ptr %imgOut, i64 %rowOutOff6
  br label %inner6.body

inner6.body:
  %j6 = phi i64 [ 0, %outer6.body ], [ %j6.next, %inner6.body ]
  %pY1_6 = getelementptr inbounds float, ptr %rowY1Ptr6, i64 %j6
  %v1_6 = load float, ptr %pY1_6, align 4
  %pY2_6 = getelementptr inbounds float, ptr %rowY2Ptr6, i64 %j6
  %v2_6 = load float, ptr %pY2_6, align 4
  %sum6 = fadd float %v1_6, %v2_6
  %mul6 = fmul float %c2, %sum6
  %pOut6 = getelementptr inbounds float, ptr %rowOutPtr6, i64 %j6
  store float %mul6, ptr %pOut6, align 4

  %j6.next = add nsw i64 %j6, 1
  %cmp.inner6 = icmp slt i64 %j6.next, %hi64
  br i1 %cmp.inner6, label %inner6.body, label %outer6.inc

outer6.inc:
  %i6.next = add nsw i64 %i6, 1
  %cmp.outer6 = icmp slt i64 %i6.next, %wi64
  br i1 %cmp.outer6, label %outer6.body, label %stage6.done

stage6.done:
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
