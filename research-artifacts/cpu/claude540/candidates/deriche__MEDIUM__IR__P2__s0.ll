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
  %e2 = call float @expf(float noundef %fneg) #2
  %sub10 = fsub float 1.000000e+00, %e2
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %e3 = call float @expf(float noundef %fneg) #2
  %mul14 = fmul float %mul11, %e3
  %add15 = fadd float 1.000000e+00, %mul14
  %mul16 = fmul float 2.000000e+00, %alpha
  %e4 = call float @expf(float noundef %mul16) #2
  %sub18 = fsub float %add15, %e4
  %k = fdiv float %mul, %sub18

  %a1 = fmul float %k, 1.0
  %a5 = fmul float %k, 1.0

  %e5 = call float @expf(float noundef %fneg) #2
  %mul21 = fmul float %k, %e5
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22
  %a6 = fmul float %mul21, %sub22

  %e6 = call float @expf(float noundef %fneg) #2
  %mul26 = fmul float %k, %e6
  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul26, %add27
  %a7 = fmul float %mul26, %add27

  %knegtmp = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %e7 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %knegtmp, %e7
  %a8 = fmul float %knegtmp, %e7

  %fneg33 = fneg float %alpha
  %b1 = call float @powf(float noundef 2.000000e+00, float noundef %fneg33) #2

  %mul35 = fmul float -2.000000e+00, %alpha
  %e8 = call float @expf(float noundef %mul35) #2
  %b2 = fneg float %e8

  %c2 = fadd float 1.000000e+00, 0.000000e+00
  %c1 = fadd float 1.000000e+00, 0.000000e+00

  %wpos = icmp sgt i32 %w, 0
  %hpos = icmp sgt i32 %h, 0

  br label %loop1.outer

loop1.outer:                                      ; preds = %entry, %loop1.outer.inc
  %i1 = phi i64 [ 0, %entry ], [ %i1.next, %loop1.outer.inc ]
  %cmp1 = icmp slt i64 %i1, %wz
  br i1 %cmp1, label %loop1.inner.preheader, label %after1

loop1.inner.preheader:
  %rowIn1 = mul nsw i64 %i1, %hz
  %rowY1a = mul nsw i64 %i1, %hz
  %inBase1 = getelementptr inbounds float, ptr %imgIn, i64 %rowIn1
  %y1Base1 = getelementptr inbounds float, ptr %y1, i64 %rowY1a
  br label %loop1.inner

loop1.inner:                                      ; preds = %loop1.inner.preheader, %loop1.inner
  %j1 = phi i64 [ 0, %loop1.inner.preheader ], [ %j1.next, %loop1.inner ]
  %ym1.1 = phi float [ 0.000000e+00, %loop1.inner.preheader ], [ %ym1new, %loop1.inner ]
  %ym2.1 = phi float [ 0.000000e+00, %loop1.inner.preheader ], [ %ym1.1, %loop1.inner ]
  %xm1.1 = phi float [ 0.000000e+00, %loop1.inner.preheader ], [ %xcur, %loop1.inner ]

  %inptr = getelementptr inbounds float, ptr %inBase1, i64 %j1
  %xcur = load float, ptr %inptr, align 4
  %mul43 = fmul float %a1, %xcur
  %mul44 = fmul float %a2, %xm1.1
  %add45 = fadd float %mul43, %mul44
  %mul46 = fmul float %b1, %ym1.1
  %add47 = fadd float %add45, %mul46
  %mul48 = fmul float %b2, %ym2.1
  %add49 = fadd float %add47, %mul48

  %y1ptr = getelementptr inbounds float, ptr %y1Base1, i64 %j1
  store float %add49, ptr %y1ptr, align 4

  %ym1new = load float, ptr %y1ptr, align 4

  %j1.next = add nsw i64 %j1, 1
  %cmp1i = icmp slt i64 %j1.next, %hz
  br i1 %cmp1i, label %loop1.inner, label %loop1.outer.inc

loop1.outer.inc:
  %i1.next = add nsw i64 %i1, 1
  br label %loop1.outer

after1:
  br label %loop2.outer

loop2.outer:                                      ; preds = %after1, %loop2.outer.inc
  %i2 = phi i64 [ 0, %after1 ], [ %i2.next, %loop2.outer.inc ]
  %cmp2 = icmp slt i64 %i2, %wz
  br i1 %cmp2, label %loop2.inner.preheader, label %after2

loop2.inner.preheader:
  %hsub1 = sub nsw i64 %hz, 1
  %rowIn2 = mul nsw i64 %i2, %hz
  %rowY2 = mul nsw i64 %i2, %hz
  %inBase2 = getelementptr inbounds float, ptr %imgIn, i64 %rowIn2
  %y2Base2 = getelementptr inbounds float, ptr %y2, i64 %rowY2
  %hgt0 = icmp sge i64 %hsub1, 0
  br i1 %hgt0, label %loop2.inner, label %loop2.outer.inc

loop2.inner:                                      ; preds = %loop2.inner.preheader, %loop2.inner
  %j2 = phi i64 [ %hsub1, %loop2.inner.preheader ], [ %j2.next, %loop2.inner ]
  %yp1.2 = phi float [ 0.000000e+00, %loop2.inner.preheader ], [ %yp1new, %loop2.inner ]
  %yp2.2 = phi float [ 0.000000e+00, %loop2.inner.preheader ], [ %yp1.2, %loop2.inner ]
  %xp1.2 = phi float [ 0.000000e+00, %loop2.inner.preheader ], [ %xp1new, %loop2.inner ]
  %xp2.2 = phi float [ 0.000000e+00, %loop2.inner.preheader ], [ %xp1.2, %loop2.inner ]

  %mul72 = fmul float %a3, %xp1.2
  %mul73 = fmul float %a4, %xp2.2
  %add74 = fadd float %mul72, %mul73
  %mul75 = fmul float %b1, %yp1.2
  %add76 = fadd float %add74, %mul75
  %mul77 = fmul float %b2, %yp2.2
  %add78 = fadd float %add76, %mul77

  %y2ptr = getelementptr inbounds float, ptr %y2Base2, i64 %j2
  store float %add78, ptr %y2ptr, align 4

  %inptr2 = getelementptr inbounds float, ptr %inBase2, i64 %j2
  %xp1new = load float, ptr %inptr2, align 4

  %yp1new = load float, ptr %y2ptr, align 4

  %j2.next = add nsw i64 %j2, -1
  %cmp2i = icmp sge i64 %j2.next, 0
  br i1 %cmp2i, label %loop2.inner, label %loop2.outer.inc

loop2.outer.inc:
  %i2.next = add nsw i64 %i2, 1
  br label %loop2.outer

after2:
  br label %loop3.outer

loop3.outer:                                      ; preds = %after2, %loop3.outer.inc
  %i3 = phi i64 [ 0, %after2 ], [ %i3.next, %loop3.outer.inc ]
  %cmp3 = icmp slt i64 %i3, %wz
  br i1 %cmp3, label %loop3.inner.preheader, label %after3

loop3.inner.preheader:
  %rowY1b3 = mul nsw i64 %i3, %hz
  %rowY2b3 = mul nsw i64 %i3, %hz
  %rowOut3 = mul nsw i64 %i3, %hz
  %y1Base3 = getelementptr inbounds float, ptr %y1, i64 %rowY1b3
  %y2Base3 = getelementptr inbounds float, ptr %y2, i64 %rowY2b3
  %outBase3 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut3
  br label %loop3.inner

loop3.inner:                                      ; preds = %loop3.inner.preheader, %loop3.inner
  %j3 = phi i64 [ 0, %loop3.inner.preheader ], [ %j3.next, %loop3.inner ]

  %y1ptr3 = getelementptr inbounds float, ptr %y1Base3, i64 %j3
  %v1 = load float, ptr %y1ptr3, align 4
  %y2ptr3 = getelementptr inbounds float, ptr %y2Base3, i64 %j3
  %v2 = load float, ptr %y2ptr3, align 4
  %add110 = fadd float %v1, %v2
  %mul111 = fmul float %c1, %add110

  %outptr3 = getelementptr inbounds float, ptr %outBase3, i64 %j3
  store float %mul111, ptr %outptr3, align 4

  %j3.next = add nsw i64 %j3, 1
  %cmp3i = icmp slt i64 %j3.next, %hz
  br i1 %cmp3i, label %loop3.inner, label %loop3.outer.inc

loop3.outer.inc:
  %i3.next = add nsw i64 %i3, 1
  br label %loop3.outer

after3:
  br label %loop4.outer

loop4.outer:                                      ; preds = %after3, %loop4.outer.inc
  %j4 = phi i64 [ 0, %after3 ], [ %j4.next, %loop4.outer.inc ]
  %cmp4 = icmp slt i64 %j4, %hz
  br i1 %cmp4, label %loop4.inner.preheader, label %after4

loop4.inner.preheader:
  br label %loop4.inner

loop4.inner:                                      ; preds = %loop4.inner.preheader, %loop4.inner
  %i4 = phi i64 [ 0, %loop4.inner.preheader ], [ %i4.next, %loop4.inner ]
  %tm1.4 = phi float [ 0.000000e+00, %loop4.inner.preheader ], [ %tm1new, %loop4.inner ]
  %ym1.4 = phi float [ 0.000000e+00, %loop4.inner.preheader ], [ %ym1new4, %loop4.inner ]
  %ym2.4 = phi float [ 0.000000e+00, %loop4.inner.preheader ], [ %ym1.4, %loop4.inner ]

  %rowOut4 = mul nsw i64 %i4, %hz
  %outptr4 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut4
  %outptr4j = getelementptr inbounds float, ptr %outptr4, i64 %j4
  %vout4 = load float, ptr %outptr4j, align 4
  %mul132 = fmul float %a5, %vout4
  %mul133 = fmul float %a6, %tm1.4
  %add134 = fadd float %mul132, %mul133
  %mul135 = fmul float %b1, %ym1.4
  %add136 = fadd float %add134, %mul135
  %mul137 = fmul float %b2, %ym2.4
  %add138 = fadd float %add136, %mul137

  %rowY1c4 = mul nsw i64 %i4, %hz
  %y1ptr4 = getelementptr inbounds float, ptr %y1, i64 %rowY1c4
  %y1ptr4j = getelementptr inbounds float, ptr %y1ptr4, i64 %j4
  store float %add138, ptr %y1ptr4j, align 4

  %tm1new = load float, ptr %outptr4j, align 4
  %ym1new4 = load float, ptr %y1ptr4j, align 4

  %i4.next = add nsw i64 %i4, 1
  %cmp4i = icmp slt i64 %i4.next, %wz
  br i1 %cmp4i, label %loop4.inner, label %loop4.outer.inc

loop4.outer.inc:
  %j4.next = add nsw i64 %j4, 1
  br label %loop4.outer

after4:
  br label %loop5.outer

loop5.outer:                                      ; preds = %after4, %loop5.outer.inc
  %j5 = phi i64 [ 0, %after4 ], [ %j5.next, %loop5.outer.inc ]
  %cmp5 = icmp slt i64 %j5, %hz
  br i1 %cmp5, label %loop5.inner.preheader, label %after5

loop5.inner.preheader:
  %wsub1 = sub nsw i64 %wz, 1
  %wge0 = icmp sge i64 %wsub1, 0
  br i1 %wge0, label %loop5.inner, label %loop5.outer.inc

loop5.inner:                                      ; preds = %loop5.inner.preheader, %loop5.inner
  %i5 = phi i64 [ %wsub1, %loop5.inner.preheader ], [ %i5.next, %loop5.inner ]
  %tp1.5 = phi float [ 0.000000e+00, %loop5.inner.preheader ], [ %tp1new, %loop5.inner ]
  %tp2.5 = phi float [ 0.000000e+00, %loop5.inner.preheader ], [ %tp1.5, %loop5.inner ]
  %yp1.5 = phi float [ 0.000000e+00, %loop5.inner.preheader ], [ %yp1new5, %loop5.inner ]
  %yp2.5 = phi float [ 0.000000e+00, %loop5.inner.preheader ], [ %yp1.5, %loop5.inner ]

  %mul164 = fmul float %a7, %tp1.5
  %mul165 = fmul float %a8, %tp2.5
  %add166 = fadd float %mul164, %mul165
  %mul167 = fmul float %b1, %yp1.5
  %add168 = fadd float %add166, %mul167
  %mul169 = fmul float %b2, %yp2.5
  %add170 = fadd float %add168, %mul169

  %rowY2d5 = mul nsw i64 %i5, %hz
  %y2ptr5 = getelementptr inbounds float, ptr %y2, i64 %rowY2d5
  %y2ptr5j = getelementptr inbounds float, ptr %y2ptr5, i64 %j5
  store float %add170, ptr %y2ptr5j, align 4

  %rowOut5 = mul nsw i64 %i5, %hz
  %outptr5 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut5
  %outptr5j = getelementptr inbounds float, ptr %outptr5, i64 %j5
  %tp1new = load float, ptr %outptr5j, align 4

  %yp1new5 = load float, ptr %y2ptr5j, align 4

  %i5.next = add nsw i64 %i5, -1
  %cmp5i = icmp sge i64 %i5.next, 0
  br i1 %cmp5i, label %loop5.inner, label %loop5.outer.inc

loop5.outer.inc:
  %j5.next = add nsw i64 %j5, 1
  br label %loop5.outer

after5:
  br label %loop6.outer

loop6.outer:                                      ; preds = %after5, %loop6.outer.inc
  %i6 = phi i64 [ 0, %after5 ], [ %i6.next, %loop6.outer.inc ]
  %cmp6 = icmp slt i64 %i6, %wz
  br i1 %cmp6, label %loop6.inner.preheader, label %after6

loop6.inner.preheader:
  %rowY1e6 = mul nsw i64 %i6, %hz
  %rowY2e6 = mul nsw i64 %i6, %hz
  %rowOut6 = mul nsw i64 %i6, %hz
  %y1Base6 = getelementptr inbounds float, ptr %y1, i64 %rowY1e6
  %y2Base6 = getelementptr inbounds float, ptr %y2, i64 %rowY2e6
  %outBase6 = getelementptr inbounds float, ptr %imgOut, i64 %rowOut6
  br label %loop6.inner

loop6.inner:                                      ; preds = %loop6.inner.preheader, %loop6.inner
  %j6 = phi i64 [ 0, %loop6.inner.preheader ], [ %j6.next, %loop6.inner ]

  %y1ptr6 = getelementptr inbounds float, ptr %y1Base6, i64 %j6
  %v1_6 = load float, ptr %y1ptr6, align 4
  %y2ptr6 = getelementptr inbounds float, ptr %y2Base6, i64 %j6
  %v2_6 = load float, ptr %y2ptr6, align 4
  %add203 = fadd float %v1_6, %v2_6
  %mul204 = fmul float %c2, %add203

  %outptr6 = getelementptr inbounds float, ptr %outBase6, i64 %j6
  store float %mul204, ptr %outptr6, align 4

  %j6.next = add nsw i64 %j6, 1
  %cmp6i = icmp slt i64 %j6.next, %hz
  br i1 %cmp6i, label %loop6.inner, label %loop6.outer.inc

loop6.outer.inc:
  %i6.next = add nsw i64 %i6, 1
  br label %loop6.outer

after6:
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
