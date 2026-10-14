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
  %fneg8 = fneg float %alpha
  %e2 = call float @expf(float noundef %fneg8) #2
  %sub10 = fsub float 1.000000e+00, %e2
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %fneg12 = fneg float %alpha
  %e3 = call float @expf(float noundef %fneg12) #2
  %mul14 = fmul float %mul11, %e3
  %add15 = fadd float 1.000000e+00, %mul14
  %mul16 = fmul float 2.000000e+00, %alpha
  %e4 = call float @expf(float noundef %mul16) #2
  %sub18 = fsub float %add15, %e4
  %k = fdiv float %mul, %sub18

  %a1 = fadd float %k, 0.000000e+00 ; a1 = a5 = k (identity add to keep value same object)
  %a5 = fadd float %k, 0.000000e+00

  %fneg19 = fneg float %alpha
  %e5 = call float @expf(float noundef %fneg19) #2
  %mul21 = fmul float %k, %e5
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22
  %a6 = fmul float %mul21, %sub22

  %fneg24 = fneg float %alpha
  %e6 = call float @expf(float noundef %fneg24) #2
  %mul26 = fmul float %k, %e6
  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul26, %add27
  %a7 = fmul float %mul26, %add27

  %fneg29 = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %e7 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %fneg29, %e7
  %a8 = fmul float %fneg29, %e7

  %fneg33 = fneg float %alpha
  %b1 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2

  %mul35 = fmul float -2.000000e+00, %alpha
  %e8 = call float @expf(float noundef %mul35) #2
  %b2 = fneg float %e8

  %c1 = fadd float 1.000000e+00, 0.000000e+00
  %c2 = fadd float 1.000000e+00, 0.000000e+00

  br label %loop1.header

loop1.header:
  %i.0 = phi i32 [ 0, %entry ], [ %inc63, %loop1.latch ]
  %cmp = icmp slt i32 %i.0, %w
  br i1 %cmp, label %loop1.body, label %loop1.exit

loop1.body:
  %i64.1 = sext i32 %i.0 to i64
  %rowIn.1 = getelementptr inbounds float, ptr %imgIn, i64 %i64.1
  %rowIn.off = mul nsw i64 %i64.1, %hz
  %rowInPtr = getelementptr inbounds float, ptr %imgIn, i64 %rowIn.off
  %rowY1.off = mul nsw i64 %i64.1, %hz
  %rowY1Ptr = getelementptr inbounds float, ptr %y1, i64 %rowY1.off
  br label %j1.header

j1.header:
  %j.1 = phi i32 [ 0, %loop1.body ], [ %j.1.inc, %j1.body ]
  %ym1.1 = phi float [ 0.000000e+00, %loop1.body ], [ %ym1.1.next, %j1.body ]
  %ym2.1 = phi float [ 0.000000e+00, %loop1.body ], [ %ym1.1, %j1.body ]
  %xm1.1 = phi float [ 0.000000e+00, %loop1.body ], [ %curIn.1, %j1.body ]
  %cmp39 = icmp slt i32 %j.1, %h
  br i1 %cmp39, label %j1.body, label %loop1.latch

j1.body:
  %j64.1 = sext i32 %j.1 to i64
  %curInPtr.1 = getelementptr inbounds float, ptr %rowInPtr, i64 %j64.1
  %curIn.1 = load float, ptr %curInPtr.1, align 4
  %mul43 = fmul float %a1, %curIn.1
  %mul44 = fmul float %a2, %xm1.1
  %add45 = fadd float %mul43, %mul44
  %mul46 = fmul float %b1, %ym1.1
  %add47 = fadd float %add45, %mul46
  %mul48 = fmul float %b2, %ym2.1
  %add49 = fadd float %add47, %mul48
  %outY1Ptr.1 = getelementptr inbounds float, ptr %rowY1Ptr, i64 %j64.1
  store float %add49, ptr %outY1Ptr.1, align 4
  %ym1.1.next = fadd float %add49, 0.000000e+00
  %j.1.inc = add nsw i32 %j.1, 1
  br label %j1.header, !llvm.loop !9

loop1.latch:
  %inc63 = add nsw i32 %i.0, 1
  br label %loop1.header, !llvm.loop !10

loop1.exit:
  br label %loop2.header

loop2.header:
  %i.2 = phi i32 [ 0, %loop1.exit ], [ %inc94, %loop2.latch ]
  %cmp66 = icmp slt i32 %i.2, %w
  br i1 %cmp66, label %loop2.body, label %loop2.exit

loop2.body:
  %i64.2 = sext i32 %i.2 to i64
  %rowIn.off2 = mul nsw i64 %i64.2, %hz
  %rowInPtr2 = getelementptr inbounds float, ptr %imgIn, i64 %rowIn.off2
  %rowY2.off = mul nsw i64 %i64.2, %hz
  %rowY2Ptr = getelementptr inbounds float, ptr %y2, i64 %rowY2.off
  %hm1 = sub nsw i32 %h, 1
  br label %j2.header

j2.header:
  %j.2 = phi i32 [ %hm1, %loop2.body ], [ %j.2.dec, %j2.body ]
  %xp1.2 = phi float [ 0.000000e+00, %loop2.body ], [ %curIn.2, %j2.body ]
  %xp2.2 = phi float [ 0.000000e+00, %loop2.body ], [ %xp1.2, %j2.body ]
  %yp1.2 = phi float [ 0.000000e+00, %loop2.body ], [ %curY2.2, %j2.body ]
  %yp2.2 = phi float [ 0.000000e+00, %loop2.body ], [ %yp1.2, %j2.body ]
  %cmp70 = icmp sge i32 %j.2, 0
  br i1 %cmp70, label %j2.body, label %loop2.latch

j2.body:
  %j64.2 = sext i32 %j.2 to i64
  %mul72 = fmul float %a3, %xp1.2
  %mul73 = fmul float %a4, %xp2.2
  %add74 = fadd float %mul72, %mul73
  %mul75 = fmul float %b1, %yp1.2
  %add76 = fadd float %add74, %mul75
  %mul77 = fmul float %b2, %yp2.2
  %add78 = fadd float %add76, %mul77
  %outY2Ptr.2 = getelementptr inbounds float, ptr %rowY2Ptr, i64 %j64.2
  store float %add78, ptr %outY2Ptr.2, align 4
  %curInPtr.2 = getelementptr inbounds float, ptr %rowInPtr2, i64 %j64.2
  %curIn.2 = load float, ptr %curInPtr.2, align 4
  %curY2.2 = load float, ptr %outY2Ptr.2, align 4
  %j.2.dec = add nsw i32 %j.2, -1
  br label %j2.header, !llvm.loop !11

loop2.latch:
  %inc94 = add nsw i32 %i.2, 1
  br label %loop2.header, !llvm.loop !12

loop2.exit:
  br label %loop3.header

loop3.header:
  %i.3 = phi i32 [ 0, %loop2.exit ], [ %inc120, %loop3.latch ]
  %cmp97 = icmp slt i32 %i.3, %w
  br i1 %cmp97, label %loop3.body, label %loop3.exit

loop3.body:
  %i64.3 = sext i32 %i.3 to i64
  %rowY1.off3 = mul nsw i64 %i64.3, %hz
  %rowY1Ptr3 = getelementptr inbounds float, ptr %y1, i64 %rowY1.off3
  %rowY2.off3 = mul nsw i64 %i64.3, %hz
  %rowY2Ptr3 = getelementptr inbounds float, ptr %y2, i64 %rowY2.off3
  %rowOut.off3 = mul nsw i64 %i64.3, %hz
  %rowOutPtr3 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut.off3
  br label %j3.header

j3.header:
  %j.3 = phi i32 [ 0, %loop3.body ], [ %j.3.inc, %j3.body ]
  %cmp100 = icmp slt i32 %j.3, %h
  br i1 %cmp100, label %j3.body, label %loop3.latch

j3.body:
  %j64.3 = sext i32 %j.3 to i64
  %y1Ptr.3 = getelementptr inbounds float, ptr %rowY1Ptr3, i64 %j64.3
  %y1val.3 = load float, ptr %y1Ptr.3, align 4
  %y2Ptr.3 = getelementptr inbounds float, ptr %rowY2Ptr3, i64 %j64.3
  %y2val.3 = load float, ptr %y2Ptr.3, align 4
  %add110 = fadd float %y1val.3, %y2val.3
  %mul111 = fmul float %c1, %add110
  %outPtr.3 = getelementptr inbounds float, ptr %rowOutPtr3, i64 %j64.3
  store float %mul111, ptr %outPtr.3, align 4
  %j.3.inc = add nsw i32 %j.3, 1
  br label %j3.header, !llvm.loop !13

loop3.latch:
  %inc120 = add nsw i32 %i.3, 1
  br label %loop3.header, !llvm.loop !14

loop3.exit:
  br label %loop4.header

loop4.header:
  %j.4o = phi i32 [ 0, %loop3.exit ], [ %inc155, %loop4.latch ]
  %cmp123 = icmp slt i32 %j.4o, %h
  br i1 %cmp123, label %loop4.body, label %loop4.exit

loop4.body:
  %j64.4o = sext i32 %j.4o to i64
  br label %i4.header

i4.header:
  %i.4 = phi i32 [ 0, %loop4.body ], [ %i.4.inc, %i4.body ]
  %tm1.4 = phi float [ 0.000000e+00, %loop4.body ], [ %curOut.4, %i4.body ]
  %ym1.4 = phi float [ 0.000000e+00, %loop4.body ], [ %add138.4, %i4.body ]
  %ym2.4 = phi float [ 0.000000e+00, %loop4.body ], [ %ym1.4, %i4.body ]
  %cmp126 = icmp slt i32 %i.4, %w
  br i1 %cmp126, label %i4.body, label %loop4.latch

i4.body:
  %i64.4 = sext i32 %i.4 to i64
  %rowOut.off4 = mul nsw i64 %i64.4, %hz
  %rowOutPtr4 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut.off4
  %outPtr.4 = getelementptr inbounds float, ptr %rowOutPtr4, i64 %j64.4o
  %curOutVal.4 = load float, ptr %outPtr.4, align 4
  %mul132 = fmul float %a5, %curOutVal.4
  %mul133 = fmul float %a6, %tm1.4
  %add134 = fadd float %mul132, %mul133
  %mul135 = fmul float %b1, %ym1.4
  %add136 = fadd float %add134, %mul135
  %mul137 = fmul float %b2, %ym2.4
  %add138.4 = fadd float %add136, %mul137
  %rowY1.off4 = mul nsw i64 %i64.4, %hz
  %rowY1Ptr4 = getelementptr inbounds float, ptr %y1, i64 %rowY1.off4
  %y1Ptr.4 = getelementptr inbounds float, ptr %rowY1Ptr4, i64 %j64.4o
  store float %add138.4, ptr %y1Ptr.4, align 4
  %curOut.4 = fadd float %curOutVal.4, 0.000000e+00
  %i.4.inc = add nsw i32 %i.4, 1
  br label %i4.header, !llvm.loop !15

loop4.latch:
  %inc155 = add nsw i32 %j.4o, 1
  br label %loop4.header, !llvm.loop !16

loop4.exit:
  br label %loop5.header

loop5.header:
  %j.5o = phi i32 [ 0, %loop4.exit ], [ %inc187, %loop5.latch ]
  %cmp158 = icmp slt i32 %j.5o, %h
  br i1 %cmp158, label %loop5.body, label %loop5.exit

loop5.body:
  %j64.5o = sext i32 %j.5o to i64
  %wm1 = sub nsw i32 %w, 1
  br label %i5.header

i5.header:
  %i.5 = phi i32 [ %wm1, %loop5.body ], [ %i.5.dec, %i5.body ]
  %tp1.5 = phi float [ 0.000000e+00, %loop5.body ], [ %curOut.5, %i5.body ]
  %tp2.5 = phi float [ 0.000000e+00, %loop5.body ], [ %tp1.5, %i5.body ]
  %yp1.5 = phi float [ 0.000000e+00, %loop5.body ], [ %add170.5, %i5.body ]
  %yp2.5 = phi float [ 0.000000e+00, %loop5.body ], [ %yp1.5, %i5.body ]
  %cmp162 = icmp sge i32 %i.5, 0
  br i1 %cmp162, label %i5.body, label %loop5.latch

i5.body:
  %i64.5 = sext i32 %i.5 to i64
  %mul164 = fmul float %a7, %tp1.5
  %mul165 = fmul float %a8, %tp2.5
  %add166 = fadd float %mul164, %mul165
  %mul167 = fmul float %b1, %yp1.5
  %add168 = fadd float %add166, %mul167
  %mul169 = fmul float %b2, %yp2.5
  %add170.5 = fadd float %add168, %mul169
  %rowY2.off5 = mul nsw i64 %i64.5, %hz
  %rowY2Ptr5 = getelementptr inbounds float, ptr %y2, i64 %rowY2.off5
  %y2Ptr.5 = getelementptr inbounds float, ptr %rowY2Ptr5, i64 %j64.5o
  store float %add170.5, ptr %y2Ptr.5, align 4
  %rowOut.off5 = mul nsw i64 %i64.5, %hz
  %rowOutPtr5 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut.off5
  %outPtr.5 = getelementptr inbounds float, ptr %rowOutPtr5, i64 %j64.5o
  %curOutVal.5 = load float, ptr %outPtr.5, align 4
  %curOut.5 = fadd float %curOutVal.5, 0.000000e+00
  %i.5.dec = add nsw i32 %i.5, -1
  br label %i5.header, !llvm.loop !17

loop5.latch:
  %inc187 = add nsw i32 %j.5o, 1
  br label %loop5.header, !llvm.loop !18

loop5.exit:
  br label %loop6.header

loop6.header:
  %i.6 = phi i32 [ 0, %loop5.exit ], [ %inc213, %loop6.latch ]
  %cmp190 = icmp slt i32 %i.6, %w
  br i1 %cmp190, label %loop6.body, label %loop6.exit

loop6.body:
  %i64.6 = sext i32 %i.6 to i64
  %rowY1.off6 = mul nsw i64 %i64.6, %hz
  %rowY1Ptr6 = getelementptr inbounds float, ptr %y1, i64 %rowY1.off6
  %rowY2.off6 = mul nsw i64 %i64.6, %hz
  %rowY2Ptr6 = getelementptr inbounds float, ptr %y2, i64 %rowY2.off6
  %rowOut.off6 = mul nsw i64 %i64.6, %hz
  %rowOutPtr6 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut.off6
  br label %j6.header

j6.header:
  %j.6 = phi i32 [ 0, %loop6.body ], [ %j.6.inc, %j6.body ]
  %cmp193 = icmp slt i32 %j.6, %h
  br i1 %cmp193, label %j6.body, label %loop6.latch

j6.body:
  %j64.6 = sext i32 %j.6 to i64
  %y1Ptr.6 = getelementptr inbounds float, ptr %rowY1Ptr6, i64 %j64.6
  %y1val.6 = load float, ptr %y1Ptr.6, align 4
  %y2Ptr.6 = getelementptr inbounds float, ptr %rowY2Ptr6, i64 %j64.6
  %y2val.6 = load float, ptr %y2Ptr.6, align 4
  %add203 = fadd float %y1val.6, %y2val.6
  %mul204 = fmul float %c2, %add203
  %outPtr.6 = getelementptr inbounds float, ptr %rowOutPtr6, i64 %j64.6
  store float %mul204, ptr %outPtr.6, align 4
  %j.6.inc = add nsw i32 %j.6, 1
  br label %j6.header, !llvm.loop !19

loop6.latch:
  %inc213 = add nsw i32 %i.6, 1
  br label %loop6.header, !llvm.loop !20

loop6.exit:
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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
!13 = distinct !{!13, !7}
!14 = distinct !{!14, !7}
!15 = distinct !{!15, !7}
!16 = distinct !{!16, !7}
!17 = distinct !{!17, !7}
!18 = distinct !{!18, !7}
!19 = distinct !{!19, !7}
!20 = distinct !{!20, !7}
