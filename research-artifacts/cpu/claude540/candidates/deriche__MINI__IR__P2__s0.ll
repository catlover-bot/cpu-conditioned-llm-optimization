; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %cmp.wh = icmp sgt i32 %w, 0
  %cmp.hh = icmp sgt i32 %h, 0
  %wz = zext i32 %w to i64
  %hz = zext i32 %h to i64

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
  %mul16 = fmul float 2.000000e+00, %alpha
  %call17 = call float @expf(float noundef %mul16) #2
  %sub18 = fsub float %add15, %call17
  %k = fdiv float %mul, %sub18

  %a1 = fadd float %k, 0.000000e+00
  %call20 = call float @expf(float noundef %fneg) #2
  %mul21 = fmul float %k, %call20
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22

  %call25 = call float @expf(float noundef %fneg) #2
  %mul26 = fmul float %k, %call25
  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul26, %add27

  %fneg29 = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %call31 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %fneg29, %call31

  %fneg33 = fneg float %alpha
  %call34 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2
  %b1 = fadd float %call34, 0.000000e+00

  %mul35 = fmul float -2.000000e+00, %alpha
  %call36 = call float @expf(float noundef %mul35) #2
  %b2 = fneg float %call36

  %a5 = fadd float %k, 0.000000e+00
  %a6 = fadd float %a2, 0.000000e+00
  %a7 = fadd float %a3, 0.000000e+00
  %a8 = fadd float %a4, 0.000000e+00
  %c1 = fadd float 1.000000e+00, 0.000000e+00
  %c2 = fadd float 1.000000e+00, 0.000000e+00

  br i1 %cmp.wh, label %loop1.preheader, label %loop3check

loop1.preheader:
  br label %loop1.i

loop1.i:                                          ; preds = %loop1.inc, %loop1.preheader
  %i1 = phi i64 [ 0, %loop1.preheader ], [ %i1.next, %loop1.inc ]
  br i1 %cmp.hh, label %loop1.j.preheader, label %loop1.inc

loop1.j.preheader:
  %rowIn1 = getelementptr inbounds float, ptr %imgIn, i64 %i1
  %rowY1.1 = getelementptr inbounds float, ptr %y1, i64 %i1
  br label %loop1.j

loop1.j:                                          ; preds = %loop1.j.preheader, %loop1.jbody
  %j1 = phi i64 [ 0, %loop1.j.preheader ], [ %j1.next, %loop1.jbody ]
  %xm1.0 = phi float [ 0.000000e+00, %loop1.j.preheader ], [ %xin1, %loop1.jbody ]
  %ym1.0 = phi float [ 0.000000e+00, %loop1.j.preheader ], [ %y1val, %loop1.jbody ]
  %ym2.0 = phi float [ 0.000000e+00, %loop1.j.preheader ], [ %ym1.0, %loop1.jbody ]
  br label %loop1.jbody

loop1.jbody:
  %inOff1 = mul nsw i64 %i1, %wz
  %inPtr1 = getelementptr inbounds float, ptr %rowIn1, i64 %inOff1
  %inElemPtr1 = getelementptr inbounds float, ptr %inPtr1, i64 %j1
  %xin1 = load float, ptr %inElemPtr1, align 4

  %m43 = fmul float %a1, %xin1
  %m44 = fmul float %a2, %xm1.0
  %s45 = fadd float %m43, %m44
  %m46 = fmul float %b1, %ym1.0
  %s47 = fadd float %s45, %m46
  %m48 = fmul float %b2, %ym2.0
  %s49 = fadd float %s47, %m48

  %y1Off = mul nsw i64 %i1, %hz
  %y1Ptr = getelementptr inbounds float, ptr %rowY1.1, i64 %y1Off
  %y1ElemPtr = getelementptr inbounds float, ptr %y1Ptr, i64 %j1
  store float %s49, ptr %y1ElemPtr, align 4

  %y1val = load float, ptr %y1ElemPtr, align 4

  %j1.next = add nsw i64 %j1, 1
  %cmp1inner = icmp slt i64 %j1.next, %hz
  br i1 %cmp1inner, label %loop1.j, label %loop1.inc

loop1.inc:                                        ; preds = %loop1.jbody, %loop1.i
  %i1.next = add nsw i64 %i1, 1
  %cmp1outer = icmp slt i64 %i1.next, %wz
  br i1 %cmp1outer, label %loop1.i, label %loop3check

loop3check:                                       ; preds = %loop1.inc, %entry
  br i1 %cmp.wh, label %loop2.preheader, label %loop3check2

loop2.preheader:
  br label %loop2.i

loop2.i:                                          ; preds = %loop2.inc, %loop2.preheader
  %i2 = phi i64 [ 0, %loop2.preheader ], [ %i2.next, %loop2.inc ]
  br i1 %cmp.hh, label %loop2.j.preheader, label %loop2.inc

loop2.j.preheader:
  %rowIn2 = getelementptr inbounds float, ptr %imgIn, i64 %i2
  %rowY2.2 = getelementptr inbounds float, ptr %y2, i64 %i2
  %hm1 = sub nsw i64 %hz, 1
  br label %loop2.j

loop2.j:                                          ; preds = %loop2.j.preheader, %loop2.jbody
  %j2 = phi i64 [ %hm1, %loop2.j.preheader ], [ %j2.next, %loop2.jbody ]
  %xp1.0 = phi float [ 0.000000e+00, %loop2.j.preheader ], [ %xin2, %loop2.jbody ]
  %xp2.0 = phi float [ 0.000000e+00, %loop2.j.preheader ], [ %xp1.0, %loop2.jbody ]
  %yp1.0 = phi float [ 0.000000e+00, %loop2.j.preheader ], [ %y2val, %loop2.jbody ]
  %yp2.0 = phi float [ 0.000000e+00, %loop2.j.preheader ], [ %yp1.0, %loop2.jbody ]
  br label %loop2.jbody

loop2.jbody:
  %m72 = fmul float %a3, %xp1.0
  %m73 = fmul float %a4, %xp2.0
  %s74 = fadd float %m72, %m73
  %m75 = fmul float %b1, %yp1.0
  %s76 = fadd float %s74, %m75
  %m77 = fmul float %b2, %yp2.0
  %s78 = fadd float %s76, %m77

  %y2Off = mul nsw i64 %i2, %hz
  %y2Ptr = getelementptr inbounds float, ptr %rowY2.2, i64 %y2Off
  %y2ElemPtr = getelementptr inbounds float, ptr %y2Ptr, i64 %j2
  store float %s78, ptr %y2ElemPtr, align 4

  %inOff2 = mul nsw i64 %i2, %wz
  %inPtr2 = getelementptr inbounds float, ptr %rowIn2, i64 %inOff2
  %inElemPtr2 = getelementptr inbounds float, ptr %inPtr2, i64 %j2
  %xin2 = load float, ptr %inElemPtr2, align 4

  %y2val = load float, ptr %y2ElemPtr, align 4

  %j2.next = add nsw i64 %j2, -1
  %cmp2inner = icmp sge i64 %j2.next, 0
  br i1 %cmp2inner, label %loop2.j, label %loop2.inc

loop2.inc:                                        ; preds = %loop2.jbody, %loop2.i
  %i2.next = add nsw i64 %i2, 1
  %cmp2outer = icmp slt i64 %i2.next, %wz
  br i1 %cmp2outer, label %loop2.i, label %loop3check2

loop3check2:                                      ; preds = %loop2.inc, %loop3check
  br i1 %cmp.wh, label %loop3.preheader, label %loop5check

loop3.preheader:
  br label %loop3.i

loop3.i:                                          ; preds = %loop3.inc, %loop3.preheader
  %i3 = phi i64 [ 0, %loop3.preheader ], [ %i3.next, %loop3.inc ]
  br i1 %cmp.hh, label %loop3.j.preheader, label %loop3.inc

loop3.j.preheader:
  %rowY1.3 = getelementptr inbounds float, ptr %y1, i64 %i3
  %rowY2.3 = getelementptr inbounds float, ptr %y2, i64 %i3
  %rowOut.3 = getelementptr inbounds float, ptr %imgOut, i64 %i3
  %y1Off3 = mul nsw i64 %i3, %hz
  %y1RowPtr3 = getelementptr inbounds float, ptr %rowY1.3, i64 %y1Off3
  %y2Off3 = mul nsw i64 %i3, %hz
  %y2RowPtr3 = getelementptr inbounds float, ptr %rowY2.3, i64 %y2Off3
  %outOff3 = mul nsw i64 %i3, %hz
  %outRowPtr3 = getelementptr inbounds float, ptr %rowOut.3, i64 %outOff3
  br label %loop3.j

loop3.j:                                          ; preds = %loop3.j.preheader, %loop3.jbody
  %j3 = phi i64 [ 0, %loop3.j.preheader ], [ %j3.next, %loop3.jbody ]
  br label %loop3.jbody

loop3.jbody:
  %y1e3 = getelementptr inbounds float, ptr %y1RowPtr3, i64 %j3
  %y1v3 = load float, ptr %y1e3, align 4
  %y2e3 = getelementptr inbounds float, ptr %y2RowPtr3, i64 %j3
  %y2v3 = load float, ptr %y2e3, align 4
  %sum3 = fadd float %y1v3, %y2v3
  %m3 = fmul float %c1, %sum3
  %oute3 = getelementptr inbounds float, ptr %outRowPtr3, i64 %j3
  store float %m3, ptr %oute3, align 4

  %j3.next = add nsw i64 %j3, 1
  %cmp3inner = icmp slt i64 %j3.next, %hz
  br i1 %cmp3inner, label %loop3.j, label %loop3.inc

loop3.inc:                                        ; preds = %loop3.jbody, %loop3.i
  %i3.next = add nsw i64 %i3, 1
  %cmp3outer = icmp slt i64 %i3.next, %wz
  br i1 %cmp3outer, label %loop3.i, label %loop5check

loop5check:                                       ; preds = %loop3.inc, %loop3check2
  br i1 %cmp.hh, label %loop5.preheader, label %loop7check

loop5.preheader:
  br label %loop5.j

loop5.j:                                          ; preds = %loop5.inc, %loop5.preheader
  %j5 = phi i64 [ 0, %loop5.preheader ], [ %j5.next, %loop5.inc ]
  br i1 %cmp.wh, label %loop5.i.preheader, label %loop5.inc

loop5.i.preheader:
  br label %loop5.i

loop5.i:                                          ; preds = %loop5.i.preheader, %loop5.ibody
  %i5 = phi i64 [ 0, %loop5.i.preheader ], [ %i5.next, %loop5.ibody ]
  %tm1.0 = phi float [ 0.000000e+00, %loop5.i.preheader ], [ %outv5, %loop5.ibody ]
  %ym1.5 = phi float [ 0.000000e+00, %loop5.i.preheader ], [ %y1v5, %loop5.ibody ]
  %ym2.5 = phi float [ 0.000000e+00, %loop5.i.preheader ], [ %ym1.5, %loop5.ibody ]
  br label %loop5.ibody

loop5.ibody:
  %outOff5 = mul nsw i64 %i5, %hz
  %outRowPtr5 = getelementptr inbounds float, ptr %imgOut, i64 %i5
  %outRow5 = getelementptr inbounds float, ptr %outRowPtr5, i64 %outOff5
  %oute5 = getelementptr inbounds float, ptr %outRow5, i64 %j5
  %outLoad5 = load float, ptr %oute5, align 4

  %m132 = fmul float %a5, %outLoad5
  %m133 = fmul float %a6, %tm1.0
  %s134 = fadd float %m132, %m133
  %m135 = fmul float %b1, %ym1.5
  %s136 = fadd float %s134, %m135
  %m137 = fmul float %b2, %ym2.5
  %s138 = fadd float %s136, %m137

  %y1RowPtr5 = getelementptr inbounds float, ptr %y1, i64 %i5
  %y1Off5 = mul nsw i64 %i5, %hz
  %y1Row5 = getelementptr inbounds float, ptr %y1RowPtr5, i64 %y1Off5
  %y1e5 = getelementptr inbounds float, ptr %y1Row5, i64 %j5
  store float %s138, ptr %y1e5, align 4

  %outv5 = load float, ptr %oute5, align 4
  %y1v5 = load float, ptr %y1e5, align 4

  %i5.next = add nsw i64 %i5, 1
  %cmp5inner = icmp slt i64 %i5.next, %wz
  br i1 %cmp5inner, label %loop5.i, label %loop5.inc

loop5.inc:                                        ; preds = %loop5.ibody, %loop5.j
  %j5.next = add nsw i64 %j5, 1
  %cmp5outer = icmp slt i64 %j5.next, %hz
  br i1 %cmp5outer, label %loop5.j, label %loop7check

loop7check:                                       ; preds = %loop5.inc, %loop5check
  br i1 %cmp.hh, label %loop7.preheader, label %loop9check

loop7.preheader:
  br label %loop7.j

loop7.j:                                          ; preds = %loop7.inc, %loop7.preheader
  %j7 = phi i64 [ 0, %loop7.preheader ], [ %j7.next, %loop7.inc ]
  br i1 %cmp.wh, label %loop7.i.preheader, label %loop7.inc

loop7.i.preheader:
  %wm1 = sub nsw i64 %wz, 1
  br label %loop7.i

loop7.i:                                          ; preds = %loop7.i.preheader, %loop7.ibody
  %i7 = phi i64 [ %wm1, %loop7.i.preheader ], [ %i7.next, %loop7.ibody ]
  %tp1.0 = phi float [ 0.000000e+00, %loop7.i.preheader ], [ %outv7, %loop7.ibody ]
  %tp2.0 = phi float [ 0.000000e+00, %loop7.i.preheader ], [ %tp1.0, %loop7.ibody ]
  %yp1.7 = phi float [ 0.000000e+00, %loop7.i.preheader ], [ %y2v7, %loop7.ibody ]
  %yp2.7 = phi float [ 0.000000e+00, %loop7.i.preheader ], [ %yp1.7, %loop7.ibody ]
  br label %loop7.ibody

loop7.ibody:
  %m164 = fmul float %a7, %tp1.0
  %m165 = fmul float %a8, %tp2.0
  %s166 = fadd float %m164, %m165
  %m167 = fmul float %b1, %yp1.7
  %s168 = fadd float %s166, %m167
  %m169 = fmul float %b2, %yp2.7
  %s170 = fadd float %s168, %m169

  %y2RowPtr7 = getelementptr inbounds float, ptr %y2, i64 %i7
  %y2Off7 = mul nsw i64 %i7, %hz
  %y2Row7 = getelementptr inbounds float, ptr %y2RowPtr7, i64 %y2Off7
  %y2e7 = getelementptr inbounds float, ptr %y2Row7, i64 %j7
  store float %s170, ptr %y2e7, align 4

  %outRowPtr7 = getelementptr inbounds float, ptr %imgOut, i64 %i7
  %outOff7 = mul nsw i64 %i7, %hz
  %outRow7 = getelementptr inbounds float, ptr %outRowPtr7, i64 %outOff7
  %oute7 = getelementptr inbounds float, ptr %outRow7, i64 %j7
  %outv7 = load float, ptr %oute7, align 4

  %y2v7 = load float, ptr %y2e7, align 4

  %i7.next = add nsw i64 %i7, -1
  %cmp7inner = icmp sge i64 %i7.next, 0
  br i1 %cmp7inner, label %loop7.i, label %loop7.inc

loop7.inc:                                        ; preds = %loop7.ibody, %loop7.j
  %j7.next = add nsw i64 %j7, 1
  %cmp7outer = icmp slt i64 %j7.next, %hz
  br i1 %cmp7outer, label %loop7.j, label %loop9check

loop9check:                                       ; preds = %loop7.inc, %loop7check
  br i1 %cmp.wh, label %loop9.preheader, label %exit

loop9.preheader:
  br label %loop9.i

loop9.i:                                          ; preds = %loop9.inc, %loop9.preheader
  %i9 = phi i64 [ 0, %loop9.preheader ], [ %i9.next, %loop9.inc ]
  br i1 %cmp.hh, label %loop9.j.preheader, label %loop9.inc

loop9.j.preheader:
  %rowY1.9 = getelementptr inbounds float, ptr %y1, i64 %i9
  %rowY2.9 = getelementptr inbounds float, ptr %y2, i64 %i9
  %rowOut.9 = getelementptr inbounds float, ptr %imgOut, i64 %i9
  %y1Off9 = mul nsw i64 %i9, %hz
  %y1RowPtr9 = getelementptr inbounds float, ptr %rowY1.9, i64 %y1Off9
  %y2Off9 = mul nsw i64 %i9, %hz
  %y2RowPtr9 = getelementptr inbounds float, ptr %rowY2.9, i64 %y2Off9
  %outOff9 = mul nsw i64 %i9, %hz
  %outRowPtr9 = getelementptr inbounds float, ptr %rowOut.9, i64 %outOff9
  br label %loop9.j

loop9.j:                                          ; preds = %loop9.j.preheader, %loop9.jbody
  %j9 = phi i64 [ 0, %loop9.j.preheader ], [ %j9.next, %loop9.jbody ]
  br label %loop9.jbody

loop9.jbody:
  %y1e9 = getelementptr inbounds float, ptr %y1RowPtr9, i64 %j9
  %y1v9 = load float, ptr %y1e9, align 4
  %y2e9 = getelementptr inbounds float, ptr %y2RowPtr9, i64 %j9
  %y2v9 = load float, ptr %y2e9, align 4
  %sum9 = fadd float %y1v9, %y2v9
  %m9 = fmul float %c2, %sum9
  %oute9 = getelementptr inbounds float, ptr %outRowPtr9, i64 %j9
  store float %m9, ptr %oute9, align 4

  %j9.next = add nsw i64 %j9, 1
  %cmp9inner = icmp slt i64 %j9.next, %hz
  br i1 %cmp9inner, label %loop9.j, label %loop9.inc

loop9.inc:                                        ; preds = %loop9.jbody, %loop9.i
  %i9.next = add nsw i64 %i9, 1
  %cmp9outer = icmp slt i64 %i9.next, %wz
  br i1 %cmp9outer, label %loop9.i, label %exit

exit:                                             ; preds = %loop9.inc, %loop9check
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
